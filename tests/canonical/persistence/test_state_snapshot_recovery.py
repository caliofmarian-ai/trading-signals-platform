from __future__ import annotations

import importlib
import json
from pathlib import Path

import pytest


def test_state_store_migrates_legacy_fsm_state_once(canonical_runtime_root: Path):
    state_store = importlib.import_module("state_store.state_store")

    legacy_path = canonical_runtime_root / "focus_state.json"
    canonical_path = canonical_runtime_root / "state" / "focus_state.json"

    legacy_path.write_text(
        json.dumps(
            {
                "version": "1.1.0",
                "watchlist": ["EURUSD"],
                "per_symbol": {"EURUSD": {"state": "WATCHLIST"}},
                "mode": "FOCUS_MODE",
                "last_updated_ts": 1720000900,
            }
        ),
        encoding="utf-8",
    )

    state = state_store.load_fsm_state()
    assert state["watchlist"] == ["EURUSD"]
    assert canonical_path.exists()

    state_again = state_store.load_fsm_state()
    assert state_again["watchlist"] == ["EURUSD"]


def test_state_store_conflict_between_legacy_and_canonical_raises(canonical_runtime_root: Path):
    state_store = importlib.import_module("state_store.state_store")

    legacy_path = canonical_runtime_root / "dist_state.json"
    canonical_path = canonical_runtime_root / "state" / "dist_state.json"

    legacy_path.write_text(json.dumps({"tier_state": {"FREE": "ACTIVE", "BASIC": "ACTIVE", "PRO": "ACTIVE", "ELITE": "ACTIVE"}, "open_signals_today": {"FREE": 1, "BASIC": 0, "PRO": 0, "ELITE": 0}, "dedup": {}}), encoding="utf-8")
    canonical_path.write_text(json.dumps({"tier_state": {"FREE": "SILENT", "BASIC": "ACTIVE", "PRO": "ACTIVE", "ELITE": "ACTIVE"}, "open_signals_today": {"FREE": 0, "BASIC": 0, "PRO": 0, "ELITE": 0}, "dedup": {}}), encoding="utf-8")

    with pytest.raises(state_store.StateConflictError):
        state_store.load_dist_state()


def test_snapshot_restore_rolls_back_on_failed_write(canonical_runtime_root: Path, monkeypatch):
    state_store = importlib.import_module("state_store.state_store")
    snapshots = importlib.import_module("snapshots.snapshot_manager")

    state_store.save_fsm_state({"watchlist": ["EURUSD"], "per_symbol": {"EURUSD": {"state": "WATCHLIST"}}})
    state_store.save_dist_state(state_store.default_dist_state())

    snapshot_path = snapshots.create_snapshot()
    snapshot_name = Path(snapshot_path).name

    original = state_store.load_fsm_state()

    call = {"count": 0}
    real_save = state_store.save_fsm_state

    def _flaky_save(payload, path=None):
        call["count"] += 1
        if call["count"] == 1:
            raise OSError("simulated write failure")
        return real_save(payload, path=path)

    monkeypatch.setattr(state_store, "save_fsm_state", _flaky_save)

    with pytest.raises(OSError):
        snapshots.restore_snapshot(snapshot_name)

    restored = state_store.load_fsm_state()
    assert restored["watchlist"] == original["watchlist"]
