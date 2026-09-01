from __future__ import annotations


def update_symbol_replacement_score(symbol: str, score: float, now_ts: int):
    """Expose strategy score to the focus replacement engine only."""

    from core import fsm_runtime

    fsm_runtime.update_symbol_replacement_score(symbol=symbol, score=score, now_ts=now_ts)


# /opt/binarybot/core/signal_engine.py
# BinaryBot — Signal Engine (one tick)

from core.storage import config_path

import importlib
import time
from typing import Any, Dict, List, Optional

from core import candle_adapter
from core import distribution_router_v3 as distribution_router
from core import fsm_runtime
from core import observability_logger
from core import runtime_param_gate
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
WIDE_SCAN_SLOT_SECONDS = 2
WIDE_SCAN_CYCLE_SECONDS = 60
_LAST_PARAM_ERROR_SIGNATURE: Optional[str] = None


def _select_scan_symbols(symbols: List[str], watchlist: List[str], now_ts: int) -> tuple[List[str], set[str]]:
    """Prioritize focus every tick while preserving bounded wide-scan coverage.

    Wide symbols are deterministically spread across the M1 decision cycle so
    the same opportunity is not fully re-evaluated every 2-second engine tick.
    """

    active_set = set(symbols)
    focus = [symbol for symbol in watchlist if symbol in active_set]
    focus_set = set(focus)
    wide = [symbol for symbol in symbols if symbol not in focus_set]
    slots = max(1, WIDE_SCAN_CYCLE_SECONDS // WIDE_SCAN_SLOT_SECONDS)
    current_slot = (int(now_ts) % WIDE_SCAN_CYCLE_SECONDS) // WIDE_SCAN_SLOT_SECONDS
    selected_wide = [
        symbol for index, symbol in enumerate(wide) if index % slots == current_slot
    ]
    return focus + selected_wide, focus_set


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
    """Load the live strategy bundle through the canonical fail-closed gate."""
    return runtime_param_gate.load_runtime_algo_params(ALGO_PARAMS_PATH)


def _load_validated_params_or_block(now_ts: int) -> Optional[Dict[str, Any]]:
    """Return validated live params, or expose one blocked operational state.

    Repeated engine ticks do not duplicate the same canonical error event; the
    operational incident layer still maintains bounded reminders. Recovery is
    explicitly cleared when a valid bundle becomes available again.
    """
    global _LAST_PARAM_ERROR_SIGNATURE

    try:
        params = _load_algo_params()
    except runtime_param_gate.RuntimeParameterError as exc:
        signature = f"{type(exc).__name__}:{exc}"
        if signature != _LAST_PARAM_ERROR_SIGNATURE:
            observability_logger.log_error(
                {
                    "event_type": "error",
                    "severity": "CRITICAL",
                    "error_type": "ALGO_PARAMS_VALIDATION_FAILED",
                    "message": "Canonical algo parameter validation failed; strategy evaluation blocked",
                    "context": {
                        "params_path": ALGO_PARAMS_PATH,
                        "reason": str(exc),
                        "exception_type": type(exc).__name__,
                    },
                    "source": {"module": "signal_engine", "function": "run_once"},
                }
            )
        observability_logger.record_operational_incident(
            incident_type="ALGO_PARAMS_VALIDATION_FAILED",
            component="signal_engine",
            runtime_state="BLOCKED",
            operator_action="Restore a canonically valid algo_params.json before strategy evaluation.",
            severity="CRITICAL",
            now_ts=now_ts,
        )
        _LAST_PARAM_ERROR_SIGNATURE = signature
        return None

    if _LAST_PARAM_ERROR_SIGNATURE is not None:
        observability_logger.clear_operational_incident(
            incident_type="ALGO_PARAMS_VALIDATION_FAILED",
            component="signal_engine",
            runtime_state="HEALTHY",
            operator_action="Canonical algo parameter validation recovered.",
            now_ts=now_ts,
        )
        _LAST_PARAM_ERROR_SIGNATURE = None

    return params


def _load_trade_temporal_telemetry():
    """Compatibility import hook only; loading does not register or emit telemetry."""

    return importlib.import_module("core.trade_temporal_telemetry")


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
    # Preserve the canonical DecisionObject while enriching its observable
    # contexts with the upstream evidence required to diagnose calibration.
    market_context = decision_dict.get("market_context")
    if isinstance(market_context, dict):
        market_context.update({
            "average_m1_range": evaluation.market.evidence.average_m1_range,
            "minimum_m1_range": evaluation.market.evidence.minimum_m1_range,
            "atr_m5": evaluation.market.evidence.atr_m5,
        })
    structure = decision_dict.get("structure")
    if isinstance(structure, dict):
        structure.update({
            "required_distance": evaluation.corridor.evidence.required_distance,
            "room_ratio": evaluation.corridor.evidence.room_ratio,
            "support_level_count": len(evaluation.corridor.evidence.support_levels),
            "resistance_level_count": len(evaluation.corridor.evidence.resistance_levels),
        })
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
    try:
        from runtime import runtime_status

        status = runtime_status.read_status()
        previous_count = status.get("strategy_evaluation_count", 0)
        if isinstance(previous_count, bool) or not isinstance(previous_count, int):
            previous_count = 0
        reject = decision_dict.get("reject")
        hard_blockers = reject.get("hard_blockers", []) if isinstance(reject, dict) else []
        trade_physics = _trade_physics_dict(decision_dict)
        runtime_status.update_status(
            strategy_evaluation_count=previous_count + 1,
            last_strategy_evaluation_ts=int(time.time()),
            last_strategy_symbol=decision.setup.symbol,
            last_strategy_candle_ts=decision.setup.evaluated_ts,
            last_strategy_decision_kind=decision.kind,
            last_strategy_score_total=decision.score.total,
            last_strategy_score_tier=decision.score.tier,
            last_strategy_tps=trade_physics.get("TPS"),
            last_strategy_hard_blockers=list(hard_blockers),
        )
    except Exception as exc:
        observability_logger.log_warning(
            warn_type="STRATEGY_STATUS_UPDATE_FAILED",
            message="Strategy evaluation was logged but runtime status projection failed",
            context={"error": str(exc)},
            source={"module": "signal_engine", "function": "_log_decision_evaluated"},
        )


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



def _log_post_distribution(decision, persistent_fsm, execution, summary: Dict[str, Any]) -> None:
    published_count = int(summary.get("published_count", 0))
    failed_count = int(summary.get("failed_count", 0))
    blocked = bool(summary.get("blocked"))

    if blocked:
        outcome = "BLOCKED"
        reason = str(summary.get("block_reason") or "DISTRIBUTION_BLOCKED")
        destination_state = "DISTRIBUTION_BLOCKED"
    elif published_count > 0:
        outcome = "EMITTED"
        reason = "AUTHORIZED_PUBLICATION_SUCCEEDED"
        destination_state = "PUBLISHED"
    elif failed_count > 0:
        outcome = "FAILED"
        reason = "ROUTE_PUBLICATION_FAILED"
        destination_state = "ROUTES_EVALUATED_NO_PUBLICATION"
    else:
        outcome = "SKIPPED"
        reason = "NO_AUTHORIZED_ROUTE_PUBLISHED"
        destination_state = "ROUTES_EVALUATED_NO_PUBLICATION"

    decision_dict = decision.to_dict()
    data = {
        "execution_phase": "POST_DISTRIBUTION",
        "execution_outcome": outcome,
        "execution_reason": reason,
        "stage_handoff_ready": execution.stage_handoff_ready,
        "trade_execution_ready": execution.trade_execution_ready,
        "execution_time_available": execution.execution_time_available,
        "execution_calibration_source": execution.execution_calibration_source,
        "execution_time_explanation": execution.execution_time_explanation,
        "signal_event_available": execution.candidate is not None,
        "destination_state": destination_state,
        "candidate_schema_version": execution.candidate.schema_version if execution.candidate is not None else None,
        "fsm_handoff": {
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
        },
        "trade_physics": _trade_physics_dict(decision_dict) or None,
        "publication_evidence": {
            "published": list(summary.get("publication_evidence") or []),
            "route_results": list(summary.get("route_results") or []),
        },
    }
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
    """Run one real-market strategy/FSM/candidate/distribution cycle.

    Governed SignalEvent candidates may be routed to Telegram. Broker execution
    remains disabled and is never invoked by this function.
    """

    del scheduler_stage
    now_ts = int(now_ts or time.time())

    settings = _load_settings()
    params = _load_validated_params_or_block(now_ts)
    if params is None:
        return
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
    if not isinstance(watchlist, list):
        watchlist = []

    if forced_symbols is not None:
        scan_symbols = [str(x).strip() for x in forced_symbols if str(x).strip()]
        focus_symbols = set(scan_symbols) if bool(forced_focus_context) else set()
    else:
        scan_symbols, focus_symbols = _select_scan_symbols(symbols, watchlist, now_ts)

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

            symbol_in_focus = symbol in focus_symbols
            raw_m1 = get_candles(symbol, "1min", prefer_live=symbol_in_focus)
            raw_m5 = get_candles(symbol, "5min", prefer_live=symbol_in_focus)

            candles_m1 = candle_adapter.normalize(raw_m1, symbol=symbol, timeframe="M1")
            candles_m5 = candle_adapter.normalize(raw_m5, symbol=symbol, timeframe="M5")
            candle_adapter.validate(candles_m1)
            candle_adapter.validate(candles_m5)

            evaluation = decide(
                candles_m1=candles_m1,
                candles_m5=candles_m5,
                params=params,
                buffer_mode=buffer_mode,
                want_open_now=bool(symbol_in_focus),
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
                    execution_time=evaluation.execution_time,
                )
                _log_signal_execution(decision, persistent_fsm, execution)
                if execution.distribution_allowed and execution.candidate is not None:
                    try:
                        distribution_summary = distribution_router.route(
                            execution.candidate, now_ts=now_ts
                        )
                    except Exception as distribution_exc:
                        observability_logger.log_error(
                            {
                                "event_type": "error",
                                "module": "signal_engine",
                                "symbol": symbol,
                                "error": str(distribution_exc),
                                "trace": "",
                            }
                        )
                        distribution_summary = {
                            "published_count": 0,
                            "failed_count": 1,
                            "skipped_count": 0,
                            "blocked": False,
                            "block_reason": None,
                            "route_results": [],
                            "publication_evidence": [],
                        }
                    _log_post_distribution(
                        decision, persistent_fsm, execution, distribution_summary
                    )

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