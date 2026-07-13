# BATCH_02_CHANGED_FILES

## Modified files

### send/schema/params_schema.json
- Removed `strategy_v2.scores` (CALL/PUT/NO_SIGNAL) — not consumed by strategy_v2.py
- Added `spike_filters`, `sr_required_multiplier`, `crypto_points_rounding`, `trend_time_adjust`, `structure_factor`
- Made schema a proper type-annotation document with constraints for all fields

### send/config/algo_params.json
- Replaced entire file with canonical shape
- Key changes: legacy thresholds → score_thresholds, legacy expiry → expiry_limits_minutes, legacy buffer.modes → buffer_multipliers
- Removed weights and gates (no canonical consumers)
- Added canonical optional fields: strategy_v2, spike_filters, sr_required_multiplier, crypto_points_rounding, trend_time_adjust, structure_factor

### send/core/params_loader.py
- Full rewrite
- New public API: `load_algo_params`, `validate_algo_params`, `migrate_legacy_params`, `detect_legacy_shape`, `compute_checksum`
- New exceptions: `ParamsValidationError`, `ParamsMigrationError`
- New type: `MigrationResult` NamedTuple

### send/core/admin_commands.py
- Updated `_load_algo_params()` to use `params_loader.load_algo_params()`
- Added `_save_algo_params_validated()` using `params_loader.validate_algo_params()` + `storage.save_json_atomic()`
- Updated `_set_threshold()` to write to `score_thresholds.{FIELD_UPPER}`
- Updated `_set_sr()` to write to `sr_required_multiplier` (not `sr_buffer`)
- Updated `_set_spike()` to write to `spike_filters.{field}`
- Removed `_safe_write_json()` non-atomic write path

### send/core/admin_views.py
- Updated `render_strategy_status()` to read canonical key paths
- Updated `render_admin_home()` spike command help text

### tests/batch_01/test_boot_and_import_stabilization.py
- Renamed `test_params_loader_behavior_is_unchanged` → `test_params_loader_loads_canonical_contract`
- Updated assertions to canonical key shape (PRE/CONFIRM/OPEN integers instead of lowercase floats)

## Created files

### tests/batch_02/__init__.py
- Empty package marker

### tests/batch_02/test_canonical_parameter_contract.py
51 tests:
1. `test_live_algo_params_validates_against_canonical_contract`
2. `test_params_loader_loads_canonical_shape`
3. `test_loaded_params_match_strategy_v2_consumption_keys`
4. `test_score_thresholds_has_one_canonical_path`
5. `test_score_thresholds_end_to_end_representation`
6. `test_unknown_top_level_parameter_is_rejected`
7. `test_unknown_score_thresholds_subkey_is_rejected`
8. `test_score_thresholds_string_value_rejected`
9. `test_buffer_multiplier_string_value_rejected`
10. `test_expiry_float_rejected_for_integer_field`
11. `test_boolean_rejected_as_number`
12. `test_score_threshold_above_100_rejected`
13. `test_score_threshold_below_zero_rejected`
14. `test_score_threshold_hierarchy_violated_rejected`
15. `test_buffer_multiplier_zero_rejected`
16. `test_expiry_min_zero_rejected`
17. `test_expiry_max_less_than_min_rejected`
18. `test_sr_required_multiplier_zero_rejected`
19. `test_crypto_points_rounding_negative_rejected`
20. `test_spike_filter_zero_rejected`
21. `test_missing_score_thresholds_fails_clearly`
22. `test_missing_expiry_limits_fails_clearly`
23. `test_missing_buffer_multipliers_fails_clearly`
24. `test_missing_algo_version_fails_clearly`
25. `test_missing_score_threshold_subkey_fails_clearly`
26. `test_optional_spike_filters_absent_allows_validation`
27. `test_optional_strategy_v2_absent_allows_validation`
28. `test_optional_trend_time_adjust_absent_allows_validation`
29. `test_malformed_json_fails_clearly`
30. `test_json_array_root_fails_clearly`
31. `test_missing_params_file_fails_clearly`
32. `test_legacy_shape_migration_thresholds`
33. `test_legacy_shape_migration_expiry`
34. `test_legacy_shape_migration_buffer_modes`
35. `test_legacy_file_loads_via_migration`
36. `test_legacy_thresholds_unknown_subkey_fails_clearly`
37. `test_legacy_buffer_unknown_mode_fails_clearly`
38. `test_legacy_weights_and_gates_reported_not_silently_dropped`
39. `test_completely_unknown_legacy_key_fails_not_discarded`
40. `test_admin_mutation_accepts_valid_threshold`
41. `test_admin_mutation_unknown_threshold_field_rejected`
42. `test_admin_threshold_out_of_range_rejected_by_validation`
43. `test_admin_spike_negative_value_rejected`
44. `test_failed_admin_mutation_does_not_persist`
45. `test_valid_admin_mutation_persists_atomically`
46. `test_reload_returns_complete_validated_params`
47. `test_failed_reload_preserves_last_valid_state`
48. `test_strategy_uses_canonical_score_thresholds`
49. `test_params_loader_import_has_no_network_or_thread_side_effects`
50. `test_batch_01_core_imports_still_side_effect_free`
51. `test_strategy_v2_decide_produces_deterministic_output`

### audit/remediation-batch-02/BATCH_02_PARAMETER_FLOW_BEFORE.md
### audit/remediation-batch-02/BATCH_02_CANONICAL_PARAMETER_CONTRACT.md
### audit/remediation-batch-02/BATCH_02_IMPLEMENTATION_REPORT.md
### audit/remediation-batch-02/BATCH_02_VALIDATION_REPORT.md
### audit/remediation-batch-02/BATCH_02_CHANGED_FILES.md (this file)
### audit/remediation-batch-02/BATCH_02_OPEN_FINDINGS.md
