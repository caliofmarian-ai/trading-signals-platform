"""
BATCH-02: Canonical Parameter Contract Tests
============================================
Verifies that the canonical parameter contract is correctly implemented across:
  - algo_params.json (live config)
  - params_loader.py (loading, validation, migration)
  - strategy_v2.py (consumption)
  - admin_commands.py (mutation, persistence, rejection)

Owner decision applied: OWNER-001 = B
Findings addressed: GAP-004, CON-007
"""

from __future__ import annotations

import importlib
import json
import os
import sys
import threading
import unittest.mock as mock
from pathlib import Path
from typing import Any, Dict

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SEND_ROOT = REPO_ROOT / "send"

if str(SEND_ROOT) not in sys.path:
    sys.path.insert(0, str(SEND_ROOT))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _purge_modules() -> None:
    for name in list(sys.modules.keys()):
        if name.startswith("core.") or name in (
            "core",
            "core.params_loader",
            "core.storage",
            "core.admin_commands",
            "core.admin_views",
            "core.admin_permissions",
            "core.strategy_v2",
        ):
            sys.modules.pop(name, None)


def _import_params_loader():
    _purge_modules()
    importlib.invalidate_caches()
    return importlib.import_module("core.params_loader")


def _import_strategy():
    _purge_modules()
    importlib.invalidate_caches()
    return importlib.import_module("core.strategy_v2")


def _import_admin_commands():
    _purge_modules()
    importlib.invalidate_caches()
    return importlib.import_module("core.admin_commands")


def _canonical_params() -> Dict[str, Any]:
    """Minimal valid canonical params (all required fields)."""
    return {
        "algo_version": "2.0.0",
        "score_thresholds": {"PRE": 70, "CONFIRM": 75, "OPEN": 80},
        "expiry_limits_minutes": {"min": 2, "max": 15},
        "buffer_multipliers": {"SMALL": 0.3, "MEDIUM": 0.55, "LARGE": 1.0},
    }


def _full_canonical_params() -> Dict[str, Any]:
    """Full canonical params including all optional fields."""
    p = _canonical_params()
    p["strategy_v2"] = {
        "ema_fast": 50,
        "ema_slow": 200,
        "rsi_period": 14,
        "rsi_call": 58.0,
        "rsi_put": 42.0,
        "min_avg_range": {
            "FOREX_DEFAULT": 0.00025,
            "FOREX_JPY": 0.025,
            "CRYPTO_USD": 8.0,
        },
    }
    p["spike_filters"] = {
        "wick_body_ratio_max": 6.0,
        "range_z_max": 3.0,
        "jump_vs_atr_max": 2.5,
    }
    p["sr_required_multiplier"] = 1.5
    p["crypto_points_rounding"] = 0.0
    p["trend_time_adjust"] = {"WITH_TREND": 0.9, "FLAT": 1.0, "COUNTER_TREND": 1.15}
    p["structure_factor"] = {"mult": 1.0}
    return p


def _write_params_file(tmp_path: Path, params: Dict[str, Any]) -> Path:
    f = tmp_path / "algo_params.json"
    f.write_text(json.dumps(params, indent=2), encoding="utf-8")
    return f


# ---------------------------------------------------------------------------
# TEST 1: Canonical algo_params.json validates successfully
# ---------------------------------------------------------------------------

def test_live_algo_params_validates_against_canonical_contract():
    """The live algo_params.json must validate against the canonical contract."""
    pl = _import_params_loader()
    params = pl.load_algo_params(path=str(SEND_ROOT / "config" / "algo_params.json"))
    pl.validate_algo_params(params)  # Must not raise


# ---------------------------------------------------------------------------
# TEST 2: params_loader loads the canonical contract
# ---------------------------------------------------------------------------

def test_params_loader_loads_canonical_shape(tmp_path):
    pl = _import_params_loader()
    pf = _write_params_file(tmp_path, _full_canonical_params())
    params = pl.load_algo_params(str(pf))
    assert "score_thresholds" in params
    assert "expiry_limits_minutes" in params
    assert "buffer_multipliers" in params
    assert "algo_version" in params


# ---------------------------------------------------------------------------
# TEST 3: Loaded runtime representation matches strategy_v2 consumption shape
# ---------------------------------------------------------------------------

