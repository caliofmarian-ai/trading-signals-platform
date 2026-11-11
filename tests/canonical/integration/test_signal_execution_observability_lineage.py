from __future__ import annotations

import json
from types import SimpleNamespace

import pytest


NOW = 1_800_000_000
_ENVELOPE_LINEAGE = ("setup_correlation_id", "decision_id", "decision_audit_id", "execution_attempt_id")


def _decision(stage, stamp):
    from core.decision_object import (
        DecisionObject, MarketContext, RejectContext, ScoreContext, SetupContext,
        StrategicFlags, StructureContext, TimeContext,
    )

    tier = {"PRE": "SCORE_PRE_BAND", "CONFIRM": "SCORE_CONFIRM_BAND", "OPEN_NOW": "SCORE_OPEN_BAND"}[stage]
    return DecisionObject(
        kind=stage, signal_id="sig-test-execution-lineage",
        setup=SetupContext("EUR/USD", "BUY", stamp, "M1", f"cycle-{stamp}", "binary_strategy_v2"),
        market_context=MarketContext(1.11234, .0002, .0008, "UP", "ACTIVE", "STABLE", .0012, .00018, .00020, .9),
        structure=StructureContext(1.11, 1.12, 1.11, 1.12, .01, .0012, "INSIDE", "VALID"),
        time=TimeContext(3.1, 3.8, 5.0, .76, None, "READY", 5.0 / 3.8),
        score=ScoreContext(86.0, .86, {"trend": 24.0}, tier=tier),
        strategic_flags=StrategicFlags(True, True, False, False, False, False, False),
        reject=RejectContext(), fsm_inputs={"score_tier": tier}, explanations=("Test-only fixture.",),
    )


def _prepare(stage, calibrated=True):
    from core.execution_model import ExecutionCalibration, derive_execution_time
    from core.fsm_decision_adapter import interpret_decision
    from core.signal_execution_gate import prepare_signal_execution
    from core.v2_fsm_orchestrator import advance_persistent_fsm
    from state_store.state_store import default_fsm_state

    calibration = ExecutionCalibration(2.0, .1, 1.0, 15.0, "test-only-lineage") if calibrated else None
    state = default_fsm_state()
    if stage != "PRE":
        state = advance_persistent_fsm(state, _decision("PRE", NOW - 60), now_ts=NOW - 59).next_state
    decision = _decision(stage, NOW)
    handoff = advance_persistent_fsm(state, decision, now_ts=NOW)
    execution_time = derive_execution_time(decision, interpret_decision(decision), calibration)
    execution = prepare_signal_execution(
        handoff, decision, buffer_mode="MEDIUM", created_ts=NOW, execution_time=execution_time,
    )
    return state, decision, handoff, execution_time, execution


@pytest.mark.parametrize(("stage", "calibrated"), [
    ("PRE", False), ("CONFIRM", True), ("OPEN_NOW", True), ("OPEN_NOW", False),
])
def test_actual_execution_writer_accepts_strict_schema_and_preserves_lineage(
    canonical_runtime_root, stage, calibrated,
):
    from core import observability_logger, signal_engine

    _, decision, handoff, _, execution = _prepare(stage, calibrated)
    signal_engine._log_fsm_handoff(decision, handoff)
    signal_engine._log_signal_execution(decision, handoff, execution)
    path = canonical_runtime_root / "observability/engine_events.jsonl"
    events = [json.loads(line) for line in path.read_text().splitlines()]
    event = events[-1]
    assert observability_logger.validate_event(event) == event
    assert event["event_type"] == "signal_execution_result"
    for field in _ENVELOPE_LINEAGE:
        assert event[field] == getattr(execution, field)
        assert field not in event["data"]
    assert "fsm_transition_id" not in event["data"]
    assert event["data"]["fsm_handoff"]["fsm_transition_id"] == handoff.fsm_transition_id
    assert event["data"]["execution_outcome"] != "EMITTED"
    fsm_event = json.loads((canonical_runtime_root / "observability/fsm_events.jsonl").read_text().splitlines()[-1])
    assert fsm_event["decision_id"] == event["decision_id"]
    assert fsm_event["decision_audit_id"] == event["decision_audit_id"]


