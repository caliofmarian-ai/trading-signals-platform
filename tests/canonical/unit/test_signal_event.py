from __future__ import annotations

from dataclasses import replace

import pytest

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
from core.signal_event import SignalEventUnavailable, build_signal_event


def _decision(kind: str = "OPEN_NOW", *, model_expiry: float = 5.0) -> DecisionObject:
    tier = {
        "PRE": "SCORE_PRE_BAND",
        "CONFIRM": "SCORE_CONFIRM_BAND",
        "OPEN_NOW": "SCORE_OPEN_BAND",
    }.get(kind, "BELOW_PRE")
    return DecisionObject(
        kind=kind,
        signal_id="sig-v2-real-opportunity" if kind in {"PRE", "CONFIRM", "OPEN_NOW"} else None,
        setup=SetupContext("EUR/USD", "BUY", 1_720_000_000, "M1", "cycle-real", "binary_strategy_v2"),
        market_context=MarketContext(1.11234, 0.0002, 0.0008, "UP", "ACTIVE", "STABLE", 0.0012),
        structure=StructureContext(1.11, 1.12, 1.11, 1.12, 0.01, 0.0012, "INSIDE", "VALID"),
        time=TimeContext(3.1, 3.8, model_expiry, 0.76, None, "READY"),
        score=ScoreContext(86.0, 0.86, {"trend": 24.0}, tier=tier),
        strategic_flags=StrategicFlags(True, True, False, False, False, False, kind == "PRE"),
        reject=RejectContext(),
        fsm_inputs={"score_tier": tier},
        explanations=("Real canonical evidence.",),
    )


def _calibration(*, pressure_bias: float = 0.1) -> ExecutionCalibration:
    return ExecutionCalibration(
        confirm_delta_minutes=1.0,
        pressure_bias=pressure_bias,
        minimum_expiry_minutes=1.0,
        maximum_expiry_minutes=15.0,
        source="test-calibration-v1",
    )


def _execution(decision: DecisionObject, *, calibrated: bool = True):
    return derive_execution_time(
        decision,
        interpret_decision(decision),
        _calibration() if calibrated else None,
    )


def test_open_now_requires_governed_execution_time() -> None:
    with pytest.raises(SignalEventUnavailable, match="governed Execution Time"):
        build_signal_event(_decision(), buffer_mode="MEDIUM", created_ts=1_720_000_002)


def test_unavailable_execution_time_cannot_be_replaced_by_model_time() -> None:
    decision = _decision()
    unavailable = _execution(decision, calibrated=False)
    assert unavailable.available is False
    assert unavailable.open_now_expiry_minutes is None

    with pytest.raises(SignalEventUnavailable, match="governed Execution Time"):
        build_signal_event(
            decision,
            buffer_mode="MEDIUM",
            created_ts=1_720_000_002,
            execution_time=unavailable,
        )


def test_builds_complete_internal_v3_candidate_from_exact_execution_time() -> None:
    decision = _decision()
    execution = _execution(decision)
    event = build_signal_event(
        decision,
        buffer_mode="medium",
        created_ts=1_720_000_002,
        execution_time=execution,
    )

    assert event.stage == "OPEN_NOW"
    assert event.signal_id == "sig-v2-real-opportunity"
    assert event.buffer_distance == pytest.approx(0.0008)
    assert event.model_expiry == pytest.approx(5.0)
    assert event.execution_time_available is True
    assert event.confirm_expiry_min_minutes == pytest.approx(4.0)
    assert event.confirm_expiry_max_minutes == pytest.approx(6.0)
    assert event.open_now_expiry_minutes == pytest.approx(4.5)
    assert event.expiry_minutes == pytest.approx(4.5)
    assert event.execution_calibration_source == "test-calibration-v1"
    assert event.entry_price == pytest.approx(1.11234)
    assert event.distribution_enabled is False
    assert event.payload["canonical_specification"] == "ALGO_SPEC_v3.0.0"
    assert event.payload["execution_time"]["open_now_expiry_minutes"] == pytest.approx(4.5)


