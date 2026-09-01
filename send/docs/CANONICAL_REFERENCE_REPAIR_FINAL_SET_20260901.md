# CANONICAL_REFERENCE_REPAIR_FINAL_SET_20260901

Status: SUPPORTING PROMOTION PREFLIGHT — NOT CANONICAL AUTHORITY  
Date: 2026-09-01  
Program: Trade Physics + staged-execution active canonical promotion

## 1. Purpose

This record freezes the final intended classification of active functional documents that remain semantically valid but contain normative references to authorities scheduled for supersession.

It prevents circular/staggered reference repair by assigning final PATCH successor filenames before those successors are materialized.

A PATCH successor must preserve the document's existing functional semantics. It may:
- update canonical filenames/versions/paths;
- update its own version/status/path metadata;
- clarify terminology only where required to avoid conflict with the promoted graph;
- add a migration/version-history note describing the reference repair.

It MUST NOT introduce new domain behavior.

## 2. Structural documents — NOT PATCH

The following are structural successors and are outside this PATCH set:

- `CANONICAL_STRATEGY_STACK_v1.0.0` -> `v2.0.0`
- `CANONICAL_MASTER_INDEX_v1.0.0` -> `v2.0.0`
- `ALGO_SPEC_v2.0.0` -> `v3.0.0`
- `SR_CORRIDOR_ENGINE_SPEC_v2.0.0` -> `v3.0.0`
- `TIME_MODEL_UNIFIED_CANON_v2.0.0` -> `v3.0.0`
- new `TRADE_PHYSICS_MODEL_SPEC_v1.0.0`
- `DECISION_OBJECT_CANONICAL_SPEC_v1.0.0` -> `v2.0.0`
- `FSM_DECISION_ENGINE_SPEC_v1.0.0` -> `v2.0.0`
- `SIGNAL_ENGINE_EXECUTION_SPEC_v2.0.0` -> `v3.0.0`
- `RISK_MODEL_v2.0.0` -> `v3.0.0`
- `OBSERVABILITY_SPEC_v2.0.0` -> `v3.0.0`
- `OBSERVABILITY_LOGGING_SPEC_v2.0.0` -> `v3.0.0`
- `EVENT_SCHEMA_SPEC_v2.0.0` -> `v3.0.0`
- `DECISION_AUDIT_SPEC_v2.0.0` -> `v3.0.0`
- `TRADE_TEMPORAL_TELEMETRY_SPEC_v2.0.0` -> `v3.0.0`
- `OUTCOME_TRACKING_SPEC_v2.0.0` -> `v3.0.0`
- `PERFORMANCE_ANALYTICS_SPEC_v2.0.0` -> `v3.0.0`
- `RESEARCH_AND_LEARNING_FRAMEWORK_SPEC_v2.0.0` -> `v3.0.0`
- new `TRADE_PHYSICS_INTELLIGENCE_SPEC_v1.0.0`
- `STRATEGY_INTELLIGENCE_SYSTEM_v2.0.0` -> `v3.0.0`
- `AUTONOMOUS_STRATEGY_EVOLUTION_SYSTEM_v2.0.0` -> `v3.0.0`
- `STRATEGY_PARAMETER_CONTROL_SPEC_v2.0.0` -> `v3.0.0`
- `MODULE_INTERFACE_SPEC_v2.0.0` -> `v3.0.0`
- `SYSTEM_ARCHITECTURE_MAP_v2.0.0` -> `v3.0.0`
- `SYSTEM_INVARIANTS_v2.0.0` -> `v3.0.0`
- `TEST_PLAN_v2.0.0` -> `v3.0.0`
- `COMMUNITY_FEEDBACK_AND_PRIVACY_SPEC_v2.0.0` -> `v3.0.0`
- `CANON_BATCH_EVALUATION_v2.0.0` -> `v3.0.0` as supporting/governance record.

## 3. Final PATCH successor set

The following functional authorities remain semantically stable and require reference-only successors:

