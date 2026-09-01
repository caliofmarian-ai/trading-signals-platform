# GOVERNANCE_AND_CHANGE_CONTROL_v2.0.1

Version: 2.0.1  
Status: ACTIVE CANONICAL  
Path: /opt/binarybot/docs/canonical/active/GOVERNANCE_AND_CHANGE_CONTROL_v2.0.1.md  
Supersedes: `GOVERNANCE_AND_CHANGE_CONTROL_v2.0.0.md`  

Linked Documents:
- SYSTEM_INVARIANTS_v3.0.0.md
- SYSTEM_ARCHITECTURE_MAP_v3.0.0.md
- MODULE_INTERFACE_SPEC_v3.0.0.md
- DECISION_AUDIT_SPEC_v3.0.0.md
- PERFORMANCE_ANALYTICS_SPEC_v3.0.0.md
- TEST_PLAN_v3.0.0.md
- DEPLOYMENT_PROTOCOL_v2.0.1.md
- OUTCOME_TRACKING_SPEC_v3.0.0.md
- OBSERVABILITY_LOGGING_SPEC_v3.0.0.md
- SIGNAL_DISTRIBUTION_SPEC_v2.0.1.md
- STRATEGY_INTELLIGENCE_SYSTEM_v3.0.0.md
- COMMUNITY_FEEDBACK_AND_PRIVACY_SPEC_v3.0.0.md

Depends on:
- SYSTEM_INVARIANTS_v3.0.0.md
- SYSTEM_ARCHITECTURE_MAP_v3.0.0.md
- MODULE_INTERFACE_SPEC_v3.0.0.md
- DECISION_AUDIT_SPEC_v3.0.0.md
- PERFORMANCE_ANALYTICS_SPEC_v3.0.0.md

Code Alignment:
- bot_service.py
- core/strategy_v2.py
- core/fsm_runtime.py
- core/signal_engine.py
- core/distribution_router.py
- core/observability_logger.py
- core/analytics_engine.py
- core/outcome_service.py
- deployment scripts
- admin command surfaces

---

## PATCH SCOPE

This successor preserves the complete governance framework of v2.0.0: authority separation, change classes, formal proposals, SemVer, approvals, incidents, drift control, isolation, synchronization, monitoring, freeze, deployment, overrides and long-term evolution.

The patch only updates normative references and version/status/path metadata and removes non-canonical formatting artifacts. No governance burden is weakened or expanded.

Promotion status: ACTIVE CANONICAL under `CANONICAL_ACTIVATION_RECORD_20260901.md` and `CANONICAL_MASTER_INDEX_v2.0.0.md`.

---

## 0. Purpose

This document defines the canonical governance, authority, change control, and operational discipline framework for BinaryBot / DROPi Signals.

Its role is to ensure that system evolution remains deliberate, auditable, evidence-based, reversible, and structurally aligned with canonical architecture.

This document does not define trading logic internals, Trade Physics mathematics, channel copywriting, or subsystem implementation details.  
It defines who may authorize change, how change must be proposed, what evidence is required, how validation is performed, how rollback must be prepared, and how drift is prevented.

Its purpose is to prevent:
- undocumented changes
- emotional parameter tuning
- shadow authority
- code-first undocumented behavior
- uncontrolled production experimentation
- structural drift between code and canonical documents
- unsafe emergency edits without traceability

## 1. Canonical Position

This document is the governance and change-control authority layer for the project.

It governs:
1. authority boundaries
2. change proposal requirements
3. approval discipline
4. validation discipline
5. rollback discipline
6. documentation synchronization
7. incident escalation
8. strategic freeze behavior
9. drift prevention
10. controlled evolution of the system

This document sits above operational change behavior and below owner intent.

It does not replace subsystem specifications.  
It defines how subsystem specifications may be changed, approved, versioned, deployed, and stabilized.

