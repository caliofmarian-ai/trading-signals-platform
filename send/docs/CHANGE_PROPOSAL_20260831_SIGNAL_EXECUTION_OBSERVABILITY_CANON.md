# CHANGE PROPOSAL — Staged SignalEvent Handoff and Signal-Execution Observability

CHANGE_ID: 20260831-01  
TITLE: Canonical remediation for staged SignalEvent handoff and signal-execution observability  
TYPE: MAJOR — structural contract / event-contract remediation  
OWNER: BinaryBot / DROPi Signals  
REQUESTED_BY: Owner-directed canonical audit  
DATE: 2026-08-31  
APPROVAL_STATUS: PROPOSED — OWNER REVIEW REQUIRED  

> This document is a governance proposal only. It is not an active canonical specification, does not modify `canonical/active`, and does not authorize code, distribution, Telegram publication, outcome registration, or broker execution by itself.

---

## 1. PURPOSE

This proposal records canonical drift discovered while reviewing PR #73 after merge of PR #72. The review was performed under the active authority hierarchy beginning with `CANONICAL_MASTER_INDEX_v1.0.0.md` and `CANONICAL_STRATEGY_STACK_v1.0.0.md`.

The purpose is to resolve the canonical contract before any further code modification.

No implementation work governed by this proposal may begin until the relevant canonical documents explicitly describe the intended truth and the proposal is approved through governance.

---

## 2. TARGET DOCS

Canonical documents requiring review and, if this proposal is approved, versioned remediation where semantic contract changes are required:

- `send/docs/canonical/active/EVENT_SCHEMA_SPEC_v2.0.0.md`
- `send/docs/canonical/active/OBSERVABILITY_LOGGING_SPEC_v2.0.0.md`
- `send/docs/canonical/active/MODULE_INTERFACE_SPEC_v2.0.0.md`
- `send/docs/canonical/active/DECISION_AUDIT_SPEC_v2.0.0.md` — only for consistency if needed
- `send/docs/canonical/active/CANONICAL_MASTER_INDEX_v1.0.0.md` — only after an approved version is promoted into the active canonical set

Canonical documents that currently establish the controlling architecture and are expected to remain authoritative unless the approved remediation proves that a versioned clarification is necessary:

- `CANONICAL_STRATEGY_STACK_v1.0.0.md`
- `FSM_DECISION_ENGINE_SPEC_v1.0.0.md`
- `SIGNAL_ENGINE_EXECUTION_SPEC_v2.0.0.md`
- `OBSERVABILITY_SPEC_v2.0.0.md`
- `SIGNAL_DISTRIBUTION_ARCHITECTURE_v2.0.0.md`
- `SIGNAL_DISTRIBUTION_SPEC_v2.0.0.md`
- `SYSTEM_INVARIANTS_v2.0.0.md`
- `GOVERNANCE_AND_CHANGE_CONTROL_v2.0.0.md`
- `TEST_PLAN_v2.0.0.md`
- `DEPLOYMENT_PROTOCOL_v2.0.0.md`

---

## 3. TARGET CODE — AFTER CANON APPROVAL ONLY

No code change is authorized by this proposal.

If and only if the canonical remediation is approved and promoted first, the later implementation scope may include:

- `send/core/v2_fsm_orchestrator.py`
- `send/core/signal_execution_gate.py`
- `send/core/signal_engine.py`
- `send/core/signal_event.py` only if the approved canonical contract requires adjustment
- `send/schema/event_schema.json`
- relevant canonical unit/integration/replay tests

PR #73 must remain blocked until this canonical contract is resolved. Its current implementation may be replaced, amended, or closed depending on the approved canonical result.

---

## 4. RATIONALE

The audit found four connected drift classes.

### 4.1 Staged SignalEvent handoff drift

The active distribution architecture defines the runtime path:

`Decision Object -> FSM Runtime -> Signal Event -> Distribution Router`

The active distribution policy defines the governed visible lifecycle:

