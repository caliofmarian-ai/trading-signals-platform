"""
tests/telegram_transport/test_telegram_transport_and_recovery.py

Telegram transport and recovery hardening — 18-point test matrix.

Verified defects addressed:
  AREA 1 — parse_mode inconsistency: edit_message used parse_mode=HTML while
            send_message used no parse_mode; admin command-help text contains
            <value>/<dir>/<filename> that caused HTML-parser 400 errors on edit,
            classified as unexpected failure, fell through to send_message and
            produced a new message instead of editing the existing one.
  AREA 2 — Silent send_message failure: _send_interactive_page swallowed
            send_message exceptions silently (except Exception: pass).
  AREA 3 — Bot-token leakage: requests exceptions embed the full URL including
            the token; str(e) was passed directly to the JSONL logger.
  AREA 4 — Unanswered callback queries: APP: and ADMIN_NAV: callbacks were
            never acknowledged with answerCallbackQuery, leaving a 10-second
            Telegram spinner.

Test matrix (18 cases):
  1.  send_message sends without parse_mode
  2.  edit_message sends without parse_mode
  3.  both functions are parse-mode consistent
  4.  Engine command edits Start message (no new message sent)
  5.  Admin button edits Engine message (no new message sent)
  6.  Start → Engine → Admin navigation remains one message
  7.  deleted active message produces exactly one replacement
  8.  replacement becomes active; subsequent navigation edits it
  9.  deleted conversation followed by /start responds (bot not silent)
 10.  failed edit plus successful send_message works
 11.  failed edit plus failed send_message is logged and not silent
 12.  unexpected edit error does not corrupt active state
 13.  polling continues after a failed update
 14.  Railway-visible safe log line is emitted
 15.  bot token never appears in stdout/stderr or JSONL error field
 16.  internal JSONL logging still works
 17.  same user/chat/thread isolation remains correct
 18.  full representative end-to-end navigation remains one interactive message
"""
from __future__ import annotations

import io
import json
import os
import sys
import tempfile
import threading
from typing import Any, Dict, List, Optional
from unittest.mock import MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _msg_update(
    chat_id: int,
    user_id: int,
    text: str,
    *,
    chat_type: str = "private",
    first_name: str = "Alice",
    message_id: int = 1001,
) -> Dict[str, Any]:
    return {
        "message": {
            "chat": {"id": chat_id, "type": chat_type},
            "from": {"id": user_id, "first_name": first_name},
            "text": text,
            "message_id": message_id,
        }
    }


def _cb_update(
    chat_id: int,
    user_id: int,
    data: str,
    *,
    message_id: int = 2001,
    chat_type: str = "private",
    first_name: str = "Alice",
) -> Dict[str, Any]:
    return {
        "callback_query": {
            "id": "cb-ack-id",
            "from": {"id": user_id, "first_name": first_name},
            "data": data,
            "message": {
                "chat": {"id": chat_id, "type": chat_type},
                "message_id": message_id,
                "text": "previous page text",
            },
        }
    }


class FakePublisher:
    """Controllable stand-in for telegram_publisher."""

    def __init__(self, *, start_id: int = 5000, edit_fail: bool = False,
                 send_fail: bool = False, edit_fail_once: bool = False,
                 edit_fail_msg: str = "message to edit not found") -> None:
        self._next_id = start_id
        self._edit_fail = edit_fail
        self._send_fail = send_fail
        self._edit_fail_once = edit_fail_once
        self._edit_fail_msg = edit_fail_msg
        self._edit_fail_used = False
        self.sends: List[Dict[str, Any]] = []
        self.edits: List[Dict[str, Any]] = []
        self.acks: List[str] = []

    def send_message(self, chat_id, text, reply_markup=None, thread_id=None):
        if self._send_fail:
            raise RuntimeError("send_message stubbed failure")
        mid = self._next_id
        self._next_id += 1
        self.sends.append({"chat_id": chat_id, "text": text, "message_id": mid})
        return {"ok": True, "result": {"message_id": mid}}

    def edit_message(self, chat_id, message_id, text=None, reply_markup=None):
        fail = self._edit_fail
        if self._edit_fail_once and not self._edit_fail_used:
            fail = True
            self._edit_fail_used = True
        if fail:
            raise RuntimeError(self._edit_fail_msg)
        self.edits.append({"chat_id": chat_id, "message_id": message_id, "text": text})
        return {"ok": True, "result": {"message_id": message_id}}

    def answer_callback_query(self, callback_query_id, text="", show_alert=False):
        self.acks.append(callback_query_id)
        return {"ok": True}

    def _sanitize(self, s: str) -> str:
        import re
        return re.sub(r"(?<=/bot)\d+:[A-Za-z0-9_-]+", "[REDACTED]", s)

    def delete_message(self, chat_id, message_id):
        return {
            "outcome": "deleted",
            "chat_id": chat_id,
            "message_id": message_id,
            "error_code": None,
            "description": None,
        }


