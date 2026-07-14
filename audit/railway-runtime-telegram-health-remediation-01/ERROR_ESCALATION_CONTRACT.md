# ERROR_ESCALATION_CONTRACT

## Destination
- `ADMIN_PROOF_CHAT_ID`
- `ADMIN_PROOF_THREAD_ID` only when configured and valid for that chat

## Active behavior
- Critical canonical error events trigger incident aggregation keyed by incident type + component.
- The first incident sends a Telegram alert immediately.
- Repeated identical incidents are aggregated.
- Reminder cadence is capped at one Telegram reminder every 5 minutes per active incident.
- Recovery notifications are emitted when an active incident is explicitly cleared (implemented for Twelve Data 429 recovery).
- Incident messages include incident type, first-seen time, latest-seen time, count, affected component, runtime state, and a safe operator action.
- Notification payloads exclude secrets and internal sensitive values.
