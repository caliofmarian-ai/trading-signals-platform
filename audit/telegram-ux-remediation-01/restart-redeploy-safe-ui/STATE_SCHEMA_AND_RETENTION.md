# State Schema and Retention

## Artifact
- Path: `state/telegram_ui_state.json` (under active runtime base dir)
- Lock: `telegram_ui_state`
- Version: `1.0.0`

## Schema
```json
{
  "version": "1.0.0",
  "retention_seconds": 604800,
  "max_sessions": 1000,
  "sessions": [
    {
      "chat_id": -100123,
      "user_id": 123456,
      "thread_id": 42,
      "message_id": 9001,
      "updated_ts": 1765063000
    }
  ],
  "last_updated_ts": 1765063000
}
```

## Validation and migration behavior
- Unsupported `version` raises validation error.
- Corrupt JSON raises validation error.
- Load path catches failures and safely starts with empty in-memory state.
- Legacy root migration path supported through state-store artifact loader.

## Retention and cleanup
- Entries older than retention are dropped.
- Duplicate session keys are deduplicated using newest `updated_ts`.
- State is bounded to `max_sessions` most recent entries.
