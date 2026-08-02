# LIVE_FAILURE_AFTER_PR36.md

## Confirmed Live Failure After PR #36

### Exact Production Sequence

1. User sends `/start`.
2. Bot responds normally.
3. User **deletes the complete Telegram conversation/history** from the client.
4. User opens the bot and presses Start or sends `/start`.
5. **The bot produces no visible response.**

### Why PR #36 Did Not Fix This

PR #36 (copilot/refs-31-telegram-ui-restart-fix) corrected:
- Stale-lock recovery in persisted UI state
- Exception propagation from `clear_active_message`
- Structured `TelegramAPIError` classification

These were real defects, but none of them are the cause of the deleted-conversation visibility failure.

### Root Cause

When the user deletes the Telegram conversation on their client side, **the bot message still exists server-side**. Telegram continues to accept `editMessageText` for that message and returns `ok: true`. The previous `/start` handler called `_send_interactive_page`, which attempted `editMessageText` first. That edit *succeeded*, the bot treated it as proof of delivery, and never called `sendMessage`. The user sees nothing.

This is not an API error. This is not a stale-lock. This is an architectural dependency on edit success as a proxy for visibility — a proxy that does not hold after client-side conversation deletion.

### Evidence

- PR #35 did not solve deleted-conversation recovery.
- PR #36 fixed stale-lock handling but live behavior remained unchanged.
- The previous design incorrectly depended on edit failure (Telegram returning an error) to detect the need for a new send.
- After conversation deletion, Telegram does not necessarily return an error. It can return `ok: true`.

### Fix

`/start` is now treated as an **explicit deterministic visible re-anchor**. It always calls `sendMessage`. It never calls `editMessageText`. The hypothesis that edit success = visibility is permanently disproven and no longer part of the `/start` path.
