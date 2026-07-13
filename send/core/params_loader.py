# /opt/binarybot/core/params_loader.py
# BinaryBot — Canonical Algo Params Loader + Validation (BATCH-02)
# Implements the canonical parameter contract from params_schema.json.
# Canonical references: STRATEGY_PARAMETER_CONTROL_SPEC_v2.0.0.md, SYSTEM_INVARIANTS_v2.0.0.md

from __future__ import annotations

import hashlib
import json
import os
from typing import Any, Dict, FrozenSet, Iterable, List, NamedTuple, Optional, Tuple

try:
    from . import storage  # type: ignore
except Exception:  # pragma: no cover
    storage = None

DEFAULT_PARAMS_PATH = os.getenv("ALGO_PARAMS_PATH", "/opt/binarybot/config/algo_params.json")

# ---------------------------------------------------------------------------
# Canonical contract definition
# ---------------------------------------------------------------------------

# Required top-level keys — must be present in every canonical params file.
REQUIRED_TOP_LEVEL_KEYS: List[str] = [
    "algo_version",
    "score_thresholds",
    "expiry_limits_minutes",
    "buffer_multipliers",
]

# Optional top-level keys — may be absent; strategy_v2.py supplies conservative defaults.
OPTIONAL_TOP_LEVEL_KEYS: FrozenSet[str] = frozenset({
    "strategy_v2",
    "spike_filters",
    "sr_required_multiplier",
    "crypto_points_rounding",
    "trend_time_adjust",
    "structure_factor",
})

# Complete canonical key set (required + optional).
CANONICAL_TOP_LEVEL_KEYS: FrozenSet[str] = (
    frozenset(REQUIRED_TOP_LEVEL_KEYS) | OPTIONAL_TOP_LEVEL_KEYS
)

# Required sub-keys for each required nested object.
REQUIRED_NESTED_KEYS: List[Tuple[str, List[str]]] = [
    ("score_thresholds", ["PRE", "CONFIRM", "OPEN"]),
    ("expiry_limits_minutes", ["min", "max"]),
    ("buffer_multipliers", ["SMALL", "MEDIUM", "LARGE"]),
]

# Required sub-keys for the optional strategy_v2 block (if the block is present).
STRATEGY_V2_KEYS: List[str] = [
    "ema_fast", "ema_slow", "rsi_period", "rsi_call", "rsi_put", "min_avg_range",
]
MIN_AVG_RANGE_KEYS: List[str] = ["FOREX_DEFAULT", "FOREX_JPY", "CRYPTO_USD"]

# Required sub-keys for the optional spike_filters block (if present).
SPIKE_FILTERS_KEYS: List[str] = ["wick_body_ratio_max", "range_z_max", "jump_vs_atr_max"]

# Required sub-keys for the optional trend_time_adjust block (if present).
TREND_TIME_ADJUST_KEYS: List[str] = ["WITH_TREND", "FLAT", "COUNTER_TREND"]

# ---------------------------------------------------------------------------
# Legacy shape detection and migration
# ---------------------------------------------------------------------------

# Legacy keys that can be deterministically migrated to canonical equivalents.
LEGACY_MIGRATABLE_KEYS: FrozenSet[str] = frozenset({"thresholds", "expiry", "buffer"})

# Legacy keys that have no canonical runtime consumer.
# They are reported explicitly and excluded from the migrated params.
LEGACY_UNCONSUMABLE_KEYS: FrozenSet[str] = frozenset({"weights", "gates"})

# All recognized legacy keys.
LEGACY_RECOGNIZED_KEYS: FrozenSet[str] = LEGACY_MIGRATABLE_KEYS | LEGACY_UNCONSUMABLE_KEYS


class MigrationResult(NamedTuple):
    """Result of a legacy parameter migration attempt."""
    params: Dict[str, Any]
    migrated_keys: List[str]
    dropped_keys: List[str]
    migration_errors: List[str]


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------

