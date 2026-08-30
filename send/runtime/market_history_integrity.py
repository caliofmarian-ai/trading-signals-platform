from __future__ import annotations

from math import isfinite
from typing import Any, Dict, List, Mapping, Sequence


def inspect_candles(candles: Sequence[Mapping[str, Any]], timeframe_seconds: int) -> Dict[str, Any]:
    """Inspect newest-first OHLC history without altering provider evidence."""
    if timeframe_seconds <= 0:
        raise ValueError("timeframe_seconds must be positive")

    invalid_ohlc = 0
    invalid_timestamp = 0
    duplicate_timestamps = 0
    out_of_order = 0
    unaligned_timestamps = 0
    gap_count = 0
    seen: set[int] = set()
    previous_ts: int | None = None

    for candle in candles:
        try:
            ts = int(candle["ts"])
            open_price = float(candle["open"])
            high = float(candle["high"])
            low = float(candle["low"])
            close = float(candle["close"])
        except (KeyError, TypeError, ValueError, OverflowError):
            invalid_ohlc += 1
            continue

        if ts <= 0:
            invalid_timestamp += 1
        if ts % timeframe_seconds != 0:
            unaligned_timestamps += 1
        if ts in seen:
            duplicate_timestamps += 1
        seen.add(ts)

        if previous_ts is not None:
            delta = previous_ts - ts
            if delta <= 0:
                out_of_order += 1
            elif delta > timeframe_seconds:
                gap_count += 1
        previous_ts = ts

        prices = (open_price, high, low, close)
        if (
            not all(isfinite(value) and value > 0 for value in prices)
            or low > high
            or not (low <= open_price <= high)
            or not (low <= close <= high)
        ):
            invalid_ohlc += 1

    hard_errors = invalid_ohlc + invalid_timestamp + duplicate_timestamps + out_of_order + unaligned_timestamps
    if hard_errors:
        state = "INVALID"
    elif len(candles) < 2:
        state = "COLLECTING"
    else:
        state = "VALID"

    return {
        "state": state,
        "checked_candles": len(candles),
        "invalid_ohlc": invalid_ohlc,
        "invalid_timestamp": invalid_timestamp,
        "duplicate_timestamps": duplicate_timestamps,
        "out_of_order": out_of_order,
        "unaligned_timestamps": unaligned_timestamps,
        "gap_count": gap_count,
        "hard_error_count": hard_errors,
    }


def inspect_history(candles_by_timeframe: Mapping[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
    reports = {
        "M1": inspect_candles(candles_by_timeframe.get("M1", []), 60),
        "M5": inspect_candles(candles_by_timeframe.get("M5", []), 300),
    }
    states = {report["state"] for report in reports.values()}
    if "INVALID" in states:
        state = "INVALID"
    elif states == {"VALID"}:
        state = "VALID"
    else:
        state = "COLLECTING"
    return {
        "state": state,
        "timeframes": reports,
        "hard_error_count": sum(report["hard_error_count"] for report in reports.values()),
        "gap_count": sum(report["gap_count"] for report in reports.values()),
    }
