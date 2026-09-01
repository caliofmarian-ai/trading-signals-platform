from __future__ import annotations


def update_symbol_replacement_score(symbol: str, score: float, now_ts: int):
    """Expose strategy score to the focus replacement engine only."""

    from core import fsm_runtime

    fsm_runtime.update_symbol_replacement_score(symbol=symbol, score=score, now_ts=now_ts)


# /opt/binarybot/core/signal_engine.py
# BinaryBot — Signal Engine (one tick)

from core.storage import config_path

import time
from typing import Any, Dict, List, Optional

from core import candle_adapter
from core import fsm_runtime
from core import observability_logger
from core.decision_object import ACTIONABLE_DECISION_KINDS
from core.signal_execution_gate import prepare_signal_execution
from core.strategy_v2 import decide
from core.v2_fsm_orchestrator import advance_persistent_fsm, current_opportunity_signal_id
from core import storage
from state_store import state_store as runtime_state_store


ACTIVE_SYMBOLS_PATH = config_path("active_symbols.json")
SETTINGS_PATH = config_path("admin_settings.json")
ALGO_PARAMS_PATH = config_path("algo_params.json")
EVENT_SCHEMA_VERSION = "3.0.0"


def _load_active_symbols() -> List[str]:
    """Load the configured active symbols while preserving stable order."""

    cfg = runtime_state_store.load_active_symbols(path=ACTIVE_SYMBOLS_PATH)
    out: List[str] = []

    if isinstance(cfg, dict):
        if isinstance(cfg.get("symbols"), list):
            out = [str(x).strip() for x in cfg["symbols"] if str(x).strip()]
        else:
            for key in ("forex", "crypto"):
                if isinstance(cfg.get(key), list):
                    out.extend([str(x).strip() for x in cfg[key] if str(x).strip()])

    seen = set()
    cleaned = []
    for symbol in out:
        if symbol not in seen:
            seen.add(symbol)
            cleaned.append(symbol)
    return cleaned


def _load_settings() -> Dict[str, Any]:
    return runtime_state_store.load_settings(path=SETTINGS_PATH)


def _load_algo_params() -> Dict[str, Any]:
    return storage.load_json(ALGO_PARAMS_PATH, default={})


