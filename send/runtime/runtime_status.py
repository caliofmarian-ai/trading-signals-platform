from __future__ import annotations

import os
import time
from typing import Any, Dict

from core import storage


def status_path() -> str:
    return storage.state_path("runtime_status.json")


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
    payload = read_status()
    if not isinstance(payload, dict):
        payload = {}
    payload.setdefault("phase", "unknown")
    payload.setdefault("message", "")
    payload.setdefault("pid", int(os.getpid()))
    payload.update(changes)
    payload["updated_ts"] = int(time.time())
    storage.save_json_atomic(status_path(), payload)
    return payload


def read_status() -> Dict[str, Any]:
    raw = storage.load_json(status_path(), default={})
    return raw if isinstance(raw, dict) else {}


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
