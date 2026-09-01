# CANONICAL_ATOMIC_ACTIVE_PROMOTION_EXECUTION_MANIFEST_20260901

Status: EXECUTION MANIFEST — PROMOTION BRANCH ONLY — NOT ACTIVE CANONICAL
Date: 2026-09-01
Branch: `canonical/atomic-active-promotion-trade-physics-execution`
Base main SHA: `f7d90211acd07d7e85a5745bc264d553363d3ddb`

## Purpose

Define the exact atomic filesystem/status transition for the staged-execution + current-scope Trade Physics canonical promotion. No runtime/Python or `send/schema/event_schema.json` changes are authorized by this manifest.

## Atomic invariants
- Exactly 43 functional canonical authorities must remain in `send/docs/canonical/active/` after promotion.
- `CANONICAL_MASTER_INDEX_v2.0.0.md` becomes the sole active master index but is not counted in the 43 functional authorities.
- Every predecessor replaced by this program must leave `canonical/active` in the same atomic commit and be preserved under `canonical/superseded/`.
- Every successor copied from `canonical/proposed` into `canonical/active` must have internal status/path metadata rewritten from PROPOSED to ACTIVE.
- Historical/supersession prose may name predecessors; normative current-authority links must name final successor versions.
- The two new Trade Physics authorities have no predecessor.
- `CANON_BATCH_EVALUATION` is a governance record, not a functional canonical specification; v2 must leave `canonical/active`, and v3 must live under `canonical/governance_records/`.
- Intake source documents remain non-authoritative source history after absorption; they are not promoted into `canonical/active`.
- PR #73 remains DO NOT MERGE until promotion and post-promotion code re-audit complete.

## Functional authority transition matrix

