# /opt/binarybot/core/fsm_runtime.py
# BinaryBot — FSM Runtime (watchlist lifecycle)

from __future__ import annotations
import time
from typing import Dict, Any, Tuple

from . import storage

STATE_PATH = "/opt/binarybot/state/focus_state.json"

MAX_WATCHLIST = 2


def load_state() -> Dict[str, Any]:
    default = {
        "version": "1.0",
        "mode": "WIDE_SCAN",
        "watchlist": [],
        "per_symbol": {},
        "last_updated_ts": int(time.time())
    }
    return storage.load_json(STATE_PATH, default)


def save_state(state: Dict[str, Any]) -> None:
    state["last_updated_ts"] = int(time.time())
    storage.save_json_atomic(STATE_PATH, state)


def enforce_invariants(state: Dict[str, Any]) -> None:
    if len(state["watchlist"]) > MAX_WATCHLIST:
        raise RuntimeError("FSM invariant violated: watchlist overflow")


def apply_transition(
    state: Dict[str, Any],
    decision: Dict[str, Any],
    now_ts: int
) -> Tuple[Dict[str, Any], Dict[str, Any]]:

    symbol = decision.get("symbol")
    kind = decision.get("kind")
    signal_id = decision.get("signal_id")
    candle_ts = decision.get("candle_ts")

    per_symbol = state["per_symbol"].setdefault(symbol, {
        "state": "IDLE",
        "current_signal_id": None,
        "last_pre_candle_ts": None,
        "last_confirm_candle_ts": None,
        "last_open_candle_ts": None,
        "cooldown_until_ts": None,
        "focus_enter_ts": None
    })

    prev_state = per_symbol["state"]
    new_state = prev_state
    trigger = None

    # cooldown block
    cd = per_symbol.get("cooldown_until_ts")
    if cd and now_ts < cd:
        return state, {
            "symbol": symbol,
            "prev_state": prev_state,
            "new_state": prev_state,
            "trigger": "cooldown_block",
            "signal_id": signal_id,
            "candle_ts": candle_ts
        }

    if kind == "PRE":
        if symbol not in state["watchlist"]:
            if len(state["watchlist"]) < MAX_WATCHLIST:
                state["watchlist"].append(symbol)
                per_symbol["focus_enter_ts"] = now_ts
        per_symbol["state"] = "WATCHLIST"
        per_symbol["current_signal_id"] = signal_id
        per_symbol["last_pre_candle_ts"] = candle_ts
        new_state = "WATCHLIST"
        trigger = "pre_emitted"

    elif kind == "CONFIRM":
        per_symbol["last_confirm_candle_ts"] = candle_ts
        new_state = prev_state
        trigger = "confirm_seen"

    elif kind == "OPEN_NOW":
        per_symbol["last_open_candle_ts"] = candle_ts
        per_symbol["state"] = "LIVE_SENT"
        new_state = "LIVE_SENT"
        trigger = "open_sent"

    elif kind == "REJECT":
        new_state = prev_state
        trigger = "reject"

    # After OPEN confirmation we expect /open command from operator
    # Engine will remove from watchlist separately.

    state["mode"] = "FOCUS_MODE" if state["watchlist"] else "WIDE_SCAN"

    enforce_invariants(state)

    return state, {
        "symbol": symbol,
        "prev_state": prev_state,
        "new_state": new_state,
        "trigger": trigger,
        "signal_id": signal_id,
        "candle_ts": candle_ts
    }