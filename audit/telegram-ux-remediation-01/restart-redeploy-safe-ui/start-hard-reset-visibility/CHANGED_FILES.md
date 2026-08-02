# CHANGED_FILES.md

## Changed Files

### Production Code

| File | Change |
|---|---|
| `send/core/telegram_publisher.py` | Added `delete_message()` function with structured outcome classification (`DELETE_OUTCOME_DELETED`, `DELETE_OUTCOME_ABSENT`, `DELETE_OUTCOME_FORBIDDEN`, `DELETE_OUTCOME_TRANSPORT`, `DELETE_OUTCOME_UNEXPECTED`). Never raises. |
| `send/core/telegram_app_nav.py` | Added `_RESET_GUARDS` dict + `_RESET_GUARD_LOCK` + `_RESET_GUARD_TTL_SEC`; added `_prune_reset_guards()`, `acquire_start_reset_guard()`, `release_start_reset_guard()`, `prepare_start_hard_reset()`. |
| `send/core/bot_service.py` | Added `_handle_start_hard_reset()`; changed `/start` command handler to call `_handle_start_hard_reset()` instead of `_send_interactive_page()`. |

### Tests

| File | Change |
|---|---|
| `tests/canonical/unit/test_start_hard_reset_visibility.py` | **New file.** 39 tests covering all 31 required scenarios. |
| `tests/canonical/unit/test_restart_redeploy_recovery.py` | Added `delete_message()` to `FakePublisher`. |
| `tests/telegram_transport/test_telegram_transport_and_recovery.py` | Added `delete_message()` to `FakePublisher`; updated `test_08_replacement_becomes_active` to not use `edit_fail_once` (which was testing the old edit-first /start path). |

### Audit Documentation

| File | Content |
|---|---|
| `audit/telegram-ux-remediation-01/restart-redeploy-safe-ui/start-hard-reset-visibility/LIVE_FAILURE_AFTER_PR36.md` | Evidence and timeline of the confirmed live failure |
| `audit/telegram-ux-remediation-01/restart-redeploy-safe-ui/start-hard-reset-visibility/EDIT_SUCCESS_NOT_VISIBILITY_PROOF.md` | Explains why editMessageText ok=true ≠ visible to user |
| `audit/telegram-ux-remediation-01/restart-redeploy-safe-ui/start-hard-reset-visibility/START_REANCHOR_CONTRACT.md` | Complete /start hard-reset contract |
| `audit/telegram-ux-remediation-01/restart-redeploy-safe-ui/start-hard-reset-visibility/DELETE_MESSAGE_BEHAVIOR_MATRIX.md` | deleteMessage outcome matrix |
| `audit/telegram-ux-remediation-01/restart-redeploy-safe-ui/start-hard-reset-visibility/IDEMPOTENCY_AND_CONCURRENCY.md` | Idempotency guard design |
| `audit/telegram-ux-remediation-01/restart-redeploy-safe-ui/start-hard-reset-visibility/ROOT_CAUSE_ANALYSIS.md` | Root cause analysis with PR history |
| `audit/telegram-ux-remediation-01/restart-redeploy-safe-ui/start-hard-reset-visibility/TEST_MATRIX.md` | Test coverage matrix |
| `audit/telegram-ux-remediation-01/restart-redeploy-safe-ui/start-hard-reset-visibility/TEST_REPORT.md` | Test results summary |
| `audit/telegram-ux-remediation-01/restart-redeploy-safe-ui/start-hard-reset-visibility/CHANGED_FILES.md` | This file |
| `audit/telegram-ux-remediation-01/restart-redeploy-safe-ui/start-hard-reset-visibility/IMPLEMENTATION_SUMMARY.md` | Implementation summary |
| `audit/telegram-ux-remediation-01/restart-redeploy-safe-ui/start-hard-reset-visibility/LIVE_ACCEPTANCE_CHECKLIST.md` | Live acceptance test checklist |
