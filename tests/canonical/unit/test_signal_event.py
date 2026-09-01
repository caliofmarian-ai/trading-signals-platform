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
from core.execution_model import ExecutionCalibration, derive_execution_time_for_stage
from core.signal_event import SignalEventUnavailable, build_signal_event


def _decision(kind: str = "OPEN_NOW", *, model_expiry: float = 5.0) -> DecisionObject:
    tier = {
        "PRE": "SCORE_PRE_BAND",
        "CONFIRM": "SCORE_CONFIRM_BAND",
        "OPEN_NOW": "SCORE_OPEN_BAND",
        "NO_SIGNAL": "BELOW_PRE",
    }[kind]
    return DecisionObject(
        kind=kind,
        signal_id="sig-v2-real-opportunity" if kind in {"PRE", "CONFIRM", "OPEN_NOW"} else None,
        setup=SetupContext("EUR/USD", "BUY", 1_720_000_000, "M1", "cycle-real", "binary_strategy_v2"),
        market_context=MarketContext(1.11234, 0.0002, 0.0008, "UP", "ACTIVE", "STABLE", 0.0012),
        structure=StructureContext(1.11, 1.12, 1.11, 1.12, 0.01, 0.0012, "INSIDE", "VALID"),
        time=TimeContext(3.1, 3.8, model_expiry, 3.8 / model_expiry, None, "READY"),
        score=ScoreContext(86.0, 0.86, {"trend": 24.0}, tier=tier),
        strategic_flags=StrategicFlags(True, True, False, False, False, False, False),
        reject=RejectContext(),
        fsm_inputs={"score_tier": tier},
        explanations=("Real canonical evidence.",),
    )


def _execution(decision: DecisionObject, *, pressure_bias: float = 0.1):
    calibration = ExecutionCalibration(
        1.0,
        pressure_bias,
        2.0,
        15.0,
        "signal-event-test",
    )
    return derive_execution_time_for_stage(decision, decision.kind, calibration)


def test_builds_complete_internal_v3_candidate_with_governed_open_now_expiry() -> None:
    decision = _decision()
    event = build_signal_event(
        decision,
        buffer_mode="medium",
        created_ts=1_720_000_002,
        execution_time=_execution(decision),
    )

    assert event.stage == "OPEN_NOW"
    assert event.signal_id == "sig-v2-real-opportunity"
    assert event.buffer_distance == pytest.approx(0.0008)
    assert event.model_expiry == pytest.approx(5.0)
    assert event.open_now_expiry_minutes == pytest.approx(4.5)
    assert event.expiry_minutes == pytest.approx(4.5)
    assert event.execution_time_available is True
    assert event.execution_calibration_source == "signal-event-test"
    assert event.entry_price == pytest.approx(1.11234)
    assert event.distribution_enabled is False
    assert event.payload["canonical_specification"] == "ALGO_SPEC_v3.0.0"


def test_model_expiry_is_never_rounded_into_external_expiry() -> None:
    decision = _decision(model_expiry=2.01)
    event = build_signal_event(
        decision,
        buffer_mode="MEDIUM",
        created_ts=1_720_000_002,
        execution_time=_execution(decision, pressure_bias=0.0),
    )
    assert event.model_expiry == pytest.approx(2.01)
    assert event.open_now_expiry_minutes == pytest.approx(2.01)
    assert event.expiry_minutes != 3.0


def test_open_now_without_governed_execution_time_is_rejected() -> None:
    with pytest.raises(SignalEventUnavailable, match="Execution Time"):
        build_signal_event(_decision(), buffer_mode="MEDIUM", created_ts=1_720_000_002)


def test_pre_has_no_trader_facing_expiry() -> None:
    event = build_signal_event(
        _decision("PRE"),
        buffer_mode="SMALL",
        created_ts=1_720_000_002,
    )
    assert event.execution_time_available is False
    assert event.expiry_minutes is None
    assert event.open_now_expiry_minutes is None


def test_confirm_can_carry_governed_interval_without_exact_open_expiry() -> None:
    decision = _decision("CONFIRM")
    event = build_signal_event(
        decision,
        buffer_mode="SMALL",
        created_ts=1_720_000_002,
        execution_time=_execution(decision),
    )
    assert event.execution_time_available is True
    assert event.confirm_expiry_min_minutes == pytest.approx(4.0)
    assert event.confirm_expiry_max_minutes == pytest.approx(6.0)
    assert event.open_now_expiry_minutes is None
    assert event.expiry_minutes is None


def test_legacy_buffer_price_is_only_explicit_distance_alias() -> None:
    payload = build_signal_event(
        _decision("PRE"), buffer_mode="SMALL", created_ts=1_720_000_002
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


def test_refuses_non_actionable_or_incomplete_real_time_evidence() -> None:
    with pytest.raises(SignalEventUnavailable, match="actionable"):
        build_signal_event(_decision("NO_SIGNAL"), buffer_mode="MEDIUM", created_ts=1_720_000_002)

    incomplete = replace(_decision("PRE"), time=replace(_decision("PRE").time, model_expiry=None))
    with pytest.raises(SignalEventUnavailable, match="model_expiry"):
        build_signal_event(incomplete, buffer_mode="MEDIUM", created_ts=1_720_000_002)


def test_refuses_unknown_buffer_mode_and_cannot_enable_distribution() -> None:
    with pytest.raises(SignalEventUnavailable, match="buffer_mode"):
        build_signal_event(_decision("PRE"), buffer_mode="invented", created_ts=1_720_000_002)

    event = build_signal_event(_decision("PRE"), buffer_mode="MEDIUM", created_ts=1_720_000_002)
    with pytest.raises(SignalEventUnavailable, match="distribution"):
        replace(event, distribution_enabled=True)
