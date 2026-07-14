# OBSERVABILITY_ERROR_SHAPE_FIX

## Fix
- `core.observability_logger.log_error()` now canonicalizes malformed error inputs even when callers provide `event_type="error"` shorthand payloads.
- Canonical error events always include `severity`, `error_type`, and `message` before schema validation.
- Extra shorthand fields are preserved inside canonical `context` data where allowed.

## Recursion protection
- Repeated identical observability write failures are aggregated in-memory.
- `observability_log_failed` emission is bounded to the first failure and then at most once every 5 minutes per repeated identical failure shape.
- This prevents uncontrolled `error_events.jsonl` growth from malformed-event or sink-failure loops.
