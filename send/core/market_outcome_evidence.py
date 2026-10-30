"""Objective post-OPEN_NOW market-truth evidence by symbol/provider/strategy version.

Read-only. Never uses Telegram, operational or community outcomes as labels.
A numeric observed win rate is descriptive and not proof of trading success,
broker execution, investment suitability, or statistical stability.
"""

from __future__ import annotations

import math
import os
import re
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Mapping, Optional

from core import storage
from core.jsonl_parser import iter_jsonl

MAX_SOURCE_BYTES = 16 * 1024 * 1024
MAX_WINDOW_DAYS = 30
MIN_DESCRIPTIVE_DECISIVE_SAMPLE = 5
TELEMETRY_VERSION = "3.0.0"
TELEMETRY_SPEC = "TRADE_TEMPORAL_TELEMETRY_SPEC_v3.0.0"
_ALLOWED_LABELS = frozenset({"WIN", "LOSS", "DRAW"})
_SAFE_SYMBOL = re.compile(r"^[A-Z0-9/_-]{2,24}$")
_SAFE_PROVIDER = re.compile(r"^[A-Z0-9_]{2,32}$")
_SAFE_TIMEFRAME = re.compile(r"^[A-Z0-9]{1,8}$")
_SAFE_VERSION = re.compile(r"^[A-Za-z0-9_.-]{1,40}$")


