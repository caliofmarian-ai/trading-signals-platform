# /opt/binarybot/monitoring/restart_guard.py
# BinaryBot — Restart Guard (Crash Loop Detection)

from __future__ import annotations

import time
from typing import Any, Dict

from core.observability_logger import build_event, log_event
from state_store import state_store as runtime_state_store


STATE_PATH = runtime_state_store.RESTART_GUARD_PATH
LOCK_NAME = "restart_guard"

MAX_RESTARTS = 3
WINDOW_SECONDS = 60


def _now_ts() -> int:
    return int(time.time())


def _default_state(now_ts: int) -> Dict[str, Any]:
    state = runtime_state_store.default_restart_guard_state()
    state["window_seconds"] = WINDOW_SECONDS
    state["max_restarts"] = MAX_RESTARTS
    state["last_updated_ts"] = now_ts
    return state


def _prune(starts: list[int], now_ts: int) -> list[int]:
    cutoff = now_ts - WINDOW_SECONDS
    return [ts for ts in starts if ts >= cutoff]


def _emit_start_event(info: Dict[str, Any]) -> None:
    event_type = "error" if info["crash_loop"] else "system_health"
    if event_type == "error":
        log_event(
            {
                "event_type": "error",
                "severity": "CRITICAL",
                "error_type": "CRASH_LOOP_DETECTED",
                "message": f"Restart loop detected: {info['restart_count']} counted restart(s) within {WINDOW_SECONDS}s",
                "context": {
                    "restart_count": info["restart_count"],
                    "window_seconds": info["window_seconds"],
                    "max_restarts": info["max_restarts"],
                    "previous_shutdown_kind": info["previous_shutdown_kind"],
                },
                "source": {"module": "restart_guard", "function": "record_start"},
            }
        )
        return

    log_event(
        build_event(
            "system_health",
            {
                "message": "Restart guard start recorded",
                "restart_count": info["restart_count"],
                "window_seconds": info["window_seconds"],
                "max_restarts": info["max_restarts"],
            },
            source={"module": "restart_guard", "function": "record_start"},
        )
    )


def record_start(now_ts: int | None = None) -> Dict[str, Any]:
    """
    Record one startup event and classify whether it represents crash recovery.
    A previous graceful shutdown does not increment the crash-loop counter.
    """
    if now_ts is None:
        now_ts = _now_ts()

    state = runtime_state_store.load_restart_guard_state(path=STATE_PATH)
    state.setdefault("window_seconds", WINDOW_SECONDS)
    state.setdefault("max_restarts", MAX_RESTARTS)

    starts = _prune([int(x) for x in state.get("starts", []) if isinstance(x, int)], now_ts)
    last_shutdown = state.get("last_shutdown", {}) if isinstance(state.get("last_shutdown"), dict) else {}
    previous_shutdown_kind = str(last_shutdown.get("kind") or "unknown").lower()
    counted_restart = previous_shutdown_kind != "graceful"
    if counted_restart:
        starts.append(now_ts)

    state["starts"] = starts
    state["last_start_ts"] = now_ts
    state["last_shutdown"] = {"kind": "running", "ts": now_ts}
    state["last_updated_ts"] = now_ts

    runtime_state_store.save_restart_guard_state(state, path=STATE_PATH)

    restart_count = len(starts)
    crash_loop = restart_count > MAX_RESTARTS
    info = {
        "crash_loop": crash_loop,
        "counted_restart": counted_restart,
        "recovery_required": counted_restart,
        "restart_count": restart_count,
        "window_seconds": WINDOW_SECONDS,
        "max_restarts": MAX_RESTARTS,
        "previous_shutdown_kind": previous_shutdown_kind,
    }
    _emit_start_event(info)
    return info


def should_freeze(now_ts: int | None = None) -> bool:
    """
    Read current restart-guard state without mutating it.
    """
    if now_ts is None:
        now_ts = _now_ts()

    state = runtime_state_store.load_restart_guard_state(path=STATE_PATH)
    starts = _prune([int(x) for x in state.get("starts", []) if isinstance(x, int)], now_ts)
    return len(starts) > MAX_RESTARTS


def mark_graceful_shutdown(now_ts: int | None = None) -> Dict[str, Any]:
    if now_ts is None:
        now_ts = _now_ts()

    state = runtime_state_store.load_restart_guard_state(path=STATE_PATH)
    state["last_shutdown"] = {"kind": "graceful", "ts": now_ts}
    state["last_updated_ts"] = now_ts
    runtime_state_store.save_restart_guard_state(state, path=STATE_PATH)
    return state
