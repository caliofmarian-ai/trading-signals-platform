# CHANGED_FILES.md

BinaryBot — Changed Files  
Audit: telegram-application-reconstruction-01

---

## Files Modified

| File | Change Type | Lines Changed | Description |
|---|---|---|---|
| `send/core/telegram_admin_ui.py` | Refactored + Extended | ~180 added | Role-scoped canonical tree home; 9 new panel markup functions |
| `send/core/admin_views.py` | Extended | ~90 added | 4 new canonical panel view renderers |
| `send/core/bot_service.py` | Extended | ~120 added, ~10 modified | Role-aware markup; 16 new canonical panel callback handlers; `_iter_recent_engine_events` helper |
| `tests/telegram_admin_ui_restoration/test_admin_ui_restoration.py` | Updated | ~60 changed, ~50 added | Tests updated to validate canonical tree structure and role-scoped rendering |

## Files Created (Audit Documentation)

| File | Description |
|---|---|
| `audit/telegram-application-reconstruction-01/CANONICAL_ANALYSIS.md` | Analysis of all canonical documents; gap identification |
| `audit/telegram-application-reconstruction-01/ROLE_MAPPING.md` | Canonical role hierarchy → codebase mapping; panel visibility matrix |
| `audit/telegram-application-reconstruction-01/UX_RECONSTRUCTION.md` | Canonical UX reconstruction per domain; panel-by-panel design |
| `audit/telegram-application-reconstruction-01/NAVIGATION_RECONSTRUCTION.md` | Full navigation graph; callback action registry; application state model |
| `audit/telegram-application-reconstruction-01/APPLICATION_STATE_MODEL.md` | State model; navigation state; system state; mutation state |
| `audit/telegram-application-reconstruction-01/IMPLEMENTATION_PLAN.md` | Implementation plan; explicit decisions; documented gaps |
| `audit/telegram-application-reconstruction-01/IMPLEMENTATION_SUMMARY.md` | Post-implementation summary; test results; backward compatibility |
| `audit/telegram-application-reconstruction-01/CHANGED_FILES.md` | This file |

---

## Key Invariants Preserved

1. Outcome vote callbacks (`VOTE_|...`, `VOTE_`, `OUTCOME:`) are unaffected
2. Existing slash command behavior is unchanged
3. All existing callback actions remain handled (SYMBOLS, ENGINE, DEBUG, REPORT, DIAGNOSE, AUDIT, DOCS, etc.)
4. Rate limiting behavior unchanged
5. Permission and authorization logic unchanged
6. Signal delivery, PRE/CONFIRM/OPEN_NOW lifecycle unchanged
7. Admin event logging unchanged
8. File delivery security unchanged