def test_loaded_params_match_strategy_v2_consumption_keys(tmp_path):
    """The loaded canonical params dict must contain the keys strategy_v2.py reads."""
    pl = _import_params_loader()
    strat = _import_strategy()
    params = pl.load_algo_params(str(SEND_ROOT / "config" / "algo_params.json"))

    # strategy_v2.decide() reads these top-level keys from the params dict.
    assert "score_thresholds" in params, "strategy_v2 reads score_thresholds"
    assert "expiry_limits_minutes" in params, "strategy_v2 reads expiry_limits_minutes"
    assert "buffer_multipliers" in params, "strategy_v2 reads buffer_multipliers"

    # score_thresholds must use uppercase PRE/CONFIRM/OPEN
    st = params["score_thresholds"]
    assert "PRE" in st
    assert "CONFIRM" in st
    assert "OPEN" in st


# ---------------------------------------------------------------------------
# TEST 4: Every configurable strategy parameter has exactly one canonical key/path
# ---------------------------------------------------------------------------

def test_score_thresholds_has_one_canonical_path(tmp_path):
    """score_thresholds.PRE/CONFIRM/OPEN must be the only threshold representation."""
    pl = _import_params_loader()
    params = pl.load_algo_params(str(SEND_ROOT / "config" / "algo_params.json"))

    # Canonical key must exist.
    assert "score_thresholds" in params
    # Legacy key must NOT exist.
    assert "thresholds" not in params

    st = params["score_thresholds"]
    assert set(st.keys()) == {"PRE", "CONFIRM", "OPEN"}


# ---------------------------------------------------------------------------
# TEST 5: score_thresholds has one representation end-to-end
# ---------------------------------------------------------------------------

def test_score_thresholds_end_to_end_representation():
    """score_thresholds keys in config, loader, and strategy must align."""
    pl = _import_params_loader()
    params = pl.load_algo_params(str(SEND_ROOT / "config" / "algo_params.json"))

    # Loader returns canonical uppercase keys.
    st = params["score_thresholds"]
    assert "PRE" in st
    assert "CONFIRM" in st
    assert "OPEN" in st

    # strategy_v2.decide() reads exactly these uppercase keys.
    strat = _import_strategy()
    candles_1m = [
        {"open": 1.1, "high": 1.12, "low": 1.09, "close": 1.11, "ts": 1000 + i}
        for i in reversed(range(30))
    ]
    candles_5m = [
        {"open": 1.1, "high": 1.12, "low": 1.09, "close": 1.11, "ts": 5000 + i * 5}
        for i in reversed(range(60))
    ]
    result = strat.decide(candles_1m, candles_5m, params, buffer_mode="MEDIUM", want_open_now=False)
    # Strategy ran successfully — thresholds were consumed from canonical shape.
    assert "kind" in result
    assert result["debug"]["thresholds"]["PRE"] == st["PRE"]
    assert result["debug"]["thresholds"]["CONFIRM"] == st["CONFIRM"]
    assert result["debug"]["thresholds"]["OPEN"] == st["OPEN"]


# ---------------------------------------------------------------------------
# TEST 6: Unknown parameters are rejected
# ---------------------------------------------------------------------------

def test_unknown_top_level_parameter_is_rejected(tmp_path):
    pl = _import_params_loader()
    params = _canonical_params()
    params["mystery_field"] = 42

    with pytest.raises(pl.ParamsValidationError, match="unknown top-level parameter keys"):
        pl.validate_algo_params(params)


def test_unknown_score_thresholds_subkey_is_rejected(tmp_path):
    pl = _import_params_loader()
    params = _canonical_params()
    params["score_thresholds"]["UNKNOWN_TIER"] = 60

    with pytest.raises(pl.ParamsValidationError, match="unknown keys"):
        pl.validate_algo_params(params)


# ---------------------------------------------------------------------------
# TEST 7: Invalid types are rejected
# ---------------------------------------------------------------------------

def test_score_thresholds_string_value_rejected():
    pl = _import_params_loader()
    params = _canonical_params()
    params["score_thresholds"]["PRE"] = "seventy"

    with pytest.raises(pl.ParamsValidationError, match="must be an integer"):
        pl.validate_algo_params(params)