`PRE -> CONFIRM -> OPEN_NOW`

`MODULE_INTERFACE_SPEC_v2.0.0.md` defines `SignalEvent` as the canonical engine-to-distribution object, and the current V2 `SignalEvent` implementation validates PRE, CONFIRM and OPEN_NOW.

However, the post-PR-#72 execution gate constructs a `SignalEvent` only when `PersistentFSMResult.candidate_ready` is true, while the current V2 FSM orchestrator sets `candidate_ready=true` only for OPEN_NOW. Valid PRE and CONFIRM transitions therefore cannot currently become staged SignalEvent candidates through this gate.

### 4.2 FSM acceptance semantics are insufficiently explicit

It is not safe to fix 4.1 by marking every PRE or CONFIRM as candidate-ready.

The current persistence FSM can return operational blockers such as:

- `cooldown_active`
- `watchlist_full`
- signal-identity continuity failure
- canonical PRE-path failure
- duplicate stage/candle conditions

The canonical execution layer requires explicit separation among accepted progression, blocked progression, non-emission and duplicate/flow suppression. Therefore the FSM-to-signal-engine handoff must explicitly represent whether the requested stage was operationally accepted for downstream SignalEvent construction.

### 4.3 Runtime event schema is behind the active canonical event schema

The active `EVENT_SCHEMA_SPEC_v2.0.0.md` defines semantic event families including:

- `decision_evaluated`
- `decision_promoted`
- `decision_rejected`
- `decision_no_signal`
- `signal_emitted`
- `signal_stage_visible`
- `route_publish_attempt`
- `route_publish_result`

The runtime `send/schema/event_schema.json` still defines legacy/generic families such as:

- `decision`
- `signal_event`
- `tier_publish`
- `tier_reset`

PR #73 attempted to fit strategy, FSM and execution material into `decision.data.debug` so the current runtime validator would accept the event. This is technically compatible with the drifted runtime schema, but it does not resolve the canonical drift and risks making the legacy schema the hidden source of truth.

### 4.4 Canonical gap for non-emitted signal-execution verdicts

`SIGNAL_ENGINE_EXECUTION_SPEC_v2.0.0.md` requires explicit execution outcome families:

- `EMITTED`
- `NOT_EMITTED`
- `BLOCKED`
- `SKIPPED`
- `FAILED`
- `DEFERRED`

`OBSERVABILITY_SPEC_v2.0.0.md` requires the execution outcome to remain semantically distinct from strategic truth and FSM truth.

`EVENT_SCHEMA_SPEC_v2.0.0.md` defines `signal_emitted`, but it does not currently define a dedicated post-FSM signal-execution event family capable of representing all non-emitted execution outcomes without falsely calling them a strategy decision or an emitted signal.

This is a canonical specification gap. Code must not invent the missing event family before the canon does.

---

## 5. PROPOSED CANONICAL DECISIONS

The following are proposals, not active truth until approved and promoted.

### CP-001 — Stage acceptance must be explicit at the FSM-to-engine boundary

For PRE, CONFIRM and OPEN_NOW, the post-FSM handoff must distinguish at minimum:

- stage operationally accepted for downstream SignalEvent construction
- duplicate/suppressed stage
- stage blocked by cooldown/focus/watchlist/policy/invariant
- stage rejected because lifecycle or signal identity is invalid
- no actionable stage

A transition event existing by itself must not be treated as proof that a stage is accepted.

### CP-002 — PRE, CONFIRM and OPEN_NOW may each form a SignalEvent only after FSM acceptance

When the FSM explicitly accepts an actionable stage, the signal engine may construct a canonical SignalEvent for that same stage.

Rules:

- SignalEvent stage must equal the originating accepted stage.
- PRE, CONFIRM and OPEN_NOW for the same trade idea must preserve the same governed `signal_id`.
- A blocked, duplicate, cooldown-suppressed, invalid-continuity or invalid-lifecycle stage must not create a distribution-eligible SignalEvent.
- SignalEvent creation is not equivalent to external publication.

