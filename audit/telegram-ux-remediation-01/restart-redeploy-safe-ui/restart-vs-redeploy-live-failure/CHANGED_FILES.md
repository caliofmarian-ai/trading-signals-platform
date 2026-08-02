# CHANGED_FILES.md
# Issue #31 — Changed Files

## Production Code Changes

| File | Type | Summary |
|------|------|---------|
| `send/core/storage.py` | Fix | Stale-lock detection and safe reclaim in `with_lock()` |
| `send/core/telegram_publisher.py` | Feature | `TelegramAPIError` structured exception; `edit_message`/`send_message` raise structured error |
| `send/core/bot_service.py` | Fix | Transport-first recovery; structured error classification; no propagation from `clear_active_message()` |
| `send/runtime/telegram_updates.py` | Feature | Poller heartbeat; per-update exception isolation |
| `send/runtime/system_boot.py` | Fix | Startup hardened against stale `restart_guard.lock`; poller liveness monitoring |

## Test File Added

| File | Tests |
|------|-------|
| `tests/canonical/unit/test_restart_redeploy_recovery.py` | 29 new tests |

## Documentation Added

| File | Content |
|------|---------|
| `audit/telegram-ux-remediation-01/restart-redeploy-safe-ui/restart-vs-redeploy-live-failure/LIVE_FAILURE_EVIDENCE.md` | Production failure sequence |
| `.../ROOT_CAUSE_ANALYSIS.md` | Proven root cause: stale lock + transport chain break |
| `.../LOCKFILE_LIFECYCLE_AUDIT.md` | Lock lifecycle and failure modes |
| `.../CORRECTIVE_IMPLEMENTATION_CONTRACT.md` | Detailed implementation decisions |
| `.../TELEGRAM_API_ERROR_EVIDENCE.md` | Telegram API error classification |
| `.../POLLER_AND_OFFSET_TRACE.md` | Update offset and poller behavior |
| `.../RESTART_GUARD_ANALYSIS.md` | Restart guard audit |
| `.../RESTART_VS_REDEPLOY_TIMELINE.md` | Timeline comparison A/B/C/D |
| `.../RUNTIME_PATH_COMPARISON.md` | Runtime path and diagnostics |
| `.../TEST_MATRIX.md` | Full test matrix with pass/fail |
| `.../CHANGED_FILES.md` | This file |
| `.../IMPLEMENTATION_SUMMARY.md` | One-page summary |
| `.../LIVE_ACCEPTANCE_CHECKLIST.md` | Live production acceptance checklist |
| `.../TEST_REPORT.md` | Test results |
