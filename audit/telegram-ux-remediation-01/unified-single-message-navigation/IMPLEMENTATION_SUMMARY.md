# Implementation Summary

- Introduced one canonical interactive page delivery function in `core.bot_service`: `_send_interactive_page(...)`
- Migrated interactive routing to canonical path for:
  - public slash pages
  - admin slash pages
  - APP callbacks
  - ADMIN_NAV callbacks
  - interactive access-denied/rate-limit/unknown pages
- Added shared edit helper `_edit_interactive_message(...)` for success/no-op/stale/unexpected handling
- Ensured callback-originating successful edits always refresh active message tracking
- Ensured stale callback/admin failures produce one tracked replacement only
- Preserved permitted separate-message exceptions (`sendDocument`, signal publication, operational alerts/proofs)