@pytest.mark.parametrize(("stage", "calibrated"), [("PRE", False), ("OPEN_NOW", True), ("OPEN_NOW", False)])
def test_real_run_once_logging_cannot_abort_before_governed_distribution(
    canonical_runtime_root, monkeypatch, stage, calibrated,
):
    from core import signal_engine as engine
    from core.market_model import M1SpeedWindowEvidence
    from runtime import market_client

    state, decision, _, execution_time, expected = _prepare(stage, calibrated)
    evaluation = SimpleNamespace(
        decision=decision, cycle_id=decision.setup.cycle_id, strategy_version="2.0.0",
        canonical_spec="ALGO_SPEC_v3.0.0", execution_time=execution_time,
        market=SimpleNamespace(
            symbol="EUR/USD", evaluated_ts=NOW,
            evidence=SimpleNamespace(
                average_m1_range=.0003, minimum_m1_range=.00025, atr_m5=.0008,
                m1_speed_window=M1SpeedWindowEvidence(
                    "COMPLETED_M1_INTERVALS_V1", 21, 20, NOW - 21 * 60,
                    NOW - 20 * 60, NOW, float(NOW), "PROVIDER_FLAGS_AND_OBSERVATION_TIME",
                ),
            ),
        ),
        corridor=SimpleNamespace(evidence=SimpleNamespace(required_distance=.0008, room_ratio=2.0, support_levels=(1.11,), resistance_levels=(1.12,))),
    )
    monkeypatch.setenv("MARKET_DATA_PROVIDER", "FINNHUB")
    monkeypatch.setenv("SHADOW_MODEL_TIME_RESEARCH_ENABLED", "false")
    monkeypatch.setattr(engine, "_load_settings", lambda: {"buffer_mode": "MEDIUM"})
    monkeypatch.setattr(engine, "_load_active_symbols", lambda: ["EUR/USD"])
    monkeypatch.setattr(engine.fsm_runtime, "load_state", lambda: state)
    monkeypatch.setattr(engine.fsm_runtime, "reconcile_state", lambda state, *a, **k: (state, []))
    monkeypatch.setattr(engine.fsm_runtime, "save_state", lambda state: None)
    monkeypatch.setattr(market_client, "get_finnhub_decision_candles",
                        lambda symbol: ([{"test": True}], [{"test": True}], NOW))
    monkeypatch.setattr(engine.candle_adapter, "normalize", lambda raw, **kwargs: raw)
    monkeypatch.setattr(engine.candle_adapter, "validate", lambda candles: None)
    monkeypatch.setattr(engine, "decide", lambda **kwargs: evaluation)
    publications = []
    monkeypatch.setattr(engine.distribution_router.legacy.telegram_publisher, "send_message", lambda **k: publications.append(k))

    engine.run_once(now_ts=NOW, forced_symbols=["EUR/USD"])

    path = canonical_runtime_root / "observability/engine_events.jsonl"
    events = [json.loads(line) for line in path.read_text().splitlines()]
    executions = [e for e in events if e["event_type"] == "signal_execution_result"]
    assert executions, "an accepted stage must not vanish in a schema-construction exception"
    assert publications == []
    error_path = canonical_runtime_root / "observability/error_events.jsonl"
    incidents = [json.loads(line)["data"] for line in error_path.read_text().splitlines()] if error_path.exists() else []
    assert not any(row.get("severity") in {"ERROR", "CRITICAL"} for row in incidents)
    assert all(row.get("code") == "FINNHUB_PERSONAL_USE_DISTRIBUTION_BLOCKED" for row in incidents)
    for event in events:
        assert event["decision_id"] == decision.decision_id
        assert event["decision_audit_id"] == decision.decision_audit_id
    for event in executions:
        for field in _ENVELOPE_LINEAGE:
            assert event[field] == getattr(expected, field)
        assert event["data"]["fsm_handoff"]["fsm_transition_id"] == expected.fsm_transition_id
    assert executions[0]["data"]["execution_phase"] == "PRE_DISTRIBUTION"
    if expected.distribution_allowed:
        assert len(executions) == 2
        assert executions[-1]["data"]["execution_phase"] == "POST_DISTRIBUTION"
        assert executions[-1]["data"]["execution_reason"] == "FINNHUB_PERSONAL_USE_DISTRIBUTION_BLOCKED"
        assert executions[0]["event_id"] != executions[1]["event_id"]
    else:
        assert len(executions) == 1
        assert executions[0]["data"]["execution_reason"] == "EXECUTION_TIME_UNAVAILABLE"
