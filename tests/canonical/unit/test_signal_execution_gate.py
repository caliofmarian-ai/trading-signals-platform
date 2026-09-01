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
from core.signal_execution_gate import prepare_signal_execution
from core.v2_fsm_orchestrator import advance_persistent_fsm
from state_store.state_store import default_fsm_state


def _decision(kind: str, candle_ts: int, *, model_expiry: float | None = 5.0) -> DecisionObject:
    tier = {
        "PRE": "SCORE_PRE_BAND",
        "CONFIRM": "SCORE_CONFIRM_BAND",
        "OPEN_NOW": "SCORE_OPEN_BAND",
    }[kind]
    return DecisionObject(
        kind=kind,
        signal_id="sig-v2-execution-gate",
        setup=SetupContext(
            "EUR/USD",
            "BUY",
            candle_ts,
            "M1",
            f"cycle-{candle_ts}",
            "binary_strategy_v2",
        ),
        market_context=MarketContext(
            1.11234,
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
        time=TimeContext(3.1, 3.8, model_expiry, 0.76, None, "READY", 5.0 / 3.8 if model_expiry else None),
        score=ScoreContext(86.0, 0.86, {"trend": 24.0}, tier=tier),
        strategic_flags=StrategicFlags(True, True, False, False, False, False, False),
        reject=RejectContext(),
        fsm_inputs={"score_tier": tier},
        explanations=("Real canonical evidence.",),
    )


def _after_pre() -> dict:
    pre = advance_persistent_fsm(
        default_fsm_state(),
        _decision("PRE", 100),
        now_ts=101,
    )
    return pre.next_state


def test_ready_pre_builds_lifecycle_candidate_but_not_trade_ready() -> None:
    decision = _decision("PRE", 100)
    persistent = advance_persistent_fsm(default_fsm_state(), decision, now_ts=101)
    result = prepare_signal_execution(
        persistent,
        decision,
        buffer_mode="MEDIUM",
        created_ts=102,
    )

    assert result.outcome == "DEFERRED"
    assert result.reason == "DISTRIBUTION_NOT_INVOKED"
    assert result.execution_phase == "PRE_DISTRIBUTION"
    assert result.destination_state == "PRE_DISTRIBUTION_UNRESOLVED"
    assert result.stage_handoff_ready is True
    assert result.trade_execution_ready is False
    assert result.signal_event_available is True
    assert result.candidate is not None
    assert result.candidate.stage == "PRE"
    assert result.distribution_allowed is False


def test_ready_confirm_builds_lifecycle_candidate_but_not_trade_ready() -> None:
    state = _after_pre()
    decision = _decision("CONFIRM", 160)
    persistent = advance_persistent_fsm(state, decision, now_ts=161)
    result = prepare_signal_execution(
        persistent,
        decision,
        buffer_mode="MEDIUM",
        created_ts=162,
    )

    assert result.outcome == "DEFERRED"
    assert result.candidate is not None
    assert result.candidate.stage == "CONFIRM"
    assert result.stage_handoff_ready is True
    assert result.trade_execution_ready is False


def test_ready_open_now_builds_candidate_and_is_trade_ready_but_still_deferred() -> None:
    decision = _decision("OPEN_NOW", 160)
    persistent = advance_persistent_fsm(_after_pre(), decision, now_ts=161)

    result = prepare_signal_execution(
        persistent,
        decision,
        buffer_mode="MEDIUM",
        created_ts=162,
    )

    assert result.outcome == "DEFERRED"
    assert result.reason == "DISTRIBUTION_NOT_INVOKED"
    assert result.distribution_allowed is False
    assert result.stage_handoff_ready is True
    assert result.trade_execution_ready is True
    assert result.candidate is not None
    assert result.candidate.event_type == "SIGNAL_CANDIDATE"
    assert result.candidate.signal_id == "sig-v2-execution-gate"
    assert result.candidate.stage == "OPEN_NOW"
    assert result.candidate.buffer_distance == 0.0008
    assert result.candidate.model_expiry == 5.0
    assert result.candidate.expiry_minutes == 5


def test_duplicate_stage_is_blocked_without_candidate() -> None:
    decision = _decision("PRE", 100)
    first = advance_persistent_fsm(default_fsm_state(), decision, now_ts=101)
    duplicate = advance_persistent_fsm(first.next_state, decision, now_ts=102)

    result = prepare_signal_execution(
        duplicate,
        decision,
        buffer_mode="MEDIUM",
        created_ts=103,
    )

    assert result.outcome == "BLOCKED"
    assert result.reason == "DUPLICATE_STAGE_CANDLE"
    assert result.candidate is None
    assert result.signal_event_available is False
    assert result.distribution_allowed is False


def test_rejected_fsm_result_is_blocked() -> None:
    decision = _decision("OPEN_NOW", 100)
    persistent = advance_persistent_fsm(default_fsm_state(), decision, now_ts=101)

    result = prepare_signal_execution(
        persistent,
        decision,
        buffer_mode="MEDIUM",
        created_ts=102,
    )

    assert result.outcome == "BLOCKED"
    assert result.candidate is None
    assert result.distribution_allowed is False


def test_incomplete_real_signal_event_evidence_stays_not_emitted() -> None:
    complete = _decision("OPEN_NOW", 160)
    persistent = advance_persistent_fsm(_after_pre(), complete, now_ts=161)
    incomplete = replace(complete, time=replace(complete.time, model_expiry=None))

    result = prepare_signal_execution(
        persistent,
        incomplete,
        buffer_mode="MEDIUM",
        created_ts=162,
    )

    assert result.outcome == "NOT_EMITTED"
    assert result.reason.startswith("SIGNAL_EVENT_UNAVAILABLE:")
    assert result.candidate is None
    assert result.signal_event_available is False
    assert result.distribution_allowed is False


def test_execution_trace_is_canonical_and_contains_no_delivery_side_effects() -> None:
    decision = _decision("OPEN_NOW", 160)
    persistent = advance_persistent_fsm(_after_pre(), decision, now_ts=161)
    result = prepare_signal_execution(
        persistent,
        decision,
        buffer_mode="LARGE",
        created_ts=162,
    )
    trace = result.to_dict()
    event_data = result.to_event_data()

    assert trace["execution_attempt_id"] == "binary-v2:sig-v2-execution-gate:OPEN_NOW:162"
    assert trace["setup_correlation_id"] == "cycle-160"
    assert trace["candidate"]["distribution_enabled"] is False
    assert trace["distribution_allowed"] is False
    assert event_data["execution_phase"] == "PRE_DISTRIBUTION"
    assert event_data["execution_outcome"] == "DEFERRED"
    assert event_data["destination_state"] == "PRE_DISTRIBUTION_UNRESOLVED"
