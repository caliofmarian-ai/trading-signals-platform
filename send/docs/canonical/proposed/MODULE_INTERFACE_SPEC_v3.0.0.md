# MODULE_INTERFACE_SPEC_v3.0.0

Version: 3.0.0
Status: PROPOSED — NOT ACTIVE CANONICAL
Supersession intent: MODULE_INTERFACE_SPEC_v2.0.0.md

All v2.0.0 module ownership rules remain inherited except where this proposed version clarifies the FSM-to-signal-engine handoff contract.

## 1. New Shared Contract: FSMExecutionHandoff

Proposed minimum semantics:
- accepted: bool
- requested_stage: str | None
- accepted_stage: str | None
- signal_id: str | None
- state_changed: bool
- reason: str
- reason_family: str | None
- transition_event: dict | None
- candidate_handoff_ready: bool

Rules:
- requested_stage reflects the actionable DecisionObject stage under evaluation.
- accepted_stage is populated only if that exact stage is operationally released.
- candidate_handoff_ready=true only when accepted_stage matches requested_stage and no blocker suppresses handoff.

## 2. fsm_runtime Ownership

FSM runtime owns:
- lifecycle state transitions
- invariant enforcement
- stage acceptance/block semantics
- persistence of FSM state

FSM runtime does not own:
- SignalEvent construction
- distribution routing
- Telegram publishing

## 3. signal_engine Ownership

Signal engine owns:
- scan cadence
- strategy invocation
- FSM invocation
- consumption of FSMExecutionHandoff
- SignalEvent construction after accepted-stage handoff
- engine-level dedup
- signal_execution_result evidence

Signal engine must not construct SignalEvent for PRE/CONFIRM/OPEN_NOW unless candidate_handoff_ready=true for the same stage.

## 4. SignalEvent Contract

SignalEvent remains the canonical engine-to-distribution object.

Required stage family:
- PRE
- CONFIRM
- OPEN_NOW

Stage must match accepted_stage from the post-FSM handoff.

SignalEvent creation does not confer distribution permission.

## 5. Distribution Router Contract

Distribution router continues to receive canonical distribution-eligible SignalEvent objects and remains the owner of route selection, entitlement and publish-or-skip decisions.

No change in this proposal authorizes signal_engine to bypass distribution_router.

## 6. Observability Contract

observability_logger must support the canonical execution-result event family after EVENT_SCHEMA_SPEC_v3.0.0 is promoted:
- signal_execution_result

It must preserve separate evidence for:
- strategy decision
- FSM transition/handoff
- signal-engine execution result
- distribution publish result

## 7. Fail-Closed Interface Rule

The following must not be treated as positive handoff by themselves:
- transition_event exists
- state_changed=true
- function returned without exception
- DecisionObject is actionable

Only explicit candidate_handoff_ready=true for the same stage permits SignalEvent construction.

## 8. Promotion Preconditions

Before activation:
- proposed FSM and signal-engine specs must align;
- EVENT_SCHEMA_SPEC_v3.0.0 must be promoted;
- root manifest and master index must identify the active versions;
- runtime code remains unchanged until re-audit.
