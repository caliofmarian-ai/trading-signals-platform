from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SEND_ROOT = REPO_ROOT / "send"

if str(SEND_ROOT) not in sys.path:
    sys.path.insert(0, str(SEND_ROOT))


def _purge_modules() -> None:
    prefixes = ("core.", "monitoring.", "runtime.", "snapshots.", "state_store.")
    exact = {"core", "monitoring", "runtime", "snapshots", "state_store"}
    for name in list(sys.modules.keys()):
        if name in exact or name.startswith(prefixes):
            sys.modules.pop(name, None)
    importlib.invalidate_caches()


def _write_json(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _prepare_runtime_root(tmp_path: Path) -> Path:
    root = tmp_path / "runtime"
    (root / "config").mkdir(parents=True)
    (root / "state").mkdir(parents=True)
    (root / "outcomes").mkdir(parents=True)
    (root / "observability").mkdir(parents=True)

    _write_json(root / "config" / "active_symbols.json", {"symbols": ["EUR/USD", "GBP/USD", "USD/JPY"]})
    _write_json(root / "config" / "admin_settings.json", {"engine_tick_interval": 2, "feature_flags": {}, "buffer_mode": "MEDIUM"})
    _write_json(
        root / "config" / "channel_config.json",
        {
            "FREE_CHANNEL_ID": 1001,
            "BASIC_CHANNEL_ID": 1002,
            "PRO_CHANNEL_ID": 1003,
            "ELITE_CHANNEL_ID": 1004,
            "ADMIN_GROUP_ID": 2001,
            "SIGNALS_LIVE_TOPIC_ID": 3001,
            "FREE_LIMIT": 5,
            "BASIC_LIMIT": 20,
            "PRO_LIMIT": 50,
            "ELITE_LIMIT": None,
            "TZ": "Europe/London",
            "RESET_TIME": "08:10",
        },
    )
    _write_json(root / "config" / "algo_params.json", _read_json(SEND_ROOT / "config" / "algo_params.json"))
    _write_json(root / "config" / "admin_roles.json", {"owner": [1001], "primary_admin": [], "strategy_admin": [], "research_admin": [], "analyst": [], "moderator": [], "affiliate_admin": {}})
    return root


def _import_batch06_modules(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    root = _prepare_runtime_root(tmp_path)
    monkeypatch.setenv("BINARYBOT_BASE_DIR", str(root))
    monkeypatch.setenv("OBS_DIR", str(root / "observability"))
    monkeypatch.setenv("ENGINE_EVENTS_LOG", str(root / "observability" / "engine_events.jsonl"))
    monkeypatch.setenv("FSM_EVENTS_LOG", str(root / "observability" / "fsm_events.jsonl"))
    monkeypatch.setenv("DIST_EVENTS_LOG", str(root / "observability" / "distribution_events.jsonl"))
    monkeypatch.setenv("ADMIN_PROOFS_LOG", str(root / "observability" / "admin_proofs.jsonl"))
    monkeypatch.setenv("ERROR_EVENTS_LOG", str(root / "observability" / "error_events.jsonl"))
    monkeypatch.setenv("OUTCOMES_LOG", str(root / "outcomes" / "outcomes.jsonl"))
    monkeypatch.delenv("ADMIN_PERMISSIONS_CONFIG", raising=False)
    monkeypatch.setenv("ADMIN_ROLES_CONFIG", str(root / "config" / "admin_roles.json"))

    _purge_modules()

    storage = importlib.import_module("core.storage")
    state_store = importlib.import_module("state_store.state_store")
    fsm_runtime = importlib.import_module("core.fsm_runtime")
    signal_engine = importlib.import_module("core.signal_engine")
    restart_guard = importlib.import_module("monitoring.restart_guard")
    snapshot_manager = importlib.import_module("snapshots.snapshot_manager")
    observability_logger = importlib.import_module("core.observability_logger")
    system_boot = importlib.import_module("runtime.system_boot")
    admin_permissions = importlib.import_module("core.admin_permissions")
    return {
        "root": root,
        "storage": storage,
        "state_store": state_store,
        "fsm_runtime": fsm_runtime,
        "signal_engine": signal_engine,
        "restart_guard": restart_guard,
        "snapshot_manager": snapshot_manager,
        "observability_logger": observability_logger,
        "system_boot": system_boot,
        "admin_permissions": admin_permissions,
    }


def _base_decision(kind: str, *, symbol: str = "EUR/USD", signal_id: str = "sig-001", score: float = 81.0, expiry_minutes: int = 5, candle_ts: int = 1_720_000_000):
    return {
        "kind": kind,
        "signal_id": signal_id,
        "symbol": symbol,
        "timeframe": "M1",
        "direction": "CALL",
        "score_total": score,
        "buffer_mode": "MEDIUM",
        "buffer_price": 1.2345,
        "expiry_minutes": expiry_minutes,
        "candle_ts": candle_ts,
        "debug": {},
        "gates": {},
    }


def _read_jsonl(path: Path):
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def test_segmented_paths_resolve_under_base_dir_override(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    modules = _import_batch06_modules(tmp_path, monkeypatch)
    root = modules["root"]
    state_store = modules["state_store"]

    assert Path(state_store.FOCUS_STATE_PATH) == root / "state" / "focus_state.json"
    assert Path(state_store.DIST_STATE_PATH) == root / "state" / "dist_state.json"
    assert Path(state_store.RESTART_GUARD_PATH) == root / "state" / "restart_guard.json"
    assert Path(state_store.ACTIVE_SYMBOLS_PATH) == root / "config" / "active_symbols.json"
    assert Path(state_store.SETTINGS_PATH) == root / "config" / "admin_settings.json"
    assert Path(modules["snapshot_manager"].SNAPSHOT_DIR) == root / "snapshots"


def test_legacy_root_level_fsm_state_migrates_idempotently_to_segmented_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    modules = _import_batch06_modules(tmp_path, monkeypatch)
    root = modules["root"]
    state_store = modules["state_store"]

    legacy_path = root / "focus_state.json"
    payload = {
        "version": "1.0",
        "mode": "FOCUS_MODE",
        "watchlist": ["EUR/USD"],
        "per_symbol": {"EUR/USD": {"state": "WATCHLIST", "current_signal_id": "sig-001", "last_pre_candle_ts": 111, "last_confirm_candle_ts": None, "last_open_candle_ts": None, "cooldown_until_ts": None, "focus_enter_ts": 100}},
        "last_updated_ts": 111,
    }
    _write_json(legacy_path, payload)

    first = state_store.load_fsm_state()
    second = state_store.load_fsm_state()

    assert first["watchlist"] == ["EUR/USD"]
    assert second["watchlist"] == ["EUR/USD"]
    assert _read_json(root / "state" / "focus_state.json")["watchlist"] == ["EUR/USD"]
    assert _read_json(legacy_path)["watchlist"] == ["EUR/USD"]


def test_identical_dual_state_is_accepted_but_conflict_and_invalid_state_fail_clearly(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    modules = _import_batch06_modules(tmp_path, monkeypatch)
    root = modules["root"]
    state_store = modules["state_store"]

    payload = {
        "version": "1.0.0",
        "mode": "FOCUS_MODE",
        "watchlist": ["EUR/USD"],
        "per_symbol": {"EUR/USD": {"state": "WATCHLIST", "current_signal_id": "sig-001", "last_pre_candle_ts": 111, "last_confirm_candle_ts": None, "last_open_candle_ts": None, "cooldown_until_ts": None, "focus_enter_ts": 100}},
        "last_updated_ts": 111,
    }
    _write_json(root / "focus_state.json", payload)
    _write_json(root / "state" / "focus_state.json", payload)
    assert state_store.load_fsm_state()["watchlist"] == ["EUR/USD"]

    changed = dict(payload)
    changed["watchlist"] = ["GBP/USD"]
    _write_json(root / "focus_state.json", changed)
    with pytest.raises(state_store.StateConflictError, match="fsm_state conflict"):
        state_store.load_fsm_state()

    (root / "focus_state.json").write_text("{bad json", encoding="utf-8")
    (root / "state" / "focus_state.json").unlink()
    with pytest.raises(state_store.StateValidationError, match="Invalid JSON"):
        state_store.load_fsm_state()


def test_canonical_writes_only_touch_segmented_paths(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    modules = _import_batch06_modules(tmp_path, monkeypatch)
    root = modules["root"]
    state_store = modules["state_store"]

    legacy_path = root / "restart_guard.json"
    _write_json(legacy_path, {"starts": [1], "last_updated_ts": 1})

    state = state_store.load_restart_guard_state()
    state["starts"] = [10]
    state_store.save_restart_guard_state(state)

    assert _read_json(root / "state" / "restart_guard.json")["starts"] == [10]
    assert _read_json(legacy_path)["starts"] == [1]
    assert not any(path.suffix == ".tmp" for path in (root / "state").glob("*"))


def test_fsm_import_and_live_source_no_longer_depend_on_scan_scheduler(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    modules = _import_batch06_modules(tmp_path, monkeypatch)
    assert modules["fsm_runtime"] is not None
    assert "scan_scheduler" not in (SEND_ROOT / "core" / "signal_engine.py").read_text(encoding="utf-8")
    assert "_focus_state_path" not in (SEND_ROOT / "core" / "signal_engine.py").read_text(encoding="utf-8")


def test_fsm_valid_transition_sequence_and_event_schema(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    modules = _import_batch06_modules(tmp_path, monkeypatch)
    fsm_runtime = modules["fsm_runtime"]
    obs = modules["observability_logger"]

    state = fsm_runtime.load_state()
    state, event_pre = fsm_runtime.apply_transition(state, _base_decision("PRE"), now_ts=1_720_000_001)
    state, event_confirm = fsm_runtime.apply_transition(state, _base_decision("CONFIRM"), now_ts=1_720_000_002)
    state, event_open = fsm_runtime.apply_transition(state, _base_decision("OPEN_NOW"), now_ts=1_720_000_003)
    state, event_close = fsm_runtime.complete_open_now(state, _base_decision("OPEN_NOW"), now_ts=1_720_000_004)

    assert state["per_symbol"]["EUR/USD"]["state"] == "COOLDOWN"
    assert state["watchlist"] == []
    for event in (event_pre, event_confirm, event_open, event_close):
        built = obs.build_event("fsm_transition", event, source={"module": "tests", "function": "fsm"})
        assert obs.validate_event(built) == built


def test_fsm_invalid_transition_is_rejected(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    modules = _import_batch06_modules(tmp_path, monkeypatch)
    fsm_runtime = modules["fsm_runtime"]

    with pytest.raises(ValueError, match="Invalid FSM transition"):
        fsm_runtime.apply_transition(fsm_runtime.load_state(), _base_decision("CONFIRM"), now_ts=1_720_000_001)


def test_fsm_duplicate_pre_is_idempotent_and_replacement_expiry_and_restart_restore_work(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    modules = _import_batch06_modules(tmp_path, monkeypatch)
    fsm_runtime = modules["fsm_runtime"]

    state = fsm_runtime.load_state()
    state, _ = fsm_runtime.apply_transition(state, _base_decision("PRE", symbol="EUR/USD", signal_id="sig-a", score=70.0, expiry_minutes=1), now_ts=100)
    state, _ = fsm_runtime.apply_transition(state, _base_decision("PRE", symbol="EUR/USD", signal_id="sig-a", score=70.0, expiry_minutes=1), now_ts=101)
    state, _ = fsm_runtime.apply_transition(state, _base_decision("PRE", symbol="GBP/USD", signal_id="sig-b", score=71.0, expiry_minutes=1), now_ts=102)
    state, replace_event = fsm_runtime.apply_transition(state, _base_decision("PRE", symbol="USD/JPY", signal_id="sig-c", score=99.0, expiry_minutes=1), now_ts=103)
    fsm_runtime.save_state(state)

    assert len(state["watchlist"]) == len(set(state["watchlist"])) == 2
    assert "USD/JPY" in state["watchlist"]
    assert replace_event["trigger"] == "watchlist_replaced"

    restored = fsm_runtime.load_state()
    assert restored["watchlist"] == state["watchlist"]

    expired_state, events = fsm_runtime.reconcile_state(restored, 500, active_symbols=["EUR/USD", "GBP/USD", "USD/JPY"])
    assert any(event["trigger"] == "focus_lease_expired" for event in events)
    assert expired_state["mode"] in {"FOCUS_MODE", "WIDE_SCAN"}


def test_signal_engine_does_not_route_when_fsm_persistence_fails(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    modules = _import_batch06_modules(tmp_path, monkeypatch)
    signal_engine = modules["signal_engine"]
    fsm_runtime = modules["fsm_runtime"]

    monkeypatch.setattr("runtime.market_client.get_candles", lambda symbol, timeframe, **kwargs: [{"t": 1, "o": 1.0, "h": 1.1, "l": 0.9, "c": 1.0} for _ in range(250)])
    monkeypatch.setattr(signal_engine.candle_adapter, "normalize", lambda raw, symbol, timeframe: [{"symbol": symbol, "timeframe": timeframe, "ts": idx, "open": 1.0, "high": 1.1, "low": 0.9, "close": 1.0, "volume": None} for idx, _ in enumerate(raw, start=1)])
    monkeypatch.setattr(signal_engine.candle_adapter, "validate", lambda candles: None)
    monkeypatch.setattr(signal_engine, "decide", lambda **kwargs: _base_decision("PRE"))

    routed = {"called": False}
    monkeypatch.setattr(signal_engine.distribution_router, "route", lambda *args, **kwargs: routed.__setitem__("called", True))
    monkeypatch.setattr(fsm_runtime, "save_state", lambda state: (_ for _ in ()).throw(RuntimeError("persist failed")))

    signal_engine.run_once(now_ts=1_720_000_010, forced_symbols=["EUR/USD"], forced_focus_context=False)
    assert not routed["called"]


def test_restart_guard_counts_once_per_start_and_handles_graceful_shutdown(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    modules = _import_batch06_modules(tmp_path, monkeypatch)
    restart_guard = modules["restart_guard"]
    state_store = modules["state_store"]

    first = restart_guard.record_start(now_ts=100)
    assert first["restart_count"] == 1
    assert not restart_guard.should_freeze(now_ts=100)
    assert state_store.load_restart_guard_state()["starts"] == [100]

    restart_guard.mark_graceful_shutdown(now_ts=120)
    second = restart_guard.record_start(now_ts=130)
    assert second["restart_count"] == 1
    assert second["previous_shutdown_kind"] == "graceful"
    assert second["counted_restart"] is False


def test_restart_guard_crash_loop_and_corrupt_state_fail_safely(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    modules = _import_batch06_modules(tmp_path, monkeypatch)
    restart_guard = modules["restart_guard"]
    state_store = modules["state_store"]
    root = modules["root"]

    counts = [restart_guard.record_start(now_ts=ts)["restart_count"] for ts in (100, 110, 120, 130)]
    assert counts == [1, 2, 3, 4]
    assert restart_guard.should_freeze(now_ts=130)

    (root / "state" / "restart_guard.json").write_text("{bad json", encoding="utf-8")
    with pytest.raises(state_store.StateValidationError, match="Invalid JSON"):
        restart_guard.record_start(now_ts=200)


def test_snapshot_creation_restore_and_invalid_snapshot_rejection(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    modules = _import_batch06_modules(tmp_path, monkeypatch)
    fsm_runtime = modules["fsm_runtime"]
    snapshot_manager = modules["snapshot_manager"]
    root = modules["root"]

    state = fsm_runtime.load_state()
    state, _ = fsm_runtime.apply_transition(state, _base_decision("PRE"), now_ts=100)
    fsm_runtime.save_state(state)
    path = Path(snapshot_manager.create_snapshot())
    snapshot = _read_json(path)
    assert snapshot["schema_version"] == snapshot_manager.SNAPSHOT_SCHEMA_VERSION
    assert snapshot["focus_state"]["watchlist"] == ["EUR/USD"]

    state["watchlist"] = []
    fsm_runtime.save_state(state)
    snapshot_manager.restore_snapshot(path.name)
    assert fsm_runtime.load_state()["watchlist"] == ["EUR/USD"]

    invalid_path = root / "snapshots" / "snapshot_invalid.json"
    _write_json(invalid_path, {"schema_version": "0.0.1", "created_ts": 1, "focus_state": state, "dist_state": modules["state_store"].default_dist_state()})
    with pytest.raises(snapshot_manager.SnapshotValidationError, match="Unsupported snapshot schema version"):
        snapshot_manager.restore_snapshot(invalid_path.name)
    assert fsm_runtime.load_state()["watchlist"] == ["EUR/USD"]


def test_system_boot_emits_recovery_events(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    modules = _import_batch06_modules(tmp_path, monkeypatch)
    system_boot = modules["system_boot"]
    root = modules["root"]

    class _Thread:
        def __init__(self, target=None, daemon=None):
            self.target = target
            self.daemon = daemon

        def start(self):
            return None

    monkeypatch.setattr(system_boot, "_register_shutdown_hooks", lambda: None)
    monkeypatch.setattr(system_boot.threading, "Thread", _Thread)
    monkeypatch.setattr(system_boot, "start_engine", lambda: None)
    monkeypatch.setattr(system_boot, "poll_updates", lambda: None)
    monkeypatch.setattr(system_boot, "scheduler_loop", lambda: None)
    monkeypatch.setattr(system_boot.time, "sleep", lambda seconds: (_ for _ in ()).throw(SystemExit(0)))

    with pytest.raises(SystemExit):
        system_boot.start_system()

    engine_events = _read_jsonl(root / "observability" / "engine_events.jsonl")
    event_types = [event["event_type"] for event in engine_events]
    assert "recovery_started" in event_types
    assert "recovery_completed" in event_types


def test_missing_permissions_fail_closed_for_non_owner_but_preserve_owner_recovery(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    modules = _import_batch06_modules(tmp_path, monkeypatch)
    admin_permissions = modules["admin_permissions"]

    with pytest.raises(admin_permissions.PermissionConfigurationError, match="Permission config is missing"):
        admin_permissions.reload_permissions_config()
    assert admin_permissions.has_permission(1001, "roles.write")
    assert not admin_permissions.has_permission(9999, "admin.view")