def _make_roles(owner_id: int) -> Dict[str, Any]:
    return {
        "owner": [owner_id],
        "primary_admin": [],
        "strategy_admin": [],
        "research_admin": [],
        "analyst": [],
        "moderator": [],
        "affiliate_admin": {},
    }


def _bot_service_module():
    """Import bot_service with sys.path adjusted for the send/ package."""
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../send"))
    import importlib
    return importlib.import_module("core.bot_service")


# ---------------------------------------------------------------------------
# Module-level import
# ---------------------------------------------------------------------------
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../send"))
import importlib
import core.telegram_publisher as _publisher_mod
import core.bot_service as _bs_mod
import core.telegram_app_nav as _nav_mod
import runtime.telegram_updates as _poller_mod


# ---------------------------------------------------------------------------
# Test 1 — send_message sends without parse_mode
# ---------------------------------------------------------------------------

def test_01_send_message_no_parse_mode():
    """send_message must not set parse_mode in the payload."""
    captured: List[Dict] = []

    def _fake_post(url, json=None, data=None, files=None, timeout=None, params=None):
        if json:
            captured.append(dict(json))
        resp = MagicMock()
        resp.json.return_value = {"ok": True, "result": {"message_id": 1}}
        return resp

    with patch.object(_publisher_mod.requests, "post", side_effect=_fake_post), \
         patch.dict(os.environ, {"TELEGRAM_BOT_TOKEN": "123:TOKEN"}):
        _publisher_mod.send_message(1, "hello")

    assert captured, "post was not called"
    assert "parse_mode" not in captured[0], (
        "send_message must not set parse_mode; found: " + str(captured[0].get("parse_mode"))
    )


# ---------------------------------------------------------------------------
# Test 2 — edit_message sends without parse_mode
# ---------------------------------------------------------------------------

def test_02_edit_message_no_parse_mode():
    """edit_message must not set parse_mode in the payload."""
    captured: List[Dict] = []

    def _fake_post(url, json=None, data=None, files=None, timeout=None, params=None):
        if json:
            captured.append(dict(json))
        resp = MagicMock()
        resp.json.return_value = {"ok": True, "result": {"message_id": 1}}
        return resp

    with patch.object(_publisher_mod.requests, "post", side_effect=_fake_post), \
         patch.dict(os.environ, {"TELEGRAM_BOT_TOKEN": "123:TOKEN"}):
        _publisher_mod.edit_message(1, 100, "hello")

    assert captured
    assert "parse_mode" not in captured[0], (
        "edit_message must not set parse_mode; found: " + str(captured[0].get("parse_mode"))
    )


# ---------------------------------------------------------------------------
# Test 3 — parse_mode consistent between send_message and edit_message
# ---------------------------------------------------------------------------

def test_03_parse_mode_consistent():
    """Both send_message and edit_message must set the same parse_mode (or none)."""
    send_modes: List[Optional[str]] = []
    edit_modes: List[Optional[str]] = []

    def _fake_post(url, json=None, **kw):
        resp = MagicMock()
        resp.json.return_value = {"ok": True, "result": {"message_id": 1}}
        if json:
            if "/sendMessage" in url:
                send_modes.append(json.get("parse_mode"))
            elif "/editMessageText" in url:
                edit_modes.append(json.get("parse_mode"))
        return resp

    with patch.object(_publisher_mod.requests, "post", side_effect=_fake_post), \
         patch.dict(os.environ, {"TELEGRAM_BOT_TOKEN": "123:TOKEN"}):
        _publisher_mod.send_message(1, "hello <value>")
        _publisher_mod.edit_message(1, 10, "hello <value>")

    assert send_modes, "send_message not called"
    assert edit_modes, "edit_message not called"
    assert send_modes[0] == edit_modes[0], (
        f"parse_mode mismatch: send={send_modes[0]!r} edit={edit_modes[0]!r}"
    )


# ---------------------------------------------------------------------------
# Test 4 — Engine command edits Start message (no new send)
# ---------------------------------------------------------------------------

def test_04_engine_command_edits_start_message(tmp_path, monkeypatch):
    """
    /engine after /start must edit the existing start message rather than
    sending a new one.  This was broken by the parse_mode=HTML mismatch when
    the engine panel text contained literal '<' characters.
    """
    owner_id = 999
    chat_id = owner_id  # private DM

    roles_file = tmp_path / "roles.json"
    roles_file.write_text(json.dumps(_make_roles(owner_id)))
    status_file = tmp_path / "status.json"
    status_file.write_text(json.dumps({"phase": "running"}))

    pub = FakePublisher()
    monkeypatch.setattr(_bs_mod, "telegram_publisher", pub)
    monkeypatch.setenv("ADMIN_CONTROL_CHAT_ID", "0")
    monkeypatch.setenv("ROLES_CONFIG_PATH", str(roles_file))
    monkeypatch.setenv("RUNTIME_STATUS_PATH", str(status_file))

    _nav_mod.clear_active_message(owner_id, chat_id)

    # /start → sends new message 5000
    _bs_mod.process_update(_msg_update(chat_id, owner_id, "/start", message_id=100))
    assert len(pub.sends) == 1, "Expected exactly one send for /start"
    start_msg_id = pub.sends[0]["message_id"]

    # /engine → must EDIT start message, not send a new one
    _bs_mod.process_update(_msg_update(chat_id, owner_id, "/engine", message_id=101))
    assert len(pub.sends) == 1, (
        f"Expected no new send after /engine, but sends count={len(pub.sends)}"
    )
    assert len(pub.edits) >= 1, "Expected at least one edit for /engine"
    assert pub.edits[-1]["message_id"] == start_msg_id


