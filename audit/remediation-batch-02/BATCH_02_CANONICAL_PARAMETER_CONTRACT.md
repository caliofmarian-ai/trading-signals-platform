# BATCH_02_CANONICAL_PARAMETER_CONTRACT

## Owner decision
OWNER-001 = B: Align config/loader/admin to the runtime strategy fields.

## Canonical Parameter Contract (post-BATCH-02)

### Required parameters (must be present in every algo_params.json)

| Canonical key | Path | Type | Range/Constraint | Default | Mutable via Admin | Persistence | Reload | Canon ref |
|---|---|---|---|---|---|---|---|---|
| `algo_version` | top-level | string | non-empty | — | no | config file | on load | STRATEGY_PARAMETER_CONTROL_SPEC |
| `score_thresholds.PRE` | score_thresholds.PRE | integer | [0, 100], ≤ CONFIRM | 70 | yes (/thresholds) | atomic JSON | immediate | STRATEGY_PARAMETER_CONTROL_SPEC |
| `score_thresholds.CONFIRM` | score_thresholds.CONFIRM | integer | [0, 100], ≥ PRE ≤ OPEN | 75 | yes (/thresholds) | atomic JSON | immediate | STRATEGY_PARAMETER_CONTROL_SPEC |
| `score_thresholds.OPEN` | score_thresholds.OPEN | integer | [0, 100], ≥ CONFIRM | 80 | yes (/thresholds) | atomic JSON | immediate | STRATEGY_PARAMETER_CONTROL_SPEC |
| `expiry_limits_minutes.min` | expiry_limits_minutes.min | integer | ≥ 1, ≤ max | 2 | no | config file | on load | ALGO_SPEC |
| `expiry_limits_minutes.max` | expiry_limits_minutes.max | integer | ≥ 1, ≥ min | 15 | no | config file | on load | ALGO_SPEC |
| `buffer_multipliers.SMALL` | buffer_multipliers.SMALL | number | > 0 | 0.3 | no | config file | on load | ALGO_SPEC |
| `buffer_multipliers.MEDIUM` | buffer_multipliers.MEDIUM | number | > 0 | 0.55 | no | config file | on load | ALGO_SPEC |
| `buffer_multipliers.LARGE` | buffer_multipliers.LARGE | number | > 0 | 1.0 | no | config file | on load | ALGO_SPEC |

### Optional parameters (may be absent; strategy uses internal defaults)