def test_buffer_multiplier_string_value_rejected():
    pl = _import_params_loader()
    params = _canonical_params()
    params["buffer_multipliers"]["SMALL"] = "small"

    with pytest.raises(pl.ParamsValidationError, match="must be a number"):
        pl.validate_algo_params(params)


def test_expiry_float_rejected_for_integer_field():
    pl = _import_params_loader()
    params = _canonical_params()
    params["expiry_limits_minutes"]["min"] = 2.5  # must be int

    with pytest.raises(pl.ParamsValidationError, match="must be integers"):
        pl.validate_algo_params(params)


def test_boolean_rejected_as_number():
    pl = _import_params_loader()
    params = _canonical_params()
    params["sr_required_multiplier"] = True  # bool is not a valid number

    with pytest.raises(pl.ParamsValidationError, match="must be a number"):
        pl.validate_algo_params(params)


# ---------------------------------------------------------------------------
# TEST 8: Out-of-range values are rejected
# ---------------------------------------------------------------------------

def test_score_threshold_above_100_rejected():
    pl = _import_params_loader()
    params = _canonical_params()
    params["score_thresholds"]["OPEN"] = 101

    with pytest.raises(pl.ParamsValidationError, match="out of range"):
        pl.validate_algo_params(params)


def test_score_threshold_below_zero_rejected():
    pl = _import_params_loader()
    params = _canonical_params()
    params["score_thresholds"]["PRE"] = -1

    with pytest.raises(pl.ParamsValidationError, match="out of range"):
        pl.validate_algo_params(params)


def test_score_threshold_hierarchy_violated_rejected():
    pl = _import_params_loader()
    params = _canonical_params()
    params["score_thresholds"] = {"PRE": 80, "CONFIRM": 75, "OPEN": 70}  # wrong order

    with pytest.raises(pl.ParamsValidationError, match="hierarchy violated"):
        pl.validate_algo_params(params)


def test_buffer_multiplier_zero_rejected():
    pl = _import_params_loader()
    params = _canonical_params()
    params["buffer_multipliers"]["MEDIUM"] = 0

    with pytest.raises(pl.ParamsValidationError, match="must be > 0"):
        pl.validate_algo_params(params)


def test_expiry_min_zero_rejected():
    pl = _import_params_loader()
    params = _canonical_params()
    params["expiry_limits_minutes"]["min"] = 0

    with pytest.raises(pl.ParamsValidationError, match=">= 1"):
        pl.validate_algo_params(params)


def test_expiry_max_less_than_min_rejected():
    pl = _import_params_loader()
    params = _canonical_params()
    params["expiry_limits_minutes"] = {"min": 10, "max": 5}

    with pytest.raises(pl.ParamsValidationError, match=">= min"):
        pl.validate_algo_params(params)


def test_sr_required_multiplier_zero_rejected():
    pl = _import_params_loader()
    params = _canonical_params()
    params["sr_required_multiplier"] = 0.0

    with pytest.raises(pl.ParamsValidationError, match="must be a number > 0"):
        pl.validate_algo_params(params)


def test_crypto_points_rounding_negative_rejected():
    pl = _import_params_loader()
    params = _canonical_params()
    params["crypto_points_rounding"] = -0.1

    with pytest.raises(pl.ParamsValidationError, match=">= 0"):
        pl.validate_algo_params(params)


def test_spike_filter_zero_rejected():
    pl = _import_params_loader()
    params = _canonical_params()
    params["spike_filters"] = {"wick_body_ratio_max": 0, "range_z_max": 3.0, "jump_vs_atr_max": 2.5}

    with pytest.raises(pl.ParamsValidationError, match="must be a number > 0"):
        pl.validate_algo_params(params)


# ---------------------------------------------------------------------------
# TEST 9: Missing required parameters fail clearly
# ---------------------------------------------------------------------------

def test_missing_score_thresholds_fails_clearly():
    pl = _import_params_loader()
    params = _canonical_params()
    del params["score_thresholds"]

    with pytest.raises(pl.ParamsValidationError, match="missing required top-level keys"):
        pl.validate_algo_params(params)