### CP-003 — Add a dedicated post-FSM execution-observability event family

A versioned event-schema update should define a canonical event family provisionally named:

`signal_execution_result`

The final canonical name must be selected during document approval, but its semantic purpose must be unambiguous: record the signal engine's execution verdict after FSM and before/through delivery orchestration, including cases where no signal is emitted.

Minimum semantic content should include:

- execution attempt identity
- setup / signal correlation identity where applicable
- symbol
- timeframe / relevant temporal context
- stage where applicable
- execution outcome family: `EMITTED | NOT_EMITTED | BLOCKED | SKIPPED | FAILED | DEFERRED`
- reason / blocker / failure detail
- event timestamp
- destination or channel class, including an explicit pre-distribution/unresolved value when destination selection has not yet occurred
- payload, payload version, or payload reference as applicable
- enough FSM handoff reference to prove the verdict was post-FSM

This event must not replace decision audit, FSM transition events, distribution-route events, or actual signal-emission proof.

### CP-004 — Preserve truth-layer separation

- `decision_evaluated` remains pre-FSM strategy truth.
- FSM events remain FSM/state truth.
- the proposed execution event remains signal-engine execution truth.
- `signal_emitted` may only represent actual governed emission under its approved semantics.
- distribution publish events remain route/destination truth.

Strategy, FSM and execution outcomes must not be hidden inside one opaque generic `debug` blob as the canonical model.

### CP-005 — Runtime event schema must be aligned before PR #73 runtime integration

`send/schema/event_schema.json` must not remain the hidden legacy authority. The runtime validator must be aligned to the approved versioned canonical event schema before the execution-observability integration is considered complete.

Compatibility aliases may exist only if explicitly documented as transitional and must not replace canonical event names/semantics.

### CP-006 — Distribution stays disabled during this remediation

This remediation must not:

- call `distribution_router.route()` for live signal delivery
- send PRE, CONFIRM or OPEN_NOW to Telegram
- register trade outcomes
- enable broker execution
- alter trading strategy mathematics
- alter the 2-second scan cadence

Actual distribution activation remains a separate governed change after staged handoff and observability have been validated.

### CP-007 — No false LIVE_SENT state

OPEN_NOW candidacy or SignalEvent construction must not by itself mark the lifecycle as successfully delivered. Any sent/live state must require the canonically approved delivery success boundary.

---

## 6. EXPECTED IMPACT

If approved and implemented in the governed order, this change should:

- remove the mismatch between the staged PRE/CONFIRM/OPEN_NOW distribution lifecycle and the current OPEN_NOW-only execution candidate gate
- prevent blocked PRE/CONFIRM transitions from being mistaken for accepted stages
- create an explicit, reconstructable post-FSM execution truth
- stop using the generic legacy `decision` event as a container for mixed strategy/FSM/execution truth
- align runtime schema validation with active canonical event semantics
- preserve distribution, Telegram and broker safety while the internal handoff is validated

---

## 7. RISK

Primary risks:

1. Event-schema compatibility risk for existing log consumers and tests that still expect legacy names.
2. FSM semantic risk if acceptance is inferred incorrectly from transition events.
3. Lifecycle duplication risk if PRE/CONFIRM/OPEN_NOW candidate creation is not stage-idempotent.
4. Observability ambiguity if strategy, FSM, execution and distribution truths are not kept separate.
5. Versioning risk if active canonical files are mutated in place instead of being superseded through the governance process.
6. Deployment risk if schema changes reach production without DEV/STAGING validation and rollback evidence.

---

## 8. BLAST RADIUS

Intended blast radius after approval:

- canonical event-contract documentation
- module-interface documentation where required
- V2 persistent FSM handoff semantics
- SignalEvent staging gate
- signal-engine observability integration
- runtime event schema
- associated tests and replay/validation evidence

Explicitly outside blast radius:

