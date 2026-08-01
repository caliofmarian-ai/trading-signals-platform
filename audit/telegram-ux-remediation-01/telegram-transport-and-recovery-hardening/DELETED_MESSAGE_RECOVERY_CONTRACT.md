# DELETED MESSAGE RECOVERY CONTRACT

## Single-message model

The application maintains one active UI message per `(chat_id, user_id, thread_id)` session
in `telegram_app_nav._active_ui`.  Navigation edits this message rather than sending new ones.

## Recovery scenarios

### Scenario A — User deletes the active message

The next navigation attempt calls `edit_message(chat_id, message_id, ...)`.
Telegram returns `400: message to edit not found`.

Flow:
1. `_edit_interactive_message` catches the exception.
2. `_classify_edit_message_failure` returns `"stale"`.
3. `clear_active_message(user_id, chat_id)` removes the stale entry.
4. `_edit_interactive_message` returns `False`.
5. `_send_interactive_page` finds no active message.
6. `send_message` is called — delivers one new message.
7. The new `message_id` is stored as the active message.
8. All subsequent navigations edit this new message.

**Result**: exactly one replacement message; navigation continues normally.

### Scenario B — User deletes the entire conversation

Identical to Scenario A: `_active_ui` still holds the old `message_id`, which Telegram
treats as deleted.  The stale-edit path triggers on the first `/start` after the
conversation is deleted, sends one new message, and the session is fully restored.

### Scenario C — send_message also fails after stale edit

1. Steps 1–5 as above.
2. `send_message` raises.
3. `observability_logger.log_error` records `telegram_app_nav_send_failure`.
4. No active message is stored.
5. On the user's next interaction, the same recovery sequence repeats.

This is not silent: the error is logged (test 11 verifies).

### Scenario D — Unexpected edit error (not stale)

The active message is **not** cleared.  The next send_message call is attempted.
If send_message succeeds, the new message_id becomes active (test 12 verifies).
The unexpected edit error is logged as `telegram_app_nav_edit_failure`.

## What does NOT recover automatically

- `_active_ui` is in-memory only.  A process restart clears it, so all sessions appear
  fresh.  This is correct: Telegram's getUpdates delivers pending updates including any
  `/start` commands, which establishes a new active message.
- If `send_message` repeatedly fails due to a missing `TELEGRAM_BOT_TOKEN`, the bot will
  log errors but cannot deliver a response.  This is a configuration failure, not a
  recoverable runtime state.

## Token present in active message vs. not

Whether an active message is present has no effect on whether the bot can receive updates.
The poller is independent of the UI message state.
