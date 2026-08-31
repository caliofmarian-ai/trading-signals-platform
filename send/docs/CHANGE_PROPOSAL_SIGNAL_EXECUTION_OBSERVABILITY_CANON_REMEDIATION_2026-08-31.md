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

Primary authorities reviewed:
- send/docs/canonical/active/CANONICAL_STRATEGY_STACK_v1.0.0.md
- send/docs/canonical/active/CANONICAL_MASTER_INDEX_v1.0.0.md
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

Future implementation surfaces may only be derived after proposed canonical material is promoted and re-audited.

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

## EXPECTED IMPACT

- Make stage acceptance explicit and fail-closed.
- Preserve PRE -> CONFIRM -> OPEN_NOW continuity without treating every FSM transition as publish eligibility.
- Define a dedicated semantic execution-result event before any runtime schema implementation.
- Keep SignalEvent construction separate from distribution authorization.
- Keep distribution, Telegram, outcomes, broker execution and scan cadence unchanged.

## RISK

- Over-broad stage acceptance could widen visibility.
- PRE/CONFIRM handoff without dedup/restart discipline could duplicate lifecycle events.
- Event-schema migration could reinterpret historical logs if not versioned.
- Internal SignalEvent construction could be confused with external publication authorization.

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

Before promotion:
1. Re-audit proposed documents against the current active root manifest and master index.
2. Verify no contradiction with distribution architecture/spec or system invariants.
3. Verify strategy/FSM/execution/distribution truth remain separated.
4. Verify PRE/CONFIRM/OPEN_NOW identity continuity and dedup requirements remain intact.
5. Verify no proposed wording itself activates distribution or broker execution.

After future code implementation, only after promotion:
- stage-acceptance tests
- SignalEvent construction tests for PRE/CONFIRM/OPEN_NOW
- stable signal_id tests
- execution-result event-schema tests
- no-distribution regression tests
- restart/dedup safety tests
- live observability validation before distribution handoff

## ROLLBACK PLAN

- Do not promote proposed docs if re-audit fails.
- Current active canon remains authoritative until explicit promotion.
- Runtime code remains unchanged during this docs phase.

## DEPLOYMENT PLAN

None. Documentation phase only.

## SUCCESS CRITERIA

- Proposed canon unambiguously defines accepted-stage handoff.
- Proposed canon defines post-FSM execution-result semantics.
- Minimum execution trace is representable before routing exists.
- SignalEvent creation does not equal distribution authorization.
- PR #73 remains blocked until promotion and re-audit.

## FAILURE TRIGGERS

Stop and return to Owner review if:
- canonical documents disagree on actionable-stage eligibility;
- execution observability blurs strategy/FSM/distribution truth;
- migration would silently reinterpret historical evidence;
- proposed docs implicitly authorize external delivery or broker execution;
- active-version authority would become ambiguous.
