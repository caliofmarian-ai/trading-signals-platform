# IDEMPOTENCY_AND_CONCURRENCY.md

## /start Idempotency and Concurrency Guard

### Problem

Two rapid `/start` commands for the same session (e.g., user presses Start
twice quickly, or a bot restart and a fresh `/start` arrive in quick succession)
could create uncontrolled duplicate anchors if not serialized.

### Solution: Per-Session Reset Guard

A lightweight in-memory per-session guard in `telegram_app_nav`:

```python
_RESET_GUARDS: Dict[_SessionKey, Dict[str, Any]] = {}
_RESET_GUARD_LOCK = threading.Lock()
_RESET_GUARD_TTL_SEC = 30.0
```

Each guard entry: `{"in_progress": bool, "generation": int, "ts": float}`

### Guard Contract

| State | Behavior |
|---|---|
| No guard for session | Acquired immediately; generation=1 |
| Guard held and not expired | Second `/start` is skipped (serialized) |
| Guard held but TTL expired | Treated as acquirable; guard is pruned |
| Guard released | Next `/start` acquires with generation+1 |

### Session Isolation

User sessions and Admin sessions always use different session keys:
- USER: `(chat_id=user_id, user_id=user_id, thread_id=None)`
- ADMIN: `(chat_id=admin_id, user_id=admin_id, thread_id=None)`

Guards are per-session-key. A USER `/start` guard never blocks an ADMIN `/start`.

### TTL Prevents Abandoned Locks

If a `/start` handler crashes between `acquire_start_reset_guard` and
`release_start_reset_guard` (e.g., process killed), the guard expires after
30 seconds. The next `/start` can then proceed. This is not a permanent lockfile
and does not survive process restart (in-memory only).

### Generation Counter

Each acquire increments the generation counter. This allows callers to detect
whether a session was reset between operations, if needed.

### API

```python
# Acquire (called by _handle_start_hard_reset before any reset work)
guard = acquire_start_reset_guard(chat_id, user_id, thread_id=None)
if not guard["acquired"]:
    return  # skip; concurrent reset in progress

# ... perform reset work ...

# Release (called in finally block)
release_start_reset_guard(chat_id, user_id, thread_id=None)
```
