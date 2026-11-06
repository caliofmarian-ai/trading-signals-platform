# V3_SCORELESS_OWNER_AMENDMENT_v1.0.0

Status: ACTIVE OWNER AMENDMENT — 2026-11-06
Policy: `PHYSICAL_ONLY_V3`
Runtime strategy: `core.strategy_v3`, version `3.0.0`

The Owner explicitly requires V3 decisions without any score. This amendment
overrides classical-score bands, TPS ranking, weights, severity levels and
score-based focus replacement in the existing ALGO, Trade Physics, DecisionObject,
parameter-control and FSM domains. It does not add another functional domain to
the Master Index's inventory of 43. Prior scored observations remain historical.

## Physical eligibility

Every actionable stage must independently pass the existing evidence gates:

1. Valid, fresh, contiguous real M1/M5 history and coherent evaluation identity.
2. Active market: the existing normalized M1-range/M5-ATR14 activity gate (0.20).
3. Stable market under the existing wick, range and jump filters.
4. Confirmed M5 swing support/resistance corridor and valid directional structure.
5. Available directional distance `D >= B`, using the canonical frozen buffer.
6. Positive directional effective speed and complete real flow/ATR evidence.
7. Feasible Model Time: `t_needed = B / directional_speed`, adjusted by the
   existing trend and structure factors; the existing model expiry limits apply.
   Clamping must never turn an infeasible adjusted time into a feasible setup.

No weighted aggregate, classical score, TPS, S/T/P/V component, RSI score cutoff,
interpretation band, or score threshold participates in calculation or selection.
Physical measurements retain their units and meaning; ratios are measurements,
not points in an aggregate. No new market cutoffs are introduced by this change.

## Ordered lifecycle

- PRE identifies the first eligible setup and establishes a new V3 opportunity ID.
- CONFIRM requires a subsequent complete eligible evaluation of the same ID and
  direction, with a previously accepted PRE.
- OPEN_NOW requires an accepted CONFIRM, a subsequent complete eligible evaluation,
  identity/direction continuity and at least 30 seconds since PRE. For Owner
  publication, the real first successful PRE API receipt also anchors the minimum
  lead and a real CONFIRM receipt is required. Internal acceptance is not delivery.
- Failed physical conditions reject the opportunity through the existing FSM.
  Cooldown, focus TTL and capacity remain operational constraints. Full focus
  capacity waits; no score ranks or replaces another symbol.
- Persisted V2 opportunities cannot be treated as V3 PRE/CONFIRM evidence.

## Execution Time and calibration

Model Time remains distinct from governed Execution Time. Removing scores does
not fabricate an approved expiry. Missing, expired, mismatched or unapproved
calibration still blocks OPEN_NOW publication with `EXECUTION_TIME_UNAVAILABLE`.
PRE and CONFIRM can be published with explicitly unavailable execution timing.

Prospective research uses one predeclared `PHYSICAL_ONLY_V3` policy and separate
storage: `analytics/physical_v3_expiry_calibration/state.json`. A complete internally
accepted chain admits at most one quote experiment per opportunity. It does not
claim Telegram delivery, a broker trade or a realized trading result.

Existing paired expiry horizons, entry/expiry quote tolerances, frozen-buffer
measurements, chronological nonoverlapping train/untouched holdout split and
data-quality/efficacy requirements are preserved. There is one policy, so the
old correction across 21 score levels is inapplicable. Candidate selection uses
training only; the selected candidate's untouched holdout uses a 95% Wilson bound.
Missing quotes remain UNKNOWN. Synthetic fixtures never approve calibration.
No historical buffer or physical chain is backfilled. No automatic artifact
activation is introduced.

## Parameters, contracts and history

Validated complete V2 parameters migrate once, with a byte-identical hashed backup
before atomic replacement. All physical parameter values are preserved. V3 removes
`score_thresholds`, the `strategy_v2` parameter block, and `rsi_call`/`rsi_put`, and
requires `market_model` plus the explicit policy/version. Unknown or scoring fields
are rejected. Invalid input blocks evaluation; no scored fallback is permitted.

The internal typed compatibility container carries `None` for total/normalization
and empty component maps in physical mode. It never contains a synthetic zero or
100. Serialized V3 decisions and signal candidates omit score/TPS fields. Legacy
numeric contracts stay strict for historical readers and replay. The V2 module and
its seed fixture remain exclusively for historical compatibility and migration.

The old 0–20 severity and cadence experiments admit no new V3 observations.
Their persisted ledgers are preserved and pending quote observations may finish.
Owner timing monitoring uses a separate V3 path; old parameter cohorts are not
silently continued under the new policy. Active views show physical evidence.

## Rollback

Rollback requires the previous code revision and restoration of the exact saved
V2 parameter backup. An old runtime must not interpret a V3 bundle or fit. Preserve
both observation cohorts and all genuine publication receipts during rollback.
