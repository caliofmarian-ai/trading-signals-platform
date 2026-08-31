# CHANGE_PROPOSAL_SIGNAL_EXECUTION_OBSERVABILITY_CANON_REMEDIATION_2026-08-31

Status: PROPOSED — OWNER APPROVED FOR CANONICAL DOCS REMEDIATION
Date: 2026-08-31

CHANGE_ID: 20260831-01
TITLE: Canonical remediation for staged SignalEvent execution and post-FSM execution observability
TYPE: MAJOR / STRUCTURAL LOGIC CHANGE
OWNER: BinaryBot / DROPi Signals Owner
REQUESTED_BY: Owner
APPROVAL_STATUS: OWNER APPROVED FOR CANONICAL DOCUMENT REMEDIATION ONLY

## TARGET_DOCS

Primary:
- send/docs/canonical/active/FSM_DECISION_ENGINE_SPEC_v1.0.0.md
- send/docs/canonical/active/SIGNAL_ENGINE_EXECUTION_SPEC_v2.0.0.md
- send/docs/canonical/active/OBSERVABILITY_SPEC_v2.0.0.md
- send/docs/canonical/active/OBSERVABILITY_LOGGING_SPEC_v2.0.0.md
- send/docs/canonical/active/EVENT_SCHEMA_SPEC_v2.0.0.md
- send/docs/canonical/active/MODULE_INTERFACE_SPEC_v2.0.0.md
- send/docs/canonical/active/CANONICAL_MASTER_INDEX_v1.0.0.md

Cross-check only unless contradiction requires explicit patch:
- send/docs/canonical/active/CANONICAL_STRATEGY_STACK_v1.0.0.md
- send/docs/canonical/active/SIGNAL_DISTRIBUTION_ARCHITECTURE_v2.0.0.md
- send/docs/canonical/active/SIGNAL_DISTRIBUTION_SPEC_v2.0.0.md
- send/docs/canonical/active/SYSTEM_INVARIANTS_v2.0.0.md
- send/docs/canonical/active/DECISION_AUDIT_SPEC_v2.0.0.md
- send/docs/canonical/active/TEST_PLAN_v2.0.0.md
- send/docs/canonical/active/DEPLOYMENT_PROTOCOL_v2.0.0.md

## TARGET_CODE

No code is authorized by this proposal.

Future code surfaces, only after the canonical docs-only remediation is merged and re-audited:
- send/core/v2_fsm_orchestrator.py
- send/core/signal_execution_gate.py
- send/core/signal_engine.py
- send/core/signal_event.py
- send/schema/event_schema.json
- affected tests

## RATIONALE

Audit of PR #73 against the latest active canonical stack exposed a structural gap between existing code and canonical contracts, and a smaller gap inside the canonical observability/event-schema layer itself.

Confirmed active canonical truths:
1. DecisionObject is produced before FSM.
2. Signal engine consumes post-FSM operational semantics.
3. SignalEvent is the canonical engine-to-distribution object.
4. PRE, CONFIRM and OPEN_NOW are governed lifecycle stages and must preserve one stable signal identity.
5. Distribution is downstream and must not invent signal validity.
6. Execution outcomes must distinguish EMITTED, NOT_EMITTED, BLOCKED, SKIPPED, FAILED and DEFERRED.
7. Observability must keep strategic truth, FSM truth, execution truth and distribution truth distinguishable.

Current implementation drift:
- the post-FSM execution gate currently materializes SignalEvent only for OPEN_NOW;
- PRE and CONFIRM may update FSM state but do not reach the engine-to-distribution SignalEvent contract;
- the persistent FSM adapter does not yet expose an explicit canonical accepted-stage semantic distinct from no-op/blocker transition evidence such as cooldown_active, watchlist_full, duplicate stage, or continuity failure;
- runtime event_schema.json still carries legacy/generic names and mechanics that do not fully match EVENT_SCHEMA_SPEC_v2.0.0;
- EVENT_SCHEMA_SPEC_v2.0.0 defines decision, signal lifecycle and route events but does not explicitly define a dedicated post-FSM signal-execution-result event for NOT_EMITTED/BLOCKED/SKIPPED/FAILED/DEFERRED outcomes.

## PROPOSED CANONICAL DIRECTION

The canonical docs-only remediation should establish the following truths before any code work:

1. FSM stage acceptance
   - FSM output must distinguish whether a governed actionable stage was actually accepted for engine handoff.
   - Transition evidence that represents a blocker, suppression, duplicate, invalid continuity or non-progression must not be treated as accepted stage release merely because the FSM call returned without raising.

2. SignalEvent construction boundary
   - SignalEvent remains the canonical engine-to-distribution object.
   - PRE, CONFIRM and OPEN_NOW may each form a SignalEvent only when the corresponding post-FSM operational result explicitly accepts that stage for handoff.
   - Stable signal_id continuity across the same trade idea is mandatory.
   - SignalEvent creation does not itself authorize distribution.

