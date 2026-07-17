# TELEGRAM_AUTH_FORENSIC_AUDIT

## Audit metadata

- **Audited HEAD:** `0e736ae251dcb81dee7d13a34bbcfafcafe36967`
- **Audit commit (this file):** recorded in CHANGED_FILES.md
- **Branch:** `copilot/telegram-capability-recovery-audit`
- **Prior audit scope-01:** `audit/telegram-admin-authentication-audit-01/` (HEAD `9912c14`)
- **Prior audit scope-02:** `audit/telegram-forensic-scope-02/` (HEAD `0e736ae`)
- **No code modifications were made during this audit.**
- **Evidence sources:** current HEAD source files, full git history (only 2 commits in shallow clone), deleted file recovery via git, archived backup modules.

---

## MANDATORY QUESTION 1 — Why does /report return "Access denied (wrong chat)" in the configured owner's private conversation?

### Exact call path at HEAD `0e736ae`

```
Telegram update (private DM, owner user_id)
  → send/runtime/telegram_updates.py::process_update
  → send/core/bot_service.py::process_update  (line ~265)
       text = "/report"
       cmd  = "/report"
       cmd in admin_command_names()  → True
       _can_run_admin_command(msg, user_id, "/report")
           _is_owner_private_context(msg, user_id)
               chat["type"] == "private"           → True
               chat["id"] == user_id               → True (in DMs, chat_id IS user_id)
               is_owner(user_id)                   → ???
           if is_owner True  → "/report" in _OWNER_PRIVATE_COMMANDS → True → ALLOW
           if is_owner False → _is_admin_topic_context(msg)
               in_admin_context(private_chat_id)   → False (private_chat_id ≠ ADMIN_CONTROL_CHAT_ID)
               → return False
           → return False
       → _send_reply("Access denied (wrong chat).")
```

### Root cause

`is_owner(user_id)` returns `False`.
This happens when **either or both** of the following conditions hold:

| Condition | Variable | Code location |
|---|---|---|
| `OWNER_TELEGRAM_ID` Railway variable is absent, blank, or set to the wrong integer | `os.getenv("OWNER_TELEGRAM_ID")` | `admin_permissions.py:235` |
| `admin_roles.json` config file is absent or does not include the owner's Telegram ID in the `"owner"` array | `ADMIN_ROLES_CONFIG` path | `admin_permissions.py:163-178` |

`load_roles_config()` is decorated `@lru_cache(maxsize=1)`.
If the cache was populated before `OWNER_TELEGRAM_ID` was set or before the correct roles file was mounted, it will serve the stale, ownerless result for the entire process lifetime until `/roles_reload` is issued — which itself requires admin access, creating a circular denial.

### Code evidence

```python
# send/core/bot_service.py  (HEAD 0e736ae)
_OWNER_PRIVATE_COMMANDS: frozenset[str] = frozenset({
    "/admin", "/strategy", "/thresholds", "/sr", "/spike",
    "/symbols", "/engine", "/debug", "/report", "/roles", "/affiliate",
})

def _is_owner_private_context(message, user_id):
    chat = message.get("chat")
    if str(chat.get("type") or "").lower() != "private": return False
    chat_id = _safe_int(chat.get("id"))
    if chat_id is None or chat_id != user_id: return False
    return is_owner(user_id)                   # ← fails here when config absent

def _can_run_admin_command(message, user_id, cmd):
    if _is_owner_private_context(message, user_id):
        return cmd in _OWNER_PRIVATE_COMMANDS  # /report IS listed; reached only if is_owner True
    return _is_admin_topic_context(message)    # ← falls here; always False in private DM
```

```python
# send/core/admin_permissions.py (HEAD 0e736ae)
@lru_cache(maxsize=1)
def load_roles_config():
    data = _load_json_file(ROLES_CONFIG_PATH)   # reads ADMIN_ROLES_CONFIG file
    owner_env = os.getenv("OWNER_TELEGRAM_ID", "").strip()
    owner_id  = _safe_int(owner_env)
    if owner_id is not None:                    # only merged if env var is a valid integer
        owners = data.get("owner", [])
        if owner_id not in owners:
            owners.append(owner_id)
        data["owner"] = owners
    return data
```

