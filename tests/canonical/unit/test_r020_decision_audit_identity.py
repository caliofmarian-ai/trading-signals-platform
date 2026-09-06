from __future__ import annotations

from dataclasses import replace

from core.decision_object import (
    DecisionObject,
    MarketContext,
    RejectContext,
    ScoreContext,
    SetupContext,
    StrategicFlags,
    StructureContext,
    TimeContext,
)
from core.execution_model import ExecutionCalibration, derive_execution_time
from core.fsm_decision_adapter import interpret_decision
from core.signal_execution_gate import prepare_signal_execution
from core.trade_temporal_telemetry import _build_trade_record
from core.v2_fsm_orchestrator import advance_persistent_fsm
from state_store.state_store import default_fsm_state


def _decision(kind: str, candle_ts: int, *, latest_price: float = 1.11234) -> DecisionObject:
    tier = {
        "PRE": "SCORE_PRE_BAND",
        "CONFIRM": "SCORE_CONFIRM_BAND",
        "OPEN_NOW": "SCORE_OPEN_BAND",
    }[kind]
    return DecisionObject(
        kind=kind,
        signal_id="sig-r020-lineage",
        setup=SetupContext(
            "EUR/USD",
            "BUY",
            candle_ts,
            "M1",
            f"EUR/USD:{candle_ts}",
            "binary_strategy_v2",
        ),
        market_context=MarketContext(
            latest_price,
            0.0002,
            0.0008,
            "UP",
            "ACTIVE",
            "STABLE",
            0.0012,
            0.00018,
            0.00020,
            0.9,
        ),
        structure=StructureContext(
            1.11,
            1.12,
            1.11,
            1.12,
            0.01,
            0.0012,
            "INSIDE",
            "VALID",
        ),
        time=TimeContext(3.1, 3.8, 5.0, 0.76, None, "READY", 5.0 / 3.8),
        score=ScoreContext(86.0, 0.86, {"trend": 24.0}, tier=tier),
        strategic_flags=StrategicFlags(True, True, False, False, False, False, False),
        reject=RejectContext(),
        fsm_inputs={"score_tier": tier},
        explanations=("Real canonical evidence.",),
    )


def _calibration() -> ExecutionCalibration:
    return ExecutionCalibration(
        confirm_delta_minutes=1.0,
        pressure_bias=0.1,
        minimum_expiry_minutes=1.0,
        maximum_expiry_minutes=15.0,
        source="r020-test-calibration-v1",
    )


def _state_after_pre() -> dict:
    pre = _decision("PRE", 100)
    return advance_persistent_fsm(default_fsm_state(), pre, now_ts=101).next_state


def _open_now_execution(decision: DecisionObject):
    return derive_execution_time(decision, interpret_decision(decision), _calibration())


def test_decision_identity_is_stable_for_same_materialized_semantics() -> None:
    first = _decision("PRE", 100)
    second = _decision("PRE", 100)

    assert first.decision_id == second.decision_id
    assert first.decision_audit_id == second.decision_audit_id
    assert first.decision_id.startswith("dec-v1-")
    assert first.decision_audit_id.startswith("da-v1-")
    assert first.to_dict()["decision_id"] == first.decision_id
    assert first.to_dict()["decision_audit_id"] == first.decision_audit_id


def test_non_identity_market_snapshot_change_does_not_recompute_lineage_identity() -> None:
    first = _decision("PRE", 100, latest_price=1.11234)
    replay = replace(
        first,
        market_context=replace(first.market_context, latest_price=1.11235),
    )

    assert replay.decision_id == first.decision_id
    assert replay.decision_audit_id == first.decision_audit_id


def test_material_decision_boundary_change_changes_decision_identity() -> None:
    pre = _decision("PRE", 100)
    confirm = _decision("CONFIRM", 100)
    next_candle = _decision("PRE", 160)

    assert confirm.decision_id != pre.decision_id
    assert confirm.decision_audit_id != pre.decision_audit_id
    assert next_candle.decision_id != pre.decision_id
    assert next_candle.decision_audit_id != pre.decision_audit_id


def test_fsm_materializes_stable_transition_identity_from_decision_identity() -> None:
    decision = _decision("PRE", 100)
    first = advance_persistent_fsm(default_fsm_state(), decision, now_ts=101)
    replay = advance_persistent_fsm(default_fsm_state(), decision, now_ts=999)

    assert first.decision_id == decision.decision_id
    assert first.decision_audit_id == decision.decision_audit_id
    assert first.fsm_transition_id == replay.fsm_transition_id
    assert first.fsm_transition_id.startswith("fsm-v1-")


def test_execution_gate_and_signal_event_carry_exact_pre_fsm_lineage() -> None:
    decision = _decision("OPEN_NOW", 160)
    persistent = advance_persistent_fsm(_state_after_pre(), decision, now_ts=161)
    result = prepare_signal_execution(
        persistent,
        decision,
        buffer_mode="MEDIUM",
        created_ts=162,
        execution_time=_open_now_execution(decision),
    )

    assert result.candidate is not None
    candidate = result.candidate
    assert result.setup_correlation_id == decision.setup.cycle_id
    assert result.decision_id == decision.decision_id
    assert result.decision_audit_id == decision.decision_audit_id
    assert result.fsm_transition_id == persistent.fsm_transition_id
    assert candidate.setup_correlation_id == result.setup_correlation_id
    assert candidate.decision_id == result.decision_id
    assert candidate.decision_audit_id == result.decision_audit_id
    assert candidate.execution_attempt_id == result.execution_attempt_id
    assert candidate.fsm_transition_id == result.fsm_transition_id
    assert candidate.payload["decision_id"] == decision.decision_id
    assert candidate.payload["decision_audit_id"] == decision.decision_audit_id
    assert candidate.payload["execution_attempt_id"] == result.execution_attempt_id
    assert candidate.payload["fsm_transition_id"] == persistent.fsm_transition_id


def test_open_now_objective_telemetry_preserves_complete_materialized_lineage() -> None:
    decision = _decision("OPEN_NOW", 160)
    persistent = advance_persistent_fsm(_state_after_pre(), decision, now_ts=161)
    result = prepare_signal_execution(
        persistent,
        decision,
        buffer_mode="MEDIUM",
        created_ts=162,
        execution_time=_open_now_execution(decision),
    )
    assert result.candidate is not None

    record = _build_trade_record(
        result.candidate.to_dict(),
        now_ts=163,
        market_provider="FINNHUB",
        publication_evidence={
            "route_result_event_id": "route-result-r020",
            "visibility_event_id": "visibility-r020",
            "route": "ELITE",
            "destination_id": -100123,
            "message_id": 77,
        },
    )

    assert record["linkage_state"] == "COMPLETE"
    assert record["missing_linkage_fields"] == []
    assert record["setup_correlation_id"] == decision.setup.cycle_id
    assert record["decision_id"] == decision.decision_id
    assert record["decision_audit_id"] == decision.decision_audit_id
    assert record["execution_attempt_id"] == result.execution_attempt_id
    assert record["fsm_transition_id"] == persistent.fsm_transition_id
