# CHAT_TOPIC_OWNER_PASSWORD_AUTH_MATRIX

| Layer | Current implementation | Historical implementation | Evidence status |
|---|---|---|---|
| Owner identity (`OWNER_TELEGRAM_ID`) | Used as roles fallback in `admin_permissions` | Same roles-based pattern present | Confirmed |
| Role/permission checks | `admin_permissions` + `admin_commands` | Present since initial import | Confirmed |
| Admin chat restriction | Enforced for admin slash commands in current `bot_service` | Enforced for admin callbacks earlier; slash gate added later (`49aaeb4`) | Confirmed |
| Topic/thread restriction | Not used in auth gate; reply threading only | Historically thread often forced for replies (`ADMIN_CONTROL_THREAD_ID`) | Confirmed |
| Password login | Not implemented | Not found in repo history reviewed | Not evidenced |
| Interactive session expiry/logout | Not implemented | Not found | Not evidenced |

## Matrix vs requested options
- A (admin topic only, no password): partially matches current behavior (chat-level restriction, not strict topic auth).
- B/C/D (password layer): no code evidence in audited repository history.
- E (evidence-backed): role-based authorization + context-gating evolution, with no password/session layer in codebase.