class ParamsValidationError(ValueError):
    pass


class ParamsMigrationError(ValueError):
    pass


# ---------------------------------------------------------------------------
# I/O helpers
# ---------------------------------------------------------------------------

def _read_json_fallback(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def load_algo_params(path: str = DEFAULT_PARAMS_PATH) -> Dict[str, Any]:
    """
    Load algo_params.json and validate it against the canonical contract.

    If the file contains a legacy parameter shape it is migrated deterministically
    before validation. Migration errors and unknown legacy fields are raised, never
    silently dropped.

    Raises ParamsValidationError if the file is missing, invalid, or fails
    canonical validation after migration.
    """
    if not os.path.exists(path):
        raise ParamsValidationError(f"algo params file not found: {path}")

    if storage and hasattr(storage, "load_json"):
        raw = storage.load_json(path, default=None)  # type: ignore
        if raw is None:
            raise ParamsValidationError(f"failed to load algo params (corrupted?): {path}")
    else:
        try:
            raw = _read_json_fallback(path)
        except json.JSONDecodeError as exc:
            raise ParamsValidationError(f"algo params file is not valid JSON: {exc}") from exc

    if not isinstance(raw, dict):
        raise ParamsValidationError("algo params must be a JSON object at the top level")

    params = raw

    # Detect and migrate legacy shape.
    if _is_legacy_shape(params):
        result = migrate_legacy_params(params)
        if result.migration_errors:
            raise ParamsMigrationError(
                f"legacy params migration failed: {result.migration_errors}"
            )
        params = result.params

    validate_algo_params(params)
    return params


def validate_algo_params(params: Dict[str, Any]) -> None:
    """
    Validate a params dict against the canonical contract.

    Raises ParamsValidationError on any violation:
    - missing required keys
    - unknown keys not in the canonical set
    - wrong types or out-of-range values
    - cross-field constraint violations
    - secret-like keys
    """
    if not isinstance(params, dict):
        raise ParamsValidationError("params must be a dict")

    _validate_no_unknown_top_level_keys(params)
    _validate_required_top_level_keys(params)
    _validate_algo_version(params)
    _validate_score_thresholds(params)
    _validate_expiry_limits_minutes(params)
    _validate_buffer_multipliers(params)

    # Optional blocks — validate only if present.
    if "strategy_v2" in params:
        _validate_strategy_v2(params)
    if "spike_filters" in params:
        _validate_spike_filters(params)
    if "sr_required_multiplier" in params:
        _validate_sr_required_multiplier(params)
    if "crypto_points_rounding" in params:
        _validate_crypto_points_rounding(params)
    if "trend_time_adjust" in params:
        _validate_trend_time_adjust(params)
    if "structure_factor" in params:
        _validate_structure_factor(params)

    _validate_no_forbidden_secrets(params)


def detect_legacy_shape(params: Dict[str, Any]) -> bool:
    """Return True if the params dict appears to use the pre-BATCH-02 legacy shape."""
    return _is_legacy_shape(params)


def migrate_legacy_params(params: Dict[str, Any]) -> MigrationResult:
    """
    Deterministically migrate a legacy parameter dict to the canonical shape.

    Migration rules:
    - thresholds.pre/confirm/open → score_thresholds.PRE/CONFIRM/OPEN (key rename only)
    - expiry.min_minutes/max_minutes → expiry_limits_minutes.min/max (key rename only)
    - buffer.modes.SMALL|MEDIUM|LARGE.atr_mult → buffer_multipliers.SMALL|MEDIUM|LARGE
    - weights → no canonical consumer; reported in dropped_keys
    - gates → no canonical consumer; reported in dropped_keys

    Ambiguous mappings (any non-recognized key in legacy shape) raise ParamsMigrationError.
    Unknown legacy fields are NEVER silently discarded.
    """
    if not isinstance(params, dict):
        raise ParamsMigrationError("legacy params must be a dict")

    result: Dict[str, Any] = {}
    migrated_keys: List[str] = []
    dropped_keys: List[str] = []
    errors: List[str] = []

    for key, value in params.items():
        if key in CANONICAL_TOP_LEVEL_KEYS:
            # Already canonical — carry forward.
            result[key] = value
        elif key == "thresholds":
            _migrate_thresholds(key, value, result, migrated_keys, errors)
        elif key == "expiry":
            _migrate_expiry(key, value, result, migrated_keys, errors)
        elif key == "buffer":
            _migrate_buffer(key, value, result, migrated_keys, errors)
        elif key in LEGACY_UNCONSUMABLE_KEYS:
            # Known legacy key with no canonical consumer — report, do not carry forward.
            dropped_keys.append(key)
        else:
            # Unrecognized key — ambiguous migration is rejected.
            errors.append(
                f"unrecognized key '{key}' has no canonical mapping and cannot be migrated"
            )

    return MigrationResult(
        params=result,
        migrated_keys=migrated_keys,
        dropped_keys=dropped_keys,
        migration_errors=errors,
    )


def compute_checksum(params: Dict[str, Any]) -> str:
    """
    Deterministic SHA-256 checksum for governance and audit logs.
    Uses canonical JSON serialization: sorted keys, compact separators.
    """
    canonical = json.dumps(params, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# Internal helpers — legacy detection
# ---------------------------------------------------------------------------

def _is_legacy_shape(params: Dict[str, Any]) -> bool:
    """Return True if the dict contains legacy keys indicating the pre-BATCH-02 shape."""
    # Legacy shape is indicated by presence of the old 'thresholds' key
    # and/or absence of the canonical 'score_thresholds' key.
    has_legacy_key = bool(LEGACY_RECOGNIZED_KEYS & set(params.keys()))
    has_canonical_thresholds = "score_thresholds" in params
    return has_legacy_key and not has_canonical_thresholds


# ---------------------------------------------------------------------------
# Internal helpers — migration
# ---------------------------------------------------------------------------

def _migrate_thresholds(
    key: str,
    value: Any,
    result: Dict[str, Any],
    migrated_keys: List[str],
    errors: List[str],
) -> None:
    if not isinstance(value, dict):
        errors.append(f"legacy '{key}' must be a dict")
        return
    score_thresholds: Dict[str, Any] = {}
    unknown: List[str] = []
    mapping = {"pre": "PRE", "confirm": "CONFIRM", "open": "OPEN"}
    for sub_key, sub_val in value.items():
        canonical_sub = mapping.get(sub_key.lower())
        if canonical_sub is not None:
            score_thresholds[canonical_sub] = sub_val
        else:
            unknown.append(sub_key)
    if unknown:
        errors.append(
            f"legacy 'thresholds' contains unrecognized sub-keys with no canonical mapping: {unknown}"
        )
        return
    result["score_thresholds"] = score_thresholds
    migrated_keys.append("thresholds")


def _migrate_expiry(
    key: str,
    value: Any,
    result: Dict[str, Any],
    migrated_keys: List[str],
    errors: List[str],
) -> None:
    if not isinstance(value, dict):
        errors.append(f"legacy '{key}' must be a dict")
        return
    expiry: Dict[str, Any] = {}
    unknown: List[str] = []
    mapping = {"min_minutes": "min", "max_minutes": "max"}
    for sub_key, sub_val in value.items():
        canonical_sub = mapping.get(sub_key)
        if canonical_sub is not None:
            expiry[canonical_sub] = sub_val
        else:
            unknown.append(sub_key)
    if unknown:
        errors.append(
            f"legacy 'expiry' contains unrecognized sub-keys with no canonical mapping: {unknown}"
        )
        return
    result["expiry_limits_minutes"] = expiry
    migrated_keys.append("expiry")


def _migrate_buffer(
    key: str,
    value: Any,
    result: Dict[str, Any],
    migrated_keys: List[str],
    errors: List[str],
) -> None:
    if not isinstance(value, dict):
        errors.append(f"legacy '{key}' must be a dict")
        return
    modes = value.get("modes")
    if not isinstance(modes, dict):
        errors.append("legacy 'buffer.modes' must be a dict")
        return
    buffer_multipliers: Dict[str, Any] = {}
    unknown: List[str] = []
    for mode_key, mode_val in modes.items():
        if mode_key not in {"SMALL", "MEDIUM", "LARGE"}:
            unknown.append(mode_key)
            continue
        if not isinstance(mode_val, dict):
            errors.append(f"legacy 'buffer.modes.{mode_key}' must be a dict")
            return
        atr_mult = mode_val.get("atr_mult")
        if atr_mult is None:
            errors.append(f"legacy 'buffer.modes.{mode_key}' missing 'atr_mult'")
            return
        unknown_mode_keys = [k for k in mode_val if k != "atr_mult"]
        if unknown_mode_keys:
            errors.append(
                f"legacy 'buffer.modes.{mode_key}' has unrecognized sub-keys: {unknown_mode_keys}"
            )
            return
        buffer_multipliers[mode_key] = atr_mult
    if unknown:
        errors.append(
            f"legacy 'buffer.modes' contains unrecognized mode keys: {unknown}"
        )
        return
    extra_buffer_keys = [k for k in value if k != "modes"]
    if extra_buffer_keys:
        errors.append(
            f"legacy 'buffer' contains unrecognized keys beyond 'modes': {extra_buffer_keys}"
        )
        return
    result["buffer_multipliers"] = buffer_multipliers
    migrated_keys.append("buffer")


# ---------------------------------------------------------------------------
# Internal helpers — canonical validation
# ---------------------------------------------------------------------------

def _validate_no_unknown_top_level_keys(params: Dict[str, Any]) -> None:
    unknown = set(params.keys()) - CANONICAL_TOP_LEVEL_KEYS
    if unknown:
        raise ParamsValidationError(
            f"unknown top-level parameter keys not in canonical contract: {sorted(unknown)}"
        )


def _validate_required_top_level_keys(params: Dict[str, Any]) -> None:
    missing = [k for k in REQUIRED_TOP_LEVEL_KEYS if k not in params]
    if missing:
        raise ParamsValidationError(f"algo params missing required top-level keys: {missing}")


def _validate_algo_version(params: Dict[str, Any]) -> None:
    v = params.get("algo_version")
    if not isinstance(v, str) or not v.strip():
        raise ParamsValidationError("algo_version must be a non-empty string")


def _validate_score_thresholds(params: Dict[str, Any]) -> None:
    t = params["score_thresholds"]
    if not isinstance(t, dict):
        raise ParamsValidationError("score_thresholds must be an object")
    unknown = set(t.keys()) - {"PRE", "CONFIRM", "OPEN"}
    if unknown:
        raise ParamsValidationError(
            f"score_thresholds contains unknown keys: {sorted(unknown)}"
        )
    for name in ("PRE", "CONFIRM", "OPEN"):
        if name not in t:
            raise ParamsValidationError(f"score_thresholds missing key: {name}")
        val = t[name]
        if not _is_int(val):
            raise ParamsValidationError(f"score_thresholds.{name} must be an integer")
        if val < 0 or val > 100:
            raise ParamsValidationError(f"score_thresholds.{name} out of range [0, 100]")
    pre, confirm, open_ = t["PRE"], t["CONFIRM"], t["OPEN"]
    if not (pre <= confirm <= open_):
        raise ParamsValidationError(
            "score_thresholds hierarchy violated: must be PRE <= CONFIRM <= OPEN"
        )


def _validate_expiry_limits_minutes(params: Dict[str, Any]) -> None:
    e = params["expiry_limits_minutes"]
    if not isinstance(e, dict):
        raise ParamsValidationError("expiry_limits_minutes must be an object")
    unknown = set(e.keys()) - {"min", "max"}
    if unknown:
        raise ParamsValidationError(
            f"expiry_limits_minutes contains unknown keys: {sorted(unknown)}"
        )
    for name in ("min", "max"):
        if name not in e:
            raise ParamsValidationError(f"expiry_limits_minutes missing key: {name}")
    mn, mx = e["min"], e["max"]
    if not _is_int(mn) or not _is_int(mx):
        raise ParamsValidationError("expiry_limits_minutes.min and .max must be integers")
    if mn < 1:
        raise ParamsValidationError("expiry_limits_minutes.min must be >= 1")
    if mx < mn:
        raise ParamsValidationError("expiry_limits_minutes.max must be >= min")


def _validate_buffer_multipliers(params: Dict[str, Any]) -> None:
    b = params["buffer_multipliers"]
    if not isinstance(b, dict):
        raise ParamsValidationError("buffer_multipliers must be an object")
    unknown = set(b.keys()) - {"SMALL", "MEDIUM", "LARGE"}
    if unknown:
        raise ParamsValidationError(
            f"buffer_multipliers contains unknown keys: {sorted(unknown)}"
        )
    for mode in ("SMALL", "MEDIUM", "LARGE"):
        if mode not in b:
            raise ParamsValidationError(f"buffer_multipliers missing key: {mode}")
        val = b[mode]
        if not _is_number(val):
            raise ParamsValidationError(f"buffer_multipliers.{mode} must be a number")
        if val <= 0:
            raise ParamsValidationError(f"buffer_multipliers.{mode} must be > 0")


def _validate_strategy_v2(params: Dict[str, Any]) -> None:
    s = params["strategy_v2"]
    if not isinstance(s, dict):
        raise ParamsValidationError("strategy_v2 must be an object")
    known = set(STRATEGY_V2_KEYS) | {"min_avg_range"}
    unknown = set(s.keys()) - known
    if unknown:
        raise ParamsValidationError(f"strategy_v2 contains unknown keys: {sorted(unknown)}")
    for k in STRATEGY_V2_KEYS:
        if k == "min_avg_range":
            continue
        if k not in s:
            raise ParamsValidationError(f"strategy_v2 missing key: {k}")

    ema_fast = s.get("ema_fast")
    ema_slow = s.get("ema_slow")
    if not _is_int(ema_fast) or ema_fast < 2 or ema_fast > 500:
        raise ParamsValidationError("strategy_v2.ema_fast must be integer in [2, 500]")
    if not _is_int(ema_slow) or ema_slow < 2 or ema_slow > 1000:
        raise ParamsValidationError("strategy_v2.ema_slow must be integer in [2, 1000]")
    if ema_slow <= ema_fast:
        raise ParamsValidationError("strategy_v2.ema_slow must be > ema_fast")

    rsi_period = s.get("rsi_period")
    if not _is_int(rsi_period) or rsi_period < 2 or rsi_period > 100:
        raise ParamsValidationError("strategy_v2.rsi_period must be integer in [2, 100]")

    rsi_call = s.get("rsi_call")
    if not _is_number(rsi_call) or rsi_call <= 50.0 or rsi_call > 100.0:
        raise ParamsValidationError("strategy_v2.rsi_call must be a number in (50.0, 100.0]")

    rsi_put = s.get("rsi_put")
    if not _is_number(rsi_put) or rsi_put < 0.0 or rsi_put >= 50.0:
        raise ParamsValidationError("strategy_v2.rsi_put must be a number in [0.0, 50.0)")

    mar = s.get("min_avg_range")
    if mar is not None:
        if not isinstance(mar, dict):
            raise ParamsValidationError("strategy_v2.min_avg_range must be an object")
        unknown_mar = set(mar.keys()) - set(MIN_AVG_RANGE_KEYS)
        if unknown_mar:
            raise ParamsValidationError(
                f"strategy_v2.min_avg_range contains unknown keys: {sorted(unknown_mar)}"
            )
        for mk in MIN_AVG_RANGE_KEYS:
            if mk not in mar:
                raise ParamsValidationError(f"strategy_v2.min_avg_range missing key: {mk}")
            v = mar[mk]
            if not _is_number(v) or v <= 0:
                raise ParamsValidationError(
                    f"strategy_v2.min_avg_range.{mk} must be a number > 0"
                )


def _validate_spike_filters(params: Dict[str, Any]) -> None:
    sf = params["spike_filters"]
    if not isinstance(sf, dict):
        raise ParamsValidationError("spike_filters must be an object")
    unknown = set(sf.keys()) - set(SPIKE_FILTERS_KEYS)
    if unknown:
        raise ParamsValidationError(f"spike_filters contains unknown keys: {sorted(unknown)}")
    for k in SPIKE_FILTERS_KEYS:
        if k not in sf:
            raise ParamsValidationError(f"spike_filters missing key: {k}")
        v = sf[k]
        if not _is_number(v) or v <= 0:
            raise ParamsValidationError(f"spike_filters.{k} must be a number > 0")


def _validate_sr_required_multiplier(params: Dict[str, Any]) -> None:
    v = params["sr_required_multiplier"]
    if not _is_number(v) or v <= 0:
        raise ParamsValidationError("sr_required_multiplier must be a number > 0")


def _validate_crypto_points_rounding(params: Dict[str, Any]) -> None:
    v = params["crypto_points_rounding"]
    if not _is_number(v) or v < 0:
        raise ParamsValidationError("crypto_points_rounding must be a number >= 0")


def _validate_trend_time_adjust(params: Dict[str, Any]) -> None:
    tta = params["trend_time_adjust"]
    if not isinstance(tta, dict):
        raise ParamsValidationError("trend_time_adjust must be an object")
    unknown = set(tta.keys()) - set(TREND_TIME_ADJUST_KEYS)
    if unknown:
        raise ParamsValidationError(
            f"trend_time_adjust contains unknown keys: {sorted(unknown)}"
        )
    for k in TREND_TIME_ADJUST_KEYS:
        if k not in tta:
            raise ParamsValidationError(f"trend_time_adjust missing key: {k}")
        v = tta[k]
        if not _is_number(v) or v <= 0:
            raise ParamsValidationError(f"trend_time_adjust.{k} must be a number > 0")


def _validate_structure_factor(params: Dict[str, Any]) -> None:
    sf = params["structure_factor"]
    if not isinstance(sf, dict):
        raise ParamsValidationError("structure_factor must be an object")
    unknown = set(sf.keys()) - {"mult"}
    if unknown:
        raise ParamsValidationError(f"structure_factor contains unknown keys: {sorted(unknown)}")
    if "mult" not in sf:
        raise ParamsValidationError("structure_factor missing key: mult")
    v = sf["mult"]
    if not _is_number(v) or v <= 0:
        raise ParamsValidationError("structure_factor.mult must be a number > 0")


def _validate_no_forbidden_secrets(params: Dict[str, Any]) -> None:
    """Guard: reject config files that accidentally contain secret-like keys."""
    forbidden_keys = {"TELEGRAM_TOKEN", "API_KEY", "PASSWORD", "SECRET", "TOKEN"}
    found = _find_keys_case_insensitive(params, forbidden_keys)
    if found:
        raise ParamsValidationError(
            f"forbidden secret-like keys found in algo params: {sorted(found)}"
        )


# ---------------------------------------------------------------------------
# Internal helpers — type checks
# ---------------------------------------------------------------------------

def _find_keys_case_insensitive(obj: Any, forbidden: Any = None) -> set:
    """Find any keys (recursively) whose uppercased form contains any forbidden substring."""
    if forbidden is None:
        forbidden = set()
    hit: set = set()
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