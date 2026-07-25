# CHANGED FILES

## Source Code Changes

| File | Type | Summary |
|---|---|---|
| `send/core/admin_permissions.py` | Modified | Added `files.view` and `diagnostics.view` to PERMISSION_MATRIX for OWNER, PRIMARY_ADMIN, STRATEGY_ADMIN, RESEARCH_ADMIN |
| `send/core/telegram_admin_ui.py` | Modified | Full update: 16-button admin home, symbol toggle markup, strategy profile markups, file browser markups, diagnostics markups, DIR_KEY constants |
| `send/core/telegram_runtime.py` | Modified | Added 6 new CommandSpec entries; updated render_help_text |
| `send/core/telegram_targets.py` | Modified | Added alerts_target(), errors_target(), reports_target() for optional topic routing |
| `send/core/admin_commands.py` | Modified | ~645 lines added: file security, symbol management, strategy profiles, diagnostics, runtime audit, extended handle_admin_command |
| `send/core/bot_service.py` | Modified | ~360 lines added/modified: rate limiting, new owner-private commands, full callback handler rewrite, graceful editMessage fallback, document delivery |
| `.env.example` | Modified | Added documentation for 4 new optional variables |

## New Files

| File | Type | Summary |
|---|---|---|
| `tests/telegram_admin_ui_restoration/__init__.py` | New | Empty init for test module |
| `tests/telegram_admin_ui_restoration/test_admin_ui_restoration.py` | New | 69 comprehensive tests |
| `audit/telegram-admin-ui-restoration-01/IMPLEMENTATION_SUMMARY.md` | New | Implementation overview |
| `audit/telegram-admin-ui-restoration-01/AUTHORIZATION_CHANGE_REPORT.md` | New | Authorization change documentation |
| `audit/telegram-admin-ui-restoration-01/UI_RESTORATION_REPORT.md` | New | UI restoration documentation |
| `audit/telegram-admin-ui-restoration-01/FILE_DELIVERY_SECURITY_REPORT.md` | New | File security documentation |
| `audit/telegram-admin-ui-restoration-01/DIAGNOSTICS_IMPLEMENTATION_REPORT.md` | New | Diagnostics documentation |
| `audit/telegram-admin-ui-restoration-01/CALLBACK_REGISTRY.md` | New | Full callback namespace registry |
| `audit/telegram-admin-ui-restoration-01/TEST_EVIDENCE.md` | New | Test evidence and results |
| `audit/telegram-admin-ui-restoration-01/RAILWAY_VARIABLES.md` | New | Railway variable reference |
| `audit/telegram-admin-ui-restoration-01/OPERATOR_ACCEPTANCE_TEST.md` | New | Manual acceptance test checklist |
| `audit/telegram-admin-ui-restoration-01/CHANGED_FILES.md` | New | This file |
| `audit/telegram-admin-ui-restoration-01/ROLLBACK_PLAN.md` | New | Rollback procedure |

## Files NOT Changed

The following canonical modules were examined but not modified:
- `send/core/telegram_publisher.py` — Used as-is via `send_document()`
- `send/core/params_loader.py` — Used as-is
- `send/core/storage.py` — Used as-is

The following legacy module was NOT restored:
- `send/legacy/bot_control.py` — Not restored (per requirements)

## Change Summary

| Metric | Value |
|---|---|
| Source files modified | 7 |
| New test files | 2 |
| New audit report files | 11 |
| New tests | 69 |
| Total tests after change | 394 |
| Tests failing | 0 |
| Lines added (source) | ~1,245 |
| Lines removed (source) | ~50 |
