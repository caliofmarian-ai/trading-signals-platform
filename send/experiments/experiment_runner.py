# /opt/binarybot/experiments/experiment_runner.py
# BinaryBot — Experiment Runner (offline / research)
# Canonical skeleton: NO live trading impact.

from __future__ import annotations

import time
from typing import Any, Dict, List, Optional

from core.storage import load_json, save_json_atomic, append_jsonl, with_lock

DEFAULT_EXPERIMENTS_DIR = "/opt/binarybot/experiments"
DEFAULT_RESULTS_JSONL = "/opt/binarybot/experiments/results.jsonl"


def _now_ts() -> int:
    return int(time.time())


def _result_record(
    experiment_name: str,
    status: str,
    payload: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    return {
        "event_type": "experiment_result",
        "experiment": experiment_name,
        "status": status,  # "START"|"OK"|"FAIL"
        "ts": _now_ts(),
        "payload": payload or {},
    }


def run_experiment(experiment_name: str, config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Runs a named experiment in an isolated/offline manner.
    This file intentionally does NOT import signal_engine runtime loop.

    Returns a summary dict.
    """
    append_jsonl(DEFAULT_RESULTS_JSONL, _result_record(experiment_name, "START", {"config": config}))

    try:
        # Placeholder: implement actual experiment execution later.
        # Examples:
        # - replay candles from snapshots/
        # - compare param sets
        # - compute funnel metrics from logs
        summary = {
            "experiment": experiment_name,
            "status": "OK",
            "ts": _now_ts(),
            "notes": "skeleton_only",
        }

        append_jsonl(DEFAULT_RESULTS_JSONL, _result_record(experiment_name, "OK", summary))
        return summary

    except Exception as e:
        err = {"error": str(e)}
        append_jsonl(DEFAULT_RESULTS_JSONL, _result_record(experiment_name, "FAIL", err))
        return {"experiment": experiment_name, "status": "FAIL", "ts": _now_ts(), **err}


def list_results(limit: int = 50) -> List[Dict[str, Any]]:
    """
    Minimal helper: reads results.jsonl if present and returns last N entries.
    """
    import os
    if not os.path.exists(DEFAULT_RESULTS_JSONL):
        return []
    out: List[Dict[str, Any]] = []
    with open(DEFAULT_RESULTS_JSONL, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                import json
                out.append(json.loads(line))
            except Exception:
                continue
    return out[-max(1, int(limit)) :]