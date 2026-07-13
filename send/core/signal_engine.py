from __future__ import annotations


def update_symbol_replacement_score(symbol: str, score: float, now_ts: int):
    """
    Feed strategy score into focus replacement engine.
    This does NOT change strategy behaviour.
    It only exposes symbol strength to the scheduler.
    """

    try:
        from core import fsm_runtime
        from core.scan_scheduler import _focus_state_path
        import json
        import os

        path = _focus_state_path()

        if not os.path.isfile(path):
            return

        with open(path, "r", encoding="utf-8") as f:
            state = json.load(f)

        if not isinstance(state, dict):
            return

        per_symbol = state.setdefault("per_symbol", {})
        ps = per_symbol.setdefault(symbol, {})

        ps["replacement_score"] = float(score)
        ps["replacement_score_ts"] = int(now_ts)

        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=2)

        os.replace(tmp, path)

    except Exception:
        pass


# /opt/binarybot/core/signal_engine.py
# BinaryBot — Signal Engine (one tick)

from core.storage import config_path

import importlib
import json
import os
import time
from typing import Any, Dict, List, Optional

from core import storage
from core import candle_adapter
from core import fsm_runtime
from core import distribution_router
from core import observability_logger

from core.strategy_v2 import decide


ACTIVE_SYMBOLS_PATH = config_path("active_symbols.json")
SETTINGS_PATH = config_path("settings.json")
ALGO_PARAMS_PATH = config_path("algo_params.json")
TPS_METRICS_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "observability", "tps_metrics.jsonl")


def _load_active_symbols() -> List[str]:
    """
    Supports BOTH formats:
      A) {"symbols": ["EUR/USD", ...]}
      B) {"forex":[...], "crypto":[...]}   <-- current format
    """
    cfg = storage.load_json(ACTIVE_SYMBOLS_PATH, default={})
    out: List[str] = []

    if isinstance(cfg, dict):
        if isinstance(cfg.get("symbols"), list):
            out = [str(x).strip() for x in cfg["symbols"] if str(x).strip()]
        else:
            for k in ("forex", "crypto"):
                if isinstance(cfg.get(k), list):
                    out.extend([str(x).strip() for x in cfg[k] if str(x).strip()])

    seen = set()
    cleaned = []
    for s in out:
        if s not in seen:
            seen.add(s)
            cleaned.append(s)

    return cleaned


def _load_settings() -> Dict[str, Any]:
    return storage.load_json(SETTINGS_PATH, default={"buffer_mode": "MEDIUM"})


def _load_algo_params() -> Dict[str, Any]:
    return storage.load_json(ALGO_PARAMS_PATH, default={})


def _make_signal_event(decision: Dict[str, Any], now_ts: int) -> Dict[str, Any]:
    return {
        "event_type": "signal_event",
        "stage": decision["kind"],
        "signal_id": decision["signal_id"],
        "symbol": decision["symbol"],
        "timeframe": decision.get("timeframe") or "M1",
        "direction": decision["direction"],
        "score_total": float(decision["score_total"]),
        "buffer_mode": decision["buffer_mode"],
        "buffer_price": float(decision["buffer_price"]),
        "expiry_minutes": int(decision["expiry_minutes"]),
        "candle_ts": int(decision["candle_ts"]),
        "created_ts": int(now_ts),
        "payload": decision.get("debug") or {},
    }


def _safe_float(x: Any) -> Optional[float]:
    try:
        if x is None:
            return None
        return float(x)
    except Exception:
        return None


def _ensure_parent_dir(path: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)


def _append_jsonl(path: str, obj: Dict[str, Any]) -> None:
    _ensure_parent_dir(path)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=False) + "\n")