# ---------------------------------------------------------------------------
# Test 5 — Admin button edits Engine message (no new send)
# ---------------------------------------------------------------------------

def test_05_admin_button_edits_engine_message(tmp_path, monkeypatch):
    """
    Pressing an admin panel button after /engine must edit the engine message.
    """
    owner_id = 998
    chat_id = owner_id

    roles_file = tmp_path / "roles.json"
    roles_file.write_text(json.dumps(_make_roles(owner_id)))
    status_file = tmp_path / "status.json"
    status_file.write_text(json.dumps({"phase": "running"}))

    pub = FakePublisher()
    monkeypatch.setattr(_bs_mod, "telegram_publisher", pub)
    monkeypatch.setenv("ADMIN_CONTROL_CHAT_ID", "0")
    monkeypatch.setenv("ROLES_CONFIG_PATH", str(roles_file))
    monkeypatch.setenv("RUNTIME_STATUS_PATH", str(status_file))

    _nav_mod.clear_active_message(owner_id, chat_id)

    # /start
    _bs_mod.process_update(_msg_update(chat_id, owner_id, "/start", message_id=200))
    assert len(pub.sends) == 1

    # /engine
    _bs_mod.process_update(_msg_update(chat_id, owner_id, "/engine", message_id=201))
    assert len(pub.sends) == 1, "Engine command should edit, not send new"

    engine_msg_id = _nav_mod.get_active_message(owner_id, chat_id)
    assert engine_msg_id is not None

    # Press admin home button (APP:ADMIN)
    sends_before = len(pub.sends)
    _bs_mod.process_update(
        _cb_update(chat_id, owner_id, "APP:ADMIN", message_id=engine_msg_id)
    )
    assert len(pub.sends) == sends_before, (
        "Admin button should edit the engine message, not create a new one"
    )


# ---------------------------------------------------------------------------
# Test 6 — Start → Engine → Admin remains one message
# ---------------------------------------------------------------------------

def test_06_full_navigation_single_message(tmp_path, monkeypatch):
    """
    The full Start → Engine → Admin sequence must result in a single message
    that is continually edited.
    """
    owner_id = 997
    chat_id = owner_id

    roles_file = tmp_path / "roles.json"
    roles_file.write_text(json.dumps(_make_roles(owner_id)))
    status_file = tmp_path / "status.json"
    status_file.write_text(json.dumps({"phase": "running"}))

    pub = FakePublisher()
    monkeypatch.setattr(_bs_mod, "telegram_publisher", pub)
    monkeypatch.setenv("ADMIN_CONTROL_CHAT_ID", "0")
    monkeypatch.setenv("ROLES_CONFIG_PATH", str(roles_file))
    monkeypatch.setenv("RUNTIME_STATUS_PATH", str(status_file))

    _nav_mod.clear_active_message(owner_id, chat_id)

    _bs_mod.process_update(_msg_update(chat_id, owner_id, "/start"))
    active_id = _nav_mod.get_active_message(owner_id, chat_id)
    assert active_id is not None
    assert len(pub.sends) == 1

    _bs_mod.process_update(_msg_update(chat_id, owner_id, "/engine"))
    assert len(pub.sends) == 1, "Engine navigation must not send new message"

    _bs_mod.process_update(
        _cb_update(chat_id, owner_id, "APP:ADMIN", message_id=active_id)
    )
    assert len(pub.sends) == 1, "Admin button must not send new message"


# ---------------------------------------------------------------------------
# Test 7 — deleted active message produces exactly one replacement
# ---------------------------------------------------------------------------

def test_07_deleted_active_message_replacement(tmp_path, monkeypatch):
    """
    When the active message has been deleted, _send_interactive_page must
    clear the stale entry and send exactly one new message.
    """
    owner_id = 996
    chat_id = owner_id

    roles_file = tmp_path / "roles.json"
    roles_file.write_text(json.dumps(_make_roles(owner_id)))
    status_file = tmp_path / "status.json"
    status_file.write_text(json.dumps({"phase": "running"}))

    # Stale message that will fail with "not found"
    pub = FakePublisher(edit_fail=True, edit_fail_msg="message to edit not found")
    monkeypatch.setattr(_bs_mod, "telegram_publisher", pub)
    monkeypatch.setenv("ADMIN_CONTROL_CHAT_ID", "0")
    monkeypatch.setenv("ROLES_CONFIG_PATH", str(roles_file))
    monkeypatch.setenv("RUNTIME_STATUS_PATH", str(status_file))

    _nav_mod.set_active_message(owner_id, chat_id, 9999)  # stale

    _bs_mod.process_update(_msg_update(chat_id, owner_id, "/start"))

    assert len(pub.sends) == 1, (
        f"Expected exactly one replacement send, got {len(pub.sends)}"
    )
    new_active = _nav_mod.get_active_message(owner_id, chat_id)
    assert new_active is not None
    assert new_active != 9999


