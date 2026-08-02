# RESTART_GUARD_ANALYSIS.md
# Issue #31 — Restart Guard Analysis

## Current Behavior (Pre-Fix)

- `record_start()` was called without error handling in `start_system()`
- `record_start()` calls `_load_artifact()` which calls `with with_lock("restart_guard")`
- If `restart_guard.lock` was stale, `TimeoutError` propagated to `start_system()`
- Result: entire bot fails to start; no Telegram polling; permanently silent

## Crash Loop Thresholds

- `MAX_RESTARTS = 3` within `WINDOW_SECONDS = 60`
- Only counted when previous shutdown was NOT graceful (kind != "graceful")
- Railway Restart without SIGTERM cleanup → kind = "running" → counted

## Crash Loop Risk Assessment

A crash loop blocking Telegram requires ≥ 4 non-graceful restarts within 60 seconds.
This could happen if:
1. Bot is restart-looping due to startup failure
2. Railway manually restarts multiple times quickly
3. Restart Guard state is stale from a previous run

## Post-Fix Behavior

```python
try:
    start_info = record_start()
except Exception as start_exc:
    log_event({"severity": "WARNING", "error_type": "RESTART_GUARD_LOAD_FAILED", ...})
    start_info = {"crash_loop": False, "recovery_required": True, ...}
```

- Startup always proceeds (degraded-safe mode)
- `recovery_required=True` activates degraded safe mode notifications
- `crash_loop=False` ensures Telegram polling is NOT blocked

## Poller Liveness Monitoring

The main loop in `system_boot.py` now logs a warning when the poller heartbeat is stale:
```
warn_type: poller_heartbeat_stalled
context: {heartbeat_age_sec: ..., pid: ..., ...}
```
