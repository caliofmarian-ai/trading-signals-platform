# SIGNAL_ENGINE_EXECUTION_SPEC_v3.0.0

Version: 3.0.0
Status: PROPOSED — NOT ACTIVE CANONICAL
Supersession intent: SIGNAL_ENGINE_EXECUTION_SPEC_v2.0.0.md

All v2.0.0 truths remain inherited except where this proposed version clarifies staged SignalEvent construction and execution-result observability.

## 1. Required Input

Signal engine consumes explicit post-FSM operational handoff semantics, not DecisionObject as primary execution authority.

For PRE, CONFIRM and OPEN_NOW, signal engine must require candidate_handoff_ready=true for the same stage before constructing SignalEvent.

## 2. SignalEvent Construction

SignalEvent may be constructed for PRE, CONFIRM or OPEN_NOW only when:
- actionable DecisionObject exists;
- stable signal_id exists;
- FSM accepted the same requested stage;
- candidate_handoff_ready=true;
- payload can be constructed coherently from real evidence;
- no execution blocker prevents candidate construction.

## 3. Construction Is Not Delivery

SignalEvent construction creates an internal engine-to-distribution candidate only.

It does not authorize:
- route selection
- entitlement
- Telegram publication
- outcome registration
- broker execution

## 4. Execution Outcomes

Required families remain:
- EMITTED
- NOT_EMITTED
- BLOCKED
- SKIPPED
- FAILED
- DEFERRED

These must remain distinct from strategy and FSM outcomes.

## 5. Pre-Distribution DEFERRED

When a valid SignalEvent exists but downstream distribution is intentionally disabled/not invoked, execution may be DEFERRED with an explicit reason.

It must not be represented as EMITTED or externally visible.

## 6. Minimum Execution Trace

Every materially relevant execution attempt must preserve:
- execution_attempt_id
- signal/setup correlation identity
- symbol
- timeframe where applicable
- stage where applicable
- execution_outcome
- reason/blocker/failure detail
- timestamp
- destination_class
- candidate/payload reference when available

Before routing begins, destination_class must explicitly represent unresolved pre-distribution state rather than being silently absent.

Baseline proposed value:
- PRE_DISTRIBUTION_UNRESOLVED

## 7. Execution Observability Event

Signal engine must emit a dedicated execution-result event family aligned with EVENT_SCHEMA_SPEC_v3.0.0 proposal:
- signal_execution_result

A generic decision debug blob cannot be the only canonical evidence for signal-engine execution truth.

## 8. Stage Handling

PRE:
- may become SignalEvent after explicit FSM acceptance.

CONFIRM:
- may become SignalEvent after explicit FSM acceptance and continuity validation.

OPEN_NOW:
- may become SignalEvent only after valid canonical lifecycle/focus requirements and explicit FSM acceptance.

External publication remains downstream.

## 9. Forbidden Paths

Still forbidden:
- strategy -> signal direct
- score -> signal direct
- DecisionObject -> SignalEvent without FSM acceptance
- transition-event existence -> automatic SignalEvent
- SignalEvent -> Telegram direct bypassing distribution router
- SignalEvent construction treated as delivery success

## 10. Promotion Preconditions

Before activation:
- FSM_DECISION_ENGINE_SPEC_v2.0.0 proposal must align;
- MODULE_INTERFACE_SPEC_v3.0.0 proposal must align;
- EVENT_SCHEMA_SPEC_v3.0.0 proposal must align;
- OBSERVABILITY specs must align;
- root manifest/master index must promote this authority unambiguously.
