# BATCH_07_INPUT_CONTRACT_INVENTORY

## Input Sources for Analytics and Research Toolchain

### 1. outcomes.jsonl

| Field             | Value                                                         |
|-------------------|---------------------------------------------------------------|
| Path              | `$OUTCOMES_LOG` env var → default `/opt/binarybot/outcomes/outcomes.jsonl` |
| Record type       | Outcome vote record (flat JSON object, NOT observability envelope) |
| Producer          | `outcome_service._build_vote_record()` → `storage.append_jsonl()` |
| Canonical spec    | OUTCOME_TRACKING_SPEC_v2.0.0, EVENT_SCHEMA_SPEC_v2.0.0 (`user_outcome`, `OUTCOME_SET`) |
| Parser            | `core.jsonl_parser.iter_jsonl()` |
| Required fields   | `signal_id` (str), `outcome` (str: WIN/LOSE/MISSED) |
| Optional fields   | `user_id`, `tier`, `voted_ts`, `voted_ts_utc`, `telemetry_trade_id`, `symbol`, `direction`, `timeframe`, `vote_window`, etc. |
| Legacy compat     | None — records written by current outcome_service after BATCH-04 |
| Invalid record    | Missing required field → excluded + counted in `invalid_count` |
| Malformed JSON    | ParseError raised → yielded as (None, err) by iter_jsonl |
| Empty input       | Returns `no_data=True` result, zero counts |
| Duplicate handling | Dedup key `(signal_id, user_id)` — first occurrence kept |
| Time ordering     | `voted_ts` (epoch sec); records processed in file order |
| Consumer          | analytics_engine, research_engine |

### 2. engine_events.jsonl

| Field             | Value                                                         |
|-------------------|---------------------------------------------------------------|
| Path              | `$ENGINE_EVENTS_LOG` env var → default `$OBS_DIR/engine_events.jsonl` |
| Record type       | Canonical observability envelope; event_types: `signal_event`, `decision`, `engine_start`, `engine_stop`, `system_health`, `recovery_started`, `recovery_completed`, `strategy_optimizer` |
| Producer          | `observability_logger.log_event()` via signal_engine, system_boot |
| Canonical spec    | EVENT_SCHEMA_SPEC_v2.0.0 |
| Parser            | `core.jsonl_parser.iter_jsonl()` |
| Required fields   | `event_type`, `event_id`, `schema_version`, `ts_utc`, `ts_epoch_ms` (envelope); `stage`, `signal_id` (signal_event top-level) |
| Optional fields   | `symbol`, `timeframe`, `data.*` |
| Invalid record    | Missing event_type or stage → excluded + invalid_count++ |
| Malformed JSON    | ParseError → (None, err) |
| Empty input       | Returns `no_data=True` funnel |
| Duplicate handling | Dedup by `event_id` (skips re-seen event_ids) |
| Time ordering     | `ts_epoch_ms` (ms UTC); file order used |
| Consumer          | research_engine (signal funnel), strategy_auditor_lib |
| **Critical note** | `stage` is a **top-level correlation field** in canonical events (after observability_logger normalization). It is NOT inside `data{}`. research_engine was incorrectly reading `rec.get("data", {}).get("stage")` — fixed in BATCH-07 to `rec.get("stage")`. |

### 3. distribution_events.jsonl

| Field             | Value                                                         |
|-------------------|---------------------------------------------------------------|
| Path              | `$DIST_EVENTS_LOG` env var → default `$OBS_DIR/distribution_events.jsonl` |
| Record type       | Canonical observability envelope; event_type: `tier_publish`, `tier_reset` |
| Producer          | `distribution_router._log_tier_publish()` via `observability_logger` |
| Canonical spec    | EVENT_SCHEMA_SPEC_v2.0.0 (`tier_publish`) |
| Parser            | `core.jsonl_parser.iter_jsonl()` |
| Required fields   | `event_type`, `data.publish_result` (enum: PUBLISHED/FAILED/SKIPPED_SILENT/SKIPPED_LIMIT/SKIPPED_DISABLED/DUPLICATE_SUPPRESSED) |
| Optional fields   | `signal_id`, `route`, `tier`, `stage`, `data.reason` |
| Invalid record    | Unknown publish_result → invalid_count++ |
| Malformed JSON    | ParseError → (None, err) |
| Empty input       | Returns `no_data=True` dist metrics |
| Duplicate handling | Not deduplicated (each tier_publish is an independent event) |
| Time ordering     | File order |
| Consumer          | analytics_engine (distribution metrics), research_engine (distribution summary) |

### 4. fsm_events.jsonl

| Field             | Value                                                         |
|-------------------|---------------------------------------------------------------|
| Path              | `$FSM_EVENTS_LOG` env var → default `$OBS_DIR/fsm_events.jsonl` |
| Record type       | Canonical observability envelope; event_type: `fsm_transition` |
| Producer          | `fsm_runtime` via `observability_logger` |
| Canonical spec    | EVENT_SCHEMA_SPEC_v2.0.0 (`fsm_transition`) |
| Parser            | `strategy_auditor_lib._read_jsonl()` |
| Required fields   | As per schema |
| Consumer          | strategy_auditor_lib (loaded but not yet analyzed in current report) |

### 5. error_events.jsonl

| Field             | Value                                                         |
|-------------------|---------------------------------------------------------------|
| Path              | `$ERROR_EVENTS_LOG` env var → default `$OBS_DIR/error_events.jsonl` |
| Record type       | Canonical observability envelope; event_type: `error`, `warning` |
| Producer          | `observability_logger.log_error()`, `log_warning()` |
| Canonical spec    | EVENT_SCHEMA_SPEC_v2.0.0 (`error`, `warning`) |
| Parser            | `strategy_auditor_lib._read_jsonl()` |
| Consumer          | strategy_auditor_lib (loaded, not yet analyzed in current report) |

### 6. config/intelligence_settings.json

| Field             | Value                                                         |
|-------------------|---------------------------------------------------------------|
| Path              | `$STRATEGY_AUDITOR_SETTINGS` env var → project-relative `config/intelligence_settings.json` |
| Record type       | JSON config object |
| Producer          | Repository config (static) |
| Required fields   | `sources`, `reports`, `heatmap`, `bottleneck_detection`, `symbol_health` |
| Consumer          | strategy_auditor_lib.load_settings() |

## Invalid Record Behavior Summary

| Condition                        | Behavior                                         |
|----------------------------------|--------------------------------------------------|
| Malformed JSON in any JSONL      | ParseError yielded by iter_jsonl; invalid_count++ |
| Non-dict JSON value              | ParseError raised (never returns {} silently)    |
| Missing required outcome field   | Excluded; invalid_count++                        |
| Unknown outcome value            | Excluded; invalid_count++                        |
| Missing signal_id in outcome     | Excluded; invalid_count++                        |
| Unknown stage in signal_event    | Classified in unsupported_stages{}; not coerced  |
| Missing stage in signal_event    | Excluded; invalid_count++                        |
| Unknown publish_result           | invalid_count++                                  |
| Duplicate (signal_id, user_id)   | Second+ occurrence skipped (not counted)         |
| Duplicate event_id               | Second+ occurrence skipped (not counted)         |
| Empty JSONL file                 | no_data=True result                              |
| Missing JSONL file (outcomes)    | no_data=True + reason="..._not_found"            |
| Missing JSONL file (engine log)  | no_data=True + reason="..._not_found"            |
| Missing settings file            | RuntimeError with clear path message             |
