# R-010 — Model Time Boundary Decision

Status: IMPLEMENTATION DECISION FOR REMEDIATION R-010
Issue: #116
Parent: #97
Base main commit: `bc761fdbf30f80fcc1abb2ad8c0e054e20ac34ae`

## Decision

R-010 does **not** change the production Model Time formula.

The current runtime uses an integer-ceiling compatibility behavior for the bounded internal model window:

`model_expiry = ceil(clamp(t_needed_adjusted, expiry_minimum, expiry_maximum))`

This behavior creates a deterministic step at integer-minute boundaries. R-010 makes that step explicit and regression-tested, but does not promote it into a new canonical mathematical rule.

A future change to the `model_expiry` derivation requires an explicitly versioned canonical formula. It must not be introduced merely to make the curve visually smoother.

## Canonical evidence reviewed

### TIME_MODEL_UNIFIED_CANON_v2.0.0

The document self-identifies as `Canonical Unified` and as the root canonical source for the time domain. It defines:

- Model Time as internal strategy truth;
- `t_needed_adjusted` as the basis from which `model_expiry` is derived;
- `model_time_reach_ratio = t_needed_adjusted / model_expiry` conceptually;
- Execution Time as downstream and distinct from Model Time;
- fractional `open_now_expiry_minutes` as valid and not subject to arbitrary rounding.

It does not prescribe a replacement fractional `model_expiry` formula that can safely replace the current runtime behavior.

### TIME_MODEL_UNIFIED_CANON_v3.0.0

The repository currently stores this file under an `active` path, but its own header says `PROPOSED COMPLETE SUCCESSOR — NOT ACTIVE CANONICAL` and states that v2 remains the sole active time authority until explicit promotion.

R-010 therefore does not use v3 to authorize a production formula change. The path/header governance contradiction remains owned by R-024.

The proposed v3 text is nevertheless consistent with the cross-layer safety boundary already implemented by R-001: trader-facing execution expiry is downstream, fractional values are allowed, and arbitrary execution-time rounding is not canonical.

## Runtime evidence reviewed

`send/core/time_model.py` currently computes:

1. `t_needed = buffer_distance / directional_effective_speed`
2. `t_needed_adjusted = t_needed * trend_adjustment * structure_adjustment`
3. bounded integer-ceiling `model_expiry`
4. `model_time_reach_ratio = t_needed_adjusted / model_expiry`
5. `time_to_buffer_ratio = model_expiry / t_needed_adjusted`

At an internal boundary around five minutes, the current deterministic behavior is:

- `4.999 -> model_expiry 5.0`
- `5.000 -> model_expiry 5.0`
- `5.001 -> model_expiry 6.0`

The reciprocal ratios therefore exhibit a step/sawtooth discontinuity at the integer boundary.

## Why R-010 does not simply remove `ceil()`

With the current available formula, replacing the integer ceiling with only:

`model_expiry = clamp(t_needed_adjusted, expiry_minimum, expiry_maximum)`

would make `model_expiry == t_needed_adjusted` throughout almost the entire interior of the allowed range. That would force:

- `model_time_reach_ratio == 1`
- `time_to_buffer_ratio == 1`

for most otherwise valid opportunities.

Because Trade Physics consumes `time_to_buffer_ratio`, that would materially change strategic scoring semantics without a canonically defined replacement model-window formula. Such a change is prohibited by the remediation discipline.

## Boundary decision

The integer-ceiling behavior is therefore classified by R-010 as **existing bounded runtime compatibility behavior**, not as newly promoted canonical mathematics.

R-010 locks these rules:

1. Do not change the Model Time formula merely for smoothness.
2. Keep the current minute-boundary behavior observable and regression-tested until a versioned canonical replacement exists.
3. Keep the configured maximum model window fail-closed: required time above the maximum remains `LATE` and the model window is not extended.
4. Never convert this internal rounding behavior into trader-facing expiry authority.
5. Execution Time remains the only authority for external expiry, under its own explicit calibration contract.

## Regression evidence added

`tests/canonical/unit/test_r010_model_time_boundaries.py` proves:

- behavior immediately below, exactly at, and immediately above an integer-minute boundary;
- the sawtooth discontinuity is explicit rather than hidden;
- the configured maximum is not extended to rescue an infeasible setup;
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

- R-024 owns the active-path/header canonical-status contradiction.
- Any future replacement of the current integer Model Time window requires a separately governed canonical derivation and full downstream Trade Physics/scoring impact review.