def test_fractional_execution_expiry_is_never_ceiled_or_truncated() -> None:
    decision = _decision(model_expiry=5.3)
    execution = _execution(decision)
    event = build_signal_event(
        decision,
        buffer_mode="MEDIUM",
        created_ts=1_720_000_002,
        execution_time=execution,
    )

    assert execution.open_now_expiry_minutes == pytest.approx(4.77)
    assert event.model_expiry == pytest.approx(5.3)
    assert event.open_now_expiry_minutes == pytest.approx(4.77)
    assert event.expiry_minutes == pytest.approx(4.77)
    assert event.expiry_minutes != 5
    assert event.expiry_minutes != 6


def test_pre_and_confirm_do_not_expose_generic_exact_expiry() -> None:
    pre = _decision("PRE")
    pre_event = build_signal_event(pre, buffer_mode="MEDIUM", created_ts=1_720_000_002)
    assert pre_event.execution_time_available is False
    assert pre_event.expiry_minutes is None
    assert pre_event.open_now_expiry_minutes is None

    confirm = _decision("CONFIRM")
    confirm_execution = _execution(confirm)
    confirm_event = build_signal_event(
        confirm,
        buffer_mode="MEDIUM",
        created_ts=1_720_000_002,
        execution_time=confirm_execution,
    )
    assert confirm_event.execution_time_available is True
    assert confirm_event.confirm_expiry_min_minutes == pytest.approx(4.0)
    assert confirm_event.confirm_expiry_max_minutes == pytest.approx(6.0)
    assert confirm_event.open_now_expiry_minutes is None
    assert confirm_event.expiry_minutes is None


def test_legacy_buffer_price_is_only_explicit_distance_alias() -> None:
    decision = _decision()
    payload = build_signal_event(
        decision,
        buffer_mode="SMALL",
        created_ts=1_720_000_002,
        execution_time=_execution(decision),
    ).to_dict()
    assert payload["buffer_price"] == payload["buffer_distance"]


def test_same_identity_survives_pre_confirm_open_lifecycle() -> None:
    pre = _decision("PRE")
    confirm = _decision("CONFIRM")
    open_now = _decision("OPEN_NOW")
    events = (
        build_signal_event(pre, buffer_mode="LARGE", created_ts=1_720_000_002),
        build_signal_event(
            confirm,
            buffer_mode="LARGE",
            created_ts=1_720_000_002,
            execution_time=_execution(confirm),
        ),
        build_signal_event(
            open_now,
            buffer_mode="LARGE",
            created_ts=1_720_000_002,
            execution_time=_execution(open_now),
        ),
    )
    assert {event.signal_id for event in events} == {"sig-v2-real-opportunity"}


def test_execution_time_must_match_decision_cycle_and_stage() -> None:
    decision = _decision()
    execution = _execution(decision)

    wrong_cycle = replace(execution, cycle_id="other-cycle")
    with pytest.raises(SignalEventUnavailable, match="same symbol/cycle"):
        build_signal_event(
            decision,
            buffer_mode="MEDIUM",
            created_ts=1_720_000_002,
            execution_time=wrong_cycle,
        )

    wrong_stage = replace(execution, fsm_outcome="CONFIRM")
    with pytest.raises(SignalEventUnavailable, match="does not match"):
        build_signal_event(
            decision,
            buffer_mode="MEDIUM",
            created_ts=1_720_000_002,
            execution_time=wrong_stage,
        )


def test_refuses_non_actionable_or_incomplete_real_time_evidence() -> None:
    with pytest.raises(SignalEventUnavailable, match="actionable"):
        build_signal_event(_decision("NO_SIGNAL"), buffer_mode="MEDIUM", created_ts=1_720_000_002)

    decision = _decision()
    incomplete = replace(decision, time=replace(decision.time, model_expiry=None))
    with pytest.raises(SignalEventUnavailable, match="model_expiry"):
        build_signal_event(
            incomplete,
            buffer_mode="MEDIUM",
            created_ts=1_720_000_002,
            execution_time=_execution(decision),
        )


def test_refuses_unknown_buffer_mode_and_cannot_enable_distribution() -> None:
    decision = _decision()
    execution = _execution(decision)
    with pytest.raises(SignalEventUnavailable, match="buffer_mode"):
        build_signal_event(
            decision,
            buffer_mode="invented",
            created_ts=1_720_000_002,
            execution_time=execution,
        )

    event = build_signal_event(
        decision,
        buffer_mode="MEDIUM",
        created_ts=1_720_000_002,
        execution_time=execution,
    )
    with pytest.raises(SignalEventUnavailable, match="distribution"):
        replace(event, distribution_enabled=True)
