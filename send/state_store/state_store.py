# /opt/binarybot/state_store/state_store.py
# BinaryBot — State Store (Layer 6)
# Purpose: single source of truth for persisted JSON states.
# Uses core.storage for atomic writes + optional locks.

from __future__ import annotations

import os
import time
from typing import Any, Dict, Optional

from core.storage import load_json, save_json_atomic, with_lock

BASE_DIR = "/opt/binarybot"
STATE_DIR = os.path.join(BASE_DIR, "state")

# Canonical state files (aligned with docs)
FOCUS_STATE_PATH = os.path.join(STATE_DIR, "focus_state.json")          # FSMState
DIST_STATE_PATH = os.path.join(STATE_DIR, "dist_state.json")            # DistState
SETTINGS_PATH = os.path.join(BASE_DIR, "settings.json")                 # buffer_mode etc.
ACTIVE_SYMBOLS_PATH = os.path.join(BASE_DIR, "active_symbols.json")     # symbol list


def _now_ts() -> int:
    return int(time.time())


def ensure_state_dir() -> None:
    os.makedirs(STATE_DIR, exist_ok=True)


# -------------------------
# Defaults (safe boot)
# -------------------------

def default_fsm_state() -> Dict[str, Any]:
    return {
        "version": "1.0.0",
        "mode": "WIDE_SCAN",
        "watchlist": [],
        "per_symbol": {},
        "last_updated_ts": _now_ts(),
    }


def default_dist_state() -> Dict[str, Any]:
    return {
        "version": "1.0.0",
        "last_reset_epoch": 0,
        "tier_state": {
            "FREE": "ACTIVE",
            "BASIC": "ACTIVE",
            "PRO": "ACTIVE",
            "ELITE": "ACTIVE",
        },
        "open_signals_today": {
            "FREE": 0,
            "BASIC": 0,
            "PRO": 0,
            "ELITE": 0,
        },
        "dedup": {},  # optional structure: tier -> signal_id -> stage -> bool
        "last_updated_ts": _now_ts(),
    }


def default_settings() -> Dict[str, Any]:
    return {
        "buffer_mode": "MEDIUM",
        "last_updated_ts": _now_ts(),
    }


def default_active_symbols() -> Dict[str, Any]:
    # keep as dict for future metadata; current canonical key: "symbols"
    return {
        "symbols": [],
        "last_updated_ts": _now_ts(),
    }


# -------------------------
# Loaders (with locks)
# -------------------------

def load_fsm_state() -> Dict[str, Any]:
    ensure_state_dir()
    with with_lock("focus_state"):
        return load_json(FOCUS_STATE_PATH, default_fsm_state())


def save_fsm_state(state: Dict[str, Any]) -> None:
    ensure_state_dir()
    state["last_updated_ts"] = _now_ts()
    with with_lock("focus_state"):
        save_json_atomic(FOCUS_STATE_PATH, state)


def load_dist_state() -> Dict[str, Any]:
    ensure_state_dir()
    with with_lock("dist_state"):
        return load_json(DIST_STATE_PATH, default_dist_state())


def save_dist_state(state: Dict[str, Any]) -> None:
    ensure_state_dir()
    state["last_updated_ts"] = _now_ts()
    with with_lock("dist_state"):
        save_json_atomic(DIST_STATE_PATH, state)


def load_settings() -> Dict[str, Any]:
    with with_lock("settings"):
        return load_json(SETTINGS_PATH, default_settings())


def save_settings(settings: Dict[str, Any]) -> None:
    settings["last_updated_ts"] = _now_ts()
    with with_lock("settings"):
        save_json_atomic(SETTINGS_PATH, settings)


def load_active_symbols() -> Dict[str, Any]:
    with with_lock("active_symbols"):
        return load_json(ACTIVE_SYMBOLS_PATH, default_active_symbols())


def save_active_symbols(obj: Dict[str, Any]) -> None:
    obj["last_updated_ts"] = _now_ts()
    with with_lock("active_symbols"):
        save_json_atomic(ACTIVE_SYMBOLS_PATH, obj)


# -------------------------
# Convenience helpers
# -------------------------

def get_buffer_mode() -> str:
    s = load_settings()
    mode = (s.get("buffer_mode") or "MEDIUM").upper()
    if mode not in {"SMALL", "MEDIUM", "LARGE"}:
        mode = "MEDIUM"
    return mode


def set_buffer_mode(mode: str) -> None:
    mode_u = (mode or "").upper()
    if mode_u not in {"SMALL", "MEDIUM", "LARGE"}:
        raise ValueError("buffer_mode must be SMALL|MEDIUM|LARGE")
    s = load_settings()
    s["buffer_mode"] = mode_u
    save_settings(s)


def list_symbols() -> list[str]:
    obj = load_active_symbols()
    syms = obj.get("symbols") or []
    # normalize
    out: list[str] = []
    for x in syms:
        if isinstance(x, str) and x.strip():
            out.append(x.strip().upper())
    return out


def set_symbols(symbols: list[str]) -> None:
    normalized = []
    seen = set()
    for s in symbols or []:
        if not isinstance(s, str):
            continue
        v = s.strip().upper()
        if not v or v in seen:
            continue
        seen.add(v)
        normalized.append(v)
    obj = load_active_symbols()
    obj["symbols"] = normalized
    save_active_symbols(obj)