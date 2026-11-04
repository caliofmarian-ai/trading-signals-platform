# Finnhub recovery evidence — 2026-11-04

## Purpose and authority

The existing Railway stream diagnostic emits FIRST_REAL_TICK only when the
total accepted tick count equals one. It therefore omits that event for an
initial multi-tick frame and provides no affirmative data-recovery evidence
after a later reconnect. A subscribe request cannot prove recovered prices.

This patch implements the existing active Master Index v2, Observability v3
and Observability Logging v3 evidence requirements. It changes only the
price-free stream diagnostic in `send/runtime/finnhub_market_data.py` and its
offline regressions. Transport, provider selection, candle construction,
freshness gates, strategy, calibration, distribution and research are unchanged.

## Intended behavior

Emit FIRST_REAL_TICK once for the first accepted trade frame, including a
multi-tick frame. On each later subscription, retain the last tick timestamp
as a recovery boundary. Emit REAL_TICK_RESUMED only after persistence of a
strictly newer quote that is within the configured freshness window. Ping,
wrong-symbol, duplicate, out-of-order, stale or future quotes do not prove
recovery. Each subscription can produce at most one recovery event; ordinary
ticks do not produce additional events. Distinct reconnect recoveries remain
visible even within the ordinary five-minute diagnostic throttle.

The diagnostic includes observation time, tick age and the configured freshness
limit, without prices, keys, URLs, messages or signal/account identities. These
events are state-change observations, not recurring heartbeats.

## Validation and release

Offline tests must reproduce the missing batch/reconnect events, exercise
multiple socket sessions, and check false-recovery exclusions and privacy.
Run focused feed tests and repository CI on the exact published tree. After
deployment, verify startup and actual real-tick evidence; offline fixtures do
not establish production recovery or strategy performance.

The eight new regressions failed before the correction. The combined focused
feed checks then passed (38 tests); full repository regression passed with
1,998 tests in 81.36 seconds. `git diff --check` is required before publication.
Exact-head CI and production verification are separate release requirements.

Pre-change source backup is immutable main commit
`1e83b3db6c7554328a01dbaa1e158f826527f9a2`. No persisted data/config migration
is required. Rollback is a reviewed revert through the existing main release
path; preserve all historical candles and research results.
