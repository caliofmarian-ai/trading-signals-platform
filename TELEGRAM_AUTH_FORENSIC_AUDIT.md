# TELEGRAM_AUTH_FORENSIC_AUDIT

## Scope and evidence sources
- Full git history (after `git fetch --unshallow origin`), including deleted file history (`send/legacy/bot_control.py`).
- Current code + historical commits: `0fb9112`, `d7e7213`, `49aaeb4`, `64345ae`.
- Archived backups under `send/_archive/backups/`.

## Executive conclusion
Hetzner-era owner/admin access did **not** use password login or sessions. It was identity + role/permission based (Telegram user ID + RBAC/roles). The current `"Access denied (wrong chat)."` behavior was introduced intentionally as chat-context hardening, but it regressed the older owner private-chat experience.

---

## Requested findings (1–18)

### 1) Every implementation of `/admin` authentication

#### A. Legacy panel auth in `bot_service.py` (imported Hetzner snapshot)
- `0fb9112:send/core/bot_service.py:262-271` (`handle_admin_command(chat_id, user_id)`) required:
  - `in_admin_context(chat_id)` (`:78-83`) and
  - `get_role(user_id)` (`:62-70`) from RBAC/legacy admin identity.
- Callback path also required same checks (`:275-281`).

#### B. Canonical command auth in `admin_commands.py` (all modern stages)
- `0fb9112:send/core/admin_commands.py:302-312` and `d7e7213`/current equivalent:
  - `/admin` and all admin commands are gated by `has_permission(user_id, "admin.view")`.
- Permission resolution in `admin_permissions.py` uses roles + permission matrix.

#### C. Dispatcher-level gate evolution (`/admin` slash)
- `0fb9112:send/core/bot_service.py:548-556`: slash `/admin` family directly dispatched to `handle_admin_command_v2(text, user_id)` (no chat gate).
- `d7e7213:send/core/bot_service.py:156-168`: same (no slash chat gate).
- `49aaeb4:send/core/bot_service.py:239-243`: added slash chat gate (`if not in_admin_context(chat_id): Access denied (wrong chat)`).
- `64345ae:send/core/bot_service.py:102-105,398-404`: replaced with `_can_run_admin_command` (owner-private subset OR admin topic context).

### 2) Did authentication use `OWNER_TELEGRAM_ID` only?
No.
- Modern/canonical: owner is loaded from roles config (`owner` list) with env fallback append from `OWNER_TELEGRAM_ID`:
  - `send/core/admin_permissions.py:232-244`.
- Hetzner-import legacy panel path also supported RBAC + `ADMIN_USER_ID` fallback:
  - `0fb9112:send/core/bot_service.py:50-70`.

### 3) Did it request an admin password?
No evidence in current code, historical commits, deleted files, or archived backups.
- Global history searches for `/login`, `/unlock`, `/logout`, `ADMIN_PASSWORD`, `PASSWORD_HASH`, `SESSION_TTL`, `bcrypt`, `pbkdf2` returned no project-auth hits.

### 4) Where was password/hash stored?
Nowhere in project auth logic (because no password auth flow exists).

### 5) Session lifetime
No auth session mechanism exists (no login session state machine/token store/TTL).

### 6) Session expiration
None (no session implementation to expire).

### 7) Owner bypass rules
- Permission layer owner bypass (all periods with canonical `admin_permissions`):
  - `has_permission`: owner returns `True` immediately (`send/core/admin_permissions.py:344-353`).
- Current dispatcher owner private-chat bypass is **limited** to `_OWNER_PRIVATE_COMMANDS`:
  - `send/core/bot_service.py:40-52,102-105`.
  - `roles_reload` intentionally blocked in owner-private flow (`:193-199`, `:206-209`).

### 8) Admin role rules
From role + permission model:
- Roles: OWNER, PRIMARY_ADMIN, STRATEGY_ADMIN, RESEARCH_ADMIN, ANALYST, MODERATOR, AFFILIATE_ADMIN, USER.
- Hardcoded baseline permission matrix:
  - `send/core/admin_permissions.py:51-122`.
