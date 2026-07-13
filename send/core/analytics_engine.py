# send/core/analytics_engine.py
# BinaryBot — Analytics Engine (performance & research)
#
# Canonical input rules (BATCH-07):
# - Consumes outcome records produced by outcome_service (BATCH-04).
# - Consumes distribution events (tier_publish) produced by distribution_router (BATCH-03).
# - All JSONL parsing uses core.jsonl_parser — malformed records are never
#   silently converted to empty valid structures.
# - Invalid records are excluded from metrics and counted separately.
# - Duplicate outcome records (same signal_id + user_id) do not inflate counts.
# - Empty input produces a deterministic no-data result.
# - Analytics does not mutate live trading state or strategy parameters.
# - Report writes use storage.save_json_atomic (atomic, preserves last valid report).
# - Paths are read from environment variables with the same pattern as
#   observability_logger.py; the hardcoded /opt/binarybot/ prefix is not required.

from __future__ import annotations

import hashlib
import os
from typing import Any, Dict, List, Optional

from core import storage
from core.jsonl_parser import iter_jsonl, ParseError

# ---------------------------------------------------------------------------
# Canonical path resolution (env-var overridable, no /opt/binarybot/ required)
# ---------------------------------------------------------------------------
_OBS_DIR = os.getenv("OBS_DIR", "/opt/binarybot/observability")
_OUTCOMES_LOG = os.getenv("OUTCOMES_LOG", os.path.join("/opt/binarybot/outcomes", "outcomes.jsonl"))
_DIST_LOG = os.getenv("DIST_EVENTS_LOG", os.path.join(_OBS_DIR, "distribution_events.jsonl"))

_ANALYTICS_BASE = os.getenv("ANALYTICS_DIR", "/opt/binarybot/analytics")
AGGREGATES_PATH = os.path.join(_ANALYTICS_BASE, "aggregates.json")

# Outcome record fields (canonical shape from outcome_service._build_vote_record)
_ALLOWED_OUTCOMES = {"WIN", "LOSE", "MISSED"}

# Distribution publish_result values (canonical from event_schema.json / BATCH-03)
_DIST_RESULTS = {"PUBLISHED", "FAILED", "SKIPPED_SILENT", "SKIPPED_LIMIT",
                 "SKIPPED_DISABLED", "DUPLICATE_SUPPRESSED"}

# Minimum sample size below which win_rate is marked insufficient
_MIN_SAMPLE_FOR_RATE = 5


def _member_ref_for_user(user_id: int) -> Optional[str]:
    salt = os.getenv("COMMUNITY_FEEDBACK_SALT", "").strip()
    if not salt:
        return None
    digest = hashlib.sha256(f"{int(user_id)}:{salt}".encode("utf-8")).hexdigest().upper()
    return f"M-{digest[:8]}"


def _load_outcomes(path: str) -> Dict[str, Any]:
    """
    Load and deduplicate outcome records.

    Deduplication key: (signal_id, user_id) — one outcome per voter per signal.
    Returns a summary dict with counts and invalid_records list.
    """
    wins = 0
    loses = 0
    missed = 0
    invalid_records: List[Dict[str, Any]] = []
    seen: set = set()  # (signal_id, user_id) dedup set

    try:
        for record, err in iter_jsonl(path):
            if err is not None:
                invalid_records.append(err.to_dict())
                continue

            signal_id = record.get("signal_id")
            outcome = record.get("outcome")
            user_id = record.get("user_id")

            # Required field validation
            if not signal_id or not outcome:
                invalid_records.append({
                    "source_path": path,
                    "message": "missing required field signal_id or outcome",
                    "raw_prefix": str(record)[:200],
                })
                continue

            # Unknown outcome classification (not silently coerced)
            if outcome not in _ALLOWED_OUTCOMES:
                invalid_records.append({
                    "source_path": path,
                    "message": f"unsupported outcome value: {outcome!r}",
                    "raw_prefix": str(record)[:200],
                })
                continue

            # Deduplication: one vote per (signal_id, user_id)
            dedup_key = (str(signal_id), str(user_id) if user_id is not None else None)
            if dedup_key in seen:
                continue
            seen.add(dedup_key)

            if outcome == "WIN":
                wins += 1
            elif outcome == "LOSE":
                loses += 1
            elif outcome == "MISSED":
                missed += 1

    except FileNotFoundError:
        return {
            "no_data": True,
            "reason": "outcomes_file_not_found",
            "path": path,
            "wins": 0,
            "loses": 0,
            "missed": 0,
            "total": 0,
            "invalid_records": [],
        }

    total = wins + loses + missed
    result: Dict[str, Any] = {
        "no_data": total == 0,
        "wins": wins,
        "loses": loses,
        "missed": missed,
        "total": total,
        "invalid_records": invalid_records,
        "invalid_count": len(invalid_records),
    }
    if total > 0:
        if total >= _MIN_SAMPLE_FOR_RATE:
            result["win_rate"] = round(wins / total * 100, 2)
            result["insufficient_sample"] = False
        else:
            result["win_rate"] = None
            result["insufficient_sample"] = True
            result["insufficient_sample_note"] = (
                f"win_rate not computed: only {total} records (min {_MIN_SAMPLE_FOR_RATE})"
            )
    else:
        result["win_rate"] = None
    return result


