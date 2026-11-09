"""Persistent FSM boundary for Binary Strategy V2.

The boundary exposes the active canonical FSMExecutionHandoff semantics:
requested/accepted stage, stage handoff readiness and final trade-execution
readiness. PRE, CONFIRM and OPEN_NOW may be released to Signal Engine only after
exact-stage acceptance. No FSM result claims external publication.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, replace
from hashlib import sha256
from math import isclose, isfinite
from typing import Any, Dict, Optional

from . import fsm_runtime
from .decision_object import ACTIONABLE_DECISION_KINDS, DecisionObject
from .execution_model import ExecutionTimeResult


FSM_IDENTITY_VERSION = "1.0.0"


@dataclass(frozen=True)
class PersistentFSMResult:
    accepted: bool
    state_changed: bool
    requested_stage: Optional[str]
    accepted_stage: Optional[str]
    signal_id: Optional[str]
    prior_state: str
    resulting_state: str
    reason: str
    reason_family: str
    stage_handoff_ready: bool
    trade_execution_ready: bool
    next_state: Dict[str, Any]
    transition_event: Optional[Dict[str, Any]]
    decision_id: str
    decision_audit_id: str
    fsm_transition_id: str

    @property
    def candidate_ready(self) -> bool:
        """Compatibility alias; canonical truth is stage_handoff_ready."""
        return self.stage_handoff_ready


def _execution_unavailable(execution: ExecutionTimeResult, reason: str) -> ExecutionTimeResult:
    return replace(execution, available=False, confirm_expiry_minutes=None,
                   confirm_expiry_min_minutes=None, confirm_expiry_max_minutes=None,
                   open_now_expiry_minutes=None, calibration_source=None,
                   explanation=reason)


def _positive_duration(value: Any) -> bool:
    return (not isinstance(value, bool) and isinstance(value, (int, float))
            and isfinite(value) and value > 0)


def bind_confirmed_execution_time(
    handoff: PersistentFSMResult, decision: DecisionObject, execution: ExecutionTimeResult,
) -> tuple[PersistentFSMResult, ExecutionTimeResult]:
    """Freeze calibrated duration before CONFIRM delivery and revalidate it at OPEN.

    Call immediately after ``advance_persistent_fsm`` and persist the returned
    state before publication. This records a strategy plan, never an API receipt
    or broker action. Legacy in-flight opportunities cannot acquire a plan at
    OPEN. The independent physical research handoff remains unchanged.
    """
    if (decision.fsm_inputs.get("decision_policy") != "PHYSICAL_ONLY_V3"
        or not handoff.stage_handoff_ready
        or handoff.accepted_stage not in {"CONFIRM", "OPEN_NOW"}):
        return handoff, execution
    if (execution.symbol != decision.setup.symbol or execution.cycle_id != decision.setup.cycle_id
        or execution.fsm_outcome != handoff.accepted_stage):
        raise ValueError("confirmed execution must describe the accepted decision cycle and stage")
    row = handoff.next_state["per_symbol"][decision.setup.symbol]
    status = row.get("physical_confirm_execution_status")
    if handoff.accepted_stage == "CONFIRM" and status is None:
        # An old CONFIRM already sent by an earlier version must not be silently
        # upgraded on a later candle without a new published preparation.
        if row.get("physical_confirm_ts") != row.get("last_transition_ts"):
            return handoff, _execution_unavailable(execution, "CONFIRM_DURATION_NOT_FROZEN")
        working = deepcopy(handoff.next_state)
        row = working["per_symbol"][decision.setup.symbol]
        # A calibrated candidate rejected by feasibility is not missing
        # calibration and must never be downgraded into the study path.
        row["physical_confirm_execution_status"] = "BLOCKED" if execution.available else "UNAVAILABLE"
        row["physical_confirm_execution"] = None
        value = execution.confirm_expiry_minutes
        needed = decision.time.t_needed_adjusted
        if (execution.available and all(_positive_duration(item) for item in (
                value, needed, execution.confirm_expiry_min_minutes, execution.confirm_expiry_max_minutes))
            and isinstance(execution.calibration_source, str) and execution.calibration_source.strip()
            and decision.time.time_state == "READY"
            and execution.confirm_expiry_min_minutes <= value <= execution.confirm_expiry_max_minutes
            and (value >= needed or isclose(value, needed, rel_tol=1e-12, abs_tol=1e-12))):
            row["physical_confirm_execution_status"] = "FROZEN"
            row["physical_confirm_execution"] = {
                "signal_id": decision.signal_id, "direction": decision.setup.direction,
                "confirmed_ts": row["physical_confirm_ts"],
                "duration_minutes": value,
                "confirm_min_minutes": execution.confirm_expiry_min_minutes,
                "confirm_max_minutes": execution.confirm_expiry_max_minutes,
                "calibration_source": execution.calibration_source,
            }
        handoff = replace(handoff, next_state=working, state_changed=True)

    plan = row.get("physical_confirm_execution")
    if not isinstance(plan, dict):
        reason = ("CONFIRM_DURATION_BLOCKED" if row.get("physical_confirm_execution_status") == "BLOCKED"
                  else "EXACT_GOVERNED_DURATION_UNAVAILABLE_AT_CONFIRM")
        return handoff, _execution_unavailable(execution, reason)
    if (plan.get("signal_id") != decision.signal_id or plan.get("direction") != decision.setup.direction
        or plan.get("confirmed_ts") != row.get("physical_confirm_ts")):
        return handoff, _execution_unavailable(execution, "CONFIRM_DURATION_IDENTITY_MISMATCH")
    if not execution.available:
        return handoff, _execution_unavailable(execution, "CONFIRM_DURATION_REVALIDATION_UNAVAILABLE")
    if plan.get("calibration_source") != execution.calibration_source:
        return handoff, _execution_unavailable(execution, "CONFIRM_DURATION_CALIBRATION_CHANGED")
    value = plan.get("duration_minutes")
    original_min, original_max = plan.get("confirm_min_minutes"), plan.get("confirm_max_minutes")
    needed = decision.time.t_needed_adjusted
    current_min, current_max = execution.confirm_expiry_min_minutes, execution.confirm_expiry_max_minutes
    if not all(_positive_duration(item) for item in (value, original_min, original_max, needed, current_min, current_max)):
        return handoff, _execution_unavailable(execution, "CONFIRM_DURATION_EVIDENCE_INVALID")
    if (not original_min <= value <= original_max or not current_min <= value <= current_max
        or decision.time.time_state != "READY"
        or (value < needed and not isclose(value, needed, rel_tol=1e-12, abs_tol=1e-12))):
        return handoff, _execution_unavailable(execution, "CONFIRM_DURATION_NO_LONGER_FEASIBLE")
    return handoff, replace(
        execution, confirm_expiry_minutes=value,
        confirm_expiry_min_minutes=max(original_min, current_min),
        confirm_expiry_max_minutes=min(original_max, current_max),
        open_now_expiry_minutes=value if handoff.accepted_stage == "OPEN_NOW" else None,
        explanation="The exact duration prepared at CONFIRM remains feasible and is preserved unchanged.",
    )


def current_opportunity_signal_id(state: Dict[str, Any], symbol: str) -> Optional[str]:
    symbol_state = (state.get("per_symbol") or {}).get(symbol, {})
    value = symbol_state.get("current_signal_id") if isinstance(symbol_state, dict) else None
    return value.strip() if isinstance(value, str) and value.strip() else None


def _symbol_state_name(state: Dict[str, Any], symbol: str) -> str:
    symbol_state = (state.get("per_symbol") or {}).get(symbol, {})
    return str(symbol_state.get("state") or "IDLE") if isinstance(symbol_state, dict) else "IDLE"


def _runtime_input(decision: DecisionObject, state: Dict[str, Any]) -> Dict[str, Any]:
    current_id = current_opportunity_signal_id(state, decision.setup.symbol)
    payload = {
        "kind": decision.kind,
        "signal_id": decision.signal_id or current_id,
        "symbol": decision.setup.symbol,
        "score_total": decision.score.total,
        "candle_ts": decision.setup.evaluated_ts,
        # Keep legacy FSM focus/cooldown TTL behavior unchanged. Model Time is
        # strategic evidence and is not silently repurposed as lifecycle TTL.
        "expiry_minutes": None,
    }
    if decision.fsm_inputs.get("decision_policy") == "PHYSICAL_ONLY_V3":
        payload.pop("score_total")
        payload["decision_policy"] = "PHYSICAL_ONLY_V3"
    return payload


def _materialize_fsm_transition_id(
    decision: DecisionObject,
    *,
    requested_stage: Optional[str],
    accepted_stage: Optional[str],
    prior_state: str,
    resulting_state: str,
    reason: str,
) -> str:
    canonical = "\x1f".join(
        (
            FSM_IDENTITY_VERSION,
            decision.decision_id,
            decision.decision_audit_id,
            requested_stage or "NO_REQUESTED_STAGE",
            accepted_stage or "NO_ACCEPTED_STAGE",
            prior_state,
            resulting_state,
            reason,
            str(decision.setup.evaluated_ts),
        )
    )
    digest = sha256(f"fsm-transition|{canonical}".encode("utf-8")).hexdigest()[:24]
    return f"fsm-v1-{digest}"


def _result(
    decision: DecisionObject,
    *,
    accepted: bool,
    state_changed: bool,
    requested_stage: Optional[str],
    accepted_stage: Optional[str],
    signal_id: Optional[str],
    prior_state: str,
    resulting_state: str,
    reason: str,
    reason_family: str,
    stage_handoff_ready: bool,
    trade_execution_ready: bool,
    next_state: Dict[str, Any],
    transition_event: Optional[Dict[str, Any]],
) -> PersistentFSMResult:
    return PersistentFSMResult(
        accepted=accepted,
        state_changed=state_changed,
        requested_stage=requested_stage,
        accepted_stage=accepted_stage,
        signal_id=signal_id,
        prior_state=prior_state,
        resulting_state=resulting_state,
        reason=reason,
        reason_family=reason_family,
        stage_handoff_ready=stage_handoff_ready,
        trade_execution_ready=trade_execution_ready,
        next_state=next_state,
        transition_event=transition_event,
        decision_id=decision.decision_id,
        decision_audit_id=decision.decision_audit_id,
        fsm_transition_id=_materialize_fsm_transition_id(
            decision,
            requested_stage=requested_stage,
            accepted_stage=accepted_stage,
            prior_state=prior_state,
            resulting_state=resulting_state,
            reason=reason,
        ),
    )


def advance_persistent_fsm(
    state: Dict[str, Any], decision: DecisionObject, *, now_ts: int
) -> PersistentFSMResult:
    """Apply lifecycle evidence and expose exact-stage Signal Engine handoff truth."""

    if not isinstance(decision, DecisionObject):
        raise TypeError("decision must be a DecisionObject")
    working = deepcopy(state)
    fsm_runtime.enforce_invariants(working)
    payload = _runtime_input(decision, working)
    current_id = current_opportunity_signal_id(working, decision.setup.symbol)
    symbol_state = (working.get("per_symbol") or {}).get(decision.setup.symbol, {})
    prior_state = _symbol_state_name(working, decision.setup.symbol)
    requested_stage = decision.kind if decision.kind in ACTIONABLE_DECISION_KINDS else None
    physical_only = decision.fsm_inputs.get("decision_policy") == "PHYSICAL_ONLY_V3"
    if (physical_only and decision.kind in ACTIONABLE_DECISION_KINDS
        and symbol_state.get("physical_closed_signal_id") == decision.signal_id):
        return _result(decision, accepted=True, state_changed=False,
            requested_stage=requested_stage, accepted_stage=None, signal_id=decision.signal_id,
            prior_state=prior_state, resulting_state=prior_state,
            reason="DUPLICATE_CLOSED_OPPORTUNITY", reason_family="DUPLICATE",
            stage_handoff_ready=False, trade_execution_ready=False,
            next_state=state, transition_event=None)
    if physical_only and decision.kind in {"CONFIRM", "OPEN_NOW"}:
        pre_ts = symbol_state.get("physical_pre_ts")
        confirm_ts = symbol_state.get("physical_confirm_ts")
        ordered = (symbol_state.get("physical_signal_id") == decision.signal_id
                   and symbol_state.get("physical_history_policy") == decision.fsm_inputs.get("history_policy")
                   and symbol_state.get("physical_direction") == decision.setup.direction
                   and isinstance(pre_ts, (int, float)) and not isinstance(pre_ts, bool)
                   and 0 <= pre_ts < now_ts)
        if decision.kind == "OPEN_NOW":
            ordered = (ordered and isinstance(confirm_ts, (int, float)) and not isinstance(confirm_ts, bool)
                       and pre_ts < confirm_ts < now_ts and now_ts - pre_ts >= 30)
        if not ordered:
            return _result(decision, accepted=False, state_changed=False,
                requested_stage=requested_stage, accepted_stage=None, signal_id=decision.signal_id,
                prior_state=prior_state, resulting_state=prior_state,
                reason="PHYSICAL_LIFECYCLE_ORDER_REQUIRED", reason_family="LIFECYCLE",
                stage_handoff_ready=False, trade_execution_ready=False,
                next_state=state, transition_event=None)

    last_stage_candle_field = {
        "PRE": "last_pre_candle_ts",
        "CONFIRM": "last_confirm_candle_ts",
        "OPEN_NOW": "last_open_candle_ts",
    }.get(decision.kind)
    if (
        last_stage_candle_field is not None
        and isinstance(symbol_state, dict)
        and current_id == decision.signal_id
        and symbol_state.get(last_stage_candle_field) == decision.setup.evaluated_ts
    ):
        return _result(
            decision,
            accepted=True,
            state_changed=False,
            requested_stage=requested_stage,
            accepted_stage=None,
            signal_id=decision.signal_id,
            prior_state=prior_state,
            resulting_state=prior_state,
            reason="DUPLICATE_STAGE_CANDLE",
            reason_family="DUPLICATE",
            stage_handoff_ready=False,
            trade_execution_ready=False,
            next_state=state,
            transition_event=None,
        )

    if decision.kind in {"CONFIRM", "OPEN_NOW"} and current_id != decision.signal_id:
        return _result(
            decision,
            accepted=False,
            state_changed=False,
            requested_stage=requested_stage,
            accepted_stage=None,
            signal_id=decision.signal_id,
            prior_state=prior_state,
            resulting_state=prior_state,
            reason="SIGNAL_ID_CONTINUITY_REQUIRED",
            reason_family="IDENTITY",
            stage_handoff_ready=False,
            trade_execution_ready=False,
            next_state=state,
            transition_event=None,
        )

    if decision.kind == "OPEN_NOW":
        if prior_state not in {"WATCHLIST", "CONFIRMED"}:
            return _result(
                decision,
                accepted=False,
                state_changed=False,
                requested_stage="OPEN_NOW",
                accepted_stage=None,
                signal_id=decision.signal_id,
                prior_state=prior_state,
                resulting_state=prior_state,
                reason="CANONICAL_PRE_PATH_REQUIRED",
                reason_family="LIFECYCLE",
                stage_handoff_ready=False,
                trade_execution_ready=False,
                next_state=state,
                transition_event=None,
            )

        # OPEN_NOW must not reuse the legacy fsm_runtime transition because that
        # transition marks LIVE_SENT before downstream publication succeeds. The
        # FSM nevertheless owns duplicate lifecycle suppression, so persist only
        # the fact that this opportunity/stage/candle was released. This marker
        # is restart-safe and does not claim distribution or broker execution.
        if not isinstance(symbol_state, dict):
            raise RuntimeError("FSM invariant violated: missing per-symbol state for OPEN_NOW")
        symbol_state["last_open_candle_ts"] = decision.setup.evaluated_ts
        symbol_state["last_transition_ts"] = now_ts
        if physical_only:
            # Internal OPEN acceptance closes the idea for deduplication only.
            # It makes no claim of external publication or a broker execution.
            symbol_state["physical_closed_signal_id"] = decision.signal_id
        state_changed = working != state

        return _result(
            decision,
            accepted=True,
            state_changed=state_changed,
            requested_stage="OPEN_NOW",
            accepted_stage="OPEN_NOW",
            signal_id=decision.signal_id,
            prior_state=prior_state,
            resulting_state=prior_state,
            reason="OPEN_NOW_STAGE_ACCEPTED",
            reason_family="STAGE_ACCEPTED",
            stage_handoff_ready=True,
            trade_execution_ready=True,
            next_state=working,
            transition_event=None,
        )

    # A newly accepted PRE establishes a new opportunity identity. Clear the
    # prior opportunity's OPEN_NOW marker before applying the PRE transition so
    # an unrelated opportunity evaluated on the same candle cannot be falsely
    # suppressed by the old identity's marker.
    if (
        decision.kind == "PRE"
        and isinstance(symbol_state, dict)
        and current_id is not None
        and current_id != decision.signal_id
    ):
        symbol_state["last_open_candle_ts"] = None
        if physical_only:
            symbol_state["last_confirm_candle_ts"] = None
            symbol_state["physical_confirm_ts"] = None

    try:
        next_state, event = fsm_runtime.apply_transition(working, payload, now_ts)
    except ValueError as exc:
        return _result(
            decision,
            accepted=False,
            state_changed=False,
            requested_stage=requested_stage,
            accepted_stage=None,
            signal_id=decision.signal_id,
            prior_state=prior_state,
            resulting_state=prior_state,
            reason=str(exc),
            reason_family="INVALID_TRANSITION",
            stage_handoff_ready=False,
            trade_execution_ready=False,
            next_state=state,
            transition_event=None,
        )

    trigger = str((event or {}).get("trigger") or "NO_STATE_CHANGE")
    resulting_state = _symbol_state_name(next_state, decision.setup.symbol)
    state_changed = next_state != state

    if trigger == "cross_symbol_attention_active":
        accepted = False
        accepted_stage = None
        reason_family = "ATTENTION"
        handoff = False
    elif trigger == "cooldown_active":
        accepted = False
        accepted_stage = None
        reason_family = "COOLDOWN"
        handoff = False
    elif trigger == "watchlist_full":
        accepted = False
        accepted_stage = None
        reason_family = "FOCUS"
        handoff = False
    elif decision.kind == "PRE" and trigger in {"watchlist_added", "watchlist_replaced", "watchlist_refreshed"}:
        accepted = True
        accepted_stage = "PRE"
        reason_family = "STAGE_ACCEPTED"
        handoff = True
    elif decision.kind == "CONFIRM" and trigger == "confirm_seen":
        accepted = True
        accepted_stage = "CONFIRM"
        reason_family = "STAGE_ACCEPTED"
        handoff = True
    else:
        accepted = True
        accepted_stage = None
        reason_family = "FSM_TRANSITION" if event is not None else "NON_ACTIONABLE"
        handoff = False

    if physical_only and handoff:
        row = next_state["per_symbol"][decision.setup.symbol]
        if accepted_stage == "PRE":
            row.update(physical_signal_id=decision.signal_id, physical_pre_ts=now_ts,
                       physical_history_policy=decision.fsm_inputs.get("history_policy"),
                       physical_confirm_ts=None, physical_confirm_model_seconds=None,
                       physical_confirm_execution_status=None, physical_confirm_execution=None,
                       physical_calibration_captured_signal_id=None, physical_direction=decision.setup.direction)
        elif accepted_stage == "CONFIRM" and row.get("physical_confirm_ts") is None:
            row["physical_confirm_ts"] = now_ts
            row["physical_confirm_model_seconds"] = decision.time.model_expiry * 60
        state_changed = next_state != state
    return _result(
        decision,
        accepted=accepted,
        state_changed=state_changed,
        requested_stage=requested_stage,
        accepted_stage=accepted_stage,
        signal_id=decision.signal_id,
        prior_state=prior_state,
        resulting_state=resulting_state,
        reason=trigger,
        reason_family=reason_family,
        stage_handoff_ready=handoff,
        trade_execution_ready=False,
        next_state=next_state,
        transition_event=event,
    )
