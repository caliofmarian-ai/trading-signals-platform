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
            "EUR/USD", "BUY", candle_ts, "M1", f"cycle-{candle_ts}", "binary_strategy_v2"
        ),
        market_context=MarketContext(
            1.11234, 0.0002, 0.0008, "UP", "ACTIVE", "STABLE", 0.0012, 0.00018, 0.00020, 0.9
        ),
        structure=StructureContext(
            1.11, 1.12, 1.11, 1.12, 0.01, 0.0012, "INSIDE", "VALID"
        ),
        time=TimeContext(
            3.1,
            3.8,
            model_expiry,
            (3.8 / model_expiry) if model_expiry else None,
            None,
            "READY",
            (model_expiry / 3.8) if model_expiry else None,
        ),
        score=ScoreContext(86.0, 0.86, {"trend": 24.0}, tier=tier),
        strategic_flags=StrategicFlags(True, True, False, False, False, False, False),
        reject=RejectContext(),
        fsm_inputs={"score_tier": tier},
        explanations=("Real canonical evidence.",),
    )


def _after_pre() -> dict:
    pre = advance_persistent_fsm(default_fsm_state(), _decision("PRE", 100), now_ts=101)
    return pre.next_state


def _calibrate(monkeypatch, pressure_bias: str = "0.1") -> None:
    monkeypatch.setenv("EXECUTION_CONFIRM_DELTA_MINUTES", "1.0")
    monkeypatch.setenv("EXECUTION_PRESSURE_BIAS", pressure_bias)
    monkeypatch.setenv("EXECUTION_MIN_EXPIRY_MINUTES", "2.0")
    monkeypatch.setenv("EXECUTION_MAX_EXPIRY_MINUTES", "15.0")
    monkeypatch.setenv("EXECUTION_CALIBRATION_SOURCE", "test-calibration")


def _uncalibrate(monkeypatch) -> None:
    for name in (
        "EXECUTION_CONFIRM_DELTA_MINUTES",
        "EXECUTION_PRESSURE_BIAS",
        "EXECUTION_MIN_EXPIRY_MINUTES",
        "EXECUTION_MAX_EXPIRY_MINUTES",
        "EXECUTION_CALIBRATION_SOURCE",
    ):
        monkeypatch.delenv(name, raising=False)


def test_ready_pre_builds_lifecycle_candidate_but_not_trade_ready(monkeypatch) -> None:
    _uncalibrate(monkeypatch)
    decision = _decision("PRE", 100)
    persistent = advance_persistent_fsm(default_fsm_state(), decision, now_ts=101)
    result = prepare_signal_execution(persistent, decision, buffer_mode="MEDIUM", created_ts=102)

    assert result.outcome == "DEFERRED"
    assert result.reason == "DISTRIBUTION_ROUTER_READY"
    assert result.execution_phase == "PRE_DISTRIBUTION"
    assert result.destination_state == "PRE_DISTRIBUTION_UNRESOLVED"
    assert result.stage_handoff_ready is True
    assert result.trade_execution_ready is False
    assert result.signal_event_available is True
    assert result.candidate is not None
    assert result.candidate.stage == "PRE"
    assert result.candidate.expiry_minutes is None
    assert result.distribution_allowed is True


def test_ready_confirm_builds_informational_candidate_without_calibration(monkeypatch) -> None:
    _uncalibrate(monkeypatch)
    state = _after_pre()
    decision = _decision("CONFIRM", 160)
    persistent = advance_persistent_fsm(state, decision, now_ts=161)
    result = prepare_signal_execution(persistent, decision, buffer_mode="MEDIUM", created_ts=162)

    assert result.outcome == "DEFERRED"
    assert result.candidate is not None
    assert result.candidate.stage == "CONFIRM"
    assert result.candidate.expiry_minutes is None
    assert result.stage_handoff_ready is True
    assert result.trade_execution_ready is False
    assert result.distribution_allowed is True


def test_open_now_without_calibration_fails_closed(monkeypatch) -> None:
    _uncalibrate(monkeypatch)
    decision = _decision("OPEN_NOW", 160)
    persistent = advance_persistent_fsm(_after_pre(), decision, now_ts=161)
    result = prepare_signal_execution(persistent, decision, buffer_mode="MEDIUM", created_ts=162)

    assert result.outcome == "BLOCKED"
    assert result.reason.startswith("EXECUTION_TIME_UNAVAILABLE:")
    assert result.distribution_allowed is False
    assert result.candidate is None


