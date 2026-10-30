"""Historical *observations* of FSM focus/watchlist transitions (read only).

Authority: active FSM + Event Schema v3. Uses the existing fsm_transition
event sink, not mutable focus_state.json, broker outcomes or legacy
focus_history.jsonl. A replacement event describes the entering symbol but
not the evicted one: missing victim exits are deliberately NOT inferred.
"""

from __future__ import annotations

import os
import re
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from statistics import median
from typing import Any, Dict, Mapping

from core import event_schema_migration, storage
from core.jsonl_parser import iter_jsonl


MAX_WINDOW_DAYS = 30
MAX_INTERACTIVE_BYTES = 16 * 1024 * 1024
MAX_DISPLAY_EVENTS = 6
_SYMBOL = re.compile(r"^[A-Z0-9/_-]{2,24}$")

_ENTRIES = frozenset({"watchlist_added", "watchlist_replaced"})
_REFRESH = "watchlist_refreshed"
_EXITS = {
    "focus_lease_expired": "COOLDOWN",
    "focus_evicted_inactive": "IDLE",
    "reject_released": "COOLDOWN",
    "open_now_completed": "COOLDOWN",
}
_FOCUS_TRIGGERS = _ENTRIES | frozenset({_REFRESH}) | frozenset(_EXITS)


def _utc(epoch_seconds: int | float) -> str:
    return datetime.fromtimestamp(float(epoch_seconds), timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )


def _source_path() -> str:
    # The actual fsm_transition event schema routes into the FSM event sink,
    # not the engine or the historical deprecated focus_history file.
    return (
        os.getenv("FSM_EVENTS_LOG")
        or str(
            Path(os.getenv("OBS_DIR") or storage.root_path("observability"))
            / "fsm_events.jsonl"
        )
    )


def _empty(*, start: int, now: int, reason: str, quality: Mapping[str, int] | None = None) -> Dict[str, Any]:
    return {
        "status": "UNKNOWN",
        "reason": reason,
        "truth_domain": "FSM_OPERATIONAL_TRUTH",
        "source": "PRIMARY_V3_FSM_TRANSITION",
        "window_start_utc": _utc(start),
        "window_end_utc": _utc(now),
        "focus_event_count": None,
        "focus_entries": None,
        "focus_exits": None,
        "focus_refreshes": None,
        "replacement_entries_without_victim_exit": None,
        "paired_explicit_entry_exit_count": None,
        "median_observed_focus_seconds": None,
        "unmatched_entry_count": None,
        "unmatched_exit_count": None,
        "ambiguous_reentry_count": None,
        "history_coverage": "NOT_VERIFIED",
        "recent_events": [],
        "quality": dict(quality or {}),
    }


