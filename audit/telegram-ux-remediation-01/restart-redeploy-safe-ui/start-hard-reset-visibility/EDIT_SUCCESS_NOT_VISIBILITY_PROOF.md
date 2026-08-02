# EDIT_SUCCESS_NOT_VISIBILITY_PROOF.md

## A Successful editMessageText Response Is Not Proof of Visibility

### The Telegram Edit/Delete Asymmetry

Telegram's `editMessageText` operates on the server-side message store. When a
Telegram user deletes their copy of a conversation:

- The bot's message is **no longer visible** in the user's client.
- The bot's message **may still exist** in Telegram's server state.
- Telegram **may still accept** `editMessageText` for that message.
- Telegram **may still return** `{"ok": true}`.

There is no Telegram API field that indicates whether a message is currently
visible in a specific user's client. Client-side conversation deletion is a
client-local operation. The Telegram Bot API has no probe for this state.

### Previous Incorrect Design

```
receive /start
  → get_active_message()         # returns old message ID
  → editMessageText(old_id)      # Telegram returns ok=true
  → set_active_message(old_id)   # same ID re-persisted
  → return                       # NO sendMessage called
                                 # USER SEES NOTHING
```

The assumption was: if `editMessageText` returns `ok=true`, the message is
visible to the user. **This assumption is false after client-side deletion.**

### Correct Design (Post-Fix)

```
receive /start
  → [NEVER call editMessageText]
  → prepare_start_hard_reset()   # read + clear old session
  → delete_message(old_id)       # best-effort, never blocking
  → sendMessage(new page)        # always: one guaranteed visible message
  → set_active_message(new_id)   # new anchor
```

The **only reliable way** to guarantee a message is visible after potential
client-side deletion is to **send a new message**. This is what `/start` now does.

### Consequence for Stale-Error Recovery

The previous stale-error recovery path depended on Telegram returning a
`400 message to edit not found` error. After conversation deletion, this error
may never come. Stale-error recovery is irrelevant to this failure mode because
there is no error to detect.

### Summary

| Scenario | editMessageText response | User sees message? |
|---|---|---|
| Message exists, conversation intact | ok=true | ✅ Yes |
| Message exists, conversation deleted by user | ok=true (possible) | ❌ No |
| Message deleted server-side | 400 error | ❌ No |

`/start` must cover **all three rows** with a single sendMessage. It does now.
