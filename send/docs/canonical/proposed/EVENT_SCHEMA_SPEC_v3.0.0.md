# EVENT_SCHEMA_SPEC_v3.0.0

BinaryBot — Canonical Event Envelope, Correlation & Domain Schema Specification
Version: 3.0.0
Status: PROPOSED DESIGN DELTA — NOT ACTIVE CANONICAL — NOT PROMOTION READY
Owner: BinaryBot / DROPi Signals

## Promotion Notice

This file records a structural schema delta only. A promoted successor must be materialized as a complete self-contained EVENT_SCHEMA specification and must not depend normatively on a version that becomes Superseded.

The major version is proposed because introducing a new first-class execution-result event family is a structural event-contract change.

## 1. Preserved Core Principles

The following active truths remain unchanged:
- every materially relevant event must be structurally representable;
- every event must be reconstructable in context;
- no silent governed-state mutation is allowed;
- signal identity must remain stable across the same trade idea lifecycle;
- schema must support forensic reconstruction, analytics and governance;
- schema-invalid events are not trustworthy canonical evidence;
- strategy, FSM, execution, distribution and outcome domains must remain semantically distinguishable.

## 2. Proposed Event Family: signal_execution_result

Purpose:
Represent signal-engine execution truth after FSM handoff without misclassifying that truth as a strategy decision, FSM transition or route publication result.

The same execution_attempt_id may correlate more than one execution-result checkpoint when the execution lifecycle advances, for example a pre-distribution DEFERRED checkpoint followed later by a post-distribution final result.

## 3. Separation Rule

signal_execution_result must not replace or be confused with:
- decision_evaluated
- decision_promoted
- decision_rejected
- decision_no_signal
- fsm_transition
- signal_stage_visible
- route_publish_attempt
- route_publish_result

Each family preserves a distinct truth domain.

Legacy signal_emitted is addressed explicitly in Section 13 as a compatibility family, not as the primary v3 execution truth.

## 4. Execution Outcome Enum

signal_execution_result.execution_outcome must support at least:
- EMITTED
- NOT_EMITTED
- BLOCKED
- SKIPPED
- FAILED
- DEFERRED

These values describe signal-engine execution truth only.

## 5. Execution Phase

Proposed required field:
- execution_phase: PRE_DISTRIBUTION | POST_DISTRIBUTION

PRE_DISTRIBUTION describes execution truth before route/publisher completion.
POST_DISTRIBUTION describes the signal-engine result after downstream distribution evidence is available.

A pre-distribution event may be the only event for an attempt while distribution remains intentionally disabled.

## 6. Required Correlation Fields

Required:
- execution_attempt_id: string
- symbol: string
- ts_utc and ts_epoch_ms through the common envelope
- run_id through the common envelope

Required when the execution attempt concerns an actionable lifecycle stage:
- signal_id: string
- stage: PRE | CONFIRM | OPEN_NOW
- timeframe: string where the originating contract provides it

Optional when no actionable signal identity exists:
- setup_correlation_id or equivalent governed correlation identity

## 7. Required Domain Payload

Minimum required payload:
- execution_phase
- execution_outcome
- execution_reason
- stage_handoff_ready: boolean
- trade_execution_ready: boolean
- signal_event_available: boolean
- destination_state: string

Conditionally required:
- candidate_reference or payload_reference when signal_event_available=true
- distribution_reference(s) for POST_DISTRIBUTION outcomes derived from downstream distribution evidence

Recommended structured evidence:
- fsm_result summary/reference
- decision_object summary/reference
- blocker/failure detail
- candidate schema version

## 8. destination_state Semantics

Before routing begins:
- destination_state = PRE_DISTRIBUTION_UNRESOLVED

Meaning:
- no route has yet been evaluated;
- no destination has been selected;
- this is not a transport failure;
- this is not publication authorization.

After routing begins, signal_execution_result should reference downstream distribution evidence. Exact route, destination and transport truth remains owned by route/distribution events.

## 9. Handoff Readiness Semantics

stage_handoff_ready=true means the post-FSM operational contract explicitly accepted the same actionable stage for signal-engine handoff.

