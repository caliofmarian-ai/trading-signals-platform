# /opt/binarybot/intelligence/research_engine.py
# BinaryBot — Research Engine (signal lifecycle analytics)

from __future__ import annotations

import os
from typing import Dict, Any

from core import storage

OBS_DIR = "/opt/binarybot/observability"
OUTCOMES_PATH = "/opt/binarybot/outcomes/outcomes.jsonl"

ENGINE_LOG = os.path.join(OBS_DIR, "engine_events.jsonl")
DIST_LOG = os.path.join(OBS_DIR, "distribution_events.jsonl")


def compute_signal_funnel() -> Dict[str, Any]:

    pre = 0
    confirm = 0
    open_now = 0

    try:
        with open(ENGINE_LOG, "r") as f:
            for line in f:
                rec = storage.safe_json_loads(line)

                if rec.get("event_type") != "signal_event":
                    continue

                stage = rec.get("data", {}).get("stage")

                if stage == "PRE":
                    pre += 1

                elif stage == "CONFIRM":
                    confirm += 1

                elif stage == "OPEN_NOW":
                    open_now += 1

    except FileNotFoundError:
        pass

    return {
        "pre": pre,
        "confirm": confirm,
        "open_now": open_now
    }


def compute_outcome_stats():

    wins = 0
    loses = 0
    missed = 0

    try:
        with open(OUTCOMES_PATH, "r") as f:
            for line in f:
                rec = storage.safe_json_loads(line)

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
            "win_rate": 0
        }

    return {
        "wins": wins,
        "loses": loses,
        "missed": missed,
        "win_rate": round(wins / total * 100, 2)
    }


def build_research_report():

    funnel = compute_signal_funnel()

    outcomes = compute_outcome_stats()

    return {
        "signal_funnel": funnel,
        "outcomes": outcomes
    }