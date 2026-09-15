from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
SEND_ROOT = REPO_ROOT / "send"
for path in (str(REPO_ROOT), str(SEND_ROOT)):
    if path not in sys.path:
        sys.path.insert(0, path)


def test_railway_deployment_id_precedes_placeholder_run_id(monkeypatch):
    updates = importlib.import_module("runtime.telegram_updates")
    monkeypatch.setenv("RUN_ID", "replace-me")
    monkeypatch.setenv("RAILWAY_SERVICE_ID", "service-123")
    monkeypatch.setenv("RAILWAY_DEPLOYMENT_ID", "deployment-456")

    assert updates._runtime_instance_id() == "deployment-456"


def test_healthy_poller_startup_uses_stdout_without_warning_log(monkeypatch, capsys):
    updates = importlib.import_module("runtime.telegram_updates")
    warnings: list[dict] = []
    monkeypatch.setattr(
        updates.observability_logger,
        "log_warning",
        lambda **kwargs: warnings.append(kwargs),
    )
    monkeypatch.setenv("RAILWAY_DEPLOYMENT_ID", "deployment-healthy")
    monkeypatch.setenv("RUN_ID", "replace-me")

    updates._emit_poller_startup(
        "poller_started",
        {"active_ui_initialized": True, "state_path": "/data/state/telegram_ui_state.json"},
    )

    captured = capsys.readouterr()
    assert captured.err == ""
    payload = json.loads(captured.out.strip())
    assert payload["event"] == "poller_started"
    assert payload["runtime_instance_id"] == "deployment-healthy"
    assert payload["deployment_identifier"] == "deployment-healthy"
    assert warnings == []


def test_duplicate_poller_warning_stays_on_stderr_and_warning_log(monkeypatch, capsys):
    updates = importlib.import_module("runtime.telegram_updates")
    warnings: list[dict] = []
    monkeypatch.setattr(
        updates.observability_logger,
        "log_warning",
        lambda **kwargs: warnings.append(kwargs),
    )
    monkeypatch.setenv("RAILWAY_DEPLOYMENT_ID", "deployment-duplicate")

    updates._emit_poller_startup("duplicate_poller_blocked", {"last_update_id": 42})

    captured = capsys.readouterr()
    assert captured.out == ""
    payload = json.loads(captured.err.strip())
    assert payload["event"] == "duplicate_poller_blocked"
    assert payload["last_update_id"] == 42
    assert len(warnings) == 1
    assert warnings[0]["warn_type"] == "telegram_poller_startup"


def test_railway_ui_adapter_routes_only_healthy_initialization_to_stdout(capsys):
    nav = importlib.import_module("core.telegram_app_nav")
    railway_start = importlib.import_module("scripts.railway_start")
    original = nav._emit_stdout_diagnostic

    try:
        railway_start._install_telegram_ui_diagnostic_stream_routing()
        first_adapter = nav._emit_stdout_diagnostic
        railway_start._install_telegram_ui_diagnostic_stream_routing()
        assert nav._emit_stdout_diagnostic is first_adapter

        nav._emit_stdout_diagnostic(
            "TELEGRAM_UI_STATE_INITIALIZED",
            {"status": "ok", "path": "/data/state/telegram_ui_state.json"},
        )
        healthy = capsys.readouterr()
        assert healthy.err == ""
        healthy_payload = json.loads(healthy.out.strip())
        assert healthy_payload["code"] == "TELEGRAM_UI_STATE_INITIALIZED"
        assert healthy_payload["context"]["status"] == "ok"

        nav._emit_stdout_diagnostic(
            "TELEGRAM_UI_STATE_LOAD_FAILED",
            {"status": "error", "reason": "unreadable"},
        )
        warning = capsys.readouterr()
        assert warning.out == ""
        warning_payload = json.loads(warning.err.strip())
        assert warning_payload["code"] == "TELEGRAM_UI_STATE_LOAD_FAILED"
        assert warning_payload["context"]["status"] == "error"
    finally:
        nav._emit_stdout_diagnostic = original
