# SILENT FAILURE AUDIT

## Identified silent failure sites before fix

### Site 1 — `_send_interactive_page` in `bot_service.py`

```python
try:
    result = telegram_publisher.send_message(...)
    ...
except Exception:
    pass   # ← SILENT FAILURE
```

**Impact**: If `send_message` fails (network error, Telegram API error, token missing), the
failure is not logged anywhere.  From the Railway log perspective the interaction appears
to complete successfully.  The active message is not updated (no `message_id` captured),
so the next navigation attempt has no active message to edit and sends a further new message.
Over time the conversation accumulates orphaned messages and the bot appears unresponsive.

**Fix**: Replace `pass` with `observability_logger.log_error(...)` emitting event_type
`telegram_app_nav_send_failure` with `chat_id`, `user_id`, and the exception message.

### Site 2 — `telegram_updates.poll_updates()` error logging

```python
except Exception as e:
    observability_logger.log_error({
        "event_type": "error",
        "module": "telegram_updates",
        "error": str(e)    # ← token may appear here
    })
```

**Impact**: Not a silent failure, but `str(e)` from a `requests.RequestException` can embed
the full API URL including the bot token (e.g. `/bot<TOKEN>/getUpdates`).  The token would
then be written to the JSONL error log.

**Fix**: Apply `telegram_publisher._sanitize(str(e))` before logging.

### Site 3 — Unanswered callback queries

APP: and ADMIN_NAV: callbacks were never answered with `answerCallbackQuery`.

**Impact**: Telegram shows a loading spinner for ~10 seconds on every button press, then
displays "An error occurred".  The underlying message edit may succeed but the user sees an
error indication.  This degrades trust in the bot's responsiveness.

**Fix**: `telegram_updates.process_update` calls `_ack_callback(callback_id)` after
`bot_service.process_update(update)` for all non-VOTE_ callbacks.

## Residual silent failure analysis

After fix, the only remaining `except … pass` blocks are:

- `bot_service._send_document_reply` — temp-file cleanup (`os.unlink`): failure to delete
  a tmp file is harmless, silently suppressed intentionally.
- `bot_service._log_app_nav_edit_failure` — itself logs; if observability_logger throws,
  the exception is not re-raised.  Acceptable: logging must never crash the main path.

All other `send_message`/`edit_message` failures now either log to JSONL or propagate.
