# /opt/binarybot/monitoring/restart_guard.py
# BinaryBot — Restart Guard (Crash Loop Detection)

from __future__ import annotations

import os
import time
from typing import Any, Dict

from core.storage import load_json, save_json_atomic, with_lock
from core.observability_logger import log_event


STATE_PATH = "/opt/binarybot/state/restart_guard.json"
LOCK_NAME = "restart_guard"

# Canonical policy (per OBSERVABILITY_LOGGING_SPEC.md)
MAX_RESTARTS = 3
WINDOW_SECONDS = 60


def _now_ts() -> int:
    return int(time.time())


def _default_state(now_ts: int) -> Dict[str, Any]:
    return {
        "version": "1.0.0",
        "window_seconds": WINDOW_SECONDS,
        "max_restarts": MAX_RESTARTS,
        "starts": [],  # list[int] epoch seconds (UTC)
        "last_updated_ts": now_ts,
    }


def _prune(starts: list[int], now_ts: int) -> list[int]:
    cutoff = now_ts - WINDOW_SECONDS
    return [ts for ts in starts if ts >= cutoff]


def record_start(now_ts: int | None = None) -> Dict[str, Any]:
    """
    Record a process start and detect crash loops.
    Returns:
      {
        "crash_loop": bool,
        "restart_count": int,
        "window_seconds": int,
        "max_restarts": int
      }
    """
    if now_ts is None:
        now_ts = _now_ts()

    os.makedirs(os.path.dirname(STATE_PATH), exist_ok=True)

    with with_lock(LOCK_NAME):
        state = load_json(STATE_PATH, default=None)
        if not isinstance(state, dict):
            state = _default_state(now_ts)

        starts = state.get("starts")
        if not isinstance(starts, list):
            starts = []

        starts = _prune([int(x) for x in starts if isinstance(x, (int, float))], now_ts)
        starts.append(now_ts)

        state["starts"] = starts
        state["last_updated_ts"] = now_ts

        save_json_atomic(STATE_PATH, state)

    restart_count = len(state["starts"])
    crash_loop = restart_count > MAX_RESTARTS

    if crash_loop:
        log_event({
            "event_type": "error",
            "severity": "CRITICAL",
            "code": "CRASH_LOOP_DETECTED",
            "message": f"Restart loop detected: {restart_count} starts within {WINDOW_SECONDS}s",
            "data": {
                "restart_count": restart_count,
                "window_seconds": WINDOW_SECONDS,
                "max_restarts": MAX_RESTARTS,
            }
        })
    else:
        log_event({
            "event_type": "system_health",
            "message": "Restart guard start recorded",
            "data": {
                "restart_count": restart_count,
                "window_seconds": WINDOW_SECONDS,
                "max_restarts": MAX_RESTARTS,
            }
        })

    return {
        "crash_loop": crash_loop,
        "restart_count": restart_count,
        "window_seconds": WINDOW_SECONDS,
        "max_restarts": MAX_RESTARTS,
    }


def should_freeze(now_ts: int | None = None) -> bool:
    """
    Helper used by system_boot / engine_loop.
    Returns True if crash loop threshold exceeded.
    """
    info = record_start(now_ts=now_ts)
    return bool(info.get("crash_loop", False))