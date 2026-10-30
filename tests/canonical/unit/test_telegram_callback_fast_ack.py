"""Conservative read-only Telegram callback acknowledgement regression tests."""

from __future__ import annotations

import pytest


def _callback(data: str, *, user_id: int = 7001, chat_id: int = 7001, callback_id: str = "callback-1") -> dict:
    return {
        "update_id": 1234,
        "callback_query": {
            "id": callback_id,
            "from": {"id": user_id},
            "data": data,
            "message": {
                "chat": {"id": chat_id, "type": "private" if chat_id > 0 else "supergroup"},
                "message_id": 55,
            },
        },
    }


def test_valid_generated_status_ack_precedes_render(
    canonical_runtime_root,
    fresh_imports,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    updates = fresh_imports("runtime.telegram_updates")
    events: list[tuple] = []
    generation = updates.telegram_app_nav.begin_navigation_generation(7001, 7001)
    assert generation > 0
    callback = _callback(f"APP:{generation}:STATUS")
    monkeypatch.setattr(
        updates, "_ack_callback",
        lambda callback_id, text="": events.append(("ack", callback_id, text)),
    )
    monkeypatch.setattr(
        updates.bot_service, "process_update",
        lambda _update: events.append(("render",)) or None,
    )
    monkeypatch.setattr(updates, "_report_slow_callback", lambda **_kwargs: None)

    updates.process_update(callback)

    assert events == [("ack", "callback-1", ""), ("render",)]


def test_stale_app_generation_preserves_recovery_toast(
    canonical_runtime_root,
    fresh_imports,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    updates = fresh_imports("runtime.telegram_updates")
    old_generation = updates.telegram_app_nav.begin_navigation_generation(7001, 7001)
    updates.telegram_app_nav.begin_navigation_generation(7001, 7001)
    events: list[tuple] = []

    monkeypatch.setattr(
        updates, "_ack_callback",
        lambda callback_id, text="": events.append(("ack", text)),
    )
    monkeypatch.setattr(
        updates.bot_service, "process_update",
        lambda _update: events.append(("render",)) or {"callback_ack_text": "Button expired — returned to Home."},
    )
    monkeypatch.setattr(updates, "_report_slow_callback", lambda **_kwargs: None)

    updates.process_update(_callback(f"APP:{old_generation}:STATUS"))

    assert events == [("render",), ("ack", "Button expired — returned to Home.")]


def test_owner_admin_read_only_home_ack_precedes_render(
    canonical_runtime_root,
    fresh_imports,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    updates = fresh_imports("runtime.telegram_updates")
    events: list[tuple] = []
    monkeypatch.setattr(updates.bot_service, "is_owner", lambda uid: uid == 7001)
    monkeypatch.setattr(updates.bot_service, "_can_use_admin_callback", lambda msg, uid: uid == 7001)
    monkeypatch.setattr(
        updates, "_ack_callback",
        lambda callback_id, text="": events.append(("ack", text)),
    )
    monkeypatch.setattr(
        updates.bot_service, "process_update",
        lambda _update: events.append(("render",)) or None,
    )
    monkeypatch.setattr(updates, "_report_slow_callback", lambda **_kwargs: None)

    updates.process_update(_callback("ADMIN_NAV:HOME"))

    assert events == [("ack", ""), ("render",)]


def test_unauthorized_admin_and_mutations_keep_governed_post_ack(
    canonical_runtime_root,
    fresh_imports,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    updates = fresh_imports("runtime.telegram_updates")
    events: list[tuple] = []
    monkeypatch.setattr(updates.bot_service, "is_owner", lambda _uid: False)
    monkeypatch.setattr(updates.bot_service, "_can_use_admin_callback", lambda _msg, _uid: False)
    monkeypatch.setattr(
        updates, "_ack_callback",
        lambda callback_id, text="": events.append(("ack", text)),
    )
    monkeypatch.setattr(
        updates.bot_service, "process_update",
        lambda _update: events.append(("process",)) or {"callback_ack_text": "Access denied."},
    )
    monkeypatch.setattr(updates, "_report_slow_callback", lambda **_kwargs: None)

    updates.process_update(_callback("ADMIN_NAV:HOME"))
    assert events == [("process",), ("ack", "Access denied.")]
    events.clear()

    # Even when Owner is allowed, a symbol mutation cannot pre-ACK.
    monkeypatch.setattr(updates.bot_service, "is_owner", lambda _uid: True)
    monkeypatch.setattr(updates.bot_service, "_can_use_admin_callback", lambda _msg, _uid: True)
    updates.process_update(_callback("ADMIN_NAV:SYM_TOGGLE:HOME:EURUSD"))
    assert events == [("process",), ("ack", "Access denied.")]


def test_slow_callback_telemetry_is_bounded_and_id_free(
    canonical_runtime_root,
    fresh_imports,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    updates = fresh_imports("runtime.telegram_updates")
    warnings: list[dict] = []
    monkeypatch.setattr(updates.observability_logger, "log_warning", lambda **kw: warnings.append(kw))
    monkeypatch.setattr(updates.time, "monotonic", lambda: 5000.0)
    monkeypatch.setattr(updates, "_LAST_SLOW_CALLBACK_LOG_MONOTONIC", 0.0)

    for _ in range(3):
        updates._report_slow_callback(fast_ack=True, ack_elapsed_ms=40, handler_elapsed_ms=1800, family="APP")

    assert len(warnings) == 1
    assert warnings[0]["warn_type"] == "telegram_callback_slow"
    assert warnings[0]["context"] == {
        "callback_family": "APP",
        "fast_ack": True,
        "ack_elapsed_ms": 40,
        "handler_elapsed_ms": 1800,
    }
    assert "callback_query_id" not in warnings[0]["context"]
    assert "user_id" not in warnings[0]["context"]


def test_legacy_generationless_status_does_not_pre_ack(
    canonical_runtime_root,
    fresh_imports,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    updates = fresh_imports("runtime.telegram_updates")
    events: list[tuple] = []
    monkeypatch.setattr(
        updates, "_ack_callback",
        lambda callback_id, text="": events.append(("ack", text)),
    )
    monkeypatch.setattr(
        updates.bot_service, "process_update",
        lambda _update: events.append(("process",)) or {"callback_ack_text": "Button expired."},
    )
    monkeypatch.setattr(updates, "_report_slow_callback", lambda **_kwargs: None)
    updates.process_update(_callback("APP:STATUS"))
    assert events == [("process",), ("ack", "Button expired.")]
