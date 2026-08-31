# OBSERVABILITY_SPEC_v3.0.0

Version: 3.0.0
Status: PROPOSED DESIGN DELTA — NOT ACTIVE CANONICAL — NOT PROMOTION READY
Supersession intent: OBSERVABILITY_SPEC_v2.0.0.md

This file records the approved observability-policy delta. A promoted successor must be materialized as a complete self-contained specification.

## 1. Execution Observability Is Explicit

Observability must reconstruct the chain:
DecisionObject -> FSM result/handoff -> signal-engine execution result -> distribution result -> external visibility/outcome where applicable.

## 2. Required Execution Questions

Observability must answer:
- what actionable stage did strategy request?
- did FSM release that exact stage to signal engine?
- was the stage lifecycle-handoff-ready?
- was it final trade-execution-ready?
- did signal engine construct SignalEvent?
- what execution outcome resulted?
- why was it emitted, not emitted, blocked, skipped, failed or deferred?
- had routing begun?
- what downstream distribution evidence exists when routing did begin?

## 3. Separate Truth Domains

Forbidden:
- hiding execution truth only inside generic decision debug;
- treating FSM state as publication proof;
- treating stage_handoff_ready as trade_execution_ready;
- treating SignalEvent construction as external visibility or EMITTED;
- treating distribution failure as strategy rejection.

## 4. Required Execution Outcome Families

Observability must preserve:
- EMITTED
- NOT_EMITTED
- BLOCKED
- SKIPPED
- FAILED
- DEFERRED

## 5. Execution Phases

Execution observability must distinguish at least:
- PRE_DISTRIBUTION
- POST_DISTRIBUTION

PRE_DISTRIBUTION may show a valid candidate with DEFERRED while distribution is intentionally not invoked.

EMITTED is not valid merely because a candidate exists. It requires linked downstream governed publication evidence.

## 6. Correlation

Execution evidence must correlate with:
- execution_attempt_id
- signal_id/setup identity
- symbol
- stage
- timeframe where applicable
- run/cycle identity where available
- timestamp
- downstream distribution references where applicable

The same execution_attempt_id may correlate a pre-distribution checkpoint with a later post-distribution final execution result.

## 7. Pre-Distribution Destination State

If routing has not begun, observability must make that explicit rather than silently omitting destination context.

Proposed semantic:
- destination_state = PRE_DISTRIBUTION_UNRESOLVED

This is not a failed destination and not authorization to publish.

## 8. Route-Level Truth Preservation

When distribution begins, exact route/destination/publish truth remains owned by distribution events.

Signal-engine observability may summarize the final execution outcome but must link to route-level evidence and must not overwrite partial route failures, skips or duplicate suppressions.

## 9. Promotion Requirements

Before active promotion:
- materialize a complete self-contained successor OBSERVABILITY specification;
- align complete EVENT_SCHEMA, OBSERVABILITY_LOGGING, SIGNAL_ENGINE_EXECUTION and MODULE_INTERFACE successors;
- resolve primary event-family semantics so internal candidate creation cannot be mistaken for external delivery;
- update root/master version references completely where required;
- keep runtime unchanged until promotion and re-audit.
