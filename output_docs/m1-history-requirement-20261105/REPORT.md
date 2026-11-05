# Finnhub M1 history requirement — 2026-11-05

## Requested behavior and authority

The Owner explicitly requested an interactive implementation change: use the
available M1 history and remove the excessive history prerequisite. This is a
code change requested separately from the read-only scheduled monitor.

Baseline main: `7784b0104541b6881d8c06ccd10d2ca81e5d43c1`, tree
`e0dde50e741e1e12a2616332139bf816c3490617`. Installed baseline deployment:
`ab2b1a2e-538e-432d-bc8c-da11f8c74e15` (SUCCESS, Online 1/1).

The active Master Index is `CANONICAL_MASTER_INDEX_v2.0.0.md` (43 functional
specifications). ALGO v3 and Time Model v3 require sufficient real evidence,
including the existing 20-interval directional-speed calculation. They do not
require the M5 EMA200 history length to be imposed on M1. The unchanged
`core.market_model.evaluate_market` already validates M1 against
`max(21, rsi_period + 1)` and M5 against `max(15, ema_slow + 1)`.

With the current RSI14 and EMA200 parameters, 21 real M1 bars and 201 real M5
bars satisfy those count requirements. The latest baseline sample already had
430 contiguous M1 bars; this correction prevents an unnecessary future recovery
wait. It does not claim that M1 is currently blocked.

## Change and compatibility

- Finnhub defaults to M1=21 and M5=201. `FINNHUB_MIN_M1_CANDLES` governs M1;
  the existing `FINNHUB_MIN_CANDLES` environment setting now governs M5 only.
  An existing production value of 201 therefore cannot reapply the M5 gate to M1.
- The explicit Python constructor `minimum_candles` override still applies to
  both timeframes for existing offline callers; `minimum_m1_candles` can override
  M1 independently. Accepted configuration range remains 2..500, and the Market
  Model independently rejects evidence below its actual indicator requirements.
- Return all currently available contiguous real M1 bars, not just the minimum.
  A gap inside the required window, stale quote, invalid OHLC, or absence of a
  real tick still blocks. Stored candles are neither deleted nor synthesized.
- Feed health, Railway stream evidence, runtime snapshots and status rendering
  expose per-timeframe minima and contiguous counts. `required_candles_each` is
  null when the two minima differ; the explicit mapping is authoritative.
  The legacy health scalar is retained as the M5 compatibility value.
- The read-only historical probe uses the same split requirements and respects
  larger configured RSI/EMA needs, completed candles and no-lookahead selection.
- A provider without the split mapping overwrites it with its own scalar minima,
  preventing stale Finnhub M1 requirements after an explicit provider switch.

Scope: Finnhub history admission, corresponding read-only diagnostics/status,
environment example, offline probe, tests and this report. No production
variables, indicator formulas/periods, strategy score thresholds, FSM transitions,
calibration, distribution, broker execution or service identities are changed.

## Validation

Initial focused regression: 25 tests passed in 0.37 seconds. The regression
includes Market Model and pure Binary Strategy V2 calculations with exactly 21
real M1 bars and 201 real M5 bars.
Cases cover insufficient M1/M5 separately, use of a longer available segment,
gap rejection, quote freshness, larger RSI requirements, configuration
compatibility, marker truth and runtime/status propagation.

Full repository regression: 2,021 tests passed in 48.29 seconds. Source
compilation and `git diff --check` passed. Exact-head Required Repository CI and
production acceptance are pending at publication; their final results belong in
PR release evidence. These are software checks, not strategy profitability evidence.

## Release and acceptance

Target only project `54752c90-3929-4854-9b50-049b5c63ab98`, production
`c8e55f1a-7518-4e7b-ae38-bad46b0a4171`, existing service
`c2c41294-4eca-4092-8cdf-94ba57511c6e`. Release the tested tree by PR squash
only after Required Repository CI succeeds on the exact head. Verify the
corresponding main deployment reaches SUCCESS and Online 1/1, then check a real
stream marker with `required_candles_by_timeframe={M1:21,M5:201}` and a fresh tick.
Do not force a disconnect to manufacture a short-history production example.

The expired research run remains frozen: SHADOW_GATE_TIMEBOX_V1,
deadline 1793815500, TIMEBOX_COMPLETE, 2,452 evaluations, no eligible observations.
No restart extends it or inserts post-deadline evaluations. Calibration and the
permitted exact broker-demo comparison remain separate requirements (#208/#217).

Rollback, if necessary, is a source revert through the same CI/main release path;
retain all existing candle, FSM, outcome and research state. Do not redeploy an
older image or reset the persistent volume.
