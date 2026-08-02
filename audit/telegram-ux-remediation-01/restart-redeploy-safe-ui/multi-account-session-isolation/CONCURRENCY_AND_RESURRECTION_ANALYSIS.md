# Concurrency and Resurrection Analysis

## Atomic Operations

All persisted state operations use `with_lock("telegram_ui_state")`:
- `delete_telegram_ui_session` acquires the lock, reads, modifies, writes atomically
- `update_telegram_ui_state` (used by set_active_message) also holds the lock
- Two concurrent operations for DIFFERENT sessions cannot corrupt each other (lock serializes writes, updater preserves unrelated sessions)
- Two concurrent operations for the SAME session are serialized by the lock; last-writer wins

## Resurrection Risk

Resurrection occurs when a cleared session reappears. This required:
1. Session cleared from memory but NOT from persisted state (Defect-1)
2. Process restart → persisted state loaded → session reappears

**Fix:** `clear_active_message` always invokes `delete_telegram_ui_session` regardless of in-memory presence. Post-delete verification confirms absence.

## Concurrent ADMIN Clear + ADMIN Replacement

Scenario: Thread 1 calls `clear_active_message(A, A)`, Thread 2 calls `set_active_message(A, A, 2002)`.

Order A (clear first):
1. Clear: pop from memory, delete from persisted (lock held) → session absent
2. Set: write 2002 to memory and persisted (lock held) → 2002 active ✓

Order B (set first):
1. Set: write 2002 to memory and persisted → 2002 active
2. Clear: pop from memory, delete from persisted → session absent
3. Next `/start` → no active message → sends new 2003 ✓

Neither order can restore the stale message_id 2001. ✓

## Thread Safety

`_active_ui_lock` (threading.RLock) guards all in-memory operations. File-level `with_lock` guards all persisted operations. Both are held during their respective critical sections. No deadlock risk (they are not both held simultaneously).
