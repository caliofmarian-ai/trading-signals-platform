# ROOT CAUSE ANALYSIS

## Production behavior (observed after PR #29 merge)

1. User deleted private Telegram conversation.
2. Pressed native Start button → bot produced first message. ✓
3. Opened Engine command/page → appeared as a NEW message instead of editing existing. ✗
4. Pressed Admin button → appeared as another NEW message. ✗
5. User deleted all messages again.
6. Bot stopped responding entirely. ✗

## Root cause 1 (PRIMARY) — parse_mode inconsistency in telegram_publisher

**File**: `send/core/telegram_publisher.py`

`edit_message()` set `payload["parse_mode"] = "HTML"`.
`send_message()` did not set `parse_mode`.

The admin panel text produced by `render_admin_home()` in `admin_views.py` includes
command-help strings from `command_registry()`:

```
/thresholds PRE|CONFIRM|OPEN <value>
/sr <multiplier>
/spike wick_body_ratio_max|range_z_max|jump_vs_atr_max <value>
/download <dir> <filename>
```

These strings contain HTML-special characters `<` and `>`.  When `edit_message()` was
called with this text under `parse_mode="HTML"`, Telegram returned:

```
400 Bad Request: can't parse entities: Unsupported start tag "value" at byte offset N
```

Execution path:
1. `_edit_interactive_message` catches the exception.
2. `_classify_edit_message_failure`: "value", "dir", "filename", "multiplier" are not
   in the stale-marker list → classified as `"unexpected"`.
3. Active state NOT cleared.
4. `_edit_interactive_message` returns `False`.
5. `_send_interactive_page` falls through to `send_message` (no parse_mode) → no error →
   NEW message sent, stored as active.

This violated the single-message contract on every admin panel interaction.

**Fix**: Remove `payload["parse_mode"] = "HTML"` from `edit_message()`.

## Root cause 2 — Silent send_message failure

**File**: `send/core/bot_service.py`

```python
except Exception:
    pass
```

When `send_message` failed (after an edit failure), the failure was silently swallowed.
No logging, no active-message update.  Subsequent navigation had no tracked message to
edit and attempted edit→send again, further producing new messages or failing silently.

After Root Cause 1 is fixed, this is a latent risk rather than an active production failure.
However it was the likely cause of "bot stopped responding entirely" — if a transient
network error caused `send_message` to fail after a stale-edit recovery, the bot appeared
unresponsive until the user retried.

**Fix**: Replace `pass` with `observability_logger.log_error(...)`.

## Root cause 3 — Bot token leakage via poller exception logging

**File**: `send/runtime/telegram_updates.py`

`requests` exceptions embed the full URL including the bot token in `str(e)`.  The poller
logged `str(e)` directly to JSONL without sanitization.

**Fix**: Apply `telegram_publisher._sanitize(str(e))` before logging.

## Root cause 4 — Unanswered callback queries

**File**: `send/runtime/telegram_updates.py`

APP: and ADMIN_NAV: callbacks were never acknowledged with `answerCallbackQuery`.
Telegram displays a loading spinner for ~10 seconds and then an "error occurred" message,
even when the underlying edit succeeded.  This degraded UX confidence and may have led the
user to press buttons multiple times, exacerbating the message-spam problem.

**Fix**: Call `_ack_callback(callback_id)` after `bot_service.process_update(update)` for
all non-VOTE_ callbacks.

## Why PR #29 tests passed but live acceptance still failed

PR #29 tests used a fake publisher that always returned `{"ok": True}` for edits.  They
did not exercise the path where `edit_message` raises a 400 parse-entities error because
the test fake did not replicate Telegram's HTML validation behaviour.  The tests verified
the navigation state machine correctly but did not test the full round-trip including
the actual HTTP payload and Telegram's parse-mode validation.
