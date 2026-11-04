# SHADOW_MODEL_TIME_RESEARCH_V1

Status: prospective observational experiment; non-active-canonical research record. Related: #208 and #217. No production strategy or execution-calibration authority is added.

## Question and baseline

Can the unchanged Binary Strategy V2's actual, FSM-accepted OPEN_NOW opportunities be followed prospectively on the same Finnhub EUR/USD stream at their **uncalibrated Model Time** horizon, with explicit missing observations?

This establishes instrumentation and a descriptive baseline for future expiry research. It does not establish the profitability of a broker contract, approve an ExecutionCalibration, or authorize signal distribution. The current strategy, score thresholds, physics formulas and parameter files are the unchanged baseline. No alternative model is fitted or auto-promoted.

## Cohort and point-in-time features

Only exact-stage accepted OPEN_NOW with a canonical non-compatibility DecisionObject, READY Model Time, valid structure, feasible time, READY Trade Physics, no hard blockers and matched decision/FSM lineage is eligible. PRE, CONFIRM, rejected or duplicate stage releases are not enrolled. One protocol/provider/signal identity is enrolled once, including across later candles and restarts; this avoids repeatedly counting a single opportunity. Separate opportunities may still overlap and be correlated.

The complete DecisionObject snapshot and FSM transition reference are saved before observing any outcome. No future quote or checkpoint changes those features. Samples are prospective; no backfill, historical candle endpoint, synthetic tick, cross-provider substitution or user vote is accepted. The raw underlying prices remain private under the existing runtime data root.

## Observation and target

- The entry reference is the first fresh same-provider real stream observation at or after registration, within ten seconds. The decision-time candle price is not silently substituted for that later observation.
- The target is actual observed entry time plus the snapshot's Model Time in minutes. This is deliberately **not** the trader-facing calibrated Execution Time.
- The expiry reference is the first observed real tick at or after that target, no more than two seconds late; the tick must also be no more than two seconds old when processed. Exact observation timestamps and prices are retained. These windows are instrumentation guardrails, not changes to trading thresholds.
- For BUY, a higher observed expiry price is a hypothetical WIN; a lower price is LOSS. SELL reverses that comparison. Exact equality is DRAW.
- Missing/stale/future/malformed/cross-provider evidence, a changed provider, or a checkpoint missed during restart is UNKNOWN. A late recovery never rewrites a final UNKNOWN. No label is inferred from an OHLC range.

## Persistence and recovery

Atomic per-opportunity JSON records under `analytics/shadow_model_time_research/records/` own this experiment's evidence. Features and observed samples are write-once; finalized records are immutable. The bounded active index is rebuilt from those records after restart, including recovery from a crash between record/index writes. Storage errors fail closed and do not block the canonical execution path. No existing market telemetry, outcome, audit or price history is deleted or overwritten.

The active capacity is 256 and the bounded research inventory is 10,000 records. Exceeding a bound or encountering malformed/symlinked evidence stops research collection/reporting explicitly; it does not authorize dropping old evidence or changing the strategy.

## Interpretation and access

Every record and summary is labeled HYPOTHETICAL_RESEARCH / NOT_PUBLISHED, with `authoritative_for_strategy_performance=false`, `broker_executed=false` and `execution_calibration_proven=false`. WIN/LOSS/DRAW/UNKNOWN, decisive sample size, pending count and a separately named hypothetical win rate are exposed in the runtime audit. The rate excludes draws and unknowns, whose counts remain visible. Price/identity-free summaries are emitted only at startup/research state changes for authenticated operational inspection.

These are not published-trade results, broker settlements, causal conversion rates, independent-sample confidence guarantees or P&L. Spread, manual latency, payout, commission, contract type and broker quote equivalence remain unverified. Regime/session coverage, missing-data rates and chronological validation must be reviewed before drawing efficacy conclusions. Official MARKET_TRUTH consumers and automatic evolution remain unchanged.

## Activation and acceptance

The collector defaults OFF. It runs only when `SHADOW_MODEL_TIME_RESEARCH_ENABLED=true`, `SHADOW_MODE=true` and broker execution is disabled, and it accepts Finnhub EUR/USD only. It reads the already ingested stream without extra paid API requests or any Telegram signal transmission. The existing Finnhub distribution gate is preserved. Enabling this experiment grants no commercial/redistribution rights.

Acceptance requires offline direction/label, missing/future/stale/provider-change, duplicate, restart, atomic-index recovery, immutable-feature, truth-separation and worker-isolation regressions; exact-head CI; a successful production deployment; and observed runtime enabled/collection status. A zero initial cohort is valid and must not be represented as completed strategy validation. Disabling the flag stops further observation without changing canonical production controls.