- File-based permission overlay (`admin_permissions.json`) merged in:
  - `send/core/admin_permissions.py:169-203,331-341`.

### 9) Moderator rules
- Baseline moderator permissions: `admin.view`, `engine.view`, `channels.view`:
  - `send/core/admin_permissions.py:112-116`.
- Effective permissions may be extended/overridden by `send/config/admin_permissions.json`.

### 10) Every command available after login
There is no login step. Effective admin command inventory is:
- `/admin`, `/strategy`, `/thresholds`, `/sr`, `/spike`, `/symbols`, `/engine`, `/debug`, `/report`, `/roles`, `/affiliate`, `/roles_reload`.
- Source: `send/core/telegram_runtime.py:21-38`.
- Public commands: `/start`, `/help`, `/status` (`:18-20`).
- Deleted legacy runner (`send/legacy/bot_control.py`) also had `/start`, `/forex`, `/crypto`, `/buffer`, `/open` (non-login UX).

### 11) How private chat access worked
- Hetzner-era slash admin commands (imported snapshot, and BATCH-05 before 49aaeb4):
  - Private chat admin commands were accepted at dispatcher level (no slash chat gate), then permission-checked by role/ID.
- Current:
  - Owner private chat allowed for command subset only (`send/core/bot_service.py:40-52,102-105`).
  - Non-owner private admin commands denied as wrong chat.

### 12) How supergroup access worked
- Supergroup/admin-control chat enforcement via `ADMIN_CONTROL_CHAT_ID`:
  - `in_admin_context(chat_id)` in all bot_service generations.
- Current adds topic-level check (`valid_thread_id` + `message_thread_id`) for admin topic context:
  - `send/core/bot_service.py:90-99`.

### 13) Why current implementation returns `"Access denied (wrong chat)"`
Because admin command gating now checks context before permission success path:
- `send/core/bot_service.py:398-401` calls `_can_run_admin_command`.
- If not owner-private-allowed or not admin topic context, reply is immediate wrong-chat denial.

### 14) Intentional restriction or regression?
Both:
- **Intentional hardening**: introduced in remediation commits to enforce strict chat context.
- **Behavioral regression vs Hetzner owner UX**: owner private `/admin` flow that previously worked got blocked at `49aaeb4`.

### 15) Exact commit where behavior changed
For `/admin` slash wrong-chat denial behavior: **`49aaeb4`** (`Implement Telegram runtime remediation`).
- Diff evidence: `d7e7213..49aaeb4` added `if not in_admin_context(chat_id): Access denied (wrong chat)` in slash path.

Related earlier tightening:
- `d7e7213` changed `in_admin_context` default from fail-open to fail-closed (`ADMIN_CONTROL_CHAT_ID==0` now denies), but did not add slash gate.

### 16) Old vs current implementation comparison
- Old Hetzner-import behavior (slash path): role/permission driven, no slash chat gate.
- Current behavior: context-first gate, then permission; owner-private allowed only on selected commands.
- See dedicated comparison file: `OWNER_ACCESS_COMPARISON.md`.

### 17) Restoration plan preserving canonical architecture
A safe restoration is possible by adjusting only the dispatcher gate policy while preserving:
- canonical command execution in `admin_commands.py`,
- canonical role/permission checks in `admin_permissions.py`,
- fail-closed admin supergroup/topic policy for non-owner flows.

Detailed plan: `RESTORATION_PLAN.md`.

### 18) Code modification constraint
No production code was modified in this audit task; only forensic documentation deliverables were produced.

---

## Final verdict
**Yes — the original owner login/access experience can be restored safely while keeping the current canonical architecture**, by restoring owner private `/admin` path behavior through policy-level gating in dispatcher logic (not by reintroducing passwords/sessions or legacy panel architecture).
