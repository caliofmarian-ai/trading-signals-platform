# Canonical Route Inventory

## Public slash commands
- `/start` → interactive page (canonical path)
- `/help` → interactive page (canonical path)
- `/status` → interactive page (canonical path)
- unknown slash commands → interactive error page (canonical path)

## Admin slash commands
- `/admin`, `/strategy`, `/thresholds`, `/sr`, `/spike`, `/symbols`, `/engine`, `/debug`, `/report`, `/roles`, `/affiliate`, `/files`, `/docs`, `/download`, `/log`, `/diagnose`, `/audit_runtime`, `/roles_reload`
- Authorized responses: interactive page (canonical path)
- Access denied: interactive error page (canonical path)
- File-path responses: sendDocument exception path

## APP callbacks
- `APP:HOME`, `APP:STATUS`, `APP:HELP`, `APP:ADMIN`
- All routed through canonical interactive page delivery with preferred originating message edit

## ADMIN_NAV callbacks
- Canonical panel routes and nested routes: `HOME`, `OPERATIONS`, `OPS_ENGINE`, `SYMBOLS_COV`, `DISTRIBUTION`, `RESEARCH`, `INTELLIGENCE`, `ROLES`, `SYSHEALTH`, `GOVDOCS`, `SECAUDIT`, strategy/symbol/profile/files/docs/diagnose/audit routes
- Authorized responses: canonical interactive page delivery
- Access denied/rate-limited/unknown: canonical interactive error page delivery
- File download/export callbacks: sendDocument exception path

## Other callbacks
- `VOTE_|...` and `OUTCOME:...` remain outcome/publication flow; not converted into interactive app-page replacement path

## Navigation controls
- Home: edits active/originating interactive message
- Back labels (`⬅️ Admin`, `⬅️ Files`, `⬅️ Strategy`) route to parent callback targets and edit one interactive message
- Refresh buttons route to same-page actions and edit one interactive message

## Stale callbacks / edit failures
- `message is not modified` treated as idempotent success
- stale/deleted/uneditable target clears stale state, then sends exactly one replacement and tracks it