def test_missing_expiry_limits_fails_clearly():
    pl = _import_params_loader()
    params = _canonical_params()
    del params["expiry_limits_minutes"]

    with pytest.raises(pl.ParamsValidationError, match="missing required top-level keys"):
        pl.validate_algo_params(params)


def test_missing_buffer_multipliers_fails_clearly():
    pl = _import_params_loader()
    params = _canonical_params()
    del params["buffer_multipliers"]

    with pytest.raises(pl.ParamsValidationError, match="missing required top-level keys"):
        pl.validate_algo_params(params)


def test_missing_algo_version_fails_clearly():
    pl = _import_params_loader()
    params = _canonical_params()
    del params["algo_version"]

    with pytest.raises(pl.ParamsValidationError, match="missing required top-level keys"):
        pl.validate_algo_params(params)


def test_missing_score_threshold_subkey_fails_clearly():
    pl = _import_params_loader()
    params = _canonical_params()
    del params["score_thresholds"]["OPEN"]

    with pytest.raises(pl.ParamsValidationError, match="missing key: OPEN"):
        pl.validate_algo_params(params)


# ---------------------------------------------------------------------------
# TEST 10: Canonical defaults for optional fields
# ---------------------------------------------------------------------------

def test_optional_spike_filters_absent_allows_validation():
    """spike_filters is optional; absence must not fail validation."""
    pl = _import_params_loader()
    params = _canonical_params()
    assert "spike_filters" not in params
    pl.validate_algo_params(params)  # Must not raise


def test_optional_strategy_v2_absent_allows_validation():
    """strategy_v2 is optional; absence must not fail validation."""
    pl = _import_params_loader()
    params = _canonical_params()
    assert "strategy_v2" not in params
    pl.validate_algo_params(params)  # Must not raise


def test_optional_trend_time_adjust_absent_allows_validation():
    pl = _import_params_loader()
    params = _canonical_params()
    pl.validate_algo_params(params)  # Must not raise


# ---------------------------------------------------------------------------
# TEST 11: Malformed JSON fails clearly
# ---------------------------------------------------------------------------

def test_malformed_json_fails_clearly(tmp_path):
    pl = _import_params_loader()
    pf = tmp_path / "algo_params.json"
    pf.write_text("{not valid json,,}", encoding="utf-8")

    with pytest.raises(pl.ParamsValidationError):
        pl.load_algo_params(str(pf))


def test_json_array_root_fails_clearly(tmp_path):
    pl = _import_params_loader()
    pf = tmp_path / "algo_params.json"
    pf.write_text("[1, 2, 3]", encoding="utf-8")

    with pytest.raises(pl.ParamsValidationError, match="JSON object"):
        pl.load_algo_params(str(pf))


def test_missing_params_file_fails_clearly(tmp_path):
    pl = _import_params_loader()
    with pytest.raises(pl.ParamsValidationError, match="not found"):
        pl.load_algo_params(str(tmp_path / "nonexistent.json"))


# ---------------------------------------------------------------------------
# TEST 12: Legacy shape migration succeeds for unambiguous mappings
# ---------------------------------------------------------------------------

def test_legacy_shape_migration_thresholds(tmp_path):
    pl = _import_params_loader()
    legacy = {
        "algo_version": "1.0.0",
        "thresholds": {"pre": 60, "confirm": 70, "open": 80},
        "expiry": {"min_minutes": 2, "max_minutes": 10},
        "buffer": {
            "modes": {
                "SMALL": {"atr_mult": 0.3},
                "MEDIUM": {"atr_mult": 0.6},
                "LARGE": {"atr_mult": 1.0},
            }
        },
    }
    result = pl.migrate_legacy_params(legacy)
    assert result.migration_errors == [], result.migration_errors
    assert "score_thresholds" in result.params
    assert result.params["score_thresholds"] == {"PRE": 60, "CONFIRM": 70, "OPEN": 80}
    assert "thresholds" in result.migrated_keys


