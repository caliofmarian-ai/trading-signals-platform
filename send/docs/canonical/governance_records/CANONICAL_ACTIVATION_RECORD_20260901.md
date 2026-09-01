# CANONICAL_ACTIVATION_RECORD_20260901

Status: EXECUTED CANONICAL PROMOTION RECORD
Date: 2026-09-01
Owner: BinaryBot / DROPi Signals
Program: staged execution + current-scope Trade Physics integration

## Promotion declaration

This record declares the atomic canonical promotion executed by the commit that contains it.

Effective in that commit:
- `CANONICAL_MASTER_INDEX_v2.0.0.md` is the sole authoritative Master Index.
- The 43 functional specifications listed as Active Canonical by that Master Index are active canonical authority.
- `CANONICAL_STRATEGY_STACK_v2.0.0.md` is the active strategy root manifest.
- `ADMIN_SURFACE_AND_CONTROL_PLANE_CANON_v2.0.1.md` is the active admin/control-plane root manifest.
- The two Trade Physics authorities, `TRADE_PHYSICS_MODEL_SPEC_v1.0.0.md` and `TRADE_PHYSICS_INTELLIGENCE_SPEC_v1.0.0.md`, are active current-scope canon.
- Replaced predecessors removed from `canonical/active` and preserved under `canonical/superseded` are historical only.
- `CANON_BATCH_EVALUATION_v3.0.0.md` is a governance/supporting record under `canonical/governance_records`, not a functional canonical specification.
- Intake Trade Physics source files remain provenance only and are not implementation authority.

## Status resolution rule

Canonical status after this promotion is determined by, in order:
1. this executed activation record;
2. `canonical/active/CANONICAL_MASTER_INDEX_v2.0.0.md`;
3. placement under `canonical/active`, `canonical/superseded`, `canonical/governance_records`, `canonical/proposed`, `intake`, or deprecated paths.

Any embedded pre-promotion phrase such as `PROPOSED`, `NOT ACTIVE`, `until promotion`, `predecessor remains active`, or a former `/canonical/proposed/` path inside a document promoted by this same commit is frozen provenance metadata from the review phase and MUST NOT be interpreted as current canonical status after this activation record takes effect.

Such stale metadata is a documentation-cleanup defect only; it does not restore authority to a superseded predecessor or negate the active status declared by the Master Index and active path.

## Runtime boundary

This promotion changes documentation authority only. It does NOT itself:
- change Python/runtime code;
- change `send/schema/event_schema.json`;
- enable Distribution publication;
- enable Telegram signal publication;
- enable broker execution;
- alter scan cadence.

Runtime changes remain blocked until a fresh canon-to-code audit against the newly active graph is complete.

PR #73 remains DO NOT MERGE until that audit determines whether it is corrected, superseded, or replaced.

## Active inventory result

Post-promotion target state:
- 43 functional active canonical authorities;
- 1 active Master Index;
- zero `CAN_BATCH_EVALUATION` governance records in `canonical/active`;
- all replaced predecessors preserved under `canonical/superseded`;
- Trade Physics active now, not future-state.