| Predecessor active | Final active successor | Action |
|---|---|---|
| `CANONICAL_STRATEGY_STACK_v1.0.0.md` | `CANONICAL_STRATEGY_STACK_v2.0.0.md` | supersede + activate |
| `ALGO_SPEC_v2.0.0.md` | `ALGO_SPEC_v3.0.0.md` | supersede + activate |
| `SR_CORRIDOR_ENGINE_SPEC_v2.0.0.md` | `SR_CORRIDOR_ENGINE_SPEC_v3.0.0.md` | supersede + activate |
| `TIME_MODEL_UNIFIED_CANON_v2.0.0.md` | `TIME_MODEL_UNIFIED_CANON_v3.0.0.md` | supersede + activate |
| — NEW DOMAIN — | `TRADE_PHYSICS_MODEL_SPEC_v1.0.0.md` | activate new authority |
| `DECISION_OBJECT_CANONICAL_SPEC_v1.0.0.md` | `DECISION_OBJECT_CANONICAL_SPEC_v2.0.0.md` | supersede + activate |
| `FSM_DECISION_ENGINE_SPEC_v1.0.0.md` | `FSM_DECISION_ENGINE_SPEC_v2.0.0.md` | supersede + activate |
| `SIGNAL_ENGINE_EXECUTION_SPEC_v2.0.0.md` | `SIGNAL_ENGINE_EXECUTION_SPEC_v3.0.0.md` | supersede + activate |
| `RISK_MODEL_v2.0.0.md` | `RISK_MODEL_v3.0.0.md` | supersede + activate |
| `OBSERVABILITY_SPEC_v2.0.0.md` | `OBSERVABILITY_SPEC_v3.0.0.md` | supersede + activate |
| `OBSERVABILITY_LOGGING_SPEC_v2.0.0.md` | `OBSERVABILITY_LOGGING_SPEC_v3.0.0.md` | supersede + activate |
| `EVENT_SCHEMA_SPEC_v2.0.0.md` | `EVENT_SCHEMA_SPEC_v3.0.0.md` | supersede + activate |
| `DECISION_AUDIT_SPEC_v2.0.0.md` | `DECISION_AUDIT_SPEC_v3.0.0.md` | supersede + activate |
| `TRADE_TEMPORAL_TELEMETRY_SPEC_v2.0.0.md` | `TRADE_TEMPORAL_TELEMETRY_SPEC_v3.0.0.md` | supersede + activate |
| `OUTCOME_TRACKING_SPEC_v2.0.0.md` | `OUTCOME_TRACKING_SPEC_v3.0.0.md` | supersede + activate |
| `PERFORMANCE_ANALYTICS_SPEC_v2.0.0.md` | `PERFORMANCE_ANALYTICS_SPEC_v3.0.0.md` | supersede + activate |
| `RESEARCH_AND_LEARNING_FRAMEWORK_SPEC_v2.0.0.md` | `RESEARCH_AND_LEARNING_FRAMEWORK_SPEC_v3.0.0.md` | supersede + activate |
| — NEW DOMAIN — | `TRADE_PHYSICS_INTELLIGENCE_SPEC_v1.0.0.md` | activate new authority |
| `STRATEGY_INTELLIGENCE_SYSTEM_v2.0.0.md` | `STRATEGY_INTELLIGENCE_SYSTEM_v3.0.0.md` | supersede + activate |
| `AUTONOMOUS_STRATEGY_EVOLUTION_SYSTEM_v2.0.0.md` | `AUTONOMOUS_STRATEGY_EVOLUTION_SYSTEM_v3.0.0.md` | supersede + activate |
| `STRATEGY_PARAMETER_CONTROL_SPEC_v2.0.0.md` | `STRATEGY_PARAMETER_CONTROL_SPEC_v3.0.0.md` | supersede + activate |
| `MODULE_INTERFACE_SPEC_v2.0.0.md` | `MODULE_INTERFACE_SPEC_v3.0.0.md` | supersede + activate |
| `SYSTEM_ARCHITECTURE_MAP_v2.0.0.md` | `SYSTEM_ARCHITECTURE_MAP_v3.0.0.md` | supersede + activate |
| `SYSTEM_INVARIANTS_v2.0.0.md` | `SYSTEM_INVARIANTS_v3.0.0.md` | supersede + activate |
| `TEST_PLAN_v2.0.0.md` | `TEST_PLAN_v3.0.0.md` | supersede + activate |
| `COMMUNITY_FEEDBACK_AND_PRIVACY_SPEC_v2.0.0.md` | `COMMUNITY_FEEDBACK_AND_PRIVACY_SPEC_v3.0.0.md` | supersede + activate |
| `ADMIN_SURFACE_AND_CONTROL_PLANE_CANON_v2.0.0.md` | `ADMIN_SURFACE_AND_CONTROL_PLANE_CANON_v2.0.1.md` | supersede + activate |
| `ADMIN_CONTROL_SPEC_v2.0.0.md` | `ADMIN_CONTROL_SPEC_v2.0.1.md` | supersede + activate |
| `ADMIN_OPERATIONS_SPEC_v2.0.0.md` | `ADMIN_OPERATIONS_SPEC_v2.0.1.md` | supersede + activate |
| `ADMIN_TREE_MAP_v2.0.0.md` | `ADMIN_TREE_MAP_v2.0.1.md` | supersede + activate |
| `CONTROL_PANEL_HIERARCHY_AND_INTELLIGENCE_SPEC_v2.0.0.md` | `CONTROL_PANEL_HIERARCHY_AND_INTELLIGENCE_SPEC_v2.0.1.md` | supersede + activate |
| `ROLE_AND_PERMISSION_MATRIX_SPEC_v2.0.0.md` | `ROLE_AND_PERMISSION_MATRIX_SPEC_v2.0.1.md` | supersede + activate |
| `SIGNAL_DISTRIBUTION_ARCHITECTURE_v2.0.0.md` | `SIGNAL_DISTRIBUTION_ARCHITECTURE_v2.0.1.md` | supersede + activate |
| `SIGNAL_DISTRIBUTION_SPEC_v2.0.0.md` | `SIGNAL_DISTRIBUTION_SPEC_v2.0.1.md` | supersede + activate |
| `CHANNEL_CONFIG_SPEC_v2.0.0.md` | `CHANNEL_CONFIG_SPEC_v2.0.1.md` | supersede + activate |
| `TELEGRAM_UX_v2.0.0.md` | `TELEGRAM_UX_v2.0.1.md` | supersede + activate |
| `AFFILIATE_SIGNAL_DISTRIBUTION_MODEL_v2.0.0.md` | `AFFILIATE_SIGNAL_DISTRIBUTION_MODEL_v2.0.1.md` | supersede + activate |
| `SIGNAL_ECONOMICS_AND_MONETIZATION_MODEL_v2.0.0.md` | `SIGNAL_ECONOMICS_AND_MONETIZATION_MODEL_v2.0.1.md` | supersede + activate |
| `FAILURE_RECOVERY_SPEC_v2.0.0.md` | `FAILURE_RECOVERY_SPEC_v2.0.1.md` | supersede + activate |
| `DEPLOYMENT_PROTOCOL_v2.0.0.md` | `DEPLOYMENT_PROTOCOL_v2.0.1.md` | supersede + activate |
| `SECURITY_MODEL_v2.0.0.md` | `SECURITY_MODEL_v2.0.1.md` | supersede + activate |
| `GOVERNANCE_AND_CHANGE_CONTROL_v2.0.0.md` | `GOVERNANCE_AND_CHANGE_CONTROL_v2.0.1.md` | supersede + activate |
| `HUMAN_COMPREHENSION_AND_SELF_EXPLAINING_CONTROL_SURFACE_CANON_v1.0.0.md` | `HUMAN_COMPREHENSION_AND_SELF_EXPLAINING_CONTROL_SURFACE_CANON_v1.0.1.md` | supersede + activate |