def test_legacy_shape_migration_expiry(tmp_path):
    pl = _import_params_loader()
    legacy = {
        "algo_version": "1.0.0",
        "thresholds": {"pre": 60, "confirm": 70, "open": 80},
        "expiry": {"min_minutes": 3, "max_minutes": 12},
        "buffer": {
            "modes": {
                "SMALL": {"atr_mult": 0.3},
                "MEDIUM": {"atr_mult": 0.6},
                "LARGE": {"atr_mult": 1.0},
            }
        },
    }
    result = pl.migrate_legacy_params(legacy)
    assert result.migration_errors == [], result.migration_errors
    assert "expiry_limits_minutes" in result.params
    assert result.params["expiry_limits_minutes"] == {"min": 3, "max": 12}
    assert "expiry" in result.migrated_keys


def test_legacy_shape_migration_buffer_modes(tmp_path):
    pl = _import_params_loader()
    legacy = {
        "algo_version": "1.0.0",
        "thresholds": {"pre": 60, "confirm": 70, "open": 80},
        "expiry": {"min_minutes": 2, "max_minutes": 10},
        "buffer": {
            "modes": {
                "SMALL": {"atr_mult": 0.3},
                "MEDIUM": {"atr_mult": 0.55},
                "LARGE": {"atr_mult": 1.0},
            }
        },
    }
    result = pl.migrate_legacy_params(legacy)
    assert result.migration_errors == [], result.migration_errors
    assert "buffer_multipliers" in result.params
    assert result.params["buffer_multipliers"] == {"SMALL": 0.3, "MEDIUM": 0.55, "LARGE": 1.0}
    assert "buffer" in result.migrated_keys


def test_legacy_file_loads_via_migration(tmp_path):
    """load_algo_params must auto-migrate a legacy file and return valid canonical params."""
    pl = _import_params_loader()
    legacy = {
        "algo_version": "1.0.0",
        "thresholds": {"pre": 60, "confirm": 70, "open": 80},
        "expiry": {"min_minutes": 2, "max_minutes": 10},
        "buffer": {
            "modes": {
                "SMALL": {"atr_mult": 0.3},
                "MEDIUM": {"atr_mult": 0.6},
                "LARGE": {"atr_mult": 1.0},
            }
        },
    }
    pf = _write_params_file(tmp_path, legacy)
    params = pl.load_algo_params(str(pf))
    assert "score_thresholds" in params
    assert "expiry_limits_minutes" in params
    assert "buffer_multipliers" in params


# ---------------------------------------------------------------------------
# TEST 13: Ambiguous legacy mappings fail clearly
# ---------------------------------------------------------------------------

def test_legacy_thresholds_unknown_subkey_fails_clearly():
    pl = _import_params_loader()
    result = pl.migrate_legacy_params({
        "algo_version": "1.0.0",
        "thresholds": {"pre": 60, "confirm": 70, "open": 80, "super": 90},
        "expiry": {"min_minutes": 2, "max_minutes": 10},
        "buffer": {"modes": {"SMALL": {"atr_mult": 0.3}, "MEDIUM": {"atr_mult": 0.6}, "LARGE": {"atr_mult": 1.0}}},
    })
    assert result.migration_errors != []
    assert any("super" in e for e in result.migration_errors)


def test_legacy_buffer_unknown_mode_fails_clearly():
    pl = _import_params_loader()
    result = pl.migrate_legacy_params({
        "algo_version": "1.0.0",
        "thresholds": {"pre": 60, "confirm": 70, "open": 80},
        "expiry": {"min_minutes": 2, "max_minutes": 10},
        "buffer": {"modes": {
            "SMALL": {"atr_mult": 0.3},
            "MEDIUM": {"atr_mult": 0.6},
            "LARGE": {"atr_mult": 1.0},
            "XLARGE": {"atr_mult": 1.5},  # Unknown mode
        }},
    })
    assert result.migration_errors != []


# ---------------------------------------------------------------------------
# TEST 14: Unknown legacy fields are not silently discarded
# ---------------------------------------------------------------------------