3. Execution truth separation
   - The signal engine must expose a dedicated post-FSM execution result distinct from strategy decision truth and distribution truth.
   - The execution-result semantics must support at least EMITTED, NOT_EMITTED, BLOCKED, SKIPPED, FAILED and DEFERRED.

4. Canonical execution observability event
   - A dedicated event family must be defined for post-FSM execution results before runtime event-schema code is changed.
   - Proposed semantic name: signal_execution_result.
   - Final naming belongs to the canonical docs remediation and must be versioned if adopted.

5. Minimum execution trace
   - execution_attempt_id
   - setup/signal correlation identity
   - stage
   - execution outcome family
   - reason/blocker/failure detail
   - timestamp
   - destination/channel class, including an explicit pre-distribution/not-resolved state when routing has not begun
   - payload or payload reference when available

6. Distribution remains separate
   - No distribution router call is authorized by this remediation.
   - No Telegram publication, outcome registration or broker execution is authorized.
   - Distribution authorization remains governed by the distribution canon and requires its own later implementation step.

## EXPECTED_IMPACT

- Remove ambiguity between strategic, FSM, execution and distribution states.
- Restore PRE/CONFIRM/OPEN_NOW lifecycle compatibility with the canonical SignalEvent handoff model.
- Make non-emission and blocker outcomes structurally observable without hiding them inside generic decision debug payloads.
- Prevent false readiness caused by transition events that are actually blockers/no-ops.
- Provide a stable canonical basis for a later code remediation PR.

## RISK

Primary risks:
- accidental widening of signal visibility if stage acceptance semantics are defined too broadly;
- lifecycle duplication if PRE/CONFIRM handoff is enabled without canonical dedup/restart continuity;
- event-schema compatibility break if event families are changed without versioning/migration discipline;
- conflating internal SignalEvent creation with external distribution authorization.

Mitigations:
- docs-first change only;
- explicit fail-closed acceptance semantics;
- no distribution activation in the remediation;
- schema version discipline;
- re-audit before code modification.

## BLAST_RADIUS

Canonical documentation and later implementation contracts for:
- DecisionObject-to-FSM handoff
- FSM-to-signal-engine handoff
- SignalEvent construction
- execution observability
- event schema validation

No market strategy mathematics, thresholds, channel entitlement policy, Telegram UX, outcome handling, broker execution, or scan cadence is to be changed by this remediation.

## VALIDATION_METHOD

Canonical docs phase:
1. Cross-check every changed document against CANONICAL_STRATEGY_STACK and CANONICAL_MASTER_INDEX authority rules.
2. Verify no contradiction with SIGNAL_DISTRIBUTION_ARCHITECTURE, SIGNAL_DISTRIBUTION_SPEC and SYSTEM_INVARIANTS.
3. Verify terminology is stable across FSM, signal engine, observability, module interface and event schema docs.
4. Verify active-version inventory and supersession status are unambiguous.

Future implementation phase only after docs approval:
1. Unit tests for accepted vs blocked PRE/CONFIRM/OPEN_NOW handoff.
2. Stable signal_id continuity tests.
3. SignalEvent construction tests for each actionable stage.
4. Execution-result event-schema tests.
5. No-distribution regression tests.
6. Restart/dedup safety tests where affected.
7. Runtime observability proof before any distribution handoff PR.

## ROLLBACK_PLAN

Docs phase:
- Do not merge the docs-only remediation if cross-document re-audit fails.
- Existing active canon remains authoritative until the new versioned canonical documents are explicitly promoted.

Future code phase:
- Code changes must be isolated in a separate PR so they can be reverted independently.
- PR #73 remains blocked until the docs-only remediation is merged and the implementation plan is re-derived from the resulting active canon.

## DEPLOYMENT_PLAN

No deployment in this proposal.

Any future code deployment must follow DEPLOYMENT_PROTOCOL_v2.0.0 after canonical alignment and tests.

## MONITORING_WINDOW

Not applicable to docs-only proposal.

A future implementation change must define a bounded runtime validation window covering:
- PRE/CONFIRM/OPEN_NOW execution traces;
- no false external delivery;
- no duplicate lifecycle release;
- restart-safe continuity;
- schema-valid observability.

## SUCCESS_CRITERIA

- Canonical docs unambiguously define accepted-stage handoff for PRE/CONFIRM/OPEN_NOW.
- Canonical docs define a dedicated post-FSM execution-result observability family.
- Execution trace requirements are structurally representable before routing exists.
- SignalEvent construction and distribution authorization are explicitly separate.
- No code is changed before this canonical truth is promoted and re-audited.

## FAILURE_TRIGGERS

Stop remediation and return to Owner review if:
- canonical documents disagree on PRE/CONFIRM/OPEN_NOW eligibility;
- proposed event semantics blur strategy/FSM/execution/distribution truth;
- schema migration would silently reinterpret historical evidence;
- a proposed docs patch implicitly authorizes distribution or broker execution;
- active-version authority becomes ambiguous.
