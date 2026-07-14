# STARTUP_AND_RECOVERY_NOTIFICATION_TRACE

## Startup and recovery events emitted
From `runtime.system_boot.start_system`:
- `recovery_started`
- `recovery_completed`
- `engine_start`
- error events on recovery/crash-loop failures

## Destination
- Event JSONL sinks (`engine_events.jsonl`, `error_events.jsonl`) through observability logger.

## Telegram startup/recovery notification
- No call to `telegram_publisher.send_message` in startup/recovery flow.
- No call to legacy `send_system.sh` in startup/recovery flow.

## Missing behavior explanation
Current Railway startup emits startup/recovery evidence to logs only; no active automatic Telegram startup/live/recovery notifier is wired.
