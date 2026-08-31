# CHANGE_PROPOSAL_SIGNAL_EXECUTION_OBSERVABILITY_CANON_REMEDIATION_2026-08-31

Status: OWNER APPROVED — CANONICAL DOCS REMEDIATION ONLY
Date: 2026-08-31

CHANGE_ID: 20260831-01
TITLE: Canonical remediation for staged SignalEvent execution and post-FSM execution observability
TYPE: MAJOR / STRUCTURAL LOGIC CHANGE
OWNER: BinaryBot / DROPi Signals Owner
REQUESTED_BY: Owner
APPROVAL_STATUS: OWNER APPROVED FOR CANONICAL DOCUMENT REMEDIATION ONLY

## TARGET_DOCS

Primary active authorities reviewed:
- send/docs/canonical/active/CANONICAL_STRATEGY_STACK_v1.0.0.md
- send/docs/canonical/active/CANONICAL_MASTER_INDEX_v1.0.0.md
- send/docs/canonical/active/SYSTEM_ARCHITECTURE_MAP_v2.0.0.md
- send/docs/canonical/active/FSM_DECISION_ENGINE_SPEC_v1.0.0.md
- send/docs/canonical/active/SIGNAL_ENGINE_EXECUTION_SPEC_v2.0.0.md
- send/docs/canonical/active/OBSERVABILITY_SPEC_v2.0.0.md
- send/docs/canonical/active/OBSERVABILITY_LOGGING_SPEC_v2.0.0.md
- send/docs/canonical/active/EVENT_SCHEMA_SPEC_v2.0.0.md
- send/docs/canonical/active/MODULE_INTERFACE_SPEC_v2.0.0.md
- send/docs/canonical/active/SIGNAL_DISTRIBUTION_ARCHITECTURE_v2.0.0.md
- send/docs/canonical/active/SIGNAL_DISTRIBUTION_SPEC_v2.0.0.md
- send/docs/canonical/active/SYSTEM_INVARIANTS_v2.0.0.md
- send/docs/canonical/active/DECISION_AUDIT_SPEC_v2.0.0.md
- send/docs/canonical/active/GOVERNANCE_AND_CHANGE_CONTROL_v2.0.0.md
- send/docs/canonical/active/TEST_PLAN_v2.0.0.md
- send/docs/canonical/active/DEPLOYMENT_PROTOCOL_v2.0.0.md

## TARGET_CODE

No code is authorized by this proposal.

Future implementation surfaces may only be derived after the intended canonical truth is fully materialized, promoted and re-audited.

## RATIONALE

A fresh audit of PR #73 and merged PR #72 against the latest active canonical stack found:

1. The active architecture requires DecisionObject -> FSM -> signal engine -> delivery/observability.
2. SignalEvent is the canonical engine-to-distribution object.
3. PRE, CONFIRM and OPEN_NOW are governed lifecycle stages sharing stable signal identity.
4. Signal engine execution outcomes must distinguish EMITTED, NOT_EMITTED, BLOCKED, SKIPPED, FAILED and DEFERRED.
5. Observability must keep strategy truth, FSM truth, execution truth and distribution truth distinguishable.
6. Current runtime code only materializes the SignalEvent candidate at OPEN_NOW.
7. Current FSM adapter can return transition evidence such as cooldown_active or watchlist_full without an explicit accepted-stage handoff semantic.
8. EVENT_SCHEMA_SPEC_v2.0.0 does not define a dedicated post-FSM execution-result family for non-emitted execution outcomes.
9. Runtime send/schema/event_schema.json still contains legacy/generic event families and is not the canonical authority.

## DEEP RE-AUDIT CORRECTIONS

A second audit against SYSTEM_ARCHITECTURE_MAP_v2.0.0 found additional governance constraints that refine the approved direction:

1. No new canonical handoff document should become a separate authority. The concern can be absorbed by the already-owned FSM, signal-engine, module-interface and observability/event-schema domains. Creating a separate active handoff canon would duplicate ownership.
2. A future replacement CANONICAL_MASTER_INDEX must remain a complete authoritative inventory. A partial index is not an acceptable successor.
3. A future replacement root strategy manifest must remain a complete self-contained root manifest. A delta-only root document is not promotion-ready.
4. Future successor canonical specs must be self-contained at promotion time. They must not depend normatively on versions that become Superseded.
5. SignalEvent construction is not EMITTED. EMITTED requires downstream governed publication evidence. If a valid SignalEvent exists while distribution is intentionally not invoked, the signal-engine execution outcome is DEFERRED.

These corrections narrow the remediation and prevent new canonical drift.

## REFINED AUTHORITY MODEL