| Current active | Final PATCH successor |
|---|---|
| `ADMIN_SURFACE_AND_CONTROL_PLANE_CANON_v2.0.0.md` | `ADMIN_SURFACE_AND_CONTROL_PLANE_CANON_v2.0.1.md` |
| `ADMIN_CONTROL_SPEC_v2.0.0.md` | `ADMIN_CONTROL_SPEC_v2.0.1.md` |
| `ADMIN_OPERATIONS_SPEC_v2.0.0.md` | `ADMIN_OPERATIONS_SPEC_v2.0.1.md` |
| `ADMIN_TREE_MAP_v2.0.0.md` | `ADMIN_TREE_MAP_v2.0.1.md` |
| `CONTROL_PANEL_HIERARCHY_AND_INTELLIGENCE_SPEC_v2.0.0.md` | `CONTROL_PANEL_HIERARCHY_AND_INTELLIGENCE_SPEC_v2.0.1.md` |
| `ROLE_AND_PERMISSION_MATRIX_SPEC_v2.0.0.md` | `ROLE_AND_PERMISSION_MATRIX_SPEC_v2.0.1.md` |
| `SIGNAL_DISTRIBUTION_ARCHITECTURE_v2.0.0.md` | `SIGNAL_DISTRIBUTION_ARCHITECTURE_v2.0.1.md` |
| `SIGNAL_DISTRIBUTION_SPEC_v2.0.0.md` | `SIGNAL_DISTRIBUTION_SPEC_v2.0.1.md` |
| `CHANNEL_CONFIG_SPEC_v2.0.0.md` | `CHANNEL_CONFIG_SPEC_v2.0.1.md` |
| `TELEGRAM_UX_v2.0.0.md` | `TELEGRAM_UX_v2.0.1.md` |
| `AFFILIATE_SIGNAL_DISTRIBUTION_MODEL_v2.0.0.md` | `AFFILIATE_SIGNAL_DISTRIBUTION_MODEL_v2.0.1.md` |
| `SIGNAL_ECONOMICS_AND_MONETIZATION_MODEL_v2.0.0.md` | `SIGNAL_ECONOMICS_AND_MONETIZATION_MODEL_v2.0.1.md` |
| `FAILURE_RECOVERY_SPEC_v2.0.0.md` | `FAILURE_RECOVERY_SPEC_v2.0.1.md` |
| `DEPLOYMENT_PROTOCOL_v2.0.0.md` | `DEPLOYMENT_PROTOCOL_v2.0.1.md` |
| `SECURITY_MODEL_v2.0.0.md` | `SECURITY_MODEL_v2.0.1.md` |
| `GOVERNANCE_AND_CHANGE_CONTROL_v2.0.0.md` | `GOVERNANCE_AND_CHANGE_CONTROL_v2.0.1.md` |
| `HUMAN_COMPREHENSION_AND_SELF_EXPLAINING_CONTROL_SURFACE_CANON_v1.0.0.md` | `HUMAN_COMPREHENSION_AND_SELF_EXPLAINING_CONTROL_SURFACE_CANON_v1.0.1.md` |

## 4. Cross-reference rule inside the PATCH set

When one PATCH successor references another document in this PATCH set, it must use the **final PATCH filename** above, not the old v2.0.0/v1.0.0 filename.

When it references a structural successor, it must use that successor's final proposed filename.

This avoids a second reference-repair cycle.

## 5. Distribution-specific allowed clarification

`SIGNAL_DISTRIBUTION_SPEC_v2.0.1.md` may replace the ambiguous phrase:

`For each emitted governed signal stage`

with:

`For each governed SignalEvent candidate released to distribution`

or equivalent.

This is a semantic clarification required by the new execution vocabulary, not a policy change.

It MUST NOT change:
- route eligibility;
- FREE/BASIC/PRO/ELITE limits;
- SILENT behavior;
- reset policy;
- successful OPEN_NOW counting;
- outcome-capable route policy;
- distribution ownership.

## 6. No-change functional authorities

At this preflight stage, the following functional authorities are not assigned a successor solely for this program unless a later exact-reference scan proves a normative stale dependency:

- `ADMIN_CONTROL`/`ADMIN_OPERATIONS` are already included above because their references are stale;
- `CHANNEL_CONFIG` is included above for the same reason;
- other untouched active documents not listed in structural or PATCH sets remain on their current versions.

Any newly discovered normative stale reference is a promotion blocker and must be classified before active promotion.

## 7. Promotion condition

This list is frozen only for the current preflight branch. Active promotion still requires:
1. materialization of every PATCH successor above as a complete self-contained document;
2. exact-reference scan against fresh main;
3. Root Stack/Master Index update to exact final filenames, including Risk v3 and Community Feedback v3;
4. atomic active/superseded placement;
5. final cross-document audit;
6. no runtime code in the promotion PR.

PR #73 remains DO NOT MERGE.