def _extract_tps_metrics(decision: Dict[str, Any], now_ts: int) -> Dict[str, Any]:
    debug = decision.get("debug") or {}
    gates = decision.get("gates") or {}

    sr_dbg = debug.get("sr") or {}
    expiry_dbg = debug.get("expiry") or {}

    sr_gate = gates.get("sr_gate") or {}
    sr_gate_details = sr_gate.get("details") or {}

    feas_gate = gates.get("feasibility") or {}
    feas_details = feas_gate.get("details") or {}

    available_space = _safe_float(sr_gate_details.get("available_space", sr_dbg.get("available_space")))
    required_space = _safe_float(debug.get("required_space"))
    atr_m5 = _safe_float(debug.get("atr_m5"))
    buffer_price = _safe_float(debug.get("buffer_price"))
    buffer_mult = _safe_float(debug.get("buffer_mult"))
    speed_price_per_min = _safe_float(feas_details.get("speed_price_per_min"))
    t_needed_adj_min = _safe_float(feas_details.get("t_needed_adj_min", expiry_dbg.get("t_needed_adj")))
    expiry_minutes = _safe_float(decision.get("expiry_minutes"))

    space_to_buffer_ratio = None
    if available_space is not None and required_space not in (None, 0.0):
        space_to_buffer_ratio = available_space / required_space

    trade_space_margin_atr = None
    if available_space is not None and required_space is not None and atr_m5 not in (None, 0.0):
        trade_space_margin_atr = (available_space - required_space) / atr_m5

    time_to_buffer_ratio = None
    if expiry_minutes not in (None, 0.0) and t_needed_adj_min not in (None, 0.0):
        time_to_buffer_ratio = expiry_minutes / t_needed_adj_min

    directional_speed_ratio = None
    if speed_price_per_min is not None and buffer_price not in (None, 0.0) and expiry_minutes not in (None, 0.0):
        required_speed_reference = buffer_price / expiry_minutes
        if required_speed_reference > 0:
            directional_speed_ratio = speed_price_per_min / required_speed_reference

    movement_stress = None
    if required_space is not None and atr_m5 not in (None, 0.0):
        movement_stress = required_space / atr_m5

    S = None
    if space_to_buffer_ratio is not None:
        S = min(space_to_buffer_ratio, 3.0) / 3.0

    T = None
    if time_to_buffer_ratio is not None:
        T = min(time_to_buffer_ratio, 2.0) / 2.0

    P = None
    if directional_speed_ratio is not None:
        P = min(directional_speed_ratio, 2.0) / 2.0

    V = None
    if movement_stress is not None:
        V = 1.0 / (1.0 + movement_stress)

    TPS = None
    if None not in (S, T, P, V):
        tps_raw = (0.35 * S) + (0.25 * T) + (0.20 * P) + (0.20 * V)
        TPS = max(0.0, min(100.0, 100.0 * tps_raw))

    return {
        "ts_epoch": int(now_ts),
        "symbol": decision.get("symbol"),
        "decision_kind": decision.get("kind"),
        "debug": debug,
        "signal_id": decision.get("signal_id"),
        "candle_ts": decision.get("candle_ts"),
        "buffer_mode": decision.get("buffer_mode"),
        "score_total": decision.get("score_total"),
        "available_space": available_space,
        "required_space": required_space,
        "atr_m5": atr_m5,
        "buffer_price": buffer_price,
        "buffer_mult": buffer_mult,
        "speed_price_per_min": speed_price_per_min,
        "t_needed_adj_min": t_needed_adj_min,
        "expiry_minutes": expiry_minutes,
        "space_to_buffer_ratio": space_to_buffer_ratio,
        "trade_space_margin_atr": trade_space_margin_atr,
        "time_to_buffer_ratio": time_to_buffer_ratio,
        "directional_speed_ratio": directional_speed_ratio,
        "movement_stress": movement_stress,
        "tps_components": {
            "S_space": S,
            "T_time": T,
            "P_speed": P,
            "V_volatility": V,
        },
        "TPS": TPS,
        "computable": TPS is not None,
    }


def _log_tps_metrics(decision: Dict[str, Any], now_ts: int) -> None:
    try:
        row = _extract_tps_metrics(decision, now_ts)
        _append_jsonl(TPS_METRICS_PATH, row)
    except Exception:
        pass


def _load_trade_temporal_telemetry():
    try:
        return importlib.import_module("core.trade_temporal_telemetry")
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "trade_temporal_telemetry module is unavailable; OPEN_NOW telemetry remains deferred by GAP-001/OWNER-004"
        ) from exc


