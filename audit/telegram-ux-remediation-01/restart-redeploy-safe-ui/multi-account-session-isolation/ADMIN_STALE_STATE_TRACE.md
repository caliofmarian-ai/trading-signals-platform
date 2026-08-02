# ADMIN Stale State Trace

## Pre-condition

```
Persisted state: [
  {chat_id: A, user_id: A, message_id: 2001, thread_id: null},
  {chat_id: U, user_id: U, message_id: 1001, thread_id: null}
]
In-memory: {(A,A,None): {message_id: 2001}, (U,U,None): {message_id: 1001}}
```

ADMIN deletes conversation in Telegram app. Message 2001 no longer exists.

## Failure Sequence (BEFORE fix)

1. ADMIN sends `/start`
2. `get_active_message(A, A)` → returns 2001 (from memory)
3. `edit_message(A, 2001, ...)` → "message to edit not found"
4. `_classify_edit_message_failure` → "stale"
5. `clear_active_message(A, A)`:
   - `_active_ui.pop((A,A,None), None)` → returns `{message_id: 2001}` (was in memory)
   - Persisted delete triggered ✓ (happened to work this time)
6. `send_message(A, ...)` → new message 2002
7. `set_active_message(A, A, 2002)` → memory + persisted updated

**But**: if between steps 5 and 6 the process restarts (Railway deployment):
1. Restart → `_load_active_ui()` → loads from persisted state
2. If step 5's persisted delete failed (e.g., due to Defect-1 on a prior cycle):
   - Persisted state still has `{message_id: 2001}`
   - In-memory loads `(A,A,None): {message_id: 2001}`
3. Next `/start` → edit 2001 → stale → clear → (skip if memory miss) → loop

## Recovery Sequence (AFTER fix)

1. ADMIN sends `/start`
2. `get_active_message(A, A)` → 2001 or None (if already cleared)
3. Attempt edit → "message to edit not found"
4. `clear_active_message(A, A)`:
   - Pop from memory (even if absent)
   - `delete_telegram_ui_session(A, A)` → atomically removes from persisted state
   - `verify_telegram_session_absent(A, A)` → confirmed absent
5. `send_message(A, ...)` → 2002
6. `set_active_message(A, A, 2002)` → tracked
7. Future restart → load → only 2002 found → edit works
