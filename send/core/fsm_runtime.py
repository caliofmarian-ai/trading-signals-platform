# /opt/binarybot/core/fsm_runtime.py
# BinaryBot — FSM Runtime (watchlist lifecycle)

from __future__ import annotations

import time
from typing import Any, Dict, Iterable, List, Optional, Tuple

from state_store import state_store as runtime_state_store


STATE_PATH = runtime_state_store.FOCUS_STATE_PATH

MAX_WATCHLIST = 2
DEFAULT_FOCUS_TTL_SECONDS = 15 * 60
DEFAULT_COOLDOWN_SECONDS = 5 * 60
PHYSICAL_FOCUS_POLICY = "SAME_SYMBOL_FREE_CROSS_SYMBOL_120S_V1"
CROSS_SYMBOL_ATTENTION_SECONDS = 120


def _default_symbol_state() -> Dict[str, Any]:
    return {
        "state": "IDLE",
        "current_signal_id": None,
        "last_pre_candle_ts": None,
        "last_confirm_candle_ts": None,
        "last_open_candle_ts": None,
        "cooldown_until_ts": None,
        "focus_enter_ts": None,
        "focus_ttl_seconds": None,
        "last_exit_reason": None,
        "last_transition_ts": None,
        "replacement_score": None,
        "replacement_score_ts": None,
    }


def _sync_state(target: Dict[str, Any], normalized: Dict[str, Any]) -> Dict[str, Any]:
    target.clear()
    target.update(normalized)
    return target


def load_state() -> Dict[str, Any]:
    state = runtime_state_store.load_fsm_state(path=STATE_PATH)
    enforce_invariants(state)
    return state


def save_state(state: Dict[str, Any]) -> None:
    normalized = runtime_state_store.validate_fsm_state(state)
    normalized["last_updated_ts"] = int(time.time())
    runtime_state_store.save_fsm_state(normalized, path=STATE_PATH)
    _sync_state(state, normalized)


def enforce_invariants(state: Dict[str, Any]) -> None:
    normalized = runtime_state_store.validate_fsm_state(state)
    watchlist = normalized["watchlist"]
    if len(watchlist) > MAX_WATCHLIST:
        raise RuntimeError("FSM invariant violated: watchlist overflow")
    for symbol in watchlist:
        symbol_state = normalized["per_symbol"][symbol]
        if symbol_state["state"] == "COOLDOWN":
            raise RuntimeError(f"FSM invariant violated: cooldown symbol remained in watchlist ({symbol})")
    _sync_state(state, normalized)


def _derive_focus_ttl(decision: Dict[str, Any]) -> int:
    expiry_minutes = decision.get("expiry_minutes")
    if isinstance(expiry_minutes, (int, float)) and expiry_minutes > 0:
        return max(int(expiry_minutes) * 60, 60)
    return DEFAULT_FOCUS_TTL_SECONDS


def _derive_cooldown_ttl(decision: Dict[str, Any]) -> int:
    expiry_minutes = decision.get("expiry_minutes")
    if isinstance(expiry_minutes, (int, float)) and expiry_minutes > 0:
        return max(int(expiry_minutes) * 60, DEFAULT_COOLDOWN_SECONDS)
    return DEFAULT_COOLDOWN_SECONDS


def _ensure_symbol_state(state: Dict[str, Any], symbol: str) -> Dict[str, Any]:
    per_symbol = state.setdefault("per_symbol", {})
    current = per_symbol.get(symbol)
    if not isinstance(current, dict):
        current = _default_symbol_state()
        per_symbol[symbol] = current
        return current

    merged = _default_symbol_state()
    merged.update(current)
    per_symbol[symbol] = merged
    return merged


def _recompute_mode(state: Dict[str, Any]) -> None:
    watchlist = state.get("watchlist", [])
    state["mode"] = "FOCUS_MODE" if watchlist else "WIDE_SCAN"


