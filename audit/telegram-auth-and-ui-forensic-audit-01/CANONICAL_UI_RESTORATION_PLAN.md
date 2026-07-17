# CANONICAL_UI_RESTORATION_PLAN

## Audit metadata

- **Audited HEAD:** `0e736ae251dcb81dee7d13a34bbcfafcafe36967`
- **No code modifications were made. This is a design document only.**
- **Canonical control plane files:**
  - `send/core/bot_service.py`
  - `send/core/admin_commands.py`
  - `send/core/telegram_admin_ui.py`
  - `send/core/telegram_publisher.py`
  - `send/core/admin_permissions.py`

---

## 1. Restoration principles (non-negotiable)

1. **No second control plane.** All admin mutations route through `admin_commands.py`.
2. **No password authentication.** Identity is Telegram user-ID + role/permission model. No password exists, no password is needed.
3. **No session tokens or TTL state.** No login/logout mechanics.
4. **No new env variables for auth.** Existing `OWNER_TELEGRAM_ID`, `ADMIN_CONTROL_CHAT_ID`, `ADMIN_CONTROL_THREAD_ID`, `ADMIN_ROLES_CONFIG` remain the identity/context sources.
5. **Permission authority stays in `admin_permissions.py`.** No inline permission checks in `telegram_admin_ui.py`.
6. **Fail-closed preserved for non-owner flows.** Admin topic requirement stays for non-owner contexts.
7. **`bot_control.py` is not restored as a separate process.** Romanian runner removed by design.
8. **Historical justification for password:** No password implementation ever existed in the repository. Therefore no fallback password auth is justified or added.

---

## 2. Owner access prerequisite (configuration, not code)

**Problem:** `/report` (and other commands) return "Access denied (wrong chat)" in owner's private DM.
**Root cause:** `OWNER_TELEGRAM_ID` Railway variable is absent or incorrect; `is_owner(user_id)` returns False.
**Fix:** Set `OWNER_TELEGRAM_ID` to the owner's numeric Telegram user ID in Railway.

```
Railway variable:  OWNER_TELEGRAM_ID = <owner_numeric_telegram_id>
```

No code change required. The `_is_owner_private_context` path already exists and correctly allows all 11 `_OWNER_PRIVATE_COMMANDS` in private DM when `is_owner(user_id)` returns True.

---

## 3. Design — single restoration architecture

### 3.1 Owner private DM — already functional

The current code contains `_OWNER_PRIVATE_COMMANDS` which lists all 11 admin slash commands.
The `_is_owner_private_context` function correctly gates on `is_owner(user_id)`.
The `_can_use_admin_callback` function correctly allows all `ADMIN_NAV:*` callbacks in owner private DM.
**No code change needed for slash or callback access in private DM.**

### 3.2 Symbols: restore inline toggle keyboard

**Problem:** `/symbols` shows a text list; no checkbox-style toggle keyboard exists.

**Design — changes to `send/core/telegram_admin_ui.py`:**
- Add `symbols_toggle_markup(all_symbols: list[str], active_symbols: list[str]) -> dict`
  - Per-symbol buttons: `✅ {SYM}` or `⬜ {SYM}` → `ADMIN_NAV:SYM_TOGGLE:{SYM}`
  - Layout: 3 buttons per row (matching legacy Era A)
  - Control row: `[✅ All]` → `ADMIN_NAV:SYMBOLS_ALL`, `[⬜ None]` → `ADMIN_NAV:SYMBOLS_NONE`, `[🔄 Refresh]` → `ADMIN_NAV:SYMBOLS`
  - Back row: `[⬅️ Admin]` → `ADMIN_NAV:HOME`

**Design — changes to `send/core/bot_service.py`:**
- Extend `_handle_admin_navigation_action` to handle:
  - `SYM_TOGGLE:{sym}` → call `admin_commands.handle_admin_command("/symbols add/remove {sym}", user_id)` based on current state
  - `SYMBOLS_ALL` → call `admin_commands` to add all known symbols
  - `SYMBOLS_NONE` → call `admin_commands` to remove all symbols

**Design — changes to `send/core/admin_commands.py`:**
- Add `handle_symbols_toggle(symbol: str, user_id: int) -> str`
- Add `get_all_known_symbols() -> list[str]` (reads from symbols config)

**Callback family added:** `ADMIN_NAV:SYM_TOGGLE:{SYM}`, `ADMIN_NAV:SYMBOLS_ALL`, `ADMIN_NAV:SYMBOLS_NONE`

