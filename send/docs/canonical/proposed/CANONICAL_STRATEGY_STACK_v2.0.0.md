# CANONICAL_STRATEGY_STACK_v2.0.0

Version: 2.0.0
Status: PROPOSED — NOT ACTIVE CANONICAL
Supersession intent: CANONICAL_STRATEGY_STACK_v1.0.0.md

This proposed root manifest preserves the existing official strategy flow and introduces explicit authority for the FSM-to-SignalEvent execution handoff contract.

## 1. Official Strategy Flow

MARKET DATA
-> MARKET MODEL
-> SR / CORRIDOR ENGINE
-> TIME MODEL
-> SCORING MODEL
-> DECISION OBJECT
-> DECISION FSM
-> SIGNAL ENGINE
-> SIGNAL EVENT / EXECUTION RESULT
-> DELIVERY / OBSERVABILITY

Distribution remains downstream of SignalEvent and execution truth.

## 2. Proposed Root Strategy Set

1. ALGO_SPEC_v2.0.0.md
2. TIME_MODEL_UNIFIED_CANON_v2.0.0.md
3. SR_CORRIDOR_ENGINE_SPEC_v2.0.0.md
4. DECISION_OBJECT_CANONICAL_SPEC_v1.0.0.md
5. FSM_DECISION_ENGINE_SPEC_v2.0.0.md
6. SIGNAL_ENGINE_EXECUTION_SPEC_v3.0.0.md
7. SIGNAL_EXECUTION_HANDOFF_CANON_v1.0.0.md
8. OBSERVABILITY_SPEC_v3.0.0.md

Supporting implementation authorities include:
- EVENT_SCHEMA_SPEC_v3.0.0.md
- OBSERVABILITY_LOGGING_SPEC_v3.0.0.md
- MODULE_INTERFACE_SPEC_v3.0.0.md

## 3. Handoff Precedence

For conflict about DecisionObject -> FSM -> SignalEvent -> execution result:
1. this root manifest
2. SIGNAL_EXECUTION_HANDOFF_CANON_v1.0.0.md
3. FSM_DECISION_ENGINE_SPEC_v2.0.0.md
4. SIGNAL_ENGINE_EXECUTION_SPEC_v3.0.0.md
5. MODULE_INTERFACE_SPEC_v3.0.0.md
6. OBSERVABILITY_SPEC_v3.0.0.md / EVENT_SCHEMA_SPEC_v3.0.0.md according to policy/mechanics scope

## 4. Locked Separation

- DecisionObject = strategy truth
- FSM handoff = operational truth
- Signal engine execution result = execution truth
- Distribution router/publisher = distribution truth

No layer may silently substitute for another.

## 5. No-Code Rule

Until this proposed root manifest and its referenced proposed specs are promoted into the active canonical set, the existing active root manifest remains authoritative and runtime code must not claim conformance to this proposal.
