# CHANGED FILES

## Source files modified

| File | Change |
|---|---|
| `send/core/telegram_publisher.py` | Remove `parse_mode="HTML"` from `edit_message`; add `_sanitize()`, `_safe_api_error()`, `answer_callback_query()`; use safe error strings in all RuntimeError messages |
| `send/runtime/telegram_updates.py` | Import `telegram_publisher`; sanitize `str(e)` in poller; add `_ack_callback()`; call `_ack_callback` after non-VOTE_ callback processing |
| `send/core/bot_service.py` | Replace `except Exception: pass` with `observability_logger.log_error(...)` in `_send_interactive_page` |

## New test files

| File | Tests |
|---|---|
| `tests/telegram_transport/__init__.py` | (empty, package marker) |
| `tests/telegram_transport/test_telegram_transport_and_recovery.py` | 18 tests |

## New documentation files

All under `audit/telegram-ux-remediation-01/telegram-transport-and-recovery-hardening/`:

- `TRANSPORT_CALL_INVENTORY.md`
- `PARSE_MODE_AND_ESCAPING_AUDIT.md`
- `SILENT_FAILURE_AUDIT.md`
- `POLLER_RESILIENCE_AUDIT.md`
- `INTERNAL_VS_STDOUT_LOGGING_CONTRACT.md`
- `DELETED_MESSAGE_RECOVERY_CONTRACT.md`
- `ROOT_CAUSE_ANALYSIS.md`
- `IMPLEMENTATION_PLAN.md`
- `TEST_MATRIX.md`
- `TEST_REPORT.md`
- `CHANGED_FILES.md` (this file)
- `IMPLEMENTATION_SUMMARY.md`
- `LIVE_ACCEPTANCE_CHECKLIST.md`

## Files NOT changed

Everything else in the repository.  In particular:
- `send/core/telegram_app_nav.py` — navigation state machine unchanged
- `send/core/bot_service.py` `_classify_edit_message_failure` — classification logic unchanged
- `send/core/admin_views.py` — page renderers unchanged (they produce correct plain text)
- All test files from previous batches — no regressions
