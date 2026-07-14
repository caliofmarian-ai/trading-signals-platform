# TWELVE_DATA_429_FAILURE_CONTRACT

## When Twelve Data returns HTTP 429
- Runtime status is marked `MARKET_DATA_LIMITED`.
- A canonical aggregated operator incident is raised on the first refusal.
- Rapid retry loops are stopped by a bounded backoff window.
- FSM/watchlist state is preserved.
- No signals are produced from missing market data.
- The remaining symbols in the current engine cycle are skipped once the rate limit is active.
- Automatic retry resumes after the backoff window.
- On the first successful provider response after the incident, the runtime returns to `READY` market-data state and emits a Telegram recovery notification.

## Not changed
- WIDE SCAN behavior.
- FOCUS MODE behavior.
- Scan gates or strategy thresholds.
- Healthy-provider request cadence.