def _replace_watchlist_entry(state: Dict[str, Any], outgoing_symbol: str, incoming_symbol: str) -> None:
    watchlist = list(state.get("watchlist", []))
    if outgoing_symbol in watchlist:
        watchlist[watchlist.index(outgoing_symbol)] = incoming_symbol
    elif incoming_symbol not in watchlist:
        watchlist.append(incoming_symbol)
    state["watchlist"] = watchlist[:MAX_WATCHLIST]


def _score_for_replacement(symbol_state: Dict[str, Any], candidate_score: float) -> float:
    stored = symbol_state.get("replacement_score")
    if isinstance(stored, (int, float)):
        return float(stored)
    return float(candidate_score)


def _best_replacement_victim(
    state: Dict[str, Any],
    incoming_symbol: str,
    incoming_score: float,
) -> Optional[str]:
    watchlist = [symbol for symbol in state.get("watchlist", []) if symbol != incoming_symbol]
    if len(watchlist) < MAX_WATCHLIST:
        return None

    ranked = []
    for symbol in watchlist:
        symbol_state = _ensure_symbol_state(state, symbol)
        ranked.append((symbol, _score_for_replacement(symbol_state, 0.0)))
    ranked.sort(key=lambda item: (item[1], item[0]))

    victim_symbol, victim_score = ranked[0]
    if incoming_score <= victim_score:
        return None
    return victim_symbol


def _transition_event(
    symbol: str,
    prev_state: str,
    new_state: str,
    trigger: str,
    *,
    signal_id: Optional[str],
    candle_ts: Optional[int],
    now_ts: int,
) -> Dict[str, Any]:
    return {
        "symbol": symbol,
        "prev_state": prev_state,
        "new_state": new_state,
        "trigger": trigger,
        "signal_id": signal_id or f"state:{symbol}",
        "candle_ts": int(candle_ts if candle_ts is not None else now_ts),
    }


def _clear_from_watchlist(state: Dict[str, Any], symbol: str) -> None:
    state["watchlist"] = [item for item in state.get("watchlist", []) if item != symbol]


def _release_to_cooldown(
    state: Dict[str, Any],
    *,
    symbol: str,
    symbol_state: Dict[str, Any],
    now_ts: int,
    trigger: str,
    signal_id: Optional[str],
    candle_ts: Optional[int],
    cooldown_seconds: int,
) -> Dict[str, Any]:
    prev_state = str(symbol_state.get("state") or "IDLE")
    if symbol_state.get("physical_signal_id"):
        # Close this idea, not the symbol. A fresh, distinct setup can start
        # immediately; the focus lease keeps the symbol on the fast scan.
        expired = trigger == "focus_lease_expired"
        if expired:
            _clear_from_watchlist(state, symbol)
        symbol_state["state"] = "IDLE" if expired else "WATCHLIST"
        symbol_state["physical_closed_signal_id"] = symbol_state.get("physical_signal_id")
        symbol_state["cooldown_until_ts"] = None
        if expired:
            symbol_state["focus_enter_ts"] = None
            symbol_state["focus_ttl_seconds"] = None
        symbol_state["last_exit_reason"] = trigger
        symbol_state["last_transition_ts"] = now_ts
        _recompute_mode(state)
        return _transition_event(symbol, prev_state, symbol_state["state"], trigger,
            signal_id=signal_id, candle_ts=candle_ts, now_ts=now_ts)
    _clear_from_watchlist(state, symbol)
    symbol_state["state"] = "COOLDOWN"
    symbol_state["cooldown_until_ts"] = now_ts + max(cooldown_seconds, 1)
    symbol_state["focus_enter_ts"] = None
    symbol_state["focus_ttl_seconds"] = None
    symbol_state["last_exit_reason"] = trigger
    symbol_state["last_transition_ts"] = now_ts
    _recompute_mode(state)
    return _transition_event(
        symbol,
        prev_state,
        "COOLDOWN",
        trigger,
        signal_id=signal_id,
        candle_ts=candle_ts,
        now_ts=now_ts,
    )


