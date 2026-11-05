# Completed M1 speed intervals — 2026-11-05

## Defect and authority

Baseline main: `336d624e2f1a24b616795f1fad96fbda8656939d`, tree
`aa6abc747aafb7f01884a4f0815b448789950fe1`.

The active Master Index is `CANONICAL_MASTER_INDEX_v2.0.0` (43 functional
authorities). `TRADE_PHYSICS_MODEL_SPEC_v1.0.0` §7.1 and
`TIME_MODEL_UNIFIED_CANON_v3.0.0` §10 require the most recent **20 completed M1
intervals**, represented by 21 chronological completed-bar closes, with weights
1..20. The implementation included the still-forming head bar, while
`candle_adapter.normalize` discarded the provider's `complete` flag.

An offline counterexample changed only the forming quote while preserving all
closed bars and BUY direction. The old directional speed changed from about
0.0000300000 to 0.0002204762. This is a software counterexample, not a measured
market return. It corrects the assumption in the preceding M1 history report
that 21 total live rows were enough when one row is still forming.

## Correction

- Preserve explicit boolean `complete` metadata; reject malformed flags rather
  than coercing strings or numbers into closure evidence.
- Select exactly 21 closed M1 bars for both gross and directional speed. Only
  the newest forming bar may be excluded. Do not cross gaps, skip unfinished
  historical bars, replace missing intervals, or synthesize data.
- Pass the actual cycle timestamp through Signal Engine → Strategy → Market
  Model. Check interval end times against it. A premature `complete=true` or
  future head fails closed. Historical read-only probes use their historical
  cutoff, not today's clock.
- Legacy pure callers with neither observation time nor closure flags retain
  their already-closed-input contract, explicitly identified in provenance.
  The live Signal Engine always supplies observation time.
- Default Finnhub live history becomes M1=22 (21 closed plus forming), M5=201.
  All available contiguous real history remains available; the M5 EMA history
  requirement is not imposed on M1. RSI history validation remains active.
- Retain weights 1..20, price-per-minute units, latest real quote for current
  context, RSI/noise calculations, strategy thresholds, freshness guard,
  FSM, execution calibration and distribution rules.
- Add completed-window provenance to decision event market context. Emit
  `TSP_M1_COMPLETED_SPEED_EVIDENCE` once per symbol per five minutes, starting
  with the first evaluation. It contains counts, endpoint timestamps,
  observation time and derivation version; no prices, scores, identifiers for
  private decisions, or trade recommendations.

## Validation and release acceptance

Offline regressions cover forming-quote invariance at fixed direction, 21 raw
rows with a forming head being insufficient, 21 already-closed rows being
sufficient, provider flags and clock-derived closure, exact close boundaries,
future/unfinished/malformed evidence, a missing final endpoint, exact BUY/SELL
weights, clock propagation from `run_once`, status minima and bounded marker
output. Existing execution-lineage fixtures include the new provenance.

The final full-suite result, exact PR head/tree, CI run and installed deployment
are recorded in the PR release evidence. Release acceptance requires green
Required Repository CI on that exact head, the corresponding main deployment
SUCCESS/Online 1/1, and a prospective marker showing 21 completed candles / 20
completed intervals with `forming_candle_included=false`.

## Research boundaries

The completed 20261104T160500Z timebox and deadline 1793815500 remain frozen.
There is no extension, new study or backfill. Software tests and closure
provenance establish correctness only. They do not establish trading efficacy,
profit, broker quote equivalence or execution calibration. The permitted demo,
calibration and broker comparison requirements in #208/#217 remain separate.
