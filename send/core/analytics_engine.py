# /opt/binarybot/core/analytics_engine.py
# BinaryBot — Analytics Engine (performance & research)

from __future__ import annotations
 
import hashlib
import json
import os
import time
from typing import Dict, Any, List

from core import storage

OBSERVABILITY_DIR = "/opt/binarybot/observability"
OUTCOMES_PATH = "/opt/binarybot/outcomes/outcomes.jsonl"

ANALYTICS_DIR = "/opt/binarybot/analytics"
AGGREGATES_PATH = os.path.join(ANALYTICS_DIR, "aggregates.json")
 
 
def _member_ref_for_user(user_id: int) -> str | None:
    salt = os.getenv("COMMUNITY_FEEDBACK_SALT", "").strip()
    if not salt:
        return None
    digest = hashlib.sha256(f"{int(user_id)}:{salt}".encode("utf-8")).hexdigest().upper()
    return f"M-{digest[:8]}"


def _safe_json_loads(line: str) -> Dict[str, Any]:
    try:
        obj = json.loads(line)
        return obj if isinstance(obj, dict) else {}
    except Exception:
        return {}


def recompute(now_ts: int) -> Dict[str, Any]:

    wins = 0
    loses = 0
    missed = 0

    signals = {}

    try:
        with open(OUTCOMES_PATH, "r") as f:
            for line in f:
                rec = _safe_json_loads(line)

                signal_id = rec.get("signal_id")
                outcome = rec.get("outcome")

                if signal_id not in signals:
                    signals[signal_id] = {"WIN": 0, "LOSE": 0, "MISSED": 0}

                if outcome in signals[signal_id]:
                    signals[signal_id][outcome] += 1

                if outcome == "WIN":
                    wins += 1
                elif outcome == "LOSE":
                    loses += 1
                elif outcome == "MISSED":
                    missed += 1

    except FileNotFoundError:
        pass

    total = wins + loses + missed

    if total > 0:
        win_rate = round(wins / total * 100, 2)
    else:
        win_rate = 0

    aggregates = {
        "updated_ts": now_ts,
        "wins": wins,
        "loses": loses,
        "missed": missed,
        "total_votes": total,
        "win_rate": win_rate,
        "signals_tracked": len(signals)
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
    member_ref = _member_ref_for_user(user_id)
 
    try:
        with open(OUTCOMES_PATH, "r") as f:
            for line in f:
                rec = _safe_json_loads(line)
 
                if rec.get("user_id") not in {user_id, member_ref}:
                    continue

                outcome = rec.get("outcome")

                if outcome == "WIN":
                    wins += 1
                elif outcome == "LOSE":
                    loses += 1
                elif outcome == "MISSED":
                    missed += 1

    except FileNotFoundError:
        pass

    total = wins + loses + missed

    if total == 0:
        return {
            "wins": 0,
            "loses": 0,
            "missed": 0,
            "total": 0
        }

    return {
        "wins": wins,
        "loses": loses,
        "missed": missed,
        "total": total,
        "win_rate": round(wins / total * 100, 2)
    }