If any implementation, deployment, parameter change, admin override, or documentation mutation conflicts with this governance framework, the conflict must be resolved canonically before further change proceeds.

## 2. Final Principle

No system behavior may change without explicit ownership, explicit documentation, explicit evaluation scope, and explicit rollback discipline.

A change is non-canonical if it introduces any of the following:
- undocumented behavioral mutation
- production-side experimentation without governance
- authority ambiguity
- parameter tuning without evidence
- structural change without version discipline
- emergency intervention without post-incident documentation
- code behavior that outruns canonical documentation
- direct production edits that bypass auditability

BinaryBot / DROPi Signals must evolve as a controlled system, not as an improvisational script.

## 3. Governance Backbone

The governance framework of the system is built on the following mandatory principles:

1. No undocumented change.
2. No untested change.
3. No hidden authority.
4. No emotional tuning.
5. No structural modification without canonical update.
6. No production experimentation.
7. No deployment without rollback path.
8. No code state ahead of documentation state.
9. No override without proof trail.
10. No repeated instability without freeze-and-review discipline.

These principles apply to:
- strategy logic
- Trade Physics / scoring logic
- lifecycle logic
- routing logic
- admin controls
- analytics interpretation that affects decisions
- outcome-driven protections
- deployment operations
- incident response
- canonical document mutation

## 4. Authority Model

Governance requires explicit authority separation.

No one role may silently own all change classes without traceability.

### 4.1 Owner Authority

Owner Authority governs:
- strategic direction
- business intent
- capital philosophy
- acceptable risk posture
- top-level product direction
- approval of major structural direction
- ultimate acceptance or rejection of major behavioral change

Owner Authority does not mean impulsive direct mutation of runtime behavior.

Owner Authority must not:
- bypass canonical process for code or production edits
- remove hard protections without documented review
- approve undocumented logic changes
- replace evidence with instinct in change validation

### 4.2 Technical Authority

Technical Authority governs:
- implementation integrity
- architectural consistency
- FSM correctness
- persistence discipline
- observability compliance
- deployment safety
- rollback readiness
- structural alignment between code and canonical docs

Technical Authority must not:
- redefine business risk philosophy unilaterally
- reinterpret owner intent outside governance process
- push structural change without canonical documentation

### 4.3 Parameter Authority

Parameter Authority governs:
- thresholds
- score gates where canonically defined
- timing buffers
- expiry values
- filter strengths
- corridor/risk tuning surfaces where canonically permitted

Parameter Authority must operate under evidence discipline and under `STRATEGY_PARAMETER_CONTROL_SPEC_v3.0.0.md` where applicable.

Parameter Authority must:
- justify the proposed change
- reference relevant analytics and audit evidence
- define expected impact
- define rollback conditions
- run the required test and validation protocol

Parameter Authority must not:
- tune based on frustration or panic
- stack multiple confounding changes without isolation
- tune parameters live without traceability
- invent new TPS lifecycle thresholds or combine TPS and classical score without the structural governance required by the active strategy canon

### 4.4 Operational Authority

Operational Authority governs:
- controlled deployments
- restart discipline
- incident containment
- freeze mode activation
- evidence preservation
- post-deploy monitoring procedures

Operational Authority may execute approved actions, but may not silently redefine governance policy.

### 4.5 Admin Surface Authority

Admin Surface Authority governs:
- who can see which controls
- who can trigger which actions
- who can review diagnostics
- which commands are owner-only
- which controls require higher privilege
- which actions require proof logging

Admin surface control is not equivalent to unrestricted system mutation authority.

No admin interface may expose mutation capability that exceeds canonical governance rules.

## 5. Change Classes

All changes must be explicitly classified before review, implementation, or deployment.

### 5.1 Cosmetic Change

A cosmetic change affects presentation but not decision behavior.

Examples:
- logging formatting
- admin wording
- message layout
- visual labeling
- non-semantic documentation cleanup

Cosmetic changes still require traceability.