The handoff concern stays inside existing primary homes:

- FSM_DECISION_ENGINE_SPEC: owns actionable-stage acceptance/block/release semantics.
- SIGNAL_ENGINE_EXECUTION_SPEC: owns SignalEvent construction gating and signal-engine execution outcomes.
- MODULE_INTERFACE_SPEC: owns the typed/shared FSM-to-signal-engine interface contract.
- OBSERVABILITY_SPEC / OBSERVABILITY_LOGGING_SPEC / EVENT_SCHEMA_SPEC: own execution-result observability policy, logging mechanics and schema.
- SIGNAL_DISTRIBUTION_ARCHITECTURE / SIGNAL_DISTRIBUTION_SPEC: remain unchanged owners of route/destination/publication truth.

No additional active canonical authority is required for the handoff itself.

## EXPECTED IMPACT

- Make stage acceptance explicit and fail-closed.
- Preserve PRE -> CONFIRM -> OPEN_NOW continuity without treating every FSM transition as handoff eligibility.
- Define a dedicated semantic execution-result event before any runtime schema implementation.
- Keep SignalEvent construction separate from distribution authorization and delivery success.
- Keep distribution, Telegram, outcomes, broker execution and scan cadence unchanged.

## EXECUTION OUTCOME CLARIFICATION

- SignalEvent constructed + distribution intentionally not invoked -> DEFERRED.
- SignalEvent construction alone must never produce EMITTED.
- EMITTED is only valid when downstream governed publication evidence confirms at least one authorized publication succeeded.
- Exact route-level success/failure remains distribution truth in route publication events.
- NOT_EMITTED, BLOCKED, SKIPPED and FAILED must remain distinguishable according to execution cause.

## RISK

- Over-broad stage acceptance could widen visibility.
- PRE/CONFIRM handoff without dedup/restart discipline could duplicate lifecycle events.
- Event-schema migration could reinterpret historical logs if not versioned.
- Internal SignalEvent construction could be confused with external publication authorization.
- A new cross-layer canonical file could duplicate ownership if introduced unnecessarily.
- Delta-only successor documents could depend on superseded sources and create ambiguous authority.

## BLAST_RADIUS

Documentation and later implementation contracts for:
- DecisionObject-to-FSM handoff
- FSM-to-signal-engine handoff
- SignalEvent construction
- execution observability
- event schema validation

Excluded:
- strategy mathematics
- thresholds
- market data
- route entitlement policy
- Telegram UX
- outcome handling
- broker execution
- scan cadence

## VALIDATION METHOD

Before any promotion:
1. Re-audit proposed material against the current active root manifest, architecture map and master index.
2. Verify no duplicate canonical ownership is introduced.
3. Verify no contradiction with distribution architecture/spec or system invariants.
4. Verify strategy/FSM/execution/distribution truth remain separated.
5. Verify PRE/CONFIRM/OPEN_NOW identity continuity and dedup requirements remain intact.
6. Verify SignalEvent construction cannot be interpreted as external delivery success.
7. Verify no proposed wording itself activates distribution or broker execution.
8. Materialize complete self-contained successor documents before they are eligible for active promotion.
9. Materialize a complete successor master index and root manifest when promotion changes version references.

After future code implementation, only after promotion:
- stage-acceptance tests
- SignalEvent construction tests for PRE/CONFIRM/OPEN_NOW
- blocked/no-op transition tests
- stable signal_id tests
- execution-result event-schema tests
- no-distribution regression tests
- restart/dedup safety tests
- live observability validation before distribution handoff

## ROLLBACK PLAN

- Do not promote proposed docs if re-audit fails.
- Current active canon remains authoritative until explicit promotion.
- Runtime code remains unchanged during this docs phase.
- Proposed documents may be corrected or discarded without changing active authority.

## DEPLOYMENT PLAN

None. Documentation phase only.

## SUCCESS CRITERIA

- Proposed material unambiguously defines accepted-stage handoff within existing authority homes.
- Proposed material defines post-FSM execution-result semantics.
- Minimum execution trace is representable before routing exists.
- SignalEvent creation does not equal distribution authorization or EMITTED.
- No new duplicate active authority is introduced.
- Any future promoted successor is self-contained.
- PR #73 remains blocked until promotion and re-audit.

## FAILURE TRIGGERS

Stop and return to Owner review if:
- canonical documents disagree on actionable-stage eligibility;
- execution observability blurs strategy/FSM/distribution truth;
- migration would silently reinterpret historical evidence;
- proposed docs implicitly authorize external delivery or broker execution;
- active-version authority would become ambiguous;
- a new document duplicates an existing architectural home;
- a successor depends normatively on a document it supersedes.
