# Back/Home/Refresh Contract — Issue #38

**Scope:** Canonical navigation contract for APP: and ADMIN_NAV: surfaces  
**Date:** 2026-08-02  
**Issue:** #38 — Implement real Back, Home, and Refresh navigation

---

## 1. Back Contract

### Definition
Back returns the user to the **immediate authorized parent** of the current page.

### Properties
- **Bounded:** Navigation history is bounded to `_NAV_HISTORY_MAX_DEPTH = 5` entries. Pressing Back more times than depth falls back to Home safely.
- **Loop-free:** Consecutive duplicate entries are not pushed (push suppresses same-page dedup). Home and BACK are excluded from recursive Back targets.
- **Restart/state-loss safe:** If history is empty (e.g., after restart), Back falls back to the role-scoped Home page.
- **Concurrency-safe:** `_nav_history_lock` (threading.Lock) guards the per-session stack.
- **Session-scoped:** History is keyed by `(chat_id, user_id, thread_id)` — same isolation as the active UI message state.

### APP: Back Behavior
APP: pages are currently one level deep from Home:
- Status → parent: Home
- Help → parent: Home
- Admin (info) → parent: Home

`handle_app_action(ACT_BACK)` pops from the per-session bounded history. On empty history or if the popped item is HOME or BACK (root guards), it returns the role-scoped welcome page.

### ADMIN_NAV: Back Behavior
The admin tree uses a static canonical parent map (`CANONICAL_ADMIN_PARENT_MAP`) for deterministic parent resolution. Context-sensitive pages (OPS_ENGINE, SH_ENGINE, OPS_DIAGNOSE, SH_DIAGNOSE) receive the correct parent via the `parent_action` parameter of their markup functions, encoded directly in the Back button callback.

This model is:
- Bounded: static map is acyclic (tree structure)
- Loop-free: no page maps to itself
- Context-preserving: parent encoded at render time, not deduced at navigation time

---

## 2. Home Contract

### APP: Home
`APP:HOME` returns to the **role-scoped welcome page** for the session user.

- OWNER: Welcome page with Admin Control Surface button
- Admin-tier roles: Welcome page with Status and Help buttons
- USER: Platform introduction with Status and Help buttons

### Admin Home
`ADMIN_NAV:HOME` returns to the **Admin Control Surface** (role-scoped admin root).

- Always accessible from any admin panel via the last row of the keyboard
- Labeled distinctly: panels use `⬅️ Admin` for Admin Home, not `🏠 Home`
- `🏠 Home` in admin panels refers to `APP:HOME` (role-scoped welcome page), appended by `admin_home_markup(home_button_callback=...)`

### Distinction
- `APP:HOME` → role-scoped welcome page
- `ADMIN_NAV:HOME` → admin control root (scoped to admin-tier roles)
- Both are always reachable; no dead ends

---

## 3. Refresh Contract

### Definition
Refresh re-renders the current page from authoritative data:
- Does **not** add to navigation history
- Does **not** send a new UI message (edit-in-place, single-message contract)
- Preserves relevant pagination/filter context where possible
- Re-fetches live data (symbols, engine state, etc.)

### APP: Refresh
`APP:STATUS` on the status page re-renders the status page with a fresh status snapshot.

### ADMIN_NAV: Refresh Callbacks
Each page's Refresh button targets the action that re-renders that page:

| Page | Refresh Target | Notes |
|------|---------------|-------|
| Status | `ADMIN_NAV:STATUS` | Re-fetches status snapshot |
| Engine | `ADMIN_NAV:ENGINE` | Re-fetches engine state |
| Diagnose | `ADMIN_NAV:DIAGNOSE` | Re-runs diagnose |
| Decision Visibility | `ADMIN_NAV:DECISION_VIS` | Re-fetches last decision |
| Distribution | `ADMIN_NAV:DISTRIBUTION` | Re-fetches route state |
| Research | `ADMIN_NAV:RESEARCH` | Re-fetches report |
| Intelligence | `ADMIN_NAV:INTELLIGENCE` | Re-fetches events |
| Symbols (from Admin Home) | `ADMIN_NAV:SYMBOLS_COV` | Re-fetches symbols, preserves admin-home context |
| Symbols (from Strategy) | `ADMIN_NAV:SYMBOLS` | Re-fetches symbols, preserves strategy context |

### Context Preservation Through Refresh
`symbols_toggle_markup(parent_action=...)` uses the correct Refresh target based on how the page was reached:
- From Admin Home (`parent_action="HOME"`): Refresh → `SYMBOLS_COV`
- From Strategy (`parent_action="STRATEGY"`): Refresh → `SYMBOLS`

This preserves the Back button context through refresh cycles.

---

## 4. Constraint Compliance

| Constraint | Status |
|-----------|--------|
| Single-message contract preserved | ✅ Back/Home/Refresh all edit in place |
| No new message sent by Back/Home/Refresh | ✅ All dispatch through same page-edit path |
| `(chat_id, user_id, thread_id)` isolation | ✅ History keyed by normalize_session_key |
| Owner-private/Admin-topic authorization | ✅ Unchanged (checked before dispatch) |
| Role-hidden surfaces preserved | ✅ role_scoped renderers unchanged |
| No second router | ✅ All navigation through existing dispatchers |
| No secrets in navigation state | ✅ History contains only action strings |
| Reuse telegram_app_nav, telegram_admin_ui | ✅ Both modules extended, not replaced |