def _build_v3_event(
    event_type: str,
    data: Dict[str, Any],
    *,
    correlation: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Build one canonical v3 event while legacy modules remain v2-compatible."""

    event = observability_logger.build_event(
        event_type,
        data,
        source={"module": "signal_engine", "function": "run_once"},
        correlation=correlation,
    )
    event["schema_version"] = EVENT_SCHEMA_VERSION
    return observability_logger.validate_event(event)


def _trade_physics_dict(decision_dict: Dict[str, Any]) -> Dict[str, Any]:
    score = decision_dict.get("score")
    if not isinstance(score, dict):
        return {}
    trade_physics = score.get("trade_physics")
    return dict(trade_physics) if isinstance(trade_physics, dict) else {}


def _log_decision_evaluated(evaluation, buffer_mode: str) -> None:
    decision = evaluation.decision
    decision_dict = decision.to_dict()
    correlation: Dict[str, Any] = {
        "setup_correlation_id": evaluation.cycle_id,
        "signal_id": decision.signal_id,
        "symbol": decision.setup.symbol,
        "timeframe": decision.setup.timeframe,
    }
    if decision.kind in ACTIONABLE_DECISION_KINDS:
        correlation["stage"] = decision.kind

    event = _build_v3_event(
        "decision_evaluated",
        {
            "decision_kind": decision.kind,
            "strategic_kind": decision.kind,
            "strategy": "BINARY_STRATEGY_V2",
            "strategy_version": evaluation.strategy_version,
            "canonical_spec": evaluation.canonical_spec,
            "score_total": decision.score.total,
            "score_tier": decision.score.tier,
            "direction": decision.setup.direction,
            "candle_ts": decision.setup.evaluated_ts,
            "signal_id": decision.signal_id,
            "buffer_mode": buffer_mode,
            "decision_object": decision_dict,
            "trade_physics": _trade_physics_dict(decision_dict),
        },
        correlation=correlation,
    )
    observability_logger.log_event(event)


def _log_fsm_handoff(decision, persistent_fsm) -> None:
    event = _build_v3_event(
        "fsm_transition",
        {
            "symbol": decision.setup.symbol,
            "prev_state": persistent_fsm.prior_state,
            "new_state": persistent_fsm.resulting_state,
            "trigger": persistent_fsm.reason,
            "signal_id": decision.signal_id or f"state:{decision.setup.symbol}",
            "candle_ts": decision.setup.evaluated_ts,
            "requested_stage": persistent_fsm.requested_stage,
            "accepted_stage": persistent_fsm.accepted_stage,
            "reason_family": persistent_fsm.reason_family,
            "stage_handoff_ready": persistent_fsm.stage_handoff_ready,
            "trade_execution_ready": persistent_fsm.trade_execution_ready,
        },
        correlation={
            "setup_correlation_id": decision.setup.cycle_id,
            "signal_id": decision.signal_id,
            "symbol": decision.setup.symbol,
            "timeframe": decision.setup.timeframe,
            "stage": persistent_fsm.requested_stage,
        },
    )
    observability_logger.log_event(event)


def _log_signal_execution(decision, persistent_fsm, execution) -> None:
    decision_dict = decision.to_dict()
    data = execution.to_event_data()
    data["fsm_handoff"] = {
        "requested_stage": persistent_fsm.requested_stage,
        "accepted_stage": persistent_fsm.accepted_stage,
        "signal_id": persistent_fsm.signal_id,
        "prior_state": persistent_fsm.prior_state,
        "resulting_state": persistent_fsm.resulting_state,
        "state_changed": persistent_fsm.state_changed,
        "reason": persistent_fsm.reason,
        "reason_family": persistent_fsm.reason_family,
        "stage_handoff_ready": persistent_fsm.stage_handoff_ready,
        "trade_execution_ready": persistent_fsm.trade_execution_ready,
    }
    data["trade_physics"] = _trade_physics_dict(decision_dict) or None

    event = _build_v3_event(
        "signal_execution_result",
        data,
        correlation={
            "execution_attempt_id": execution.execution_attempt_id,
            "setup_correlation_id": execution.setup_correlation_id,
            "signal_id": decision.signal_id,
            "symbol": decision.setup.symbol,
            "timeframe": decision.setup.timeframe,
            "stage": decision.kind,
        },
    )
    observability_logger.log_event(event)


def run_once(now_ts=None, forced_symbols=None, forced_focus_context=None, scheduler_stage=None) -> None:
    """Run one real-market strategy/FSM/execution-candidate cycle.

    Distribution, Telegram publication, outcome registration and broker execution
    are intentionally not invoked by this function in the current activation.
    """

    del scheduler_stage
    now_ts = int(now_ts or time.time())

    settings = _load_settings()
    params = _load_algo_params()
    buffer_mode = settings.get("buffer_mode", "MEDIUM")

    symbols = _load_active_symbols()
    if not symbols:
        observability_logger.log_warning(
            warn_type="NO_ACTIVE_SYMBOLS",
            message="active_symbols.json produced empty symbol list",
            context={
                "module": "signal_engine",
                "active_symbols_path": ACTIVE_SYMBOLS_PATH,
            },
            source={"module": "signal_engine", "function": "run_once"},
        )
        return

    state = fsm_runtime.load_state()
    state, maintenance_events = fsm_runtime.reconcile_state(
        state, now_ts, active_symbols=symbols
    )
    if maintenance_events:
        fsm_runtime.save_state(state)
        for maintenance_event in maintenance_events:
            observability_logger.log_event(
                observability_logger.build_event(
                    "fsm_transition",
                    maintenance_event,
                    source={"module": "signal_engine", "function": "run_once"},
                )
            )

    watchlist = state.get("watchlist", []) if isinstance(state, dict) else []
    natural_in_focus = isinstance(watchlist, list) and len(watchlist) > 0

    if forced_symbols is not None:
        scan_symbols = [str(x).strip() for x in forced_symbols if str(x).strip()]
        effective_in_focus = bool(forced_focus_context)
    else:
        scan_symbols = watchlist if natural_in_focus else symbols
        effective_in_focus = bool(natural_in_focus)

    from runtime import market_client

    provider_symbols = market_client.configured_symbols()
    if provider_symbols is not None:
        allowed = {str(item).strip().upper() for item in provider_symbols}
        scan_symbols = [
            symbol
            for symbol in scan_symbols
            if str(symbol).strip().upper().replace("_", "/") in allowed
        ]

    for symbol in scan_symbols:
        try:
            from runtime.market_client import (
                MarketDataRateLimitError,
                MarketDataUnavailableError,
                get_candles,
            )

            raw_m1 = get_candles(symbol, "1min")
            raw_m5 = get_candles(symbol, "5min")

            candles_m1 = candle_adapter.normalize(raw_m1, symbol=symbol, timeframe="M1")
            candles_m5 = candle_adapter.normalize(raw_m5, symbol=symbol, timeframe="M5")
            candle_adapter.validate(candles_m1)
            candle_adapter.validate(candles_m5)

            evaluation = decide(
                candles_m1=candles_m1,
                candles_m5=candles_m5,
                params=params,
                buffer_mode=buffer_mode,
                want_open_now=bool(effective_in_focus),
                context={
                    "decision_timeframe": "M1",
                    "opportunity_signal_id": current_opportunity_signal_id(state, symbol),
                },
            )
            decision = evaluation.decision

            _log_decision_evaluated(evaluation, buffer_mode)

            persistent_fsm = advance_persistent_fsm(state, decision, now_ts=now_ts)
            if persistent_fsm.state_changed:
                state = persistent_fsm.next_state
                fsm_runtime.save_state(state)

            _log_fsm_handoff(decision, persistent_fsm)

            if decision.kind in ACTIONABLE_DECISION_KINDS:
                execution = prepare_signal_execution(
                    persistent_fsm,
                    decision,
                    buffer_mode=buffer_mode,
                    created_ts=now_ts,
                )
                _log_signal_execution(decision, persistent_fsm, execution)

        except Exception as exc:
            if isinstance(exc, MarketDataRateLimitError):
                observability_logger.log_warning(
                    warn_type="MARKET_DATA_LIMITED",
                    message="Twelve Data rate limit is active; skipping remaining symbols for this cycle",
                    context={"symbol": symbol},
                    source={"module": "signal_engine", "function": "run_once"},
                )
                break
            if isinstance(exc, MarketDataUnavailableError):
                observability_logger.log_warning(
                    warn_type="MARKET_DATA_UNAVAILABLE",
                    message="Current market data is unavailable; no decision was produced",
                    context={"symbol": symbol, "reason": str(exc)},
                    source={"module": "signal_engine", "function": "run_once"},
                )
                break
            observability_logger.log_error(
                {
                    "event_type": "error",
                    "module": "signal_engine",
                    "symbol": symbol,
                    "error": str(exc),
                    "trace": "",
                }
            )
            continue


def run_for_symbols(symbols, now_ts=None, focus_context=False, scheduler_stage=None) -> None:
    return run_once(
        now_ts=now_ts,
        forced_symbols=symbols,
        forced_focus_context=focus_context,
        scheduler_stage=scheduler_stage or ("FOCUS" if focus_context else "WIDE"),
    )
