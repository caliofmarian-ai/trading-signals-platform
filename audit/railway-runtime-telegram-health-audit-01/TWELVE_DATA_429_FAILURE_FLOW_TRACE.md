# TWELVE_DATA_429_FAILURE_FLOW_TRACE

## Exact flow
1. `runtime.engine_loop.start_engine()` ticks every 2s.
2. Calls `core.signal_engine.run_once(now_ts)`.
3. For each symbol, `runtime.market_client.get_candles` -> `fetch_klines`.
4. On exhausted credits: Twelve Data responds HTTP 429.
5. `fetch_klines` raises `Exception("Market API error 429: ...")`.
6. `signal_engine.run_once` catches per-symbol exception and calls `observability_logger.log_error({...event_type:error,module,symbol,error...})`.
7. Loop continues across symbols and next ticks.

## Effects
- Rapid repeated market retries continue by design (no backoff/circuit breaker at this layer).
- Error logging path is malformed for `event_type=error` shorthand (see schema defect trace).
- This drives high-volume entries in `error_events.jsonl` (mostly `observability_log_failed`).

## Telegram impact
- No active automatic error->Telegram notifier path is wired; therefore 429 storms do not notify operators through Telegram automatically.
