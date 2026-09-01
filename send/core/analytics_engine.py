# send/core/analytics_engine.py
# BinaryBot — multi-truth analytics engine

from __future__ import annotations

import hashlib
import os
from typing import Any, Dict, List, Optional

from core import storage
from core.jsonl_parser import iter_jsonl


TRUTH_MARKET = "MARKET_TRUTH"
TRUTH_OPERATIONAL = "OPERATIONAL_TRUTH"
TRUTH_COMMUNITY = "COMMUNITY_TRUTH"
COMMUNITY_SOURCE = "COMMUNITY_SELF_REPORT"

_OBS_DIR = os.getenv("OBS_DIR", storage.root_path("observability"))
_OUTCOMES_LOG = os.getenv("OUTCOMES_LOG", storage.root_path("outcomes", "outcomes.jsonl"))
_OPERATIONAL_OUTCOMES_LOG = os.getenv(
    "OPERATIONAL_OUTCOMES_LOG",
    storage.root_path("outcomes", "operational_outcomes.jsonl"),
)
_MARKET_TELEMETRY_LOG = os.getenv(
    "TRADE_TEMPORAL_TELEMETRY_LOG",
    storage.root_path("observability", "trade_temporal_telemetry.jsonl"),
)
_DIST_LOG = os.getenv("DIST_EVENTS_LOG", os.path.join(_OBS_DIR, "distribution_events.jsonl"))
_ANALYTICS_BASE = os.getenv("ANALYTICS_DIR", storage.root_path("analytics"))
AGGREGATES_PATH = os.path.join(_ANALYTICS_BASE, "aggregates.json")

_COMMUNITY_OUTCOMES = {"WIN", "LOSE", "MISSED"}
_OPERATIONAL_OUTCOMES = {"WIN", "LOSE", "MISSED"}
_MARKET_OUTCOMES = {"WIN", "LOSS", "DRAW"}
_DIST_RESULTS = {
    "PUBLISHED",
    "FAILED",
    "SKIPPED_SILENT",
    "SKIPPED_LIMIT",
    "SKIPPED_DISABLED",
    "DUPLICATE_SUPPRESSED",
}
_MIN_SAMPLE_FOR_RATE = 5


def _member_ref_for_user(user_id: int) -> Optional[str]:
    salt = os.getenv("COMMUNITY_FEEDBACK_SALT", "").strip()
    if not salt:
        return None
    digest = hashlib.sha256(f"{int(user_id)}:{salt}".encode("utf-8")).hexdigest().upper()
    return f"M-{digest[:8]}"


def _invalid(path: str, message: str, record: Any) -> Dict[str, Any]:
    return {
        "source_path": path,
        "message": message,
        "raw_prefix": str(record)[:200],
    }


def _rate(wins: int, losses: int, *, field_name: str) -> Dict[str, Any]:
    decisive = wins + losses
    result: Dict[str, Any] = {
        "decisive_sample": decisive,
        field_name: None,
        "minimum_sample_for_rate": _MIN_SAMPLE_FOR_RATE,
        "insufficient_sample": decisive < _MIN_SAMPLE_FOR_RATE,
    }
    if decisive >= _MIN_SAMPLE_FOR_RATE:
        result[field_name] = round(wins / decisive * 100.0, 2)
    return result


def _load_market_truth(path: str) -> Dict[str, Any]:
    wins = losses = draws = 0
    invalid_records: List[Dict[str, Any]] = []
    excluded_incomplete = 0
    duplicate_count = 0
    seen: set[str] = set()

    try:
        for record, err in iter_jsonl(path):
            if err is not None:
                invalid_records.append(err.to_dict())
                continue
            if record.get("truth_domain") != TRUTH_MARKET:
                invalid_records.append(_invalid(path, "record is not MARKET_TRUTH", record))
                continue
            if record.get("telemetry_status") != "FINALIZED":
                excluded_incomplete += 1
                continue
            trade_id = str(record.get("trade_id") or record.get("signal_id") or "").strip()
            outcome = str(record.get("result_at_expiry") or "").upper()
            if not trade_id or outcome not in _MARKET_OUTCOMES:
                invalid_records.append(_invalid(path, "invalid finalized MARKET_TRUTH record", record))
                continue
            if trade_id in seen:
                duplicate_count += 1
                continue
            seen.add(trade_id)
            if outcome == "WIN":
                wins += 1
            elif outcome == "LOSS":
                losses += 1
            else:
                draws += 1
    except FileNotFoundError:
        return {
            "truth_domain": TRUTH_MARKET,
            "authoritative_for_strategy_performance": True,
            "no_data": True,
            "reason": "market_telemetry_file_not_found",
            "path": path,
            "wins": 0,
            "losses": 0,
            "draws": 0,
            "total": 0,
            "decisive_sample": 0,
            "market_win_rate_percent": None,
            "insufficient_sample": True,
            "minimum_sample_for_rate": _MIN_SAMPLE_FOR_RATE,
            "excluded_incomplete": 0,
            "duplicate_count": 0,
            "invalid_count": 0,
            "invalid_records": [],
        }

    total = wins + losses + draws
    result: Dict[str, Any] = {
        "truth_domain": TRUTH_MARKET,
        "authoritative_for_strategy_performance": True,
        "no_data": total == 0,
        "path": path,
        "wins": wins,
        "losses": losses,
        "draws": draws,
        "total": total,
        "draw_rate_percent": round(draws / total * 100.0, 2) if total else None,
        "excluded_incomplete": excluded_incomplete,
        "duplicate_count": duplicate_count,
        "invalid_count": len(invalid_records),
        "invalid_records": invalid_records,
    }
    result.update(_rate(wins, losses, field_name="market_win_rate_percent"))
    return result