def build_focus_history(
    *,
    range_days: int = 7,
    now_ts: int | None = None,
    path: str | None = None,
) -> Dict[str, Any]:
    """Observe confirmed FSM focus transitions, without rewriting FSM history.

    A window-scoped entry and explicit exit for the same symbol support only
    that observed duration. Missing entry/exit, replacement victim identity,
    log gaps and events before the window remain unknown.
    """
    if (
        isinstance(range_days, bool)
        or not isinstance(range_days, int)
        or not 1 <= range_days <= MAX_WINDOW_DAYS
    ):
        raise ValueError("range_days must be an integer between 1 and 30")
    if now_ts is None:
        now = int(time.time())
    elif isinstance(now_ts, bool) or not isinstance(now_ts, int) or now_ts <= 0:
        raise ValueError("now_ts must be a positive integer")
    else:
        now = now_ts
    start = now - 86400 * range_days
    source = path if path is not None else _source_path()
    quality = Counter(
        {
            "invalid_rows": 0,
            "historical_excluded": 0,
            "out_of_window": 0,
            "duplicate_event_ids": 0,
            "primary_fsm_rows": 0,
            "unsupported_focus_transitions": 0,
        }
    )
    try:
        if Path(source).stat().st_size > MAX_INTERACTIVE_BYTES:
            return _empty(start=start, now=now, reason="SOURCE_TOO_LARGE_FOR_INTERACTIVE_SCAN")
    except FileNotFoundError:
        return _empty(start=start, now=now, reason="FSM_EVENT_LOG_NOT_FOUND")
    except OSError:
        return _empty(start=start, now=now, reason="FSM_EVENT_LOG_UNREADABLE")

    events: list[tuple[int, int, str, str, str]] = []
    # A replay of a different event under an identical event_id cannot count as
    # independent evidence. It also invalidates the entire derived history.
    seen: dict[str, tuple[Any, ...]] = {}
    try:
        for row_index, (row, error) in enumerate(iter_jsonl(str(source))):
            if error is not None:
                quality["invalid_rows"] += 1
                continue
            if row.get("event_type") != "fsm_transition":
                continue
            if (
                event_schema_migration.classify_event_identity(row)
                != event_schema_migration.PRIMARY_V3
            ):
                quality["historical_excluded"] += 1
                continue
            event_id = row.get("event_id")
            timestamp_ms = row.get("ts_epoch_ms")
            data = row.get("data")
            if (
                not isinstance(event_id, str)
                or not event_id.strip()
                or isinstance(timestamp_ms, bool)
                or not isinstance(timestamp_ms, int)
                or timestamp_ms <= 0
                or not isinstance(data, dict)
            ):
                quality["invalid_rows"] += 1
                continue
            if timestamp_ms < start * 1000 or timestamp_ms > now * 1000:
                quality["out_of_window"] += 1
                continue
            symbol = data.get("symbol")
            trigger = data.get("trigger")
            prior_state = data.get("prev_state")
            new_state = data.get("new_state")
            if (
                not isinstance(symbol, str)
                or not _SYMBOL.fullmatch(symbol)
                or not isinstance(trigger, str)
                or not isinstance(prior_state, str)
                or not isinstance(new_state, str)
            ):
                quality["invalid_rows"] += 1
                continue
            if row.get("symbol") is not None and row["symbol"] != symbol:
                quality["invalid_rows"] += 1
                continue
            signature = (
                timestamp_ms, symbol, trigger, prior_state, new_state,
                data.get("signal_id"), data.get("candle_ts"),
            )
            eid = event_id.strip()
            if eid in seen:
                if signature != seen[eid]:
                    return _empty(
                        start=start,
                        now=now,
                        reason="CONFLICTING_FSM_EVENT_ID",
                        quality=quality,
                    )
                quality["duplicate_event_ids"] += 1
                continue
            seen[eid] = signature
            quality["primary_fsm_rows"] += 1
            if trigger not in _FOCUS_TRIGGERS:
                continue
            valid = (
                trigger in _ENTRIES and new_state == "WATCHLIST"
            ) or (
                trigger == _REFRESH and new_state == "WATCHLIST"
            ) or (
                trigger in _EXITS
                and new_state == _EXITS[trigger]
                and prior_state in {"WATCHLIST", "CONFIRMED", "LIVE_SENT"}
            )
            if not valid:
                quality["unsupported_focus_transitions"] += 1
                continue
            events.append((timestamp_ms, row_index, symbol, trigger, new_state))
    except OSError:
        return _empty(
            start=start, now=now, reason="FSM_EVENT_LOG_READ_INTERRUPTED",
            quality=quality,
        )

    if not events:
        return _empty(
            start=start,
            now=now,
            reason="NO_VALID_PRIMARY_V3_FOCUS_EVENTS_IN_WINDOW",
            quality=quality,
        )
    events.sort(key=lambda row: (row[0], row[1]))
    active: dict[str, int] = {}
    entries = exits = refreshes = replacements = orphan_exits = reentries = 0
    durations: list[float] = []
    recent: list[Dict[str, str]] = []

    for ts_ms, _index, symbol, trigger, _new_state in events:
        if trigger in _ENTRIES:
            entries += 1
            if trigger == "watchlist_replaced":
                # Incoming symbol is known; evicted victim is NOT recorded.
                replacements += 1
            if symbol in active:
                # Two enters without a recorded exit are ambiguous; do not
                # synthesize a dwell interval from either of them.
                active.pop(symbol)
                reentries += 1
            else:
                active[symbol] = ts_ms
            action = "ENTER"
        elif trigger == _REFRESH:
            refreshes += 1
            action = "REFRESH"
        else:
            exits += 1
            action = "EXIT"
            entered = active.pop(symbol, None)
            if entered is None or ts_ms < entered:
                orphan_exits += 1
            else:
                durations.append((ts_ms - entered) / 1000.0)
        recent.append(
            {"at_utc": _utc(ts_ms / 1000.0), "symbol": symbol, "action": action,
             "trigger": trigger}
        )

    return {
        "status": "OBSERVED",
        "reason": "BOUNDED_PRIMARY_V3_FSM_FOCUS_EVIDENCE",
        "truth_domain": "FSM_OPERATIONAL_TRUTH",
        "source": "PRIMARY_V3_FSM_TRANSITION",
        "window_start_utc": _utc(start),
        "window_end_utc": _utc(now),
        "focus_event_count": len(events),
        "focus_entries": entries,
        "focus_exits": exits,
        "focus_refreshes": refreshes,
        "replacement_entries_without_victim_exit": replacements,
        "paired_explicit_entry_exit_count": len(durations),
        "median_observed_focus_seconds": (
            round(float(median(durations)), 2) if durations else None
        ),
        "unmatched_entry_count": len(active),
        "unmatched_exit_count": orphan_exits,
        "ambiguous_reentry_count": reentries,
        "history_coverage": "PARTIAL_EXPLICIT_FSM_EVENTS_ONLY",
        "recent_events": recent[-MAX_DISPLAY_EVENTS:],
        "recent_events_truncated": len(recent) > MAX_DISPLAY_EVENTS,
        "quality": dict(quality),
    }


