"""Persistent FSM boundary for Binary Strategy V2.

PRE, CONFIRM, REJECT and NO_SIGNAL may update lifecycle evidence. OPEN_NOW
becomes a candidate for the governed SignalEvent execution layer, but remains
not LIVE_SENT until a later distribution step confirms a successful handoff.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import Any, Dict, Optional

from . import fsm_runtime
from .decision_object import DecisionObject


@dataclass(frozen=True)
class PersistentFSMResult:
    accepted: bool
    state_changed: bool
    candidate_ready: bool
    reason: str
    next_state: Dict[str, Any]
    transition_event: Optional[Dict[str, Any]]


def current_opportunity_signal_id(state: Dict[str, Any], symbol: str) -> Optional[str]:
    symbol_state = (state.get("per_symbol") or {}).get(symbol, {})
    value = symbol_state.get("current_signal_id") if isinstance(symbol_state, dict) else None
    return value.strip() if isinstance(value, str) and value.strip() else None


def _runtime_input(decision: DecisionObject, state: Dict[str, Any]) -> Dict[str, Any]:
    current_id = current_opportunity_signal_id(state, decision.setup.symbol)
    return {
        "kind": decision.kind,
        "signal_id": decision.signal_id or current_id,
        "symbol": decision.setup.symbol,
        "score_total": decision.score.total,
        "candle_ts": decision.setup.evaluated_ts,
        "expiry_minutes": None,
    }


def advance_persistent_fsm(
    state: Dict[str, Any], decision: DecisionObject, *, now_ts: int
) -> PersistentFSMResult:
    """Apply lifecycle evidence and expose governed OPEN_NOW candidate readiness."""

    if not isinstance(decision, DecisionObject):
        raise TypeError("decision must be a DecisionObject")
    working = deepcopy(state)
    fsm_runtime.enforce_invariants(working)
    payload = _runtime_input(decision, working)
    current_id = current_opportunity_signal_id(working, decision.setup.symbol)
    symbol_state = (working.get("per_symbol") or {}).get(decision.setup.symbol, {})

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
        return PersistentFSMResult(
            True, False, False, "DUPLICATE_STAGE_CANDLE", state, None
        )

    if decision.kind in {"CONFIRM", "OPEN_NOW"} and current_id != decision.signal_id:
        return PersistentFSMResult(
            False, False, False, "SIGNAL_ID_CONTINUITY_REQUIRED", state, None
        )

    if decision.kind == "OPEN_NOW":
        prior = symbol_state.get("state") if isinstance(symbol_state, dict) else "IDLE"
        if prior not in {"WATCHLIST", "CONFIRMED"}:
            return PersistentFSMResult(
                False, False, False, "CANONICAL_PRE_PATH_REQUIRED", state, None
            )
        return PersistentFSMResult(
            True, False, True, "SIGNAL_EVENT_CANDIDATE_READY", state, None
        )

    try:
        next_state, event = fsm_runtime.apply_transition(working, payload, now_ts)
    except ValueError as exc:
        return PersistentFSMResult(False, False, False, str(exc), state, None)

    return PersistentFSMResult(
        True,
        next_state != state,
        False,
        "FSM_TRANSITION_APPLIED" if event is not None else "NO_STATE_CHANGE",
        next_state,
        event,
    )