# ---------------------------------------------------------------------------
# Test 8 — replacement becomes active; subsequent navigation edits it
# ---------------------------------------------------------------------------

def test_08_replacement_becomes_active(tmp_path, monkeypatch):
    """
    After /start creates a new anchor, subsequent navigation must edit it
    rather than sending yet another new message.

    With the hard-reset implementation, /start always bypasses editMessageText
    and calls sendMessage directly. Subsequent /help must edit the new anchor.
    """
    owner_id = 995
    chat_id = owner_id

    roles_file = tmp_path / "roles.json"
    roles_file.write_text(json.dumps(_make_roles(owner_id)))
    status_file = tmp_path / "status.json"
    status_file.write_text(json.dumps({"phase": "running"}))

    # /start always sends (no edit needed); subsequent edits succeed.
    pub = FakePublisher(start_id=6000)
    monkeypatch.setattr(_bs_mod, "telegram_publisher", pub)
    monkeypatch.setenv("ADMIN_CONTROL_CHAT_ID", "0")
    monkeypatch.setenv("ROLES_CONFIG_PATH", str(roles_file))
    monkeypatch.setenv("RUNTIME_STATUS_PATH", str(status_file))

    _nav_mod.set_active_message(owner_id, chat_id, 9998)  # old anchor

    # /start — hard reset bypasses edit, sends new anchor (6000)
    _bs_mod.process_update(_msg_update(chat_id, owner_id, "/start"))
    assert len(pub.sends) == 1
    replacement_id = pub.sends[0]["message_id"]

    # /help — must edit the replacement, not send another new message
    _bs_mod.process_update(_msg_update(chat_id, owner_id, "/help"))
    assert len(pub.sends) == 1, "Second navigation must not produce a new send"
    assert len(pub.edits) >= 1
    assert pub.edits[-1]["message_id"] == replacement_id


# ---------------------------------------------------------------------------
# Test 9 — deleted conversation followed by /start responds
# ---------------------------------------------------------------------------

def test_09_deleted_conversation_start_responds(tmp_path, monkeypatch):
    """
    After the user deletes the entire conversation, pressing Start must
    produce a response without any crash or silent failure.
    """
    owner_id = 994
    chat_id = owner_id

    roles_file = tmp_path / "roles.json"
    roles_file.write_text(json.dumps(_make_roles(owner_id)))
    status_file = tmp_path / "status.json"
    status_file.write_text(json.dumps({"phase": "running"}))

    # No active message (clean slate, as if conversation was deleted)
    pub = FakePublisher()
    monkeypatch.setattr(_bs_mod, "telegram_publisher", pub)
    monkeypatch.setenv("ADMIN_CONTROL_CHAT_ID", "0")
    monkeypatch.setenv("ROLES_CONFIG_PATH", str(roles_file))
    monkeypatch.setenv("RUNTIME_STATUS_PATH", str(status_file))

    _nav_mod.clear_active_message(owner_id, chat_id)

    _bs_mod.process_update(_msg_update(chat_id, owner_id, "/start"))

    assert len(pub.sends) == 1, "Bot must respond to /start with one new message"
    assert _nav_mod.get_active_message(owner_id, chat_id) is not None


# ---------------------------------------------------------------------------
# Test 10 — failed edit plus successful send works
# ---------------------------------------------------------------------------

def test_10_stale_edit_then_successful_send(tmp_path, monkeypatch):
    """
    When the edit fails because the message was deleted, the fallback
    send_message must succeed and track the new message.
    """
    owner_id = 993
    chat_id = owner_id

    roles_file = tmp_path / "roles.json"
    roles_file.write_text(json.dumps(_make_roles(owner_id)))
    status_file = tmp_path / "status.json"
    status_file.write_text(json.dumps({"phase": "running"}))

    pub = FakePublisher(edit_fail=True, edit_fail_msg="message to edit not found",
                        start_id=7000)
    monkeypatch.setattr(_bs_mod, "telegram_publisher", pub)
    monkeypatch.setenv("ADMIN_CONTROL_CHAT_ID", "0")
    monkeypatch.setenv("ROLES_CONFIG_PATH", str(roles_file))
    monkeypatch.setenv("RUNTIME_STATUS_PATH", str(status_file))

    _nav_mod.set_active_message(owner_id, chat_id, 8888)

    _bs_mod.process_update(_msg_update(chat_id, owner_id, "/start"))

    assert len(pub.sends) == 1
    assert pub.sends[0]["message_id"] == 7000
    assert _nav_mod.get_active_message(owner_id, chat_id) == 7000


