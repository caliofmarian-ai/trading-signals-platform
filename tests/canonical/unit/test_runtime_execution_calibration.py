from __future__ import annotations

import hashlib
import importlib
import json
import os
from pathlib import Path
from types import SimpleNamespace

import pytest


NOW = 1_800_000_000


def _artifact(params: dict) -> dict:
    from core.runtime_execution_calibration import algo_params_sha256

    # Test-only values and attestations, never a production calibration.
    return {
        "schema_version": "1.0.0", "calibration_id": "TEST-ONLY-v1", "status": "APPROVED",
        "strategy_version": "2.0.0", "time_model_schema_version": "2.0.0",
        "provider": "FINNHUB", "symbol": "EUR/USD", "buffer_mode": "MEDIUM",
        "algo_params_sha256": algo_params_sha256(params),
        "valid_from_ts": NOW - 100, "valid_until_ts": NOW + 100,
        "governance": {
            "change_id": "TEST-ONLY", "approval_ref": "test-only-approval",
            "evidence_ref": "test-only-replay", "rollback_ref": "test-only-rollback",
            "approved_at_ts": NOW - 200,
        },
        "values": {
            "confirm_delta_minutes": 2.0, "pressure_bias": 0.1,
            "minimum_expiry_minutes": 1.0, "maximum_expiry_minutes": 15.0,
        },
    }


def _load(path: Path, params: dict, **changes):
    from core.runtime_execution_calibration import load_runtime_execution_calibration

    arguments = {
        "now_ts": NOW, "provider": "FINNHUB", "symbol": "EUR/USD",
        "buffer_mode": "MEDIUM", "params": params,
    }
    arguments.update(changes)
    return load_runtime_execution_calibration(str(path), **arguments)


def _write(path: Path, artifact: dict) -> None:
    from core.storage import save_json_atomic

    save_json_atomic(str(path), artifact)


def _params(root: Path) -> dict:
    return json.loads((root / "config/algo_params.json").read_text())


def test_matching_artifact_preserves_values_and_exact_file_provenance(canonical_runtime_root):
    params = _params(canonical_runtime_root)
    path = canonical_runtime_root / "config/execution_calibration.json"
    _write(path, _artifact(params))
    result = _load(path, params)

    assert result.status == "AVAILABLE"
    assert result.calibration.confirm_delta_minutes == 2.0
    assert result.calibration.pressure_bias == 0.1
    assert result.calibration.source == "exec-cal-v1:TEST-ONLY-v1:" + hashlib.sha256(path.read_bytes()).hexdigest()
    assert result.summary()["calibration_efficacy_established"] is False
    assert result.summary()["broker_executed"] is False
    assert "test-only-approval" not in json.dumps(result.summary())


@pytest.mark.parametrize(("field", "value", "status"), [
    ("schema_version", "999.0.0", "INVALID"),
    ("strategy_version", "999.0.0", "SCOPE_MISMATCH"),
    ("time_model_schema_version", "999.0.0", "SCOPE_MISMATCH"),
    ("provider", "TWELVE_DATA", "SCOPE_MISMATCH"),
    ("symbol", "EUR/USD OTC", "SCOPE_MISMATCH"),
    ("buffer_mode", "SMALL", "SCOPE_MISMATCH"),
    ("algo_params_sha256", "a" * 64, "SCOPE_MISMATCH"),
    ("status", "SUSPENDED", "UNAPPROVED"),
    ("status", "PROPOSED", "UNAPPROVED"),
    ("valid_from_ts", NOW + 1, "NOT_YET_VALID"),
    ("valid_until_ts", NOW, "EXPIRED"),
    ("valid_until_ts", NOW - 101, "INVALID"),
    ("valid_from_ts", True, "INVALID"),
    ("valid_until_ts", float(NOW), "INVALID"),
    ("valid_until_ts", 2**60, "INVALID"),
    ("calibration_id", "bad\nid", "INVALID"),
])
def test_inactive_invalid_or_mismatched_artifact_never_supplies_values(
    canonical_runtime_root, field, value, status,
):
    params = _params(canonical_runtime_root)
    path = canonical_runtime_root / "config/execution_calibration.json"
    artifact = _artifact(params)
    artifact[field] = value
    _write(path, artifact)
    result = _load(path, params)
    assert result.status == status
    assert result.calibration is None
    assert result.summary()["source"] is None


