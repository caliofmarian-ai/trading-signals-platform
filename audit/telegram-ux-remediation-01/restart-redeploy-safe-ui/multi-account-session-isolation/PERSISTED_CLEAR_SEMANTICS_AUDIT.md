# Persisted Clear Semantics Audit

## Before (Broken)

```python
def clear_active_message(user_id, chat_id, thread_id=None):
    key = normalize_session_key(chat_id, user_id, thread_id)
    removed = _active_ui.pop(key, None)
    if removed is None:
        return   # ← BUG: persisted delete never called for memory-miss
    # ... persisted delete only reached when session was in memory
```

**Contract violated:** A session existing only in persisted storage could not be removed.

## After (Fixed)

```python
def clear_active_message(user_id, chat_id, thread_id=None) -> Dict[str, Any]:
    key = normalize_session_key(chat_id, user_id, thread_id)
    _active_ui.pop(key, None)  # always removes from memory (even if absent)
    if not _persistence_enabled() or not _runtime_path_ready():
        return {...}
    # Always invokes exact persisted deletion regardless of in-memory presence
    delete_result = state_store.delete_telegram_ui_session(chat_id, user_id, thread_id)
    verification = state_store.verify_telegram_session_absent(chat_id, user_id, thread_id)
    return {
        "status": "ok",
        "in_memory_removed": True,
        "persisted_delete_attempted": True,
        "persisted_absent": verification["absent"],
        ...
    }
```

**Contract satisfied:**
1. Normalizes key ✓
2. Removes from memory (even if absent) ✓
3. Invokes exact persisted deletion always ✓
4. Verifies persisted absence ✓
5. Preserves unrelated sessions ✓
6. Returns structured result ✓
7. Logs failures safely ✓
8. Never restores stale message_id ✓

## delete_telegram_ui_session Semantics

1. Acquires exclusive lock on telegram_ui_state file
2. Reads latest persisted document
3. Normalizes all session keys (thread_id=0 → None)
4. Removes only the exact target session by canonical key equality
5. Preserves all other sessions
6. Writes atomically via save_json_atomic
7. Returns TelegramSessionDeleteResult with structured evidence
