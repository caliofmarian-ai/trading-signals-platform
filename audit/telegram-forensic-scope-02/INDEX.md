# TELEGRAM FORENSIC AUDIT — SCOPE-02 INDEX

## All 9 audit deliverables (one dedicated audit directory)

HEAD at audit completion: `9912c14` (branch `copilot/telegram-capability-recovery-audit`)

### Reports produced in this directory (`audit/telegram-forensic-scope-02/`)

| # | Report | Path |
|---|---|---|
| 5 | TELEGRAM_LEGACY_UI_INVENTORY | `audit/telegram-forensic-scope-02/TELEGRAM_LEGACY_UI_INVENTORY.md` |
| 6 | TELEGRAM_UI_FLOW_MAP | `audit/telegram-forensic-scope-02/TELEGRAM_UI_FLOW_MAP.md` |
| 7 | TELEGRAM_BUTTON_AND_CALLBACK_REGISTER | `audit/telegram-forensic-scope-02/TELEGRAM_BUTTON_AND_CALLBACK_REGISTER.md` |
| 8 | OLD_VS_CURRENT_TELEGRAM_UI_COMPARISON | `audit/telegram-forensic-scope-02/OLD_VS_CURRENT_TELEGRAM_UI_COMPARISON.md` |
| 9 | CANONICAL_UI_RESTORATION_PLAN | `audit/telegram-forensic-scope-02/CANONICAL_UI_RESTORATION_PLAN.md` |

### Reports produced in scope-01 (root level, commit `9912c14`)

| # | Report | Path |
|---|---|---|
| 1 | TELEGRAM_AUTH_FORENSIC_AUDIT | `TELEGRAM_AUTH_FORENSIC_AUDIT.md` |
| 2 | AUTH_FLOW_DIAGRAM | `AUTH_FLOW_DIAGRAM.md` |
| 3 | OWNER_ACCESS_COMPARISON | `OWNER_ACCESS_COMPARISON.md` |
| 4 | RESTORATION_PLAN | `RESTORATION_PLAN.md` |

Additional supporting audit evidence: `audit/telegram-admin-authentication-audit-01/` (20 reports from prior agent session).

---

## Mandatory unresolved questions — answers

### Why does `/report` return "Access denied (wrong chat)" in the owner's private bot conversation even though OWNER_TELEGRAM_ID is configured?

**Finding:** `/report` IS in `_OWNER_PRIVATE_COMMANDS` (commit `64345ae`+, current HEAD). The command is allowed in owner private DM.

**Root causes if the owner still observes denial:**
1. `OWNER_TELEGRAM_ID` env var is unset, empty, or set to a non-matching value → `is_owner(user_id)` returns `False` → `_is_owner_private_context` returns `False` → denied.
2. The chat type from Telegram is not `"private"` (e.g., user is in a group forwarding) → `_is_owner_private_context` returns `False`.
3. The deployed Railway instance predates commit `64345ae` (2026-07-14) which introduced owner-private access. The running container has commit `49aaeb4` or earlier which blocked private DM entirely.

**Evidence:** `send/core/bot_service.py:40-52` (`_OWNER_PRIVATE_COMMANDS` set includes `/report`), `send/core/bot_service.py:78-89` (`_is_owner_private_context` logic), `send/core/bot_service.py:102-105` (`_can_run_admin_command` gate).

### Which commands currently allow owner private-chat access and which still require the configured admin chat?

**Owner private DM allowed:**
`/admin`, `/strategy`, `/thresholds`, `/sr`, `/spike`, `/symbols`, `/engine`, `/debug`, `/report`, `/roles`, `/affiliate`
Source: `send/core/bot_service.py:40-52` (`_OWNER_PRIVATE_COMMANDS` frozenset)

**Admin topic required (blocked in private):**
`/roles_reload` (not in `_OWNER_PRIVATE_COMMANDS`)
`RELOAD_ROLES_CONFIRM` callback action (explicitly returns `"Access denied (wrong chat)."` in private context: `send/core/bot_service.py:193-199`)
`♻️ Reload Roles` button (not rendered in private: `telegram_admin_ui.admin_home_markup(include_roles_reload=False)`)

**Public (any chat, no auth):**
`/start`, `/help`, `/status`

### Did the historical Hetzner implementation actually use an admin password?

**Finding: No.**

**Repository evidence examined:**
- `send/legacy/bot_control.py` (commit `0fb9112`): No password prompt, no password check, no password env var.
- `send/_archive/backups/bot_service.py.bak_step16` through `bak_step26`: No password prompt, no hash comparison, no session token, no `ADMIN_PASSWORD` env var.
- `send/core/admin_permissions.py` (all commits): Role/permission only; no password field.
- Full grep across all `.py` files and all commits: No `ADMIN_PASSWORD`, `PASSWORD_HASH`, `bcrypt`, `pbkdf2`, `/login`, `/logout`, `/unlock`, session TTL, or session token storage.
- `.env.example`: No `ADMIN_PASSWORD` entry.

**Distinction from owner recollection:** If the owner recalls a password-based experience, this may refer to: (a) the Telegram bot token being treated as a "password" for the bot itself; (b) an external authentication layer (reverse proxy, VPN) that was not part of this codebase; or (c) the role-ID system where knowing and providing your Telegram user ID was the implicit credential. The repository contains no code that implements any admin password mechanism.

---

## Commit hash at completion

`9912c14` — this is the HEAD commit at the time these reports were written and will be superseded by the commit that adds this directory.
The commit that persists these 5 reports is the one immediately following `9912c14` on branch `copilot/telegram-capability-recovery-audit`.
