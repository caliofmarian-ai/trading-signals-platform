from dataclasses import FrozenInstanceError, replace

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
from send.core.fsm_decision_adapter import FSMInterpretationError, interpret_decision


def _decision(tier: str = "SCORE_CONFIRM_BAND") -> DecisionObject:
    return DecisionObject(
        setup=SetupContext("EUR/USD", "BUY", 1_700_000_000, "M1", "cycle-1", "shadow-test"),
        market_context=MarketContext(1.1, 0.001, 0.002, "UP", "NORMAL", "LOW"),
        structure=StructureContext(1.09, 1.12, 1.09, 1.12, 0.03, 0.02, "INSIDE", "VALID"),
        time=TimeContext(2.0, 2.0, 5.0, 0.4, None, "READY"),
        score=ScoreContext(80.0, 0.8, {"trend": 24.0}, tier=tier),
        strategic_flags=StrategicFlags(True, True, False, False, False, False, False),
        reject=RejectContext(),
        fsm_inputs={"score_tier": tier},
        explanations=("Synchronized canonical evidence.",),
    )


@pytest.mark.parametrize(
    ("tier", "outcome", "execution_ready"),
    [
        ("BELOW_PRE", "WAIT", False),
        ("SCORE_PRE_BAND", "PREPARE", False),
        ("SCORE_CONFIRM_BAND", "CONFIRM", False),
        ("SCORE_OPEN_BAND", "OPEN_NOW", True),
    ],
)
def test_score_bands_map_to_canonical_outcome_families(tier, outcome, execution_ready) -> None:
    result = interpret_decision(_decision(tier))

    assert result.outcome == outcome
    assert result.execution_ready is execution_ready
    assert result.signal_handoff_ready is False


def test_strategic_hard_blockers_override_a_high_score() -> None:
    decision = _decision("SCORE_OPEN_BAND")
    decision = replace(
        decision,
        structure=replace(decision.structure, feasibility_state="CONSTRAINED"),
        strategic_flags=replace(decision.strategic_flags, valid_structure=False, rejectable=True),
        reject=RejectContext("Insufficient directional room.", "STRUCTURE", "CORRIDOR", ("room",)),
    )

    result = interpret_decision(decision)

    assert result.outcome == "REJECT"
    assert result.reasons == ("room",)
    assert result.signal_handoff_ready is False


def test_runtime_safety_blockers_have_highest_priority() -> None:
    result = interpret_decision(_decision("SCORE_OPEN_BAND"), runtime_blockers=("market_data_stale",))

    assert result.outcome == "BLOCKED"
    assert result.runtime_blocked is True
    assert result.execution_ready is False
    assert result.signal_handoff_ready is False


def test_degraded_setup_never_becomes_actionable() -> None:
    decision = _decision("SCORE_OPEN_BAND")
    decision = replace(decision, strategic_flags=replace(decision.strategic_flags, degraded_setup=True))

    result = interpret_decision(decision)

    assert result.outcome == "DEGRADED"
    assert result.signal_handoff_ready is False


def test_unknown_score_tier_fails_closed_as_degraded() -> None:
    decision = _decision("FUTURE_TIER")

    result = interpret_decision(decision)

    assert result.outcome == "DEGRADED"
    assert result.reason_family == "UNKNOWN_SCORE_TIER"


def test_contradictory_decision_evidence_is_rejected() -> None:
    decision = _decision()
    decision = replace(decision, strategic_flags=replace(decision.strategic_flags, feasible_time=False))

    with pytest.raises(FSMInterpretationError, match="feasible_time"):
        interpret_decision(decision)


def test_interpretation_is_immutable_and_deterministic() -> None:
    first = interpret_decision(_decision())
    second = interpret_decision(_decision())

    assert first == second
    with pytest.raises(FrozenInstanceError):
        first.outcome = "OPEN_NOW"
