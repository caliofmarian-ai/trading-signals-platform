from __future__ import annotations

import importlib
import os
import time
from typing import Any, Dict

from core import storage


def status_path() -> str:
    return storage.state_path("runtime_status.json")


def _read_status_file() -> Dict[str, Any]:
    raw = storage.load_json(status_path(), default={})
    return raw if isinstance(raw, dict) else {}


def write_status(phase: str, message: str, **extra: Any) -> Dict[str, Any]:
    payload: Dict[str, Any] = {
        "phase": str(phase),
        "message": str(message),
        "pid": int(os.getpid()),
        "updated_ts": int(time.time()),
    }
    payload.update(extra)
    storage.save_json_atomic(status_path(), payload)
    return payload


def update_status(**changes: Any) -> Dict[str, Any]:
    payload = _read_status_file()
    if not isinstance(payload, dict):
        payload = {}
    payload.setdefault("phase", "unknown")
    payload.setdefault("message", "")
    payload.setdefault("pid", int(os.getpid()))
    payload.update(changes)
    payload["updated_ts"] = int(time.time())
    storage.save_json_atomic(status_path(), payload)
    return payload


def _strategy_auditor_env_presence() -> Dict[str, bool]:
    """Return presence-only schedule evidence without disclosing configured values."""
    return {
        "STRATEGY_AUDITOR_ENABLED": bool(os.getenv("STRATEGY_AUDITOR_ENABLED", "").strip()),
        "STRATEGY_AUDITOR_DAILY_TIME": bool(os.getenv("STRATEGY_AUDITOR_DAILY_TIME", "").strip()),
        "STRATEGY_AUDITOR_TIMEZONE": bool(os.getenv("STRATEGY_AUDITOR_TIMEZONE", "").strip()),
        "STRATEGY_AUDITOR_DAILY_TIME_UTC": bool(os.getenv("STRATEGY_AUDITOR_DAILY_TIME_UTC", "").strip()),
    }


def read_status() -> Dict[str, Any]:
    payload = dict(_read_status_file())
    payload["strategy_auditor_env_presence"] = _strategy_auditor_env_presence()
    try:
        # Import the canonical R-019 status authority directly by module name.
        # `tools.__init__` may intentionally expose the local-time adapter as the
        # package-level `strategy_auditor_runtime` attribute; that adapter owns
        # scheduling, while durable status persistence remains in this base module.
        strategy_auditor_runtime = importlib.import_module("tools.strategy_auditor_runtime")
        auditor_status = strategy_auditor_runtime.read_auditor_status(
            max_age_seconds=strategy_auditor_runtime.STATUS_OVERLAY_MAX_AGE_SECONDS
        )
        if auditor_status:
            payload["strategy_auditor"] = auditor_status
    except Exception:
        pass
    return payload


def is_pid_alive(pid: Any) -> bool:
    try:
        value = int(pid)
    except Exception:
        return False
    if value <= 0:
        return False
    try:
        os.kill(value, 0)
        return True
    except OSError:
        return False
