"""Safe, one-shot production evidence checkpoint for Railway deployment logs.

Reads only existing persisted v3 observability truth, after Railway readiness
checks and before runtime workers start. No network, database, Telegram, or
broker actions; no writes to persisted state. Never prints raw event records,
identifiers, prices, log paths, credentials or exception messages.

This checkpoint is a *snapshot at startup*, NOT a streaming liveness or trade
performance guarantee. It cannot establish client receipt, user interaction,
broker execution or statistically validated win-rate.
"""

from __future__ import annotations

import json
import math
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Mapping


EVENT_PREFIX = "TSP_PRODUCTION_EVIDENCE "
CHECKPOINT_VERSION = "1.0.0"
_SEGMENT_LIMIT = 3
_ALLOWED_STATES = frozenset({"OBSERVED", "UNKNOWN", "PARTIAL"})
_SAFE_CODE = re.compile(r"^[A-Z0-9_]{1,90}$")
_SAFE_LABEL = re.compile(r"^[A-Za-z0-9_./-]{1,40}$")

_QUALITY_FIELDS = (
    "invalid_count", "invalid_rows", "historical_excluded_count",
    "historical_excluded_rows", "duplicate_event_rows", "duplicate_event_ids",
    "conflicting_identities", "incomplete_rows",
    "other_truth_excluded", "future_evidence_excluded",
    "out_of_window", "identical_duplicates", "unmatched_exit_count",
)


def _utc(value: int) -> str:
    return datetime.fromtimestamp(value, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _status(value: Any) -> str:
    return value if isinstance(value, str) and value in _ALLOWED_STATES else "UNKNOWN"


def _reason(value: Any) -> str:
    if isinstance(value, str) and _SAFE_CODE.fullmatch(value):
        return value
    return "UNKNOWN_REASON"


def _label(value: Any) -> str:
    if isinstance(value, str) and _SAFE_LABEL.fullmatch(value):
        return value
    return "UNKNOWN"


def _count(value: Any) -> int | None:
    if isinstance(value, int) and not isinstance(value, bool) and value >= 0:
        return value
    return None


def _number(value: Any, *, minimum: float = 0, maximum: float = 1_000_000) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (float, int)):
        return None
    n = float(value)
    return round(n, 2) if math.isfinite(n) and minimum <= n <= maximum else None


def _quality(row: Any) -> dict[str, int]:
    if not isinstance(row, Mapping):
        return {}
    return {
        key: n
        for key in _QUALITY_FIELDS
        if (n := _count(row.get(key))) is not None and n > 0
    }


def _read_safely(fn: Callable[[], dict[str, Any]]) -> dict[str, Any]:
    try:
        value = fn()
        return value if isinstance(value, dict) else {
            "status": "UNKNOWN",
            "reason": "INVALID_READER_RESPONSE",
        }
    except Exception:
        # No exception details or log paths may appear in Railway log payloads.
        return {"status": "UNKNOWN", "reason": "READER_EXCEPTION"}