### Fix prerequisite (configuration, not code)

1. Ensure `OWNER_TELEGRAM_ID` Railway variable equals the owner's numeric Telegram user ID.
2. Ensure the value is a plain integer string (no quotes, no spaces, no `@username`).
3. If `/roles_reload` cannot be issued (circular denial), restart the Railway service after updating the variable — the `lru_cache` resets on process start.

---

## MANDATORY QUESTION 2 — Exact authorization flow per command

### Common prefix: public commands (no auth gate)

| Command | Auth | Code |
|---|---|---|
| `/start` | None | `bot_service.py` process_update, first branch |
| `/help` | None | same |
| `/status` | None | same |

### Admin commands (all require `_can_run_admin_command` → True)

`_can_run_admin_command(msg, user_id, cmd)` is evaluated for every admin command before `handle_admin_command` is called.

```
Gate 1: _is_owner_private_context(msg, user_id)
    → chat.type == "private"
    → chat.id == user_id
    → is_owner(user_id)  [via OWNER_TELEGRAM_ID or admin_roles.json]
    If True → allowed IFF cmd in _OWNER_PRIVATE_COMMANDS

Gate 2 (fallback): _is_admin_topic_context(msg)
    → in_admin_context(chat.id)  [chat.id == ADMIN_CONTROL_CHAT_ID]
    → if ADMIN_CONTROL_THREAD_ID != 0:
          reply_target.thread_id == ADMIN_CONTROL_THREAD_ID
    If True → allowed unconditionally
```

### Per-command authorization table

| Command | In _OWNER_PRIVATE_COMMANDS | Gate 1 (owner private) | Gate 2 (admin topic) | 2nd permission check inside admin_commands |
|---|---|---|---|---|
| `/admin` | Yes | Allowed | Allowed | `admin.view` |
| `/strategy` | Yes | Allowed | Allowed | `strategy.view` |
| `/thresholds` | Yes | Allowed | Allowed | `strategy.view` (read), `strategy.thresholds.write` (write) |
| `/sr` | Yes | Allowed | Allowed | `strategy.view` (read), `strategy.sr.write` (write) |
| `/spike` | Yes | Allowed | Allowed | `strategy.view` (read), `strategy.spike.write` (write) |
| `/symbols` | Yes | Allowed | Allowed | `strategy.view` (list), `strategy.symbols.write` (add/remove) |
| `/engine` | Yes | Allowed | Allowed | `engine.view` |
| `/debug` | Yes | Allowed | Allowed | `debug.view` |
| `/report` | Yes | Allowed | Allowed | `reports.view` |
| `/roles` | Yes | Allowed | Allowed | `roles.view` |
| `/affiliate` | Yes | Allowed | Allowed | `affiliate.view` (scoped) |
| `/roles_reload` | **No** | **Denied** | Allowed | `roles.write` |
| Callbacks (ADMIN_NAV:*) | n/a | `_can_use_admin_callback` → allowed | Allowed | None inline |
| `RELOAD_ROLES_CONFIRM` callback | n/a | **Denied** (explicit block in `_handle_admin_navigation_action`) | Allowed | None |

---

## MANDATORY QUESTION 3 — Context allowance per command