@pytest.mark.parametrize(("group", "field", "value"), [
    ("governance", "approval_ref", ""),
    ("governance", "evidence_ref", None),
    ("governance", "rollback_ref", ""),
    ("governance", "approved_at_ts", NOW),
    ("governance", "approved_at_ts", True),
    ("values", "confirm_delta_minutes", -1),
    ("values", "pressure_bias", 1),
    ("values", "pressure_bias", "0.1"),
    ("values", "pressure_bias", True),
    ("values", "pressure_bias", float("nan")),
    ("values", "maximum_expiry_minutes", float("inf")),
    ("values", "maximum_expiry_minutes", .5),
    ("values", "minimum_expiry_minutes", 0),
])
def test_invalid_attestations_and_values_fail_closed(canonical_runtime_root, group, field, value):
    params = _params(canonical_runtime_root)
    artifact = _artifact(params)
    artifact[group][field] = value
    path = canonical_runtime_root / "config/execution_calibration.json"
    _write(path, artifact)
    assert _load(path, params).status == "INVALID"
    assert _load(path, params).calibration is None


@pytest.mark.parametrize("group", [None, "governance", "values"])
@pytest.mark.parametrize("change", ["missing", "unknown", "duplicate"])
def test_ambiguous_schema_is_rejected(canonical_runtime_root, group, change):
    params = _params(canonical_runtime_root)
    artifact = _artifact(params)
    target = artifact if group is None else artifact[group]
    field = next(iter(target))
    if change == "missing":
        target.pop(field)
    elif change == "unknown":
        target["unrecognized"] = "value"
    raw = json.dumps(artifact)
    if change == "duplicate":
        token = json.dumps(field) + ": " + json.dumps(target[field])
        raw = raw.replace(token, token + ", " + token, 1)
    path = canonical_runtime_root / "config/execution_calibration.json"
    path.write_text(raw)
    assert _load(path, params).calibration is None
    assert _load(path, params).status == "INVALID"


@pytest.mark.parametrize("kind", ["malformed", "oversized", "directory", "symlink", "fifo"])
def test_bad_files_cannot_block_or_supply_calibration(canonical_runtime_root, kind):
    params = _params(canonical_runtime_root)
    path = canonical_runtime_root / "config/execution_calibration.json"
    if kind == "malformed":
        path.write_bytes(b"{bad\xff")
    elif kind == "oversized":
        path.write_bytes(b" " * (32 * 1024 + 1))
    elif kind == "directory":
        path.mkdir()
    elif kind == "symlink":
        other = path.with_suffix(".target")
        _write(other, _artifact(params))
        path.symlink_to(other)
    else:
        os.mkfifo(path)
    result = _load(path, params)
    assert result.status == "INVALID"
    assert result.calibration is None


def test_expiry_scope_change_suspension_and_deletion_take_effect_without_cached_fallback(canonical_runtime_root):
    params = _params(canonical_runtime_root)
    path = canonical_runtime_root / "config/execution_calibration.json"
    artifact = _artifact(params)
    assert _load(path, params).status == "MISSING"
    _write(path, artifact)
    assert _load(path, params).calibration is not None
    assert _load(path, params, now_ts=NOW + 100).status == "EXPIRED"
    changed = json.loads(json.dumps(params))
    changed["score_thresholds"]["OPEN"] += 1
    assert _load(path, changed).status == "SCOPE_MISMATCH"
    assert _load(path, params, symbol="EUR/USD OTC").status == "SCOPE_MISMATCH"
    assert _load(path, params, now_ts=NOW - 100).calibration is not None
    artifact["status"] = "SUSPENDED"
    _write(path, artifact)
    assert _load(path, params).status == "UNAPPROVED"
    artifact["status"] = "APPROVED"
    artifact["values"]["pressure_bias"] = 0.05
    _write(path, artifact)
    module = importlib.import_module("core.runtime_execution_calibration")
    importlib.reload(module)
    assert _load(path, params).calibration.pressure_bias == 0.05
    path.unlink()
    assert _load(path, params).status == "MISSING"


@pytest.mark.parametrize(("field", "value"), [
    ("confirm_delta_minutes", 1.0),
    ("minimum_expiry_minutes", 2.0),
    ("maximum_expiry_minutes", 10.0),
])
def test_artifact_must_cover_the_governed_model_horizon_range(canonical_runtime_root, field, value):
    params = _params(canonical_runtime_root)
    artifact = _artifact(params)
    artifact["values"][field] = value
    path = canonical_runtime_root / "config/execution_calibration.json"
    _write(path, artifact)
    result = _load(path, params)
    assert result.calibration is None
    assert result.reason == "EXPIRY_RANGE_INCONSISTENT"


