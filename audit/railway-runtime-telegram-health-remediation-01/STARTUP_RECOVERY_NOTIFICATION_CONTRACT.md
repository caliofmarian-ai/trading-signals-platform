# STARTUP_RECOVERY_NOTIFICATION_CONTRACT

## Destination
- `ADMIN_CONTROL_CHAT_ID`
- `ADMIN_CONTROL_THREAD_ID` only when configured and valid for that chat

## Notifications
- `BOT STARTING` after Railway init + readiness succeed and before `start_system()` begins.
- `BOT LIVE` only after runtime boot reaches the running state and Railway readiness evaluation has already completed.
- `RECOVERY STARTED` and `RECOVERY COMPLETED` when restart-guard recovery is active.
- `DEGRADED SAFE MODE` when the runtime resumes after a counted recovery.
- `STARTUP BLOCKED` when boot is blocked by validation or restart-guard safety.
- `GRACEFUL SHUTDOWN` during orderly shutdown.