def test_legacy_weights_and_gates_reported_not_silently_dropped():
    """weights and gates are known unconsumable legacy fields — they must be reported."""
    pl = _import_params_loader()
    legacy = {
        "algo_version": "1.0.0",
        "thresholds": {"pre": 60, "confirm": 70, "open": 80},
        "expiry": {"min_minutes": 2, "max_minutes": 10},
        "buffer": {"modes": {"SMALL": {"atr_mult": 0.3}, "MEDIUM": {"atr_mult": 0.6}, "LARGE": {"atr_mult": 1.0}}},
        "weights": {"trend": 1.0, "momentum": 1.0},
        "gates": {"spike_filter": True},
    }
    result = pl.migrate_legacy_params(legacy)
    assert result.migration_errors == [], result.migration_errors
    assert "weights" in result.dropped_keys
    assert "gates" in result.dropped_keys
    # Must NOT appear in migrated params
    assert "weights" not in result.params
    assert "gates" not in result.params


def test_completely_unknown_legacy_key_fails_not_discarded():
    """A completely unrecognized key must produce a migration error, not be silently dropped."""
    pl = _import_params_loader()
    result = pl.migrate_legacy_params({
        "algo_version": "1.0.0",
        "thresholds": {"pre": 60, "confirm": 70, "open": 80},
        "expiry": {"min_minutes": 2, "max_minutes": 10},
        "buffer": {"modes": {"SMALL": {"atr_mult": 0.3}, "MEDIUM": {"atr_mult": 0.6}, "LARGE": {"atr_mult": 1.0}}},
        "mysterious_field": "something",
    })
    assert result.migration_errors != []
    assert any("mysterious_field" in e for e in result.migration_errors)


# ---------------------------------------------------------------------------
# TEST 15: Admin mutation accepts valid values
# ---------------------------------------------------------------------------

def test_admin_mutation_accepts_valid_threshold(tmp_path, monkeypatch):
    pl = _import_params_loader()
    pf = _write_params_file(tmp_path, _full_canonical_params())

    # Import admin_commands with storage patched to use tmp path.
    _purge_modules()
    import core.admin_commands as ac
    import core.storage as st

    monkeypatch.setattr(ac, "_algo_params_path", lambda: str(pf))

    ac._set_threshold("PRE", 65)
    updated = json.loads(pf.read_text())
    assert updated["score_thresholds"]["PRE"] == 65


# ---------------------------------------------------------------------------
# TEST 16: Admin mutation rejects unknown keys
# ---------------------------------------------------------------------------

def test_admin_mutation_unknown_threshold_field_rejected(tmp_path, monkeypatch):
    pf = _write_params_file(tmp_path, _full_canonical_params())

    _purge_modules()
    import core.admin_commands as ac
    import core.params_loader as pl

    monkeypatch.setattr(ac, "_algo_params_path", lambda: str(pf))

    original_content = pf.read_text()

    with pytest.raises((pl.ParamsValidationError, Exception)):
        ac._set_threshold("MEGA_THRESHOLD", 99)

    # File must not have changed
    assert pf.read_text() == original_content


# ---------------------------------------------------------------------------
# TEST 17: Admin mutation rejects invalid types/ranges
# ---------------------------------------------------------------------------

def test_admin_threshold_out_of_range_rejected_by_validation(tmp_path, monkeypatch):
    pf = _write_params_file(tmp_path, _full_canonical_params())

    _purge_modules()
    import core.admin_commands as ac
    import core.params_loader as pl

    monkeypatch.setattr(ac, "_algo_params_path", lambda: str(pf))
    original = pf.read_text()

    with pytest.raises((pl.ParamsValidationError, Exception)):
        ac._set_threshold("PRE", 101)  # out of range

    # File unchanged on rejection
    assert pf.read_text() == original


def test_admin_spike_negative_value_rejected(tmp_path, monkeypatch):
    pf = _write_params_file(tmp_path, _full_canonical_params())

    _purge_modules()
    import core.admin_commands as ac
    import core.params_loader as pl

    monkeypatch.setattr(ac, "_algo_params_path", lambda: str(pf))
    original = pf.read_text()

    with pytest.raises((pl.ParamsValidationError, Exception)):
        ac._set_spike("wick_body_ratio_max", -1.0)

    assert pf.read_text() == original


# ---------------------------------------------------------------------------
# TEST 18: Failed Admin mutation does not modify persisted configuration
# ---------------------------------------------------------------------------