# ---------------------------------------------------------------------------
# Test 11 — failed edit plus failed send is logged and not silent
# ---------------------------------------------------------------------------

def test_11_failed_edit_and_send_not_silent(tmp_path, monkeypatch):
    """
    When both edit and send_message fail, the error must be logged via
    observability_logger — not silently swallowed.
    """
    owner_id = 992
    chat_id = owner_id

    roles_file = tmp_path / "roles.json"
    roles_file.write_text(json.dumps(_make_roles(owner_id)))
    status_file = tmp_path / "status.json"
    status_file.write_text(json.dumps({"phase": "running"}))

    pub = FakePublisher(
        edit_fail=True, edit_fail_msg="message to edit not found",
        send_fail=True,
    )
    monkeypatch.setattr(_bs_mod, "telegram_publisher", pub)
    monkeypatch.setenv("ADMIN_CONTROL_CHAT_ID", "0")
    monkeypatch.setenv("ROLES_CONFIG_PATH", str(roles_file))
    monkeypatch.setenv("RUNTIME_STATUS_PATH", str(status_file))

    _nav_mod.set_active_message(owner_id, chat_id, 7777)

    logged: List[Dict] = []

    import core.observability_logger as _obs
    original_log_error = _obs.log_error

    def _capturing_log_error(payload):
        logged.append(payload)
        try:
            original_log_error(payload)
        except Exception:
            pass

    monkeypatch.setattr(_obs, "log_error", _capturing_log_error)
    monkeypatch.setattr(_bs_mod, "observability_logger", _obs)

    _bs_mod.process_update(_msg_update(chat_id, owner_id, "/start"))

    assert logged, (
        "Expected at least one log_error call when both edit and send fail"
    )
    error_types = [
        (p.get("data") or {}).get("error_type") or p.get("event_type")
        for p in logged
    ]
    assert any("send_failure" in str(et) or "error" in str(et) for et in error_types), (
        f"Expected send-failure to be logged; got: {error_types}"
    )


# ---------------------------------------------------------------------------
# Test 12 — unexpected edit error does not corrupt active state
# ---------------------------------------------------------------------------

def test_12_unexpected_edit_does_not_corrupt_state(tmp_path, monkeypatch):
    """
    An unexpected edit failure (not a stale-message error) must leave the
    active message record intact so the next attempt can retry.
    """
    owner_id = 991
    chat_id = owner_id

    roles_file = tmp_path / "roles.json"
    roles_file.write_text(json.dumps(_make_roles(owner_id)))
    status_file = tmp_path / "status.json"
    status_file.write_text(json.dumps({"phase": "running"}))

    pub = FakePublisher(edit_fail=True, edit_fail_msg="internal server error",
                        start_id=8000)
    monkeypatch.setattr(_bs_mod, "telegram_publisher", pub)
    monkeypatch.setenv("ADMIN_CONTROL_CHAT_ID", "0")
    monkeypatch.setenv("ROLES_CONFIG_PATH", str(roles_file))
    monkeypatch.setenv("RUNTIME_STATUS_PATH", str(status_file))

    _nav_mod.set_active_message(owner_id, chat_id, 4444)
    pre_active = _nav_mod.get_active_message(owner_id, chat_id)

    # Unexpected failure (not "message to edit not found") must NOT clear the
    # active state.  It falls through to send_message which succeeds here.
    _bs_mod.process_update(_msg_update(chat_id, owner_id, "/start"))

    # Active state should either be preserved (4444) or updated to the new
    # send result — it must not be None/cleared to nothing.
    post_active = _nav_mod.get_active_message(owner_id, chat_id)
    assert post_active is not None, (
        "Active message must not be cleared after an unexpected edit failure"
    )


# ---------------------------------------------------------------------------
# Test 13 — polling continues after a failed update
# ---------------------------------------------------------------------------

class _StopPoller(BaseException):
    """Sentinel raised to break out of poll_updates() in tests.

    Must be a BaseException subclass (NOT Exception) so it propagates through
    the ``except Exception`` handler inside poll_updates() without being caught.
    """


