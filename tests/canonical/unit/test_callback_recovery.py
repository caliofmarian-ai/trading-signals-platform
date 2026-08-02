"""
tests/canonical/unit/test_callback_recovery.py

Canonical unit tests for Telegram callback recovery.

Covers Epic #23 remaining item: "Correct stale/unknown/retired/unauthorized
callback handling".

Four recovery categories:
  1. STALE generation  — APP: callback whose generation number does not match
                         the current session.  Must render Home and deliver a
                         toast via answerCallbackQuery; must NOT silently
                         redirect without user feedback.
  2. UNKNOWN           — Callback data that does not match any known prefix.
                         Must return ack text; must NOT overwrite the active
                         navigation message.
  3. RETIRED           — Legacy admin-panel callback data retired in BATCH-05.
                         Must return ack text; must NOT overwrite the active
                         navigation message.
  4. UNAUTHORIZED      — ADMIN_NAV: callback from a context that lacks admin
                         access.  Must return ack text; must NOT overwrite the
                         active navigation message.

Each category is covered at two layers:
  - bot_service.process_update() return-value contract
  - telegram_updates.process_update() answer_callback_query integration
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional
from unittest.mock import call

import pytest


# ---------------------------------------------------------------------------
# Update builder helpers
# ---------------------------------------------------------------------------

def _app_callback_update(
    chat_id: int,
    user_id: int,
    data: str,
    *,
    callback_id: str = "cb-test",
    message_id: int = 5001,
    chat_type: str = "private",
    thread_id: Optional[int] = None,
) -> Dict[str, Any]:
    msg: Dict[str, Any] = {
        "chat": {"id": chat_id, "type": chat_type},
        "message_id": message_id,
        "text": "previous page",
    }
    if thread_id is not None:
        msg["message_thread_id"] = thread_id
    return {
        "callback_query": {
            "id": callback_id,
            "from": {"id": user_id, "first_name": "Tester"},
            "data": data,
            "message": msg,
        }
    }


def _capture_send(monkeypatch: pytest.MonkeyPatch, bot_mod) -> List[Dict]:
    calls: List[Dict] = []

    def _send(chat_id, text, reply_markup=None, thread_id=None):
        calls.append({"chat_id": chat_id, "text": text})
        return {"ok": True, "result": {"message_id": 9000}}

    monkeypatch.setattr(bot_mod.telegram_publisher, "send_message", _send)
    return calls


def _capture_edit(monkeypatch: pytest.MonkeyPatch, bot_mod) -> List[Dict]:
    calls: List[Dict] = []

    def _edit(chat_id, message_id, text, reply_markup=None):
        calls.append({"chat_id": chat_id, "message_id": message_id, "text": text})
        return {"ok": True}

    monkeypatch.setattr(bot_mod.telegram_publisher, "edit_message", _edit)
    return calls


def _capture_answer_cb(monkeypatch: pytest.MonkeyPatch, publisher_mod) -> List[Dict]:
    calls: List[Dict] = []

    def _answer(callback_query_id, text="", show_alert=False):
        calls.append({"id": callback_query_id, "text": text, "show_alert": show_alert})
        return {"ok": True}

    monkeypatch.setattr(publisher_mod, "answer_callback_query", _answer)
    return calls


# ===========================================================================
# 1. STALE GENERATION — APP: callback with an outdated generation number
# ===========================================================================

class TestStaleGenerationCallbackRecovery:

    def test_stale_app_callback_returns_ack_text(
        self,
        canonical_runtime_root: Path,
        fresh_imports,
        monkeypatch: pytest.MonkeyPatch,
    ):
        """Stale generation APP: callback must return callback_ack_text."""
        monkeypatch.setenv("OWNER_TELEGRAM_ID", "7001")
        bot = fresh_imports("core.bot_service")
        nav = fresh_imports("core.telegram_app_nav")
        _capture_send(monkeypatch, bot)
        _capture_edit(monkeypatch, bot)

        # Start a session so generation 1 is current.
        nav.begin_navigation_generation(7001, 7001)
        # Advance to generation 2; generation 1 is now stale.
        nav.begin_navigation_generation(7001, 7001)

        stale_data = "APP:1:STATUS"  # generation=1, current=2
        result = bot.process_update(_app_callback_update(7001, 7001, stale_data))

        assert result is not None, "Stale APP: callback must return a result dict"
        assert "callback_ack_text" in result, "Result must contain callback_ack_text"
        assert result["callback_ack_text"], "callback_ack_text must not be empty"

    def test_stale_app_callback_renders_home_not_dead_end(
        self,
        canonical_runtime_root: Path,
        fresh_imports,
        monkeypatch: pytest.MonkeyPatch,
    ):
        """Stale generation APP: callback must still render the Home page (no dead end)."""
        monkeypatch.setenv("OWNER_TELEGRAM_ID", "7002")
        bot = fresh_imports("core.bot_service")
        nav = fresh_imports("core.telegram_app_nav")
        sends = _capture_send(monkeypatch, bot)
        edits = _capture_edit(monkeypatch, bot)

        nav.begin_navigation_generation(7002, 7002)
        nav.begin_navigation_generation(7002, 7002)

        result = bot.process_update(_app_callback_update(7002, 7002, "APP:1:HELP"))

        assert result is not None
        assert result.get("callback_ack_text")
        # Must have produced a page (edit or send) — not a dead end.
        assert len(sends) + len(edits) >= 1

    def test_stale_app_callback_does_not_contaminate_with_no_generation(
        self,
        canonical_runtime_root: Path,
        fresh_imports,
        monkeypatch: pytest.MonkeyPatch,
    ):
        """APP: callback without a generation number is never treated as stale."""
        monkeypatch.setenv("OWNER_TELEGRAM_ID", "7003")
        bot = fresh_imports("core.bot_service")
        nav = fresh_imports("core.telegram_app_nav")
        _capture_send(monkeypatch, bot)
        _capture_edit(monkeypatch, bot)

        nav.begin_navigation_generation(7003, 7003)
        nav.begin_navigation_generation(7003, 7003)

        # No generation number in callback data.
        result = bot.process_update(_app_callback_update(7003, 7003, "APP:STATUS"))

        # Must NOT be classified as stale.
        assert result is None or not result.get("callback_ack_text"), (
            "APP: callback without generation number must not produce stale ack text"
        )

    def test_stale_admin_app_callback_returns_ack_text(
        self,
        canonical_runtime_root: Path,
        fresh_imports,
        monkeypatch: pytest.MonkeyPatch,
    ):
        """Stale generation APP:ADMIN callback must also return callback_ack_text."""
        monkeypatch.setenv("OWNER_TELEGRAM_ID", "7004")
        bot = fresh_imports("core.bot_service")
        nav = fresh_imports("core.telegram_app_nav")
        _capture_send(monkeypatch, bot)
        _capture_edit(monkeypatch, bot)

        nav.begin_navigation_generation(7004, 7004)
        nav.begin_navigation_generation(7004, 7004)

        result = bot.process_update(_app_callback_update(7004, 7004, "APP:1:ADMIN"))

        assert result is not None
        assert "callback_ack_text" in result
        assert result["callback_ack_text"]


# ===========================================================================
# 2. UNKNOWN CALLBACK — data that matches no known prefix
# ===========================================================================

class TestUnknownCallbackRecovery:

    def test_unknown_callback_returns_ack_text(
        self,
        canonical_runtime_root: Path,
        fresh_imports,
        monkeypatch: pytest.MonkeyPatch,
    ):
        """Unrecognised callback data must return callback_ack_text."""
        monkeypatch.setenv("ADMIN_CONTROL_CHAT_ID", "-9001")
        bot = fresh_imports("core.bot_service")
        monkeypatch.setattr(bot, "ADMIN_CONTROL_CHAT_ID", -9001)
        _capture_send(monkeypatch, bot)
        _capture_edit(monkeypatch, bot)

        result = bot.process_update(
            _app_callback_update(-9001, 500, "COMPLETELY_UNKNOWN_GARBAGE_XYZ123",
                                 chat_type="supergroup", thread_id=99)
        )

        assert result is not None
        assert "callback_ack_text" in result
        assert result["callback_ack_text"]

    def test_unknown_callback_does_not_overwrite_nav_message(
        self,
        canonical_runtime_root: Path,
        fresh_imports,
        monkeypatch: pytest.MonkeyPatch,
    ):
        """Unrecognised callback must NOT edit the active navigation message."""
        monkeypatch.setenv("ADMIN_CONTROL_CHAT_ID", "-9002")
        bot = fresh_imports("core.bot_service")
        monkeypatch.setattr(bot, "ADMIN_CONTROL_CHAT_ID", -9002)
        sends = _capture_send(monkeypatch, bot)
        edits = _capture_edit(monkeypatch, bot)

        bot.process_update(
            _app_callback_update(-9002, 501, "NO_MATCHING_PREFIX",
                                 chat_type="supergroup", thread_id=77)
        )

        assert sends == [], "Unknown callback must not send a new message"
        assert edits == [], "Unknown callback must not edit the navigation message"

    def test_handle_callback_unknown_has_toast_flag(
        self,
        canonical_runtime_root: Path,
        fresh_imports,
        monkeypatch: pytest.MonkeyPatch,
    ):
        """handle_callback() must mark unknown responses with __toast__: True."""
        monkeypatch.setenv("ADMIN_CONTROL_CHAT_ID", "-9003")
        bot = fresh_imports("core.bot_service")
        monkeypatch.setattr(bot, "ADMIN_CONTROL_CHAT_ID", -9003)

        result = bot.handle_callback(chat_id=-9003, user_id=1, data="UNKNOWN_CB_DATA_ZZZ")
        assert result.get("__toast__") is True
        assert result.get("text"), "Unknown response must have text"


# ===========================================================================
# 3. RETIRED CALLBACK — legacy admin-panel buttons from before BATCH-05
# ===========================================================================

class TestRetiredCallbackRecovery:

    _RETIRED_SAMPLES = [
        "ADMIN_STATUS",
        "ADMIN_SET_BUFFER",
        "BUFFER_SMALL",
        "SYM_TOGGLE:EURUSD",
        "DOC:some_file.md",
    ]

    def test_retired_callback_returns_ack_text(
        self,
        canonical_runtime_root: Path,
        fresh_imports,
        monkeypatch: pytest.MonkeyPatch,
    ):
        """Retired callback data must return callback_ack_text."""
        monkeypatch.setenv("ADMIN_CONTROL_CHAT_ID", "-8001")
        bot = fresh_imports("core.bot_service")
        monkeypatch.setattr(bot, "ADMIN_CONTROL_CHAT_ID", -8001)
        _capture_send(monkeypatch, bot)
        _capture_edit(monkeypatch, bot)

        result = bot.process_update(
            _app_callback_update(-8001, 200, "ADMIN_STATUS",
                                 chat_type="supergroup", thread_id=55)
        )

        assert result is not None
        assert "callback_ack_text" in result
        assert result["callback_ack_text"]

    def test_retired_callback_does_not_overwrite_nav_message(
        self,
        canonical_runtime_root: Path,
        fresh_imports,
        monkeypatch: pytest.MonkeyPatch,
    ):
        """Retired callback must NOT edit the active navigation message."""
        monkeypatch.setenv("ADMIN_CONTROL_CHAT_ID", "-8002")
        bot = fresh_imports("core.bot_service")
        monkeypatch.setattr(bot, "ADMIN_CONTROL_CHAT_ID", -8002)
        sends = _capture_send(monkeypatch, bot)
        edits = _capture_edit(monkeypatch, bot)

        bot.process_update(
            _app_callback_update(-8002, 201, "BUFFER_LARGE",
                                 chat_type="supergroup", thread_id=55)
        )

        assert sends == [], "Retired callback must not send a new message"
        assert edits == [], "Retired callback must not edit the navigation message"

    def test_handle_callback_retired_has_toast_flag(
        self,
        canonical_runtime_root: Path,
        fresh_imports,
        monkeypatch: pytest.MonkeyPatch,
    ):
        """handle_callback() must mark retired responses with __toast__: True."""
        monkeypatch.setenv("ADMIN_CONTROL_CHAT_ID", "-8003")
        bot = fresh_imports("core.bot_service")
        monkeypatch.setattr(bot, "ADMIN_CONTROL_CHAT_ID", -8003)

        for data in self._RETIRED_SAMPLES:
            result = bot.handle_callback(chat_id=-8003, user_id=1, data=data)
            assert result.get("__toast__") is True, (
                f"Retired callback '{data}' must have __toast__: True. Got: {result}"
            )
            assert result.get("text"), f"Retired callback '{data}' must have text"


# ===========================================================================
# 4. UNAUTHORIZED ADMIN_NAV: — callback from wrong chat/thread
# ===========================================================================

class TestUnauthorizedAdminNavCallbackRecovery:

    def test_unauthorized_admin_nav_callback_returns_ack_text(
        self,
        canonical_runtime_root: Path,
        fresh_imports,
        monkeypatch: pytest.MonkeyPatch,
    ):
        """Unauthorized ADMIN_NAV: callback must return callback_ack_text."""
        monkeypatch.setenv("OWNER_TELEGRAM_ID", "6001")
        monkeypatch.setenv("ADMIN_CONTROL_CHAT_ID", "-6001")
        monkeypatch.setenv("ADMIN_CONTROL_THREAD_ID", "100")
        bot = fresh_imports("core.bot_service")
        _capture_send(monkeypatch, bot)
        _capture_edit(monkeypatch, bot)

        # Non-owner user 6002 in the admin chat but wrong thread (42 ≠ 100).
        result = bot.process_update(
            _app_callback_update(-6001, 6002, "ADMIN_NAV:HOME",
                                 chat_type="supergroup", thread_id=42)
        )

        assert result is not None
        assert "callback_ack_text" in result
        assert result["callback_ack_text"]
        assert "denied" in result["callback_ack_text"].lower()

    def test_unauthorized_admin_nav_callback_does_not_overwrite_nav_message(
        self,
        canonical_runtime_root: Path,
        fresh_imports,
        monkeypatch: pytest.MonkeyPatch,
    ):
        """Unauthorized ADMIN_NAV: callback must NOT edit or send any message."""
        monkeypatch.setenv("OWNER_TELEGRAM_ID", "6001")
        monkeypatch.setenv("ADMIN_CONTROL_CHAT_ID", "-6001")
        monkeypatch.setenv("ADMIN_CONTROL_THREAD_ID", "100")
        bot = fresh_imports("core.bot_service")
        sends = _capture_send(monkeypatch, bot)
        edits = _capture_edit(monkeypatch, bot)

        bot.process_update(
            _app_callback_update(-6001, 6002, "ADMIN_NAV:OPERATIONS",
                                 chat_type="supergroup", thread_id=42)
        )

        assert sends == [], "Unauthorized ADMIN_NAV: callback must not send a message"
        assert edits == [], "Unauthorized ADMIN_NAV: callback must not edit the navigation message"

    def test_multiple_unauthorized_callbacks_accumulate_no_messages(
        self,
        canonical_runtime_root: Path,
        fresh_imports,
        monkeypatch: pytest.MonkeyPatch,
    ):
        """Multiple unauthorized ADMIN_NAV: callbacks must not accumulate messages."""
        monkeypatch.setenv("OWNER_TELEGRAM_ID", "6001")
        monkeypatch.setenv("ADMIN_CONTROL_CHAT_ID", "-6001")
        monkeypatch.setenv("ADMIN_CONTROL_THREAD_ID", "100")
        bot = fresh_imports("core.bot_service")
        sends = _capture_send(monkeypatch, bot)
        edits = _capture_edit(monkeypatch, bot)

        for action in ("HOME", "OPERATIONS", "SYSHEALTH", "RESEARCH"):
            bot.process_update(
                _app_callback_update(-6001, 6002, f"ADMIN_NAV:{action}",
                                     chat_type="supergroup", thread_id=42)
            )

        assert sends == []
        assert edits == []


# ===========================================================================
# 5. telegram_updates integration — answerCallbackQuery delivery
# ===========================================================================

class TestCallbackRecoveryAckDelivery:

    def test_stale_callback_triggers_answer_callback_query_with_text(
        self,
        canonical_runtime_root: Path,
        fresh_imports,
        monkeypatch: pytest.MonkeyPatch,
    ):
        """telegram_updates must call answer_callback_query with text for stale callbacks."""
        monkeypatch.setenv("OWNER_TELEGRAM_ID", "5001")
        updates = fresh_imports("runtime.telegram_updates")
        bot = fresh_imports("core.bot_service")
        nav = fresh_imports("core.telegram_app_nav")
        publisher = fresh_imports("core.telegram_publisher")

        _capture_send(monkeypatch, bot)
        _capture_edit(monkeypatch, bot)
        acks = _capture_answer_cb(monkeypatch, publisher)

        monkeypatch.setattr(updates, "bot_service", bot)
        monkeypatch.setattr(updates, "outcome_service", bot.outcome_service)
        monkeypatch.setattr(updates, "telegram_publisher", publisher)

        nav.begin_navigation_generation(5001, 5001)
        nav.begin_navigation_generation(5001, 5001)

        updates.process_update(
            _app_callback_update(5001, 5001, "APP:1:STATUS", callback_id="ack-stale-1")
        )

        assert acks, "answer_callback_query must be called for stale callback"
        assert acks[0]["id"] == "ack-stale-1"
        assert acks[0]["text"], "answer_callback_query must carry ack text for stale callback"

    def test_unauthorized_admin_nav_triggers_answer_callback_query_with_text(
        self,
        canonical_runtime_root: Path,
        fresh_imports,
        monkeypatch: pytest.MonkeyPatch,
    ):
        """telegram_updates must call answer_callback_query with text for unauthorized callbacks."""
        monkeypatch.setenv("OWNER_TELEGRAM_ID", "5001")
        monkeypatch.setenv("ADMIN_CONTROL_CHAT_ID", "-5001")
        monkeypatch.setenv("ADMIN_CONTROL_THREAD_ID", "200")
        updates = fresh_imports("runtime.telegram_updates")
        bot = fresh_imports("core.bot_service")
        publisher = fresh_imports("core.telegram_publisher")

        _capture_send(monkeypatch, bot)
        _capture_edit(monkeypatch, bot)
        acks = _capture_answer_cb(monkeypatch, publisher)

        monkeypatch.setattr(updates, "bot_service", bot)
        monkeypatch.setattr(updates, "outcome_service", bot.outcome_service)
        monkeypatch.setattr(updates, "telegram_publisher", publisher)

        updates.process_update(
            _app_callback_update(-5001, 9999, "ADMIN_NAV:HOME",
                                 callback_id="ack-unauth-1",
                                 chat_type="supergroup", thread_id=42)
        )

        assert acks, "answer_callback_query must be called for unauthorized ADMIN_NAV: callback"
        assert acks[0]["id"] == "ack-unauth-1"
        assert acks[0]["text"], "answer_callback_query must carry ack text"

    def test_normal_app_callback_uses_empty_ack(
        self,
        canonical_runtime_root: Path,
        fresh_imports,
        monkeypatch: pytest.MonkeyPatch,
    ):
        """Normal APP: callbacks must use an empty ack (no toast text)."""
        monkeypatch.setenv("OWNER_TELEGRAM_ID", "5002")
        updates = fresh_imports("runtime.telegram_updates")
        bot = fresh_imports("core.bot_service")
        publisher = fresh_imports("core.telegram_publisher")

        sends: List[Dict] = []

        def _send(chat_id, text, reply_markup=None, thread_id=None):
            sends.append({"text": text})
            return {"ok": True, "result": {"message_id": 9999}}

        monkeypatch.setattr(bot.telegram_publisher, "send_message", _send)
        monkeypatch.setattr(bot.telegram_publisher, "edit_message",
                            lambda *a, **kw: {"ok": True})

        acks = _capture_answer_cb(monkeypatch, publisher)

        monkeypatch.setattr(updates, "bot_service", bot)
        monkeypatch.setattr(updates, "outcome_service", bot.outcome_service)
        monkeypatch.setattr(updates, "telegram_publisher", publisher)

        updates.process_update(
            _app_callback_update(5002, 5002, "APP:STATUS", callback_id="ack-normal-1")
        )

        # There may be an empty ack via _ack_callback, but text must be empty.
        if acks:
            assert acks[0]["text"] == "", (
                "Normal APP: callback must not carry toast text in ack"
            )
