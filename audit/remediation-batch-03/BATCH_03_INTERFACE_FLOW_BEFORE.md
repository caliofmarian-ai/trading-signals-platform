# BATCH_03_INTERFACE_FLOW_BEFORE

## Findings addressed
- GAP-005
- GAP-006
- GAP-008
- GAP-019

## Before-state interface flow
1. `core/signal_engine.py` produced raw `signal_event` payloads and called `core/distribution_router.py:route()`.
2. `core/distribution_router.py` loaded channels from config, but limits/admin/reset truth was split between config defaults and environment fallbacks.
3. `route()` selected destinations, called `core.telegram_publisher.send_message()`, then attempted observability logging through `_log_tier_publish()`.
4. `_log_tier_publish()` called `core.observability_logger.build_event()` with unsupported kwargs (`module=`, `now_ts=`, `extra=`), so tier publication logging could raise before a canonical event was built.
5. `core/observability_logger.py` only enforced a minimal runtime allow-list and did not validate emitted events against `send/schema/event_schema.json`.
6. `send/schema/event_schema.json` still described an older message-style structure and did not match live distribution events.
7. `log_event()` wrote JSONL files fail-open, but incompatible event types and invalid warning call sites could reroute material events into generic logger-failure records.

## Before-state decision -> persistence map
- distribution decision: `core/signal_engine.py` signal event
- route selection: `core/distribution_router.py:route()`
- publish attempt: `core.telegram_publisher.send_message()`
- publish result handling: success / failure / skip branches in `route()`
- event construction: `core/distribution_router.py:_log_tier_publish()` and `core/distribution_router.py:maybe_daily_reset()`
- schema validation: minimal allow-list only inside `core/observability_logger.py`
- persistence: `core/observability_logger.py:log_event()` -> `distribution_events.jsonl` / `error_events.jsonl`

## Root causes
- Router and logger interfaces diverged after BATCH-01/BATCH-02.
- Live event payloads evolved, but `event_schema.json` did not.
- Config-file admin/limit/reset truth was not fully consumed by the router.
- Legacy warning/event producers still depended on older shorthand observability calls.