Minimum requirements:
- changelog or audit note
- confirmation that behavior is unchanged
- no hidden contract mutation

### 5.2 Parameter Change

A parameter change affects runtime thresholds or tunable values without changing structural logic ownership.

Examples:
- an existing PRE/CONFIRM/OPEN_NOW threshold adjustment where such a threshold is already canonically defined
- expiry window modification
- spike multiplier change
- corridor threshold tuning
- risk cap tuning where no structural redesign occurs

Minimum requirements:
- evidence-based rationale
- performance comparison
- risk impact note
- version bump discipline
- test plan execution
- monitoring window

Parameter change is not “minor” merely because code diff is small.  
If behavior changes materially, governance obligations apply fully.

### 5.3 Structural Logic Change

A structural logic change alters ownership, decision rules, lifecycle rules, architecture, event contracts, or subsystem interaction.

Examples:
- new scoring model
- new Trade Physics formula or feature contract
- new strategy gate
- new lifecycle stage logic
- new risk-control architecture
- new state persistence model
- new admin authority layer
- new distribution routing model
- any reallocation of subsystem responsibility

Minimum requirements:
- canonical document update first
- explicit architectural classification
- full regression/testing scope
- deployment discipline
- rollback plan
- structured monitoring period
- versioning consistent with structural significance

### 5.4 Emergency Fix

An emergency fix is an urgent change required to stop active harm, instability, duplication, corruption, or outage.

Examples:
- duplicate live publication
- crash loop
- persistence corruption
- cooldown bypass
- uncontrolled signal flood
- broken lifecycle transition causing unsafe behavior

Emergency status does not remove governance.  
It compresses the timeline but preserves the obligation.

Minimum requirements:
- immediate containment
- backup before intervention where possible
- incident record
- proof preservation
- post-fix documentation
- post-fix audit
- follow-up canonical reconciliation

## 6. Required Change Proposal Format

Every non-trivial change must be written in a formal proposal structure before approval and implementation.

Canonical proposal fields:

- CHANGE_ID
- TITLE
- TYPE
- OWNER
- REQUESTED_BY
- DATE
- TARGET_DOCS
- TARGET_CODE
- RATIONALE
- EXPECTED_IMPACT
- RISK
- BLAST_RADIUS
- VALIDATION_METHOD
- ROLLBACK_PLAN
- DEPLOYMENT_PLAN
- MONITORING_WINDOW
- SUCCESS_CRITERIA
- FAILURE_TRIGGERS
- APPROVAL_STATUS

Minimum core format may be expressed as:

CHANGE_ID: YYYYMMDD-XX  
TYPE: PATCH / MINOR / MAJOR  
RATIONALE: why change is needed  
EXPECTED IMPACT: what should improve  
RISK: what could break  
ROLLBACK PLAN: how to revert  
TEST PLAN: what will be executed  

No informal production change is canonical.

## 7. Versioning Rule

Versioning must follow:

MAJOR.MINOR.PATCH

Interpretation:
- PATCH = bug fix, reference repair, or non-structural correction
- MINOR = controlled parameter-level or bounded behavior tuning
- MAJOR = structural architecture, ownership, event-contract, or logic change

Versioning must remain aligned across all affected artifacts where applicable, including:
- canonical documents
- configuration version references
- startup display or runtime version display if used
- deployment records
- changelog material
- test references

A change may not be labeled as PATCH merely to avoid governance burden if its behavioral impact is structurally meaningful.

## 8. Approval Discipline

Every proposed change must pass through explicit review stages appropriate to its class.

Canonical approval sequence:

1. Written proposal exists.
2. Change class is identified.
3. Relevant evidence is reviewed.
4. Risk impact is reviewed.
5. Canonical docs are updated or confirmed unchanged.
6. Test scope is defined.
7. Rollback plan is validated.
8. Deployment plan is approved.
9. Monitoring criteria are defined.
10. Deployment occurs under controlled conditions.
11. Post-deploy monitoring confirms or rejects stabilization.