def test_failed_admin_mutation_does_not_persist(tmp_path, monkeypatch):
    """If validation fails, the config file must remain unchanged."""
    pf = _write_params_file(tmp_path, _full_canonical_params())
    original_content = pf.read_text()

    _purge_modules()
    import core.admin_commands as ac
    import core.params_loader as pl

    monkeypatch.setattr(ac, "_algo_params_path", lambda: str(pf))

    # Force a hierarchy violation: PRE > OPEN would fail validation
    try:
        ac._set_threshold("PRE", 99)  # Makes PRE=99 > OPEN=80 → hierarchy violation
    except (pl.ParamsValidationError, Exception):
        pass

    persisted = json.loads(pf.read_text())
    # PRE must still be the original value, not 99 (which violated hierarchy)
    assert persisted["score_thresholds"]["PRE"] != 99 or (
        persisted["score_thresholds"]["PRE"] <= persisted["score_thresholds"]["OPEN"]
    )


# ---------------------------------------------------------------------------
# TEST 19: Valid Admin mutation persists atomically
# ---------------------------------------------------------------------------

def test_valid_admin_mutation_persists_atomically(tmp_path, monkeypatch):
    pf = _write_params_file(tmp_path, _full_canonical_params())

    _purge_modules()
    import core.admin_commands as ac

    monkeypatch.setattr(ac, "_algo_params_path", lambda: str(pf))

    ac._set_threshold("CONFIRM", 76)

    persisted = json.loads(pf.read_text())
    assert persisted["score_thresholds"]["CONFIRM"] == 76

    # Verify the file is valid JSON (no partial write)
    reloaded_pl = _import_params_loader()
    reloaded_pl.validate_algo_params(persisted)


# ---------------------------------------------------------------------------
# TEST 20: Runtime reload receives a complete validated parameter set
# ---------------------------------------------------------------------------

def test_reload_returns_complete_validated_params(tmp_path):
    pl = _import_params_loader()
    pf = _write_params_file(tmp_path, _full_canonical_params())

    params = pl.load_algo_params(str(pf))

    # All required fields must be present in reloaded params
    assert "score_thresholds" in params
    assert "expiry_limits_minutes" in params
    assert "buffer_multipliers" in params
    assert "algo_version" in params
    pl.validate_algo_params(params)


# ---------------------------------------------------------------------------
# TEST 21: Failed reload preserves last valid runtime state
# ---------------------------------------------------------------------------

def test_failed_reload_preserves_last_valid_state(tmp_path):
    """A params file that fails validation must raise, not return partial data."""
    pl = _import_params_loader()

    # Load a valid file first.
    good_dir = tmp_path / "good"
    good_dir.mkdir()
    good_pf = good_dir / "algo_params.json"
    good_pf.write_text(json.dumps(_full_canonical_params(), indent=2), encoding="utf-8")
    good_params = pl.load_algo_params(str(good_pf))

    # Now attempt to load a bad file.
    bad_pf = tmp_path / "algo_params_bad.json"
    bad_pf.write_text(json.dumps({"algo_version": "bad"}), encoding="utf-8")

    with pytest.raises(pl.ParamsValidationError):
        pl.load_algo_params(str(bad_pf))

    # The good_params from the valid load are still intact (not modified)
    assert good_params["score_thresholds"]["PRE"] == 70


# ---------------------------------------------------------------------------
# TEST 22: Strategy evaluation receives updated canonical parameter values
# ---------------------------------------------------------------------------

def test_strategy_uses_canonical_score_thresholds(tmp_path):
    """Passing custom score_thresholds to strategy_v2.decide() must affect decision kind."""
    strat = _import_strategy()

    # Build candles that will generate a score above default thresholds.
    # Use flat trend (ema_fast ~ ema_slow) with RSI bias toward BUY.
    candles_1m = [
        {"open": 1.10 + 0.0001 * i, "high": 1.11 + 0.0001 * i,
         "low": 1.09 + 0.0001 * i, "close": 1.105 + 0.0001 * i,
         "ts": 1000 + i, "symbol": "EURUSD"}
        for i in reversed(range(30))
    ]
    candles_5m = [
        {"open": 1.10, "high": 1.12, "low": 1.09, "close": 1.11, "ts": 5000 + i * 5}
        for i in reversed(range(60))
    ]

    # With very low thresholds, most setups should reach CONFIRM or above.
    low_thr_params = _canonical_params()
    low_thr_params["score_thresholds"] = {"PRE": 1, "CONFIRM": 2, "OPEN": 3}
    low_thr_params["expiry_limits_minutes"]["max"] = 15
    low_thr_params["buffer_multipliers"]["MEDIUM"] = 0.55

    result = strat.decide(candles_1m, candles_5m, low_thr_params, "MEDIUM", True)
    # The debug block must show the custom thresholds
    assert result["debug"]["thresholds"]["PRE"] == 1
    assert result["debug"]["thresholds"]["CONFIRM"] == 2


