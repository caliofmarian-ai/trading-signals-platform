# send/intelligence/research_engine.py
# BinaryBot — Research Engine (signal lifecycle analytics)
#
# Canonical input rules (BATCH-07):
# - Consumes engine_events.jsonl (signal_event, decision) and
#   distribution_events.jsonl (tier_publish) produced by BATCH-03/04.
# - Consumes outcome records from outcomes.jsonl produced by BATCH-04.
# - All JSONL parsing uses core.jsonl_parser — malformed records are never
#   silently converted to empty structures.
# - Invalid records are excluded and counted.
# - Outputs are advisory only — research does not mutate live parameters
#   or auto-promote strategies.
# - Paths are env-var overridable; /opt/binarybot/ prefix is not required.
#
# Signal event field layout (canonical after observability normalization):
#   event_type, event_id, schema_version, ts_utc, ts_epoch_ms, ...envelope...
#   stage          (top-level correlation field, NOT inside data)
#   signal_id      (top-level correlation field)
#   symbol         (top-level correlation field)
#   data.direction, data.score_total, ...

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

from core import storage
from core.jsonl_parser import iter_jsonl

# ---------------------------------------------------------------------------
# Canonical path resolution (env-var overridable)
# ---------------------------------------------------------------------------
_OBS_DIR = os.getenv("OBS_DIR", "/opt/binarybot/observability")
_OUTCOMES_LOG = os.getenv("OUTCOMES_LOG", os.path.join("/opt/binarybot/outcomes", "outcomes.jsonl"))
_ENGINE_LOG = os.getenv("ENGINE_EVENTS_LOG", os.path.join(_OBS_DIR, "engine_events.jsonl"))
_DIST_LOG = os.getenv("DIST_EVENTS_LOG", os.path.join(_OBS_DIR, "distribution_events.jsonl"))

_ANALYTICS_BASE = os.getenv("ANALYTICS_DIR", "/opt/binarybot/analytics")
_RESEARCH_REPORT_PATH = os.path.join(_ANALYTICS_BASE, "research_report.json")

_ALLOWED_OUTCOMES = {"WIN", "LOSE", "MISSED"}
_ALLOWED_STAGES = {"PRE", "CONFIRM", "OPEN_NOW"}
# Known signal_event stages per canonical EVENT_SCHEMA_SPEC v2.0.0
# Unsupported stage values are classified explicitly, not silently coerced.
_KNOWN_UNSUPPORTED_STAGES: frozenset = frozenset()

_DIST_RESULTS = {"PUBLISHED", "FAILED", "SKIPPED_SILENT", "SKIPPED_LIMIT",
                 "SKIPPED_DISABLED", "DUPLICATE_SUPPRESSED"}


def _classify_stage(stage: Optional[str]) -> str:
    """Classify a stage value as supported, unsupported, or missing."""
    if stage is None:
        return "MISSING"
    if stage in _ALLOWED_STAGES:
        return "SUPPORTED"
    return "UNSUPPORTED"


def compute_signal_funnel() -> Dict[str, Any]:
    """
    Count signal_event records by stage (PRE / CONFIRM / OPEN_NOW).

    Stage is a top-level correlation field in canonical events, not inside data.
    Unknown stage values are counted separately and not coerced.
    """
    counts: Dict[str, int] = {"PRE": 0, "CONFIRM": 0, "OPEN_NOW": 0}
    unsupported_stages: Dict[str, int] = {}
    invalid_count = 0
    seen_event_ids: set = set()

    try:
        for record, err in iter_jsonl(_ENGINE_LOG):
            if err is not None:
                invalid_count += 1
                continue
            if record.get("event_type") != "signal_event":
                continue

            # Dedup by event_id where available
            event_id = record.get("event_id")
            if event_id and event_id in seen_event_ids:
                continue
            if event_id:
                seen_event_ids.add(event_id)

            # stage is a top-level correlation field (BATCH-03/BATCH-06 schema)
            stage = record.get("stage")
            classification = _classify_stage(stage)
            if classification == "SUPPORTED":
                counts[stage] += 1  # type: ignore[index]
            elif classification == "UNSUPPORTED":
                unsupported_stages[str(stage)] = unsupported_stages.get(str(stage), 0) + 1
            # MISSING stage → excluded silently (counted as invalid)
            elif classification == "MISSING":
                invalid_count += 1

    except FileNotFoundError:
        return {
            "no_data": True,
            "reason": "engine_log_not_found",
            "path": _ENGINE_LOG,
            "PRE": 0,
            "CONFIRM": 0,
            "OPEN_NOW": 0,
            "invalid_count": 0,
            "unsupported_stages": {},
        }

    total = sum(counts.values())
    return {
        "no_data": total == 0,
        **counts,
        "total_signal_events": total,
        "invalid_count": invalid_count,
        "unsupported_stages": unsupported_stages,
    }