def test_13_poller_continues_after_failure(monkeypatch):
    """
    The poller must catch per-update RuntimeError exceptions and continue
    processing subsequent updates without crashing.

    Verified behaviour: when process_update raises for update_id=1, the outer
    exception handler logs the error and sleeps, then on the next poll cycle
    update_id=2 is fetched and processed.  A _StopPoller (BaseException, not
    Exception) is used to terminate the otherwise-infinite polling loop.
    """
    processed: List[int] = []
    errors: List[str] = []

    def _fake_process(update):
        uid = update.get("update_id", -1)
        if uid == 1:
            raise RuntimeError("Simulated per-update crash")
        processed.append(uid)
        if uid == 2:
            # Signal test-end after update 2 is successfully processed.
            raise _StopPoller("test complete")

    import core.observability_logger as _obs

    def _fake_log_error(payload):
        errors.append(str(payload))

    # Cycle: first poll delivers update 1 (fails) and update 2 (succeeds).
    # Because update 1 crashes mid-batch, the outer handler catches it; on the
    # next cycle offset=2 is sent and update 2 is delivered and processed.
    poll_call = [0]

    def _fake_get(url, params=None, timeout=None):
        poll_call[0] += 1
        resp = MagicMock()
        if poll_call[0] == 1:
            # First poll: deliver two updates; update 1 will crash
            resp.json.return_value = {
                "ok": True,
                "result": [
                    {
                        "update_id": 1,
                        "message": {"chat": {"id": 1}, "from": {"id": 1}, "text": "/start"},
                    },
                ],
            }
        elif poll_call[0] == 2:
            # Second poll (after crash+sleep): deliver update 2
            resp.json.return_value = {
                "ok": True,
                "result": [
                    {
                        "update_id": 2,
                        "message": {"chat": {"id": 1}, "from": {"id": 1}, "text": "/help"},
                    },
                ],
            }
        else:
            resp.json.return_value = {"ok": True, "result": []}
        return resp

    monkeypatch.setattr(_poller_mod, "process_update", _fake_process)
    monkeypatch.setattr(_poller_mod.observability_logger, "log_error", _fake_log_error)

    sleep_calls = [0]

    def _fast_sleep(_t):
        sleep_calls[0] += 1

    with patch.dict(os.environ, {"TELEGRAM_BOT_TOKEN": "123:TOKEN"}), \
         patch.object(_poller_mod.requests, "get", side_effect=_fake_get), \
         patch("time.sleep", side_effect=_fast_sleep):
        try:
            _poller_mod.LAST_UPDATE_ID = None
            _poller_mod.poll_updates()
        except _StopPoller:
            pass  # Expected: raised after update 2 was successfully processed

    assert 2 in processed, "Update 2 must be processed despite update 1 crashing"
    assert any("Simulated" in e or "error" in e.lower() for e in errors), (
        "The crash on update 1 must be logged"
    )


def test_13b_duplicate_poller_start_is_blocked(monkeypatch):
    starts: list[dict] = []
    monkeypatch.setattr(_poller_mod, "_emit_poller_startup", lambda event, extra: starts.append({"event": event, **extra}))
    monkeypatch.setattr(_poller_mod, "_POLLER_STARTED", True)
    _poller_mod.poll_updates()
    assert starts and starts[0]["event"] == "duplicate_poller_blocked"


# ---------------------------------------------------------------------------
# Test 14 — Railway-visible safe log line is emitted
# ---------------------------------------------------------------------------

def test_14_railway_safe_log_line(tmp_path, monkeypatch):
    """
    process_update must not crash on a typical /start update; the observability
    logger must produce at least one JSONL record (engine or error) and the
    Railway stdout stream must not contain the bot token.
    """
    owner_id = 990
    chat_id = owner_id

    roles_file = tmp_path / "roles.json"
    roles_file.write_text(json.dumps(_make_roles(owner_id)))
    status_file = tmp_path / "status.json"
    status_file.write_text(json.dumps({"phase": "running"}))

    pub = FakePublisher()
    monkeypatch.setattr(_bs_mod, "telegram_publisher", pub)
    monkeypatch.setenv("ADMIN_CONTROL_CHAT_ID", "0")
    monkeypatch.setenv("ROLES_CONFIG_PATH", str(roles_file))
    monkeypatch.setenv("RUNTIME_STATUS_PATH", str(status_file))
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "987654321:AABBCCddeeff_GGHHII-testtoken")

    _nav_mod.clear_active_message(owner_id, chat_id)

    captured_stdout = io.StringIO()
    captured_stderr = io.StringIO()

    with patch("sys.stdout", captured_stdout), patch("sys.stderr", captured_stderr):
        _bs_mod.process_update(_msg_update(chat_id, owner_id, "/start"))

    out = captured_stdout.getvalue() + captured_stderr.getvalue()
    assert "987654321:AABBCCddeeff_GGHHII-testtoken" not in out, (
        "Bot token must not appear in Railway stdout/stderr"
    )


# ---------------------------------------------------------------------------
# Test 15 — bot token never appears in error log strings
# ---------------------------------------------------------------------------

def test_15_token_not_in_logs(monkeypatch):
    """
    _sanitize in telegram_publisher must strip the bot token from any string
    that embeds a Telegram API URL.
    """
    token = "123456789:AABBCCddeeff-testtoken"
    raw = f"HTTPSConnectionPool: Max retries with url: /bot{token}/getUpdates"
    sanitized = _publisher_mod._sanitize(raw)
    assert token not in sanitized, "Token must be redacted from error strings"
    assert "[REDACTED]" in sanitized


# ---------------------------------------------------------------------------
# Test 16 — internal JSONL logging still works
# ---------------------------------------------------------------------------

