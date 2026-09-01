"""Governed post-FSM execution gate for Binary Strategy V2.

This module consumes explicit persistent FSM truth. It can construct
PRE/CONFIRM/OPEN_NOW SignalEvent candidates only after exact-stage acceptance.
OPEN_NOW additionally requires an available, governed Execution Time result.
The pre-distribution checkpoint remains DEFERRED and can never claim EMITTED.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

from .decision_object import ACTIONABLE_DECISION_KINDS, DecisionObject
from .execution_model import (
    ExecutionModelError,
    derive_execution_time_for_stage,
    load_execution_calibration_from_env,
)
from .signal_event import SignalEvent, SignalEventUnavailable, build_signal_event
from .v2_fsm_orchestrator import PersistentFSMResult


EXECUTION_OUTCOMES = frozenset(
    {"EMITTED", "NOT_EMITTED", "BLOCKED", "SKIPPED", "FAILED", "DEFERRED"}
)
EXECUTION_PHASE = "PRE_DISTRIBUTION"
PRE_DISTRIBUTION_DESTINATION_STATE = "PRE_DISTRIBUTION_UNRESOLVED"
_BLOCKING_REASON_FAMILIES = frozenset(
    {"COOLDOWN", "FOCUS", "DUPLICATE", "IDENTITY", "LIFECYCLE", "INVALID_TRANSITION"}
)


@dataclass(frozen=True)
class SignalExecutionGateResult:
    """Execution-layer truth before any Distribution side effect."""

    outcome: str
    reason: str
    signal_id: Optional[str]
    stage: Optional[str]
    execution_attempt_id: str
    created_ts: int
    setup_correlation_id: str
    execution_phase: str
    stage_handoff_ready: bool
    trade_execution_ready: bool
    signal_event_available: bool
    destination_state: str
    candidate: Optional[SignalEvent]
    distribution_allowed: bool = False

    def __post_init__(self) -> None:
        if self.outcome not in EXECUTION_OUTCOMES:
            raise ValueError(f"unsupported execution outcome: {self.outcome}")
        if not isinstance(self.reason, str) or not self.reason.strip():
            raise ValueError("reason is required")
        if not isinstance(self.execution_attempt_id, str) or not self.execution_attempt_id.strip():
            raise ValueError("execution_attempt_id is required")
        if not isinstance(self.setup_correlation_id, str) or not self.setup_correlation_id.strip():
            raise ValueError("setup_correlation_id is required")
        if not isinstance(self.created_ts, int) or isinstance(self.created_ts, bool) or self.created_ts <= 0:
            raise ValueError("created_ts must be a positive integer")
        if self.execution_phase != EXECUTION_PHASE:
            raise ValueError("pre-distribution gate must use PRE_DISTRIBUTION phase")
        if self.destination_state != PRE_DISTRIBUTION_DESTINATION_STATE:
            raise ValueError("pre-distribution destination state is unresolved")
        if self.distribution_allowed:
            if self.candidate is None or not self.stage_handoff_ready:
                raise ValueError("distribution requires an available handoff-ready candidate")
            if self.outcome != "DEFERRED":
                raise ValueError("distribution authorization requires a DEFERRED pre-distribution checkpoint")
        if self.signal_event_available != (self.candidate is not None):
            raise ValueError("signal_event_available must match candidate presence")
        if self.candidate is not None:
            if self.signal_id != self.candidate.signal_id:
                raise ValueError("candidate signal_id must match execution result")
            if self.stage != self.candidate.stage:
                raise ValueError("candidate stage must match execution result")
        if self.outcome == "EMITTED":
            raise ValueError("EMITTED is forbidden before governed publication evidence")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "outcome": self.outcome,
            "reason": self.reason,
            "signal_id": self.signal_id,
            "stage": self.stage,
            "execution_attempt_id": self.execution_attempt_id,
            "created_ts": self.created_ts,
            "setup_correlation_id": self.setup_correlation_id,
            "execution_phase": self.execution_phase,
            "stage_handoff_ready": self.stage_handoff_ready,
            "trade_execution_ready": self.trade_execution_ready,
            "signal_event_available": self.signal_event_available,
            "destination_state": self.destination_state,
            "distribution_allowed": self.distribution_allowed,
            "candidate": self.candidate.to_dict() if self.candidate is not None else None,
        }

    def to_event_data(self) -> Dict[str, Any]:
        return {
            "execution_phase": self.execution_phase,
            "execution_outcome": self.outcome,
            "execution_reason": self.reason,
            "stage_handoff_ready": self.stage_handoff_ready,
            "trade_execution_ready": self.trade_execution_ready,
            "signal_event_available": self.signal_event_available,
            "execution_time_available": (
                self.candidate.execution_time_available
                if self.candidate is not None
                else False
            ),
            "destination_state": self.destination_state,
            "candidate_schema_version": self.candidate.schema_version if self.candidate is not None else None,
        }


def _attempt_id(decision: DecisionObject, created_ts: int) -> str:
    signal_id = decision.signal_id or "no-signal"
    return f"binary-v2:{signal_id}:{decision.kind}:{created_ts}"


def _base_result(
    persistent_fsm: PersistentFSMResult,
    decision: DecisionObject,
    *,
    created_ts: int,
    outcome: str,
    reason: str,
    candidate: Optional[SignalEvent] = None,
    distribution_allowed: bool = False,
) -> SignalExecutionGateResult:
    return SignalExecutionGateResult(
        outcome=outcome,
        reason=reason,
        signal_id=decision.signal_id,
        stage=decision.kind if decision.kind in ACTIONABLE_DECISION_KINDS else None,
        execution_attempt_id=_attempt_id(decision, created_ts),
        created_ts=created_ts,
        setup_correlation_id=decision.setup.cycle_id,
        execution_phase=EXECUTION_PHASE,
        stage_handoff_ready=persistent_fsm.stage_handoff_ready,
        trade_execution_ready=persistent_fsm.trade_execution_ready,
        signal_event_available=candidate is not None,
        destination_state=PRE_DISTRIBUTION_DESTINATION_STATE,
        candidate=candidate,
        distribution_allowed=distribution_allowed,
    )


def prepare_signal_execution(
    persistent_fsm: PersistentFSMResult,
    decision: DecisionObject,
    *,
    buffer_mode: str,
    created_ts: int,
) -> SignalExecutionGateResult:
    """Prepare a traceable exact-stage pre-distribution verdict."""

    if not isinstance(persistent_fsm, PersistentFSMResult):
        raise TypeError("persistent_fsm must be a PersistentFSMResult")
    if not isinstance(decision, DecisionObject):
        raise TypeError("decision must be a DecisionObject")

    if decision.kind not in ACTIONABLE_DECISION_KINDS:
        return _base_result(
            persistent_fsm,
            decision,
            created_ts=created_ts,
            outcome="NOT_EMITTED",
            reason="NON_ACTIONABLE_DECISION",
        )

    if persistent_fsm.requested_stage != decision.kind:
        return _base_result(
            persistent_fsm,
            decision,
            created_ts=created_ts,
            outcome="BLOCKED",
            reason="FSM_REQUESTED_STAGE_MISMATCH",
        )

    if not persistent_fsm.stage_handoff_ready:
        outcome = (
            "BLOCKED"
            if not persistent_fsm.accepted or persistent_fsm.reason_family in _BLOCKING_REASON_FAMILIES
            else "NOT_EMITTED"
        )
        return _base_result(
            persistent_fsm,
            decision,
            created_ts=created_ts,
            outcome=outcome,
            reason=persistent_fsm.reason or "FSM_STAGE_HANDOFF_NOT_READY",
        )

    if persistent_fsm.accepted_stage != decision.kind:
        return _base_result(
            persistent_fsm,
            decision,
            created_ts=created_ts,
            outcome="BLOCKED",
            reason="FSM_EXACT_STAGE_ACCEPTANCE_REQUIRED",
        )

    if persistent_fsm.signal_id != decision.signal_id:
        return _base_result(
            persistent_fsm,
            decision,
            created_ts=created_ts,
            outcome="BLOCKED",
            reason="FSM_SIGNAL_ID_MISMATCH",
        )

    try:
        calibration = load_execution_calibration_from_env()
        execution_time = derive_execution_time_for_stage(
            decision,
            decision.kind,
            calibration,
        )
    except ExecutionModelError as exc:
        return _base_result(
            persistent_fsm,
            decision,
            created_ts=created_ts,
            outcome="BLOCKED",
            reason=f"EXECUTION_TIME_INVALID:{exc}",
        )

    if decision.kind == "OPEN_NOW" and not execution_time.available:
        return _base_result(
            persistent_fsm,
            decision,
            created_ts=created_ts,
            outcome="BLOCKED",
            reason=f"EXECUTION_TIME_UNAVAILABLE:{execution_time.explanation}",
        )

    try:
        candidate = build_signal_event(
            decision,
            buffer_mode=buffer_mode,
            created_ts=created_ts,
            execution_time=execution_time,
        )
    except SignalEventUnavailable as exc:
        return _base_result(
            persistent_fsm,
            decision,
            created_ts=created_ts,
            outcome="NOT_EMITTED",
            reason=f"SIGNAL_EVENT_UNAVAILABLE:{exc}",
        )

    return _base_result(
        persistent_fsm,
        decision,
        created_ts=created_ts,
        outcome="DEFERRED",
        reason="DISTRIBUTION_ROUTER_READY",
        candidate=candidate,
        distribution_allowed=True,
    )
