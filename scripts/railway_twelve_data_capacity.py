"""One-shot, read-only Twelve Data scan-demand versus REST-budget assessment.

Never mutates active symbols, provider selection, watchlist, runtime or broker.
Only counts/safe enums leave this module: no symbols, tokens or paths.
Calculations are capacity estimates under the documented 60-second wide-scan
cycle, not observed provider HTTP calls or evidence of strategy success.
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any, Mapping

MAX_INPUT_BYTES = 64 * 1024
MAX_SYMBOLS = 128
MAX_FOCUS = 2
WIDE_CYCLE_SECONDS = 60
REST_INTERVALS_PER_SYMBOL = 2
_SYMBOL = re.compile(r"^[A-Z0-9]{2,12}/[A-Z0-9]{2,12}$")
_ALLOWED_PROVIDER = {"FINNHUB", "TWELVE_DATA"}


def _read_small_json(path: Path) -> tuple[dict[str, Any] | None, str]:
    try:
        size = path.stat().st_size
        if size > MAX_INPUT_BYTES:
            return None, "SOURCE_TOO_LARGE"
        if size == 0:
            return None, "EMPTY_FILE"
        with path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
    except FileNotFoundError:
        return None, "FILE_NOT_FOUND"
    except (OSError, ValueError, UnicodeError):
        return None, "INVALID_OR_UNREADABLE"
    if not isinstance(data, dict):
        return None, "NOT_A_JSON_OBJECT"
    return data, "PRESENT"


def _symbols(raw: Any) -> list[str] | None:
    """Reproduce observable universe shape; never report actual identities."""
    if not isinstance(raw, Mapping):
        return None
    if "symbols" in raw:
        values = raw.get("symbols")
        if not isinstance(values, list):
            return None
    else:
        values = []
        found = False
        for domain in ("forex", "crypto"):
            if domain in raw:
                found = True
                rows = raw.get(domain)
                if not isinstance(rows, list):
                    return None
                values += rows
        if not found:
            return None
    if len(values) > MAX_SYMBOLS:
        return None
    clean = []
    seen = set()
    for value in values:
        if not isinstance(value, str):
            return None
        symbol = value.strip().upper().replace("_", "/")
        if not _SYMBOL.fullmatch(symbol):
            return None
        if symbol not in seen:
            seen.add(symbol)
            clean.append(symbol)
    return clean


def _env_int(name: str, fallback: int, *, min_value: int, max_value: int) -> int | None:
    raw = os.getenv(name)
    if raw is None:
        return fallback
    # Do not echo raw env values: an invalid value could be a credential.
    value = raw.strip()
    if not value or not value.isdecimal():
        return None
    parsed = int(value)
    return parsed if min_value <= parsed <= max_value else None


def estimate_request_demand(
    *,
    active_symbols_path: str | Path,
    focus_state_path: str | Path,
    provider: str,
) -> dict[str, Any]:
    """Conservative idealized REST demand if wide cycle runs to completion.

    For Twelve Data: unconstrained wide scan evaluates each active non-focus
    symbol once in 60s and asks for M1 and M5; with <60s REST cache TTL the
    same symbol+timeframe is not expected to remain cached on its next cycle.
    If focus state is unavailable, up to two active symbols *may* be focused;
    calculate only a lower bound, not an exact demand. Actual requests can be
    fewer because the runtime fails closed on the request budget.
    """
    raw_provider = str(provider or "").strip().upper()
    selected = raw_provider if raw_provider in _ALLOWED_PROVIDER else "UNKNOWN"
    raw_symbols, active_state = _read_small_json(Path(active_symbols_path))
    symbols = _symbols(raw_symbols)
    if symbols is None:
        active_state = active_state if active_state != "PRESENT" else "INVALID_SYMBOLS"
    active_count = len(symbols) if symbols is not None else None

    raw_focus, focus_status = _read_small_json(Path(focus_state_path))
    focus_count: int | None = None
    if symbols is not None and raw_focus is not None:
        watchlist = raw_focus.get("watchlist")
        if isinstance(watchlist, list) and len(watchlist) <= MAX_FOCUS:
            if all(isinstance(x, str) for x in watchlist):
                normalized = [x.strip().upper().replace("_", "/") for x in watchlist]
                if len(set(normalized)) == len(normalized) and set(normalized).issubset(set(symbols)):
                    focus_count = len(normalized)
                else:
                    focus_status = "INVALID_FOCUS_MEMBERSHIP"
            else:
                focus_status = "INVALID_FOCUS_ENTRIES"
        else:
            focus_status = "INVALID_FOCUS_LIST"
    elif raw_focus is not None:
        focus_status = "ACTIVE_SYMBOLS_UNAVAILABLE"

    limit = _env_int(
        "TWELVE_DATA_REST_REQUESTS_PER_MINUTE", 8,
        min_value=1, max_value=1000,
    )
    cache_ttl = _env_int(
        "TWELVE_DATA_REST_CACHE_SECONDS", 55,
        min_value=1, max_value=86400,
    )
    streaming_value = os.getenv("TWELVE_DATA_STREAMING_ENABLED", "1").strip().lower()
    stream_enabled = streaming_value not in {"0", "false", "off", "no"}
    # Invalid/unexpected input is not reinterpreted as safely enabled.
    stream_known = streaming_value in {"1", "true", "on", "yes", "0", "false", "off", "no"}
    if not stream_known:
        stream_enabled = None

    wide_min = None
    wide_max = None
    demand_min = None
    demand_max = None
    demand_basis = "UNAVAILABLE"
    exceed = None
    if active_count is not None and cache_ttl is not None:
        if focus_count is not None and stream_enabled is not None:
            # When streaming is false, even focus needs REST; otherwise only wide.
            wide_min = wide_max = active_count - focus_count if stream_enabled else active_count
        else:
            wide_min = max(0, active_count - MAX_FOCUS)
            wide_max = active_count
        if cache_ttl < WIDE_CYCLE_SECONDS:
            demand_min = REST_INTERVALS_PER_SYMBOL * wide_min
            demand_max = REST_INTERVALS_PER_SYMBOL * wide_max
            demand_basis = "UNCAPPED_TWO_TIMEFRAMES_PER_WIDE_SYMBOL_PER_60S"
            exceed = (
                demand_min > limit if limit is not None else None
            )
        else:
            demand_basis = "CACHE_TTL_MAY_COVER_NEXT_WIDE_CYCLE"

    return {
        "scope": "PREBOOT_CONFIG_CAPACITY_ESTIMATE_NOT_OBSERVED_REQUESTS",
        "provider": selected,
        "active_symbols_source_status": active_state,
        "active_symbol_count": active_count,
        "focus_source_status": focus_status,
        "focus_active_symbol_count": focus_count,
        "twelve_rest_budget_requests_per_60s": limit,
        "twelve_rest_cache_ttl_seconds": cache_ttl,
        "twelve_live_focus_stream_enabled_by_config": stream_enabled,
        "wide_scan_cycle_seconds": WIDE_CYCLE_SECONDS,
        "wide_rest_symbol_count_lower_bound": wide_min,
        "wide_rest_symbol_count_upper_bound": wide_max,
        "uncapped_rest_calls_per_wide_cycle_lower_bound": demand_min,
        "uncapped_rest_calls_per_wide_cycle_upper_bound": demand_max,
        "structural_budget_exceeded_if_all_wide_scanned": (
            exceed if selected == "TWELVE_DATA" else None
        ),
        "demand_basis": demand_basis,
        "actual_rest_http_calls_observed": None,
        "provider_http429_verified": False,
        "strategy_throughput_verified": False,
    }


def collect_request_capacity(*, base_dir: Path) -> dict[str, Any]:
    """Read stable bounded config paths, without emitting their contents."""
    root = Path(base_dir)
    try:
        return estimate_request_demand(
            active_symbols_path=root / "config" / "active_symbols.json",
            focus_state_path=root / "state" / "focus_state.json",
            provider=os.getenv("MARKET_DATA_PROVIDER", ""),
        )
    except Exception:
        return {
            "scope": "PREBOOT_CONFIG_CAPACITY_ESTIMATE_NOT_OBSERVED_REQUESTS",
            "status": "UNKNOWN",
            "reason": "CAPACITY_READER_FAILED",
        }
