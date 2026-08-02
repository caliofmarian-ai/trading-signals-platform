# POLLER_AND_OFFSET_TRACE.md
# Issue #31 — Poller and Update Offset Behavior

## Pre-Fix Behavior

```python
for update in updates:
    LAST_UPDATE_ID = update["update_id"] + 1  # Offset advanced BEFORE processing
    process_update(update)                     # If this raises, update is lost
```

- If `process_update()` raised (due to stale lock), the outer try-except caught it
- The update was permanently consumed (offset advanced) but user saw nothing
- The poller continued but the `/start` update was gone

## Post-Fix Behavior

```python
for update in updates:
    LAST_UPDATE_ID = update["update_id"] + 1  # Still advanced before processing
    try:
        process_update(update)
    except Exception as exc:
        # Log the error with update_id
        ...
        # Poller continues to next update
```

- Failed updates are isolated — other updates are not blocked
- Offset is still advanced (prevents infinite re-processing of a broken update)
- Each failure is logged with its update_id for forensic analysis

## Heartbeat Mechanism

- `_POLLER_LAST_HEARTBEAT` is updated after every successful `getUpdates` response
- `get_poller_heartbeat_age()` returns seconds since last heartbeat
- `is_poller_alive()` returns False if heartbeat is older than 120s
- Main loop in `system_boot.py` emits a warning when heartbeat is stale

## Update Offset Behavior During Failure

| Event | LAST_UPDATE_ID Before | LAST_UPDATE_ID After | User Sees |
|-------|----------------------|---------------------|----------|
| Normal /start | N | N+1 | Response |
| /start (stale lock, pre-fix) | N | N+1 | Nothing |
| /start (stale lock, post-fix) | N | N+1 | Response |
| Network error (getUpdates) | N | N (unchanged) | Retry |
