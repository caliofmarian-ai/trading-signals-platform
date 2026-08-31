# OBSERVABILITY_LOGGING_SPEC_v3.0.0

Version: 3.0.0
Status: PROPOSED — NOT ACTIVE CANONICAL
Supersession intent: OBSERVABILITY_LOGGING_SPEC_v2.0.0.md

All v2.0.0 implementation mechanics remain inherited except where this proposed version adds the post-FSM execution-result event family.

## 1. New Event Family

Observability logging must support:
- signal_execution_result

Purpose:
- persist signal-engine execution truth after FSM handoff and before/independent of distribution publication truth.

## 2. Minimum Logged Fields

Required correlation:
- event_id and common envelope
- execution_attempt_id
- symbol
- signal_id where applicable
- stage where applicable
- run_id
- timestamp

Required domain payload:
- execution_outcome
- execution_reason
- candidate_handoff_ready
- signal_event_available
- destination_class

Recommended:
- payload_reference/candidate_reference
- fsm summary/reference
- decision summary/reference
- blocker/failure detail

## 3. Outcome Separation

signal_execution_result must not reuse distribution publish-result enums as substitutes for execution outcomes.

Execution outcomes remain:
- EMITTED
- NOT_EMITTED
- BLOCKED
- SKIPPED
- FAILED
- DEFERRED

Distribution publish outcomes remain owned by route/distribution events.

## 4. Pre-Distribution State

When routing has not started:
- destination_class must explicitly state PRE_DISTRIBUTION_UNRESOLVED or a canonically equivalent value;
- no route_publish_attempt/result may be fabricated;
- no external visibility may be claimed.

## 5. Decision Logging Clarification

Decision observability remains responsible for strategy decision evidence.
Execution outcome must not exist only as nested generic decision debug evidence.

Compatibility logs may coexist during migration, but the dedicated execution event is the target canonical mechanism.

## 6. Failure Logging

Failure to persist a materially required execution-result event must itself be surfaced as an observability failure where possible, without mutating trading behavior.

## 7. Promotion Preconditions

- EVENT_SCHEMA_SPEC_v3.0.0 defines the event contract.
- OBSERVABILITY_SPEC_v3.0.0 defines policy.
- runtime logging implementation changes only after active promotion and re-audit.
