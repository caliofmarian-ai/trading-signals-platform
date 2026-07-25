# TEST EVIDENCE

## Test Suite Results

**Total tests passing: 394**  
**Failures: 0**  
**New tests added: 69**  
**Pre-existing tests: 325**

---

## New Test File

`tests/telegram_admin_ui_restoration/test_admin_ui_restoration.py`

Run command:
```bash
PYTHONPATH=send python -m pytest tests/telegram_admin_ui_restoration/ -v
```

---

## Test Categories and Coverage

### AUTH — Authorization (9 tests)

| Test | Validates |
|---|---|
| `test_owner_private_dm_allowed` | Owner private DM allowed for /admin |
| `test_wrong_private_user_denied` | Non-owner private user denied |
| `test_admin_chat_allowed` | Configured admin chat allowed |
| `test_wrong_chat_denied` | Non-admin chat denied |
| `test_callbacks_follow_same_auth` | Callbacks use same auth as slash commands |
| `test_missing_owner_telegram_id_fails_closed` | Missing OWNER_TELEGRAM_ID → deny |
| `test_owner_id_must_match_exactly` | Partial match → deny |
| `test_callback_non_owner_private_denied` | Non-owner callback in private DM denied |
| `test_reload_roles_blocked_in_private` | RELOAD_ROLES_CONFIRM blocked in private DM |

### UI — Visual Admin Panel (8 tests)

| Test | Validates |
|---|---|
| `test_admin_home_button_layout` | 16+ buttons in home markup |
| `test_admin_home_has_required_emojis` | All required emojis present |
| `test_role_based_visibility` | Permissions filter visible panels |
| `test_back_navigation_home` | Back button present in symbol panel |
| `test_confirmation_flow_profile` | Profile confirm markup contains Apply/Cancel |
| `test_symbol_state_rendering` | Active=✅, inactive=⬜ |
| `test_symbols_sections` | FOREX and CRYPTO labels present |
| `test_pagination_present` | Files list includes Prev/Next when needed |

### SYM — Symbol Management (7 tests)

| Test | Validates |
|---|---|
| `test_symbol_toggle_on` | Toggle disabled symbol enables it |
| `test_symbol_toggle_off` | Toggle enabled symbol disables it |
| `test_symbols_all` | ALL activates all symbols |
| `test_symbols_none` | NONE deactivates all symbols |
| `test_symbol_toggle_permission_denial` | Non-authorized user denied |
| `test_symbol_admin_proof` | Admin Proof generated on mutation |
| `test_invalid_symbol_rejected` | Invalid symbol name rejected |

### PROF — Strategy Profile (6 tests)

| Test | Validates |
|---|---|
| `test_profile_conservative_maps_correctly` | CONSERVATIVE params applied correctly |
| `test_profile_balanced_maps_correctly` | BALANCED params applied correctly |
| `test_profile_aggressive_maps_correctly` | AGGRESSIVE params applied correctly |
| `test_profile_confirmation_required` | Direct exec without confirm not possible via UI |
| `test_profile_admin_proof` | Admin Proof generated on profile apply |
| `test_invalid_profile_rejected` | Unknown profile name rejected |

### FILE — File Security (12 tests)

| Test | Validates |
|---|---|
| `test_allowed_file_download` | Allowed .txt file served |
| `test_allowed_json_download` | Allowed .json file served |
| `test_unsupported_extension_rejected` | .py extension rejected |
| `test_traversal_rejected` | `../` in path rejected |
| `test_double_dot_rejected` | `..` component rejected |
| `test_symlink_escape_rejected` | Symlink escaping root rejected |
| `test_excessive_file_size_rejected` | File exceeding size limit rejected |
| `test_secret_filename_rejected` | `.env` filename rejected |
| `test_token_filename_rejected` | `token.txt` filename rejected |
| `test_unauthorized_access_denied` | User without files.view denied |
| `test_files_list_pagination` | Paginated file listing works |
| `test_files_list_hides_secrets` | Secret-named files not listed |

### DIAG — Diagnostics (6 tests)

| Test | Validates |
|---|---|
| `test_diagnose_output_sanitized` | No secret values in /diagnose output |
| `test_diagnose_no_token_in_output` | TELEGRAM_BOT_TOKEN not in output |
| `test_audit_runtime_bounded` | Artifact does not exceed MAX_AUDIT_SIZE |
| `test_audit_runtime_no_secrets` | Secret keys redacted in runtime audit |
| `test_diagnose_telegram_failure_handled` | Telegram failure → error message, no crash |
| `test_diagnose_missing_dir_handled` | Missing observability dir handled gracefully |

### RATE — Rate Limiting (8 tests)

| Test | Validates |
|---|---|
| `test_files_list_rate_limit` | files_list limited to 20/60s |
| `test_file_download_rate_limit` | file_download limited to 10/60s |
| `test_diagnose_rate_limit` | diagnose limited to 5/60s |
| `test_audit_runtime_rate_limit` | audit_runtime limited to 3/60s |
| `test_mutation_rate_limit` | mutations limited to 30/60s |
| `test_rate_limit_per_user` | Different users have separate limits |
| `test_rate_limit_window_resets` | Counts reset after window expires |
| `test_rate_limit_message_clear` | Rate limit message shown on exceed |

### REG — Regression (13 tests)

| Test | Validates |
|---|---|
| `test_existing_status_command` | /status still works |
| `test_existing_strategy_command` | /strategy still works |
| `test_existing_thresholds_command` | /thresholds still works |
| `test_existing_roles_command` | /roles still works |
| `test_startup_notification_still_works` | Startup notification logic unchanged |
| `test_distribution_still_works` | Signal distribution logic unchanged |
| `test_outcome_callback_still_works` | Outcome callback unchanged |
| `test_canonical_polling_loop_still_works` | Polling loop entry point unchanged |
| `test_unknown_callback_fails_safe` | Unknown callback → safe error, no crash |
| `test_malformed_callback_fails_safe` | Malformed callback → safe error, no state mutation |
| `test_help_lists_new_commands` | /help output includes new commands |
| `test_topic_routing_fallback` | Topic routing falls back when IDs absent |
| `test_alerts_target_with_thread` | alerts_target returns thread when configured |

---

## Running the full suite

```bash
cd /path/to/repo
PYTHONPATH=send python -m pytest -q
```

Expected output (reference):
```
394 passed in 5.70s
```
