# OBSERVABILITY_SPEC_v3.0.0

Version: 3.0.0
Status: PROPOSED — NOT ACTIVE CANONICAL
Supersession intent: OBSERVABILITY_SPEC_v2.0.0.md

All v2.0.0 policy truths remain inherited except where this proposed version makes execution truth a first-class observability domain distinct from strategy, FSM and distribution truth.

## 1. Execution Observability Is Explicit

Observability must reconstruct the chain:
DecisionObject -> FSM result -> signal-engine execution result -> distribution result -> external visibility/outcome where applicable.

## 2. Required Execution Questions

Observability must answer:
- was the actionable stage accepted by FSM?
- did signal engine construct SignalEvent?
- what execution outcome resulted?
- why was it emitted, not emitted, blocked, skipped, failed or deferred?
- had routing begun?
- which destination class was involved, or was it explicitly pre-distribution unresolved?

## 3. Separate Truth Domains

Forbidden:
- hiding execution truth only inside generic decision debug;
- treating FSM state as publication proof;
- treating SignalEvent construction as external visibility;
- treating distribution failure as strategy rejection.

## 4. Required Execution Outcome Families

Observability must preserve:
- EMITTED
- NOT_EMITTED
- BLOCKED
- SKIPPED
- FAILED
- DEFERRED

## 5. Correlation

Execution evidence must correlate with:
- execution_attempt_id
- signal_id/setup identity
- symbol
- stage
- timeframe where applicable
- run/cycle identity where available
- timestamp

## 6. Pre-Distribution Visibility

If routing has not begun, observability must make that explicit. Absence of route data must not be mistaken for missing evidence or delivery failure.

Baseline proposed semantic:
- destination_class = PRE_DISTRIBUTION_UNRESOLVED

## 7. Promotion Preconditions

Promotion requires aligned EVENT_SCHEMA, OBSERVABILITY_LOGGING, SIGNAL_ENGINE_EXECUTION and MODULE_INTERFACE versions plus root manifest/master-index promotion.
