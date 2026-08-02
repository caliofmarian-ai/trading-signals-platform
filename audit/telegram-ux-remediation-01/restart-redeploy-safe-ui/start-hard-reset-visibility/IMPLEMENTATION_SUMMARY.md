# IMPLEMENTATION_SUMMARY.md

## Implementation Summary — /start Hard Reset Visibility

### Problem

After a user deletes their Telegram conversation, pressing Start produces no
visible response. The bot's previous design tried to edit the old message
first; when Telegram returned `ok: true` for that edit (even though the
message was no longer visible to the user), the bot considered delivery
successful and never called `sendMessage`.

### Solution

`/start` is now a **deterministic visible re-anchor**. For private chats:

1. Session is normalized and the reset guard is acquired.
2. The old active message is read and the session is cleared.
3. Old message is best-effort deleted (all outcomes non-blocking).
4. `sendMessage` is called exactly once — unconditionally.
5. The new message ID becomes the active anchor.

### New Code

#### `telegram_publisher.delete_message(chat_id, message_id)`
- Canonical best-effort deletion
- Returns structured result dict, never raises
- Classifies: deleted, message_absent, forbidden, transport_failure, unexpected
- Token-safe: bot token is redacted from all output

#### `telegram_app_nav.acquire_start_reset_guard(chat_id, user_id)`
- Returns `{"acquired": True/False, "generation": N}`
- Per-session; USER/ADMIN sessions are independent
- TTL of 30s prevents abandoned locks after crashes

#### `telegram_app_nav.release_start_reset_guard(chat_id, user_id)`
- Marks guard as no longer in progress

#### `telegram_app_nav.prepare_start_hard_reset(chat_id, user_id)`
- Reads previous message ID
- Clears memory and persistence (best-effort)
- Returns structured result with diagnostics

#### `bot_service._handle_start_hard_reset(...)`
- Orchestrates the full reset sequence for private-chat `/start`
- Never calls `editMessageText`
- Logs full mandatory diagnostics to stderr
- Falls through to `_send_interactive_page` for non-private contexts

### Invariants Preserved

- Normal button navigation (APP:, ADMIN_NAV:) still uses edit-first path
- `/status`, `/help`, `/admin` still use edit-first path
- Group and forum-topic behavior unchanged
- Role and permission resolution unchanged
- Single-message UI model preserved after `/start`

### Diagnostics

Every `/start` hard reset logs to stderr:
- update_id, normalized_command, chat_id, user_id
- session_fingerprint
- previous_active_message_id
- edit_path_bypassed (always true for private /start)
- delete_attempted, delete_result, delete_error_code
- session_clear_result
- send_attempted, send_result, send_error (if failed)
- new_message_id
- persistence_result
- runtime_instance_id, deployment_id, process_id
- reset_guard_acquired, reset_generation
