# Test Matrix — Multi-Account Session Isolation

File: `tests/canonical/unit/test_multi_account_session_isolation.py`

| # | Test Name | Requirement | Result |
|---|-----------|-------------|--------|
| 1 | test_01_user_creates_session | USER creates U1 | ✅ |
| 2 | test_02_admin_creates_session | ADMIN creates A1 | ✅ |
| 3 | test_03_user_and_admin_keys_differ | Keys are distinct | ✅ |
| 4 | test_04_clear_admin_does_not_touch_user | Only A is cleared | ✅ |
| 5 | test_05_user_status_still_works_after_admin_clear | USER /status still edits U1 | ✅ |
| 6-7 | test_06_08_admin_session_removed_from_memory_and_persistence | A removed from mem+disk | ✅ |
| 8 | (included above) | A removed from persisted state | ✅ |
| 9-10 | test_09_10_user_unchanged_after_admin_operations | U unchanged in mem+disk | ✅ |
| 11-12 | test_11_12_exactly_one_replacement_sent | Exactly one A2; A2 active | ✅ |
| 13-14 | test_13_14_subsequent_edits_do_not_send_new_message | A2 edited; no A3 | ✅ |
| 15 | test_15_failed_replacement_leaves_session_absent | Failed send leaves A absent | ✅ |
| 16 | test_16_admin_start_retries_after_stale_failure | Later /start retries OK | ✅ |
| 17 | test_17_cleared_state_absent_after_reload | No resurrection after reload | ✅ |
| 18 | test_18_cleared_state_absent_after_simulated_restart | No resurrection after restart | ✅ |
| 19 | test_19_persisted_only_session_can_be_cleared | Persisted-only clearable | ✅ |
| 20 | test_20_thread_id_normalization | None/0/missing normalize same | ✅ |
| 21 | test_21_duplicate_private_session_variants_collapsed | Duplicates collapsed | ✅ |
| 22 | test_22_concurrent_user_save_and_admin_clear | Concurrent ops safe | ✅ |
| 23 | test_23_concurrent_clear_and_replacement_no_resurrection | No A1 resurrection | ✅ |
| 24 | test_24_exact_persisted_delete_preserves_others | Only target removed | ✅ |
| 25 | test_25_state_corruption_fails_safely | Corruption → safe | ✅ |
| 26 | test_26_unsupported_schema_fails_safely | Bad schema → safe | ✅ |
| 27 | test_27_start_not_permanently_silent | /start never silent | ✅ |
| 28 | test_28_one_account_failure_does_not_block_another | Failures isolated | ✅ |
| 29 | test_29_railway_restart_recovery | Railway restart OK | ✅ |
| 30 | test_30_both_accounts_responsive_after_repeated_switching | Full isolation | ✅ |
| + | test_delete_result_structure | Structured evidence returned | ✅ |
| + | test_delete_nonexistent_session_is_safe | Idempotent delete | ✅ |
| + | test_diagnostics_independent_persisted_read | Diagnostics independent | ✅ |
