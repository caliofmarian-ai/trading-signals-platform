# COMMAND_PERMISSION_AND_CONTEXT_MATRIX

| Surface | Gate | Context rule | Behavior on mismatch | Logging |
|---|---|---|---|---|
| Admin slash commands (`/admin`, etc.) | `has_permission(user_id, "admin.view")` + per-command permissions in `admin_commands` | No chat gate in slash path; uses sender `user_id` roles | returns unauthorized text if permission denied | no explicit warning event for unknown slash commands |
| Unknown slash commands (e.g. `/start`, `/help`, `/status`) | N/A | N/A | silently ignored | none |
| Admin callbacks (legacy panel family) | `in_admin_context(chat_id)` in `bot_service` | `ADMIN_CONTROL_CHAT_ID` must be non-zero and equal to callback chat id | returns `Access denied (wrong chat).` | no explicit warning event |
| Outcome callbacks (`VOTE_*`) | outcome service checks membership + callback context | chat/message must match registered contexts when provided | rejected with reason (`unauthorized_callback_context`, etc.) | warning events via outcome service |

## Role source
- `admin_roles.json` + `OWNER_TELEGRAM_ID` fallback loaded by `core.admin_permissions`

## Thread/topic behavior
- Incoming admin slash command acceptance does **not** check `ADMIN_CONTROL_THREAD_ID`.
- Outgoing admin reply attaches `message_thread_id=ADMIN_CONTROL_THREAD_ID` when non-zero.
