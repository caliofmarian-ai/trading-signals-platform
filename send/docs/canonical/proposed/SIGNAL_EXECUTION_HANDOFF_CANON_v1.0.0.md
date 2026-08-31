# SIGNAL_EXECUTION_HANDOFF_CANON_v1.0.0

Version: 1.0.0
Status: PROPOSED — NOT ACTIVE CANONICAL
Owner: BinaryBot / DROPi Signals
Scope: DecisionObject -> FSM -> SignalEvent -> execution-result handoff semantics before distribution

## Authority Notice

This document is a proposed reconciliation artifact. It does not override any active canonical document until explicitly promoted through canonical governance.

It is derived from and must remain consistent with:
- CANONICAL_STRATEGY_STACK_v1.0.0.md
- FSM_DECISION_ENGINE_SPEC_v1.0.0.md
- SIGNAL_ENGINE_EXECUTION_SPEC_v2.0.0.md
- OBSERVABILITY_SPEC_v2.0.0.md
- EVENT_SCHEMA_SPEC_v2.0.0.md
- MODULE_INTERFACE_SPEC_v2.0.0.md
- SIGNAL_DISTRIBUTION_ARCHITECTURE_v2.0.0.md
- SIGNAL_DISTRIBUTION_SPEC_v2.0.0.md
- SYSTEM_INVARIANTS_v2.0.0.md

## 1. Purpose

This proposal removes ambiguity at the boundary between FSM lifecycle handling, SignalEvent construction, signal-engine execution truth and downstream distribution eligibility.

It does not define strategy mathematics, route entitlement policy, Telegram transport, outcome tracking, broker execution or scan cadence.

## 2. Locked Pipeline

The governing order remains:

Market/Strategy -> DecisionObject -> FSM -> Signal Engine -> SignalEvent / Execution Result -> Distribution -> Publisher / External Surface

No layer may bypass the preceding authority boundary.

## 3. Four Truth Domains Must Remain Separate

The runtime must preserve four distinct truth domains:

1. Strategy truth
   - produced in DecisionObject
   - examples: PRE, CONFIRM, OPEN_NOW, REJECT, NO_SIGNAL

2. FSM operational truth
   - states whether the strategic stage was accepted, blocked, suppressed, stalled, rejected or otherwise not released operationally

3. Signal-engine execution truth
   - examples: EMITTED, NOT_EMITTED, BLOCKED, SKIPPED, FAILED, DEFERRED

4. Distribution truth
   - route selection, entitlement, destination resolution, publish attempt/result and delivery evidence

These domains may be correlated but must never be collapsed into one ambiguous field.

## 4. Canonical Actionable Lifecycle

The governed actionable lifecycle remains:

PRE -> CONFIRM -> OPEN_NOW

All visible or distribution-eligible stages of the same trade idea must preserve one stable signal_id.

A stage does not become distribution-eligible merely because the strategy produced that stage.

## 5. Explicit FSM Stage-Acceptance Contract

For every actionable DecisionObject stage PRE, CONFIRM or OPEN_NOW, the post-FSM handoff must explicitly distinguish whether that exact stage was operationally accepted for signal-engine handoff.

The handoff contract must be able to express at least:
- accepted: boolean
- stage: PRE | CONFIRM | OPEN_NOW where applicable
- signal_id
- state_changed: boolean
- reason / reason_family
- transition evidence where applicable
- candidate_handoff_ready: boolean

### 5.1 Accepted-stage meaning

candidate_handoff_ready=true means:
- the DecisionObject stage is actionable;
- lifecycle continuity is valid;
- applicable focus/watchlist/cooldown rules permit the stage;
- the stage is not a duplicate suppressed by the FSM boundary;
- the stage has not been blocked by an invariant or policy guard;
- the post-FSM contract explicitly releases this stage to the signal engine.

### 5.2 Fail-closed rule

candidate_handoff_ready must be false when any of the following apply:
- cooldown_active
- watchlist_full without canonical replacement acceptance
- duplicate stage/candle suppression
- signal identity continuity failure
- invalid lifecycle path
- FSM rejection/block
- invariant failure
- any transition result that does not actually release the requested stage

A function returning normally is not evidence of stage acceptance.
A transition event existing is not by itself evidence of stage acceptance.

## 6. SignalEvent Construction Boundary

SignalEvent remains the canonical engine-to-distribution object.

A SignalEvent may be constructed for PRE, CONFIRM or OPEN_NOW only when:
- DecisionObject is actionable;
- signal_id exists and continuity is valid;
- post-FSM candidate_handoff_ready is true for the same stage;
- the required semantic payload can be built from real decision evidence;
- no hard execution blocker prevents construction.