No change is considered fully accepted merely because it was deployed.  
Validation occurs only after the monitoring discipline is completed.

## 9. Forbidden Actions

The following actions are categorically non-canonical unless explicitly redefined by a higher canonical governance update:

- editing production code directly without backup discipline
- undocumented runtime mutation
- removing core gates impulsively
- lowering critical thresholds without evidence
- disabling spike or protection layers without canonical review
- testing ideas live on production behavior
- mutating structural behavior through admin surfaces without governance trace
- combining multiple confounding strategy changes in one uncontrolled deploy
- applying fixes silently without incident note where impact was operational
- letting code exceed documentation in structural truth

A forbidden action is a governance failure even if the system appears to keep running.

## 10. Incident Management

An incident is any abnormal behavior that threatens correctness, trust, stability, or auditability.

Examples include:
- performance collapse
- signal flood
- duplicate publication
- missed lifecycle transition
- corrupted state
- restart inconsistency
- silent output suppression
- broken admin control
- observability gaps during live behavior

Canonical incident procedure:

1. Contain the issue.
2. Preserve logs and proof artifacts.
3. Freeze further speculative changes.
4. Identify affected layer(s).
5. Perform root-cause analysis.
6. Document the incident.
7. Apply controlled fix.
8. Validate the fix.
9. Update canonical material if governance truth changed.
10. Close the incident only after evidence supports stabilization.

No silent correction is acceptable for material incidents.

## 11. Drift Control Policy

Drift is defined as divergence between actual system behavior and canonical system definition.

Drift may occur between:
- code and canonical docs
- runtime behavior and intended logic
- admin controls and authorized scope
- distribution behavior and routing rules
- audit narratives and recorded truth
- analytics interpretations and measurable evidence

Drift detection signals may include:
- unexpected signal frequency
- abnormal score/TPS distribution
- gate rejection anomalies
- routing anomalies
- unexplained lifecycle death clusters
- performance degradation
- mismatch between observed and documented behavior
- restart-state inconsistencies

Upon drift detection:
1. freeze non-essential changes
2. inspect recent change history
3. compare runtime truth to canonical specs
4. identify the canonical owner document involved
5. decide whether code must be corrected or documents must be canonically updated
6. do not continue normal tuning until drift is resolved

## 12. Change Isolation Rule

The system must preserve interpretability of impact.

Only one structural change should be introduced per controlled deployment cycle unless a larger bundled migration is itself explicitly designed, documented, and governed as one atomic program of change.

Confounding combinations are strongly discouraged, especially:
- new scoring logic plus threshold retuning
- lifecycle rule change plus routing redesign
- outcome protection redesign plus parameter tuning
- architecture refactor plus production hotfix mixed together without controlled scope

Multiple simultaneous changes obscure attribution and weaken governance confidence.

## 13. Documentation Synchronization Rule

If behavior changes, relevant canonical documentation must be updated before or together with implementation, never as an optional afterthought.

Depending on the change, synchronization may include:
- system architecture map
- module interface contracts
- strategy specs
- Trade Physics specs
- parameter references
- decision audit definitions
- observability/event schema docs
- risk/outcome docs
- deployment protocol
- test plan
- change logs or audit reports

Code must not become the hidden primary source of truth.

## 14. Validation and Monitoring Window

No meaningful conclusion may be drawn immediately after deployment.

Minimum monitoring discipline must be defined before deployment.

Typical validation windows may include:
- a bounded number of trades
- a bounded number of lifecycle events
- a bounded number of channel publications
- a bounded runtime duration
- a bounded restart stability period
- a bounded incident-free operational period

As a default governance pattern:
- smaller change classes may use shorter windows
- structural changes require materially larger validation windows

No parameter or structural conclusion should be declared valid before its monitoring window has been completed or responsibly reviewed.

