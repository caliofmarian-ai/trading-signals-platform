# Changed Files — Issue #38

Refs #38

## Modified Files

| File | Type | Change Summary |
|------|------|---------------|
| `send/core/telegram_app_nav.py` | Implementation | Add `ACT_BACK`, bounded nav history, update `handle_app_action`, clear history on `/start` reset |
| `send/core/telegram_admin_ui.py` | Implementation | Add `CANONICAL_ADMIN_PARENT_MAP`, `_PANEL_BACK_LABELS`, `parent_action` params to 3 markup functions, fix `strategy_markup` Back to OPERATIONS |
| `send/core/bot_service.py` | Implementation | Handle BACK admin action, pass correct `parent_action` to markup functions, explicit SYMBOLS handler |
| `tests/telegram_app/test_real_navigation.py` | Tests (new) | 59 focused tests for Back/Home/Refresh navigation |
| `tests/telegram_admin_ui_restoration/test_admin_ui_restoration.py` | Tests (updated) | Update 2 tests to reflect new correct Back button targets |

## New Files (Audit)

| File | Purpose |
|------|---------|
| `audit/telegram-ux-remediation-01/real-navigation-model/CANONICAL_PAGE_INVENTORY.md` | Full page and callback inventory |
| `audit/telegram-ux-remediation-01/real-navigation-model/BACK_HOME_REFRESH_CONTRACT.md` | Navigation contract specification |
| `audit/telegram-ux-remediation-01/real-navigation-model/PARENT_MAP.md` | Canonical parent map with tree diagram |
| `audit/telegram-ux-remediation-01/real-navigation-model/STATE_MODEL.md` | Navigation state model and concurrency analysis |
| `audit/telegram-ux-remediation-01/real-navigation-model/ROLE_AND_CONTEXT_ANALYSIS.md` | Role and authorization analysis |
| `audit/telegram-ux-remediation-01/real-navigation-model/TEST_MATRIX.md` | Test coverage matrix |
| `audit/telegram-ux-remediation-01/real-navigation-model/IMPLEMENTATION_SUMMARY.md` | Implementation summary and decision record |
| `audit/telegram-ux-remediation-01/real-navigation-model/CHANGED_FILES.md` | This file |
