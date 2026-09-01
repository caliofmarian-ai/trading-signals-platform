"""Persistent FSM boundary for Binary Strategy V2.

The boundary exposes the active canonical FSMExecutionHandoff semantics:
requested/accepted stage, stage handoff readiness and final trade-execution
readiness. PRE, CONFIRM and OPEN_NOW may be released to Signal Engine only after
exact-stage acceptance. No FSM result claims external publication.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from math import ceil
from typing import Any, Dict, Optional

from . import fsm_runtime
from .decision_object import ACTIONABLE_DECISION_KINDS, DecisionObject


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

    @property
    def candidate_ready(self) -> bool:
        """Compatibility alias; canonical truth is stage_handoff_ready."""
        return self.stage_handoff_ready


def current_opportunity_signal_id(state: Dict[str, Any], symbol: str) -> Optional[str]:
    symbol_state = (state.get("per_symbol") or {}).get(symbol, {})
    value = symbol_state.get("current_signal_id") if isinstance(symbol_state, dict) else None
    return value.strip() if isinstance(value, str) and value.strip() else None


def _symbol_state_name(state: Dict[str, Any], symbol: str) -> str:
    symbol_state = (state.get("per_symbol") or {}).get(symbol, {})
    return str(symbol_state.get("state") or "IDLE") if isinstance(symbol_state, dict) else "IDLE"


def _runtime_input(decision: DecisionObject, state: Dict[str, Any]) -> Dict[str, Any]:
    current_id = current_opportunity_signal_id(state, decision.setup.symbol)
    model_expiry = decision.time.model_expiry
    expiry_compat = int(ceil(model_expiry)) if isinstance(model_expiry, (int, float)) and model_expiry > 0 else None
    return {
        "kind": decision.kind,
        "signal_id": decision.signal_id or current_id,
        "symbol": decision.setup.symbol,
        "score_total": decision.score.total,
        "candle_ts": decision.setup.evaluated_ts,
        # Legacy FSM TTL compatibility only. Canonical model-time truth remains model_expiry.
        "expiry_minutes": expiry_compat,
    }


def _result(
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

    last_stage_candle_field = {
        "PRE": "last_pre_candle_ts",
        "CONFIRM": "last_confirm_candle_ts",
    }.get(decision.kind)
    if (
        last_stage_candle_field is not None
        and isinstance(symbol_state, dict)
        and current_id == decision.signal_id
        and symbol_state.get(last_stage_candle_field) == decision.setup.evaluated_ts
    ):
        return _result(
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
        return _result(
            accepted=True,
            state_changed=False,
            requested_stage="OPEN_NOW",
            accepted_stage="OPEN_NOW",
            signal_id=decision.signal_id,
            prior_state=prior_state,
            resulting_state=prior_state,
            reason="OPEN_NOW_STAGE_ACCEPTED",
            reason_family="STAGE_ACCEPTED",
            stage_handoff_ready=True,
            trade_execution_ready=True,
            next_state=state,
            transition_event=None,
        )

    try:
        next_state, event = fsm_runtime.apply_transition(working, payload, now_ts)
    except ValueError as exc:
        return _result(
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

    if trigger == "cooldown_active":
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

    return _result(
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