It must be false when the stage is blocked or suppressed by cooldown, watchlist/focus capacity, duplicate suppression, identity continuity failure, invalid lifecycle path, FSM rejection/block, invariant failure or another explicit no-release result.

trade_execution_ready is distinct:
- false for PRE;
- false for CONFIRM;
- may be true only for accepted OPEN_NOW.

Normal function return or transition-event existence is not sufficient evidence of either readiness field.

## 10. signal_event_available Semantics

signal_event_available=true means a canonical SignalEvent candidate was successfully constructed from real evidence for the accepted stage.

It does not mean:
- route eligible
- destination selected
- Telegram published
- entitlement consumed
- outcome registered
- broker trade executed

SignalEvent construction alone must not result in EMITTED.

## 11. Outcome Mapping Constraints

### PRE_DISTRIBUTION

If SignalEvent is available but distribution is intentionally not invoked, execution_outcome must be DEFERRED with an explicit reason.

If no candidate can be formed because readiness/evidence is insufficient, NOT_EMITTED may apply.
If an explicit rule blocks the path, BLOCKED may apply.
If a flow rule intentionally skips the attempt, SKIPPED may apply.
If a technical execution-layer failure occurs, FAILED may apply.

EMITTED is forbidden in PRE_DISTRIBUTION phase.

### POST_DISTRIBUTION

EMITTED is permitted only when linked downstream distribution evidence proves at least one authorized publication succeeded.

If multiple routes exist, exact per-route success/failure remains represented by route_publish_result events. signal_execution_result must link to those events rather than flattening route truth into invented detail.

Mixed route outcomes may still yield execution_outcome=EMITTED when at least one authorized route published successfully, provided the linked distribution events preserve all partial failures/skips exactly.

## 12. Decision Event Clarification

Canonical decision-family names remain:
- decision_evaluated
- decision_promoted
- decision_rejected
- decision_no_signal

A generic legacy event name such as decision may be retained only as a compatibility/migration concern in runtime implementation. It must not be treated as the primary canonical family.

Execution truth must not exist only inside generic decision debug data.

## 13. Signal Lifecycle Event Clarification

The proposed v3 primary families are:
- signal_execution_result for signal-engine execution truth;
- signal_stage_visible for governed external lifecycle visibility;
- route_publish_attempt / route_publish_result for exact route publication truth.

The legacy signal_emitted family becomes a compatibility-only event name in the v3 migration model. It must not be emitted as the primary v3 proof for new execution attempts after migration completes.

Historical signal_emitted records remain readable as historical evidence under their original schema/version. They must not be silently reinterpreted as signal_execution_result or signal_stage_visible.

A SignalEvent candidate built while distribution is intentionally not invoked must produce neither signal_stage_visible nor a new primary signal_emitted event.

This removes the ambiguity between internal candidate construction and external delivery.

## 14. Distribution Event Preservation

Distribution event families remain authoritative for route-level truth, including:
- route_publish_attempt
- route_publish_result
- route_reset
- route_state_changed
- route_mapping_invalid

## 15. Stable Signal Identity

The same trade idea must preserve the same signal_id across:
- PRE
- CONFIRM
- OPEN_NOW
- signal_execution_result events for those stages
- downstream distribution events
- signal_stage_visible when external visibility occurs
- outcome/reconciliation events where applicable

## 16. Dedup Observability

Engine-side duplicate suppression and distribution-side duplicate suppression must remain distinguishable and observable.

Distribution-side dedup remains represented in distribution events.

## 17. Migration Requirements

Before active promotion:
1. materialize a complete self-contained successor EVENT_SCHEMA specification;
2. encode signal_emitted as compatibility-only for new v3 behavior while preserving historical readability;
3. define compatibility status for generic legacy runtime event families;
4. update runtime schema only in a later code PR after canonical promotion;
5. update observability logging mechanics only after promotion;
6. add schema-validation tests for all execution phases/outcomes;
7. do not reinterpret historical events silently;
8. update the complete canonical master index/root references as required.

## 18. No-Code / No-Distribution Rule

This proposed delta authorizes no runtime code change and no distribution activation.

Until active promotion:
- EVENT_SCHEMA_SPEC_v2.0.0 remains authoritative;
- runtime code must not claim compliance with this proposal;
- PR #73 remains blocked.
