# FSM_DECISION_ENGINE_SPEC_v2.0.0

Version: 2.0.0
Status: PROPOSED DESIGN DELTA — NOT ACTIVE CANONICAL — NOT PROMOTION READY
Supersession intent: FSM_DECISION_ENGINE_SPEC_v1.0.0.md

This file records the approved semantic delta for the FSM domain. It is not eligible for active promotion as written because a promoted successor must be a complete self-contained specification rather than depending normatively on a superseded version.

## 1. Preserved Role

FSM remains the operational consumer of DecisionObject and remains upstream of signal engine. It does not rederive strategy mathematics and does not own distribution.

## 2. Actionable Stage Handoff

For PRE, CONFIRM and OPEN_NOW, FSM must explicitly expose whether the requested stage is operationally released to the signal engine.

Proposed minimum post-FSM semantics:
- requested_stage: PRE | CONFIRM | OPEN_NOW | null
- accepted_stage: PRE | CONFIRM | OPEN_NOW | null
- signal_id where applicable
- state_changed: boolean
- reason
- reason_family where available
- transition evidence where applicable
- stage_handoff_ready: boolean
- trade_execution_ready: boolean

### 2.1 stage_handoff_ready

stage_handoff_ready=true means the exact requested actionable stage has been accepted and released to the signal engine for canonical SignalEvent consideration.

It may be true for PRE, CONFIRM or OPEN_NOW.

### 2.2 trade_execution_ready

trade_execution_ready is a distinct operational truth.

It must be false for PRE and CONFIRM.
It may be true only for an accepted OPEN_NOW stage whose canonical focus/actionability/lifecycle requirements are satisfied.

stage_handoff_ready must never be treated as equivalent to trade_execution_ready.

This distinction allows PRE and CONFIRM to enter the governed signal lifecycle without falsely claiming final trade readiness.

## 3. Fail-Closed Handoff

stage_handoff_ready=false for:
- cooldown_active
- watchlist_full without accepted replacement
- duplicate stage/candle suppression
- signal identity continuity failure
- invalid PRE/CONFIRM/OPEN_NOW lifecycle path
- FSM reject/block
- invariant failure
- no-op transition that does not release the requested stage

Neither normal function return nor transition-event existence is sufficient proof of stage release.

trade_execution_ready must also be false whenever stage_handoff_ready=false.

## 4. PRE

PRE may be released when watchlist/focus rules permit lifecycle entry or refresh and no blocker suppresses the stage.

For an accepted PRE:
- accepted_stage = PRE
- stage_handoff_ready = true
- trade_execution_ready = false

An accepted PRE must preserve stable signal identity for subsequent CONFIRM/OPEN_NOW progression.

## 5. CONFIRM

CONFIRM may be released only when lifecycle continuity and focus/watchlist state permit confirmation of the same signal identity.

For an accepted CONFIRM:
- accepted_stage = CONFIRM
- stage_handoff_ready = true
- trade_execution_ready = false

## 6. OPEN_NOW

OPEN_NOW may be released only through a valid canonical PRE path, with valid focus/actionability context and stable identity continuity.

For an accepted actionable OPEN_NOW:
- accepted_stage = OPEN_NOW
- stage_handoff_ready = true
- trade_execution_ready = true

OPEN_NOW acceptance does not itself mark external publication success and does not authorize broker execution.

## 7. State vs Visibility

Internal FSM state names such as WATCHLIST or CONFIRMED must not be treated as proof that an external PRE/CONFIRM was published.

External visibility is downstream distribution truth.

## 8. Observability

FSM observability must expose enough semantics to distinguish:
- requested stage
- accepted stage
- stage release vs block/suppression
- transition reason
- lifecycle continuity result
- stage_handoff_ready
- trade_execution_ready

## 9. Promotion Requirements

Before this semantic delta can become active canonical truth:
- a complete self-contained successor FSM specification must be materialized;
- SIGNAL_ENGINE_EXECUTION successor must consume stage_handoff_ready rather than an overloaded OPEN_NOW-only candidate flag;
- MODULE_INTERFACE successor must define the shared handoff contract;
- EVENT_SCHEMA / OBSERVABILITY successors must preserve separate FSM and execution evidence;
- the full canonical root manifest/master index must be updated if version references change;
- runtime code remains unchanged until active promotion and re-audit.
