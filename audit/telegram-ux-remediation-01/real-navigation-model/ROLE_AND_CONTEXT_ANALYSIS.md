# Role and Context Analysis — Issue #38

**Scope:** Role-based and context-based navigation authorization  
**Date:** 2026-08-02  
**Issue:** #38 — Implement real Back, Home, and Refresh navigation

---

## 1. APP: Navigation Role Access

| Page | Roles Allowed | Notes |
|------|--------------|-------|
| Welcome/Home | All | Role-scoped content |
| Status | All | Public, role-agnostic content |
| Help | All | Role-scoped content |
| Admin Surface | OWNER (full), admin-tier (info), USER (redirect) | Pre-existing security boundary |

The `ACT_BACK` action delegates to the parent page renderer. Since all APP: pages are
accessible to all roles, BACK always produces an authorized page.

The bounded history contains only APP: action constants (HOME, STATUS, HELP, ADMIN),
never role-specific tokens or session secrets. No authorization bypass is possible.

---

## 2. ADMIN_NAV: Navigation Role Access

Role enforcement is unchanged. The admin navigation dispatcher (`_handle_admin_navigation_action`)
requires admin context (admin-topic or Owner private DM) before processing any `ADMIN_NAV:` callback.

The `parent_action` parameter only affects which admin page is shown after pressing Back.
Since Back targets are always within the admin tree, no privilege escalation is possible.

| Back Target | Authorization Required |
|-------------|----------------------|
| ADMIN_NAV:HOME | Admin context (unchanged) |
| ADMIN_NAV:OPERATIONS | Admin context (unchanged) |
| ADMIN_NAV:SYSHEALTH | Admin context (unchanged) |
| ADMIN_NAV:STRATEGY | Admin context (unchanged) |

---

## 3. Role-Hidden Surfaces

Role-hidden surfaces are preserved:
- Panel visibility is filtered by `_PANEL_VISIBILITY` in `admin_home_markup(role=...)` (unchanged)
- Back navigation targets are within authorized zones only
- No navigation button can bypass role-scoped panel filtering

---

## 4. Cross-Chat and Cross-Thread Isolation

Navigation history is scoped by `(chat_id, user_id, thread_id)`:
- Same user in different chats has independent histories
- Same user in different forum threads has independent histories
- Same chat with different users has independent histories

This matches the existing `_active_ui` isolation model (canonical §D).

---

## 5. Owner-Private / Admin-Topic Distinction

- OWNER private DM: some commands restricted (e.g., `RELOAD_ROLES_CONFIRM` blocked) — unchanged
- Admin-topic: full admin access — unchanged
- Back navigation within admin tree does not change these access boundaries

---

## 6. Security Properties

| Property | Status | Notes |
|----------|--------|-------|
| No role escalation via Back | ✅ | Back targets are admin tree nodes, same auth required |
| No secrets in nav history | ✅ | History contains only action strings |
| No bypass of admin-context check | ✅ | Check performed before dispatch, not in markup |
| Session isolation preserved | ✅ | Keyed by (chat_id, user_id, thread_id) |
| No dead end after unauthorized nav | ✅ | BACK fallback always produces navigable Home |
