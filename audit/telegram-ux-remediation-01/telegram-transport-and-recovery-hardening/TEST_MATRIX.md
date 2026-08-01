# TEST MATRIX

Source: problem statement acceptance checklist items 1–18.

| # | Test ID | Description | Coverage area |
|---|---|---|---|
| 1 | `test_01_send_message_no_parse_mode` | `send_message` sends without `parse_mode` in payload | AREA 1 |
| 2 | `test_02_edit_message_no_parse_mode` | `edit_message` sends without `parse_mode` in payload | AREA 1 |
| 3 | `test_03_parse_mode_consistent` | Both functions use the same `parse_mode` value (or none) | AREA 1 |
| 4 | `test_04_engine_command_edits_start_message` | `/engine` after `/start` edits the start message; no new send | AREA 1 |
| 5 | `test_05_admin_button_edits_engine_message` | Admin button after `/engine` edits; no new send | AREA 1 |
| 6 | `test_06_full_navigation_single_message` | Start → Engine → Admin remains one message | AREA 1 |
| 7 | `test_07_deleted_active_message_replacement` | Deleted active message produces exactly one replacement | Recovery |
| 8 | `test_08_replacement_becomes_active` | Replacement becomes active; subsequent navigation edits it | Recovery |
| 9 | `test_09_deleted_conversation_start_responds` | Deleted conversation + `/start` produces a response | Recovery |
| 10 | `test_10_stale_edit_then_successful_send` | Failed edit + successful `send_message` works | Recovery |
| 11 | `test_11_failed_edit_and_send_not_silent` | Failed edit + failed send is logged, not silent | AREA 2 |
| 12 | `test_12_unexpected_edit_does_not_corrupt_state` | Unexpected edit error does not clear active state | AREA 1 |
| 13 | `test_13_poller_continues_after_failure` | Polling continues after a per-update crash | AREA 4 (poller) |
| 14 | `test_14_railway_safe_log_line` | Railway stdout does not contain bot token | AREA 3 |
| 15 | `test_15_token_not_in_logs` | `_sanitize()` redacts bot token from error strings | AREA 3 |
| 16 | `test_16_jsonl_logging_works` | Internal JSONL logging still works after changes | Regression |
| 17 | `test_17_session_isolation` | Same user/chat/thread isolation remains correct | Regression |
| 18 | `test_18_full_e2e_single_message` | Full representative end-to-end navigation stays one message | AREA 1 |

## Coverage areas

- **AREA 1**: parse_mode inconsistency → new-message-per-navigation
- **AREA 2**: Silent `send_message` failure swallowed with `pass`
- **AREA 3**: Bot token leakage in exception log strings
- **AREA 4**: Poller resilience and callback acknowledgement
- **Recovery**: Deleted message / deleted conversation recovery
- **Regression**: Existing behaviour preserved after changes
