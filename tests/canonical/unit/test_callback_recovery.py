"""Canonical callback recovery tests for Issue #42."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional

import pytest


def _callback_update(
    chat_id: int,
    user_id: int,
    data: str,
    *,
    callback_id: str = "callback-1",
    message_id: int = 5001,
    chat_type: str = "private",
    thread_id: Optional[int] = None,
) -> Dict[str, Any]:
    message: Dict[str, Any] = {
        "chat": {"id": chat_id, "type": chat_type},
        "message_id": message_id,
        "text": "previous interactive page",
    }
    if thread_id is not None:
        message["message_thread_id"] = thread_id
    return {
        "callback_query": {
            "id": callback_id,
            "from": {"id": user_id, "first_name": "Owner"},
            "data": data,
            "message": message,
        }
    }


def _capture_interactive_transport(
    monkeypatch: pytest.MonkeyPatch,
    bot_module,
) -> tuple[list[dict], list[dict]]:
    sends: list[dict] = []
    edits: list[dict] = []

    def _send(chat_id, text, reply_markup=None, thread_id=None):
        sends.append(
            {
                "chat_id": chat_id,
                "text": text,
                "reply_markup": reply_markup,
                "thread_id": thread_id,
            }
        )
        return {"ok": True, "result": {"message_id": 9900}}

    def _edit(chat_id, message_id, text, reply_markup=None):
        edits.append(
            {
                "chat_id": chat_id,
                "message_id": message_id,
                "text": text,
                "reply_markup": reply_markup,
            }
        )
        return {"ok": True, "result": {"message_id": message_id}}

    monkeypatch.setattr(bot_module.telegram_publisher, "send_message", _send)
    monkeypatch.setattr(bot_module.telegram_publisher, "edit_message", _edit)
    return sends, edits


def _callbacks(markup: Dict[str, Any]) -> list[str]:
    return [
        str(button.get("callback_data") or "")
        for row in (markup or {}).get("inline_keyboard", [])
        for button in row
    ]


def test_stale_app_callback_recovers_tracked_active_message_not_obsolete_origin(
    canonical_runtime_root: Path,
    fresh_imports,
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setenv("OWNER_TELEGRAM_ID", "7001")
    bot = fresh_imports("core.bot_service")
    nav = bot.telegram_app_nav
    sends, edits = _capture_interactive_transport(monkeypatch, bot)

    nav.begin_navigation_generation(7001, 7001)
    nav.begin_navigation_generation(7001, 7001)
    nav.set_active_message(user_id=7001, chat_id=7001, message_id=9001)

    result = bot.process_update(
        _callback_update(7001, 7001, "APP:1:STATUS", message_id=8001)
    )

    assert result and "expired" in result["callback_ack_text"].lower()
    assert sends == []
    assert [item["message_id"] for item in edits] == [9001]
    assert "role-aware entry point" in edits[0]["text"]
    assert edits[0]["reply_markup"]["inline_keyboard"]
    assert any(
        callback.endswith(":STATUS") or callback == "APP:STATUS"
        for callback in _callbacks(edits[0]["reply_markup"])
    )
    assert nav.get_active_message(user_id=7001, chat_id=7001) == 9001


def test_stale_app_callback_reuses_origin_when_no_active_message_is_known(
    canonical_runtime_root: Path,
    fresh_imports,
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setenv("OWNER_TELEGRAM_ID", "7002")
    bot = fresh_imports("core.bot_service")
    nav = bot.telegram_app_nav
    sends, edits = _capture_interactive_transport(monkeypatch, bot)

    nav.begin_navigation_generation(7002, 7002)
    nav.begin_navigation_generation(7002, 7002)

    result = bot.process_update(
        _callback_update(7002, 7002, "APP:1:HELP", message_id=8002)
    )

    assert result and result["callback_ack_text"]
    assert sends == []
    assert [item["message_id"] for item in edits] == [8002]
    assert edits[0]["reply_markup"]["inline_keyboard"]
    assert nav.get_active_message(user_id=7002, chat_id=7002) == 8002


@pytest.mark.parametrize("callback_data", ["APP:NOT_A_REAL_PAGE", "APP:"])
def test_unknown_app_callback_recovers_public_home_without_admin_surface(
    canonical_runtime_root: Path,
    fresh_imports,
    monkeypatch: pytest.MonkeyPatch,
    callback_data: str,
):
    monkeypatch.setenv("OWNER_TELEGRAM_ID", "7099")
    monkeypatch.setenv("ADMIN_CONTROL_CHAT_ID", "-7099")
    bot = fresh_imports("core.bot_service")
    sends, edits = _capture_interactive_transport(monkeypatch, bot)

    result = bot.process_update(
        _callback_update(7003, 7003, callback_data, message_id=8003)
    )

    assert result and "unknown" in result["callback_ack_text"].lower()
    assert "Admin Home" not in result["callback_ack_text"]
    assert sends == []
    assert len(edits) == 1
    assert "role-aware entry point" in edits[0]["text"]
    callbacks = _callbacks(edits[0]["reply_markup"])
    assert callbacks
    assert not any(callback.startswith("ADMIN_NAV:") for callback in callbacks)
    assert not any(callback.endswith(":ADMIN") for callback in callbacks)


@pytest.mark.parametrize(
    ("callback_data", "expected_ack"),
    [
        ("ADMIN_STATUS", "retired"),
        ("UNRECOGNISED_CALLBACK", "unknown"),
        ("ADMIN_NAV:NOT_A_REAL_PAGE", "unknown"),
    ],
)
def test_authorized_unknown_and_retired_callbacks_recover_role_scoped_admin_home(
    canonical_runtime_root: Path,
    fresh_imports,
    monkeypatch: pytest.MonkeyPatch,
    callback_data: str,
    expected_ack: str,
):
    monkeypatch.setenv("OWNER_TELEGRAM_ID", "7101")
    bot = fresh_imports("core.bot_service")
    sends, edits = _capture_interactive_transport(monkeypatch, bot)

    result = bot.process_update(
        _callback_update(7101, 7101, callback_data, message_id=8101)
    )

    assert result and expected_ack in result["callback_ack_text"].lower()
    assert sends == []
    assert len(edits) == 1
    assert "Admin Control Surface" in edits[0]["text"]
    callbacks = _callbacks(edits[0]["reply_markup"])
    assert callbacks
    assert "ADMIN_NAV:INFO:admin_home:HOME" in callbacks
    assert any(callback.startswith("ADMIN_NAV:") for callback in callbacks)


def test_unknown_callback_recovery_does_not_expand_analyst_visibility(
    canonical_runtime_root: Path,
    fresh_imports,
    monkeypatch: pytest.MonkeyPatch,
):
    roles_path = canonical_runtime_root / "config" / "admin_roles.json"
    roles = json.loads(roles_path.read_text(encoding="utf-8"))
    roles["analyst"] = [7151]
    roles_path.write_text(json.dumps(roles), encoding="utf-8")

    monkeypatch.setenv("ADMIN_ROLES_CONFIG", str(roles_path))
    monkeypatch.setenv("ADMIN_CONTROL_CHAT_ID", "-7151")
    monkeypatch.setenv("ADMIN_CONTROL_THREAD_ID", "55")
    bot = fresh_imports("core.bot_service")
    sends, edits = _capture_interactive_transport(monkeypatch, bot)

    result = bot.process_update(
        _callback_update(
            -7151,
            7151,
            "UNKNOWN_ADMIN_CALLBACK",
            message_id=8151,
            chat_type="supergroup",
            thread_id=55,
        )
    )

    assert result and "unknown" in result["callback_ack_text"].lower()
    assert sends == []
    assert len(edits) == 1
    callbacks = _callbacks(edits[0]["reply_markup"])
    assert "ADMIN_NAV:DECISION_VIS" in callbacks
    assert "ADMIN_NAV:RESEARCH" in callbacks
    assert "ADMIN_NAV:INTELLIGENCE" in callbacks
    assert "ADMIN_NAV:OPERATIONS" not in callbacks
    assert "ADMIN_NAV:ROLES" not in callbacks
    assert "ADMIN_NAV:SECAUDIT" not in callbacks


def test_unauthorized_admin_callback_is_toast_only_and_fail_closed(
    canonical_runtime_root: Path,
    fresh_imports,
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setenv("OWNER_TELEGRAM_ID", "7201")
    monkeypatch.setenv("ADMIN_CONTROL_CHAT_ID", "-7201")
    monkeypatch.setenv("ADMIN_CONTROL_THREAD_ID", "100")
    bot = fresh_imports("core.bot_service")
    sends, edits = _capture_interactive_transport(monkeypatch, bot)

    result = bot.process_update(
        _callback_update(
            -7201,
            7202,
            "ADMIN_NAV:HOME",
            message_id=8201,
            chat_type="supergroup",
            thread_id=42,
        )
    )

    assert result and "denied" in result["callback_ack_text"].lower()
    assert sends == []
    assert edits == []


def test_context_restricted_admin_callback_is_toast_only_in_owner_private_chat(
    canonical_runtime_root: Path,
    fresh_imports,
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setenv("OWNER_TELEGRAM_ID", "7251")
    monkeypatch.setenv("ADMIN_CONTROL_CHAT_ID", "-7251")
    bot = fresh_imports("core.bot_service")
    sends, edits = _capture_interactive_transport(monkeypatch, bot)

    result = bot.process_update(
        _callback_update(
            7251,
            7251,
            "ADMIN_NAV:RELOAD_ROLES_CONFIRM",
            message_id=8251,
        )
    )

    assert result and "denied" in result["callback_ack_text"].lower()
    assert sends == []
    assert edits == []


@pytest.mark.parametrize("callback_data", ["ADMIN_STATUS", "UNKNOWN_RAW_CALLBACK"])
def test_legacy_or_unknown_callback_outside_admin_context_reveals_no_admin_page(
    canonical_runtime_root: Path,
    fresh_imports,
    monkeypatch: pytest.MonkeyPatch,
    callback_data: str,
):
    monkeypatch.setenv("OWNER_TELEGRAM_ID", "7301")
    monkeypatch.setenv("ADMIN_CONTROL_CHAT_ID", "-7301")
    bot = fresh_imports("core.bot_service")
    sends, edits = _capture_interactive_transport(monkeypatch, bot)

    result = bot.process_update(
        _callback_update(7302, 7302, callback_data, message_id=8301)
    )

    assert result and "denied" in result["callback_ack_text"].lower()
    assert sends == []
    assert edits == []


@pytest.mark.parametrize(
    "ack_text",
    [
        "Button expired — returned to Home.",
        "Unknown action — returned to Home.",
        "Unknown action — returned to Admin Home.",
        "This button was retired — returned to Admin Home.",
        "Access denied.",
    ],
)
def test_transport_delivers_recovery_notification_text(
    canonical_runtime_root: Path,
    fresh_imports,
    monkeypatch: pytest.MonkeyPatch,
    ack_text: str,
):
    updates = fresh_imports("runtime.telegram_updates")
    acknowledgements: list[dict] = []

    monkeypatch.setattr(
        updates.bot_service,
        "process_update",
        lambda _update: {"callback_ack_text": ack_text},
    )
    monkeypatch.setattr(
        updates.telegram_publisher,
        "answer_callback_query",
        lambda callback_query_id, text="", show_alert=False: acknowledgements.append(
            {
                "id": callback_query_id,
                "text": text,
                "show_alert": show_alert,
            }
        ),
    )

    updates.process_update(
        _callback_update(7401, 7401, "APP:HOME", callback_id="ack-recovery")
    )

    assert acknowledgements == [
        {"id": "ack-recovery", "text": ack_text, "show_alert": False}
    ]


def test_transport_keeps_normal_callback_ack_empty(
    canonical_runtime_root: Path,
    fresh_imports,
    monkeypatch: pytest.MonkeyPatch,
):
    updates = fresh_imports("runtime.telegram_updates")
    acknowledgements: list[dict] = []

    monkeypatch.setattr(updates.bot_service, "process_update", lambda _update: None)
    monkeypatch.setattr(
        updates.telegram_publisher,
        "answer_callback_query",
        lambda callback_query_id, text="", show_alert=False: acknowledgements.append(
            {"id": callback_query_id, "text": text, "show_alert": show_alert}
        ),
    )

    updates.process_update(
        _callback_update(7501, 7501, "APP:HOME", callback_id="ack-normal")
    )

    assert acknowledgements == [
        {"id": "ack-normal", "text": "", "show_alert": False}
    ]


def test_transport_bounds_callback_notification_to_telegram_limit(
    canonical_runtime_root: Path,
    fresh_imports,
    monkeypatch: pytest.MonkeyPatch,
):
    updates = fresh_imports("runtime.telegram_updates")
    acknowledgements: list[str] = []

    monkeypatch.setattr(
        updates.bot_service,
        "process_update",
        lambda _update: {"callback_ack_text": "x" * 500},
    )
    monkeypatch.setattr(
        updates.telegram_publisher,
        "answer_callback_query",
        lambda _callback_query_id, text="", show_alert=False: acknowledgements.append(text),
    )

    updates.process_update(
        _callback_update(7601, 7601, "APP:HOME", callback_id="ack-bounded")
    )

    assert len(acknowledgements) == 1
    assert len(acknowledgements[0]) == 200
    assert acknowledgements[0].endswith("...")


def test_vote_callback_keeps_outcome_ack_contract(
    canonical_runtime_root: Path,
    fresh_imports,
    monkeypatch: pytest.MonkeyPatch,
):
    updates = fresh_imports("runtime.telegram_updates")
    acknowledgements: list[dict] = []

    monkeypatch.setattr(
        updates.outcome_service,
        "handle_vote_callback_data",
        lambda **_kwargs: {"accepted": True, "reason": "ok"},
    )
    monkeypatch.setattr(
        updates.bot_service,
        "process_update",
        lambda _update: pytest.fail("VOTE_ callback reached generic bot dispatcher"),
    )
    monkeypatch.setattr(
        updates.requests,
        "post",
        lambda _url, json, timeout: acknowledgements.append(json),
    )

    updates.process_update(
        _callback_update(
            7701,
            7701,
            "VOTE_|signal-1|WIN",
            callback_id="ack-vote",
        )
    )

    assert acknowledgements == [
        {
            "callback_query_id": "ack-vote",
            "text": "Outcome recorded.",
            "show_alert": False,
        }
    ]