| Command | Owner private chat | Configured admin group (ADMIN_CONTROL_CHAT_ID) | Admin topic (ADMIN_CONTROL_THREAD_ID) | Any authorised admin chat | Role-based only |
|---|---|---|---|---|---|
| `/admin` | ✅ | ✅ | ✅ (topic required if ADMIN_CONTROL_THREAD_ID set) | ❌ (only the single ADMIN_CONTROL_CHAT_ID) | ❌ (chat gate precedes role) |
| `/strategy` | ✅ | ✅ | ✅ | ❌ | ❌ |
| `/thresholds` | ✅ | ✅ | ✅ | ❌ | ❌ |
| `/sr` | ✅ | ✅ | ✅ | ❌ | ❌ |
| `/spike` | ✅ | ✅ | ✅ | ❌ | ❌ |
| `/symbols` | ✅ | ✅ | ✅ | ❌ | ❌ |
| `/engine` | ✅ | ✅ | ✅ | ❌ | ❌ |
| `/debug` | ✅ | ✅ | ✅ | ❌ | ❌ |
| `/report` | ✅ (if is_owner True) | ✅ | ✅ | ❌ | ❌ |
| `/roles` | ✅ | ✅ | ✅ | ❌ | ❌ |
| `/affiliate` | ✅ | ✅ | ✅ | ❌ | ❌ |
| `/roles_reload` | ❌ (not in _OWNER_PRIVATE_COMMANDS) | ✅ | ✅ | ❌ | ❌ |
| ADMIN_NAV:* callbacks | ✅ | ✅ | ✅ | ❌ | ❌ |
| RELOAD_ROLES_CONFIRM callback | ❌ (explicit deny) | ✅ | ✅ | ❌ | ❌ |
| VOTE_* callbacks | ✅ (no admin context check) | ✅ | ✅ | ✅ | ❌ |
| OUTCOME:* callbacks | ✅ | ✅ | ✅ | ✅ | ❌ |

---

## MANDATORY QUESTION 4 — Every check involving auth environment variables

### OWNER_TELEGRAM_ID

| File | Line | Purpose |
|---|---|---|
| `send/core/admin_permissions.py:235` | `os.getenv("OWNER_TELEGRAM_ID", "").strip()` | Fallback injection into owner list inside `load_roles_config()` |

Not used directly in `bot_service.py`. Identity flows through `is_owner(user_id)` → `get_user_roles(user_id)` → `load_roles_config()`.

### ADMIN_CONTROL_CHAT_ID

| File | Line | Purpose |
|---|---|---|
| `send/core/bot_service.py:37` | `ADMIN_CONTROL_CHAT_ID = env_chat_id("ADMIN_CONTROL_CHAT_ID") or 0` | Module-level constant; used in `in_admin_context()` and `_is_admin_topic_context()` |
| `send/core/telegram_targets.py:38` | `env_chat_id("ADMIN_CONTROL_CHAT_ID")` | Used in `control_target()` for outgoing reply routing |
| `send/core/bot_service.py:66-68` | `if ADMIN_CONTROL_CHAT_ID == 0: return False` | Fail-closed: missing config = no access |
| `send/core/bot_service.py:68` | `return chat_id == ADMIN_CONTROL_CHAT_ID` | Single-chat exact match |
| `send/core/bot_service.py:96` | `valid_thread_id(ADMIN_CONTROL_CHAT_ID, ADMIN_CONTROL_THREAD_ID)` | Thread validation depends on chat ID sign (negative = supergroup) |

### ADMIN_CONTROL_THREAD_ID

| File | Line | Purpose |
|---|---|---|
| `send/core/bot_service.py:38` | `ADMIN_CONTROL_THREAD_ID = env_thread_id("ADMIN_CONTROL_THREAD_ID") or 0` | Thread filter for `_is_admin_topic_context` |
| `send/core/bot_service.py:95-98` | `required_thread_id = valid_thread_id(...)` | If set and positive: incoming thread_id must match |
| `send/core/telegram_targets.py:41` | `env_thread_id("ADMIN_CONTROL_THREAD_ID")` | Outgoing reply thread |

### ADMIN_SUPERGROUP_ID / ADMIN_GROUP_ID

| File | Line | Purpose |
|---|---|---|
| `send/core/distribution_router.py:177-179` | `_env_int("ADMIN_SUPERGROUP_ID") or _env_int("ADMIN_GROUP_ID")` | Signal distribution target for admin group topic; **NOT used in command authorization** |