def run_once(now_ts=None, forced_symbols=None, forced_focus_context=None, scheduler_stage=None) -> None:
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
                "active_symbols_path": ACTIVE_SYMBOLS_PATH
            },
            source={"module": "signal_engine", "function": "run_once"}
        )
        return

    state = fsm_runtime.load_state()

    watchlist = state.get("watchlist", []) if isinstance(state, dict) else []
    natural_in_focus = isinstance(watchlist, list) and len(watchlist) > 0

    if forced_symbols is not None:
        scan_symbols = [str(x).strip() for x in forced_symbols if str(x).strip()]
        effective_in_focus = bool(forced_focus_context)
    else:
        scan_symbols = watchlist if natural_in_focus else symbols
        effective_in_focus = bool(natural_in_focus)

    for symbol in scan_symbols:
        try:
            from runtime.market_client import get_candles

            raw_m1 = get_candles(symbol, "1min")
            raw_m5 = get_candles(symbol, "5min")

            candles_m1 = candle_adapter.normalize(raw_m1, symbol=symbol, timeframe="M1")
            candles_m5 = candle_adapter.normalize(raw_m5, symbol=symbol, timeframe="M5")

            candle_adapter.validate(candles_m1)
            candle_adapter.validate(candles_m5)

            want_open_now = bool(effective_in_focus)

            decision = decide(
                candles_m1=candles_m1,
                candles_m5=candles_m5,
                params=params,
                buffer_mode=buffer_mode,
                want_open_now=want_open_now,
                context={}
            )

            debug_payload = decision.get("debug") or {}
            threshold_block = debug_payload.get("thresholds") or {}

            ev = observability_logger.build_event(
                "decision",
                {
                    "symbol": symbol,
                    "decision_kind": decision.get("kind"),
                    "signal_id": decision.get("signal_id"),
                    "score_total": decision.get("score_total"),
                    "buffer_mode": decision.get("buffer_mode"),
                    "expiry_minutes": decision.get("expiry_minutes"),
                    "candle_ts": decision.get("candle_ts"),
                    "gates": decision.get("gates"),
                    "debug": debug_payload,
                    "threshold_pre": threshold_block.get("PRE"),
                    "threshold_confirm": threshold_block.get("CONFIRM"),
                    "threshold_open": threshold_block.get("OPEN"),
                    "threshold_source": debug_payload.get("threshold_source"),
                    "threshold_config_error": debug_payload.get("threshold_config_error"),
                },
                source={"module": "signal_engine", "function": "run_once"},
            )
            observability_logger.log_event(ev)

            _log_tps_metrics(decision, now_ts)

            state, transition_info = fsm_runtime.apply_transition(state, decision, now_ts)
            fsm_runtime.save_state(state)

            if transition_info:
                ev = observability_logger.build_event(
                    "fsm_transition",
                    transition_info,
                    source={"module": "signal_engine", "function": "run_once"},
                )
                observability_logger.log_event(ev)

            if decision.get("kind") in ("PRE", "CONFIRM", "OPEN_NOW"):
                event = _make_signal_event(decision, now_ts)

                if decision.get("kind") == "OPEN_NOW":
                    try:
                        tps_row = _extract_tps_metrics(decision, now_ts)
                        if isinstance(tps_row, dict):
                            event["TPS"] = tps_row.get("TPS")
                            event["space_to_buffer_ratio"] = tps_row.get("space_to_buffer_ratio")
                            event["trade_space_margin_atr"] = tps_row.get("trade_space_margin_atr")
                            event["time_to_buffer_ratio"] = tps_row.get("time_to_buffer_ratio")
                            event["directional_speed_ratio"] = tps_row.get("directional_speed_ratio")
                            event["movement_stress"] = tps_row.get("movement_stress")
                    except Exception:
                        pass

                    try:
                        telemetry = _load_trade_temporal_telemetry()
                        reg = telemetry.register_open_now_trade(event, now_ts)
                        ev_reg = observability_logger.build_event(
                            "decision",
                            {
                                "decision_kind": "OPEN_NOW_REGISTERED",
                                "symbol": event.get("symbol"),
                                "signal_id": event.get("signal_id"),
                                "telemetry_register_status": reg.get("status") if isinstance(reg, dict) else None,
                            },
                            source={"module": "signal_engine", "function": "run_once"},
                        )
                        observability_logger.log_event(ev_reg)
                    except Exception as reg_err:
                        try:
                            observability_logger.log_warning(
                                warn_type="OPEN_NOW_TELEMETRY_REGISTER_FAILED",
                                message="Failed to register OPEN_NOW trade in temporal telemetry",
                                context={
                                    "symbol": event.get("symbol"),
                                    "signal_id": event.get("signal_id"),
                                    "error": str(reg_err),
                                },
                                source={"module": "signal_engine", "function": "run_once"},
                            )
                        except Exception:
                            pass

                distribution_router.route(event, now_ts)

        except Exception as e:
            observability_logger.log_error({
                "event_type": "error",
                "module": "signal_engine",
                "symbol": symbol,
                "error": str(e),
            })
            continue


def run_for_symbols(symbols, now_ts=None, focus_context=False, scheduler_stage=None) -> None:
    return run_once(
        now_ts=now_ts,
        forced_symbols=symbols,
        forced_focus_context=focus_context,
        scheduler_stage=scheduler_stage or ("FOCUS" if focus_context else "WIDE"),
    )
