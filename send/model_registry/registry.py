# /opt/binarybot/model_registry/registry.py
# BinaryBot — Model Registry
# Canonical, minimal, deterministic.

from __future__ import annotations

import os
import time
from dataclasses import dataclass
from typing import Any, Dict, Optional

from core.storage import load_json, save_json_atomic, with_lock

REGISTRY_PATH_DEFAULT = "/opt/binarybot/model_registry/registry.json"


@dataclass(frozen=True)
class ModelInfo:
    key: str                    # e.g. "strategy_v2"
    version: str                # e.g. "1.0.0"
    checksum: str               # params checksum or artifact checksum
    created_ts: int             # epoch seconds UTC
    meta: Dict[str, Any]        # any extra info (no secrets)


def _now_ts() -> int:
    return int(time.time())


def _registry_path() -> str:
    return os.environ.get("MODEL_REGISTRY_PATH", REGISTRY_PATH_DEFAULT)


def _default_registry() -> Dict[str, Any]:
    return {
        "version": "1.0.0",
        "models": {},            # key -> dict(ModelInfo fields)
        "active": {},            # key -> version (or model id)
        "last_updated_ts": _now_ts(),
    }


def load_registry(path: Optional[str] = None) -> Dict[str, Any]:
    p = path or _registry_path()
    return load_json(p, default=_default_registry())


def save_registry(reg: Dict[str, Any], path: Optional[str] = None) -> None:
    p = path or _registry_path()
    reg["last_updated_ts"] = _now_ts()
    save_json_atomic(p, reg)


def register_model(
    key: str,
    version: str,
    checksum: str,
    meta: Optional[Dict[str, Any]] = None,
    *,
    path: Optional[str] = None,
) -> ModelInfo:
    """
    Register or update a model entry.
    - Safe atomic write under lock.
    - Does not set as active automatically (use set_active()).
    """
    p = path or _registry_path()
    meta = meta or {}

    with with_lock("model_registry"):
        reg = load_registry(p)
        models = reg.setdefault("models", {})

        info = ModelInfo(
            key=key,
            version=version,
            checksum=checksum,
            created_ts=_now_ts(),
            meta=dict(meta),
        )
        models[key] = {
            "key": info.key,
            "version": info.version,
            "checksum": info.checksum,
            "created_ts": info.created_ts,
            "meta": info.meta,
        }
        save_registry(reg, p)
        return info


def get_model(key: str, *, path: Optional[str] = None) -> Optional[Dict[str, Any]]:
    p = path or _registry_path()
    reg = load_registry(p)
    return reg.get("models", {}).get(key)


def set_active(key: str, version: str, *, path: Optional[str] = None) -> bool:
    """
    Mark a model version as active.
    Returns True if success, False if model missing/mismatch.
    """
    p = path or _registry_path()
    with with_lock("model_registry"):
        reg = load_registry(p)
        model = reg.get("models", {}).get(key)
        if not model:
            return False
        if str(model.get("version")) != str(version):
            return False
        reg.setdefault("active", {})[key] = version
        save_registry(reg, p)
        return True


def get_active(key: str, *, path: Optional[str] = None) -> Optional[Dict[str, Any]]:
    p = path or _registry_path()
    reg = load_registry(p)
    active_ver = reg.get("active", {}).get(key)
    if not active_ver:
        return None
    model = reg.get("models", {}).get(key)
    if not model:
        return None
    if str(model.get("version")) != str(active_ver):
        return None
    return model


def list_models(*, path: Optional[str] = None) -> Dict[str, Any]:
    p = path or _registry_path()
    reg = load_registry(p)
    return {
        "models": reg.get("models", {}),
        "active": reg.get("active", {}),
        "last_updated_ts": reg.get("last_updated_ts"),
    }