def _community_record_class(record: Dict[str, Any]) -> Optional[str]:
    if record.get("truth_domain") == TRUTH_COMMUNITY or record.get("truth_source") == COMMUNITY_SOURCE:
        return "EXPLICIT"
    if (
        record.get("event_type") == "user_outcome_record"
        and record.get("truth_domain") is None
        and record.get("truth_source") is None
    ):
        return "LEGACY_INFERRED_FROM_EVENT_TYPE"
    return None


def _load_community_truth(path: str, *, user_id: Any = None) -> Dict[str, Any]:
    wins = loses = missed = 0
    invalid_records: List[Dict[str, Any]] = []
    excluded_other_truth = 0
    duplicate_count = 0
    legacy_inferred_count = 0
    seen: set[tuple[str, str]] = set()

    try:
        for record, err in iter_jsonl(path):
            if err is not None:
                invalid_records.append(err.to_dict())
                continue
            classification = _community_record_class(record)
            if classification is None:
                excluded_other_truth += 1
                continue
            uid = record.get("user_id")
            if user_id is not None:
                member_ref = _member_ref_for_user(int(user_id))
                if uid not in {user_id, member_ref}:
                    try:
                        if int(uid) != int(user_id):
                            continue
                    except (TypeError, ValueError):
                        continue
            signal_id = str(record.get("signal_id") or "").strip()
            outcome = str(record.get("outcome") or "").upper()
            if not signal_id or outcome not in _COMMUNITY_OUTCOMES:
                invalid_records.append(_invalid(path, "invalid COMMUNITY_TRUTH record", record))
                continue
            dedup_key = (signal_id, str(uid))
            if dedup_key in seen:
                duplicate_count += 1
                continue
            seen.add(dedup_key)
            if classification == "LEGACY_INFERRED_FROM_EVENT_TYPE":
                legacy_inferred_count += 1
            if outcome == "WIN":
                wins += 1
            elif outcome == "LOSE":
                loses += 1
            else:
                missed += 1
    except FileNotFoundError:
        return {
            "truth_domain": TRUTH_COMMUNITY,
            "truth_source": COMMUNITY_SOURCE,
            "authoritative_for_strategy_performance": False,
            "migration_policy": "legacy user_outcome_record without truth labels is COMMUNITY_TRUTH only",
            "no_data": True,
            "reason": "community_outcomes_file_not_found",
            "path": path,
            "wins": 0,
            "loses": 0,
            "missed": 0,
            "total": 0,
            "decisive_sample": 0,
            "community_win_rate_percent": None,
            "community_missed_rate_percent": None,
            "insufficient_sample": True,
            "minimum_sample_for_rate": _MIN_SAMPLE_FOR_RATE,
            "excluded_other_truth": 0,
            "legacy_inferred_count": 0,
            "duplicate_count": 0,
            "invalid_count": 0,
            "invalid_records": [],
        }

    total = wins + loses + missed
    result: Dict[str, Any] = {
        "truth_domain": TRUTH_COMMUNITY,
        "truth_source": COMMUNITY_SOURCE,
        "authoritative_for_strategy_performance": False,
        "migration_policy": "legacy user_outcome_record without truth labels is COMMUNITY_TRUTH only",
        "no_data": total == 0,
        "path": path,
        "wins": wins,
        "loses": loses,
        "missed": missed,
        "total": total,
        "community_missed_rate_percent": round(missed / total * 100.0, 2) if total else None,
        "excluded_other_truth": excluded_other_truth,
        "legacy_inferred_count": legacy_inferred_count,
        "duplicate_count": duplicate_count,
        "invalid_count": len(invalid_records),
        "invalid_records": invalid_records,
    }
    result.update(_rate(wins, loses, field_name="community_win_rate_percent"))
    return result


def _load_outcomes(path: str) -> Dict[str, Any]:
    """Compatibility name for the community-feedback store only."""
    return _load_community_truth(path)


