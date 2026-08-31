from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Tuple

from .decision_object import DecisionObject


SCHEMA_VERSION = "1.0.0"
ALLOWED_OUTCOMES = frozenset(
    {"REJECT", "WAIT", "PREPARE", "CONFIRM", "OPEN_NOW", "DEGRADED", "BLOCKED"}
)
_TIER_OUTCOMES = {
    "BELOW_PRE": "WAIT",
    "SCORE_PRE_BAND": "PREPARE",
    "SCORE_CONFIRM_BAND": "CONFIRM",
    "SCORE_OPEN_BAND": "OPEN_NOW",
}


class FSMInterpretationError(ValueError):
    """Raised when a DecisionObject contains contradictory FSM evidence."""


@dataclass(frozen=True)
class FSMInterpretation:
    schema_version: str
    symbol: str
    cycle_id: str
    outcome: str
    reason_family: str
    execution_ready: bool
    degraded: bool
    rejected: bool
    runtime_blocked: bool
    signal_handoff_ready: bool
    reasons: Tuple[str, ...]
    explanation: str


def _clean_runtime_blockers(values: Iterable[str]) -> Tuple[str, ...]:
    blockers = []
    for value in values:
        if not isinstance(value, str) or not value.strip():
            raise FSMInterpretationError("runtime blockers must be non-empty text")
        cleaned = value.strip()
        if cleaned not in blockers:
            blockers.append(cleaned)
    return tuple(blockers)


def _validate_consistency(decision: DecisionObject) -> None:
    has_hard_blockers = bool(decision.reject.hard_blockers)
    if decision.strategic_flags.rejectable != has_hard_blockers:
        raise FSMInterpretationError("rejectable flag contradicts hard-blocker evidence")

    structure_valid = decision.structure.feasibility_state == "VALID"
    if decision.strategic_flags.valid_structure != structure_valid:
        raise FSMInterpretationError("valid_structure flag contradicts structure evidence")

    time_feasible = decision.time.time_state == "READY"
    if decision.strategic_flags.feasible_time != time_feasible:
        raise FSMInterpretationError("feasible_time flag contradicts time evidence")

    if decision.score.tier == "BLOCKED" and not has_hard_blockers:
        raise FSMInterpretationError("BLOCKED score tier requires strategic hard blockers")


def _is_decision_contract(value: object) -> bool:
    return type(value).__name__ == "DecisionObject" and all(
        hasattr(value, field)
        for field in ("setup", "market_context", "structure", "time", "score", "strategic_flags", "reject")
    )


def interpret_decision(
    decision: DecisionObject,
    *,
    runtime_blockers: Iterable[str] = (),
) -> FSMInterpretation:
    """Interpret canonical decision evidence without mutating the live FSM.

    OPEN_NOW means only that the strategic evidence reached that canonical
    family. This shadow adapter never authorizes a signal or broker action.
    """

    if not isinstance(decision, DecisionObject) and not _is_decision_contract(decision):
        raise TypeError("decision must be a DecisionObject")
    blockers = _clean_runtime_blockers(runtime_blockers)
    _validate_consistency(decision)

    if blockers:
        outcome = "BLOCKED"
        reason_family = "RUNTIME_SAFETY"
        reasons = blockers
        explanation = "Runtime safety evidence blocks every downstream action."
    elif decision.strategic_flags.rejectable:
        outcome = "REJECT"
        reason_family = decision.reject.category or "STRATEGIC_REJECTION"
        reasons = tuple(decision.reject.hard_blockers)
        explanation = decision.reject.reason or "Strategic hard blockers require rejection."
    elif decision.strategic_flags.degraded_setup:
        outcome = "DEGRADED"
        reason_family = "INCOMPLETE_OR_DEGRADED_EVIDENCE"
        reasons = tuple(decision.reject.soft_blockers) or ("degraded_setup",)
        explanation = "The evidence is degraded, so no actionable stage is exposed."
    else:
        outcome = _TIER_OUTCOMES.get(decision.score.tier, "DEGRADED")
        if outcome == "DEGRADED":
            reason_family = "UNKNOWN_SCORE_TIER"
            reasons = (decision.score.tier,)
            explanation = "The score tier is not recognized by the canonical FSM adapter."
        else:
            reason_family = "CANONICAL_SCORE_BAND"
            reasons = (decision.score.tier,)
            explanation = f"Canonical score evidence maps to the {outcome} outcome family."

    return FSMInterpretation(
        schema_version=SCHEMA_VERSION,
        symbol=decision.setup.symbol,
        cycle_id=decision.setup.cycle_id,
        outcome=outcome,
        reason_family=reason_family,
        execution_ready=outcome == "OPEN_NOW",
        degraded=outcome == "DEGRADED",
        rejected=outcome == "REJECT",
        runtime_blocked=outcome == "BLOCKED",
        signal_handoff_ready=False,
        reasons=reasons,
        explanation=explanation,
    )
