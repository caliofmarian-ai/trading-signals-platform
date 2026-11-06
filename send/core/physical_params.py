"""Strict physical V3 parameters and explicit, backed-up V2 retirement."""
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path

from . import params_loader as legacy
from . import storage
from .market_history_policy import HISTORY_POLICY

POLICY = "PHYSICAL_ONLY_V3"
MARKET_KEYS = {"ema_fast", "ema_slow", "rsi_period", "min_avg_range"}


def physical_runtime_enabled():
    """Read-only policy discriminator for observer processes and admin views."""
    try:
        params = json.loads(Path(storage.config_path("algo_params.json")).read_text())
        return params.get("algo_version") == "3.0.0" and params.get("decision_policy") == POLICY
    except (OSError, ValueError, TypeError):
        return False


def validate_physical_params(params):
    required = {"algo_version", "decision_policy", "market_model", "expiry_limits_minutes", "buffer_multipliers"}
    allowed = required | {"history_policy"} | (set(legacy.OPTIONAL_TOP_LEVEL_KEYS) - {"strategy_v2"})
    if set(params) - allowed or required - set(params):
        raise legacy.ParamsValidationError("V3 parameter keys must be physical-only and complete")
    if params.get("algo_version") != "3.0.0" or params.get("decision_policy") != POLICY:
        raise legacy.ParamsValidationError("V3 physical policy/version mismatch")
    if params.get("history_policy", HISTORY_POLICY) != HISTORY_POLICY:
        raise legacy.ParamsValidationError("V3 history_policy is unsupported")
    model = params["market_model"]
    if not isinstance(model, dict) or set(model) != MARKET_KEYS:
        raise legacy.ParamsValidationError("V3 market_model requires only physical indicator parameters")
    for key, low, high in (("ema_fast", 2, 500), ("ema_slow", 2, 1000), ("rsi_period", 2, 100)):
        val = model[key]
        if isinstance(val, bool) or not isinstance(val, int) or not low <= val <= high:
            raise legacy.ParamsValidationError(f"market_model.{key} is invalid")
    if model["ema_slow"] <= model["ema_fast"]:
        raise legacy.ParamsValidationError("market_model.ema_slow must exceed ema_fast")
    ranges = model["min_avg_range"]
    if not isinstance(ranges, dict) or set(ranges) != set(legacy.MIN_AVG_RANGE_KEYS):
        raise legacy.ParamsValidationError("market_model.min_avg_range is incomplete")
    from math import isfinite
    if any(isinstance(v, bool) or not isinstance(v, (int, float)) or not isfinite(v) or v <= 0 for v in ranges.values()):
        raise legacy.ParamsValidationError("market_model.min_avg_range must be finite and positive")
    legacy._validate_expiry_limits_minutes(params)
    legacy._validate_buffer_multipliers(params)
    for key in ("spike_filters", "sr_required_multiplier", "crypto_points_rounding", "trend_time_adjust", "structure_factor"):
        if key in params:
            getattr(legacy, "_validate_" + key)(params)


def migrate_physical_params(params):
    """Preserve every existing physical parameter; delete scoring configuration."""
    legacy.validate_algo_params(params)
    if params.get("algo_version") != "2.0.0" or not isinstance(params.get("strategy_v2"), dict):
        raise legacy.ParamsValidationError("incompatible bundle: only complete validated V2 bundles can migrate to physical V3")
    result = deepcopy(params)
    result.pop("score_thresholds")
    strategy = result.pop("strategy_v2")
    result["market_model"] = {key: strategy[key] for key in MARKET_KEYS}
    result.update(algo_version="3.0.0", decision_policy=POLICY, history_policy=HISTORY_POLICY)
    validate_physical_params(result)
    return result


def load_physical_runtime_algo_params(path):
    from .runtime_param_gate import RuntimeParameterError
    try:
        with storage.with_lock("algo_params"):
            params = legacy.load_algo_params(path)
            if params.get("algo_version") == "3.0.0":
                validate_physical_params(params)
                if params.get("history_policy") == HISTORY_POLICY:
                    return params
                migrated = {**deepcopy(params), "history_policy": HISTORY_POLICY}
                prefix = "v3_before_recent_history_"
            else:
                migrated = migrate_physical_params(params)
                prefix = "v2_before_physical_v3_"
            original = Path(path).read_bytes()
            digest = sha256(original).hexdigest()
            backup = Path(path).parent / "policy_migrations" / (prefix + digest + ".json")
            if backup.exists() and backup.read_bytes() != original:
                raise ValueError("physical migration backup mismatch")
            if not backup.exists():
                backup.parent.mkdir(parents=True, exist_ok=True)
                with backup.open("xb") as handle:
                    handle.write(original)
                    handle.flush()
                    import os
                    os.fsync(handle.fileno())
            storage.save_json_atomic(str(path), migrated)
            verified = legacy.load_algo_params(path)
            if verified != migrated:
                raise ValueError("physical migration readback mismatch")
            print("TSP_PHYSICAL_V3_POLICY " + json.dumps({"decision_policy": POLICY,
                  "algo_version": "3.0.0", "scoring_enabled": False,
                  "history_policy": HISTORY_POLICY,
                  "migration_backup_sha256": digest}), flush=True)
            return verified
    except Exception as exc:
        raise RuntimeParameterError("Physical V3 parameters unavailable: " + str(exc)) from exc
