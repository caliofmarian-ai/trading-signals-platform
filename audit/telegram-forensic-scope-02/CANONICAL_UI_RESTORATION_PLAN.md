# CANONICAL_UI_RESTORATION_PLAN

## Audit metadata
- HEAD at audit time: `9912c14`
- No code modifications made during this audit. This is a design plan only.
- This document defines one and only one restoration design that does not recreate a second control plane.

---

## 1. Restoration scope statement

The owner has identified that the original Telegram admin experience included:
- Accessible admin commands from the owner's private DM without requiring the admin supergroup.
- An inline-keyboard panel accessible after `/admin` with direct navigation to all major admin areas.
- Symbol toggle UI (checkbox-style, per category).
- Buffer mode selector (three-option keyboard).
- Docs viewer accessible from the panel.

The current implementation preserves the slash-command architecture and the permission model, but lacks:
- Symbol toggle inline keyboard (replaced by slash-only mutations).
- Buffer selector inline keyboard (no current equivalent button).
- Docs viewer button (removed from panel).

**Goal:** Restore usable panel UX for the owner without recreating a separate legacy control plane, second auth stack, or session mechanism.

---

## 2. Guardrails (non-negotiable)

1. **No second control plane.** All admin mutations route through `admin_commands.py` (canonical).
2. **No password authentication.** Identity remains Telegram user-ID + role/permission model.
3. **No session tokens or TTL state.** No login/logout mechanics.
4. **No new env variables for auth.** Existing `OWNER_TELEGRAM_ID`, `ADMIN_CONTROL_CHAT_ID`, `ADMIN_CONTROL_THREAD_ID`, `ADMIN_ROLES_CONFIG` remain the identity/context sources.
5. **Permission authority stays in `admin_permissions.py`.** No inline permission checks in `telegram_admin_ui.py` or bot_service dispatcher.
6. **Fail-closed behavior preserved for non-owner flows.** Admin topic requirement stays for all non-owner contexts.
7. **No modification to `admin_commands.py` or `admin_permissions.py`.** Restoration is entirely in the dispatcher and UI layer.

---

## 3. Design: what changes are required

### 3.1 Owner private DM — already functional for slash commands

The owner can already use all 11 `_OWNER_PRIVATE_COMMANDS` slash commands privately.
**No change required for slash access.**

### 3.2 Symbols: restore inline toggle keyboard

**Problem:** `/symbols` shows a text list; no toggle keyboard exists.
**Design:**
- Extend `telegram_admin_ui.py` with a `symbols_toggle_markup(symbols: list[str], active: list[str])` function.
- Add `ADMIN_NAV:SYMBOLS_TOGGLE:{sym}` action for toggle.
- Add `ADMIN_NAV:SYMBOLS_ALL` and `ADMIN_NAV:SYMBOLS_NONE` actions for bulk select.
- Route these new `ADMIN_NAV:` callbacks through `_handle_admin_navigation_action` to `admin_commands` mutation calls (`/symbols add/remove`).
- No new callback prefix or auth model. Same `ADMIN_NAV:` prefix, same context gate.
- Mutation remains in `admin_commands.py`.

### 3.3 Buffer mode: restore three-option keyboard

**Problem:** No buffer/strategy-setting keyboard exists; mutations require slash arguments.
**Design:**
- Add a `strategy_quick_markup()` function in `telegram_admin_ui.py` with three buffer-tier buttons.
- Actions: `ADMIN_NAV:STRATEGY_SMALL`, `ADMIN_NAV:STRATEGY_MEDIUM`, `ADMIN_NAV:STRATEGY_LARGE`.
- Route to existing `/thresholds` or a dedicated strategy mutation in `admin_commands.py`.
- Keep existing permission gate (`strategy.thresholds.write`).
- Button appears on strategy sub-panel only, gated behind existing permission checks.

### 3.4 Docs viewer: restore from panel

**Problem:** No docs viewer button; docs exist on filesystem.
**Design:**
- Add `ADMIN_NAV:DOCS` action to `admin_home_markup`.
- Add `ADMIN_NAV:DOC:{filename}` for per-file selection (extends existing parse_action to handle `DOC:` sub-action after `ADMIN_NAV:`).
- Route to a `render_docs_list(docs_dir)` / `render_doc_content(filename)` in `admin_commands.py` or a new `admin_docs.py` helper.
- No mutation; read-only.
- Gate with `debug.view` or a new `docs.view` permission added to PERMISSION_MATRIX (OWNER, PRIMARY_ADMIN, STRATEGY_ADMIN, ANALYST roles).

---

## 4. Single restoration design (unified)

### Phase 1: Panel completeness (no auth change, no new control plane)

