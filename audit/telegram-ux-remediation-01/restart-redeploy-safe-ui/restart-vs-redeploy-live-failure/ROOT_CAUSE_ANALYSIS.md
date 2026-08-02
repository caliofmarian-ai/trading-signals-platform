# ROOT_CAUSE_ANALYSIS.md
# Issue #31 — Root Cause Analysis

## Primary Root Cause: Stale Lockfile Blocks Transport Recovery

### Mechanism

1. User deletes conversation and sends `/start`
2. Bot receives update; `_send_interactive_page()` tries to edit old message
3. Telegram API returns 400 `message to edit not found`
4. `_edit_interactive_message()` classifies failure as "stale"
5. `clear_active_message()` is called to clear the session
6. `delete_telegram_ui_session()` → `with_lock("telegram_ui_state")` → **blocks if stale lock**
7. **Critical path pre-fix**: `clear_active_message()` raised `TimeoutError` after 10 seconds
8. **Pre-fix bug**: `TimeoutError` was NOT caught in `_edit_interactive_message()`
9. Exception propagated to `process_update()` top-level handler → error logged, **no message sent**

### Why Restart Doesn't Fix It

- The stale lock file exists on the container's ephemeral filesystem
- Railway Restart kills and restarts the process inside the SAME container context
- The lock file was written during a process that was killed (SIGKILL from Railway)
- The `finally:` block that removes the lock never executed under SIGKILL
- The new process cannot acquire `telegram_ui_state.lock` → same failure

### Why Redeploy Fixes It

- Railway Redeploy creates a NEW container from scratch
- The container filesystem is fresh — stale lock files do not exist
- The new process acquires the lock immediately on startup
- Telegram UI state is loaded cleanly; `/start` succeeds

## Secondary Contributing Factors

### 1. Non-atomic Update Offset Advancement

**Pre-fix**: `LAST_UPDATE_ID = update["update_id"] + 1` was set before `process_update()`.
If `process_update()` raised, the update was permanently consumed without being processed.
After Restart, `LAST_UPDATE_ID = None`, so Telegram might re-deliver unconfirmed updates.
**Post-fix**: Per-update try-except ensures both offset and processing are isolated.

### 2. String-Only Error Classification

**Pre-fix**: `_classify_edit_message_failure()` used only string matching on exception message.
This is fragile — any change to Telegram's error description format breaks classification.
**Post-fix**: `TelegramAPIError` carries structured `http_status`, `error_code`, and `description`.
Classification uses structured fields first, string matching as fallback.

### 3. Missing Restart Guard Startup Hardening

If `record_start()` raised `TimeoutError` (stale `restart_guard.lock`), the entire bot failed
to start without any error recovery. **Post-fix**: `record_start()` is wrapped in try-except;
failure results in a degraded-safe start, not a hard crash.

### 4. No Poller Heartbeat

**Pre-fix**: No way to verify that the Telegram poller thread was alive after Restart.
`telegram_polling_started=True` was set based on thread creation, not actual poll confirmation.
**Post-fix**: `_POLLER_LAST_HEARTBEAT` is updated on every successful `getUpdates` response.
`is_poller_alive()` and `get_poller_heartbeat_age()` provide liveness verification.

## Ruling Out Other Causes

| Hypothesis | Ruling |
|-----------|--------|
| USER/ADMIN session-key mismatch | Ruled out — both accounts affected |
| Restart Guard crash loop | Not primary — single restart insufficient to trigger 4-restart limit |
| Multiple Railway instances polling | No evidence; single deployment |
| Telegram send failing (blocked chat) | Ruled out — deleting conversation doesn't block sends |
| Wrong BINARYBOT_BASE_DIR | Not involved — lock path is consistent |
| Update offset advancing past unprocessed updates | Contributing factor, addressed |
