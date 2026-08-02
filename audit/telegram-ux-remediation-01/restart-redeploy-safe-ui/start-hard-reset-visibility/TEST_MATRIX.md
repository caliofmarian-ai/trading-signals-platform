# TEST_MATRIX.md

## Test Matrix — /start Hard Reset Visibility

All tests located in:
`tests/canonical/unit/test_start_hard_reset_visibility.py`

### Required Coverage (from problem statement)

| # | Scenario | Test | Result |
|---|---|---|---|
| 1 | Existing USER session U1 → /start bypasses edit | `test_01_user_start_bypasses_edit_path` | ✅ |
| 2 | Explicit USER /start bypasses edit-first delivery | `test_02_user_start_bypasses_edit_first_delivery` | ✅ |
| 3 | Old U1 is deleted best-effort | `test_03_old_message_deleted_best_effort` | ✅ |
| 4 | Exactly one U2 is sent | `test_04_exactly_one_new_message_sent` | ✅ |
| 5 | U2 becomes active | `test_05_new_message_id_becomes_active` | ✅ |
| 6 | Subsequent /status edits U2 | `test_06_subsequent_status_edits_new_anchor` | ✅ |
| 7 | Existing ADMIN session A1 → /start bypasses edit | `test_07_admin_start_bypasses_edit` | ✅ |
| 8 | Explicit ADMIN /start performs the same reset | `test_08_admin_start_sends_exactly_one_message` | ✅ |
| 9 | Exactly one A2 is sent | `test_09_admin_new_anchor_is_active` | ✅ |
| 10 | Subsequent /admin, Engine, Home edit A2 | `test_10_subsequent_admin_actions_edit_new_anchor` | ✅ |
| 11 | Critical scenario: edit would succeed but /start still sends new | `test_11_start_does_not_call_edit_even_when_edit_would_succeed` | ✅ |
| 12 | Old-message deletion succeeds → replacement sent once | `test_12_delete_succeeds_replacement_sent_once` | ✅ |
| 13 | Old-message deletion: not found → replacement sent once | `test_13_delete_absent_replacement_sent_once` | ✅ |
| 14 | Old-message deletion forbidden → replacement sent once | `test_14_delete_forbidden_replacement_sent_once` | ✅ |
| 15 | Old-message deletion times out → replacement sent once | `test_15_delete_transport_failure_replacement_sent_once` | ✅ |
| 16 | All deletion outcomes: replacement sent exactly once | `test_16_all_delete_outcomes_send_exactly_once` | ✅ |
| 17 | Persisted session clear fails → replacement still sent | `test_17_persisted_session_clear_fails_replacement_still_sent` | ✅ |
| 18 | Replacement send still occurs when session clear fails | `test_18_replacement_sent_when_clear_fails` | ✅ |
| 19 | Replacement send succeeds and persistence fails → delivery visible | `test_19_send_succeeds_persistence_fails_delivery_still_visible` | ✅ |
| 20 | User-visible delivery remains successful | `test_20_delivery_visible_when_persistence_fails` | ✅ |
| 21 | Replacement send fails → old session not restored | `test_21_send_fails_old_session_not_restored` | ✅ |
| 22 | Old session not restored | `test_22_old_session_cleared_before_send_attempt` | ✅ |
| 23 | A later /start after send failure succeeds | `test_23_subsequent_start_succeeds_after_send_failure` | ✅ |
| 24 | Two rapid /start updates do not create duplicate anchors | `test_24_concurrent_start_uses_reset_guard` | ✅ |
| 24b | Guard TTL prevents abandoned locks | `test_24b_guard_expires_after_ttl` | ✅ |
| 25 | USER and ADMIN resets remain independent | `test_25_user_and_admin_resets_independent` | ✅ |
| 26 | Restart preserves the new anchor | `test_26_restart_preserves_new_anchor` | ✅ |
| 27 | Redeploy preserves correct behavior | `test_27_redeploy_correct_behavior` | ✅ |
| 28 | Group and forum-topic behavior is unchanged | `test_28_group_start_uses_edit_first_path` | ✅ |
| 29 | Role and permission behavior is unchanged | `test_29_role_resolution_not_affected` | ✅ |
| 30 | Full repository suite passes | (full suite) | ✅ 636/636 |
| 31 | Tests leave repository clean | `test_31_no_stale_test_artefacts` | ✅ |

### Additional Unit Tests

| Test | Covers |
|---|---|
| `test_delete_message_success` | delete_message() returns DELETE_OUTCOME_DELETED |
| `test_delete_message_not_found` | delete_message() returns DELETE_OUTCOME_ABSENT |
| `test_delete_message_transport_failure` | delete_message() returns DELETE_OUTCOME_TRANSPORT |
| `test_delete_message_never_raises` | delete_message() never raises |
| `test_delete_message_no_token_in_description` | Token redaction in diagnostics |
| `test_acquire_and_release` | Guard acquire/release cycle |
| `test_user_admin_guards_independent` | Cross-session independence |
| `test_guard_ttl_prevents_abandonment` | Expired guards are re-acquirable |