def reconcile_state(
    state: Dict[str, Any],
    now_ts: int,
    *,
    active_symbols: Optional[Iterable[str]] = None,
) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    enforce_invariants(state)
    active_set = {str(symbol) for symbol in active_symbols or []}
    events: List[Dict[str, Any]] = []

    # Existing physical cooldowns are retired on upgrade. Preserve opportunity
    # identity so restart cannot revive the closed idea or invent a new PRE.
    for symbol, row in state.get("per_symbol", {}).items():
        if row.get("state") == "COOLDOWN" and row.get("physical_signal_id"):
            row["state"] = "IDLE"
            row["cooldown_until_ts"] = None
            row["physical_closed_signal_id"] = row["physical_signal_id"]
            row["last_exit_reason"] = "physical_cooldown_retired"
            row["last_transition_ts"] = now_ts
            events.append(_transition_event(symbol, "COOLDOWN", "IDLE", "physical_cooldown_retired",
                signal_id=row.get("current_signal_id"), candle_ts=now_ts, now_ts=now_ts))

    for symbol in list(state.get("watchlist", [])):
        symbol_state = _ensure_symbol_state(state, symbol)

        if active_set and symbol not in active_set:
            prev_state = str(symbol_state.get("state") or "IDLE")
            _clear_from_watchlist(state, symbol)
            symbol_state["state"] = "IDLE"
            symbol_state["focus_enter_ts"] = None
            symbol_state["focus_ttl_seconds"] = None
            symbol_state["last_exit_reason"] = "focus_evicted_inactive"
            symbol_state["last_transition_ts"] = now_ts
            events.append(
                _transition_event(
                    symbol,
                    prev_state,
                    "IDLE",
                    "focus_evicted_inactive",
                    signal_id=symbol_state.get("current_signal_id"),
                    candle_ts=symbol_state.get("last_pre_candle_ts") or symbol_state.get("last_confirm_candle_ts"),
                    now_ts=now_ts,
                )
            )
            continue

        focus_enter_ts = symbol_state.get("focus_enter_ts")
        focus_ttl_seconds = symbol_state.get("focus_ttl_seconds")
        if focus_enter_ts and focus_ttl_seconds and now_ts >= focus_enter_ts + focus_ttl_seconds:
            events.append(
                _release_to_cooldown(
                    state,
                    symbol=symbol,
                    symbol_state=symbol_state,
                    now_ts=now_ts,
                    trigger="focus_lease_expired",
                    signal_id=symbol_state.get("current_signal_id"),
                    candle_ts=symbol_state.get("last_pre_candle_ts") or symbol_state.get("last_confirm_candle_ts"),
                    cooldown_seconds=DEFAULT_COOLDOWN_SECONDS,
                )
            )

    for symbol, symbol_state in state.get("per_symbol", {}).items():
        if symbol_state.get("state") != "COOLDOWN":
            continue
        cooldown_until_ts = symbol_state.get("cooldown_until_ts")
        if cooldown_until_ts and now_ts >= int(cooldown_until_ts):
            prev_state = "COOLDOWN"
            symbol_state["state"] = "IDLE"
            symbol_state["cooldown_until_ts"] = None
            symbol_state["current_signal_id"] = None
            symbol_state["last_exit_reason"] = "cooldown_expired"
            symbol_state["last_transition_ts"] = now_ts
            events.append(
                _transition_event(
                    symbol,
                    prev_state,
                    "IDLE",
                    "cooldown_expired",
                    signal_id=f"state:{symbol}",
                    candle_ts=symbol_state.get("last_open_candle_ts") or now_ts,
                    now_ts=now_ts,
                )
            )

    _recompute_mode(state)
    enforce_invariants(state)
    return state, events