- strategy mathematics
- scoring model
- corridor model
- time model mathematics
- adjustable trading thresholds
- market-data provider logic
- 2-second scan cadence
- external signal distribution activation
- Telegram publication activation
- broker execution

---

## 9. VALIDATION METHOD

### 9.1 Canonical validation before code

- confirm versioned canonical event family for post-FSM execution truth
- confirm PRE/CONFIRM/OPEN_NOW SignalEvent handoff semantics
- confirm FSM accepted/blocked/duplicate semantics
- confirm module ownership boundaries
- confirm observability truth-layer separation
- update authoritative master index only when a replacement canonical version is promoted

### 9.2 Implementation validation after canon approval

Required unit/integration cases should include at minimum:

- valid PRE after FSM acceptance -> PRE SignalEvent candidate, no external delivery
- valid CONFIRM with stable identity -> CONFIRM SignalEvent candidate, no external delivery
- valid OPEN_NOW through canonical PRE/focus path -> OPEN_NOW SignalEvent candidate, no external delivery
- cooldown-active PRE/CONFIRM/OPEN_NOW -> blocked/suppressed outcome, no SignalEvent candidate
- watchlist-full PRE without valid replacement -> blocked/suppressed outcome, no SignalEvent candidate
- duplicate same stage/candle -> duplicate/suppressed outcome, no duplicate candidate
- CONFIRM/OPEN_NOW identity discontinuity -> blocked/rejected, no candidate
- OPEN_NOW without canonical PRE path -> blocked, no candidate
- incomplete real model evidence -> non-emission/failure family according to approved contract, never fabricated data
- each execution result validates against the approved runtime event schema
- strategy decision event remains separate from execution result event
- distribution route is never called in this remediation phase
- Telegram/outcome/broker surfaces remain untouched
- scan cadence remains unchanged

### 9.3 Regression / replay

Execute the relevant canonical test categories from `TEST_PLAN_v2.0.0.md`, including:

- DecisionObject/pipeline-order validation
- FSM lifecycle/invariant validation
- observability/audit-trail validation
- distribution-safety validation
- restart/persistence validation where state semantics change
- replay/regression validation

No production trust may be claimed solely from code review or a passing narrow unit test.

---

## 10. ROLLBACK PLAN

Proposal stage:
- closing this proposal PR has no runtime effect
- no active canonical file or code is changed by the proposal itself

Canonical-remediation stage:
- new canonical versions must preserve prior versions as superseded/historical evidence
- promotion must be reversible through the canonical index/governance process

Implementation stage:
- implementation must be a separate PR after canonical promotion
- branch/commit boundary must permit clean revert
- no external distribution activation may be bundled with the remediation

Deployment stage:
- follow `DEPLOYMENT_PROTOCOL_v2.0.0.md`
- preserve pre-deploy state/evidence
- define exact rollback commit and restart procedure before deployment

---

## 11. DEPLOYMENT PLAN

1. Owner reviews this proposal.
2. If approved, prepare versioned canonical document replacements/clarifications first.
3. Review and promote the canonical-document PR according to governance.
4. Update the authoritative master index to the promoted versions.
5. Re-audit the intended code change exclusively against the newly active canonical set.
6. Implement the FSM handoff, event schema and signal-engine observability in a separate code PR.
7. Execute required DEV/STAGING validation and regression evidence.
8. Deploy only the internal handoff/observability remediation under controlled protocol.
9. Validate bounded Railway runtime evidence and restart behavior.
10. Keep external distribution disabled.
11. Treat actual distribution activation as a separate future change proposal / deployment scope.

---

## 12. MONITORING WINDOW

The implementation monitoring window must be defined before deployment and should include a bounded sample of:

- actionable PRE lifecycle events
- actionable CONFIRM lifecycle events
- actionable OPEN_NOW candidate events if naturally produced
- blocked/suppressed lifecycle cases
- at least one controlled restart/persistence check if FSM semantics are modified
- schema-valid execution-result events across the relevant outcome families

This phase must not require or permit real subscriber signal delivery as proof.