def _load_operational_truth(path: str) -> Dict[str, Any]:
    invalid_records: List[Dict[str, Any]] = []
    excluded_other_truth = 0
    by_signal: Dict[str, Dict[str, Any]] = {}

    try:
        for record, err in iter_jsonl(path):
            if err is not None:
                invalid_records.append(err.to_dict())
                continue
            if record.get("truth_domain") != TRUTH_OPERATIONAL:
                excluded_other_truth += 1
                continue
            signal_id = str(record.get("signal_id") or "").strip()
            outcome = str(record.get("outcome") or "").upper()
            if not signal_id or outcome not in _OPERATIONAL_OUTCOMES:
                invalid_records.append(_invalid(path, "invalid OPERATIONAL_TRUTH record", record))
                continue
            ts_value = record.get("outcome_set_ts", record.get("ts", record.get("updated_ts", 0)))
            try:
                ts = float(ts_value or 0)
            except (TypeError, ValueError):
                invalid_records.append(_invalid(path, "invalid operational outcome timestamp", record))
                continue
            current = by_signal.get(signal_id)
            if current is None or ts >= current["_resolved_ts"]:
                by_signal[signal_id] = {**record, "_resolved_ts": ts}
    except FileNotFoundError:
        return {
            "truth_domain": TRUTH_OPERATIONAL,
            "authoritative_for_strategy_performance": False,
            "no_data": True,
            "reason": "operational_outcomes_file_not_found",
            "path": path,
            "wins": 0,
            "loses": 0,
            "missed": 0,
            "total": 0,
            "decisive_sample": 0,
            "operational_win_rate_percent": None,
            "execution_rate_percent": None,
            "missed_rate_percent": None,
            "insufficient_sample": True,
            "minimum_sample_for_rate": _MIN_SAMPLE_FOR_RATE,
            "excluded_other_truth": 0,
            "invalid_count": 0,
            "invalid_records": [],
        }

    wins = loses = missed = 0
    for record in by_signal.values():
        outcome = str(record.get("outcome") or "").upper()
        if outcome == "WIN":
            wins += 1
        elif outcome == "LOSE":
            loses += 1
        elif outcome == "MISSED":
            missed += 1
    total = wins + loses + missed
    executed = wins + loses
    result: Dict[str, Any] = {
        "truth_domain": TRUTH_OPERATIONAL,
        "authoritative_for_strategy_performance": False,
        "no_data": total == 0,
        "path": path,
        "wins": wins,
        "loses": loses,
        "missed": missed,
        "total": total,
        "execution_rate_percent": round(executed / total * 100.0, 2) if total else None,
        "missed_rate_percent": round(missed / total * 100.0, 2) if total else None,
        "excluded_other_truth": excluded_other_truth,
        "invalid_count": len(invalid_records),
        "invalid_records": invalid_records,
    }
    result.update(_rate(wins, loses, field_name="operational_win_rate_percent"))
    return result


def _load_distribution_metrics(path: str) -> Dict[str, Any]:
    counts: Dict[str, int] = {key: 0 for key in _DIST_RESULTS}
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
            **{key: 0 for key in _DIST_RESULTS},
            "total_distribution_events": 0,
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
    """Recompute explicitly separated analytics products without mutating runtime truth."""
    market = _load_market_truth(_MARKET_TELEMETRY_LOG)
    operational = _load_operational_truth(_OPERATIONAL_OUTCOMES_LOG)
    community = _load_community_truth(_OUTCOMES_LOG)
    distribution = _load_distribution_metrics(_DIST_LOG)

    aggregates: Dict[str, Any] = {
        "schema_version": "3.0.0",
        "updated_ts": int(now_ts),
        "truth_separation_enforced": True,
        "strategy_performance_truth_domain": TRUTH_MARKET,
        "no_data": market["no_data"] and operational["no_data"] and community["no_data"],
        "market_truth": market,
        "operational_truth": operational,
        "community_truth": community,
        "distribution": distribution,
        "data_quality": {
            "market_invalid_count": market.get("invalid_count", 0),
            "market_incomplete_count": market.get("excluded_incomplete", 0),
            "operational_invalid_count": operational.get("invalid_count", 0),
            "community_invalid_count": community.get("invalid_count", 0),
            "community_excluded_other_truth": community.get("excluded_other_truth", 0),
            "community_legacy_inferred_count": community.get("legacy_inferred_count", 0),
        },
    }
    storage.save_json_atomic(AGGREGATES_PATH, aggregates)
    return aggregates


def get_symbol_ranking(range_days: int) -> List[Dict[str, Any]]:
    return []


def get_focus_history(range_days: int) -> Dict[str, Any]:
    return {}


def get_funnel(range_days: int) -> Dict[str, Any]:
    return {}


def get_user_stats(user_id: int, range_days: int) -> Dict[str, Any]:
    del range_days
    return _load_community_truth(_OUTCOMES_LOG, user_id=user_id)
