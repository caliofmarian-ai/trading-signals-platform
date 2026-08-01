from __future__ import annotations

import importlib
import json
import sys
import threading
import time
from pathlib import Path


def _load_app_nav():
    if "core.telegram_app_nav" in sys.modules:
        return importlib.reload(sys.modules["core.telegram_app_nav"])
    return importlib.import_module("core.telegram_app_nav")


def _state_file(base_dir: Path) -> Path:
    return base_dir / "state" / "telegram_ui_state.json"


def test_active_ui_persists_across_module_reload(tmp_path, monkeypatch):
    monkeypatch.setenv("BINARYBOT_BASE_DIR", str(tmp_path))
    monkeypatch.setenv("TELEGRAM_UI_PERSISTENCE", "1")

    nav = _load_app_nav()
    nav.clear_active_message(101, chat_id=5001, thread_id=11)
    nav.clear_active_message(101, chat_id=5001, thread_id=22)

    nav.set_active_message(101, chat_id=5001, thread_id=11, message_id=7001)
    nav.set_active_message(101, chat_id=5001, thread_id=22, message_id=7002)

    nav = importlib.reload(nav)
    assert nav.get_active_message(101, chat_id=5001, thread_id=11) == 7001
    assert nav.get_active_message(101, chat_id=5001, thread_id=22) == 7002


def test_corrupt_persistence_does_not_break_startup(tmp_path, monkeypatch):
    monkeypatch.setenv("BINARYBOT_BASE_DIR", str(tmp_path))
    monkeypatch.setenv("TELEGRAM_UI_PERSISTENCE", "1")
    state_file = _state_file(tmp_path)
    state_file.parent.mkdir(parents=True, exist_ok=True)
    state_file.write_text("{not valid json", encoding="utf-8")

    nav = _load_app_nav()
    assert nav.get_active_message(202, chat_id=6001) is None

    nav.set_active_message(202, chat_id=6001, message_id=8001)
    assert nav.get_active_message(202, chat_id=6001) == 8001


def test_unsupported_schema_recovers_safely(tmp_path, monkeypatch):
    monkeypatch.setenv("BINARYBOT_BASE_DIR", str(tmp_path))
    monkeypatch.setenv("TELEGRAM_UI_PERSISTENCE", "1")
    state_file = _state_file(tmp_path)
    state_file.parent.mkdir(parents=True, exist_ok=True)
    state_file.write_text(json.dumps({"version": "9.9.9", "sessions": []}), encoding="utf-8")

    nav = _load_app_nav()
    assert nav.get_active_message(203, chat_id=6002) is None
    nav.set_active_message(203, chat_id=6002, message_id=8002)
    assert nav.get_active_message(203, chat_id=6002) == 8002


def test_retention_and_abandoned_cleanup_on_load(tmp_path, monkeypatch):
    monkeypatch.setenv("BINARYBOT_BASE_DIR", str(tmp_path))
    monkeypatch.setenv("TELEGRAM_UI_PERSISTENCE", "1")
    monkeypatch.setenv("TELEGRAM_UI_STATE_RETENTION_SECONDS", "120")
    now_ts = int(time.time())
    old_ts = now_ts - 3600
    state_file = _state_file(tmp_path)
    state_file.parent.mkdir(parents=True, exist_ok=True)
    state_file.write_text(
        json.dumps(
            {
                "version": "1.0.0",
                "retention_seconds": 120,
                "max_sessions": 1000,
                "sessions": [
                    {"chat_id": 1, "user_id": 1, "thread_id": None, "message_id": 111, "updated_ts": old_ts},
                    {"chat_id": 2, "user_id": 2, "thread_id": 7, "message_id": 222, "updated_ts": now_ts},
                ],
            }
        ),
        encoding="utf-8",
    )

    nav = _load_app_nav()
    assert nav.get_active_message(1, chat_id=1) is None
    assert nav.get_active_message(2, chat_id=2, thread_id=7) == 222


def test_concurrent_updates_are_safe_and_atomic(tmp_path, monkeypatch):
    monkeypatch.setenv("BINARYBOT_BASE_DIR", str(tmp_path))
    monkeypatch.setenv("TELEGRAM_UI_PERSISTENCE", "1")
    nav = _load_app_nav()

    def _writer(base: int) -> None:
        for i in range(25):
            nav.set_active_message(300 + base, chat_id=9000 + base, message_id=10000 + i, thread_id=base)

    threads = [threading.Thread(target=_writer, args=(idx,)) for idx in range(4)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    state_file = _state_file(tmp_path)
    payload = json.loads(state_file.read_text(encoding="utf-8"))
    assert payload["version"] == "1.0.0"
    assert isinstance(payload.get("sessions"), list)
    tmp_files = list(state_file.parent.glob(".tmp_*.json"))
    assert not tmp_files