def render_focus_history(snapshot: Mapping[str, Any]) -> str:
    """Compact authorized Research text; never disclose raw signal IDs."""
    lines = [
        "FSM Focus / Watchlist History — read only",
        f"Evidence: {snapshot.get('status', 'UNKNOWN')}",
        f"Window: {snapshot.get('window_start_utc', 'UNKNOWN')} to {snapshot.get('window_end_utc', 'UNKNOWN')}",
    ]
    if snapshot.get("status") != "OBSERVED":
        lines.extend(
            [
                f"Reason: {snapshot.get('reason', 'UNKNOWN')}",
                "Focus history: UNKNOWN — not zero.",
            ]
        )
    else:
        median_seconds = snapshot.get("median_observed_focus_seconds")
        lines.extend(
            [
                f"Entries / exits / refreshes: {snapshot['focus_entries']} / {snapshot['focus_exits']} / {snapshot['focus_refreshes']}",
                f"Explicit entry-to-exit pairs: {snapshot['paired_explicit_entry_exit_count']}",
                "Observed median dwell: " + (
                    "UNKNOWN" if median_seconds is None else f"{median_seconds}s"
                ),
                f"Replacement victim exits missing: {snapshot['replacement_entries_without_victim_exit']}",
                f"Unmatched entry / exit: {snapshot['unmatched_entry_count']} / {snapshot['unmatched_exit_count']}",
            ]
        )
        for item in list(snapshot.get("recent_events") or [])[-3:]:
            lines.append(f"- {item['at_utc']}: {item['symbol']} {item['action']}")
        if snapshot.get("recent_events_truncated"):
            lines.append("Only recent events displayed.")
    quality = snapshot.get("quality") or {}
    if quality.get("invalid_rows") or quality.get("historical_excluded"):
        lines.append(
            f"Quality: invalid {quality.get('invalid_rows', 0)}, "
            f"historical excluded {quality.get('historical_excluded', 0)}"
        )
    lines.append(
        "Observed FSM transitions only; missing victims, past entries and live membership are not inferred."
    )
    return "\n".join(lines)