### 3.3 Buffer mode: restore three-option keyboard

**Problem:** No strategy quick-select keyboard; mutations require full slash command with arguments.

**Design — changes to `send/core/telegram_admin_ui.py`:**
- Add `strategy_quick_markup(current_profile: str) -> dict`
  - Buttons: `[✅/⬜ CONSERVATIVE]` → `ADMIN_NAV:STRATEGY_CONSERVATIVE`, `[✅/⬜ BALANCED]` → `ADMIN_NAV:STRATEGY_BALANCED`, `[✅/⬜ AGGRESSIVE]` → `ADMIN_NAV:STRATEGY_AGGRESSIVE`
  - Current profile shown with `✅`
  - Back row: `[⬅️ Admin]` → `ADMIN_NAV:HOME`

**Design — changes to `send/core/admin_commands.py`:**
- Add `handle_strategy_profile(profile: str, user_id: int) -> str`
  - Calls `_set_threshold` (and optionally SR/spike presets) for a named profile
  - Permission gate: `strategy.thresholds.write`

**Design — changes to `send/core/bot_service.py`:**
- Extend `_handle_admin_navigation_action` to handle `STRATEGY_CONSERVATIVE`, `STRATEGY_BALANCED`, `STRATEGY_AGGRESSIVE`

**Callback family added:** `ADMIN_NAV:STRATEGY_CONSERVATIVE`, `ADMIN_NAV:STRATEGY_BALANCED`, `ADMIN_NAV:STRATEGY_AGGRESSIVE`

### 3.4 Docs viewer: restore from panel

**Problem:** No docs viewer button; `/docs` and `/files` commands do not exist.

**Design — changes to `send/core/telegram_admin_ui.py`:**
- Add `docs_list_markup(filenames: list[str]) -> dict`
  - One button per file: `[{filename}]` → `ADMIN_NAV:DOC:{filename}`
  - Back row: `[⬅️ Admin]` → `ADMIN_NAV:HOME`

**Design — changes to `send/core/admin_commands.py`:**
- Add `handle_docs_list(docs_dir: str, user_id: int) -> tuple[str, list[str]]`
  - Returns title text + list of filenames
  - Permission gate: `debug.view` (or new `docs.view` permission)
- Add `handle_doc_render(filename: str, docs_dir: str, user_id: int) -> str or bytes`
  - Returns file content or signals publisher to call `sendDocument`

**Design — changes to `send/core/bot_service.py`:**
- Extend `_handle_admin_navigation_action` to handle `DOCS` (list) and `DOC:{filename}` (send)
- For `DOC:{filename}`: call `telegram_publisher.send_document(chat_id, path, thread_id=...)` after permission check

**New slash commands:**
- `/files` → alias to `handle_docs_list` (list files)
- `/docs` → same
- `/audit_runtime` → read observability JSONL and send last N lines as text or attachment
- `/diagnose` → enhanced `/debug` with system health check sequence

**Callback family added:** `ADMIN_NAV:DOCS`, `ADMIN_NAV:DOC:{filename}`

### 3.5 Report delivery as .md/.txt/.jsonl

**Design — changes to `send/core/admin_commands.py`:**
- Extend `/report` to support: `/report` (text), `/report md`, `/report txt`, `/report jsonl`
- Add `_report_as_file(fmt: str) -> str (path)` that writes the latest report summary to a temp file
- Return file path for publisher to call `sendDocument`

**Design — changes to `send/core/bot_service.py`:**
- In `_render_panel_for_command`, detect file-return signals and route to `telegram_publisher.send_document`

### 3.6 Topic routing

Topic routing is already functional via `reply_target_from_message(message)` and `valid_thread_id()`.
Outgoing admin replies preserve the incoming `message_thread_id` via `telegram_publisher.send_message(thread_id=...)`.
No change required for topic routing.

---

## 4. Railway variables — complete register

### Already existing (no change)

| Variable | Purpose | Required? |
|---|---|---|
| `TELEGRAM_BOT_TOKEN` | Bot API authentication | Yes — mandatory |
| `OWNER_TELEGRAM_ID` | Owner identity for private DM access | Yes — critical for owner access |
| `ADMIN_CONTROL_CHAT_ID` | Admin group/supergroup ID for command gate | Yes — mandatory for admin topic |
| `ADMIN_CONTROL_THREAD_ID` | Topic thread ID within admin group | Optional (any topic allowed if 0) |
| `ADMIN_ROLES_CONFIG` | Path to admin_roles.json | Optional (OWNER_TELEGRAM_ID fallback) |
| `ADMIN_PERMISSIONS_CONFIG` | Path to admin_permissions.json | Optional (hardcoded matrix fallback) |
| `ENABLE_TELEGRAM` | Enable Telegram polling | Yes — must be `true` |