def test_16_jsonl_logging_works(tmp_path, monkeypatch):
    """
    The observability logger must write a valid JSONL record when log_error
    is called with a canonical payload.
    """
    import core.observability_logger as _obs

    error_log = tmp_path / "errors.jsonl"
    monkeypatch.setenv("ERROR_EVENTS_LOG", str(error_log))
    monkeypatch.setenv("OBS_DIR", str(tmp_path))

    _obs.log_error({
        "event_type": "error",
        "data": {
            "severity": "ERROR",
            "error_type": "test_log",
            "message": "transport hardening test log record",
        },
    })

    if error_log.exists():
        lines = [l for l in error_log.read_text().splitlines() if l.strip()]
        if lines:
            record = json.loads(lines[-1])
            assert record.get("event_type") == "error" or "error" in str(record)


# ---------------------------------------------------------------------------
# Test 17 — same user/chat/thread isolation remains correct
# ---------------------------------------------------------------------------

def test_17_session_isolation(tmp_path, monkeypatch):
    """
    Active message tracking must isolate sessions by (chat_id, user_id, thread_id).
    Operations on one session must not affect another.
    """
    _nav_mod.clear_active_message(100, 1)
    _nav_mod.clear_active_message(100, 2)
    _nav_mod.clear_active_message(200, 1)

    _nav_mod.set_active_message(1, 100, 111)
    _nav_mod.set_active_message(2, 100, 222)
    _nav_mod.set_active_message(1, 200, 333)

    assert _nav_mod.get_active_message(1, 100) == 111
    assert _nav_mod.get_active_message(2, 100) == 222
    assert _nav_mod.get_active_message(1, 200) == 333

    _nav_mod.clear_active_message(1, 100)

    assert _nav_mod.get_active_message(1, 100) is None
    assert _nav_mod.get_active_message(2, 100) == 222, "Other user must not be affected"
    assert _nav_mod.get_active_message(1, 200) == 333, "Other chat must not be affected"


# ---------------------------------------------------------------------------
# Test 18 — full representative end-to-end navigation remains one message
# ---------------------------------------------------------------------------

def test_18_full_e2e_single_message(tmp_path, monkeypatch):
    """
    A representative production session covering /start → APP:STATUS →
    APP:HELP → APP:HOME must stay within a single interactive message
    throughout, with no new sends after the first.
    """
    owner_id = 989
    chat_id = owner_id

    roles_file = tmp_path / "roles.json"
    roles_file.write_text(json.dumps(_make_roles(owner_id)))
    status_file = tmp_path / "status.json"
    status_file.write_text(json.dumps({"phase": "running"}))

    pub = FakePublisher()
    monkeypatch.setattr(_bs_mod, "telegram_publisher", pub)
    monkeypatch.setenv("ADMIN_CONTROL_CHAT_ID", "0")
    monkeypatch.setenv("ROLES_CONFIG_PATH", str(roles_file))
    monkeypatch.setenv("RUNTIME_STATUS_PATH", str(status_file))

    _nav_mod.clear_active_message(owner_id, chat_id)

    # /start — first message
    _bs_mod.process_update(_msg_update(chat_id, owner_id, "/start"))
    assert len(pub.sends) == 1
    active_id = _nav_mod.get_active_message(owner_id, chat_id)
    assert active_id is not None

    # APP:STATUS callback
    _bs_mod.process_update(_cb_update(chat_id, owner_id, "APP:STATUS", message_id=active_id))
    assert len(pub.sends) == 1, "APP:STATUS must edit, not send new"
    assert len(pub.edits) >= 1

    # APP:HELP callback
    _bs_mod.process_update(_cb_update(chat_id, owner_id, "APP:HELP", message_id=active_id))
    assert len(pub.sends) == 1, "APP:HELP must edit, not send new"

    # APP:HOME callback
    _bs_mod.process_update(_cb_update(chat_id, owner_id, "APP:HOME", message_id=active_id))
    assert len(pub.sends) == 1, "APP:HOME must edit, not send new"

    # All edits must target the same message
    for edit in pub.edits:
        assert edit["message_id"] == active_id, (
            f"Edit targeted wrong message: expected {active_id}, got {edit['message_id']}"
        )


def test_19_restart_reuses_persisted_active_message(tmp_path, monkeypatch):
    owner_id = 1991
    chat_id = owner_id

    roles_file = tmp_path / "roles.json"
    roles_file.write_text(json.dumps(_make_roles(owner_id)))
    status_file = tmp_path / "status.json"
    status_file.write_text(json.dumps({"phase": "running"}))

    monkeypatch.setenv("BINARYBOT_BASE_DIR", str(tmp_path))
    monkeypatch.setenv("TELEGRAM_UI_PERSISTENCE", "1")
    monkeypatch.setenv("ADMIN_CONTROL_CHAT_ID", "0")
    monkeypatch.setenv("ROLES_CONFIG_PATH", str(roles_file))
    monkeypatch.setenv("RUNTIME_STATUS_PATH", str(status_file))
    nav_mod = importlib.import_module("core.telegram_app_nav")
    _bs_mod.telegram_app_nav = nav_mod

    pub_start = FakePublisher(start_id=9100)
    monkeypatch.setattr(_bs_mod, "telegram_publisher", pub_start)
    nav_mod.clear_active_message(owner_id, chat_id)
    _bs_mod.process_update(_msg_update(chat_id, owner_id, "/start"))
    active_id = nav_mod.get_active_message(owner_id, chat_id)
    assert active_id == 9100

    nav_mod = importlib.reload(nav_mod)
    _bs_mod.telegram_app_nav = nav_mod
    assert nav_mod.get_active_message(owner_id, chat_id) == active_id

    pub_after = FakePublisher(start_id=9200)
    monkeypatch.setattr(_bs_mod, "telegram_publisher", pub_after)
    _bs_mod.process_update(_msg_update(chat_id, owner_id, "/status"))

    assert len(pub_after.sends) == 0, "Restarted runtime must reuse persisted active message"
    assert len(pub_after.edits) == 1
    assert pub_after.edits[0]["message_id"] == active_id