def compose_checkpoint(
    *,
    now_ts: int,
    publications: Mapping[str, Any],
    lifecycle: Mapping[str, Any],
    market: Mapping[str, Any],
    focus: Mapping[str, Any],
) -> dict[str, Any]:
    """Produce an allowlisted, aggregation-only record.

    Do not log raw event records, trade IDs, subscriber/chat IDs, prices,
    or unapproved scenario identifiers, even if the source supplies them.
    """
    if isinstance(now_ts, bool) or not isinstance(now_ts, int) or now_ts <= 0:
        raise ValueError("now_ts must be a positive integer")

    pub_ready = _status(publications.get("status")) == "OBSERVED"
    cycle_status = _status(lifecycle.get("status"))
    market_ready = _status(market.get("status")) == "OBSERVED"
    focus_ready = _status(focus.get("status")) == "OBSERVED"

    segments: list[dict[str, Any]] = []
    if market_ready:
        rows = market.get("segments")
        for segment in (rows if isinstance(rows, list) else [])[:_SEGMENT_LIMIT]:
            if not isinstance(segment, Mapping):
                continue
            sample = _count(segment.get("decisive_sample"))
            descriptive = (
                _number(segment.get("descriptive_win_rate_percent"), maximum=100)
                if sample is not None and sample >= 5 else None
            )
            interval = segment.get("wilson_95_interval_percent")
            ci: dict[str, float] | None = None
            if descriptive is not None and isinstance(interval, Mapping):
                lower = _number(interval.get("lower"), maximum=100)
                upper = _number(interval.get("upper"), maximum=100)
                if lower is not None and upper is not None and lower <= descriptive <= upper:
                    ci = {"lower_percent": lower, "upper_percent": upper}
            segments.append(
                {
                    "symbol": _label(segment.get("symbol")),
                    "market_provider": _label(segment.get("market_provider")),
                    "timeframe": _label(segment.get("timeframe")),
                    "strategy_version": _label(segment.get("strategy_version")),
                    "wins": _count(segment.get("wins")),
                    "losses": _count(segment.get("losses")),
                    "draws": _count(segment.get("draws")),
                    "decisive_sample": sample,
                    "descriptive_win_rate_percent": descriptive,
                    "wilson_95_interval_percent": ci,
                    "not_live_trading_or_statistical_proof": True,
                }
            )

    sources = lifecycle.get("sources")
    sources = sources if isinstance(sources, Mapping) else {}
    engine = sources.get("engine")
    engine = engine if isinstance(engine, Mapping) else {}
    distribution = sources.get("distribution")
    distribution = distribution if isinstance(distribution, Mapping) else {}

    record = {
        "component": "tsp_production_evidence_checkpoint",
        "version": CHECKPOINT_VERSION,
        "checkpoint_utc": _utc(now_ts),
        "scope": "ONE_SHOT_PERSISTED_EVENT_OBSERVATION_AT_STARTUP",
        "live_client_or_broker_acceptance": "NOT_TESTED",
        "publication_24h": {
            "status": _status(publications.get("status")),
            "reason": _reason(publications.get("reason")),
            "unique_published_open_now": (
                _count(publications.get("unique_open_now_published")) if pub_ready else None
            ),
            "rolling_average_per_hour": (
                _number(publications.get("published_per_hour_rolling_avg"))
                if pub_ready else None
            ),
            "quality": {
                "invalid_count": _count(publications.get("invalid_count")),
                "historical_excluded_count": _count(
                    publications.get("historical_excluded_count")
                ),
            },
        },
        "lifecycle_24h": {
            "status": cycle_status,
            "engine_status": _status(engine.get("status")),
            "distribution_status": _status(distribution.get("status")),
            "engine_reason": _reason(engine.get("reason")),
            "distribution_reason": _reason(distribution.get("reason")),
            "pre_open_visible_matched_pairs": (
                _count(lifecycle.get("pre_to_open_visible_matched_pairs"))
                if cycle_status != "UNKNOWN" else None
            ),
            "pairs_lead_at_least_30s": (
                _count(lifecycle.get("pre_to_open_pairs_at_least_30_seconds"))
                if cycle_status != "UNKNOWN" else None
            ),
            "median_observed_pre_open_lead_seconds": (
                _number(lifecycle.get("pre_to_open_lead_median_seconds"))
                if cycle_status != "UNKNOWN" else None
            ),
            "engine_quality": _quality(engine),
            "distribution_quality": _quality(distribution),
        },
        "objective_market_7d": {
            "status": _status(market.get("status")),
            "reason": _reason(market.get("reason")),
            "validated_finalized_trades": (
                _count(market.get("verified_finalized_trade_count"))
                if market_ready else None
            ),
            "segment_count": (
                _count(market.get("segment_count"))
                if market_ready else None
            ),
            "sample_ranked_segments": segments,
            "quality": _quality(market.get("quality")),
        },
        "focus_7d": {
            "status": _status(focus.get("status")),
            "reason": _reason(focus.get("reason")),
            "observed_entries": (
                _count(focus.get("focus_entries")) if focus_ready else None
            ),
            "observed_exits": (
                _count(focus.get("focus_exits")) if focus_ready else None
            ),
            "replacement_victim_gap_count": (
                _count(focus.get("replacement_entries_without_victim_exit"))
                if focus_ready else None
            ),
            "history_coverage": (
                "PARTIAL_EXPLICIT_FSM_EVENTS_ONLY" if focus_ready else "NOT_VERIFIED"
            ),
            "quality": _quality(focus.get("quality")),
        },
    }
    return record