### Optional (for enhanced restoration)

| Variable | Purpose | When to add |
|---|---|---|
| `ADMIN_PROOF_CHAT_ID` | Destination for admin proof audit messages | If audit delivery to Telegram is wanted |
| `ADMIN_PROOF_THREAD_ID` | Thread for audit proof messages | Same |
| `DOCS_DIR` | Path to documents for `/docs`, `/files` | If docs viewer is restored |

### New variables (for restoration phase 2 only)

| Variable | Purpose | Notes |
|---|---|---|
| `ADMIN_DOCS_DIR` | Override docs directory for docs viewer | Canonical default: `/opt/binarybot/docs` |
| `ADMIN_REPORTS_DIR` | Override reports directory for report delivery | Canonical default: `/opt/binarybot/analytics/reports` |

### Legacy-only (not recommended)

| Variable | Why not recommended |
|---|---|
| `ADMIN_USER_ID` | Old single-user identity; superseded by `ADMIN_ROLES_CONFIG` + `OWNER_TELEGRAM_ID` |
| `ADMIN_SUPERGROUP_ID` / `ADMIN_GROUP_ID` | Signal distribution only; auth uses `ADMIN_CONTROL_CHAT_ID` |

---

## 5. Fail-closed RBAC

Current implementation is already fail-closed:
- `ADMIN_CONTROL_CHAT_ID == 0` → deny (`in_admin_context` returns False)
- Missing `admin_roles.json` → env fallback; missing env → empty role list → USER role → `admin.view` denied
- `has_permission` returns False for any unrecognized role

No change needed for RBAC fail-closed behavior.

---

## 6. Rate limiting

No rate limiting exists in current implementation.
If needed, add a rate-limit decorator to `handle_admin_command` in `admin_commands.py`:
- Per-user rate limit: max N mutations per minute per user_id
- Implemented as a simple in-memory counter dict (TTL sliding window)
- Gate: `_check_rate_limit(user_id)` before permission check
- No new env variable required; defaults configurable as constants

---

## 7. Audit proof generation

Already implemented:
- `admin_commands._audit(user_id, command, result, details)` writes to `ADMIN_EVENTS_PATH` and `ADMIN_PROOFS_PATH`
- `observability_logger.send_admin_proof_telegram(...)` sends proof to `ADMIN_PROOF_CHAT_ID` if configured

Every mutation command (`/thresholds`, `/sr`, `/spike`, `/symbols add/remove`, `/roles_reload`) calls `_audit(...)`.

For restoration additions: each new mutation handler (symbol toggle, strategy profile set) must call `_audit(...)` before returning.

---

## 8. Scope of changes: minimal change summary

| File | Change type | Estimated lines |
|---|---|---|
| `send/core/telegram_admin_ui.py` | Add 4 markup functions, extend parse_action | ~70 |
| `send/core/bot_service.py` | Extend `_handle_admin_navigation_action` + `_OWNER_PRIVATE_COMMANDS` (if new slashes added) | ~30 |
| `send/core/admin_commands.py` | Add 5 handlers, expose in `handle_admin_command` | ~80 |
| `send/core/telegram_runtime.py` | Add CommandSpec entries for `/files`, `/docs`, `/audit_runtime`, `/diagnose` | ~10 |
| `send/core/admin_permissions.py` | Optionally add `docs.view` to PERMISSION_MATRIX | ~5 |
| New tests | Cover new actions, both contexts | ~60 |

**Total: ~255 lines. No new dependencies. No new external processes. No new auth mechanisms.**

---

## 9. What this plan explicitly does NOT do

| Excluded | Reason |
|---|---|
| Restore `bot_control.py` as separate process | Violates restoration guardrail #7 |
| Restore Romanian-language UI | Runner was intentionally deleted; English canonical |
| Re-introduce `BUFFER_*`, `SYM_TOGGLE:*`, `DOC:*` callback formats | Replaced by `ADMIN_NAV:` canonical prefix |
| Add admin password authentication | No historical justification; not needed |
| Add session management / TTL / logout | No historical justification; not needed |
| Restore fail-open `in_admin_context` | Security regression (GAP-013) |
| Restore `rbac.json` / `ADMIN_USER_ID` identity | Superseded by canonical roles config |
| Create a second control plane | Violates guardrail #1 |
