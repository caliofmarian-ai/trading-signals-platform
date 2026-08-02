# IMPLEMENTATION_SUMMARY.md
# Issue #31 — Implementation Summary

## Problem Proven

A stale lock file at `state/.locks/telegram_ui_state.lock`, left by a process
killed (SIGKILL) during Railway Restart, caused `clear_active_message()` to
raise `TimeoutError` after 10 seconds. This exception was NOT caught in
`_edit_interactive_message()` and propagated to `process_update()`, which
swallowed it without sending any Telegram response. The user saw silence.

After Railway Restart (same container filesystem), the stale lock persisted.
After Railway Redeploy (fresh container), the lock was gone — hence the
"Restart fails, Redeploy succeeds" pattern.

## Fixes Delivered

1. **Stale-lock recovery** (`storage.py`): Locks from dead PIDs, different deployments,
   or older than 300s are safely reclaimed. Active locks are never stolen.

2. **Transport-first command recovery** (`bot_service.py`): `clear_active_message()`
   failure is now caught and logged; `send_message()` is ALWAYS reached. Users always
   see a response regardless of state persistence failures.

3. **Structured Telegram API errors** (`telegram_publisher.py`): `TelegramAPIError`
   carries `http_status`, `error_code`, `description`, `retry_after`. Classification
   uses structured fields, not just string matching.

4. **Poller heartbeat** (`telegram_updates.py`): `_POLLER_LAST_HEARTBEAT` updated on
   every successful `getUpdates`. `is_poller_alive()` and `get_poller_heartbeat_age()`
   available for external verification.

5. **Per-update exception isolation** (`telegram_updates.py`): Each `process_update()`
   call is individually try-except'd. One failed update never stops the poller.

6. **Startup hardening** (`system_boot.py`): `record_start()` failure (e.g. from stale
   `restart_guard.lock`) is handled gracefully; bot starts in degraded-safe mode.

## Tests

- 29 new targeted tests covering all scenarios
- 597 total tests passing (no regressions)

## Status

Implementation complete. Draft PR created for review.
Issue #31 remains OPEN pending live production acceptance.