def _decision(kind, candle_ts):
    from core.decision_object import (
        DecisionObject, MarketContext, RejectContext, ScoreContext, SetupContext,
        StrategicFlags, StructureContext, TimeContext,
    )

    tier = "SCORE_PRE_BAND" if kind == "PRE" else "SCORE_OPEN_BAND"
    return DecisionObject(
        kind=kind, signal_id="sig-test-only-calibration",
        setup=SetupContext("EUR/USD", "BUY", candle_ts, "M1", f"cycle-{candle_ts}", "binary_strategy_v2"),
        market_context=MarketContext(1.11234, .0002, .0008, "UP", "ACTIVE", "STABLE", .0012, .00018, .00020, .9),
        structure=StructureContext(1.11, 1.12, 1.11, 1.12, .01, .0012, "INSIDE", "VALID"),
        time=TimeContext(3.1, 3.8, 5.0, .76, None, "READY", 5.0 / 3.8),
        score=ScoreContext(86.0, .86, {"trend": 24.0}, tier=tier),
        strategic_flags=StrategicFlags(True, True, False, False, False, False, False),
        reject=RejectContext(), fsm_inputs={"score_tier": tier}, explanations=("Test-only fixture.",),
    )


@pytest.mark.parametrize("artifact_state", ["valid", "missing", "expired"])
def test_runtime_wires_source_preserves_evaluation_and_existing_publication_block(
    canonical_runtime_root, monkeypatch, capsys, artifact_state,
):
    from core import signal_engine as engine
    from core.execution_model import derive_execution_time
    from core.fsm_decision_adapter import interpret_decision
    from core.v2_fsm_orchestrator import advance_persistent_fsm
    from state_store.state_store import default_fsm_state

    from core.physical_params import load_physical_runtime_algo_params
    params = load_physical_runtime_algo_params(str(canonical_runtime_root / "config/algo_params.json"))
    path = canonical_runtime_root / "config/execution_calibration.json"
    artifact = _artifact(params)
    artifact["strategy_version"] = "3.0.0"
    if artifact_state == "expired":
        artifact["valid_until_ts"] = NOW
    if artifact_state != "missing":
        _write(path, artifact)
    monkeypatch.setenv("MARKET_DATA_PROVIDER", "FINNHUB")
    monkeypatch.setenv("SHADOW_MODEL_TIME_RESEARCH_ENABLED", "false")
    monkeypatch.setattr(engine, "EXECUTION_CALIBRATION_PATH", str(path))
    monkeypatch.setattr(engine, "_load_settings", lambda: {"buffer_mode": "MEDIUM"})
    monkeypatch.setattr(engine, "_load_active_symbols", lambda: ["EUR/USD"])
    pre = advance_persistent_fsm(default_fsm_state(), _decision("PRE", NOW - 60), now_ts=NOW - 59)
    monkeypatch.setattr(engine.fsm_runtime, "load_state", lambda: pre.next_state)
    monkeypatch.setattr(engine.fsm_runtime, "reconcile_state", lambda state, *a, **k: (state, []))
    monkeypatch.setattr(engine.fsm_runtime, "save_state", lambda state: None)
    monkeypatch.setattr("runtime.market_client.get_finnhub_decision_candles",
                        lambda symbol: ([{"test": True}], [{"test": True}], NOW))
    monkeypatch.setattr(engine.candle_adapter, "normalize", lambda raw, **kwargs: raw)
    monkeypatch.setattr(engine.candle_adapter, "validate", lambda candles: None)
    monkeypatch.setattr(engine, "_log_decision_evaluated", lambda *a: None)
    engine._LAST_CALIBRATION_STATE.clear()
    captured = []

    def capture_decide(**kwargs):
        calibration = kwargs["execution_calibration"]
        captured.append(calibration)
        decision = _decision("OPEN_NOW", NOW)
        return SimpleNamespace(
            decision=decision,
            execution_time=derive_execution_time(decision, interpret_decision(decision), calibration),
        )

    monkeypatch.setattr(engine, "decide", capture_decide)
    publications = []
    monkeypatch.setattr(engine.distribution_router.legacy.telegram_publisher, "send_message", lambda **k: publications.append(k))
    executions = []
    monkeypatch.setattr(engine, "_log_signal_execution", lambda d, f, execution: executions.append(execution))
    engine.run_once(now_ts=NOW, forced_symbols=["EUR/USD"])
    assert len(captured) == 1  # Research/strategy evaluation survives missing calibration.
    assert len(executions) == 1
    assert publications == []
    if artifact_state == "valid":
        assert captured[0] is not None
        assert executions[0].candidate.open_now_expiry_minutes == 4.5
        assert executions[0].candidate.execution_calibration_source == captured[0].source
        events = [json.loads(line) for line in (canonical_runtime_root / "observability/engine_events.jsonl").read_text().splitlines()]
        assert any(e.get("data", {}).get("execution_reason") == "FINNHUB_PERSONAL_USE_DISTRIBUTION_BLOCKED" for e in events)
    else:
        assert captured == [None]
        assert executions[0].reason == "EXECUTION_TIME_UNAVAILABLE"
        assert executions[0].candidate is None
    stdout = capsys.readouterr().out
    assert "TSP_EXECUTION_CALIBRATION_EVIDENCE" in stdout
    assert "test-only-approval" not in stdout
    assert "pressure_bias" not in stdout
