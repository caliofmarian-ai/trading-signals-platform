# BATCH_02_PARAMETER_FLOW_BEFORE

## Owner decision applied
OWNER-001 = B: Align config/loader/admin to the runtime strategy fields already implied by `params_schema.json` and `strategy_v2.py`.

## Pre-BATCH-02 Parameter Flow

### Persisted configuration (algo_params.json)
```json
{
  "algo_version": "1.0.0",
  "thresholds": { "pre": 40, "confirm": 60, "open": 80 },
  "weights": { "trend": 1.0, "momentum": 1.0 },
  "expiry": { "min_minutes": 2, "max_minutes": 10 },
  "buffer": { "modes": { "SMALL": {"atr_mult": 0.3}, "MEDIUM": {"atr_mult": 0.6}, "LARGE": {"atr_mult": 1.0} } },
  "gates": { "spike_filter": true, "sr_gate": true, "feasibility": true }
}
```

### Loader validation contract (params_loader.py)
- Required keys: `algo_version`, `thresholds`, `weights`, `expiry`, `buffer`, `gates`
- Validated nested: `thresholds.pre/confirm/open`, `expiry.min_minutes/max_minutes`, `buffer.modes.SMALL/MEDIUM/LARGE`
- No unknown-key rejection
- No atomic write

### Strategy consumption (strategy_v2.py)
Strategy read from params dict using DIFFERENT keys than what the loader validated:
- `params.get("strategy_v2", {})` → ema_fast, ema_slow, rsi_period, rsi_call, rsi_put, min_avg_range
- `params.get("score_thresholds", {})` → PRE, CONFIRM, OPEN (UPPERCASE)
- `params.get("expiry_limits_minutes", {})` → min, max
- `params.get("buffer_multipliers", {})` → SMALL, MEDIUM, LARGE (flat float values)
- `params.get("spike_filters", {})` → wick_body_ratio_max, range_z_max, jump_vs_atr_max
- `params.get("sr_required_multiplier", 1.5)` → float
- `params.get("trend_time_adjust", {})` → WITH_TREND, FLAT, COUNTER_TREND
- `params.get("structure_factor", {})` → mult

**Since algo_params.json did not contain any of these canonical keys, strategy_v2 was using HARDCODED DEFAULTS for all configurable parameters. The operator-visible config had zero effect on live strategy behavior.**

### Admin mutation (admin_commands.py)
- Wrote to `params["thresholds"]["pre/confirm/open"]` (not consumed by strategy)
- Wrote to `params["sr_buffer"]` (not consumed by strategy)
- Wrote to `params["spike"]["wick_ratio/atr_jump"]` (wrong key path — strategy reads spike_filters)
- Used non-atomic `_safe_write_json()` without validation
- Did not invoke `params_loader.validate_algo_params()` before writing

### Incompatible schema (params_schema.json)
- Declared `strategy_v2`, `buffer_multipliers`, `expiry_limits_minutes`, `score_thresholds`
- Did NOT match either the old algo_params.json shape or the loader validation keys
- Three completely different contracts in simultaneous use

### Admin views (admin_views.py)
- Read from `params["thresholds"]["pre/confirm/open"]` (legacy keys)
- Read from `params["sr_buffer"]` (legacy key)
- Read from `params["spike"]["wick_ratio/atr_jump"]` (legacy keys)

## Finding Summary
- GAP-004: Strategy parameter contract split across three incompatible schemas
- CON-007: Strategy reader, params loader, schema file, and config file use different key shapes
- Consequence: operator config changes had no effect on live strategy behavior
