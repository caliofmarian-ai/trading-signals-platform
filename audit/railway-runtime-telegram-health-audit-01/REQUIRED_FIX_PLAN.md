# REQUIRED_FIX_PLAN

## Minimal safe remediation order
1. Fix command-response gap first:
   - add explicit handling for `/start`, `/help`, `/status` (or explicit unsupported-command response)
   - ensure unknown slash commands do not fail silently.
2. Harden response sending context:
   - avoid forcing `message_thread_id` for non-topic chats.
3. Fix observability error-shape defect:
   - guarantee canonical `error` payload (`severity`, `error_type`, `message`) before validation.
4. Add active operator notification wiring:
   - startup/recovery notifier on successful boot and blocked boot
   - error escalation notifier for repeated critical failures/rate-limit storms.
5. Reconnect admin proof Telegram route if required by ops policy.
6. Add focused regression tests for:
   - `/start` `/help` `/status`
   - unknown slash fallback
   - private-chat reply with configured admin thread id
   - 429 storm error logging shape and volume controls
   - startup/error notification routing

## Constraint
No strategy behavior changes (WIDE/FOCUS, market cadence unchanged).
