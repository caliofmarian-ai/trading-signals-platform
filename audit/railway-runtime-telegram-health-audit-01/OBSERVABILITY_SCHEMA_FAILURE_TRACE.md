# OBSERVABILITY_SCHEMA_FAILURE_TRACE

## Defect summary
Shorthand error payloads are emitted with `event_type="error"` but without required error schema fields (`severity`, `error_type`, `message`) inside `data`.

## Primary malformed call sites
- `send/runtime/engine_loop.py` lines 24-29
- `send/core/signal_engine.py` lines 402-407
- `send/runtime/telegram_updates.py` lines 65-69
- `send/runtime/distribution_scheduler.py` lines 44-48

## Failure chain
1. `observability_logger.log_error(error_dict)` called.
2. Because `event_type == "error"`, `log_error` does **not** rebuild canonical error payload.
3. `log_event` normalizes+validates event.
4. Validation of `event_type=error` fails (`data.severity/error_type/message` missing).
5. Fallback path emits a new canonical error: `error_type="observability_log_failed"`.

## Result
Original error details are downgraded to context in fallback events, inflating `error_events.jsonl` during failure storms.