---

## 13. SUCCESS CRITERIA

Success requires all of the following:

- active canonical documents unambiguously define staged SignalEvent handoff and post-FSM execution observability
- runtime schema matches the approved canonical event contract
- PRE, CONFIRM and OPEN_NOW can each be represented after valid FSM acceptance
- blocked or duplicate stages cannot form distribution candidates
- stable signal identity is preserved across lifecycle stages
- execution outcomes remain distinct from strategy/FSM/distribution truths
- delivery trace contains all canonically required correlation and destination/payload semantics
- no false `LIVE_SENT` state is produced before delivery success
- no distribution/Telegram/outcome/broker activation occurs in this remediation phase
- validation evidence meets the applicable `TEST_PLAN_v2.0.0.md` scope

---

## 14. FAILURE TRIGGERS

The change must stop and return to canonical review if any of the following occurs:

- canonical documents remain ambiguous or contradictory about the execution event family
- an accepted-stage rule cannot distinguish cooldown/watchlist/duplicate blockers
- strategy, FSM and execution truth are still combined into one opaque event
- a blocked stage produces a SignalEvent candidate
- signal identity changes across PRE/CONFIRM/OPEN_NOW for the same opportunity
- runtime schema accepts behavior that the active canonical event spec does not define
- any code path performs external distribution during this remediation
- OPEN_NOW candidacy is persisted as successful live delivery without delivery proof
- required regression/replay or restart-safety evidence fails

---

## 15. CANONICAL EVIDENCE BASIS

This proposal is derived from the active canonical authority chain and current runtime state:

- `CANONICAL_MASTER_INDEX_v1.0.0.md` — authoritative inventory and precedence
- `CANONICAL_STRATEGY_STACK_v1.0.0.md` — root strategy flow and patch/audit order
- `FSM_DECISION_ENGINE_SPEC_v1.0.0.md` — post-DecisionObject operational semantics and handoff
- `SIGNAL_ENGINE_EXECUTION_SPEC_v2.0.0.md` — execution gating, outcome families and delivery trace requirement
- `SIGNAL_DISTRIBUTION_ARCHITECTURE_v2.0.0.md` — Signal Event -> Distribution Router architecture and PRE/CONFIRM/OPEN_NOW scope
- `SIGNAL_DISTRIBUTION_SPEC_v2.0.0.md` — stable lifecycle identity and PRE -> CONFIRM -> OPEN_NOW governance
- `EVENT_SCHEMA_SPEC_v2.0.0.md` — active semantic event families and versioning rules
- `OBSERVABILITY_SPEC_v2.0.0.md` — end-to-end truth-layer separation and signal-execution observability requirements
- `OBSERVABILITY_LOGGING_SPEC_v2.0.0.md` — implementation-level observability obligations
- `MODULE_INTERFACE_SPEC_v2.0.0.md` — SignalEvent engine-to-distribution contract and module ownership
- `SYSTEM_INVARIANTS_v2.0.0.md` — documentation supremacy, lifecycle, cooldown, identity, schema and logging invariants
- `GOVERNANCE_AND_CHANGE_CONTROL_v2.0.0.md` — structural change proposal, docs-first and approval requirements
- `TEST_PLAN_v2.0.0.md` — required validation evidence
- `DEPLOYMENT_PROTOCOL_v2.0.0.md` — docs-first major deployment preconditions

Runtime evidence reviewed:

- `send/core/signal_event.py`
- `send/core/v2_fsm_orchestrator.py`
- `send/core/fsm_runtime.py`
- `send/core/signal_execution_gate.py`
- `send/schema/event_schema.json`
- PR #73 diff

---

## 16. APPROVAL RECORD

Current status: **PROPOSED — OWNER REVIEW REQUIRED**

Approval has not been inferred from prior implementation work or from PR mergeability.

If approved, the next artifact is a **canonical-documents-only remediation PR**. Code remains frozen until the new active canonical truth is promoted and re-audited.