| Canonical key | Path | Type | Range/Constraint | Default | Mutable via Admin | Persistence | Reload | Canon ref |
|---|---|---|---|---|---|---|---|---|
| `strategy_v2.ema_fast` | strategy_v2.ema_fast | integer | [2, 500], < ema_slow | 50 | no | config file | on load | ALGO_SPEC |
| `strategy_v2.ema_slow` | strategy_v2.ema_slow | integer | [2, 1000], > ema_fast | 200 | no | config file | on load | ALGO_SPEC |
| `strategy_v2.rsi_period` | strategy_v2.rsi_period | integer | [2, 100] | 14 | no | config file | on load | ALGO_SPEC |
| `strategy_v2.rsi_call` | strategy_v2.rsi_call | number | (50.0, 100.0] | 58.0 | no | config file | on load | ALGO_SPEC |
| `strategy_v2.rsi_put` | strategy_v2.rsi_put | number | [0.0, 50.0) | 42.0 | no | config file | on load | ALGO_SPEC |
| `strategy_v2.min_avg_range.FOREX_DEFAULT` | strategy_v2.min_avg_range.FOREX_DEFAULT | number | > 0 | 0.00025 | no | config file | on load | ALGO_SPEC |
| `strategy_v2.min_avg_range.FOREX_JPY` | strategy_v2.min_avg_range.FOREX_JPY | number | > 0 | 0.025 | no | config file | on load | ALGO_SPEC |
| `strategy_v2.min_avg_range.CRYPTO_USD` | strategy_v2.min_avg_range.CRYPTO_USD | number | > 0 | 8.0 | no | config file | on load | ALGO_SPEC |
| `spike_filters.wick_body_ratio_max` | spike_filters.wick_body_ratio_max | number | > 0 | 6.0 | yes (/spike) | atomic JSON | immediate | STRATEGY_PARAMETER_CONTROL_SPEC |
| `spike_filters.range_z_max` | spike_filters.range_z_max | number | > 0 | 3.0 | yes (/spike) | atomic JSON | immediate | STRATEGY_PARAMETER_CONTROL_SPEC |
| `spike_filters.jump_vs_atr_max` | spike_filters.jump_vs_atr_max | number | > 0 | 2.5 | yes (/spike) | atomic JSON | immediate | STRATEGY_PARAMETER_CONTROL_SPEC |
| `sr_required_multiplier` | sr_required_multiplier | number | > 0, ≤ 10.0 | 1.5 | yes (/sr) | atomic JSON | immediate | STRATEGY_PARAMETER_CONTROL_SPEC |
| `crypto_points_rounding` | crypto_points_rounding | number | ≥ 0 | 0.0 | no | config file | on load | ALGO_SPEC |
| `trend_time_adjust.WITH_TREND` | trend_time_adjust.WITH_TREND | number | > 0 | 0.9 | no | config file | on load | ALGO_SPEC |
| `trend_time_adjust.FLAT` | trend_time_adjust.FLAT | number | > 0 | 1.0 | no | config file | on load | ALGO_SPEC |
| `trend_time_adjust.COUNTER_TREND` | trend_time_adjust.COUNTER_TREND | number | > 0 | 1.15 | no | config file | on load | ALGO_SPEC |
| `structure_factor.mult` | structure_factor.mult | number | > 0 | 1.0 | no | config file | on load | ALGO_SPEC |

## score_thresholds canonical representation

There is exactly ONE canonical representation of score thresholds:
- Key: `score_thresholds`
- Sub-keys: `PRE`, `CONFIRM`, `OPEN` (uppercase integers)
- Location: top-level in algo_params.json
- Consumer: `strategy_v2.py:310-313`
- Validator: `params_loader._validate_score_thresholds()`
- Admin mutator: `admin_commands._set_threshold()`

## Legacy migration support

The following legacy → canonical mappings are deterministically supported:

| Legacy key | Legacy sub-key | Canonical key | Canonical sub-key | Migration rule |
|---|---|---|---|---|
| `thresholds` | `pre` | `score_thresholds` | `PRE` | rename only, value unchanged |
| `thresholds` | `confirm` | `score_thresholds` | `CONFIRM` | rename only, value unchanged |
| `thresholds` | `open` | `score_thresholds` | `OPEN` | rename only, value unchanged |
| `expiry` | `min_minutes` | `expiry_limits_minutes` | `min` | rename only, value unchanged |
| `expiry` | `max_minutes` | `expiry_limits_minutes` | `max` | rename only, value unchanged |
| `buffer` | `modes.SMALL.atr_mult` | `buffer_multipliers` | `SMALL` | extract atr_mult, flatten |
| `buffer` | `modes.MEDIUM.atr_mult` | `buffer_multipliers` | `MEDIUM` | extract atr_mult, flatten |
| `buffer` | `modes.LARGE.atr_mult` | `buffer_multipliers` | `LARGE` | extract atr_mult, flatten |
| `weights` | (any) | (none) | (none) | reported in dropped_keys, not migrated (no canonical consumer) |
| `gates` | (any) | (none) | (none) | reported in dropped_keys, not migrated (no canonical consumer) |

## Rejected legacy mappings

- Any unrecognized sub-key in `thresholds` → migration error
- Any unrecognized sub-key in `expiry` → migration error
- Any unrecognized mode in `buffer.modes` beyond SMALL/MEDIUM/LARGE → migration error
- Any extra key in `buffer` beyond `modes` → migration error
- Any completely unrecognized top-level key → migration error (not silently dropped)