def _load_distribution_metrics(path: str) -> Dict[str, Any]:
    """
    Aggregate distribution metrics from tier_publish events (BATCH-03 canonical shape).

    Counts: PUBLISHED, FAILED, SKIPPED_*, DUPLICATE_SUPPRESSED.
    """
    counts: Dict[str, int] = {k: 0 for k in _DIST_RESULTS}
    invalid_count = 0

    try:
        for record, err in iter_jsonl(path):
            if err is not None:
                invalid_count += 1
                continue
            if record.get("event_type") != "tier_publish":
                continue
            result = (record.get("data") or {}).get("publish_result")
            if result in counts:
                counts[result] += 1
            elif result is not None:
                invalid_count += 1
    except FileNotFoundError:
        return {
            "no_data": True,
            "reason": "distribution_log_not_found",
            "path": path,
            **{k: 0 for k in _DIST_RESULTS},
            "invalid_count": 0,
        }

    total = sum(counts.values())
    return {
        "no_data": total == 0,
        **counts,
        "total_distribution_events": total,
        "invalid_count": invalid_count,
    }


def recompute(now_ts: int) -> Dict[str, Any]:
    """
    Recompute aggregate analytics from canonical outcome and distribution records.

    - Deduplicates outcomes by (signal_id, user_id).
    - Reports invalid records explicitly.
    - Produces a deterministic no-data result when inputs are empty.
    - Writes result atomically via storage.save_json_atomic.
    - Does not mutate live trading state.
    """
    outcome_stats = _load_outcomes(_OUTCOMES_LOG)
    dist_metrics = _load_distribution_metrics(_DIST_LOG)

    # Count distinct signals with at least one valid outcome
    signal_set: set = set()
    try:
        for record, err in iter_jsonl(_OUTCOMES_LOG):
            if err is None and record.get("signal_id") and record.get("outcome") in _ALLOWED_OUTCOMES:
                signal_set.add(str(record["signal_id"]))
    except FileNotFoundError:
        pass

    aggregates: Dict[str, Any] = {
        "updated_ts": now_ts,
        "no_data": outcome_stats["no_data"],
        "wins": outcome_stats["wins"],
        "loses": outcome_stats["loses"],
        "missed": outcome_stats["missed"],
        "total_votes": outcome_stats["total"],
        "win_rate": outcome_stats.get("win_rate"),
        "insufficient_sample": outcome_stats.get("insufficient_sample", False),
        "signals_tracked": len(signal_set),
        "invalid_outcome_records": outcome_stats["invalid_count"],
        "distribution": dist_metrics,
    }

    storage.save_json_atomic(AGGREGATES_PATH, aggregates)
    return aggregates


def get_symbol_ranking(range_days: int) -> List[Dict[str, Any]]:
    # placeholder for future symbol ranking logic
    return []


def get_focus_history(range_days: int) -> Dict[str, Any]:
    # placeholder
    return {}


def get_funnel(range_days: int) -> Dict[str, Any]:
    # placeholder
    return {}


def get_user_stats(user_id: int, range_days: int) -> Dict[str, Any]:
    wins = 0
    loses = 0
    missed = 0
    invalid_count = 0
    member_ref = _member_ref_for_user(user_id)
    seen: set = set()

    try:
        for record, err in iter_jsonl(_OUTCOMES_LOG):
            if err is not None:
                invalid_count += 1
                continue

            uid = record.get("user_id")
            if uid not in {user_id, member_ref}:
                # Try int comparison for string-encoded user IDs
                try:
                    if int(uid) != int(user_id):
                        continue
                except (TypeError, ValueError):
                    continue

            outcome = record.get("outcome")
            signal_id = record.get("signal_id")
            if not signal_id or outcome not in _ALLOWED_OUTCOMES:
                invalid_count += 1
                continue

            dedup_key = (str(signal_id), str(uid))
            if dedup_key in seen:
                continue
            seen.add(dedup_key)

            if outcome == "WIN":
                wins += 1
            elif outcome == "LOSE":
                loses += 1
            elif outcome == "MISSED":
                missed += 1

    except FileNotFoundError:
        return {
            "no_data": True,
            "reason": "outcomes_file_not_found",
            "wins": 0,
            "loses": 0,
            "missed": 0,
            "total": 0,
        }

    total = wins + loses + missed

    if total == 0:
        return {
            "no_data": True,
            "wins": 0,
            "loses": 0,
            "missed": 0,
            "total": 0,
            "invalid_count": invalid_count,
        }

    result: Dict[str, Any] = {
        "no_data": False,
        "wins": wins,
        "loses": loses,
        "missed": missed,
        "total": total,
        "invalid_count": invalid_count,
    }
    if total >= _MIN_SAMPLE_FOR_RATE:
        result["win_rate"] = round(wins / total * 100, 2)
        result["insufficient_sample"] = False
    else:
        result["win_rate"] = None
        result["insufficient_sample"] = True
    return result