## Master Index transition

| Predecessor active | Final active successor | Action |
|---|---|---|
| `CANONICAL_MASTER_INDEX_v1.0.0.md` | `CANONICAL_MASTER_INDEX_v2.0.0.md` | supersede + activate |

## Supporting governance record correction

| Current | Final | Action |
|---|---|---|
| `canonical/active/CANON_BATCH_EVALUATION_v2.0.0.md` | `canonical/superseded/CANON_BATCH_EVALUATION_v2.0.0.md` | remove misclassified governance record from active + preserve history |
| `canonical/proposed/CANON_BATCH_EVALUATION_v3.0.0.md` | `canonical/governance_records/CANON_BATCH_EVALUATION_v3.0.0.md` | promote as supporting governance record, NOT functional active canon |

## Required metadata rewrite for every promoted functional successor and Master Index

Before placement in `canonical/active`, each successor must be made self-consistent:
- top-level Status must say ACTIVE CANONICAL (or domain-equivalent active status), never PROPOSED / NOT ACTIVE;
- Path / Canonical Path must point to `send/docs/canonical/active/<filename>`;
- promotion-gate wording must be converted to post-promotion wording where it would otherwise say the predecessor remains active;
- Supersession Intent may remain only as historical provenance and must not imply the predecessor is still authoritative;
- Linked/Depends-on references must use final active successor filenames.

## Predecessor preservation rule

Each replaced active predecessor is copied byte-for-byte into `send/docs/canonical/superseded/<same filename>` before its active-path entry is removed. Existing superseded files remain untouched unless an exact filename collision is detected; any collision is a hard promotion blocker.

## Proposed-source cleanup

After a successor is activated, its promoted source file under `canonical/proposed/` must not remain as a second pseudo-current authority. Preferred action: remove the promoted successor from `canonical/proposed/` in the same commit. Unrelated historical/proposed files remain untouched.

## Post-commit validation
- `canonical/active` contains exactly 43 functional authorities plus the active Master Index, and no `CANON_BATCH_EVALUATION` governance record.
- Every final active filename listed by Master Index v2 exists.
- No predecessor scheduled for supersession remains in `canonical/active`.
- Every scheduled predecessor exists in `canonical/superseded`.
- `canonical/governance_records/CANON_BATCH_EVALUATION_v3.0.0.md` exists and is non-authoritative supporting material.
- No active document self-identifies as PROPOSED / NOT ACTIVE.
- No active normative reference targets a superseded predecessor.
- Trade Physics deterministic and intelligence authorities are present and uniquely named.
- PR #73 remains unmerged.

Promotion must fail closed if any check above fails.