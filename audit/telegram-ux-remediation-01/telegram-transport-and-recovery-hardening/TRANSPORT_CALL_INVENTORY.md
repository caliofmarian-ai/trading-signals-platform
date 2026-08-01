# TRANSPORT CALL INVENTORY

Audit scope: `send/core/telegram_publisher.py`, `send/runtime/telegram_updates.py`, `send/core/bot_service.py`

## Telegram API Calls

| Call site | Module | Function | API method | parse_mode before fix | parse_mode after fix |
|---|---|---|---|---|---|
| `send_message` | `telegram_publisher` | `send_message()` | `POST /sendMessage` | none | none (unchanged) |
| `edit_message` | `telegram_publisher` | `edit_message()` | `POST /editMessageText` | `"HTML"` | **none** (removed) |
| `send_document` | `telegram_publisher` | `send_document()` | `POST /sendDocument` | n/a | n/a |
| `answer_callback_query` | `telegram_publisher` | `answer_callback_query()` | `POST /answerCallbackQuery` | n/a | n/a (new function) |
| VOTE_ ack | `telegram_updates` | `_answer_callback_query()` | `POST /answerCallbackQuery` | n/a | n/a |
| APP:/ADMIN_NAV: ack | `telegram_updates` | `_ack_callback()` | `POST /answerCallbackQuery` | missing before fix | n/a (new call) |
| getUpdates | `telegram_updates` | `poll_updates()` | `GET /getUpdates` | n/a | n/a |

## parse_mode state before fix

- `edit_message()` set `payload["parse_mode"] = "HTML"` only when `text` was provided.
- `send_message()` never set `parse_mode`.
- This created an inconsistency: messages sent via `send_message` used no parse mode (plain text rendering) but subsequent edits via `edit_message` switched to HTML mode.
- Any text containing HTML-special characters (`<`, `>`, `&`) caused a Telegram 400 "Bad Request: can't parse entities" error on the edit path.

## parse_mode state after fix

- `edit_message()` no longer sets `parse_mode`.
- `send_message()` still does not set `parse_mode`.
- Both calls now use the same mode (Telegram default: no formatting), which is consistent with the page text format (plain text with Markdown-style `*bold*` that renders literally — no format errors).

## New function: answer_callback_query

Added to `telegram_publisher` to expose a typed wrapper for `POST /answerCallbackQuery`.
Used by `telegram_updates._ack_callback()` to dismiss the Telegram loading spinner for APP: and ADMIN_NAV: callbacks.
