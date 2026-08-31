# MODULE_INTERFACE_SPEC_v3.0.0

Version: 3.0.0
Status: PROPOSED DESIGN DELTA — NOT ACTIVE CANONICAL — NOT PROMOTION READY
Supersession intent: MODULE_INTERFACE_SPEC_v2.0.0.md

This file records the approved interface delta. A promoted successor must be materialized as a complete self-contained module-interface specification.

## 1. Proposed Shared Contract: FSMExecutionHandoff

Minimum semantics:
- requested_stage: str | None
- accepted_stage: str | None
- signal_id: str | None
- state_changed: bool
- reason: str
- reason_family: str | None
- transition_event: dict | None
- stage_handoff_ready: bool
- trade_execution_ready: bool

Rules:
- requested_stage reflects the actionable DecisionObject stage under evaluation.
- accepted_stage is populated only if that exact stage is operationally released.
- stage_handoff_ready=true only when accepted_stage matches requested_stage and no blocker suppresses handoff.
- trade_execution_ready is independent of lifecycle visibility readiness: it must be false for PRE and CONFIRM and may be true only for accepted OPEN_NOW.

## 2. FSM Ownership

FSM domain owns:
- lifecycle state transitions
- invariant enforcement
- stage acceptance/block semantics
- persistence of FSM state
- production of FSMExecutionHandoff semantics

FSM does not own:
- SignalEvent construction
- distribution routing
- Telegram publishing

## 3. Signal Engine Ownership

Signal engine owns:
- scan cadence
- strategy invocation
- FSM invocation
- consumption of FSMExecutionHandoff
- SignalEvent construction after accepted-stage handoff
- engine-level dedup
- signal_execution_result evidence

Signal engine must not construct SignalEvent for PRE/CONFIRM/OPEN_NOW unless stage_handoff_ready=true for the same stage.

Signal engine must not interpret trade_execution_ready=false on PRE/CONFIRM as a reason to suppress their canonical lifecycle SignalEvent solely because they are not final trade-action stages.

## 4. SignalEvent Contract Delta

SignalEvent remains the canonical engine-to-distribution object.

Required stage family:
- PRE
- CONFIRM
- OPEN_NOW

Stage must match accepted_stage from the post-FSM handoff.

SignalEvent creation does not confer distribution permission and does not prove EMITTED.

The eventual complete successor must preserve the existing SignalEvent field contract while reconciling canonical V2 terminology such as buffer_distance and any explicitly documented compatibility aliases.

## 5. Distribution Router Contract

Distribution router continues to receive canonical SignalEvent objects and remains the owner of route selection, entitlement and publish-or-skip decisions.

No change in this proposal authorizes signal_engine to bypass distribution_router.

## 6. Observability Contract

observability_logger must support the proposed execution-result event family after the corresponding event-schema successor is promoted:
- signal_execution_result

It must preserve separate evidence for:
- strategy decision
- FSM transition/handoff
- signal-engine execution result
- distribution publish result

## 7. Fail-Closed Interface Rule

The following must not be treated as positive stage handoff by themselves:
- transition_event exists
- state_changed=true
- function returned without exception
- DecisionObject is actionable

Only explicit stage_handoff_ready=true for the same stage permits SignalEvent construction.

trade_execution_ready must never be inferred from stage_handoff_ready for PRE or CONFIRM.

## 8. Promotion Requirements

Before activation:
- a complete self-contained successor MODULE_INTERFACE specification must be materialized;
- complete FSM and signal-engine successor specs must align;
- EVENT_SCHEMA / OBSERVABILITY successors must align;
- root manifest/master index must be fully updated if version references change;
- runtime code remains unchanged until active promotion and re-audit.
