# INTERNAL VS STDOUT LOGGING CONTRACT

## Contract

| Channel | Mechanism | Contents | Token risk |
|---|---|---|---|
| Internal JSONL (observability) | `observability_logger.log_error / log_warning` | Structured JSON records; error messages sanitized by `_sanitize()` | None after fix |
| Railway stdout | `print()` — none used in transport path | n/a | None |
| Railway stderr | Unhandled exceptions only; bot_service wraps `process_update` in `try/except` | Exception message string | Mitigated by `_sanitize()` on poller path |

## What goes to JSONL

- `telegram_app_nav_edit_failure` — unexpected edit errors (e.g. server error, timeout)
- `telegram_app_nav_send_failure` — send_message failure after edit fallback (new in this fix)
- `callback_ack_failed` — `answerCallbackQuery` failure
- Poller-level exceptions — sanitized `str(e)`

## What never goes anywhere

- Bot token — redacted from all error strings via `_sanitize()` before any log write
- Full Telegram API error response JSON — replaced with `code=N description='...'` via
  `_safe_api_error()`.  The full response dict is never passed to a log sink.
- Authorization headers — not set by this codebase (token is in URL path, not header)

## Railway stdout guarantee

The transport path makes no `print()` calls.  All logging goes to JSONL files under
`OBS_DIR`.  Railway stdout only receives output from unhandled exceptions that reach the
process top level, which is prevented by the `try/except` in `poll_updates()` and the
`try/except` in `bot_service.process_update()`.

## Internal JSONL still works (test 16)

Test 16 (`test_16_jsonl_logging_works`) calls `observability_logger.log_error` directly
and verifies a valid JSON record is written.  The JSONL sink is independent of the
Telegram transport fixes.
