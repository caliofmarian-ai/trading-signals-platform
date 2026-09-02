# R-010 — Model Time Boundary Decision

Status: IMPLEMENTATION DECISION FOR REMEDIATION R-010
Issue: #116
Parent: #97
Base main commit: `bc761fdbf30f80fcc1abb2ad8c0e054e20ac34ae`

## Decision

R-010 does **not** replace the production Model Time derivation.

The runtime keeps its existing bounded integer-ceiling internal model window:

`model_expiry = ceil(clamp(t_needed_adjusted, expiry_minimum, expiry_maximum))`

This behavior creates a deterministic step at integer-minute boundaries. R-010 makes that step explicit and regression-tested, but does not promote it into a new canonical mathematical rule.

R-010 does make one bounded numerical-safety correction: values that are conceptually equal to the internal model window but differ only by machine floating-point noise are normalized as an exact fit (`model_time_reach_ratio = 1`, `time_to_buffer_ratio = 1`, `READY`). A real positive overrun remains `LATE`.

A future replacement of the `model_expiry` derivation requires an explicitly versioned canonical formula. It must not be introduced merely to make the curve visually smoother.

## Canonical authority reviewed

### CANONICAL_MASTER_INDEX_v2.0.0

The Master Index is the active authoritative canonical inventory after the 2026-09-01 promotion. It explicitly lists `TIME_MODEL_UNIFIED_CANON_v3.0.0.md` as **Active Canonical** and states that, where a lower-level document contains stale pre-promotion wording, the activation record, Master Index and canonical path classification determine current status.

Therefore R-010 treats Time Model v3 as the active time authority. The stale `PROPOSED / NOT ACTIVE` wording still present inside the v3 file is a documentation-governance defect owned by R-024; it does not demote the file after the executed promotion.

### TIME_MODEL_UNIFIED_CANON_v3.0.0

The active v3 Time Model establishes:

- Model Time as internal strategic time feasibility;
- `t_needed = buffer_distance / directional_effective_speed` for valid positive directional evidence;
- `t_needed_adjusted` as context-adjusted required time;
- `model_expiry` as the internal model horizon;
- `model_time_reach_ratio = t_needed_adjusted / model_expiry`;
- `time_to_buffer_ratio = model_expiry / t_needed_adjusted`;
- Execution Time as downstream and distinct from Model Time;
- fractional trader-facing OPEN_NOW expiry where precision requires it;
- no arbitrary trader-facing execution rounding.

The active v3 document does **not** define a fractional replacement formula for deriving `model_expiry` from `t_needed_adjusted`, and it does not authorize replacing the existing model-window behavior merely for smoothness.

### TIME_MODEL_UNIFIED_CANON_v2.0.0

v2 is superseded historical authority after the 2026-09-01 promotion. It was reviewed only as provenance because the runtime integer-ceiling behavior predates the promotion. It cannot override the active Master Index or v3 Time Model.

## Runtime evidence reviewed

`send/core/time_model.py` computes:

1. `t_needed = buffer_distance / directional_effective_speed`
2. `t_needed_adjusted = t_needed * trend_adjustment * structure_adjustment`
3. bounded integer-ceiling `model_expiry`
4. `model_time_reach_ratio = t_needed_adjusted / model_expiry`
5. `time_to_buffer_ratio = model_expiry / t_needed_adjusted`
6. exact-fit numerical normalization only when the two time values differ by machine-scale floating-point drift.

At an internal boundary around five minutes, the deterministic model-window behavior is:

- `4.999 -> model_expiry 5.0`
- `5.000 -> model_expiry 5.0`
- `5.001 -> model_expiry 6.0`

The reciprocal ratios therefore exhibit a step/sawtooth discontinuity at the integer boundary.

## Numerical boundary defect found by R-010

The first R-010 full-suite run exposed a separate floating-point defect at the configured maximum. A conceptually exact `15.0` minute requirement could be represented internally as a value microscopically above `15.0` and therefore be classified as `LATE` even though the model window was exactly 15.

R-010 fixes only that machine-precision equality problem.

The normalization tolerance is intentionally extremely small (`1e-12` relative and absolute). It is not a market tolerance, expiry tolerance, score tolerance, or calibration parameter. It only prevents representational noise from changing the semantic result of an exact mathematical equality.

A genuine overrun such as `15.001` remains above the configured maximum and remains `LATE`.

## Why R-010 does not simply remove `ceil()`

With the current available derivation, replacing the integer ceiling with only:

`model_expiry = clamp(t_needed_adjusted, expiry_minimum, expiry_maximum)`

would make `model_expiry == t_needed_adjusted` throughout almost the entire interior of the allowed range. That would force:

- `model_time_reach_ratio == 1`
- `time_to_buffer_ratio == 1`

for most otherwise valid opportunities.

Because Trade Physics consumes `time_to_buffer_ratio`, that would materially change strategic scoring semantics without an active canonical replacement model-window derivation. Such a change is not authorized by the v3 Time Model and is prohibited by the remediation discipline.

The correct R-010 action is therefore to expose and test the current boundary behavior while refusing to invent a replacement mathematical policy.

## Boundary decision

The integer-ceiling behavior is classified by R-010 as **existing bounded runtime compatibility behavior**, not as newly promoted canonical mathematics.

R-010 locks these rules:

1. Do not replace the Model Time derivation merely for smoothness.
2. Keep the current minute-boundary behavior observable and regression-tested until a versioned canonical replacement derivation exists.
3. Treat mathematical exact-fit as exact-fit despite machine floating-point noise.
4. Keep the configured maximum model window fail-closed: any real requirement above the maximum remains `LATE` and the model window is not extended.
5. Never convert internal Model Time rounding into trader-facing expiry authority.
6. Execution Time remains the only authority for external expiry, under its own explicit calibration contract.
7. Any future Model Time derivation change must review downstream Trade Physics because the T component consumes `time_to_buffer_ratio`.

## Regression evidence added

`tests/canonical/unit/test_r010_model_time_boundaries.py` proves:

- behavior immediately below, exactly at, and immediately above an integer-minute boundary;
- the sawtooth discontinuity is explicit rather than hidden;
- mathematical exact-fit at the configured maximum is not falsely degraded by floating-point representation noise;
- a real overrun above the configured maximum remains fail-closed as `LATE`;
- Model Time does not expose generic/external `expiry_minutes` or `open_now_expiry_minutes` fields.

## Out of scope

R-010 does not change:

- score thresholds;
- TPS formula or bands;
- SR hard feasibility;
- provider selection or market data;
- FINNHUB licensing controls;
- FSM lifecycle;
- Signal Engine scheduling;
- distribution semantics;
- broker execution.

## Follow-up ownership

- R-024 owns cleanup of stale active-file headers/status wording so lower-level documents visibly agree with the authoritative Master Index.
- Any future replacement of the current integer Model Time window requires a separately governed canonical derivation and full downstream Trade Physics/scoring impact review.
