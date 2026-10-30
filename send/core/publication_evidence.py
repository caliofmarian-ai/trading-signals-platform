"""Bounded, read-only publication-frequency evidence for the Owner research surface.

This is DISTRIBUTION_TRUTH, not market outcome or broker execution truth.
Count unique, canonically identified OPEN_NOW signals that have a primary-v3
PUBLISHED route result. Multiple tier publications of one signal count once.
No historical/legacy event is silently promoted into v3 evidence.
"""

from __future__ import annotations

import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

from core import analytics_engine, event_schema_migration
from core.jsonl_parser import iter_jsonl

DEFAULT_WINDOW_HOURS = 24
MAX_WINDOW_HOURS = 168
MAX_INTERACTIVE_SOURCE_BYTES = 16 * 1024 * 1024

_PUBLISH_RESULTS = frozenset(
    {
        "PUBLISHED",
        "FAILED",
        "SKIPPED_SILENT",
        "SKIPPED_LIMIT",
        "SKIPPED_DISABLED",
        "DUPLICATE_SUPPRESSED",
    }
)


def _utc_iso(ts: int) -> str:
    return datetime.fromtimestamp(int(ts), tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _empty_snapshot(*, hours: int, now: int, reason: str, invalid: int = 0) -> Dict[str, Any]:
    return {
        "status": "UNKNOWN",
        "reason": reason,
        "truth_domain": "DISTRIBUTION_TRUTH",
        "source_identity": "PRIMARY_V3_ROUTE_PUBLISH_RESULT",
        "window_hours": hours,
        "window_start_utc": _utc_iso(now - hours * 3600),
        "window_end_utc": _utc_iso(now),
        "primary_result_rows": 0,
        "unique_open_now_published": None,
        "published_route_rows": None,
        "published_per_hour_rolling_avg": None,
        "max_observed_utc_hour_count": None,
        "deduplicated_publications": None,
        "results": {},
        "invalid_count": invalid,
        "historical_excluded_count": 0,
        "hourly_utc": {},
    }


def publication_snapshot(
    *,
    path: str | None = None,
    now_ts: int | None = None,
    window_hours: int = DEFAULT_WINDOW_HOURS,
) -> Dict[str, Any]:
    """Measure observed canonical route publications, never emitted decisions.

    The rolling window is [now - hours * 3600, now], measured in UTC.
    Historical rows, missing timestamps, invalid records and missing files
    cannot establish a positive or negative production performance claim.
    """
    if isinstance(window_hours, bool) or not isinstance(window_hours, int):
        raise ValueError("window_hours must be an integer")
    if not 1 <= window_hours <= MAX_WINDOW_HOURS:
        raise ValueError("window_hours must be between 1 and 168")
    if now_ts is None:
        now = int(time.time())
    elif isinstance(now_ts, bool) or not isinstance(now_ts, int) or now_ts <= 0:
        raise ValueError("now_ts must be a positive integer")
    else:
        now = now_ts

    start = now - window_hours * 3600
    source_path = path if path is not None else analytics_engine._DIST_LOG
    # Admin Research is an interactive Telegram surface. A large append-only
    # log cannot be scanned synchronously without potentially stalling polling.
    # Refuse an unbounded scan rather than publish a partial-window rate.
    try:
        if Path(source_path).stat().st_size > MAX_INTERACTIVE_SOURCE_BYTES:
            return _empty_snapshot(
                hours=window_hours,
                now=now,
                reason="SOURCE_TOO_LARGE_FOR_INTERACTIVE_SCAN",
            )
    except FileNotFoundError:
        return _empty_snapshot(
            hours=window_hours, now=now, reason="DISTRIBUTION_LOG_NOT_FOUND"
        )
    except OSError:
        return _empty_snapshot(
            hours=window_hours, now=now, reason="DISTRIBUTION_LOG_UNREADABLE"
        )
    results: Counter[str] = Counter()
    first_publication: Dict[str, float] = {}
    primary_rows = 0
    published_rows = 0
    excluded_historical = 0
    invalid = 0

    try:
        for record, error in iter_jsonl(str(source_path)):
            if error is not None:
                invalid += 1
                continue
            if record.get("event_type") == "tier_publish":
                excluded_historical += 1
                continue
            if record.get("event_type") != "route_publish_result":
                continue
            if (
                event_schema_migration.classify_event_identity(record)
                != event_schema_migration.PRIMARY_V3
            ):
                excluded_historical += 1
                continue
            if record.get("stage") != "OPEN_NOW":
                continue
            ts_ms = record.get("ts_epoch_ms")
            if isinstance(ts_ms, bool) or not isinstance(ts_ms, int) or ts_ms <= 0:
                invalid += 1
                continue
            observed_ts = ts_ms / 1000.0
            if observed_ts < start or observed_ts > now:
                continue
            data = record.get("data")
            outcome = data.get("publish_result") if isinstance(data, dict) else None
            if not isinstance(outcome, str) or outcome not in _PUBLISH_RESULTS:
                invalid += 1
                continue
            if outcome == "PUBLISHED":
                signal_id = record.get("signal_id")
                if not isinstance(signal_id, str) or not signal_id.strip():
                    invalid += 1
                    continue
                signal_id = signal_id.strip()
                published_rows += 1
                previous_ts = first_publication.get(signal_id)
                if previous_ts is None or observed_ts < previous_ts:
                    first_publication[signal_id] = observed_ts
            primary_rows += 1
            results[outcome] += 1
    except FileNotFoundError:
        return _empty_snapshot(
            hours=window_hours, now=now, reason="DISTRIBUTION_LOG_NOT_FOUND"
        )
    except OSError:
        return _empty_snapshot(
            hours=window_hours, now=now, reason="DISTRIBUTION_LOG_UNREADABLE"
        )

    if not primary_rows:
        snapshot = _empty_snapshot(
            hours=window_hours,
            now=now,
            reason="NO_PRIMARY_V3_OPEN_NOW_EVIDENCE_IN_WINDOW",
            invalid=invalid,
        )
        snapshot["historical_excluded_count"] = excluded_historical
        return snapshot

    by_hour: Counter[str] = Counter()
    for observed_ts in first_publication.values():
        hour_epoch = int(observed_ts) // 3600 * 3600
        by_hour[_utc_iso(hour_epoch)] += 1

    unique = len(first_publication)
    return {
        "status": "OBSERVED",
        "reason": "BOUNDED_PRIMARY_V3_PUBLICATION_EVIDENCE",
        "truth_domain": "DISTRIBUTION_TRUTH",
        "source_identity": "PRIMARY_V3_ROUTE_PUBLISH_RESULT",
        "window_hours": window_hours,
        "window_start_utc": _utc_iso(start),
        "window_end_utc": _utc_iso(now),
        "primary_result_rows": primary_rows,
        "unique_open_now_published": unique,
        "published_route_rows": published_rows,
        "published_per_hour_rolling_avg": round(unique / window_hours, 2),
        "max_observed_utc_hour_count": max(by_hour.values(), default=0),
        "deduplicated_publications": published_rows - unique,
        "results": {name: results.get(name, 0) for name in sorted(_PUBLISH_RESULTS)},
        "invalid_count": invalid,
        "historical_excluded_count": excluded_historical,
        "hourly_utc": dict(sorted(by_hour.items())),
    }


def render_publication_summary(snapshot: Dict[str, Any]) -> str:
    """Format only aggregate operational evidence, never raw signal/user IDs."""
    hours = snapshot.get("window_hours", DEFAULT_WINDOW_HOURS)
    lines = [
        f"Observed OPEN_NOW Publications — trailing {hours}h UTC",
        f"Evidence: {snapshot.get('status', 'UNKNOWN')}",
        f"Window: {snapshot.get('window_start_utc', 'UNKNOWN')} to {snapshot.get('window_end_utc', 'UNKNOWN')}",
    ]
    if snapshot.get("status") != "OBSERVED":
        lines.extend(
            [
                f"Reason: {snapshot.get('reason', 'UNKNOWN')}",
                "Signals/hour: UNKNOWN — not zero.",
            ]
        )
    else:
        results = snapshot.get("results") or {}
        lines.extend(
            [
                f"Unique signals published: {snapshot['unique_open_now_published']}",
                f"Observed rolling average per hour: {snapshot['published_per_hour_rolling_avg']}",
                f"Route PUBLISHED events: {snapshot['published_route_rows']}",
                f"Additional tier publications suppressed: {snapshot['deduplicated_publications']}",
                f"FAILED route results: {results.get('FAILED', 0)}",
            ]
        )
    invalid = snapshot.get("invalid_count", 0)
    historical = snapshot.get("historical_excluded_count", 0)
    if invalid or historical:
        lines.append(
            f"Evidence quality: invalid rows {invalid}; historical excluded {historical}"
        )
    lines.extend(
        [
            "Published route truth only; delivery/client execution is not inferred.",
            "Market WIN/LOSS and win-rate require separate finalized MARKET_TRUTH.",
        ]
    )
    return "\n".join(lines)
