# CORRECTIVE_IMPLEMENTATION_CONTRACT.md
# Issue #31 — Corrective Implementation Contract

## Changed Files

### 1. `send/core/storage.py`

**Changes**:
- Added `import socket` and `import sys`
- Added helper functions: `_current_deployment_id()`, `_safe_hostname()`, `_read_lock_metadata()`,
  `_is_pid_alive()`, `_lock_is_stale()`, `_reclaim_stale_lock()`
- `with_lock()`: Added stale-lock detection and reclaim on every contention cycle
- Lock metadata now includes: `pid`, `ts`, `deploy`, `host`
- `_is_pid_alive(0)` returns False (PID 0 is not a valid owning process)

**Contract**:
- A lock held by a demonstrably live process on the current deployment is NEVER stolen
- A lock from a dead PID, different deployment, or older than 300s is safely reclaimed
- Reclaim events emit a structured JSON diagnostic to stderr for Railway log capture
- Atomic safety is preserved: reclaim uses `os.remove()` + retry (not a replace/rename)

### 2. `send/core/telegram_publisher.py`

**Changes**:
- Added `TelegramAPIError(RuntimeError)` structured exception class
- Fields: `operation`, `http_status`, `error_code`, `description`, `retry_after`
- Methods: `from_response()`, `is_stale_message()`, `is_not_modified()`, `is_chat_not_found()`
- `edit_message()` now raises `TelegramAPIError` instead of bare `RuntimeError`
- `send_message()` now raises `TelegramAPIError` instead of bare `RuntimeError`
- `_safe_api_error()` kept as legacy helper (not removed)

**Contract**:
- Classification uses structured fields (error_code, http_status) first
- String matching on normalized_description as fallback for legacy code
- Bot token is never exposed in `TelegramAPIError.description` (redacted)

### 3. `send/core/bot_service.py`

**Changes**:
- Added `from core.telegram_publisher import TelegramAPIError as _TelegramAPIError`
- `_edit_interactive_message()`: `clear_active_message()` is now wrapped in try-except;
  a failure during clear (e.g. TimeoutError from stale lock) is logged but NEVER propagated.
  The send path is always reached.
- `_classify_edit_message_failure()`: Uses `_TelegramAPIError` structured fields first;
  legacy string matching retained as fallback; added `peer_id_invalid` to stale markers

**Contract** (Transport-First):
1. `/start` receives a valid command
2. Edit is attempted on tracked message
3. If edit fails (stale): clear is attempted best-effort
4. Even if clear raises, send_message is ALWAYS called
5. User always sees a response

### 4. `send/runtime/telegram_updates.py`

**Changes**:
- Added `Optional` import
- Added `_POLLER_LAST_HEARTBEAT`, `_POLLER_HEARTBEAT_LOCK`, `POLLER_HEARTBEAT_TIMEOUT_SEC`
- Added `_update_poller_heartbeat()`, `get_poller_heartbeat_age()`, `is_poller_alive()`
- `poll_updates()`: Heartbeat recorded after every successful `getUpdates` response
- Per-update try-except: `process_update()` failures are caught and logged individually;
  the poller loop continues; the offset is still advanced

**Contract**:
- One failed update NEVER stops or stalls Telegram command processing
- `is_poller_alive()` returns False if no heartbeat within 120s
- `LAST_UPDATE_ID` is advanced before `process_update()` to prevent infinite re-processing
  of a permanently-failing update

### 5. `send/runtime/system_boot.py`

**Changes**:
- `start_system()`: `record_start()` is wrapped in try-except
- On failure: degraded-safe start_info is used; `crash_loop=False`, `recovery_required=True`
- Main loop: emits poller liveness warnings when heartbeat is stale

**Contract**:
- A stale `restart_guard.lock` never prevents the bot from starting
- Poller liveness is monitored and logged every 60 seconds
