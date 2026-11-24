# V3_DURATION_PAIR_PHYSICAL_COMPONENTS_DIAGNOSTIC_v1.0.0

Status: ACTIVE RESEARCH DIAGNOSTIC — 2026-11-24

## Purpose

This diagnostic records the physical numeric inputs at the first genuinely
accepted V3 CONFIRM and at its matching accepted OPEN_NOW. It supports the
open investigation in issue #311 by separating changes in directional speed,
available structural distance, buffer distance and the derived movement-time
adjustment. It does not change the strategy or the exact duration frozen at
CONFIRM.

## Capture and identity

- Capture the first accepted CONFIRM for a new PHYSICAL_ONLY_V3 opportunity.
- Preserve that snapshot across retries and restart; do not replace it with a
  later CONFIRM evaluation.
- Capture the matching OPEN snapshot only when the same opportunity is
  internally accepted as OPEN_NOW and the existing PRE/CONFIRM lifecycle gates
  are satisfied.
- Join the two snapshots through the existing privacy-safe opportunity digest
  and the existing immutable study record.
- Legacy records without a CONFIRM snapshot remain incomplete. No historical
  backfill, reconstructed CONFIRM or synthetic OPEN is permitted.

## Frozen components

V3_PHYSICAL_COMPONENT_SNAPSHOT_V1 contains only derived measurements and
canonical state labels:

- Directional and gross movement: directional_effective_speed,
  weighted_gross_speed, flow_efficiency.
- Geometry: buffer_distance, available_distance, corridor_width,
  space_to_buffer_ratio, trade_space_margin_atr.
- Time derivation: t_needed_seconds, t_needed_adjusted_seconds,
  model_expiry_seconds, model_time_reach_ratio,
  time_to_buffer_ratio, adjustment_multiplier.
- Supporting physical context: atr_speed_reference,
  directional_speed_ratio, movement_stress.
- State context: trend, volatility, noise, structure, time and Trade Physics
  readiness states.

The snapshot deliberately excludes raw prices, quotes, support/resistance
levels, signal IDs, decision IDs, destination IDs, personal data and every
score/TPS field. Each snapshot is schema-validated and SHA-256 hashed. The
canonical time identity residual is recorded as the difference between the
frozen t_needed and buffer_distance / directional_effective_speed; it is not
used as a gate or forced to zero. The adjustment multiplier is checked against
adjusted/unaltered movement time. Because these fields are optional
research metadata, an invalid or orphaned component snapshot is discarded
without blocking the canonical FSM or study-delivery path; the pair report
then records the component snapshot as missing.

## Pair reconciliation

TSP_PHYSICAL_V3_DURATION_PAIR_DIAGNOSTICS reports, per pair and in bounded
detail chunks:

- component availability (COMPLETE, CONFIRM_MISSING, OPEN_MISSING or
  BOTH_MISSING);
- CONFIRM and OPEN numeric component snapshots;
- absolute and percentage changes in directional speed, buffer distance,
  available distance, required/adjusted movement time, adjustment multiplier,
  flow efficiency and space-to-buffer ratio;
- the already-frozen CONFIRM duration, OPEN feasibility, entry-delivery reason,
  elapsed lifecycle timing and the existing opportunity-trace join.

The report remains research-only. Deltas describe observed changes between
snapshots; they do not by themselves establish causality. A source-market
change, changed geometry or changed adjustment context must be interpreted
from the paired evidence, not inferred from aggregate counts.

## Invariants

- V3 remains scoreless: no score, ranking, replacement score or TPS is created.
- PRE → CONFIRM → OPEN_NOW order, the minimum PRE lead, exact CONFIRM duration,
  current OPEN physical revalidation and fail-closed infeasibility remain
  unchanged.
- The diagnostic does not relax a gate, extend duration, change buffer
  semantics, select a pressure bias, approve calibration or activate parameters.
- Study protocol/storage protocol, outcome labels, quote windows, training and
  untouched holdout boundaries are unchanged. The component snapshot is
  additive metadata on new opportunities only.
- No canonical OPEN publication, phone-display claim, broker action, Pocket
  Option integration or execution authority is created.
- Finnhub EUR/USD, Shadow Mode, broker-off, the existing service, environment
  and /data volume remain unchanged.
