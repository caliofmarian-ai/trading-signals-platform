"""One-shot, read-only historical Binary Strategy V2 evaluation probe.

This is NOT a backtest, signal, win-rate, OPEN_NOW publication, or live
market-data observation. It answers only whether the current governed strategy
can process an existing, internally persisted Finnhub candle window that was
available at the historical decision cutoff.

Never calls a market provider, a Telegram API, any FSM, distribution, outcome
service, telemetry writer, broker, or filesystem write operation. Never exposes
prices, directions, scores, signal IDs or strategy recommendations in logs.
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any, Mapping, Optional

from core import market_data_provider_control, runtime_param_gate
from core.strategy_v2 import decide
from runtime.market_history_integrity import inspect_history


REPORT_COMPONENT = "finnhub_historical_strategy_probe"
MAX_STORE_BYTES = 2 * 1024 * 1024
MAX_SETTINGS_BYTES = 64 * 1024
MAX_CANDLES = 500


def _report(status: str, **safe_fields: Any) -> dict[str, Any]:
    return {
        "component": REPORT_COMPONENT,
        "status": status,
        "scope": "ONE_HISTORICAL_READ_ONLY_STRATEGY_CYCLE_NOT_LIVE",
        "data_provenance": "PERSISTED_FINNHUB_LABEL_UNVERIFIED_EXTERNALLY",
        "fresh_market_data_proven": False,
        "telegram_signals_published": 0,
        "broker_trades_executed": 0,
        "market_truth_outcomes_created": 0,
        "hypothetical_win_rate_calculated": False,
        "historical_replay_only": True,
        **safe_fields,
    }


def _read_bounded_object(path: Path, *, limit: int) -> dict[str, Any]:
    if path.is_symlink() or not path.is_file():
        raise ValueError("UNAVAILABLE_OR_SYMLINK")
    with path.open("rb") as handle:
        payload = handle.read(limit + 1)
    if len(payload) > limit:
        raise ValueError("SOURCE_TOO_LARGE")
    value = json.loads(payload)
    if not isinstance(value, dict):
        raise ValueError("SOURCE_NOT_OBJECT")
    return value


def _complete_runs(rows: list[dict[str, Any]], seconds: int) -> list[list[dict[str, Any]]]:
    """Split newest-first real, completed OHLC observations at actual gaps."""
    runs: list[list[dict[str, Any]]] = []
    current: list[dict[str, Any]] = []
    for row in rows:
        if row.get("complete") is not True:
            if current:
                runs.append(current)
                current = []
            continue
        if current and int(current[-1]["ts"]) - int(row["ts"]) != seconds:
            runs.append(current)
            current = []
        current.append(row)
    if current:
        runs.append(current)
    return runs


def _select_no_lookahead_window(
    m1: list[dict[str, Any]],
    m5: list[dict[str, Any]],
    *,
    min_m1: int,
    min_m5: int,
) -> Optional[tuple[list[dict[str, Any]], list[dict[str, Any]], int]]:
    """Use only completed candles whose close precedes the M1 decision cutoff."""
    for run_m1 in _complete_runs(m1, 60):
        if len(run_m1) < min_m1:
            continue
        # M1 decision is observed only after this M1 bar closes, not at open.
        cutoff = int(run_m1[0]["ts"]) + 60
        earlier_m5 = [
            row for row in m5
            if row.get("complete") is True
            and int(row["ts"]) + 300 <= cutoff
        ]
        m5_runs = _complete_runs(earlier_m5, 300)
        if not m5_runs or len(m5_runs[0]) < min_m5:
            continue
        return run_m1[:min_m1], m5_runs[0][:min_m5], cutoff
    return None


def _provider_selected() -> bool:
    try:
        return market_data_provider_control.get_active_provider() == "FINNHUB"
    except Exception:
        return False


def collect_historical_strategy_probe(
    *, base_dir: Path, now_ts: Optional[int] = None
) -> dict[str, Any]:
    """Evaluate once without any publication, side effects or invented outcome."""
    now = int(time.time()) if now_ts is None else now_ts
    if isinstance(now, bool) or not isinstance(now, int) or now <= 0:
        raise ValueError("invalid observation timestamp")

    if os.getenv("SHADOW_MODE", "").strip().lower() not in {"true", "1", "yes", "on"}:
        return _report("SHADOW_MODE_REQUIRED")
    if os.getenv("ENABLE_BROKER_EXECUTION", "").strip().lower() in {"true", "1", "yes", "on"}:
        return _report("BROKER_EXECUTION_GUARD_BLOCKED")
    if not _provider_selected():
        return _report("FINNHUB_NOT_SELECTED_OR_UNVERIFIED")

    root = Path(base_dir).resolve()
    source_env = os.getenv("FINNHUB_CANDLE_STORE", "").strip()
    store = Path(source_env) if source_env else root / "market_data" / "finnhub_eurusd.json"
    if not store.is_absolute():
        store = root / store
    if not store.resolve().is_relative_to(root):
        return _report("STORE_PATH_OUTSIDE_GOVERNED_ROOT")

    try:
        payload = _read_bounded_object(store, limit=MAX_STORE_BYTES)
    except (OSError, ValueError, TypeError):
        return _report("STORE_UNAVAILABLE_OR_INVALID")
    if payload.get("provider") != "FINNHUB":
        return _report("PROVIDER_PROVENANCE_MISMATCH")
    candles = payload.get("candles")
    if not isinstance(candles, dict):
        return _report("CANDLE_STORE_INVALID")
    m1, m5 = candles.get("M1"), candles.get("M5")
    if not isinstance(m1, list) or not isinstance(m5, list):
        return _report("CANDLE_STORE_INVALID")
    if not (1 <= len(m1) <= MAX_CANDLES and 1 <= len(m5) <= MAX_CANDLES):
        return _report("CANDLE_COUNT_UNSAFE")
    for code, rows in (("M1", m1), ("M5", m5)):
        for row in rows:
            if not isinstance(row, dict):
                return _report("CANDLE_STORE_INVALID")
            if (row.get("provider") != "FINNHUB"
                or str(row.get("symbol", "")).strip().upper() not in {"EUR/USD", "EURUSD"}
                or row.get("timeframe") != code
                or not isinstance(row.get("complete"), bool)):
                return _report("CANDLE_PROVENANCE_UNVERIFIED")
    integrity = inspect_history({"M1": m1, "M5": m5})
    if integrity["state"] != "VALID":
        return _report("CANDLE_INTEGRITY_NOT_VALID")

    try:
        params = runtime_param_gate.load_runtime_algo_params(str(root / "config" / "algo_params.json"))
        settings_path = root / "config" / "admin_settings.json"
        settings = _read_bounded_object(settings_path, limit=MAX_SETTINGS_BYTES) if settings_path.is_file() else {}
        buffer_mode = str(settings.get("buffer_mode") or "MEDIUM").strip().upper()
        if buffer_mode not in {"SMALL", "MEDIUM", "LARGE"}:
            return _report("INVALID_GOVERNED_BUFFER_MODE")
        required_m1 = int(os.getenv("FINNHUB_MIN_CANDLES", "201"))
        if not 2 <= required_m1 <= MAX_CANDLES:
            return _report("FINNHUB_CANDLE_REQUIREMENT_INVALID")
        # Retain the current Finnhub adapter's 201/201 gate for source
        # reproducibility, despite the Market Model's smaller M1 base need.
        selected = _select_no_lookahead_window(
            m1, m5, min_m1=required_m1, min_m5=required_m1,
        )
        if selected is None:
            return _report(
                "NO_COMPLETED_HISTORICAL_OVERLAP",
                required_bars_each=required_m1,
            )
        window_m1, window_m5, cutoff_ts = selected
        if cutoff_ts > now:
            return _report("HISTORICAL_CUTOFF_IN_FUTURE")
        # No Signal Engine, FSM persistence, event logger, distribution or
        # broker invocation: strategy_v2.decide is pure/deterministic.
        evaluation = decide(
            candles_m1=window_m1,
            candles_m5=window_m5,
            params=params,
            buffer_mode=buffer_mode,
            context={"decision_timeframe": "M1", "cycle_id": "HISTORICAL_READONLY_PROBE"},
        )
        if evaluation.canonical_spec != "ALGO_SPEC_v3.0.0" or evaluation.signal_handoff_ready:
            return _report("UNEXPECTED_STRATEGY_AUTHORITY_OR_HANDOFF")
        return _report(
            "HISTORICAL_EVALUATION_COMPLETED",
            historical_cutoff_ts=cutoff_ts,
            historical_age_days=(now - cutoff_ts) // 86400,
            m1_completed_window_bars=len(window_m1),
            m5_completed_window_bars=len(window_m5),
            strategy_version=evaluation.strategy_version,
            model_decision_object_created=True,
        )
    except Exception:
        # Do not log exception text; it may include prices, filesystem paths or
        # provider secrets. This is only a diagnostic, never a boot gate.
        return _report("HISTORICAL_EVALUATION_UNAVAILABLE")
