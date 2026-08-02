# Root Cause Analysis — Multi-Account Session Isolation

**Issue:** #31 — Make Telegram UI restart and redeploy safe  
**Branch:** copilot/copilotrefs-31-multi-account-session-isolation-v2  
**Date:** 2026-08-02

## Verified Production Failure

Owner has two Telegram accounts in the same mobile app:
- USER account (user_id = U)
- ADMIN/OWNER account (user_id = A, A ≠ U)

Observed:
1. USER opened bot, /start /help /status worked.
2. Owner switched to ADMIN account.
3. ADMIN deleted its conversation history.
4. ADMIN /start and all subsequent commands produced **no visible response**.
5. USER continued working normally.

**Therefore:** Telegram polling was alive; update processing was alive; the failure was **isolated to the ADMIN session** which became stuck on stale persisted active-message state.

## Five Confirmed Defects

### DEFECT-1 — `clear_active_message()` early return skips persisted deletion

```python
# BEFORE (broken):
removed = _active_ui.pop(key, None)
if removed is None:
    return   # ← exits without clearing persisted state!
```

A session that existed only in persisted state (e.g., after a restart when memory was reset) **could not be cleared**. The stale ADMIN message_id survived, was reloaded on next boot, and caused perpetual edit-not-found loops.

### DEFECT-2 — No exact-session deletion primitive in state_store

The `update_telegram_ui_state(updater)` pattern reads the whole document and rewrites it, but there was no standalone `delete_telegram_ui_session` function with atomic lock + structured evidence. A persisted-only session had no clean removal path.

### DEFECT-3 — `get_runtime_diagnostics` lied about persisted state

```python
# BEFORE (broken):
"active_message_id": entry.get("message_id"),
"persisted_message_id": entry.get("message_id"),  # ← same value! not independently read
```

Post-clear diagnostics would show `persisted_message_id=None` even if the session survived on disk (because the in-memory entry was gone). This masked the actual bug.

### DEFECT-4 — `validate_telegram_ui_state` used raw thread_id in dedup key

```python
# BEFORE (broken):
thread_id = _safe_int(item.get("thread_id"), ...)  # could be 0 or None
key = (chat_id, user_id, thread_id)  # 0 ≠ None → two keys for same session!
```

For private chats, thread_id=0 (from JSON) and thread_id=None (canonical) produced **different dedup keys**. This allowed duplicate private-session variants to coexist in persisted state, creating resurrection opportunities.

### DEFECT-5 — Replacement-send failure left no guaranteed clean state

When `send_message` failed after a stale-edit detection:
- The session was cleared from memory ✓
- But persisted state was only cleared if the session was in memory **before** the clear (Defect-1 again)
- A subsequent `/start` could load the stale session from disk and loop

## Impact

The ADMIN session became permanently silent after:
1. ADMIN conversation was deleted (message no longer editable)
2. `clear_active_message` was called but skipped persisted deletion (DEFECT-1)
3. On next request, the stale ADMIN message_id was reloaded from disk
4. Edit attempt → "message to edit not found" → clear → (skip persisted) → reload → loop

USER was unaffected because USER and ADMIN have **different session keys**:
- USER key: `(user_id=U, chat_id=U, thread_id=None)`
- ADMIN key: `(user_id=A, chat_id=A, thread_id=None)`

No sharing of state between accounts.
