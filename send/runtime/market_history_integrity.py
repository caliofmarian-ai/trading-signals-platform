from __future__ import annotations

from datetime import datetime, timedelta, timezone
from math import isfinite
from typing import Any, Dict, List, Mapping, Sequence


def _touches_utc_weekend(older_ts: int, newer_ts: int) -> bool:
    """Classify only the objective calendar fact; do not invent FX session hours."""
    older_date = datetime.fromtimestamp(int(older_ts), tz=timezone.utc).date()
    newer_date = datetime.fromtimestamp(int(newer_ts), tz=timezone.utc).date()
    day_span = (newer_date - older_date).days
    if day_span >= 7:
        return True
    for offset in range(max(0, day_span) + 1):
        if (older_date + timedelta(days=offset)).weekday() >= 5:
            return True
    return False


def _gap_detail(newer_ts: int, older_ts: int, timeframe_seconds: int) -> Dict[str, Any]:
    delta_seconds = int(newer_ts) - int(older_ts)
    missing_intervals = max(0, (delta_seconds // timeframe_seconds) - 1)
    return {
        "newer_ts": int(newer_ts),
        "older_ts": int(older_ts),
        "delta_seconds": delta_seconds,
        "missing_intervals": missing_intervals,
        "classification": (
            "WEEKEND_DISCONTINUITY"
            if _touches_utc_weekend(older_ts, newer_ts)
            else "NON_WEEKEND_GAP"
        ),
    }


def inspect_candles(candles: Sequence[Mapping[str, Any]], timeframe_seconds: int) -> Dict[str, Any]:
    """Inspect newest-first OHLC history without altering provider evidence.

    Gaps are evidence discontinuities, not fabricated corruption. They remain
    visible in the report and reduce ``contiguous_head_count`` so downstream
    temporal physics can use only the newest exactly-cadenced segment.
    """
    if timeframe_seconds <= 0:
        raise ValueError("timeframe_seconds must be positive")

    invalid_ohlc = 0
    invalid_timestamp = 0
    duplicate_timestamps = 0
    out_of_order = 0
    unaligned_timestamps = 0
    gap_details: List[Dict[str, Any]] = []
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
                gap_details.append(_gap_detail(previous_ts, ts, timeframe_seconds))
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

    if state == "INVALID":
        contiguous_head_count = 0
        continuity_state = "INVALID"
    elif len(candles) == 0:
        contiguous_head_count = 0
        continuity_state = "COLLECTING"
    elif len(candles) == 1:
        contiguous_head_count = 1
        continuity_state = "COLLECTING"
    else:
        contiguous_head_count = 1
        for index in range(1, len(candles)):
            newer_ts = int(candles[index - 1]["ts"])
            older_ts = int(candles[index]["ts"])
            if newer_ts - older_ts != timeframe_seconds:
                break
            contiguous_head_count += 1
        continuity_state = "CONTIGUOUS" if contiguous_head_count == len(candles) else "GAPPED"

    weekend_gap_count = sum(
        1 for detail in gap_details if detail["classification"] == "WEEKEND_DISCONTINUITY"
    )
    non_weekend_gap_count = len(gap_details) - weekend_gap_count

    return {
        "state": state,
        "temporal_continuity_state": continuity_state,
        "checked_candles": len(candles),
        "contiguous_head_count": contiguous_head_count,
        "invalid_ohlc": invalid_ohlc,
        "invalid_timestamp": invalid_timestamp,
        "duplicate_timestamps": duplicate_timestamps,
        "out_of_order": out_of_order,
        "unaligned_timestamps": unaligned_timestamps,
        "gap_count": len(gap_details),
        "weekend_gap_count": weekend_gap_count,
        "non_weekend_gap_count": non_weekend_gap_count,
        "gap_details": gap_details,
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

    continuity_states = {report["temporal_continuity_state"] for report in reports.values()}
    if "INVALID" in continuity_states:
        continuity_state = "INVALID"
    elif "GAPPED" in continuity_states:
        continuity_state = "GAPPED"
    elif continuity_states == {"CONTIGUOUS"}:
        continuity_state = "CONTIGUOUS"
    else:
        continuity_state = "COLLECTING"

    return {
        "state": state,
        "temporal_continuity_state": continuity_state,
        "timeframes": reports,
        "contiguous_candle_counts": {
            code: report["contiguous_head_count"] for code, report in reports.items()
        },
        "hard_error_count": sum(report["hard_error_count"] for report in reports.values()),
        "gap_count": sum(report["gap_count"] for report in reports.values()),
        "weekend_gap_count": sum(report["weekend_gap_count"] for report in reports.values()),
        "non_weekend_gap_count": sum(report["non_weekend_gap_count"] for report in reports.values()),
    }
