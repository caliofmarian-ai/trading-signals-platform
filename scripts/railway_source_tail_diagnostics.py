"""Read-only bounded suffix inspection of Railway persisted observability logs.

NOT a complete 24h report. Every partial sample explicitly says SUFFIX_ONLY.
Never retain or expose raw signals, prices, chat IDs, user IDs, filesystem
paths, message text, or source records. Designed for a one-shot startup probe.
"""

from __future__ import annotations

import json
import math
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

TAIL_BYTES = 512 * 1024
_SOURCE_NAMES = ("engine", "distribution", "fsm", "market")
_LEGACY_COMPAT_EVENT_TYPES = frozenset({
    "decision", "signal_event", "tier_publish", "tier_reset", "signal_emitted",
})
_EVENT_TYPES = {
    "engine": frozenset({"decision_evaluated", "signal_execution_result"}),
    "distribution": frozenset({"route_publish_result", "signal_stage_visible"}),
    "fsm": frozenset({"fsm_transition"}),
    "market": frozenset(),
}


def _utc(seconds: int | float) -> str:
    return datetime.fromtimestamp(float(seconds), timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )


def _epoch(value: Any) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    result = float(value)
    return result if math.isfinite(result) and result > 0 else None


def _unknown(reason: str) -> dict[str, Any]:
    return {
        "status": reason,
        "coverage": "NONE",
        "size_mib": None,
        "over_16_mib": None,
        "tail_read_bytes": 0,
        "tail_json_objects": None,
        "tail_primary_v3_header_rows": None,
        "tail_target_family_rows": None,
        "tail_utc_24h_header_rows": None,
        "tail_open_now_published_route_rows": None,
        "last_event_utc": None,
        "last_target_event_utc": None,
        "invalid_tail_rows": None,
    }


