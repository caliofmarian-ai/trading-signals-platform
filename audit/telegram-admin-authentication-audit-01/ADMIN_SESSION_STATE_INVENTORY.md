# ADMIN_SESSION_STATE_INVENTORY

## Session/login state mechanisms searched
- in-memory auth sessions
- file-backed admin sessions
- expiry timestamps linked to login
- logout/revoke handlers
- per-user unlock state

## Findings

## Current runtime
No login/session state layer exists.
- No session files under `send/state` for admin auth.
- No session dictionaries or login FSM in admin modules.
- Permission comes from static role mapping (`admin_roles.json` + env owner fallback) via `send/core/admin_permissions.py`.

## Historical runtime and deleted modules
- `send/legacy/bot_control.py`: no login/session state.
- Historical `send/core/bot_service.py`: had role lookup (`rbac.json` / `ADMIN_USER_ID`) and admin chat checks; no session lifecycle model.

## Outcome sessions vs admin sessions (not equivalent)
`outcome_service` has vote window timing and callback context mapping for signal outcomes; this is unrelated to admin login sessions.

## Result
Admin session model with expiry/revocation/unlock is **not evidenced** in repository history reviewed.
