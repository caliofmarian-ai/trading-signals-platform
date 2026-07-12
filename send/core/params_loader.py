# /opt/binarybot/core/params_loader.py
# BinaryBot — Algo Params Loader + Validation
# Loads config/algo_params.json and enforces "no missing keys" + computes checksum.
# Canonical references: PARAMS_REFERENCE.md, SYSTEM_INVARIANTS.md (INV-30/31/32)

from __future__ import annotations

import hashlib
import json
import os
from typing import Any, Dict, Iterable, List, Tuple

try:
    from . import storage  # type: ignore
except Exception:  # pragma: no cover
    storage = None


DEFAULT_PARAMS_PATH = os.getenv("ALGO_PARAMS_PATH", "/opt/binarybot/config/algo_params.json")


# Minimal required keys (expand when you paste your real PARAMS_REFERENCE.md)
# Keep this strict: missing keys should stop engine at startup.
REQUIRED_TOP_LEVEL_KEYS = [
    "algo_version",
    "thresholds",
    "weights",
    "expiry",
    "buffer",
    "gates",
]

# Minimal nested keys (expand gradually, but keep deterministic)
REQUIRED_NESTED_KEYS = [
    ("thresholds", ["pre", "confirm", "open"]),
    ("expiry", ["min_minutes", "max_minutes"]),
    ("buffer", ["modes"]),  # modes: SMALL/MEDIUM/LARGE config
    ("gates", ["spike_filter", "sr_gate", "feasibility"]),
]


class ParamsValidationError(ValueError):
    pass


def _read_json_fallback(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_algo_params(path: str = DEFAULT_PARAMS_PATH) -> Dict[str, Any]:
    """
    Load algo_params.json (single source of truth for strategy thresholds).
    Raises ParamsValidationError if file missing or invalid.
    """
    if not os.path.exists(path):
        raise ParamsValidationError(f"algo params file not found: {path}")

    if storage and hasattr(storage, "load_json"):
        params = storage.load_json(path, default=None)  # type: ignore
        if params is None:
            raise ParamsValidationError(f"failed to load algo params: {path}")
    else:
        params = _read_json_fallback(path)

    if not isinstance(params, dict):
        raise ParamsValidationError("algo params must be a JSON object")

    validate_algo_params(params)
    return params


def validate_algo_params(params: Dict[str, Any]) -> None:
    """
    Strict-enough validation. Grow this list as PARAMS_REFERENCE.md evolves.
    """
    missing: List[str] = []
    for k in REQUIRED_TOP_LEVEL_KEYS:
        if k not in params:
            missing.append(k)

    if missing:
        raise ParamsValidationError(f"algo params missing top-level keys: {missing}")

    # nested
    for parent, keys in REQUIRED_NESTED_KEYS:
        obj = params.get(parent)
        if not isinstance(obj, dict):
            raise ParamsValidationError(f"algo params '{parent}' must be an object")
        for kk in keys:
            if kk not in obj:
                raise ParamsValidationError(f"algo params missing key: {parent}.{kk}")

    # sanity checks
    _validate_thresholds(params)
    _validate_expiry(params)
    _validate_buffer_modes(params)
    _validate_no_hardcoded_leaks(params)


def compute_checksum(params: Dict[str, Any]) -> str:
    """
    Deterministic checksum for governance + logs.
    Uses canonical JSON serialization: sorted keys, compact separators.
    """
    canonical = json.dumps(params, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _validate_thresholds(params: Dict[str, Any]) -> None:
    t = params["thresholds"]
    pre = t.get("pre")
    confirm = t.get("confirm")
    open_ = t.get("open")

    if not _is_number(pre) or not _is_number(confirm) or not _is_number(open_):
        raise ParamsValidationError("thresholds.pre/confirm/open must be numbers")

    # INV-20: PRE ≤ CONFIRM ≤ OPEN
    if not (pre <= confirm <= open_):
        raise ParamsValidationError("threshold hierarchy violated: must be PRE <= CONFIRM <= OPEN")

    # scores typically 0..100
    for name, v in [("pre", pre), ("confirm", confirm), ("open", open_)]:
        if v < 0 or v > 100:
            raise ParamsValidationError(f"thresholds.{name} out of range 0..100")


def _validate_expiry(params: Dict[str, Any]) -> None:
    e = params["expiry"]
    mn = e.get("min_minutes")
    mx = e.get("max_minutes")
    if not _is_int(mn) or not _is_int(mx):
        raise ParamsValidationError("expiry.min_minutes/max_minutes must be integers")
    if mn <= 0 or mx <= 0 or mn > mx:
        raise ParamsValidationError("expiry range invalid (min must be >0 and <= max)")


def _validate_buffer_modes(params: Dict[str, Any]) -> None:
    b = params["buffer"]
    modes = b.get("modes")
    if not isinstance(modes, dict):
        raise ParamsValidationError("buffer.modes must be an object mapping modes")

    for mode in ("SMALL", "MEDIUM", "LARGE"):
        if mode not in modes:
            raise ParamsValidationError(f"buffer.modes missing mode: {mode}")

        cfg = modes[mode]
        if not isinstance(cfg, dict):
            raise ParamsValidationError(f"buffer.modes.{mode} must be an object")

        # allow different schemas; require at least one numeric multiplier field
        # e.g. atr_mult, fixed_pips, points_mult, etc.
        numeric_fields = [k for k, v in cfg.items() if _is_number(v)]
        if not numeric_fields:
            raise ParamsValidationError(f"buffer.modes.{mode} must contain at least one numeric field")


def _validate_no_hardcoded_leaks(params: Dict[str, Any]) -> None:
    """
    Soft guardrail: ensure there are no obviously wrong fields.
    This is NOT a full schema check — just protects from accidental .env style injection.
    """
    forbidden_keys = {"TELEGRAM_TOKEN", "API_KEY", "PASSWORD", "SECRET", "TOKEN"}
    found = _find_keys_case_insensitive(params, forbidden_keys)
    if found:
        raise ParamsValidationError(f"forbidden secret-like keys found in algo params: {sorted(found)}")


def _find_keys_case_insensitive(obj: Any, forbidden: set) -> set:
    hit = set()
    if isinstance(obj, dict):
        for k, v in obj.items():
            ku = str(k).upper()
            for fk in forbidden:
                if fk in ku:
                    hit.add(k)
            hit |= _find_keys_case_insensitive(v, forbidden)
    elif isinstance(obj, list):
        for it in obj:
            hit |= _find_keys_case_insensitive(it, forbidden)
    return hit


def _is_number(x: Any) -> bool:
    return isinstance(x, (int, float)) and not isinstance(x, bool)


def _is_int(x: Any) -> bool:
    return isinstance(x, int) and not isinstance(x, bool)