def inspect_source(*, source: str, path: str | Path, now_ts: int) -> dict[str, Any]:
    """Inspect at most 512 KiB; raw source content never reaches the return."""
    if source not in _SOURCE_NAMES:
        raise ValueError("unknown source family")
    if isinstance(now_ts, bool) or not isinstance(now_ts, int) or now_ts <= 0:
        raise ValueError("invalid observation time")
    try:
        with open(path, "rb") as handle:
            first = os.fstat(handle.fileno())
            size = first.st_size
            if size == 0:
                info = _unknown("EMPTY_FILE")
                info.update(coverage="FULL_FILE", size_mib=0, over_16_mib=False,
                            tail_json_objects=0, tail_primary_v3_header_rows=0,
                            tail_target_family_rows=0, tail_utc_24h_header_rows=0,
                            tail_open_now_published_route_rows=0, invalid_tail_rows=0)
                return info
            width = min(size, TAIL_BYTES)
            start = size - width
            handle.seek(start)
            tail = handle.read(width)
            second = os.fstat(handle.fileno())
            if (
                first.st_size != second.st_size
                or first.st_ino != second.st_ino
                or first.st_mtime_ns != second.st_mtime_ns
                or len(tail) != width
            ):
                return _unknown("FILE_CHANGED_DURING_READ")
    except FileNotFoundError:
        return _unknown("FILE_NOT_FOUND")
    except OSError:
        return _unknown("FILE_UNREADABLE")

    coverage = "FULL_FILE" if start == 0 else "SUFFIX_ONLY"
    if start > 0:
        # The first bytes may belong to the middle of an event. Exclude it.
        newline = tail.find(b"\n")
        if newline < 0:
            info = _unknown("NO_COMPLETE_ROW_IN_BOUNDED_SUFFIX")
            info.update(
                coverage=coverage,
                size_mib=round(size / (1024 * 1024), 2),
                over_16_mib=size > 16 * 1024 * 1024,
                tail_read_bytes=width,
            )
            return info
        tail = tail[newline + 1:]
        if not tail.strip():
            info = _unknown("NO_COMPLETE_ROW_IN_BOUNDED_SUFFIX")
            info.update(
                coverage=coverage,
                size_mib=round(size / (1024 * 1024), 2),
                over_16_mib=size > 16 * 1024 * 1024,
                tail_read_bytes=width,
            )
            return info

    incomplete_last_line = bool(tail and not tail.endswith(b"\n"))
    lines = tail.split(b"\n")
    if incomplete_last_line:
        # Concurrent incomplete writes or a truncated log cannot become truth.
        lines = lines[:-1]

    parsed = invalid = header_v3 = target_rows = recent = route_published = 0
    last_ts: float | None = None
    last_target_ts: float | None = None
    for raw in lines:
        if not raw.strip():
            continue
        try:
            row = json.loads(raw.decode("utf-8"))
        except (UnicodeError, ValueError):
            invalid += 1
            continue
        if not isinstance(row, dict):
            invalid += 1
            continue
        parsed += 1
        if source == "market":
            # Market truth has a different, separately governed schema.
            is_target = (
                row.get("truth_domain") == "MARKET_TRUTH"
                and row.get("telemetry_version") == "3.0.0"
                and row.get("telemetry_status") == "FINALIZED"
            )
            if is_target:
                target_rows += 1
            ts = _epoch(row.get("finalized_ts"))
        else:
            event_type = row.get("event_type")
            is_primary = (
                row.get("schema_version") == "3.0.0"
                and isinstance(event_type, str)
                and bool(event_type)
                and event_type not in _LEGACY_COMPAT_EVENT_TYPES
            )
            if is_primary:
                # Header classification, NOT full canonical event validation.
                header_v3 += 1
            is_target = is_primary and event_type in _EVENT_TYPES[source]
            if is_target:
                target_rows += 1
                if (
                    source == "distribution"
                    and event_type == "route_publish_result"
                    and row.get("stage") == "OPEN_NOW"
                    and isinstance(row.get("data"), dict)
                    and row["data"].get("publish_result") == "PUBLISHED"
                ):
                    # Route rows, NOT distinct trade/signal identities.
                    route_published += 1
            ms = _epoch(row.get("ts_epoch_ms"))
            ts = ms / 1000.0 if ms is not None else None

        if ts is not None and ts <= now_ts + 300:
            last_ts = ts if last_ts is None else max(last_ts, ts)
            if is_target:
                last_target_ts = ts if last_target_ts is None else max(last_target_ts, ts)
            if now_ts - 86400 <= ts <= now_ts and is_target:
                recent += 1

    return {
        "status": "OBSERVED_TAIL" if parsed else "NO_VALID_JSON_OBJECT_IN_TAIL",
        "coverage": coverage,
        "size_mib": round(size / (1024 * 1024), 2),
        "over_16_mib": size > 16 * 1024 * 1024,
        "tail_read_bytes": width,
        "tail_json_objects": parsed,
        "tail_primary_v3_header_rows": (
            header_v3 if source != "market" else None
        ),
        "tail_target_family_rows": target_rows,
        "tail_utc_24h_header_rows": recent,
        "tail_open_now_published_route_rows": (
            route_published if source == "distribution" else None
        ),
        "last_event_utc": _utc(last_ts) if last_ts is not None else None,
        "last_target_event_utc": (
            _utc(last_target_ts) if last_target_ts is not None else None
        ),
        "invalid_tail_rows": invalid + int(incomplete_last_line),
    }


def collect_source_tails(*, base_dir: Path, now_ts: int) -> dict[str, Any]:
    """Inspect exactly the four known sources, never print resolved file paths."""
    root = Path(base_dir) / "observability"
    names = {
        "engine": (
            "ENGINE_EVENTS_LOG", root / "engine_events.jsonl"
        ),
        "distribution": (
            "DIST_EVENTS_LOG", root / "distribution_events.jsonl"
        ),
        "fsm": (
            "FSM_EVENTS_LOG", root / "fsm_events.jsonl"
        ),
        "market": (
            "TRADE_TEMPORAL_TELEMETRY_LOG",
            root / "trade_temporal_telemetry.jsonl",
        ),
    }
    output = {}
    for name, (env_name, default) in names.items():
        try:
            path = os.getenv(env_name) or str(default)
            output[name] = inspect_source(
                source=name, path=path, now_ts=now_ts,
            )
        except Exception:
            output[name] = _unknown("INSPECTION_FAILED")
    return {
        "purpose": "BOUNDED_SUFFIX_DIAGNOSTIC_NOT_FULL_WINDOW_STATISTICS",
        "source_tails": output,
    }
