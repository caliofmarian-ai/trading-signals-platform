# /opt/binarybot/snapshots/snapshot_manager.py
# BinaryBot — Snapshot Manager (Layer 6)

from __future__ import annotations

import os
import time
import json
from typing import Dict, Any

BASE_DIR = "/opt/binarybot"
STATE_DIR = os.path.join(BASE_DIR, "state")
SNAPSHOT_DIR = os.path.join(BASE_DIR, "snapshots")

FOCUS_STATE = os.path.join(STATE_DIR, "focus_state.json")
DIST_STATE = os.path.join(STATE_DIR, "dist_state.json")


def _now_ts() -> int:
    return int(time.time())


def ensure_snapshot_dir():
    os.makedirs(SNAPSHOT_DIR, exist_ok=True)


def _load_json_safe(path: str) -> Dict[str, Any]:
    if not os.path.exists(path):
        return {}

    try:
        with open(path, "r") as f:
            return json.load(f)
    except Exception:
        return {}


def create_snapshot() -> str:
    """
    Creates a full system snapshot.
    Returns snapshot file path.
    """

    ensure_snapshot_dir()

    snapshot = {
        "created_ts": _now_ts(),
        "focus_state": _load_json_safe(FOCUS_STATE),
        "dist_state": _load_json_safe(DIST_STATE)
    }

    filename = f"snapshot_{snapshot['created_ts']}.json"
    path = os.path.join(SNAPSHOT_DIR, filename)

    with open(path, "w") as f:
        json.dump(snapshot, f, indent=2)

    return path


def list_snapshots():

    ensure_snapshot_dir()

    files = []

    for f in os.listdir(SNAPSHOT_DIR):
        if f.startswith("snapshot_") and f.endswith(".json"):
            files.append(f)

    files.sort()

    return files


def load_snapshot(name: str) -> Dict[str, Any]:

    path = os.path.join(SNAPSHOT_DIR, name)

    if not os.path.exists(path):
        raise FileNotFoundError(name)

    with open(path, "r") as f:
        return json.load(f)


def restore_snapshot(name: str):

    snapshot = load_snapshot(name)

    focus = snapshot.get("focus_state", {})
    dist = snapshot.get("dist_state", {})

    os.makedirs(STATE_DIR, exist_ok=True)

    with open(FOCUS_STATE, "w") as f:
        json.dump(focus, f, indent=2)

    with open(DIST_STATE, "w") as f:
        json.dump(dist, f, indent=2)