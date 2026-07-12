# /opt/binarybot/state_store/event_store.py
# BinaryBot — Event Store (Layer 6)
# Purpose: append-only JSONL storage for structured events (observability / proofs / errors).
# Uses core.storage.append_jsonl for safe writes.

from __future__ import annotations

import os
import time
from typing import Any, Dict

from core.storage import append_jsonl, with_lock

BASE_DIR = "/opt/binarybot"
OBS_DIR = os.path.join(BASE_DIR, "observability")

EVENTS_JSONL = os.path.join(OBS_DIR, "events.jsonl")
ERRORS_JSONL = os.path.join(OBS_DIR, "errors.jsonl")
WARNINGS_JSONL = os.path.join(OBS_DIR, "warnings.jsonl")
PROOFS_JSONL = os.path.join(OBS_DIR, "admin_proofs.jsonl")


def _now_ts() -> int:
    return int(time.time())


def ensure_obs_dir() -> None:
    os.makedirs(OBS_DIR, exist_ok=True)


def write_event(event: Dict[str, Any]) -> None:
    """
    Generic structured event.
    Must be a dict. Will be enriched with created_ts if missing.
    """
    if not isinstance(event, dict):
        raise TypeError("event must be dict")
    ensure_obs_dir()
    event.setdefault("created_ts", _now_ts())
    with with_lock("observability_events"):
        append_jsonl(EVENTS_JSONL, event)


def write_error(error: Dict[str, Any]) -> None:
    if not isinstance(error, dict):
        raise TypeError("error must be dict")
    ensure_obs_dir()
    error.setdefault("created_ts", _now_ts())
    with with_lock("observability_errors"):
        append_jsonl(ERRORS_JSONL, error)


def write_warning(warn: Dict[str, Any]) -> None:
    if not isinstance(warn, dict):
        raise TypeError("warn must be dict")
    ensure_obs_dir()
    warn.setdefault("created_ts", _now_ts())
    with with_lock("observability_warnings"):
        append_jsonl(WARNINGS_JSONL, warn)


def write_proof(kind: str, payload: Dict[str, Any]) -> None:
    """
    Proof log for admin-sensitive actions / publish results.
    """
    if not isinstance(payload, dict):
        raise TypeError("payload must be dict")
    ensure_obs_dir()
    record = {
        "kind": str(kind),
        "payload": payload,
        "created_ts": _now_ts(),
    }
    with with_lock("observability_proofs"):
        append_jsonl(PROOFS_JSONL, record)