# BATCH_04_TELEMETRY_CONTRACT

## Applied authority
- Canon: `TRADE_TEMPORAL_TELEMETRY_SPEC_v2.0.0.md`
- Prior owner decision applied: OWNER-004

## Canonical registration contract implemented
- Module: `send/core/trade_temporal_telemetry.py`
- Entry point: `register_open_now_trade(event, now_ts)`
- Import side effects: none
- Network usage: none

## Telemetry identity contract
- Stable trade identity: `trade_id == signal_id`
- Immutable registration fields enforced:
  - `signal_id`
  - `symbol`
  - `timeframe`
  - `direction`
  - `entry_price`
  - `open_ts`
  - `expiry_minutes`
  - `expiry_ts`
  - `candle_ts`
- Duplicate identical registration: returns `already_registered`
- Duplicate conflicting registration: raises clear `ValueError`

## Required persisted registration fields
- Identity:
  - `trade_id`
  - `signal_id`
  - `symbol`
  - `timeframe`
  - `direction`
- Timing:
  - `open_ts`
  - `open_ts_utc`
  - `mid_expiry_ts`
  - `mid_expiry_ts_utc`
  - `expiry_minutes`
  - `expiry_ts`
  - `expiry_ts_utc`
  - `candle_ts`
  - `candle_ts_utc`
- Price and strategy context:
  - `entry_price`
  - `buffer_mode`
  - `buffer_price`
  - `score_total`
  - `TPS`
  - `decision_debug`
- Placeholder outcome fields preserved for downstream tracking:
  - `result_at_expiry`
  - `mid_expiry_price`
  - `expiry_price`
  - `post_1m_price`
  - `post_3m_price`
  - `post_5m_price`
  - `would_win_at_plus_1m`
  - `would_win_at_plus_3m`
  - `would_win_at_plus_5m`
  - `post_expiry_recovery`

## Persistence behavior
- Durable registry path: `observability/open_trades_registry.json` under `BINARYBOT_BASE_DIR`
- Atomicity: `storage.save_json_atomic(...)`
- Restart safety: registry is read back from disk via `get_open_trade(...)`
- Invalid registrations are rejected before persistence

## UTC semantics
- Canonical UTC strings are stored as `YYYY-MM-DDTHH:MM:SSZ`
- Epoch timestamps remain preserved alongside UTC strings

## Observability behavior
- Successful and idempotent registration emit canonical `decision` events with:
  - `decision_kind = OPEN_NOW_REGISTERED`
  - `telemetry_register_status = registered|already_registered`
- Observability failures are swallowed so successful persistence is not misreported as failed

## Integration points
- `send/core/signal_engine.py` now loads the real module and delegates OPEN_NOW registration to it
- `send/core/distribution_router.py` continues to register callback metadata independently for the vote surface