def apply_transition(
    state: Dict[str, Any],
    decision: Dict[str, Any],
    now_ts: int,
) -> Tuple[Dict[str, Any], Optional[Dict[str, Any]]]:
    enforce_invariants(state)

    symbol = _safe_symbol(decision)
    kind = str(decision.get("kind") or "").strip().upper()
    signal_id = decision.get("signal_id")
    candle_ts = decision.get("candle_ts")

    symbol_state = _ensure_symbol_state(state, symbol)
    prev_state = str(symbol_state.get("state") or "IDLE")

    cooldown_until_ts = symbol_state.get("cooldown_until_ts")
    if cooldown_until_ts and now_ts < int(cooldown_until_ts) and kind in {"PRE", "CONFIRM", "OPEN_NOW"}:
        return state, _transition_event(
            symbol,
            prev_state,
            prev_state,
            "cooldown_active",
            signal_id=signal_id,
            candle_ts=candle_ts,
            now_ts=now_ts,
        )

    if kind == "PRE":
        watchlist = list(state.get("watchlist", []))
        physical_only = decision.get("decision_policy") == "PHYSICAL_ONLY_V3"
        attention = state.get("physical_attention") or {}
        if (physical_only and symbol not in watchlist and attention
            and symbol != attention["symbol"] and now_ts < attention["until_ts"]):
            return state, _transition_event(symbol, prev_state, prev_state, "cross_symbol_attention_active",
                signal_id=signal_id, candle_ts=candle_ts, now_ts=now_ts)
        incoming_score = None if physical_only else float(decision.get("score_total") or 0.0)
        if symbol not in watchlist and len(watchlist) >= MAX_WATCHLIST:
            if physical_only:
                # Retained fast-scan focus for a closed idea must not occupy
                # capacity ahead of a genuinely new eligible opportunity.
                closed = [item for item in watchlist if (
                    state["per_symbol"][item].get("physical_closed_signal_id")
                    and state["per_symbol"][item].get("physical_closed_signal_id")
                    == state["per_symbol"][item].get("current_signal_id"))]
                victim = min(closed, key=lambda item: (
                    state["per_symbol"][item].get("last_transition_ts") or 0, item)) if closed else None
            else:
                victim = _best_replacement_victim(state, symbol, incoming_score)
            if victim is None:
                return state, _transition_event(
                    symbol,
                    prev_state,
                    prev_state,
                    "watchlist_full",
                    signal_id=signal_id,
                    candle_ts=candle_ts,
                    now_ts=now_ts,
                )

            victim_state = _ensure_symbol_state(state, victim)
            victim_state["state"] = "IDLE"
            victim_state["focus_enter_ts"] = None
            victim_state["focus_ttl_seconds"] = None
            victim_state["last_exit_reason"] = "watchlist_replaced"
            victim_state["last_transition_ts"] = now_ts
            _replace_watchlist_entry(state, victim, symbol)
            trigger = "watchlist_replaced"
        else:
            if symbol not in watchlist:
                watchlist.append(symbol)
                state["watchlist"] = watchlist
                trigger = "watchlist_added"
            else:
                trigger = "watchlist_refreshed"

        symbol_state["state"] = "WATCHLIST"
        symbol_state["current_signal_id"] = signal_id
        symbol_state["last_pre_candle_ts"] = candle_ts
        symbol_state["focus_enter_ts"] = symbol_state.get("focus_enter_ts") or now_ts
        symbol_state["focus_ttl_seconds"] = _derive_focus_ttl(decision)
        symbol_state["replacement_score"] = incoming_score
        symbol_state["replacement_score_ts"] = None if physical_only else now_ts
        symbol_state["last_transition_ts"] = now_ts
        if physical_only and (not attention or now_ts >= attention["until_ts"]):
            state["physical_attention"] = {"policy": PHYSICAL_FOCUS_POLICY,
                "symbol": symbol, "started_ts": now_ts,
                "until_ts": now_ts + CROSS_SYMBOL_ATTENTION_SECONDS}
        _recompute_mode(state)
        enforce_invariants(state)
        return state, _transition_event(symbol, prev_state, "WATCHLIST", trigger, signal_id=signal_id, candle_ts=candle_ts, now_ts=now_ts)

    if kind == "CONFIRM":
        if prev_state not in {"WATCHLIST", "CONFIRMED"}:
            raise ValueError(f"Invalid FSM transition: {prev_state} -> CONFIRM for {symbol}")

        symbol_state["state"] = "CONFIRMED"
        symbol_state["current_signal_id"] = signal_id
        symbol_state["last_confirm_candle_ts"] = candle_ts
        symbol_state["last_transition_ts"] = now_ts
        _recompute_mode(state)
        enforce_invariants(state)
        return state, _transition_event(symbol, prev_state, "CONFIRMED", "confirm_seen", signal_id=signal_id, candle_ts=candle_ts, now_ts=now_ts)

    if kind == "OPEN_NOW":
        if prev_state not in {"WATCHLIST", "CONFIRMED", "LIVE_SENT"}:
            raise ValueError(f"Invalid FSM transition: {prev_state} -> OPEN_NOW for {symbol}")

        symbol_state["state"] = "LIVE_SENT"
        symbol_state["current_signal_id"] = signal_id
        symbol_state["last_open_candle_ts"] = candle_ts
        symbol_state["last_transition_ts"] = now_ts
        _recompute_mode(state)
        enforce_invariants(state)
        return state, _transition_event(symbol, prev_state, "LIVE_SENT", "open_sent", signal_id=signal_id, candle_ts=candle_ts, now_ts=now_ts)

    if kind == "REJECT":
        if prev_state in {"WATCHLIST", "CONFIRMED", "LIVE_SENT"} or symbol in state.get("watchlist", []):
            event = _release_to_cooldown(
                state,
                symbol=symbol,
                symbol_state=symbol_state,
                now_ts=now_ts,
                trigger="reject_released",
                signal_id=signal_id,
                candle_ts=candle_ts,
                cooldown_seconds=_derive_cooldown_ttl(decision),
            )
            enforce_invariants(state)
            return state, event
        return state, _transition_event(symbol, prev_state, prev_state, "reject_seen", signal_id=signal_id, candle_ts=candle_ts, now_ts=now_ts)

    if kind == "NO_SIGNAL":
        _recompute_mode(state)
        enforce_invariants(state)
        return state, None

    raise ValueError(f"Unsupported FSM decision kind: {kind}")