def collect_checkpoint(*, base_dir: Path, now_ts: int | None = None) -> dict[str, Any]:
    """Reuse existing bounded, read-only analytics directly against /data logs."""
    from core import focus_history_evidence, lifecycle_funnel_evidence
    from core import market_outcome_evidence, publication_evidence

    now = int(time.time()) if now_ts is None else now_ts
    if isinstance(now, bool) or not isinstance(now, int) or now <= 0:
        raise ValueError("invalid checkpoint time")
    obs = Path(base_dir) / "observability"
    engine_path = os.getenv("ENGINE_EVENTS_LOG") or str(obs / "engine_events.jsonl")
    dist_path = os.getenv("DIST_EVENTS_LOG") or str(obs / "distribution_events.jsonl")
    fsm_path = os.getenv("FSM_EVENTS_LOG") or str(obs / "fsm_events.jsonl")
    market_path = (
        os.getenv("TRADE_TEMPORAL_TELEMETRY_LOG")
        or str(obs / "trade_temporal_telemetry.jsonl")
    )

    publications = _read_safely(
        lambda: publication_evidence.publication_snapshot(
            path=dist_path, now_ts=now, window_hours=24
        )
    )
    lifecycle = _read_safely(
        lambda: lifecycle_funnel_evidence.build_funnel(
            engine_path=engine_path, distribution_path=dist_path,
            now_ts=now, range_days=1,
        )
    )
    market = _read_safely(
        lambda: market_outcome_evidence.build_market_snapshot(
            path=market_path, now_ts=now, range_days=7, max_segments=_SEGMENT_LIMIT
        )
    )
    focus = _read_safely(
        lambda: focus_history_evidence.build_focus_history(
            path=fsm_path, now_ts=now, range_days=7
        )
    )
    report = compose_checkpoint(
        now_ts=now,
        publications=publications,
        lifecycle=lifecycle,
        market=market,
        focus=focus,
    )
    # R-034: source tail diagnostics are bounded and explicitly PARTIAL when
    # reading only a suffix. They do not change canonical 24h metrics.
    try:
        from scripts.railway_source_tail_diagnostics import collect_source_tails
        report["source_diagnostics"] = collect_source_tails(
            base_dir=Path(base_dir), now_ts=now,
        )
    except Exception:
        report["source_diagnostics"] = {
            "purpose": "BOUNDED_SUFFIX_DIAGNOSTIC_NOT_FULL_WINDOW_STATISTICS",
            "status": "UNKNOWN",
            "reason": "TAIL_INSPECTION_FAILED",
        }

    # Never echo the provider token/config body; only known code identifiers.
    candidate = str(os.getenv("MARKET_DATA_PROVIDER") or "").strip().upper()
    report["configured_provider_from_env"] = (
        candidate if candidate in {"FINNHUB", "TWELVE_DATA"} else "UNKNOWN"
    )
    return report


def emit_checkpoint(*, base_dir: Path, now_ts: int | None = None) -> None:
    """Emit a single sanitized JSON line; failure never changes boot safety."""
    try:
        snapshot = collect_checkpoint(base_dir=base_dir, now_ts=now_ts)
    except Exception:
        now = int(time.time())
        snapshot = {
            "component": "tsp_production_evidence_checkpoint",
            "version": CHECKPOINT_VERSION,
            "checkpoint_utc": _utc(now),
            "scope": "ONE_SHOT_PERSISTED_EVENT_OBSERVATION_AT_STARTUP",
            "status": "UNKNOWN",
            "reason": "CHECKPOINT_COLLECTION_FAILED",
            "live_client_or_broker_acceptance": "NOT_TESTED",
        }
    try:
        print(EVENT_PREFIX + json.dumps(snapshot, sort_keys=True, separators=(",", ":")),
              file=sys.stdout, flush=True)
    except Exception:
        # A diagnostics output failure cannot stop a guarded runtime.
        return