SignalEvent stage must match the accepted originating stage.

## 7. SignalEvent Is Not Distribution Authorization

Constructing SignalEvent means only that a canonical internal distribution candidate exists.

It does not mean:
- a route has been selected;
- entitlement has been granted;
- a destination exists;
- Telegram may publish;
- an outcome may be registered;
- broker execution may occur.

Distribution authorization remains exclusively downstream under the distribution canon.

## 8. Signal-Engine Execution Result

Every materially relevant post-FSM execution attempt must expose a signal-engine execution result distinct from the strategy and FSM results.

Required outcome families remain:
- EMITTED
- NOT_EMITTED
- BLOCKED
- SKIPPED
- FAILED
- DEFERRED

### 8.1 Pre-distribution meaning

Before a distribution route is evaluated:
- a valid SignalEvent candidate may still have execution outcome DEFERRED when downstream distribution is intentionally not active or not yet invoked;
- absence of route resolution must not be represented as successful delivery;
- NOT_EMITTED or BLOCKED must remain semantically distinguishable from DEFERRED.

## 9. Minimum Execution Trace

The signal-engine execution result must be able to carry at least:
- execution_attempt_id
- signal_id or setup correlation identity
- symbol
- timeframe where available
- stage
- execution outcome family
- reason / blocker / failure detail
- created/evaluated timestamp
- destination_class
- payload_reference or candidate reference where available

### 9.1 Destination before routing

When distribution has not begun, destination_class must have an explicit semantic state rather than disappearing silently.

Proposed baseline value:
- PRE_DISTRIBUTION_UNRESOLVED

This value means no route/destination has yet been evaluated. It is not a failed destination and not authorization to publish.

## 10. Execution Observability Family

A dedicated canonical event family should represent the post-FSM signal-engine execution result.

Proposed name:
- signal_execution_result

This event must remain distinct from:
- decision_evaluated / decision_promoted / decision_rejected
- fsm_transition
- signal_emitted / signal_stage_visible
- route_publish_attempt / route_publish_result

## 11. signal_execution_result Minimum Semantics

Required correlation/context:
- execution_attempt_id
- stage where applicable
- signal_id where applicable
- symbol
- timestamp

Required payload semantics:
- execution_outcome
- execution_reason
- candidate_handoff_ready
- signal_event_available
- destination_class
- payload_reference or structured candidate summary where available

Optional structured evidence may include:
- DecisionObject reference/summary
- FSM verdict summary
- persistent transition summary
- blocker detail

The event must not convert execution truth into strategy truth.

## 12. PRE / CONFIRM / OPEN_NOW Handling

### PRE
- may form SignalEvent after explicit FSM acceptance;
- does not consume route entitlement by itself;
- external visibility still depends on downstream route policy.

### CONFIRM
- may form SignalEvent after explicit FSM acceptance and stable identity continuity;
- external visibility still depends on downstream route policy.

### OPEN_NOW
- may form SignalEvent only after valid lifecycle path, focus/actionability requirements and explicit FSM acceptance;
- OPEN_NOW SignalEvent is not proof of publication;
- successful external publication must be proven separately by distribution/publisher observability.

## 13. Duplicate and Restart Safety

This proposal does not weaken existing dedup rules.

Minimum boundaries remain:
- engine-side stage dedup must prevent duplicate release of the same actionable stage/candle opportunity;
- distribution-side dedup remains route + signal_id + stage or stronger;
- restart must not reclassify previously released stages as new without canonical reason;
- duplicate suppression must be observable.

## 14. Forbidden Patterns

Forbidden:
- DecisionObject -> SignalEvent without FSM acceptance
- PRE/CONFIRM/OPEN_NOW release based only on function success
- treating transition_event existence as release permission
- SignalEvent creation == Telegram publish permission
- using generic decision debug as the only canonical execution-result record
- calling distribution router from this documentation remediation
- enabling broker execution through this contract

## 15. Promotion Requirements

Before this proposal can become active canonical truth:
1. affected active specs must be versioned or explicitly amended through governance;
2. CANONICAL_MASTER_INDEX must unambiguously identify the active authority set;
3. CANONICAL_STRATEGY_STACK must identify the resulting authority/order if this document becomes a root/subordinate contract;
4. EVENT_SCHEMA_SPEC must define the adopted execution-result family;
5. MODULE_INTERFACE_SPEC must align the FSM-to-engine handoff object semantics;
6. OBSERVABILITY specifications must align event purpose and correlation obligations;
7. no active old and new documents may simultaneously claim conflicting authority.

## 16. No-Code Rule

No runtime implementation is authorized merely by the existence or merge of this proposed document.

Code may be changed only after the intended canonical truth is promoted into the active canonical set and re-audited.
