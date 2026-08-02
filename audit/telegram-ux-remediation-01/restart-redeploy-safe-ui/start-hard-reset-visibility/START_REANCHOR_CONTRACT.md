# START_REANCHOR_CONTRACT.md

## `/start` Hard-Reset and Visible Re-Anchor Contract

### Context

Every explicit `/start` command, including Start-button payload variants such as
`/start <payload>`, must act as a **hard UI reset and re-anchor** in private chats.

`/start` must **not** use the normal edit-first navigation path.

### Required Sequence

1. **Normalize the private session key:**
   `(chat_id=user_id, user_id=user_id, thread_id=None)`

2. **Acquire a short-lived per-session recovery/idempotency guard.**
   - If a concurrent `/start` is already in progress for this session, skip silently.
   - The guard uses a bounded TTL (`_RESET_GUARD_TTL_SEC = 30s`) to prevent
     abandoned locks.

3. **Read and clear the previously tracked bot message ID** via
   `prepare_start_hard_reset()`:
   - Memory: pop the session entry.
   - Persistence: call `clear_active_message()` (best-effort; failures captured
     and logged but never suppress step 6).

4. **Best-effort `deleteMessage` for the old tracked message:**
   - Deleted successfully → continue.
   - Message absent → continue.
   - Deletion forbidden / too old → continue.
   - Transport failure → continue (does not block send unless Telegram is
     completely unreachable).
   - No old message ID → skip deletion, continue.

5. **Call `sendMessage` exactly once** with the canonical Start/dashboard page.

6. **The newly returned message ID becomes the only active session anchor.**
   - Call `set_active_message(new_id)` (best-effort).

7. **If persistence fails after Telegram send succeeds:**
   - The visible send remains a success.
   - Do not delete the newly sent message.
   - Keep the new ID in memory.
   - Log the persistence failure.

8. **If `sendMessage` fails:**
   - Do not restore the previous message ID.
   - Leave the session cleared.
   - Allow the next `/start` to retry.
   - Log the failure with full diagnostics.

9. **Never silently fall back to editing the previous anchor during `/start`.**

### Non-Private Context

In non-private chat contexts (groups, forum topics), `/start` falls through to
the normal `_send_interactive_page` path. The hard-reset sequence is private-chat
only because:

- Private chat session key is `(chat_id=user_id, user_id=user_id, thread_id=None)`.
- Group/forum topics are not affected by single-user conversation deletion.
- Group behavior must remain unchanged.

### Single-Message Contract

After `/start`:
- `/status`, `/help`, `/admin`, Engine, Home, all callbacks **must edit the new anchor** normally.
- The hard-reset does not change navigation behavior; it only changes the initial anchor creation.

### Idempotency

- One `/start` → one new anchor.
- A concurrent duplicate `/start` for the same session is serialized behind the
  first via `acquire_start_reset_guard`.
- After the first finishes, subsequent `/start` commands create new anchors
  (each gets a new generation token).
- No global lock coupling USER and ADMIN sessions.