**Changes confined to:**
- `send/core/telegram_admin_ui.py` — add markup functions for symbols toggle, strategy quick-select, docs list.
- `send/core/bot_service.py` — extend `_handle_admin_navigation_action` to route new ADMIN_NAV actions.
- `send/core/admin_commands.py` — add `handle_symbols_toggle`, `handle_strategy_quick_set`, `handle_docs_list`, `handle_doc_render` handlers that call existing mutation/read helpers.

**What does NOT change:**
- `admin_permissions.py` (permission matrix, role loading, identity).
- Context gate logic (`_can_run_admin_command`, `_can_use_admin_callback`, `_is_owner_private_context`, `_is_admin_topic_context`).
- All existing tests.
- All env variable names and config file schemas.

### Phase 2: Owner private DM completeness (no new auth)

The current `_OWNER_PRIVATE_COMMANDS` already covers all slash commands the owner needs.
Callback access in private DM is already allowed via `_can_use_admin_callback`.
**No phase 2 changes needed** unless new mutation actions from Phase 1 callbacks require private-context explicit allow — which they do not, since `_can_use_admin_callback` grants callback access in owner private context unconditionally.

---

## 5. What this design explicitly does NOT do

| Excluded action | Reason |
|---|---|
| Recreate `ADMIN_STATUS`, `ADMIN_SET_BUFFER`, `ADMIN_SET_SYMBOLS`, `ADMIN_RESEARCH`, `ADMIN_DOCS` callbacks | These are retired; new actions use `ADMIN_NAV:` prefix |
| Re-introduce `BUFFER_SMALL/MEDIUM/LARGE` callbacks | Replaced by canonical `ADMIN_NAV:STRATEGY_SMALL/MEDIUM/LARGE` |
| Re-introduce `SYM_TOGGLE:{sym}` callbacks | Replaced by `ADMIN_NAV:SYMBOLS_TOGGLE:{sym}` |
| Re-introduce `DOC:{filename}` callbacks | Replaced by `ADMIN_NAV:DOC:{filename}` |
| Restore the Romanian-language UI from `bot_control.py` | That runner was intentionally deleted; symbol mgmt moved to canonical slash path |
| Restore `in_admin_context` fail-open behavior | Security regression (GAP-013); stays fail-closed |
| Add password auth | Not needed; never existed |
| Add session management | Not needed; never existed |
| Restore `rbac.json` / `ADMIN_USER_ID` legacy identity | Superseded by canonical roles config + `OWNER_TELEGRAM_ID` |
| Recreate inline `/start` dual-panel bot behavior | Public UX concern; not admin panel scope |

---

## 6. Risk register

| Risk | Mitigation |
|---|---|
| New `ADMIN_NAV:` sub-actions bypass permission checks | Route ALL new actions through `admin_commands.py` permission gate, not directly to storage |
| Symbol toggle in private DM leaks to non-owners | Context gate (`_can_use_admin_callback`) already blocks non-owners; no change needed |
| Docs viewer exposes sensitive files | Restrict to known-safe docs directory; no traversal; gate with `docs.view` permission |
| New callbacks break existing tests | New actions are additive; existing action set unchanged; old retired callbacks still return error message |
| Restoration diverges between admin topic and private DM | Test both contexts explicitly for each new action |

---

## 7. Test matrix (restoration-specific)

For each new Phase 1 action:
- Owner private: callback allowed, routes to correct handler, mutation/read executes with permission.
- Admin topic: same as private.
- Non-owner private: `_can_use_admin_callback` → denied (no context change needed).
- Unset admin chat + non-owner: denied.
- Retired old callback still returns retirement message (regression guard).

---

## 8. Relationship to existing plans

- This plan supersedes the general restoration strategy in `/RESTORATION_PLAN.md` (root, commit `9912c14`) for the UI-specific scope.
- It does not contradict that plan; it adds specificity for the symbol, buffer, and docs surfaces.
- The auth flow diagram in `/AUTH_FLOW_DIAGRAM.md` remains accurate and does not need revision.
- The `OWNER_ACCESS_COMPARISON.md` facts remain accurate.

---

## 9. Minimal change summary

| File | Change type | Lines estimated |
|---|---|---|
| `send/core/telegram_admin_ui.py` | Add 3 new markup functions + extend `parse_action` | ~50 |
| `send/core/bot_service.py` | Extend `_handle_admin_navigation_action` dict + add cases | ~20 |
| `send/core/admin_commands.py` | Add 4 new handler functions + expose in `handle_admin_command` | ~60 |
| `send/core/admin_permissions.py` | Optionally add `docs.view` permission to matrix | ~5 |
| New tests | Cover each new action in owner-private + admin-topic + denied contexts | ~40 |

**Total: ~175 lines across 5 files. No new files, no new dependencies, no new env vars.**
