# BATCH_02_OPEN_FINDINGS

## Status of BATCH-02 findings

### GAP-004 — Strategy parameter contract split across incompatible schemas
**Status: RESOLVED**
One canonical parameter contract is now in effect across:
- algo_params.json (persisted config)
- params_loader.py (validation)
- params_schema.json (type-annotation schema)
- admin_commands.py (mutation)
- strategy_v2.py (consumption — unchanged, was already canonical)

### CON-007 — Strategy reader, params loader, schema, and config use different key shapes
**Status: RESOLVED**
All layers now use the same key shapes.
- `score_thresholds.PRE/CONFIRM/OPEN` (uppercase integers)
- `expiry_limits_minutes.min/max` (integers)
- `buffer_multipliers.SMALL/MEDIUM/LARGE` (flat floats)

## Compatibility risks

### sr_required_multiplier semantics change
- The admin `/sr` command previously accepted absolute pip distances (range 0.0001–0.002)
- Now accepts ATR multipliers (range > 0, ≤ 10.0)
- Any live operator muscle memory for the old range is now invalid
- New default: 1.5 (matches strategy_v2.py default)
- Risk level: LOW (production only affects operators who used `/sr`)

### weights and gates keys dropped
- The legacy `weights` and `gates` config keys had no consumers in strategy_v2.py
- They were explicitly listed in LEGACY_UNCONSUMABLE_KEYS and reported in migration output
- They are no longer accepted in new config files
- Risk level: LOW (they had no effect on trading behavior)

### Admin /spike field names changed
- Old: `wick_ratio`, `atr_jump`
- New: `wick_body_ratio_max`, `jump_vs_atr_max`, `range_z_max`
- Any stored admin instructions or documentation referencing old names will fail
- Risk level: LOW (operator-facing only)

## Deferred findings

### OWNER-002 — Retire legacy core/bot_service.py control-plane path
- Deferred to dedicated later batch per owner decision
- bot_service.py still contains its own parameter loading path
- This is a known redundancy, intentionally deferred
- Finding remains open until OWNER-002 batch completes

### OWNER-003 — Converge mutable runtime state/config on segmented directories
- Deferred to dedicated later batch per owner decision
- Config still lives at send/config/algo_params.json (flat)
- Finding remains open until OWNER-003 batch completes

### OWNER-004 — Trade temporal telemetry
- Remains deferred per prior governance record
- Not started in BATCH-02

## Rollback instructions

To revert BATCH-02 changes:
```
git revert <batch-02-commit-sha>
```

Or to manually restore the previous state:
1. Restore `send/config/algo_params.json` to the pre-BATCH-02 legacy shape (thresholds, weights, expiry, buffer, gates)
2. Restore `send/core/params_loader.py` to the pre-BATCH-02 version
3. Restore `send/core/admin_commands.py` to the pre-BATCH-02 version
4. Restore `send/core/admin_views.py` to the pre-BATCH-02 version
5. Restore `send/schema/params_schema.json` to the pre-BATCH-02 version
6. Remove `tests/batch_02/`
7. Revert `tests/batch_01/test_boot_and_import_stabilization.py` to original test name/assertions

Note: After rollback, strategy_v2.py will again use hardcoded defaults and operator config changes will have no effect — this was the pre-BATCH-02 state.

## Remaining CRITICAL findings
None. BATCH-02 fully resolves GAP-004 and CON-007.

## Remaining HIGH findings related to BATCH-02 scope
None.

## Recommendation for BATCH-03
- Confirm OWNER-002 batch scope before proceeding
- BATCH-03 is safe to begin; BATCH-02 is fully complete and does not conflict with pending deferred work
