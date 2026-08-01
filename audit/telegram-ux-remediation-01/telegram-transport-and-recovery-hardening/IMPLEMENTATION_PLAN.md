# IMPLEMENTATION PLAN

## Scope

Corrective continuation of telegram-ux-remediation.  Not a new feature.  Targeted
at the four root causes identified in ROOT_CAUSE_ANALYSIS.md.

## Changes

### 1. `send/core/telegram_publisher.py`

- **Remove** `payload["parse_mode"] = "HTML"` from `edit_message()`.
- **Add** `_sanitize(s: str) -> str` — redacts bot-token substring via regex.
- **Add** `_safe_api_error(data: dict) -> str` — safe one-line summary of API error.
- **Replace** raw `{data}` in all `RuntimeError` messages with `_safe_api_error(data)`.
- **Add** `answer_callback_query(callback_query_id, text, show_alert)` function.

### 2. `send/runtime/telegram_updates.py`

- **Import** `telegram_publisher` for `_sanitize` and `answer_callback_query`.
- **Sanitize** `str(e)` before passing to `log_error` in `poll_updates`.
- **Add** `_ack_callback(callback_id)` — calls `telegram_publisher.answer_callback_query`.
- **Call** `_ack_callback(callback_id)` after `bot_service.process_update(update)` for
  all callback_query updates that are not VOTE_ (which already have their own ack path).

### 3. `send/core/bot_service.py`

- **Replace** `except Exception: pass` with `observability_logger.log_error(...)` in
  the `send_message` fallback inside `_send_interactive_page`.

## Files not changed

- `send/core/telegram_app_nav.py` — navigation state machine correct; no change needed.
- `send/core/admin_views.py` — page renderers produce correct text; no change needed.
- `send/core/telegram_runtime.py` — command registry correct; no change needed.
- All other source files — no transport or logging path affected.

## Testing

New test file: `tests/telegram_transport/test_telegram_transport_and_recovery.py`
18 test cases covering the full acceptance matrix.

## Security

- Token redaction via `_sanitize()` in publisher and poller.
- `_safe_api_error()` strips raw API response fields that could contain sensitive data.
- No secrets committed.
- Secret scan: run before final commit.
- CodeQL: run before final commit.

## Delivery

- Branch: `copilot/correction-telegram-ux-remediation`
- PR: new Draft PR, `Refs #27` only.
- Do not merge.  Do not close Issue #27.
