# AUTH_FLOW_DIAGRAM

## 1) Hetzner-era effective slash `/admin` flow (pre-49aaeb4)

```mermaid
flowchart TD
  A[Telegram /admin message] --> B[bot_service.process_update]
  B --> C{Command in admin set?}
  C -- yes --> D[handle_admin_command_v2 text user_id]
  D --> E{has_permission admin.view?}
  E -- no --> F[Unauthorized]
  E -- yes --> G[Admin response]
```

Evidence:
- `0fb9112:send/core/bot_service.py:548-556`
- `d7e7213:send/core/bot_service.py:156-168`
- `send/core/admin_commands.py` + `send/core/admin_permissions.py`

---

## 2) 49aaeb4 hardened flow that introduced wrong-chat slash denial

```mermaid
flowchart TD
  A[Telegram /admin message] --> B[bot_service.process_update]
  B --> C{Command in admin_command_names?}
  C -- yes --> D{in_admin_context chat_id?}
  D -- no --> E[Access denied wrong chat]
  D -- yes --> F[handle_admin_command_v2]
  F --> G[Permission checks]
```

Evidence:
- `49aaeb4:send/core/bot_service.py:239-243`

---

## 3) Current canonical flow (64345ae+)

```mermaid
flowchart TD
  A[Telegram /admin message] --> B[bot_service.process_update]
  B --> C{cmd in admin_command_names?}
  C -- yes --> D{_can_run_admin_command?}
  D --> E{Owner private context?}
  E -- yes --> F{cmd in OWNER_PRIVATE_COMMANDS?}
  F -- yes --> I[Render admin panel response]
  F -- no --> H[Access denied wrong chat]
  E -- no --> J{Admin topic context valid?}
  J -- yes --> I
  J -- no --> H
  I --> K[admin_commands permission layer]
```

Evidence:
- `send/core/bot_service.py:40-52,78-105,398-404`

---

## 4) Callback/admin-panel context flow (historical and current)

```mermaid
flowchart TD
  A[Callback query] --> B{Admin callback?}
  B -- yes --> C{Admin context check}
  C -- fail --> D[Access denied wrong chat]
  C -- pass --> E[Action handler]
```

Notes:
- Legacy callback context checks existed already in imported Hetzner snapshot (`0fb9112:275-281`).
- BATCH-05 made context default fail-closed when `ADMIN_CONTROL_CHAT_ID` missing (`d7e7213:34-40`).
- Current uses topic-aware context for callbacks (`send/core/bot_service.py:90-99,358-363`).
