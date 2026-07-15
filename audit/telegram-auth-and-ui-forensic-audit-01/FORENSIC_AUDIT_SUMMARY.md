# FORENSIC_AUDIT_SUMMARY

## Audit metadata

- **Audited HEAD:** `0e736ae251dcb81dee7d13a34bbcfafcafe36967`
- **Audit commit hash:** recorded in CHANGED_FILES.md after push
- **Branch:** `copilot/telegram-capability-recovery-audit`
- **Audit date:** 2026-07-15
- **No code modifications were made during this audit.**
- **Files audited:**
  - `send/core/bot_service.py`
  - `send/core/admin_commands.py`
  - `send/core/admin_permissions.py`
  - `send/core/telegram_admin_ui.py`
  - `send/core/telegram_publisher.py`
  - `send/core/telegram_runtime.py`
  - `send/core/telegram_targets.py`
  - `send/legacy/bot_control.py` (git history; pre-BATCH-09 deletion)
  - `send/_archive/backups/bot_service.py.bak_step16` (Hetzner import snapshot)
  - `.env.example`
  - Full git history (2 commits in shallow clone)
  - All prior audit deliverables in `audit/`

---

## Part 1 — Authentication findings

### Finding AUTH-001: /report "Access denied" is a configuration failure, not a code bug

**Status:** Configuration issue.

The current code at HEAD `0e736ae` contains `_is_owner_private_context` which correctly allows the owner to use all 11 `_OWNER_PRIVATE_COMMANDS` (including `/report`) from a private DM. The denial occurs because `is_owner(user_id)` returns False when `OWNER_TELEGRAM_ID` Railway variable is absent, blank, or set to an incorrect value.

**Fix:** Set `OWNER_TELEGRAM_ID` = owner's numeric Telegram user ID in Railway. No code change required.

**Confidence:** High. Call path traced to exact code in `bot_service.py:_is_owner_private_context` + `admin_permissions.py:load_roles_config`.

### Finding AUTH-002: No password authentication ever existed

**Status:** Definitively confirmed absent.

No password, PIN, passcode, `/login`, `/auth`, `/unlock`, or session mechanism was found in:
- Current HEAD
- Any commit in git history
- `send/legacy/bot_control.py` (deleted)
- `send/_archive/backups/bot_service.py.bak_step16` (Hetzner snapshot)
- Any environment variable in `.env.example` or known Railway configuration

If the owner recalls a password prompt, it was not part of this repository's codebase. It may have existed in untracked external scripts on the Hetzner server.

### Finding AUTH-003: Commit 49aaeb4 introduced the breakage

The commit `49aaeb4` added an explicit slash-command chat gate (`in_admin_context`) without a private-owner exception. This caused all admin commands from the owner's private DM to return "Access denied (wrong chat)."

A subsequent remediation (visible in current HEAD) added `_is_owner_private_context` to restore the private DM path — but only if `OWNER_TELEGRAM_ID` is correctly configured.

### Finding AUTH-004: /roles_reload is intentionally blocked in private DM

`/roles_reload` is NOT in `_OWNER_PRIVATE_COMMANDS`. `RELOAD_ROLES_CONFIRM` callback is explicitly denied for owner-private context in `_handle_admin_navigation_action`. This is a deliberate security choice, not a bug.

### Finding AUTH-005: ADMIN_SUPERGROUP_ID and ADMIN_GROUP_ID are not auth variables

These variables are used only in `distribution_router.py` for signal delivery routing. They have no role in command authorization. Only `ADMIN_CONTROL_CHAT_ID` gates command access.

---

## Part 2 — Legacy UI findings

### Finding UI-001: Symbol toggle keyboard existed in two forms; neither is present now

**Era A (`bot_control.py`):** Full checkbox-style grid (3 per row), ALL/NONE/Refresh controls, `tg:<cat>:<sym>` callbacks.
**Era B (admin panel):** List of active symbols (up to 12), one per row, `SYM_TOGGLE:{sym}` callbacks.
**Current:** Text list only; add/remove via slash commands.

**Classification:** Removed. Recommended to restore (design in CANONICAL_UI_RESTORATION_PLAN.md section 3.2).

### Finding UI-002: Buffer mode selector existed; no equivalent button exists now

**Era A:** Romanian 3-button row (`buffer_set:small/medium/large`).
**Era B:** English 3-button row (`BUFFER_SMALL/MEDIUM/LARGE`).
**Current:** Strategy parameters managed via `/thresholds`, `/sr`, `/spike` slash commands with arguments. No button.

**Classification:** Superseded. Recommended to restore as strategy profile buttons (design in section 3.3).

### Finding UI-003: Docs viewer existed; no equivalent exists now

**Era B only:** `ADMIN_DOCS` → `DOC:{filename}` flow; sent files as Telegram documents.
**Current:** No docs viewer button; no `/docs`, `/files` commands.

**Classification:** Removed. Recommended to restore (design in section 3.4).

### Finding UI-004: Research panel was always a placeholder

`ADMIN_RESEARCH` → "coming next — analytics_engine.py". Never implemented.
**Classification:** Removed. Not recommended to restore (analytics accessible via /report, /debug).

### Finding UI-005: Admin panel home is present but restructured