def complete_open_now(
    state: Dict[str, Any],
    decision: Dict[str, Any],
    now_ts: int,
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    symbol = _safe_symbol(decision)
    signal_id = decision.get("signal_id")
    candle_ts = decision.get("candle_ts")
    symbol_state = _ensure_symbol_state(state, symbol)

    if symbol_state.get("state") == "COOLDOWN":
        return state, _transition_event(
            symbol,
            "COOLDOWN",
            "COOLDOWN",
            "open_now_finalize_idempotent",
            signal_id=signal_id,
            candle_ts=candle_ts,
            now_ts=now_ts,
        )

    event = _release_to_cooldown(
        state,
        symbol=symbol,
        symbol_state=symbol_state,
        now_ts=now_ts,
        trigger="open_now_completed",
        signal_id=signal_id,
        candle_ts=candle_ts,
        cooldown_seconds=_derive_cooldown_ttl(decision),
    )
    enforce_invariants(state)
    return state, event


def update_symbol_replacement_score(symbol: str, score: float, now_ts: int) -> None:
    state = load_state()
    symbol_state = _ensure_symbol_state(state, symbol)
    symbol_state["replacement_score"] = float(score)
    symbol_state["replacement_score_ts"] = int(now_ts)
    symbol_state["last_transition_ts"] = int(now_ts)
    save_state(state)


def _safe_symbol(decision: Dict[str, Any]) -> str:
    symbol = str(decision.get("symbol") or "").strip()
    if not symbol:
        raise ValueError("FSM decision is missing symbol")
    return symbol
