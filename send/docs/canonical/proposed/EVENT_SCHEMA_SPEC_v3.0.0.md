# EVENT_SCHEMA_SPEC_v3.0.0

BinaryBot — Canonical Event Envelope, Correlation & Domain Schema Specification
Version: 3.0.0
Status: PROPOSED — NOT ACTIVE CANONICAL
Owner: BinaryBot / DROPi Signals

## Supersession Intent

If promoted, this document is intended to supersede EVENT_SCHEMA_SPEC_v2.0.0.md.

All v2.0.0 provisions not explicitly changed below are inherited unchanged. This proposed v3.0.0 exists because the new post-FSM execution-result family is a structural event-contract change and therefore requires major-version discipline under GOVERNANCE_AND_CHANGE_CONTROL_v2.0.0.md.

This proposal does not become authoritative until promoted through canonical governance and reflected in the canonical master index.

## 1. Preserved Core Principles

The following v2 truths remain unchanged:
- every materially relevant event must be structurally representable;
- every event must be reconstructable in context;
- no silent governed-state mutation is allowed;
- signal identity must remain stable across the same trade idea lifecycle;
- schema must support forensic reconstruction, analytics and governance;
- schema-invalid events are not trustworthy canonical evidence;
- strategy, FSM, execution, distribution and outcome domains must remain semantically distinguishable.

## 2. New Canonical Event Family: signal_execution_result

This proposed version adds a dedicated signal-engine execution event family:

- signal_execution_result

Purpose:
Represent the post-FSM signal-engine execution verdict before, during or after SignalEvent candidate construction, without misclassifying that truth as a strategy decision, FSM transition or distribution result.

## 3. Separation Rule

signal_execution_result must not replace or be confused with:
- decision_evaluated
- decision_promoted
- decision_rejected
- decision_no_signal
- fsm_transition
- signal_emitted
- signal_stage_visible
- route_publish_attempt
- route_publish_result

A single logical opportunity may produce correlated events in several of these families because each family represents a different truth domain.

## 4. Execution Outcome Enum

signal_execution_result.execution_outcome must support at least:
- EMITTED
- NOT_EMITTED
- BLOCKED
- SKIPPED
- FAILED
- DEFERRED

These values describe signal-engine execution truth only.

## 5. Required Correlation Fields

A signal_execution_result event must contain enough context for deterministic reconstruction.

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

## 6. Required Domain Payload

Minimum required payload:
- execution_outcome: enum
- execution_reason: string
- candidate_handoff_ready: boolean
- signal_event_available: boolean
- destination_class: string

Conditionally required:
- payload_reference or candidate_reference when signal_event_available=true

Recommended structured evidence:
- fsm_result summary/reference
- decision_object summary/reference
- blocker/failure detail
- candidate schema version

## 7. destination_class Semantics

Execution trace must not silently omit destination state.

Before routing begins, destination_class should use the explicit semantic baseline:
- PRE_DISTRIBUTION_UNRESOLVED

Meaning:
- no distribution route has yet been evaluated;
- no destination has been selected;
- this is not a transport failure;
- this is not publication authorization.

After routing begins, distribution-domain events remain the authoritative source for concrete route/destination selection and publication result.

## 8. candidate_handoff_ready Semantics

candidate_handoff_ready=true means the post-FSM operational contract explicitly accepted the same actionable stage for signal-engine handoff.

It must be false when the stage is blocked or suppressed by:
- cooldown
- watchlist/focus capacity without valid replacement
- duplicate stage/candle suppression
- identity continuity failure
- invalid lifecycle path
- FSM rejection/block
- invariant failure
- another explicit no-release outcome

Normal function return or transition-event existence is not sufficient evidence of readiness.

## 9. signal_event_available Semantics

signal_event_available=true means a canonical SignalEvent candidate was successfully constructed from real evidence for the accepted stage.

It does not mean:
- route eligible
- destination selected
- Telegram published
- entitlement consumed
- outcome registered
- broker trade executed

## 10. Decision Event Clarification

The canonical decision-family names remain:
- decision_evaluated
- decision_promoted
- decision_rejected
- decision_no_signal

A generic legacy event name such as decision may be retained only as a compatibility/migration concern in runtime schema implementation. It must not be treated as the primary canonical v3 decision family.

Execution outcome fields must not be hidden exclusively inside generic decision debug data as the only canonical execution evidence.

## 11. Signal Lifecycle Event Clarification

signal_emitted means a signal has been generated/emitted according to the signal-engine execution semantics defined by the active execution canon.

signal_stage_visible remains reserved for governed external visibility evidence.

Where a SignalEvent candidate is built but downstream distribution is intentionally not invoked, signal_execution_result with DEFERRED is the appropriate execution evidence; signal_stage_visible must not be emitted.

## 12. Distribution Event Preservation

The v2 distribution event families remain unchanged in authority intent:
- route_publish_attempt
- route_publish_result
- route_reset
- route_state_changed
- route_mapping_invalid

Distribution events remain the source of route/destination publication truth.

## 13. Stable Signal Identity

The same trade idea must preserve the same signal_id across:
- PRE
- CONFIRM
- OPEN_NOW
- signal_execution_result events for those stages
- downstream distribution events
- outcome/reconciliation events where applicable

## 14. Dedup Observability

Dedup-related execution suppression must be observable.

If the signal engine suppresses a duplicate actionable stage before distribution, signal_execution_result should use an outcome/reason combination that preserves the distinction between duplicate suppression and other non-emission causes.

Distribution-side dedup remains represented in distribution events.

## 15. Migration Requirements

Promotion of v3.0.0 requires:
1. runtime event schema to be updated in a separate code PR only after canonical promotion;
2. legacy generic event families to be explicitly migrated or retained as compatibility aliases with documented status;
3. observability logging mechanics to recognize signal_execution_result;
4. tests proving schema validation for all execution outcomes;
5. no historical event reinterpretation without explicit migration notes.

## 16. No-Code / No-Distribution Rule

This proposed document authorizes no runtime code change by itself and no distribution activation.

Until promotion:
- EVENT_SCHEMA_SPEC_v2.0.0 remains authoritative;
- runtime code must not claim compliance with v3.0.0;
- PR #73 remains blocked.
