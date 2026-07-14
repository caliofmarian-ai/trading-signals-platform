# CURRENT_ADMIN_AUTH_FLOW

## Current authorization model (code evidence)

### 1) Update intake
`send/runtime/telegram_updates.py:74-106` routes message/callback updates to `core.bot_service.process_update`.

### 2) Public commands
`send/core/bot_service.py:230-238` handles `/start`, `/help`, `/status` without admin auth.

### 3) Admin command gate order
For `/admin`, `/strategy`, `/thresholds`, `/sr`, `/spike`, `/symbols`, `/engine`, `/debug`, `/report`:
1. Command recognized (`send/core/bot_service.py:239`).
2. **Chat context check first** via `in_admin_context(chat_id)` (`:240-242`).
3. Only if chat is allowed, call `handle_admin_command_v2(text, user_id)` (`:243`).
4. `admin_commands` then applies role/permission checks (`send/core/admin_commands.py:354-355`, per-command `require_permission`).

### 4) `in_admin_context` behavior
`send/core/bot_service.py:47-54`:
- if `ADMIN_CONTROL_CHAT_ID == 0` => deny (fail-closed);
- otherwise requires exact `chat_id == ADMIN_CONTROL_CHAT_ID`.

### 5) Thread/topic behavior (current)
- Incoming admin gate uses **chat ID only** (no thread check).
- Reply thread uses incoming `message_thread_id` only (`send/core/bot_service.py:56-65`, `send/core/telegram_targets.py:51-61`).
- `ADMIN_CONTROL_THREAD_ID` currently is not used for admin command authorization.

### 6) No interactive password/session flow in current code
No login prompt state machine, no password validator, no session token table, no logout/unlock command.

## Why current live behavior is "Access denied (wrong chat)."
Given:
- `ADMIN_CONTROL_CHAT_ID=-1003855058603`
- `OWNER_TELEGRAM_ID=7553887987`

When owner sends admin command in private chat:
- incoming `chat_id` is private user chat id, not `-1003855058603`;
- check fails at `send/core/bot_service.py:240-242`;
- bot returns `"Access denied (wrong chat)."`.

This occurs **before** permission evaluation in `admin_commands`.
