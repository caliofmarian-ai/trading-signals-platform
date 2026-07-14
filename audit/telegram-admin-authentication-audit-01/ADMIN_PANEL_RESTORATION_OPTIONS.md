# ADMIN_PANEL_RESTORATION_OPTIONS

## Can previous visual panel be restored safely?
**Yes, partially**, but only by re-implementing selected UI affordances on top of the canonical control plane.

## Features that were lost
- Visual admin callback menus (`ADMIN_*`).
- Symbol toggle inline panel (`SYM_TOGGLE`).
- Buffer mode inline selector (`BUFFER_*` / `buffer_set:*`).
- Legacy `/start` visual dual-panel behavior from `legacy/bot_control.py`.

## Features that should stay deprecated
- Legacy independent RBAC inside `bot_service`.
- Any control path that bypasses canonical `admin_permissions` and `admin_commands`.
- Any silent mutation callback flows without strong audit coupling.

## Safe restoration strategy
1. Keep canonical authorization source (`admin_permissions` + roles config).
2. Add optional inline keyboard front-end that maps to canonical slash-command handlers.
3. Preserve explicit mutation confirmations and audit logging.
4. Keep outcome callback handling unchanged.

## Authentication note
Restoration of visual panel does not require reintroducing password-in-chat flows.