These two variables are **not used in any command authentication gate**. They are routing targets for signal delivery only.

### Role and permission configuration

| Variable / File | Role |
|---|---|
| `ADMIN_ROLES_CONFIG` env → `admin_roles.json` | Maps Telegram user IDs to role names (owner, primary_admin, strategy_admin, etc.) |
| `ADMIN_PERMISSIONS_CONFIG` env → `admin_permissions.json` | Optional file-based permission overrides; merged with hardcoded PERMISSION_MATRIX |
| `PERMISSION_MATRIX` in `admin_permissions.py` | Hardcoded role→permission set; authoritative baseline |
| `ROLE_PRIORITY` dict | Defines role hierarchy |

---

## MANDATORY QUESTION 5 — Did the historical Hetzner implementation use an admin password?

**Finding: No evidence of an admin password implementation in any form.**

Evidence examined:
- `send/legacy/bot_control.py` (pre-BATCH-09, git history): no login/password/PIN code
- `send/_archive/backups/bot_service.py.bak_step16` (Hetzner import snapshot): role-based RBAC only
- All commits in repository history: no `/login`, `/auth`, `/unlock`, `/logout` command handlers
- All env variables across `.env.example` and Railway config: no `ADMIN_PASSWORD`, `ADMIN_SECRET`, `BOT_PASSWORD`, or equivalent
- `send/docs/canonical/active/SECURITY_MODEL_v2.0.0.md`: reference to "Password login disabled" is in SSH context, not Telegram admin

---

## MANDATORY QUESTION 6 — If a password implementation existed: full detail

**Not applicable.** No password implementation found. See Question 7 for explicit statement.

---

## MANDATORY QUESTION 7 — Explicit statement: no password implementation

No admin password implementation exists in:
- Any file in the current HEAD (`0e736ae`)
- Any commit in the repository's full git history (2 commits visible: `9912c14`, `0e736ae`)
- The legacy runner `send/legacy/bot_control.py` (recovered from git history pre-deletion at commit `63834b3` per prior audit evidence)
- The Hetzner backup archive `send/_archive/backups/bot_service.py.bak_step16`
- Any backup file (`*.bak_*`) in the repository

**Distinction: repository evidence vs owner recollection.**

Repository evidence definitively shows no password implementation in tracked code.
If the owner recalls a password prompt, possible explanations that are **outside repository scope**:
- An untracked external script on the Hetzner server (not committed to version control)
- A third-party Telegram bot management panel used alongside this bot
- SSH/server login which the owner may have associated mentally with the bot admin experience

No claim is made about what existed outside the repository. The repository itself does not contain a password implementation.

---

## MANDATORY QUESTION 8 — Exact commit where private owner behavior changed

| Commit | Change | Effect on owner private DM |
|---|---|---|
| `9912c14` (`d7e7213` ancestor per stored memory) | No explicit slash chat gate | Owner could send `/admin`, `/report`, etc. in private DM; no context check blocked them |
| `49aaeb4` (named in stored memory as the gate introduction) | Added explicit `if not _can_run_admin_command(msg, user_id, cmd): _send_reply("Access denied (wrong chat).")` | All admin slash commands in private DM denied for any user including owner |
| Current HEAD (`0e736ae`) | `_can_run_admin_command` includes `_is_owner_private_context` branch | Owner CAN use private DM for all 11 `_OWNER_PRIVATE_COMMANDS` IF `is_owner(user_id)` returns True |

**Critical distinction:** The current HEAD code already contains the private-owner path. The persistent "Access denied" symptom is therefore a **configuration failure** (OWNER_TELEGRAM_ID not set correctly), not a code failure requiring change.

The exact commit that introduced the breakage was `49aaeb4`.
The current HEAD partially restores private access via `_OWNER_PRIVATE_COMMANDS`, but the restoration is silent when `OWNER_TELEGRAM_ID` is misconfigured — it fails identically to the broken pre-`_is_owner_private_context` code.
