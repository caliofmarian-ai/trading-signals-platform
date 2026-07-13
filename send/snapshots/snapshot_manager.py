# /opt/binarybot/snapshots/snapshot_manager.py
# BinaryBot — Snapshot Manager (Layer 6)

from __future__ import annotations

import json
import os
import time
from typing import Any, Dict

from core import storage
from state_store import state_store as runtime_state_store

SNAPSHOT_SCHEMA_VERSION = "1.0.0"
SNAPSHOT_DIR = runtime_state_store.snapshots_dir()

FOCUS_STATE = runtime_state_store.FOCUS_STATE_PATH
DIST_STATE = runtime_state_store.DIST_STATE_PATH


class SnapshotValidationError(RuntimeError):
    pass


def _now_ts() -> int:
    return int(time.time())


def ensure_snapshot_dir() -> None:
    os.makedirs(SNAPSHOT_DIR, exist_ok=True)


def _snapshot_path(name: str) -> str:
    return os.path.join(SNAPSHOT_DIR, name)


def _validate_snapshot_payload(payload: Any) -> Dict[str, Any]:
    if not isinstance(payload, dict):
        raise SnapshotValidationError("Snapshot payload must be an object")

    version = str(payload.get("schema_version") or "")
    if version != SNAPSHOT_SCHEMA_VERSION:
        raise SnapshotValidationError(
            f"Unsupported snapshot schema version: {version or '<missing>'}"
        )

    created_ts = payload.get("created_ts")
    if not isinstance(created_ts, int):
        raise SnapshotValidationError("Snapshot created_ts must be an integer")

    focus_state = runtime_state_store.validate_fsm_state(payload.get("focus_state"))
    dist_state = runtime_state_store.validate_dist_state(payload.get("dist_state"))

    return {
        "schema_version": SNAPSHOT_SCHEMA_VERSION,
        "created_ts": created_ts,
        "focus_state": focus_state,
        "dist_state": dist_state,
    }


def create_snapshot() -> str:
    """
    Creates a full system snapshot atomically.
    Returns snapshot file path.
    """
    ensure_snapshot_dir()

    snapshot = {
        "schema_version": SNAPSHOT_SCHEMA_VERSION,
        "created_ts": _now_ts(),
        "focus_state": runtime_state_store.load_fsm_state(),
        "dist_state": runtime_state_store.load_dist_state(),
    }

    filename = f"snapshot_{snapshot['created_ts']}.json"
    path = _snapshot_path(filename)
    storage.save_json_atomic(path, snapshot)
    return path


def list_snapshots():
    ensure_snapshot_dir()
    files = [
        file_name
        for file_name in os.listdir(SNAPSHOT_DIR)
        if file_name.startswith("snapshot_") and file_name.endswith(".json")
    ]
    files.sort()
    return files


def load_snapshot(name: str) -> Dict[str, Any]:
    path = _snapshot_path(name)
    try:
        with open(path, "r", encoding="utf-8") as handle:
            payload = json.load(handle)
    except FileNotFoundError:
        raise FileNotFoundError(name)
    except json.JSONDecodeError as exc:
        raise SnapshotValidationError(f"Invalid snapshot JSON: {exc.msg}") from exc
    return _validate_snapshot_payload(payload)


def restore_snapshot(name: str):
    snapshot = load_snapshot(name)

    try:
        current_focus = runtime_state_store.load_fsm_state()
    except Exception:
        current_focus = None
    try:
        current_dist = runtime_state_store.load_dist_state()
    except Exception:
        current_dist = None

    try:
        runtime_state_store.save_fsm_state(snapshot["focus_state"])
        runtime_state_store.save_dist_state(snapshot["dist_state"])
    except Exception:
        if current_focus is not None:
            runtime_state_store.save_fsm_state(current_focus)
        if current_dist is not None:
            runtime_state_store.save_dist_state(current_dist)
        raise

    return {
        "snapshot_name": name,
        "schema_version": snapshot["schema_version"],
        "created_ts": snapshot["created_ts"],
    }
