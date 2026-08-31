# CANONICAL_MASTER_INDEX_v2.0.0

Version: 2.0.0
Status: PROPOSED — NOT ACTIVE CANONICAL
Supersession intent: CANONICAL_MASTER_INDEX_v1.0.0.md

## 1. Purpose

This proposed master index describes the intended active authority set after the signal-execution/observability remediation is promoted.

It does not alter current active authority until promotion is completed.

## 2. Proposed Strategy Pipeline Authorities

- CANONICAL_STRATEGY_STACK_v2.0.0.md — proposed root manifest
- ALGO_SPEC_v2.0.0.md — unchanged
- SR_CORRIDOR_ENGINE_SPEC_v2.0.0.md — unchanged
- TIME_MODEL_UNIFIED_CANON_v2.0.0.md — unchanged
- DECISION_OBJECT_CANONICAL_SPEC_v1.0.0.md — unchanged
- FSM_DECISION_ENGINE_SPEC_v2.0.0.md — proposed successor
- SIGNAL_ENGINE_EXECUTION_SPEC_v3.0.0.md — proposed successor
- SIGNAL_EXECUTION_HANDOFF_CANON_v1.0.0.md — proposed new explicit handoff authority

## 3. Proposed Observability Authorities

- OBSERVABILITY_SPEC_v3.0.0.md — proposed successor
- OBSERVABILITY_LOGGING_SPEC_v3.0.0.md — proposed successor
- EVENT_SCHEMA_SPEC_v3.0.0.md — proposed successor
- DECISION_AUDIT_SPEC_v2.0.0.md — unchanged

## 4. Proposed System Interface Authority

- MODULE_INTERFACE_SPEC_v3.0.0.md — proposed successor

## 5. Unchanged Distribution Authorities

The following remain unchanged and authoritative for their current domains after any future promotion:
- SIGNAL_DISTRIBUTION_ARCHITECTURE_v2.0.0.md
- SIGNAL_DISTRIBUTION_SPEC_v2.0.0.md
- CHANNEL_CONFIG_SPEC_v2.0.0.md
- TELEGRAM_UX_v2.0.0.md

## 6. Unchanged System Governance Authorities

- SYSTEM_INVARIANTS_v2.0.0.md
- GOVERNANCE_AND_CHANGE_CONTROL_v2.0.0.md
- TEST_PLAN_v2.0.0.md
- DEPLOYMENT_PROTOCOL_v2.0.0.md

## 7. Supersession Rule on Promotion

If the proposed remediation is promoted, the following prior versions must become Superseded and must not remain simultaneously authoritative:
- CANONICAL_MASTER_INDEX_v1.0.0.md
- CANONICAL_STRATEGY_STACK_v1.0.0.md
- FSM_DECISION_ENGINE_SPEC_v1.0.0.md
- SIGNAL_ENGINE_EXECUTION_SPEC_v2.0.0.md
- OBSERVABILITY_SPEC_v2.0.0.md
- OBSERVABILITY_LOGGING_SPEC_v2.0.0.md
- EVENT_SCHEMA_SPEC_v2.0.0.md
- MODULE_INTERFACE_SPEC_v2.0.0.md

The promotion procedure must make this status transition explicit and auditable.

## 8. Proposed Execution Event Addition

The proposed event-schema authority adds:
- signal_execution_result

This event represents post-FSM signal-engine execution truth and does not replace strategy, FSM or distribution event families.

## 9. No-Code Rule

No runtime code change is authorized by this proposed index. Active v1/v2 canonical documents remain authoritative until explicit promotion is completed.
