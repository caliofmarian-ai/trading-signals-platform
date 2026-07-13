# BATCH_02_IMPLEMENTATION_REPORT

## Findings addressed
- GAP-004: Strategy parameter contract split across three incompatible schemas
- CON-007: Strategy reader, params loader, schema file, and config file use different key shapes

## Owner decision applied
OWNER-001 = B

## Changed files

### send/schema/params_schema.json
- Replaced informal schema with a full canonical type-annotation schema
- Removed undocumented `strategy_v2.scores` (CALL/PUT/NO_SIGNAL) which had no consumer in strategy_v2.py
- Added all strategy-consumed optional fields: `spike_filters`, `sr_required_multiplier`, `crypto_points_rounding`, `trend_time_adjust`, `structure_factor`
- Each field now includes: type, constraints, required flag, description, governing canonical spec reference

### send/config/algo_params.json
- Completely replaced legacy shape with canonical shape
- `algo_version` changed from `"1.0.0"` to `"2.0.0"`
- `thresholds.pre/confirm/open` → `score_thresholds.PRE/CONFIRM/OPEN`
- `expiry.min_minutes/max_minutes` → `expiry_limits_minutes.min/max`
- `buffer.modes.SMALL.atr_mult` etc. → `buffer_multipliers.SMALL/MEDIUM/LARGE` (flat floats)
- `weights` (key) → removed (no canonical consumer)
- `gates` (key) → removed (no canonical consumer)
- Added: `strategy_v2`, `spike_filters`, `sr_required_multiplier`, `crypto_points_rounding`, `trend_time_adjust`, `structure_factor`

### send/core/params_loader.py
Full rewrite:
- `ParamsValidationError` exception for validation failures
- `ParamsMigrationError` exception for migration failures
- `MigrationResult` NamedTuple: `(migrated_params, dropped_keys, migration_errors)`
- `CANONICAL_TOP_LEVEL_KEYS`, `REQUIRED_TOP_LEVEL_KEYS`, `OPTIONAL_TOP_LEVEL_KEYS` constants
- `LEGACY_MIGRATABLE_KEYS`, `LEGACY_UNCONSUMABLE_KEYS` constants
- `detect_legacy_shape(raw_dict)` → bool
- `migrate_legacy_params(raw_dict)` → MigrationResult (deterministic, testable, rejects ambiguous)
- `validate_algo_params(params_dict)` → validated dict (raises on invalid/unknown fields)
- `load_algo_params(path)` → validated dict (auto-detects legacy, migrates if needed, validates)
- `compute_checksum(params)` → hex string for state tracking

### send/core/admin_commands.py
- `_load_algo_params()` now calls `params_loader.load_algo_params()` (canonical path)
- `_save_algo_params_validated(updated_raw)` now calls `params_loader.validate_algo_params()` before writing, then `storage.save_json_atomic()` for atomic persistence; validation failure → exception, no write
- `_set_threshold(field, value)` now writes to `params["score_thresholds"][field.upper()]` — allowed fields: PRE/CONFIRM/OPEN only
- `_set_sr(multiplier)` now writes to `params["sr_required_multiplier"]` (float, range 0–10.0); was `params["sr_buffer"]` (absolute pips)
- `_set_spike(field, value)` now writes to `params["spike_filters"][field]` (field must be one of wick_body_ratio_max/range_z_max/jump_vs_atr_max)
- Removed `_safe_write_json()` non-atomic write path

### send/core/admin_views.py
- `render_strategy_status()` now reads `score_thresholds.PRE/CONFIRM/OPEN`, `sr_required_multiplier`, `spike_filters.wick_body_ratio_max/range_z_max/jump_vs_atr_max`
- `render_admin_home()` spike command help updated to show canonical field names

## Files not modified
- `send/core/strategy_v2.py` (authoritative parameter consumer — not changed)
- `send/core/storage.py` (from BATCH-01 — used as-is)
- `send/core/bot_service.py` (OWNER-002 deferred)

## Admin mutation command changes

| Command | Before | After |
|---|---|---|
| `/thresholds PRE 75` | wrote to `params["thresholds"]["pre"]` | writes to `params["score_thresholds"]["PRE"]` |
| `/thresholds MEGA 99` | wrote to `params["thresholds"]["mega"]` (unknown, accepted) | rejected: only PRE/CONFIRM/OPEN allowed |
| `/sr 0.001` | wrote to `params["sr_buffer"]` (0.0001–0.002 range) | rejected: range is 0–10.0 now |
| `/sr 1.5` | wrote to `params["sr_buffer"]` | writes to `params["sr_required_multiplier"]` |
| `/spike wick_ratio 8` | wrote to `params["spike"]["wick_ratio"]` | rejected: canonical field is wick_body_ratio_max |
| `/spike wick_body_ratio_max 8` | wrote to `params["spike"]["wick_body_ratio_max"]` | writes to `params["spike_filters"]["wick_body_ratio_max"]` |

## Tests created
File: `tests/batch_02/test_canonical_parameter_contract.py`  
51 tests total covering all 25 required scenarios from the problem statement.

See BATCH_02_CHANGED_FILES.md for test listing.

## Deferred
- OWNER-002: bot_service.py control-plane retirement
- OWNER-003: segmented config directories
- OWNER-004: trade temporal telemetry
