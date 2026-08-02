# ROOT_CAUSE_ANALYSIS.md

## Root Cause Analysis — Issue #31: Deleted-Conversation Invisible Response

### Timeline

| PR | What it fixed | What it missed |
|---|---|---|
| #35 | Multi-account session isolation | Deleted-conversation visibility |
| #36 | Stale-lock recovery, exception propagation, structured TelegramAPIError | Deleted-conversation visibility |
| This PR | Deleted-conversation visibility | — |

### Root Cause

**Classification:** Architectural assumption failure — edit success treated as visibility proof.

**Precise description:**

The `/start` handler called `_send_interactive_page`, which:
1. Read the active message ID from in-memory state.
2. Called `editMessageText` for the active message.
3. If `editMessageText` returned `ok: true`: persisted the same ID and **returned**.
4. `sendMessage` was only reached if `editMessageText` failed.

**Critical fact:** When a Telegram user deletes their conversation from the
client, the bot's message may still exist server-side. Telegram continues to
accept `editMessageText` for that message and returns `ok: true`. The bot
received this `ok: true`, treated it as proof of successful delivery, and
returned without calling `sendMessage`. The user saw nothing.

### Why Previous Fixes Did Not Help

**PR #35 (session isolation):**
- Fixed: USER and ADMIN session keys were not fully isolated.
- Missed: The delivery path still depended on edit success.

**PR #36 (stale-lock recovery):**
- Fixed: `clear_active_message` could deadlock on a stale filesystem lock;
  exceptions from `clear_active_message` were not handled gracefully.
- Missed: The stale-lock recovery only activated when Telegram returned an
  error from `editMessageText`. After conversation deletion, Telegram may
  return `ok: true`, so no error was produced, no stale-lock code ran,
  and `sendMessage` was never called.

### Why This Fix Works

`/start` now always calls `sendMessage`. It never calls `editMessageText`.
The user's conversation deletion state has no effect on whether a new visible
message is delivered, because the new implementation does not depend on the
old message in any way to produce the response.

### The Core Architectural Principle

> A successful `editMessageText` response proves only that Telegram accepted
> the edit on the server side. It does not prove that the message is visible
> in the user's current Telegram client state.

This principle is now enforced permanently in the `/start` path.