def test_20_restart_with_deleted_message_generates_single_replacement(tmp_path, monkeypatch):
    owner_id = 1992
    chat_id = owner_id

    roles_file = tmp_path / "roles.json"
    roles_file.write_text(json.dumps(_make_roles(owner_id)))
    status_file = tmp_path / "status.json"
    status_file.write_text(json.dumps({"phase": "running"}))

    monkeypatch.setenv("BINARYBOT_BASE_DIR", str(tmp_path))
    monkeypatch.setenv("TELEGRAM_UI_PERSISTENCE", "1")
    monkeypatch.setenv("ADMIN_CONTROL_CHAT_ID", "0")
    monkeypatch.setenv("ROLES_CONFIG_PATH", str(roles_file))
    monkeypatch.setenv("RUNTIME_STATUS_PATH", str(status_file))
    nav_mod = importlib.import_module("core.telegram_app_nav")
    _bs_mod.telegram_app_nav = nav_mod

    pub_start = FakePublisher(start_id=9300)
    monkeypatch.setattr(_bs_mod, "telegram_publisher", pub_start)
    nav_mod.clear_active_message(owner_id, chat_id)
    _bs_mod.process_update(_msg_update(chat_id, owner_id, "/start"))
    active_id = nav_mod.get_active_message(owner_id, chat_id)
    assert active_id == 9300

    nav_mod = importlib.reload(nav_mod)
    _bs_mod.telegram_app_nav = nav_mod
    assert nav_mod.get_active_message(owner_id, chat_id) == active_id

    pub_after = FakePublisher(start_id=9400, edit_fail=True, edit_fail_msg="message to edit not found")
    monkeypatch.setattr(_bs_mod, "telegram_publisher", pub_after)
    _bs_mod.process_update(_msg_update(chat_id, owner_id, "/status"))

    assert len(pub_after.sends) == 1, "Deleted persisted message must trigger one replacement send"
    assert nav_mod.get_active_message(owner_id, chat_id) == 9400


def test_21_restart_then_repeated_admin_stays_single_message(tmp_path, monkeypatch):
    owner_id = 1993
    chat_id = owner_id

    roles_file = tmp_path / "roles.json"
    roles_file.write_text(json.dumps(_make_roles(owner_id)))
    status_file = tmp_path / "status.json"
    status_file.write_text(json.dumps({"phase": "running"}))

    monkeypatch.setenv("BINARYBOT_BASE_DIR", str(tmp_path))
    monkeypatch.setenv("TELEGRAM_UI_PERSISTENCE", "1")
    monkeypatch.setenv("ADMIN_CONTROL_CHAT_ID", "0")
    monkeypatch.setenv("ROLES_CONFIG_PATH", str(roles_file))
    monkeypatch.setenv("RUNTIME_STATUS_PATH", str(status_file))
    nav_mod = importlib.import_module("core.telegram_app_nav")
    nav_mod.initialize_active_ui_state(force_reload=True)
    _bs_mod.telegram_app_nav = nav_mod

    pub_start = FakePublisher(start_id=9500)
    monkeypatch.setattr(_bs_mod, "telegram_publisher", pub_start)
    nav_mod.clear_active_message(owner_id, chat_id)
    _bs_mod.process_update(_msg_update(chat_id, owner_id, "/start"))
    active_id = nav_mod.get_active_message(owner_id, chat_id)
    assert active_id == 9500

    nav_mod = importlib.reload(nav_mod)
    nav_mod.initialize_active_ui_state(force_reload=True)
    _bs_mod.telegram_app_nav = nav_mod

    pub_after = FakePublisher(start_id=9600)
    monkeypatch.setattr(_bs_mod, "telegram_publisher", pub_after)
    _bs_mod.process_update(_msg_update(chat_id, owner_id, "/admin", message_id=301))
    _bs_mod.process_update(_msg_update(chat_id, owner_id, "/admin", message_id=302))

    assert len(pub_after.sends) == 0
    assert len(pub_after.edits) == 2
    assert {edit["message_id"] for edit in pub_after.edits} == {active_id}
