# OWNER_ACCESS_COMPARISON

## Audit metadata

- **Audited HEAD:** `0e736ae251dcb81dee7d13a34bbcfafcafe36967`
- **No code modifications were made during this audit.**
- **Evidence:** `send/core/bot_service.py`, `send/core/admin_permissions.py`, `send/core/telegram_runtime.py`, git history

---

## Section 1 — What the owner can do at HEAD `0e736ae`

### Precondition for owner private DM access

`OWNER_TELEGRAM_ID` Railway variable must be set to the correct numeric Telegram user ID.
Without this, `is_owner(user_id)` returns False and all private DM admin commands are denied.

### Owner private DM: slash commands

| Command | Allowed in private DM? | Permission required | Code gate |
|---|---|---|---|
| `/start` | ✅ Always (public) | None | `bot_service.py` public branch |
| `/help` | ✅ Always (public) | None | same |
| `/status` | ✅ Always (public) | None | same |
| `/admin` | ✅ if is_owner | `admin.view` | `_OWNER_PRIVATE_COMMANDS` |
| `/strategy` | ✅ if is_owner | `strategy.view` | same |
| `/thresholds` | ✅ if is_owner | `strategy.view` / `.thresholds.write` | same |
| `/sr` | ✅ if is_owner | `strategy.view` / `.sr.write` | same |
| `/spike` | ✅ if is_owner | `strategy.view` / `.spike.write` | same |
| `/symbols` | ✅ if is_owner | `strategy.view` / `.symbols.write` | same |
| `/engine` | ✅ if is_owner | `engine.view` | same |
| `/debug` | ✅ if is_owner | `debug.view` | same |
| `/report` | ✅ if is_owner | `reports.view` | same |
| `/roles` | ✅ if is_owner | `roles.view` | same |
| `/affiliate` | ✅ if is_owner | `affiliate.view` | same |
| `/roles_reload` | ❌ Never in private DM | — | NOT in `_OWNER_PRIVATE_COMMANDS` |

### Owner private DM: callbacks

| Callback family | Allowed in private DM? | Note |
|---|---|---|
| `ADMIN_NAV:*` (all except RELOAD_ROLES_CONFIRM) | ✅ if is_owner | `_can_use_admin_callback` |
| `ADMIN_NAV:RELOAD_ROLES_CONFIRM` | ❌ Explicit deny | `_handle_admin_navigation_action` returns "Access denied (wrong chat)." |
| `ADMIN_NAV:RELOAD_ROLES_EXEC` | ❌ Blocked indirectly | Requires confirmation via RELOAD_ROLES_CONFIRM first, which is denied |
| `VOTE_*` / `OUTCOME:*` | ✅ (no context check) | Public outcome callbacks |

### Owner in admin topic (ADMIN_CONTROL_CHAT_ID match, thread optional)

All commands allowed. All callbacks allowed. Same as any authorized admin user in that chat.

---

## Section 2 — What the owner CANNOT do at HEAD (when configuration correct)

| Action | Why blocked | Code |
|---|---|---|
| `/roles_reload` from private DM | Not in `_OWNER_PRIVATE_COMMANDS` | `bot_service.py _can_run_admin_command` |
| RELOAD_ROLES_CONFIRM from private DM | Explicit denial even after callback auth passes | `_handle_admin_navigation_action` line checking `owner_private` |
| Admin commands from non-owner private DM | `is_owner` returns False → admin topic gate fails | `_is_owner_private_context` |
| Admin commands from any chat other than private DM or ADMIN_CONTROL_CHAT_ID | Neither gate passes | Both branches in `_can_run_admin_command` |

---

## Section 3 — Historical comparison

| Era | Owner private DM behavior | Code evidence |
|---|---|---|
| `d7e7213` (pre-gate, per stored memory) | All admin commands worked from any chat; no context gate on slash path | Stored memory + HISTORICAL_ADMIN_AUTH_FLOW.md |
| `49aaeb4` (gate introduced) | All admin commands denied from private DM; no owner exception | Stored memory; ROOT_CAUSE_REGISTER RC-AUTH-001 |
| Current HEAD `0e736ae` | Admin commands allowed in private DM IF `is_owner(user_id)` True (requires OWNER_TELEGRAM_ID configured correctly) | `bot_service.py _OWNER_PRIVATE_COMMANDS` + `_is_owner_private_context` |

---

## Section 4 — Access comparison matrix: owner vs roles

| Access type | OWNER | PRIMARY_ADMIN | STRATEGY_ADMIN | RESEARCH_ADMIN | ANALYST | MODERATOR | AFFILIATE_ADMIN | USER |
|---|---|---|---|---|---|---|---|---|
| Private DM slash commands | ✅ (11 commands) | ❌ (no private gate) | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Admin topic slash commands | ✅ | ✅ | ✅ (limited) | ✅ (limited) | ✅ (limited) | ✅ (limited) | ✅ (affiliate only) | ❌ |
| admin.view | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ |
| engine.restart | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| strategy.thresholds.write | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| roles.write | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| debug.view | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |
| reports.view | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |
| affiliate.view.any | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| affiliate.view.own | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ (own scope) | ❌ |

Note: OWNER bypasses all permission checks via `is_owner(user_id)` shortcut in `has_permission()`:
```python
def has_permission(user_id, permission, ...):
    if is_owner(user_id):
        return True   # bypass all permission matrix
    ...
```

---

## Section 5 — Railway variables required for owner access

| Variable | Required for owner private DM? | Effect if missing |
|---|---|---|
| `OWNER_TELEGRAM_ID` | **Yes — critical** | `is_owner()` returns False; private DM access denied for all commands |
| `ADMIN_CONTROL_CHAT_ID` | No (for private DM), Yes (for admin topic) | Admin topic path blocked |
| `ADMIN_CONTROL_THREAD_ID` | No | Topic thread check skipped (any topic within admin chat allowed) |
| `ADMIN_ROLES_CONFIG` | No (env var fallback is sufficient) | Uses default path; if not mounted, env var fallback handles owner identity |
| `TELEGRAM_BOT_TOKEN` | Yes (bot won't poll without it) | Bot completely offline |
