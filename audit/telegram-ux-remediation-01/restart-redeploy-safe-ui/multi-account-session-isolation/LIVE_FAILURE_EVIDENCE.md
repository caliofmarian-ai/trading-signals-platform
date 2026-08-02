# Live Failure Evidence — Multi-Account Session Isolation

**Issue:** #31

## Observed Behavior

| Step | Account | Action | Result |
|------|---------|--------|--------|
| 1 | USER | `/start` | ✅ Welcome message sent |
| 2 | USER | `/help` | ✅ Edited existing message |
| 3 | USER | `/status` | ✅ Edited existing message |
| 4 | ADMIN | Switched accounts | — |
| 5 | ADMIN | Deleted conversation history | — |
| 6 | ADMIN | `/start` | ❌ No response |
| 7 | ADMIN | All commands | ❌ Silent |
| 8 | USER | Switched back | — |
| 9 | USER | Any command | ✅ Still working |

## Classification

- Telegram polling: **ALIVE** (USER updates processed)
- Update processing: **ALIVE** (USER commands executed)
- ADMIN session: **STUCK** on stale persisted message_id
- USER session: **UNAFFECTED** (different session key)

## Recovery

After this implementation:
1. ADMIN `/start` triggers edit attempt on stale message_id
2. Telegram returns "message to edit not found"
3. `clear_active_message` atomically removes session from memory AND persisted state
4. `delete_telegram_ui_session` verifies persisted absence
5. Exactly one replacement message is sent
6. Replacement is tracked; subsequent commands edit it
7. USER session remains unchanged throughout
