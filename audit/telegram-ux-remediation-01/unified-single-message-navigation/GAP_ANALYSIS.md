# Gap Analysis

## Confirmed gaps before remediation
1. Admin slash commands used `_send_reply()` (always send new message)
2. ADMIN_NAV callback flow edited message but fallback used `_send_reply()` and created untracked extra messages
3. Access denied / unknown / rate-limited interactive responses could bypass canonical active-message path
4. APP callbacks and ADMIN callbacks were not using one shared canonical delivery function

## Remediation applied
- Added canonical `core.bot_service._send_interactive_page(...)` and migrated interactive routes to this single path
- Added `_edit_interactive_message(...)` to unify edit/no-op/stale/unexpected handling
- Routed all interactive slash/admin/callback responses through canonical path
- Preserved documented separate-message exceptions (documents/signals/alerts/proofs)

## Residual risk
- Active message tracking is in-memory (expected), so process restarts create a new active UI message for the next interaction