## 15. Strategic Freeze Mode

Strategic Freeze Mode is a governance state used to stop destabilizing change velocity.

When freeze mode is active:
- no parameter changes
- no structural changes
- no opportunistic tuning
- only tightly scoped corrective fixes may proceed
- every allowed fix must preserve traceability

Freeze mode may be activated during:
- performance instability
- repeated contradictory tuning attempts
- unresolved drift
- incident clusters
- high uncertainty about root cause
- post-deploy instability
- suspicious mismatch between analytics and live behavior

Freeze mode ends only after:
- root cause is understood sufficiently
- corrective scope is defined
- governance confidence is restored

## 16. Deployment Governance Rule

Deployment is not merely a technical action.  
It is a governed transition from approved change to monitored runtime behavior.

Every governed deployment should define:
- exact scope
- pre-deploy backup
- target files/modules
- rollback procedure
- restart plan
- post-restart audit
- success checks
- failure checks
- evidence output location

No deployment is complete until post-deploy verification confirms that the intended effect occurred and unintended damage did not.

Deployment mechanics are governed by `DEPLOYMENT_PROTOCOL_v2.0.1.md`.

## 17. Admin Override Governance

If any admin surface permits override-like behaviors, those behaviors must remain within canonical governance constraints.

Override-capable actions must satisfy:
- explicit role restriction
- proof logging
- visible intent
- traceable execution
- bounded scope
- non-silent effect
- post-action auditability

No admin command may function as a secret bypass around governance, risk, or architecture rules.

## 18. Long-Term Evolution Model

Long-term evolution must follow a stable cycle:

Stability  
→ Measurement  
→ Diagnosis  
→ Proposal  
→ Controlled Change  
→ Validation  
→ Stabilization

The forbidden anti-pattern is:

Instability  
→ Panic  
→ Over-adjustment  
→ Confounded results  
→ More panic  
→ Structural collapse

Governance exists to keep evolution cumulative, interpretable, and institutionally disciplined.

## 19. Governance Failure Conditions

Governance failure exists if any of the following occur:
- undocumented production mutation
- repeated tuning without stable measurement windows
- inability to explain who approved a change
- inability to revert a bad deployment
- code/document divergence left unresolved
- emergency fixes with no incident trail
- architecture changes introduced without canonical reclassification
- admin powers exceeding documented authority
- drift known but ignored

When governance failure is detected, expansion work should pause until the failure is corrected.

## 20. Privacy Protection and Pseudonymous Member References

### 20.1 Raw identifier exposure prohibition
Raw `telegram_user_id` must not be exposed in user-facing surfaces, community views, or non-privileged operator outputs except where an explicitly authorized secure administrative path requires it.

### 20.2 Pseudonymous member reference rule
`MEMBER_REF` may be derived as a salted pseudonymous identifier so analytics, audits, and community-facing references can operate without exposing raw identity.

### 20.3 Protected fields
Members must never see privileged identity fields such as raw `telegram_user_id` values for other members.

This privacy governance must align with `COMMUNITY_FEEDBACK_AND_PRIVACY_SPEC_v3.0.0.md`.

## 21. Final Canonical Statement

BinaryBot / DROPi Signals must evolve through governed change, not through improvisation.

No authority is valid without boundary.  
No change is valid without traceability.  
No deployment is valid without rollback discipline.  
No tuning is valid without evidence.  
No structural evolution is valid without canonical documentation.

This document is the authoritative governance and change-control framework for the project when promoted.

---

## 22. VERSION HISTORY

| Version | Date | Description |
|---|---|---|
| 2.0.1 | 2026-09-01 | Proposed PATCH successor for canonical reference repair and non-semantic cleanup; governance semantics unchanged. |
| 2.0.0 | 2026-07-12 | Active canonical governance/change-control framework before this proposed patch. |

---

End of GOVERNANCE_AND_CHANGE_CONTROL_v2.0.1.md
