"""Governed post-FSM execution gate for Binary Strategy V2.

This module consumes the persistent FSM verdict and, only when the FSM exposes
an OPEN_NOW candidate, builds the validated canonical SignalEvent.  It does not
route, publish, register outcomes, call Telegram, or execute broker trades.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

from .decision_object import DecisionObject
from .signal_event import SignalEvent, SignalEventUnavailable, build_signal_event
from .v2_fsm_orchestrator import PersistentFSMResult


EXECUTION_OUTCOMES = frozenset(
    {"EMITTED", "NOT_EMITTED", "BLOCKED", "SKIPPED", "FAILED", "DEFERRED"}
)


@dataclass(frozen=True)
class SignalExecutionGateResult:
    """Execution-layer verdict before any distribution side effect."""

    outcome: str
    reason: str
    signal_id: Optional[str]
    stage: Optional[str]
    execution_attempt_id: str
    created_ts: int
    candidate: Optional[SignalEvent]
    distribution_allowed: bool = False

    def __post_init__(self) -> None:
        if self.outcome not in EXECUTION_OUTCOMES:
            raise ValueError(f"unsupported execution outcome: {self.outcome}")
        if not isinstance(self.reason, str) or not self.reason.strip():
            raise ValueError("reason is required")
        if not isinstance(self.execution_attempt_id, str) or not self.execution_attempt_id.strip():
            raise ValueError("execution_attempt_id is required")
        if not isinstance(self.created_ts, int) or isinstance(self.created_ts, bool) or self.created_ts <= 0:
            raise ValueError("created_ts must be a positive integer")
        if self.distribution_allowed:
            raise ValueError("distribution cannot be enabled by the pre-distribution execution gate")
        if self.candidate is not None:
            if self.signal_id != self.candidate.signal_id:
                raise ValueError("candidate signal_id must match execution result")
            if self.stage != self.candidate.stage:
                raise ValueError("candidate stage must match execution result")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "outcome": self.outcome,
            "reason": self.reason,
            "signal_id": self.signal_id,
            "stage": self.stage,
            "execution_attempt_id": self.execution_attempt_id,
            "created_ts": self.created_ts,
            "distribution_allowed": self.distribution_allowed,
            "candidate": self.candidate.to_dict() if self.candidate is not None else None,
        }


def _attempt_id(decision: DecisionObject, created_ts: int) -> str:
    signal_id = decision.signal_id or "no-signal"
    return f"binary-v2:{signal_id}:{decision.kind}:{created_ts}"


def prepare_signal_execution(
    persistent_fsm: PersistentFSMResult,
    decision: DecisionObject,
    *,
    buffer_mode: str,
    created_ts: int,
) -> SignalExecutionGateResult:
    """Prepare a traceable execution verdict without performing distribution."""

    if not isinstance(persistent_fsm, PersistentFSMResult):
        raise TypeError("persistent_fsm must be a PersistentFSMResult")
    if not isinstance(decision, DecisionObject):
        raise TypeError("decision must be a DecisionObject")

    attempt_id = _attempt_id(decision, created_ts)

    if not persistent_fsm.accepted:
        return SignalExecutionGateResult(
            outcome="BLOCKED",
            reason=persistent_fsm.reason or "FSM_REJECTED_EXECUTION",
            signal_id=decision.signal_id,
            stage=decision.kind,
            execution_attempt_id=attempt_id,
            created_ts=created_ts,
            candidate=None,
        )

    if not persistent_fsm.candidate_ready:
        return SignalExecutionGateResult(
            outcome="NOT_EMITTED",
            reason=persistent_fsm.reason or "FSM_NOT_EXECUTION_READY",
            signal_id=decision.signal_id,
            stage=decision.kind,
            execution_attempt_id=attempt_id,
            created_ts=created_ts,
            candidate=None,
        )

    try:
        candidate = build_signal_event(
            decision,
            buffer_mode=buffer_mode,
            created_ts=created_ts,
        )
    except SignalEventUnavailable as exc:
        return SignalExecutionGateResult(
            outcome="NOT_EMITTED",
            reason=f"SIGNAL_EVENT_UNAVAILABLE:{exc}",
            signal_id=decision.signal_id,
            stage=decision.kind,
            execution_attempt_id=attempt_id,
            created_ts=created_ts,
            candidate=None,
        )

    return SignalExecutionGateResult(
        outcome="DEFERRED",
        reason="V2_DISTRIBUTION_NOT_ENABLED",
        signal_id=candidate.signal_id,
        stage=candidate.stage,
        execution_attempt_id=attempt_id,
        created_ts=created_ts,
        candidate=candidate,
        distribution_allowed=False,
    )