Era B had 5 role-filtered buttons with `ADMIN_*` callbacks.
Current has 8 buttons (no role-filtering at UI level) with `ADMIN_NAV:*` callbacks.
Status, Strategy, Engine, Debug, Report, Roles, Affiliate are all accessible.
Buffer and Docs are the main gaps.

**Classification:** Partially present.

---

## Part 3 — Key risk summary

| Risk ID | Severity | Description | Status |
|---|---|---|---|
| R-001 | HIGH | Owner cannot use `/report` in private DM due to OWNER_TELEGRAM_ID misconfiguration | Configuration fix required |
| R-002 | HIGH | lru_cache on `load_roles_config` causes stale owner denial across process lifetime | Restart required after setting OWNER_TELEGRAM_ID |
| R-003 | MEDIUM | `/roles_reload` not accessible from private DM (circular denial scenario) | Acknowledged; mitigated by service restart |
| R-004 | LOW | Symbol toggle UI absent; operators must use slash syntax to manage symbols | Recommended restoration available |
| R-005 | LOW | No buffer quick-select button; strategy changes require slash arguments | Recommended restoration available |
| R-006 | LOW | No docs viewer; no `/files` or `/docs` command | Recommended restoration available |
| R-007 | INFO | No password auth exists or is needed | No action required |

---

## Part 4 — Answers to all 18 mandatory questions (summary index)

| Q | Answer location | Summary |
|---|---|---|
| 1 | TELEGRAM_AUTH_FORENSIC_AUDIT.md §Q1 | is_owner() returns False due to OWNER_TELEGRAM_ID misconfiguration |
| 2 | TELEGRAM_AUTH_FORENSIC_AUDIT.md §Q2 | Two-gate: owner-private → _OWNER_PRIVATE_COMMANDS; fallback → admin topic |
| 3 | TELEGRAM_AUTH_FORENSIC_AUDIT.md §Q3 | Per-command context allowance table |
| 4 | TELEGRAM_AUTH_FORENSIC_AUDIT.md §Q4 | OWNER_TELEGRAM_ID: roles fallback; ADMIN_CONTROL_CHAT_ID: chat gate; SUPERGROUP/GROUP: routing only |
| 5 | TELEGRAM_AUTH_FORENSIC_AUDIT.md §Q5 | No password implementation found |
| 6 | TELEGRAM_AUTH_FORENSIC_AUDIT.md §Q6 | Not applicable (no password) |
| 7 | TELEGRAM_AUTH_FORENSIC_AUDIT.md §Q7 | Explicit: no password in repo history or any backup |
| 8 | TELEGRAM_AUTH_FORENSIC_AUDIT.md §Q8 | Commit 49aaeb4 introduced breakage; current HEAD partially restored |
| 9 | TELEGRAM_LEGACY_UI_INVENTORY.md | Era A (runner) and Era B (admin panel) fully inventoried |
| 10 | TELEGRAM_BUTTON_AND_CALLBACK_REGISTER.md | All buttons with text, emoji, row layout, role visibility, callback_data |
| 11 | TELEGRAM_LEGACY_UI_INVENTORY.md | All requested screens covered |
| 12 | TELEGRAM_BUTTON_AND_CALLBACK_REGISTER.md | All callback families: tg:, buffer_set:, ADMIN_*, BUFFER_*, SYM_TOGGLE:, DOC:, ADMIN_NAV:, VOTE_\|, OUTCOME:, VOTE_ |
| 13 | OLD_VS_CURRENT_TELEGRAM_UI_COMPARISON.md §S9 | Legacy→current mapping |
| 14 | OLD_VS_CURRENT_TELEGRAM_UI_COMPARISON.md §S9 | Classifications: still present / partially / removed / superseded / recommended |
| 15 | CANONICAL_UI_RESTORATION_PLAN.md §3 | One architecture using current 5 files only |
| 16 | CANONICAL_UI_RESTORATION_PLAN.md §1 | bot_control.py not restored as separate process |
| 17 | CANONICAL_UI_RESTORATION_PLAN.md §3,4 | All required capabilities covered; variables identified |
| 18 | CANONICAL_UI_RESTORATION_PLAN.md §4 | Existing / optional / new / legacy-only variables identified |

---

## Part 5 — Audited file list

```
send/core/bot_service.py                             (HEAD 0e736ae)
send/core/admin_commands.py                          (HEAD 0e736ae)
send/core/admin_permissions.py                       (HEAD 0e736ae)
send/core/telegram_admin_ui.py                       (HEAD 0e736ae)
send/core/telegram_publisher.py                      (HEAD 0e736ae)
send/core/telegram_runtime.py                        (HEAD 0e736ae)
send/core/telegram_targets.py                        (HEAD 0e736ae)
send/core/distribution_router.py                     (HEAD 0e736ae, partial — env var usage)
send/legacy/bot_control.py                           (git history: 0fb9112, deleted 63834b3)
send/_archive/backups/bot_service.py.bak_step16      (git history: 0fb9112)
.env.example                                         (HEAD 0e736ae)
audit/telegram-admin-authentication-audit-01/*       (HEAD 9912c14)
audit/telegram-forensic-scope-02/*                   (HEAD 0e736ae)
```
