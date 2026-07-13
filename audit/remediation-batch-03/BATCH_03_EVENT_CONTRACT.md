# BATCH_03_EVENT_CONTRACT

## Findings addressed
- GAP-005
- GAP-006
- GAP-008
- GAP-019

## Canonicalized live contract

### Common envelope
All BATCH-03 events now require:
- `event_id`
- `event_type`
- `schema_version`
- `ts_utc`
- `ts_epoch_ms`
- `service`
- `env`
- `run_id`
- `source.module`
- `source.function`
- `host.hostname`
- `host.pid`
- `host.app_version`
- `data`

### Shared correlation fields
Supported top-level correlation fields:
- `signal_id`
- `symbol`
- `timeframe`
- `candle_ts_epoch`
- `route`
- `tier`
- `destination_id`
- `stage`
- `user_id`
- `message_id`
- `thread_id`
- `trace_id`

Unknown correlation fields are rejected explicitly.

## Distribution event families

### `tier_publish`
Required top-level fields:
- `signal_id`
- `route`
- `tier`
- `stage`

Required payload fields:
- `publish_result`
- `route_state_before`
- `route_state_after`
- `limit`
- `counter_before`
- `counter_after`
- `counted`
- `attempted`
- `destination_kind`
- `feedback_enabled`
- `transport.ok`
- `transport.message_id`
- `transport.error`
- `dedup.key`
- `dedup.was_duplicate`
- `dedup.action`

Optional payload fields:
- `reason`

Supported publish results:
- `PUBLISHED`
- `SKIPPED_SILENT`
- `SKIPPED_LIMIT`
- `SKIPPED_DISABLED`
- `FAILED`
- `DUPLICATE_SUPPRESSED`

### `tier_reset`
Required payload fields:
- `reset_time_london`
- `effective_date_london`
- `before`
- `after`

## Compatibility event families kept readable/testable
- `warning`
- `error`
- `OUTCOME_SET`
- `outcome_panel_enabled`
- `system_health`
- `strategy_optimizer`
- existing runtime families already accepted before BATCH-03 (`engine_start`, `engine_stop`, `signal_event`, `decision`, `fsm_transition`, `admin_change`, `user_outcome`)

## Persistence contract
- sink selection now comes from `send/schema/event_schema.json`
- runtime validation and file routing use the same contract source
- JSONL writes are locked per sink before append
- logger failures emit explicit `observability_log_failed` error events instead of malformed partial records
