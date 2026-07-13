from __future__ import annotations

import importlib
import threading
from pathlib import Path

import pytest


def test_imports_are_boot_safe(monkeypatch: pytest.MonkeyPatch, canonical_runtime_root: Path):
    started_threads: list[str] = []

    class _FailThread:
        def __init__(self, *args, **kwargs):
            started_threads.append("created")

        def start(self):
            started_threads.append("started")
            raise AssertionError("thread started during import")

    monkeypatch.setattr(threading, "Thread", _FailThread)

    importlib.invalidate_caches()
    assert importlib.import_module("core.signal_engine") is not None
    assert importlib.import_module("runtime.system_boot") is not None
    assert started_threads == []


def test_system_boot_blocks_on_invalid_state(monkeypatch: pytest.MonkeyPatch, canonical_runtime_root: Path):
    boot = importlib.import_module("runtime.system_boot")

    captured: list[dict] = []

    monkeypatch.setattr(boot, "_register_shutdown_hooks", lambda: None)
    monkeypatch.setattr(
        boot,
        "record_start",
        lambda: {
            "restart_count": 1,
            "window_seconds": 60,
            "max_restarts": 3,
            "previous_shutdown_kind": "unknown",
            "recovery_required": False,
            "crash_loop": False,
        },
    )
    monkeypatch.setattr(boot.fsm_runtime, "load_state", lambda: (_ for _ in ()).throw(ValueError("invalid fsm state")))
    monkeypatch.setattr(boot, "log_event", lambda event: captured.append(event))

    boot.start_system()

    assert any(event.get("event_type") == "error" for event in captured)
    assert any("UNSAFE_BLOCKED" in str(event) for event in captured)


def test_candle_normalization_and_validation_contract():
    adapter = importlib.import_module("core.candle_adapter")

    raw = {
        "candles": [
            {"ts": 1720000060000, "open": "1.1", "high": "1.2", "low": "1.0", "close": "1.15", "volume": 11},
            {"ts": 1720000000000, "o": 1.0, "h": 1.1, "l": 0.9, "c": 1.05, "vol": 10},
            {"ts": "bad", "open": 1, "high": 2, "low": 0.5, "close": 1.5},
        ]
    }

    normalized = adapter.normalize(raw, symbol="EURUSD", timeframe="M1")
    assert [c["ts"] for c in normalized] == [1720000060, 1720000000]
    adapter.validate(normalized)

    with pytest.raises(ValueError, match="ordering invalid"):
        adapter.validate(list(reversed(normalized)))