def test_ready_open_now_with_calibration_uses_exact_execution_expiry(monkeypatch) -> None:
    _calibrate(monkeypatch)
    decision = _decision("OPEN_NOW", 160)
    persistent = advance_persistent_fsm(_after_pre(), decision, now_ts=161)
    result = prepare_signal_execution(persistent, decision, buffer_mode="MEDIUM", created_ts=162)

    assert result.outcome == "DEFERRED"
    assert result.reason == "DISTRIBUTION_ROUTER_READY"
    assert result.distribution_allowed is True
    assert result.stage_handoff_ready is True
    assert result.trade_execution_ready is True
    assert result.candidate is not None
    assert result.candidate.event_type == "SIGNAL_CANDIDATE"
    assert result.candidate.signal_id == "sig-v2-execution-gate"
    assert result.candidate.stage == "OPEN_NOW"
    assert result.candidate.buffer_distance == 0.0008
    assert result.candidate.model_expiry == 5.0
    assert result.candidate.open_now_expiry_minutes == 4.5
    assert result.candidate.expiry_minutes == 4.5


def test_model_expiry_201_is_not_rounded_to_external_3m(monkeypatch) -> None:
    _calibrate(monkeypatch, pressure_bias="0.0")
    decision = _decision("OPEN_NOW", 160, model_expiry=2.01)
    persistent = advance_persistent_fsm(_after_pre(), decision, now_ts=161)
    result = prepare_signal_execution(persistent, decision, buffer_mode="MEDIUM", created_ts=162)

    assert result.candidate is not None
    assert result.candidate.model_expiry == 2.01
    assert result.candidate.open_now_expiry_minutes == 2.01
    assert result.candidate.expiry_minutes != 3.0


def test_duplicate_stage_is_blocked_without_candidate(monkeypatch) -> None:
    _uncalibrate(monkeypatch)
    decision = _decision("PRE", 100)
    first = advance_persistent_fsm(default_fsm_state(), decision, now_ts=101)
    duplicate = advance_persistent_fsm(first.next_state, decision, now_ts=102)
    result = prepare_signal_execution(duplicate, decision, buffer_mode="MEDIUM", created_ts=103)

    assert result.outcome == "BLOCKED"
    assert result.reason == "DUPLICATE_STAGE_CANDLE"
    assert result.candidate is None
    assert result.signal_event_available is False
    assert result.distribution_allowed is False


def test_rejected_fsm_result_is_blocked(monkeypatch) -> None:
    _uncalibrate(monkeypatch)
    decision = _decision("OPEN_NOW", 100)
    persistent = advance_persistent_fsm(default_fsm_state(), decision, now_ts=101)
    result = prepare_signal_execution(persistent, decision, buffer_mode="MEDIUM", created_ts=102)

    assert result.outcome == "BLOCKED"
    assert result.candidate is None
    assert result.distribution_allowed is False


def test_incomplete_model_time_stays_blocked(monkeypatch) -> None:
    _calibrate(monkeypatch)
    complete = _decision("OPEN_NOW", 160)
    persistent = advance_persistent_fsm(_after_pre(), complete, now_ts=161)
    incomplete = replace(complete, time=replace(complete.time, model_expiry=None))
    result = prepare_signal_execution(persistent, incomplete, buffer_mode="MEDIUM", created_ts=162)

    assert result.outcome == "BLOCKED"
    assert result.reason.startswith("EXECUTION_TIME_UNAVAILABLE:")
    assert result.candidate is None
    assert result.signal_event_available is False
    assert result.distribution_allowed is False


def test_execution_trace_is_canonical_and_contains_no_delivery_side_effects(monkeypatch) -> None:
    _calibrate(monkeypatch)
    decision = _decision("OPEN_NOW", 160)
    persistent = advance_persistent_fsm(_after_pre(), decision, now_ts=161)
    result = prepare_signal_execution(persistent, decision, buffer_mode="LARGE", created_ts=162)
    trace = result.to_dict()
    event_data = result.to_event_data()

    assert trace["execution_attempt_id"] == "binary-v2:sig-v2-execution-gate:OPEN_NOW:162"
    assert trace["setup_correlation_id"] == "cycle-160"
    assert trace["candidate"]["distribution_enabled"] is False
    assert trace["candidate"]["open_now_expiry_minutes"] == 4.5
    assert trace["distribution_allowed"] is True
    assert event_data["execution_phase"] == "PRE_DISTRIBUTION"
    assert event_data["execution_outcome"] == "DEFERRED"
    assert event_data["execution_time_available"] is True
    assert event_data["destination_state"] == "PRE_DISTRIBUTION_UNRESOLVED"
