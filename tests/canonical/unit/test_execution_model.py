from dataclasses import replace

import pytest

from send.core.decision_object import (
    DecisionObject,
    MarketContext,
    RejectContext,
    ScoreContext,
    SetupContext,
    StrategicFlags,
    StructureContext,
    TimeContext,
)
from send.core.execution_model import (
    ExecutionCalibration,
    ExecutionModelError,
    derive_execution_time,
)
from send.core.fsm_decision_adapter import interpret_decision


def _decision(tier: str) -> DecisionObject:
    return DecisionObject(
        setup=SetupContext("EUR/USD", "BUY", 1_700_000_000, "M1", "cycle-1", "test"),
        market_context=MarketContext(1.1, 0.001, 0.002, "UP", "NORMAL", "LOW"),
        structure=StructureContext(1.09, 1.12, 1.09, 1.12, 0.03, 0.02, "INSIDE", "VALID"),
        time=TimeContext(4.0, 4.0, 5.0, 0.8, None, "READY"),
        score=ScoreContext(80.0, 0.8, {"trend": 24.0}, tier=tier),
        strategic_flags=StrategicFlags(True, True, False, False, False, False, False),
        reject=RejectContext(),
        fsm_inputs={"score_tier": tier},
        explanations=("Canonical evidence.",),
    )


def _calibration() -> ExecutionCalibration:
    return ExecutionCalibration(1.0, 0.1, 2.0, 15.0, "test-calibration-v1")


def test_confirm_produces_a_range_but_not_an_exact_expiry() -> None:
    decision = _decision("SCORE_CONFIRM_BAND")
    result = derive_execution_time(decision, interpret_decision(decision), _calibration())

    assert result.available is True
    assert result.confirm_expiry_min_minutes == 4.0
    assert result.confirm_expiry_max_minutes == 6.0
    assert result.open_now_expiry_minutes is None
    assert result.signal_handoff_ready is False


def test_open_now_is_exact_and_inside_the_confirm_range() -> None:
    decision = _decision("SCORE_OPEN_BAND")
    result = derive_execution_time(decision, interpret_decision(decision), _calibration())

    assert result.open_now_expiry_minutes == 4.5
    assert result.confirm_expiry_min_minutes <= result.open_now_expiry_minutes
    assert result.open_now_expiry_minutes <= result.confirm_expiry_max_minutes
    assert result.signal_handoff_ready is False


def test_missing_calibration_remains_explicitly_unavailable() -> None:
    decision = _decision("SCORE_OPEN_BAND")
    result = derive_execution_time(decision, interpret_decision(decision))

    assert result.available is False
    assert result.open_now_expiry_minutes is None
    assert "not invented" in result.explanation


def test_non_actionable_fsm_outcomes_do_not_expose_expiry() -> None:
    decision = _decision("BELOW_PRE")
    result = derive_execution_time(decision, interpret_decision(decision), _calibration())

    assert result.available is False
    assert result.confirm_expiry_min_minutes is None


def test_mismatched_cycles_are_rejected() -> None:
    decision = _decision("SCORE_OPEN_BAND")
    other = replace(decision, setup=replace(decision.setup, cycle_id="cycle-2"))

    with pytest.raises(ExecutionModelError, match="same cycle"):
        derive_execution_time(other, interpret_decision(decision), _calibration())


@pytest.mark.parametrize(
    "calibration",
    [
        (-1.0, 0.1, 2.0, 15.0),
        (1.0, 1.0, 2.0, 15.0),
        (1.0, 0.1, 0.0, 15.0),
        (1.0, 0.1, 15.0, 2.0),
    ],
)
def test_invalid_calibration_is_rejected(calibration) -> None:
    with pytest.raises(ExecutionModelError):
        ExecutionCalibration(*calibration, source="invalid")
