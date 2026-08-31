# FSM_DECISION_ENGINE_SPEC_v2.0.0

Version: 2.0.0
Status: PROPOSED — NOT ACTIVE CANONICAL
Supersession intent: FSM_DECISION_ENGINE_SPEC_v1.0.0.md

All v1.0.0 truths remain inherited except where this proposed version makes the FSM-to-signal-engine handoff contract explicit.

## 1. Preserved Role

FSM remains the operational consumer of DecisionObject and remains upstream of signal engine. It does not rederive strategy mathematics and does not own distribution.

## 2. Actionable Stage Acceptance

For PRE, CONFIRM and OPEN_NOW, FSM must explicitly expose whether the requested stage was operationally accepted for signal-engine handoff.

Minimum post-FSM semantics:
- accepted: boolean
- requested_stage
- accepted_stage or null
- signal_id where applicable
- state_changed
- reason
- reason_family where available
- transition evidence where available
- candidate_handoff_ready: boolean

candidate_handoff_ready=true only when the requested actionable stage is genuinely released downstream.

## 3. Fail-Closed Handoff

candidate_handoff_ready=false for:
- cooldown_active
- watchlist_full without accepted replacement
- duplicate stage/candle suppression
- signal identity continuity failure
- invalid PRE/CONFIRM/OPEN_NOW lifecycle path
- FSM reject/block
- invariant failure
- no-op transition that does not release the requested stage

Neither normal function return nor transition-event existence is sufficient proof of stage acceptance.

## 4. PRE

PRE may be accepted when watchlist/focus rules permit lifecycle entry or refresh and no blocker suppresses the stage.

An accepted PRE must preserve stable signal identity for subsequent CONFIRM/OPEN_NOW progression.

## 5. CONFIRM

CONFIRM may be accepted only when lifecycle continuity and focus/watchlist state permit confirmation of the same signal identity.

## 6. OPEN_NOW

OPEN_NOW may be accepted only through a valid canonical PRE path, with valid focus/actionability context and stable identity continuity.

OPEN_NOW acceptance releases an execution candidate; it does not itself mark external publication success.

## 7. State vs Visibility

Internal FSM state names such as WATCHLIST or CONFIRMED must not be treated as proof that an external PRE/CONFIRM was published.

External visibility is downstream distribution truth.

## 8. Observability

FSM observability must expose:
- requested stage
- acceptance/rejection/block result
- transition reason
- candidate_handoff_ready
- lifecycle continuity result

## 9. Promotion Preconditions

Before activation:
- SIGNAL_ENGINE_EXECUTION_SPEC must align with candidate_handoff_ready;
- MODULE_INTERFACE_SPEC must define the handoff object;
- EVENT_SCHEMA_SPEC must support separate FSM and execution evidence;
- CANONICAL_STRATEGY_STACK and CANONICAL_MASTER_INDEX must identify this version as active.