def compute_outcome_stats() -> Dict[str, Any]:
    """
    Count outcome records (WIN / LOSE / MISSED).

    Deduplicates by (signal_id, user_id); does not inflate counts on duplicates.
    """
    wins = 0
    loses = 0
    missed = 0
    invalid_count = 0
    seen: set = set()

    try:
        for record, err in iter_jsonl(_OUTCOMES_LOG):
            if err is not None:
                invalid_count += 1
                continue

            outcome = record.get("outcome")
            signal_id = record.get("signal_id")
            user_id = record.get("user_id")

            if not signal_id or outcome not in _ALLOWED_OUTCOMES:
                invalid_count += 1
                continue

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
            "wins": 0,
            "loses": 0,
            "missed": 0,
            "win_rate": None,
            "invalid_count": 0,
        }

    total = wins + loses + missed
    if total == 0:
        return {
            "no_data": True,
            "wins": 0,
            "loses": 0,
            "missed": 0,
            "win_rate": None,
            "invalid_count": invalid_count,
        }

    return {
        "no_data": False,
        "wins": wins,
        "loses": loses,
        "missed": missed,
        "win_rate": round(wins / total * 100, 2),
        "invalid_count": invalid_count,
    }


def compute_distribution_summary() -> Dict[str, Any]:
    """
    Summarise distribution tier_publish event outcomes.

    Counts PUBLISHED, FAILED, SKIPPED_*, DUPLICATE_SUPPRESSED separately.
    """
    counts: Dict[str, int] = {k: 0 for k in _DIST_RESULTS}
    invalid_count = 0

    try:
        for record, err in iter_jsonl(_DIST_LOG):
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


def build_research_report() -> Dict[str, Any]:
    """
    Build a research report from validated canonical source records.

    Output contract:
    - All findings are advisory only.
    - Recommendations must not be applied automatically.
    - Insufficient evidence is reported explicitly, not fabricated.
    - Observations, hypotheses, and recommendations are distinguished.
    """
    funnel = compute_signal_funnel()
    outcomes = compute_outcome_stats()
    distribution = compute_distribution_summary()

    observations: List[str] = []
    hypotheses: List[str] = []
    recommendations: List[str] = []
    limitations: List[str] = []

    # Observations
    if funnel.get("no_data"):
        observations.append("No signal_event records found in engine log.")
    else:
        total_signals = funnel.get("total_signal_events", 0)
        open_now = funnel.get("OPEN_NOW", 0)
        observations.append(
            f"Signal funnel: {total_signals} signal events; "
            f"PRE={funnel.get('PRE', 0)}, "
            f"CONFIRM={funnel.get('CONFIRM', 0)}, "
            f"OPEN_NOW={open_now}."
        )
        if funnel.get("unsupported_stages"):
            observations.append(
                f"Unsupported stage values encountered: {funnel['unsupported_stages']}."
            )

    if outcomes.get("no_data"):
        observations.append("No valid outcome records found.")
        limitations.append("Win rate cannot be computed without outcome data.")
    else:
        total_outcomes = outcomes["wins"] + outcomes["loses"] + outcomes["missed"]
        observations.append(
            f"Outcome totals: WIN={outcomes['wins']}, LOSE={outcomes['loses']}, "
            f"MISSED={outcomes['missed']} (total={total_outcomes})."
        )

    if distribution.get("no_data"):
        observations.append("No distribution (tier_publish) events found.")
    else:
        observations.append(
            f"Distribution: PUBLISHED={distribution.get('PUBLISHED', 0)}, "
            f"FAILED={distribution.get('FAILED', 0)}, "
            f"DUPLICATE_SUPPRESSED={distribution.get('DUPLICATE_SUPPRESSED', 0)}."
        )

    # Hypotheses (evidence-based, not fabricated)
    if not outcomes.get("no_data") and outcomes.get("win_rate") is not None:
        win_rate = outcomes["win_rate"]
        if win_rate >= 55:
            hypotheses.append(
                f"Win rate of {win_rate}% is above 55% threshold; "
                "current signal parameters may be performing adequately."
            )
        else:
            hypotheses.append(
                f"Win rate of {win_rate}% is at or below 55% threshold; "
                "further investigation warranted."
            )
    else:
        limitations.append("Insufficient outcome data to form win-rate hypothesis.")

    # Recommendations (advisory only — must not be applied automatically)
    if distribution.get("FAILED", 0) > 0:
        recommendations.append(
            "[ADVISORY] Distribution FAILED events detected; review distribution_router logs. "
            "Do not apply changes without operator review."
        )
    if not funnel.get("no_data") and funnel.get("OPEN_NOW", 0) == 0:
        recommendations.append(
            "[ADVISORY] No OPEN_NOW signal events found; verify signal pipeline is active. "
            "Do not adjust parameters without operator review."
        )

    report = {
        "signal_funnel": funnel,
        "outcomes": outcomes,
        "distribution": distribution,
        "research": {
            "observations": observations,
            "hypotheses": hypotheses,
            "recommendations": recommendations,
            "limitations": limitations,
            "validation_status": "UNVALIDATED",
            "confidence": "LOW" if (funnel.get("no_data") or outcomes.get("no_data")) else "MEDIUM",
            "advisory_only": True,
            "auto_apply": False,
        },
    }
    return report


def persist_research_report(report: Dict[str, Any]) -> None:
    """
    Persist research report atomically.

    Uses storage.save_json_atomic; failed write preserves the last valid report.
    Research report is advisory only and must not be used to trigger automatic changes.
    """
    storage.save_json_atomic(_RESEARCH_REPORT_PATH, report)