# SIGNAL_ENGINE_EXECUTION_SPEC_v3.0.0

Version: 3.0.0
Status: PROPOSED DESIGN DELTA — NOT ACTIVE CANONICAL — NOT PROMOTION READY
Supersession intent: SIGNAL_ENGINE_EXECUTION_SPEC_v2.0.0.md

This file records the approved semantic delta for the signal-execution domain. A promoted successor must be materialized as a complete self-contained specification.

## 1. Required Input

Signal engine consumes explicit post-FSM operational handoff semantics, not DecisionObject as primary execution authority.

For PRE, CONFIRM and OPEN_NOW, SignalEvent construction requires stage_handoff_ready=true and accepted_stage matching the requested DecisionObject stage.

trade_execution_ready is a separate field and is expected to remain false for PRE/CONFIRM. It may be true only for accepted OPEN_NOW.

## 2. SignalEvent Construction

SignalEvent may be constructed for PRE, CONFIRM or OPEN_NOW only when:
- actionable DecisionObject exists;
- stable signal_id exists;
- FSM accepted the same requested stage;
- stage_handoff_ready=true;
- accepted_stage matches the DecisionObject stage;
- payload can be constructed coherently from real evidence;
- no execution blocker prevents candidate construction.

## 3. Construction Is Not Delivery

SignalEvent construction creates an internal engine-to-distribution candidate only.

It does not authorize or prove:
- route selection
- entitlement
- destination resolution
- Telegram publication
- outcome registration
- broker execution

SignalEvent construction alone must never be classified as EMITTED.

## 4. Execution Outcomes

Required families remain:
- EMITTED
- NOT_EMITTED
- BLOCKED
- SKIPPED
- FAILED
- DEFERRED

These remain distinct from strategy, FSM and per-route distribution outcomes.

## 5. Outcome Semantics

### 5.1 DEFERRED

When a valid SignalEvent exists but downstream distribution is intentionally disabled, not yet invoked, or deliberately deferred, signal-engine execution is DEFERRED with an explicit reason.

Current pre-distribution remediation work must use this family for a valid candidate while distribution remains disabled.

### 5.2 EMITTED

EMITTED requires downstream governed publication evidence confirming that at least one authorized publication succeeded.

SignalEvent construction is insufficient evidence.
FSM acceptance is insufficient evidence.
A route selection without publish success is insufficient evidence.

Exact route-by-route publication truth remains owned by distribution events.

### 5.3 NOT_EMITTED

NOT_EMITTED represents a non-technical non-emission such as insufficient handoff/readiness or inability to form a valid SignalEvent candidate.

### 5.4 BLOCKED

BLOCKED represents an explicit operational or policy blocker.

### 5.5 SKIPPED

SKIPPED represents a flow decision not to proceed despite no technical failure.

### 5.6 FAILED

FAILED represents a technical/infrastructure failure on an execution path that otherwise intended to proceed.

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
- destination context
- candidate/payload reference when available

Before routing begins, destination context must explicitly represent unresolved pre-distribution state rather than being silently absent.

Proposed baseline:
- destination_state = PRE_DISTRIBUTION_UNRESOLVED

If routing later occurs, route/destination details must be linked to canonical distribution evidence rather than invented by signal engine.

## 7. Execution Observability Event

The proposed event-schema successor should define a dedicated execution-result family:
- signal_execution_result

A generic decision debug blob cannot be the only canonical evidence for signal-engine execution truth.

The event may represent a pre-distribution execution checkpoint and, when future distribution is active, a later final execution result correlated by the same execution_attempt_id.

## 8. Stage Handling

PRE:
- may become SignalEvent after explicit FSM stage handoff;
- trade_execution_ready remains false.

CONFIRM:
- may become SignalEvent after explicit FSM stage handoff and continuity validation;
- trade_execution_ready remains false.

OPEN_NOW:
- may become SignalEvent only after valid canonical lifecycle/focus requirements and explicit FSM stage handoff;
- trade_execution_ready may be true;
- external publication remains downstream.

## 9. Forbidden Paths

Still forbidden:
- strategy -> signal direct
- score -> signal direct
- DecisionObject -> SignalEvent without FSM stage handoff
- transition-event existence -> automatic SignalEvent
- stage_handoff_ready -> automatic broker execution
- SignalEvent -> Telegram direct bypassing distribution router
- SignalEvent construction treated as delivery success or EMITTED

## 10. Promotion Requirements

Before activation:
- a complete self-contained successor execution specification must be materialized;
- the complete successor FSM spec must align on stage_handoff_ready and trade_execution_ready;
- the complete successor MODULE_INTERFACE spec must align;
- EVENT_SCHEMA / OBSERVABILITY successors must align;
- root manifest/master index must be fully updated if version references change;
- runtime code remains unchanged until promotion and re-audit.