def _utc(ts: int) -> str:
    return datetime.fromtimestamp(int(ts), timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _source_path() -> str:
    return (
        os.getenv("TRADE_TEMPORAL_TELEMETRY_LOG")
        or storage.root_path("observability", "trade_temporal_telemetry.jsonl")
    )


def _number(value: Any) -> Optional[float]:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    result = float(value)
    return result if math.isfinite(result) and result > 0 else None


def _canonical_row(row: Dict[str, Any]) -> Optional[tuple[Any, ...]]:
    """Validate immutable identity and raw objective expiry-label provenance."""
    if row.get("truth_domain") != "MARKET_TRUTH":
        return None
    if row.get("telemetry_status") != "FINALIZED":
        return None
    if (
        row.get("telemetry_version") != TELEMETRY_VERSION
        or row.get("telemetry_specification") != TELEMETRY_SPEC
    ):
        return None
    trade_id = row.get("trade_id")
    signal_id = row.get("signal_id")
    if (
        not isinstance(trade_id, str) or not trade_id.strip()
        or not isinstance(signal_id, str) or signal_id.strip() != trade_id.strip()
    ):
        return None

    symbol = row.get("symbol")
    provider = row.get("market_provider")
    timeframe = row.get("timeframe")
    if not all(isinstance(x, str) for x in (symbol, provider, timeframe)):
        return None
    symbol, provider, timeframe = (
        symbol.strip().upper(), provider.strip().upper(), timeframe.strip().upper()
    )
    if (
        not _SAFE_SYMBOL.fullmatch(symbol)
        or not _SAFE_PROVIDER.fullmatch(provider)
        or not _SAFE_TIMEFRAME.fullmatch(timeframe)
    ):
        return None

    raw_strategy_version = row.get("strategy_version")
    if raw_strategy_version is not None and (
        not isinstance(raw_strategy_version, str)
        or not _SAFE_VERSION.fullmatch(raw_strategy_version)
    ):
        return None

    open_ts = row.get("open_ts")
    finalized_ts = row.get("finalized_ts")
    if isinstance(open_ts, bool) or not isinstance(open_ts, int) or open_ts <= 0:
        return None
    if (
        isinstance(finalized_ts, bool) or not isinstance(finalized_ts, int)
        or finalized_ts < open_ts
    ):
        return None
    direction = row.get("direction")
    entry = _number(row.get("entry_price"))
    if direction not in ("BUY", "SELL") or entry is None:
        return None
    checkpoints = row.get("checkpoints")
    expiry = checkpoints.get("expiry") if isinstance(checkpoints, dict) else None
    if not isinstance(expiry, dict) or expiry.get("state") != "OBSERVED":
        return None
    # FINALIZED is authoritative only when all governed checkpoints resolved
    # with real observations; otherwise the record is not objective full truth.
    if not all(
        isinstance(checkpoints.get(key), dict)
        and checkpoints[key].get("state") == "OBSERVED"
        for key in ("mid_expiry", "expiry", "post_1m", "post_3m", "post_5m")
    ):
        return None
    price = _number(expiry.get("price"))
    target_ts = _number(expiry.get("target_ts"))
    observed_ts = _number(expiry.get("observed_ts"))
    if (
        price is None or target_ts is None or observed_ts is None
        or observed_ts < target_ts
        or expiry.get("provider") != provider
    ):
        return None
    recorded_label = row.get("result_at_expiry")
    if not isinstance(recorded_label, str) or recorded_label not in _ALLOWED_LABELS:
        return None
    expected_label = "DRAW" if price == entry else (
        "WIN" if (price > entry if direction == "BUY" else price < entry) else "LOSS"
    )
    if (
        recorded_label != expected_label
        or expiry.get("directional_result") != expected_label
        or _number(row.get("expiry_price")) != price
        or _number(row.get("label_observation_ts")) != observed_ts
        or finalized_ts < observed_ts
    ):
        return None
    return (
        trade_id.strip(), symbol, provider, timeframe, raw_strategy_version,
        recorded_label, open_ts, observed_ts - target_ts,
    )


def _wilson95(wins: int, decisive: int) -> Dict[str, float]:
    z = 1.96
    p = wins / decisive
    z2 = z * z
    denominator = 1 + z2 / decisive
    center = (p + z2 / (2 * decisive)) / denominator
    margin = z * math.sqrt((p * (1 - p) + z2 / (4 * decisive)) / decisive) / denominator
    return {
        "lower": round(max(0, center - margin) * 100, 2),
        "upper": round(min(1, center + margin) * 100, 2),
    }


def _unknown(*, start: int, now: int, reason: str, quality: Mapping[str, int] | None = None) -> Dict[str, Any]:
    return {
        "status": "UNKNOWN",
        "reason": reason,
        "truth_domain": "MARKET_TRUTH",
        "authority": TELEMETRY_SPEC,
        "window_start_utc": _utc(start),
        "window_end_utc": _utc(now),
        "time_basis": "OPEN_TS",
        "verified_finalized_trade_count": None,
        "segment_count": None,
        "segments": [],
        "quality": dict(quality or {}),
        "ranked_by": "DECISIVE_SAMPLE_DESC_NOT_WIN_RATE",
        "profit_or_broker_performance": None,
    }


def build_market_snapshot(
    *,
    range_days: int = 7,
    now_ts: int | None = None,
    path: str | None = None,
    max_segments: int = 10,
) -> Dict[str, Any]:
    """Return only validated MARKET_TRUTH finalized records from the open-time cohort."""
    if isinstance(range_days, bool) or not isinstance(range_days, int) or not 1 <= range_days <= MAX_WINDOW_DAYS:
        raise ValueError("range_days must be an integer between 1 and 30")
    if isinstance(max_segments, bool) or not isinstance(max_segments, int) or not 1 <= max_segments <= 100:
        raise ValueError("max_segments must be an integer between 1 and 100")
    if now_ts is None:
        now = int(time.time())
    elif isinstance(now_ts, bool) or not isinstance(now_ts, int) or now_ts <= 0:
        raise ValueError("now_ts must be a positive integer")
    else:
        now = now_ts
    start = now - range_days * 86400
    source = path or _source_path()
    quality = Counter(
        {
            "invalid_rows": 0,
            "incomplete_rows": 0,
            "other_truth_excluded": 0,
            "historical_excluded": 0,
            "out_of_window": 0,
            "identical_duplicates": 0,
            "conflicting_identities": 0,
            "future_evidence_excluded": 0,
        }
    )
    try:
        if Path(source).stat().st_size > MAX_SOURCE_BYTES:
            return _unknown(start=start, now=now, reason="SOURCE_TOO_LARGE_FOR_INTERACTIVE_SCAN")
    except FileNotFoundError:
        return _unknown(start=start, now=now, reason="MARKET_TELEMETRY_FILE_NOT_FOUND")
    except OSError:
        return _unknown(start=start, now=now, reason="MARKET_TELEMETRY_FILE_UNREADABLE")

    seen: Dict[str, tuple[Any, ...]] = {}
    conflicted: set[str] = set()
    try:
        for row, error in iter_jsonl(source):
            if error is not None:
                quality["invalid_rows"] += 1
                continue
            if row.get("truth_domain") != "MARKET_TRUTH":
                quality["other_truth_excluded"] += 1
                continue
            if row.get("telemetry_status") != "FINALIZED":
                quality["incomplete_rows"] += 1
                continue
            if (
                row.get("telemetry_version") != TELEMETRY_VERSION
                or row.get("telemetry_specification") != TELEMETRY_SPEC
            ):
                quality["historical_excluded"] += 1
                continue
            valid = _canonical_row(row)
            if valid is None:
                quality["invalid_rows"] += 1
                continue
            trade_id, _, _, _, _, _, opened, _ = valid
            # Point-in-time reports must not consume labels or finalization
            # whose timestamps lie beyond the observation cutoff.
            if (
                _number(row.get("label_observation_ts")) > now
                or row["finalized_ts"] > now
            ):
                quality["future_evidence_excluded"] += 1
                continue
            if opened < start or opened > now:
                quality["out_of_window"] += 1
                continue
            if trade_id in conflicted:
                quality["conflicting_identities"] += 1
                continue
            if trade_id in seen:
                if valid == seen[trade_id]:
                    quality["identical_duplicates"] += 1
                else:
                    # The identity is now untrustworthy: exclude all its rows.
                    seen.pop(trade_id)
                    conflicted.add(trade_id)
                    quality["conflicting_identities"] += 1
                continue
            seen[trade_id] = valid
    except OSError:
        return _unknown(
            start=start, now=now, reason="MARKET_TELEMETRY_READ_INTERRUPTED",
            quality=quality,
        )

    if not seen:
        return _unknown(
            start=start, now=now,
            reason="NO_VALID_FINALIZED_V3_MARKET_TRUTH_IN_WINDOW",
            quality=quality,
        )

    segments: Dict[tuple[str, str, str, Optional[str]], Dict[str, Any]] = {}
    for (_trade_id, symbol, provider, timeframe, strategy_version, outcome, _opened, lag) in seen.values():
        key = (symbol, provider, timeframe, strategy_version)
        segment = segments.setdefault(
            key, {"symbol": symbol, "market_provider": provider,
                  "timeframe": timeframe, "strategy_version": strategy_version,
                  "wins": 0, "losses": 0, "draws": 0,
                  "expiry_observation_lag_over_30_seconds": 0},
        )
        segment[{"WIN": "wins", "LOSS": "losses", "DRAW": "draws"}[outcome]] += 1
        if lag > 30:
            segment["expiry_observation_lag_over_30_seconds"] += 1

    result_segments = []
    for segment in segments.values():
        wins, losses, draws = segment["wins"], segment["losses"], segment["draws"]
        n = wins + losses
        sufficient = n >= MIN_DESCRIPTIVE_DECISIVE_SAMPLE
        result_segments.append(
            {
                **segment,
                "total_finalized": n + draws,
                "decisive_sample": n,
                "insufficient_sample": not sufficient,
                "descriptive_win_rate_percent": (
                    round(wins / n * 100, 2) if sufficient else None
                ),
                "wilson_95_interval_percent": _wilson95(wins, n) if sufficient else None,
                "minimum_descriptive_sample": MIN_DESCRIPTIVE_DECISIVE_SAMPLE,
                "statistical_proof_or_live_payout": False,
            }
        )
    result_segments.sort(
        key=lambda x: (
            -x["decisive_sample"], x["symbol"], x["market_provider"],
            x["timeframe"], x["strategy_version"] or "",
        )
    )
    return {
        "status": "OBSERVED",
        "reason": "VALIDATED_FINALIZED_MARKET_TRUTH",
        "truth_domain": "MARKET_TRUTH",
        "authority": TELEMETRY_SPEC,
        "window_start_utc": _utc(start),
        "window_end_utc": _utc(now),
        "time_basis": "OPEN_TS",
        "verified_finalized_trade_count": len(seen),
        "segment_count": len(result_segments),
        "segments": result_segments[:max_segments],
        "segments_truncated": len(result_segments) > max_segments,
        "quality": dict(quality),
        "ranked_by": "DECISIVE_SAMPLE_DESC_NOT_WIN_RATE",
        "profit_or_broker_performance": None,
    }


def render_market_summary(snapshot: Mapping[str, Any]) -> str:
    lines = [
        "Objective market outcomes — finalized OPEN_NOW (trailing open-time window)",
        f"Evidence: {snapshot.get('status', 'UNKNOWN')}",
        f"Window UTC: {snapshot.get('window_start_utc', 'UNKNOWN')} to {snapshot.get('window_end_utc', 'UNKNOWN')}",
    ]
    if snapshot.get("status") != "OBSERVED":
        lines.append(f"Reason: {snapshot.get('reason', 'UNKNOWN')}")
        lines.append("Market win-rate: UNKNOWN — not zero.")
    else:
        lines.append(f"Validated trades: {snapshot.get('verified_finalized_trade_count')}")
        lines.append("Symbols grouped by provider, timeframe and strategy version (sample-ranked):")
        for segment in list(snapshot.get("segments") or [])[:5]:
            n = segment["decisive_sample"]
            rate = segment["descriptive_win_rate_percent"]
            ci = segment["wilson_95_interval_percent"]
            rate_text = (
                "UNKNOWN (small sample)" if rate is None
                else f"{rate}% (95% Wilson {ci['lower']}–{ci['upper']}%)"
            )
            lines.append(
                f"- {segment['symbol']} {segment['timeframe']} "
                f"{segment['market_provider']}, v={segment.get('strategy_version') or 'UNKNOWN'}: "
                f"W/L/D={segment['wins']}/{segment['losses']}/{segment['draws']}, "
                f"n={n}; descriptive {rate_text}"
            )
        if snapshot.get("segments_truncated"):
            lines.append("Additional segments omitted from compact display.")
    q = snapshot.get("quality") or {}
    if any(q.values()):
        lines.append(
            f"Quality: invalid {q.get('invalid_rows', 0)}, incomplete {q.get('incomplete_rows', 0)}, "
            f"conflicting {q.get('conflicting_identities', 0)}, future excluded {q.get('future_evidence_excluded', 0)}, "
            f"other-truth excluded {q.get('other_truth_excluded', 0)}"
        )
    lines.extend(
        [
            "No community votes, Telegram feedback or operational MISSED results are market labels.",
            "Descriptive data only; no statistical acceptance, broker execution or profit claim.",
        ]
    )
    return "\n".join(lines)