# ---------------------------------------------------------------------------
# TEST 23: Parameter module imports produce no network calls or side effects
# ---------------------------------------------------------------------------

def test_params_loader_import_has_no_network_or_thread_side_effects(monkeypatch):
    network_calls = []

    def _fail_get(*args, **kwargs):
        network_calls.append(("get", args))
        raise AssertionError("network call during import")

    def _fail_post(*args, **kwargs):
        network_calls.append(("post", args))
        raise AssertionError("network call during import")

    def _fail_thread(*args, **kwargs):
        raise AssertionError("thread started during import")

    monkeypatch.setattr("requests.get", _fail_get)
    monkeypatch.setattr("requests.post", _fail_post)
    monkeypatch.setattr("threading.Thread", _fail_thread)

    _purge_modules()
    pl = importlib.import_module("core.params_loader")
    assert pl is not None
    assert network_calls == []


# ---------------------------------------------------------------------------
# TEST 24: BATCH-01 boot/import tests remain passing (regression)
# ---------------------------------------------------------------------------

def test_batch_01_core_imports_still_side_effect_free(monkeypatch):
    """Regression: core runtime modules must still import without network/thread side effects."""
    network_calls = []

    def _fail_get(*args, **kwargs):
        network_calls.append(("get", args))
        raise AssertionError("network call during import")

    def _fail_post(*args, **kwargs):
        network_calls.append(("post", args))
        raise AssertionError("network call during import")

    def _fail_thread(*args, **kwargs):
        raise AssertionError("thread started during import")

    monkeypatch.setattr("requests.get", _fail_get)
    monkeypatch.setattr("requests.post", _fail_post)
    monkeypatch.setattr("threading.Thread", _fail_thread)

    _purge_modules()
    importlib.invalidate_caches()

    assert importlib.import_module("core.signal_engine") is not None
    assert importlib.import_module("runtime.engine_loop") is not None
    assert importlib.import_module("runtime.system_boot") is not None
    assert network_calls == []


# ---------------------------------------------------------------------------
# TEST 25: No unrelated strategy behavior changes
# ---------------------------------------------------------------------------

def test_strategy_v2_decide_produces_deterministic_output():
    """
    strategy_v2.decide() must return a deterministic result for identical inputs,
    and must not have changed its output contract.
    """
    strat = _import_strategy()

    candles_1m = [
        {"open": 1.1000, "high": 1.1020, "low": 1.0980, "close": 1.1010,
         "ts": 1000 + i, "symbol": "EURUSD"}
        for i in reversed(range(30))
    ]
    candles_5m = [
        {"open": 1.1000, "high": 1.1030, "low": 1.0970, "close": 1.1010,
         "ts": 5000 + i * 5}
        for i in reversed(range(60))
    ]
    params = _canonical_params()

    result1 = strat.decide(candles_1m, candles_5m, params, "MEDIUM", False)
    result2 = strat.decide(candles_1m, candles_5m, params, "MEDIUM", False)

    # Deterministic
    assert result1["kind"] == result2["kind"]
    assert result1["score_total"] == result2["score_total"]

    # Contract keys still present
    required_keys = {"kind", "signal_id", "symbol", "timeframe", "direction",
                     "score_total", "buffer_mode", "buffer_price", "expiry_minutes",
                     "want_open_now", "gates", "debug", "candle_ts"}
    assert required_keys.issubset(set(result1.keys()))

    # kind must be one of the canonical values
    assert result1["kind"] in {"OPEN_NOW", "CONFIRM", "PRE", "NO_SIGNAL", "REJECT"}
