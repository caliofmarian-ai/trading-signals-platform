from __future__ import annotations

import importlib
import os
import sys

import pytest

SEND_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../send"))
if SEND_ROOT not in sys.path:
    sys.path.insert(0, SEND_ROOT)

@pytest.fixture
def bot(monkeypatch, tmp_path):
    monkeypatch.setenv("BINARYBOT_BASE_DIR", str(tmp_path))
    monkeypatch.setenv("OBS_DIR", str(tmp_path / "observability"))
    monkeypatch.setenv("ADMIN_CONTROL_CHAT_ID", "-1003726714813")
    monkeypatch.setenv("ADMIN_CONTROL_THREAD_ID", "1310")
    import core.bot_service as module
    return importlib.reload(module)

def test_file_transport_marker_is_not_wrapped(bot, monkeypatch):
    monkeypatch.setattr(bot, "handle_admin_command_v2", lambda cmd, user_id: "__FILE_PATH__:/tmp/binarybot_audit_test.json")
    text, markup = bot._render_panel_for_command("/audit_runtime", 7553887987, owner_private=True)
    assert text == "__FILE_PATH__:/tmp/binarybot_audit_test.json"
    assert markup is None
    assert "Runtime Audit" not in text

def test_interactive_send_failure_retries_once_as_text_only(bot, monkeypatch):
    calls = []
    monkeypatch.setattr(bot.telegram_app_nav, "get_runtime_diagnostics", lambda **kwargs: {"session_key_fingerprint":"abc","active_message_id":None,"persisted_message_id":None,"resolved_state_path":"/data/state/telegram_ui_state.json","save_result":{},"load_result":{},"pid":1,"deployment_id":"test"})
    monkeypatch.setattr(bot.telegram_app_nav, "get_active_message", lambda **kwargs: None)
    monkeypatch.setattr(bot.telegram_app_nav, "set_active_message", lambda **kwargs: None)
    monkeypatch.setattr(bot, "_emit_interactive_trace", lambda *args, **kwargs: None)
    monkeypatch.setattr(bot.observability_logger, "log_error", lambda payload: None)
    def fake_send_message(*, chat_id, text, reply_markup=None, thread_id=None):
        calls.append({"chat_id":chat_id,"text":text,"reply_markup":reply_markup,"thread_id":thread_id})
        if len(calls) == 1:
            raise RuntimeError("Bad Request: BUTTON_DATA_INVALID")
        return {"ok":True,"result":{"message_id":77}}
    monkeypatch.setattr(bot.telegram_publisher, "send_message", fake_send_message)
    message = {"chat":{"id":-1003726714813,"type":"supergroup"},"message_thread_id":1310}
    bot._send_interactive_page(message, 6766367444, "Admin page", {"inline_keyboard":[[{"text":"x","callback_data":"ADMIN_NAV:HOME"}]]})
    assert len(calls) == 2
    assert calls[0]["reply_markup"] is not None
    assert calls[1]["reply_markup"] is None
    assert "failure was logged" in calls[1]["text"]
    assert calls[1]["thread_id"] == 1310

def test_authorized_admin_renderer_exception_gets_sanitized_fallback(bot, monkeypatch):
    sent = []
    logged = []
    monkeypatch.setattr(bot, "admin_command_names", lambda: {"/admin"})
    monkeypatch.setattr(bot, "_can_run_admin_command", lambda message, user_id, cmd: True)
    monkeypatch.setattr(bot.telegram_app_nav, "record_app_navigation", lambda **kwargs: (_ for _ in ()).throw(RuntimeError("INTERNAL_DETAIL")))
    monkeypatch.setattr(bot.observability_logger, "log_error", lambda payload: logged.append(payload))
    def fake_send_message(*, chat_id, text, reply_markup=None, thread_id=None):
        sent.append({"chat_id":chat_id,"text":text,"reply_markup":reply_markup,"thread_id":thread_id})
        return {"ok":True,"result":{"message_id":88}}
    monkeypatch.setattr(bot.telegram_publisher, "send_message", fake_send_message)
    update = {"update_id":1,"message":{"chat":{"id":-1003726714813,"type":"supergroup"},"from":{"id":6766367444,"first_name":"Primary"},"text":"/admin","message_id":500,"message_thread_id":1310}}
    bot.process_update(update)
    assert logged
    assert sent
    assert sent[-1]["thread_id"] == 1310
    assert "could not be completed safely" in sent[-1]["text"]
    assert "INTERNAL_DETAIL" not in sent[-1]["text"]

def test_wrong_chat_remains_fail_closed(bot, monkeypatch):
    replies = []
    monkeypatch.setattr(bot, "admin_command_names", lambda: {"/admin"})
    monkeypatch.setattr(bot, "_can_run_admin_command", lambda message, user_id, cmd: False)
    monkeypatch.setattr(bot, "_send_interactive_page", lambda message, user_id, text, reply_markup, **kwargs: replies.append(text))
    bot.process_update({"update_id":2,"message":{"chat":{"id":-1009999999999,"type":"supergroup"},"from":{"id":6766367444},"text":"/admin","message_id":501,"message_thread_id":999}})
    assert replies == ["Access denied (wrong chat)."]
