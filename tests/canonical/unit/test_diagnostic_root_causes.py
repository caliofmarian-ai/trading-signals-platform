from __future__ import annotations

import importlib
import json
import threading

import pytest


def _group_command(text):
    return {"message": {"chat": {"id": -10012345, "type": "supergroup"},
                        "from": {"id": 123}, "message_id": 10,
                        "message_thread_id": 99, "text": text}}


@pytest.mark.parametrize("command", ["/diagnose@dropi_trading_bot", "/DiAgNoSe@dropi_trading_bot"])
def test_addressed_command_reaches_real_admin_parser(canonical_runtime_root, fresh_imports, monkeypatch, command):
    bot = fresh_imports("core.bot_service")
    admin = importlib.import_module("core.admin_commands")
    monkeypatch.setattr(bot, "_can_run_admin_command", lambda *a: True)
    monkeypatch.setattr(admin, "has_permission", lambda *a: True)
    monkeypatch.setattr(admin, "handle_diagnose", lambda user_id: "DIAGNOSTIC_HANDLER_REACHED")
    pages = []
    monkeypatch.setattr(bot, "_send_interactive_page", lambda msg, user_id, text, markup, **kw: pages.append((text, markup)))
    bot.process_update(_group_command(command))
    assert len(pages) == 1
    assert "DIAGNOSTIC_HANDLER_REACHED" in pages[0][0]
    assert "Unknown admin command" not in pages[0][0]
    assert pages[0][1] is not None


def test_addressed_download_preserves_arguments_and_document_transport(canonical_runtime_root, fresh_imports, monkeypatch):
    bot = fresh_imports("core.bot_service")
    admin = importlib.import_module("core.admin_commands")
    monkeypatch.setattr(bot, "_can_run_admin_command", lambda *a: True)
    monkeypatch.setattr(admin, "has_permission", lambda *a: True)
    calls = []
    document = canonical_runtime_root / "observability" / "MixedCase.json"
    document.write_text("{}")
    monkeypatch.setattr(admin, "handle_file_download_path", lambda directory, name, user: calls.append((directory, name, user)) or (str(document), ""))
    delivered = []
    monkeypatch.setattr(bot, "_send_document_reply", lambda msg, path, caption: delivered.append((path, caption)))
    monkeypatch.setattr(bot, "_send_interactive_page", lambda *a, **kw: pytest.fail("file marker was wrapped as a panel"))
    bot.process_update(_group_command("/download@dropi_trading_bot obs MixedCase.json"))
    assert calls == [("obs", "MixedCase.json", 123)]
    assert delivered == [(str(document), "/download")]


def test_addressed_command_still_denies_wrong_chat_before_admin_read(canonical_runtime_root, fresh_imports, monkeypatch):
    bot = fresh_imports("core.bot_service")
    monkeypatch.setattr(bot, "_can_run_admin_command", lambda *a: False)
    monkeypatch.setattr(bot, "_render_panel_for_command", lambda *a, **kw: pytest.fail("unauthorized command reached handler"))
    pages = []
    monkeypatch.setattr(bot, "_send_interactive_page", lambda msg, user_id, text, markup, **kw: pages.append(text))
    bot.process_update(_group_command("/diagnose@dropi_trading_bot"))
    assert pages == ["Access denied (wrong chat)."]


