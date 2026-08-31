# OBSERVABILITY_LOGGING_SPEC_v3.0.0

Version: 3.0.0
Status: PROPOSED DESIGN DELTA — NOT ACTIVE CANONICAL — NOT PROMOTION READY
Supersession intent: OBSERVABILITY_LOGGING_SPEC_v2.0.0.md

This file records the approved logging/telemetry delta. A promoted successor must be materialized as a complete self-contained specification.

## 1. Proposed Event Family

Observability logging must support:
- signal_execution_result

Purpose:
- persist signal-engine execution truth after FSM handoff and separately from route-level publication truth.

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
- execution_phase
- execution_outcome
- execution_reason
- stage_handoff_ready
- trade_execution_ready
- signal_event_available
- destination_state

Conditionally required:
- candidate/payload reference when a SignalEvent exists
- distribution references when execution_phase=POST_DISTRIBUTION

Recommended:
- FSM summary/reference
- DecisionObject summary/reference
- blocker/failure detail

## 3. Outcome Separation

Execution outcomes remain:
- EMITTED
- NOT_EMITTED
- BLOCKED
- SKIPPED
- FAILED
- DEFERRED

Distribution publish outcomes remain owned by route/distribution events.

SignalEvent construction alone must not be logged as EMITTED.

## 4. Execution Phase Rules

### PRE_DISTRIBUTION

If a SignalEvent exists but routing is intentionally disabled/not invoked:
- execution_phase = PRE_DISTRIBUTION
- execution_outcome = DEFERRED
- destination_state = PRE_DISTRIBUTION_UNRESOLVED

No route_publish_attempt/result may be fabricated.
No external visibility may be claimed.

### POST_DISTRIBUTION

When downstream distribution evidence exists:
- execution_phase = POST_DISTRIBUTION
- signal_execution_result must reference the relevant distribution evidence;
- EMITTED requires proof that at least one authorized publication succeeded;
- exact route-level success/failure remains in route events.

The same execution_attempt_id may connect pre- and post-distribution checkpoints.

## 5. Readiness Logging

stage_handoff_ready and trade_execution_ready must be logged as distinct semantics.

PRE/CONFIRM may have stage_handoff_ready=true while trade_execution_ready=false.
OPEN_NOW may have both true only after valid FSM acceptance/actionability.

## 6. Decision Logging Clarification

Decision observability remains responsible for strategy decision evidence.
Execution outcome must not exist only as nested generic decision debug evidence.

Compatibility logs may coexist during migration, but the dedicated execution-result event is the target mechanism after promotion.

## 7. Failure Logging

Failure to persist a materially required execution-result event must itself be surfaced as an observability failure where possible, without mutating trading behavior.

## 8. Promotion Requirements

Before active promotion:
- materialize a complete self-contained successor logging specification;
- complete EVENT_SCHEMA successor defines the event contract;
- complete OBSERVABILITY successor defines policy;
- primary event semantics must ensure candidate creation cannot be mistaken for delivery;
- runtime logging implementation changes only after active promotion and re-audit.
