# RESTART_VS_REDEPLOY_TIMELINE.md
# Issue #31 — Restart vs Redeploy Timeline Comparison

## A. Normal Operation

```
Process starts → lock files clean → getUpdates polling
→ /start → lock acquired (clean) → edit or send → response visible
```

## B. After Conversation Deletion

```
User deletes chat → bot still running → old message_id tracked in memory
→ User sends /start
→ edit_message(old_msg_id) → Telegram 400 "message to edit not found"
→ clear_active_message() → with_lock("telegram_ui_state") → 
  [pre-fix: blocks 10s on stale lock → TimeoutError → no send]
  [post-fix: stale lock reclaimed immediately → clear → send_message → response visible]
```

## C. After Railway Restart

**Why failure persisted pre-fix**:
1. Previous process was killed (SIGKILL or timeout after SIGTERM)
2. `telegram_ui_state.lock` was held at time of kill → file remains
3. New process starts with same container filesystem → lock file present
4. New process tries to load state → `with_lock("telegram_ui_state")` blocks 10s → TimeoutError
5. `_load_active_ui()` returns error → `_active_ui` is empty (correct)
6. But when user sends `/start` and bot tries to clear → same stale lock → TimeoutError in clear
7. **Pre-fix**: TimeoutError propagated → no send → silence

**Post-fix behavior**:
1. Stale lock detected (dead PID) → reclaimed immediately
2. State loaded (or started fresh on error) → bot proceeds
3. User sends `/start` → clear tried, any reclaim needed happens fast
4. `send_message()` always reached → response visible

## D. After Railway Redeploy

- New container → fresh ephemeral filesystem → no stale lock files
- Bot starts clean → all operations succeed
- This confirms lock files were in container filesystem (not a mounted volume)

## What Changes Between Restart and Redeploy

| Attribute | Restart | Redeploy |
|-----------|---------|---------|
| Container filesystem | **Same** (stale locks survive) | **Fresh** (stale locks gone) |
| Process PID | New (process restarted) | New |
| `LAST_UPDATE_ID` | Reset to None | Reset to None |
| `_POLLER_STARTED` | Reset to False | Reset to False |
| `_active_ui` dict | Empty (new process) | Empty |
| Persisted state files | Survive | Survive (if on volume) |
| Lock files in container fs | **Survive** | Gone |
| Railway environment vars | Same | May change (new deploy ID) |