def test_inflight_worker_cannot_restore_starting_after_running(canonical_runtime_root, fresh_imports, monkeypatch):
    status = fresh_imports("runtime.runtime_status")
    status.write_status("starting", "boot", recovery_state="STARTING")
    actual_read = status._read_status_file
    worker_read, release_worker, boot_started, boot_done = (threading.Event() for _ in range(4))
    errors = []

    def paused_read():
        snapshot = actual_read()
        if threading.current_thread().name == "paused-status-worker":
            worker_read.set()
            if not release_worker.wait(3):
                raise AssertionError("test worker release timed out")
        return snapshot

    monkeypatch.setattr(status, "_read_status_file", paused_read)

    def worker():
        try:
            status.update_status(market_data_state="READY")
        except BaseException as exc:
            errors.append(exc)

    def finish_boot():
        boot_started.set()
        try:
            status.write_status("running", "ready", recovery_state="HEALTHY")
        except BaseException as exc:
            errors.append(exc)
        finally:
            boot_done.set()

    slow = threading.Thread(target=worker, name="paused-status-worker")
    ready = threading.Thread(target=finish_boot)
    slow.start()
    try:
        assert worker_read.wait(3)
        ready.start()
        assert boot_started.wait(3)
        # Without serialization, boot commits during this pause and the worker
        # then overwrites RUNNING with its stale STARTING snapshot. With a
        # shared lock, boot waits until the worker completes its transaction.
        boot_done.wait(0.2)
    finally:
        release_worker.set()
        slow.join(4)
        if ready.ident is not None:
            ready.join(4)
    assert not slow.is_alive() and not ready.is_alive()
    assert errors == []
    assert actual_read()["phase"] == "running"
    assert actual_read()["recovery_state"] == "HEALTHY"


def test_boot_completion_keeps_observations_written_by_started_workers(canonical_runtime_root, fresh_imports, monkeypatch):
    boot = fresh_imports("runtime.system_boot")
    monkeypatch.setattr(boot, "_register_shutdown_hooks", lambda: None)
    monkeypatch.setattr(boot, "record_start", lambda: {"restart_count": 0, "window_seconds": 60, "max_restarts": 3,
                                                    "previous_shutdown_kind": "graceful", "recovery_required": False,
                                                    "crash_loop": False})
    monkeypatch.setattr(boot.startup_preflight, "run_startup_preflight", lambda **kw: {"active_provider": "FINNHUB", "effective_symbols": ["EUR/USD"]})
    monkeypatch.setattr(boot.fsm_runtime, "load_state", lambda: {})
    monkeypatch.setattr(boot.distribution_router, "load_state", lambda: {})
    monkeypatch.setattr(boot.telegram_app_nav, "initialize_active_ui_state", lambda: {})
    monkeypatch.setattr(boot, "_should_start_telegram_thread", lambda: False)
    monkeypatch.setattr(boot, "_start_strategy_auditor_thread", lambda: {"enabled": False})
    monkeypatch.setattr(boot, "send_control_notification", lambda *a: None)

    class Worker:
        def __init__(self, target=None, **kw): self.target = target
        def start(self):
            if self.target is boot.telemetry_market_loop:
                boot.runtime_status.update_status(market_data_state="READY", market_data_valid_trade_tick_count=7)

    monkeypatch.setattr(boot.threading, "Thread", Worker)
    monkeypatch.setattr(boot.time, "sleep", lambda seconds: (_ for _ in ()).throw(SystemExit()))
    with pytest.raises(SystemExit):
        boot.start_system()
    result = boot.runtime_status._read_status_file()
    assert result["phase"] == "running"
    assert result["market_data_state"] == "READY"
    assert result["market_data_valid_trade_tick_count"] == 7


def test_diagnose_never_scans_whole_incident_history(canonical_runtime_root, fresh_imports, monkeypatch):
    admin = fresh_imports("core.admin_commands")
    monkeypatch.setattr(admin, "require_permission", lambda *a: (True, ""))
    monkeypatch.setattr(admin, "_iter_jsonl", lambda *a: pytest.fail("diagnose scanned full error history"))
    path = canonical_runtime_root / "observability" / "error_events.jsonl"
    path.write_text("".join(json.dumps({"data": {"message": f"incident-{i}"}}) + "\n" for i in range(100)))
    result = admin.handle_diagnose(123)
    for i in (97, 98, 99):
        assert f"incident-{i}" in result
    assert "incident-96" not in result


def test_diagnose_explains_corrupt_incident_tail(canonical_runtime_root, fresh_imports, monkeypatch):
    admin = fresh_imports("core.admin_commands")
    monkeypatch.setattr(admin, "require_permission", lambda *a: (True, ""))
    path = canonical_runtime_root / "observability" / "error_events.jsonl"
    path.write_text("invalid json\n")
    result = admin.handle_diagnose(123)
    assert "INVALID_JSONL_RECORD" in result
