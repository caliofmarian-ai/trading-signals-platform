# ADMIN_OPERATIONS_SPEC_v2.0.1.md

BinaryBot — Admin Operations & Governed Control Procedures  
Version: 2.0.1  
Status: ACTIVE CANONICAL  
Path: /opt/binarybot/docs/canonical/active/ADMIN_OPERATIONS_SPEC_v2.0.1.md  
Supersedes: `ADMIN_OPERATIONS_SPEC_v2.0.0.md`  

Linked Documents:
- ADMIN_CONTROL_SPEC_v2.0.1.md
- ROLE_AND_PERMISSION_MATRIX_SPEC_v2.0.1.md
- ADMIN_TREE_MAP_v2.0.1.md
- CONTROL_PANEL_HIERARCHY_AND_INTELLIGENCE_SPEC_v2.0.1.md
- TELEGRAM_UX_v2.0.1.md
- SIGNAL_DISTRIBUTION_SPEC_v2.0.1.md
- CHANNEL_CONFIG_SPEC_v2.0.1.md
- OBSERVABILITY_LOGGING_SPEC_v3.0.0.md
- DECISION_AUDIT_SPEC_v3.0.0.md
- TRADE_TEMPORAL_TELEMETRY_SPEC_v3.0.0.md
- OUTCOME_TRACKING_SPEC_v3.0.0.md
- PERFORMANCE_ANALYTICS_SPEC_v3.0.0.md
- GOVERNANCE_AND_CHANGE_CONTROL_v2.0.1.md
- FAILURE_RECOVERY_SPEC_v2.0.1.md
- SYSTEM_INVARIANTS_v3.0.0.md

---

## 0. PATCH SCOPE

This successor preserves the operational semantics of v2.0.0.

The patch only:
- updates normative references to the final successor filenames required by the Trade Physics + staged-execution promotion graph;
- updates this document's version/status/path metadata;
- makes no permission, action-class, freeze, restart, recovery, mutation, or governance-policy change.

Promotion status: ACTIVE CANONICAL under `CANONICAL_ACTIVATION_RECORD_20260901.md` and `CANONICAL_MASTER_INDEX_v2.0.0.md`.

---

## 1. PURPOSE

This document defines the canonical operational control procedures for BinaryBot.

It governs how human operators interact with the system through the admin surface, how approved actions are executed, how operational safety is preserved, and how production control remains auditable and role-scoped.

This document is the operational procedure layer of the admin architecture.

It defines:
- operational control principles
- governed mutation rules
- emergency and recovery procedures
- execution constraints for operator actions
- audit requirements for every meaningful control event
- role-aware operating procedures for production use

This document does not replace the permission matrix or the structural admin tree map.

Primary companion documents:
- `ROLE_AND_PERMISSION_MATRIX_SPEC_v2.0.1.md`
- `ADMIN_CONTROL_SPEC_v2.0.1.md`
- `ADMIN_TREE_MAP_v2.0.1.md`
- `CONTROL_PANEL_HIERARCHY_AND_INTELLIGENCE_SPEC_v2.0.1.md`

---

## 2. OPERATIONAL PHILOSOPHY

BinaryBot must be operated under governed control, not ad hoc command behavior.

The operational layer must preserve the following truths:

### 2.1 Role-scoped control
No actor may execute an action outside their granted scope.

### 2.2 Future-facing mutation
Admin actions may change future operation, not rewrite historical facts.

### 2.3 Audit-first mutation
Every meaningful mutating control action must produce evidence.

### 2.4 Safety over convenience
Potentially dangerous actions must require explicit guarded pathways.

### 2.5 Observability before recovery
Whenever possible, incident context should be visible before restart or recovery.

### 2.6 Canonical alignment
Operational procedures must match the newer admin hierarchy, role model, intelligence layer and audit framework.

---

## 3. DEFINITIONS

**Admin Surface**  
The governed control environment exposed through Telegram and any future equivalent admin interface.

**Mutating Action**  
An operator action that changes configuration, activation scope, runtime behavior, route state, or control state for future operation.

**Visibility Action**  
A read-only action that reveals state, diagnostics, reports or explanations without changing future behavior.

**Guarded Action**  
A sensitive or high-impact action that requires stricter role, flow, confirmation, or contextual checks.

**Proof Record**  
The auditable combination of operator-facing proof output and machine-readable event evidence.

**Freeze State**  
A protected operational state that halts or constrains strategy and/or publication activity to prevent uncontrolled behavior.

**Recovery Action**  
A governed action intended to restore normal operation after incident, freeze or fault.

---

## 4. OPERATIONAL DOMAINS

Operational procedures are grouped into the following canonical domains:

### 4.1 Operations domain
Runtime state, incident handling, freeze state, restart pathways and continuity actions.

### 4.2 Symbols & Coverage domain
Future symbol activation, coverage selection and scope diagnostics.

### 4.3 Distribution domain
Route readiness, destination state, publication controls and dispatch diagnostics.

### 4.4 Decision Visibility domain
Read-only interpretability of decision state, gate results, rejection reasons and lifecycle progression.

### 4.5 Research & Analytics domain
Report review, trend analysis, outcome inspection and rejection analytics.

### 4.6 Intelligence domain
Higher-order intelligence summaries, drift signals, anomaly review and recommendation visibility.

### 4.7 Governance & Docs domain
Canonical specification access, migration references and change-control guidance.

### 4.8 Security & Audit domain
Audit trails, sensitive action review, access denial visibility and privileged oversight.

---

## 5. CONTROL ACTION CLASSES

All actions exposed via admin surfaces must belong to one of the following classes.

### 5.1 Visibility actions
Read-only state inspection.

Examples:
- view engine status
- inspect route readiness
- inspect decision object state
- inspect rejection reasons
- inspect reports and drift summaries

### 5.2 Low-risk mutating actions
Governed actions with limited blast radius.

Examples:
- change active symbol selection
- change allowed coverage within approved boundaries
- toggle approved future-facing runtime modes where policy allows

### 5.3 Guarded mutating actions
Actions with broader operational effect that require stronger controls.

Examples:
- freeze
- unfreeze
- guarded restart
- route hold / route release where implemented
- change sensitive distribution controls

### 5.4 Governance-sensitive actions
Actions reserved for top authority and/or explicit approval chains.

Examples:
- role architecture changes
- policy changes
- canonical governance changes
- production release markers and controlled deployment approvals
- destructive or retention-sensitive audit/log procedures if ever allowed

---

## 6. ROLE-AWARE OPERATING MODEL

The admin operating model is hierarchical and scoped.

### 6.1 Owner
Highest operational authority.

Owner may:
- access all operational domains
- execute all governed actions allowed by policy
- approve or perform governance-sensitive changes
- review all audit and security evidence
- authorize recovery from major incidents where policy requires top-level approval

### 6.2 Primary Admin
High-trust operator with broad operational control but not unrestricted sovereign authority.

Primary Admin may:
- operate day-to-day runtime controls within policy
- view broad operational and analytical surfaces
- execute approved guarded actions when granted
- participate in incident response
- manage assigned functional admin pathways

Primary Admin may not bypass Owner-reserved governance boundaries.

### 6.3 Functional Admin
Domain-specific operator.

Examples:
- operations admin
- distribution admin
- research admin
- observability admin
- affiliate/admin support role

Functional Admin acts only within assigned subtree and granted action scope.

### 6.4 Analyst / Read-only operator
Can inspect decision, analytics and intelligence surfaces but cannot mutate production behavior.

### 6.5 Limited support or moderation role
May access only narrowly scoped visibility or support flows required by policy.

### 6.6 Affiliate-facing admin role
May access only affiliate-scoped operational/support functions and must not gain unrelated global admin visibility.

Detailed role boundaries are canonical in:
`ROLE_AND_PERMISSION_MATRIX_SPEC_v2.0.1.md`

---

## 7. CONTROL SURFACE RULES

### 7.1 Governed entry point
Operational actions must originate from the governed admin surface, not from arbitrary uncontrolled message contexts.

### 7.2 Role-filtered visibility
Users must only see actions that are relevant and authorized for them.

### 7.3 No public control execution
Mutating control actions must not execute from public user-facing channels.

### 7.4 Control versus visibility clarity
The UI must clearly distinguish read-only inspection from state-changing operations.

### 7.5 Guarded action signaling
Sensitive actions must be labeled and handled as guarded actions.

### 7.6 Deterministic response expectation
An executed action must return a deterministic and auditable result state whenever technically possible.

---

## 8. OPERATIONAL PROCEDURES BY DOMAIN

## 8.1 Operations Procedures

### 8.1.1 Engine status inspection
Authorized operators may inspect:
- current runtime state
- freeze state
- recent important operational state
- last relevant execution timestamps
- incident markers
- restart guard status

This is a visibility action.

### 8.1.2 Freeze procedure
Freeze is a guarded mutating action.

Expected canonical behavior:
- prevent or halt further governed production activity according to freeze semantics
- preserve the evidence needed for diagnosis
- produce audit evidence
- emit critical operational visibility where required
- avoid silent destructive side effects

### 8.1.3 Unfreeze procedure
Unfreeze must be governed and may be restricted to higher authority.

Before unfreeze:
- incident context should be visible
- reason for freeze should be reviewable
- any required approval condition should be satisfied
- restart/recovery prerequisites should be met if policy requires them

### 8.1.4 Guarded restart
Restart pathways must be governed, role-scoped and auditable.

Restart should:
- preserve enough evidence for post-incident review
- surface outcome status
- not silently erase critical incident context
- respect freeze and recovery rules

### 8.1.5 Recovery references
Operators must have access to the relevant recovery references rather than improvising recovery behavior.

Companion docs:
- `FAILURE_RECOVERY_SPEC_v2.0.1.md`
- `SYSTEM_INVARIANTS_v3.0.0.md`
- `OBSERVABILITY_LOGGING_SPEC_v3.0.0.md`

---

## 8.2 Symbols & Coverage Procedures

### 8.2.1 Active coverage inspection
Authorized operators may inspect current active symbols and allowed scope.

### 8.2.2 Coverage modification
Coverage changes are mutating actions affecting future operation.

Coverage procedures must:
- be role-scoped
- be auditable
- show what changed
- avoid ambiguous partial state where possible
- preserve canonical distinction between available scope and active scope

### 8.2.3 Save/apply semantics
If the interface allows staged selection and then save/apply:
- staged view and committed view must not be confused
- commit action must produce proof evidence
- committed result must be inspectable

---

## 8.3 Distribution Procedures

### 8.3.1 Distribution visibility
Authorized actors may inspect:
- route state
- destination readiness
- publication restrictions
- recent dispatch diagnostics
- dedup behavior visibility where implemented

### 8.3.2 Distribution mutation
Any change to future route or publication behavior is a mutating action and must be auditable.

### 8.3.3 Sensitive routing controls
Sensitive route changes should be treated as guarded actions where blast radius is meaningful.

---

## 8.4 Decision Visibility Procedures

This domain is visibility-only by default.

Authorized actors may inspect:
- current candidate state
- last decision state
- decision object view
- gate results
- rejection reasons
- score composition
- corridor/timing context
- focus/feasibility state

No action in this domain may rewrite historical decision truth.

Decision semantics are governed by:
- `DECISION_AUDIT_SPEC_v3.0.0.md`
- `TRADE_TEMPORAL_TELEMETRY_SPEC_v3.0.0.md`

---

## 8.5 Research & Analytics Procedures

Authorized actors may:
- inspect current and periodic summaries
- review performance and rejection analytics
- inspect outcome trends
- review symbol/session level analytics
- export approved reports where allowed

This domain is primarily visibility-oriented unless export or scheduled generation is considered a governed action.

Related documents:
- `PERFORMANCE_ANALYTICS_SPEC_v3.0.0.md`
- `OUTCOME_TRACKING_SPEC_v3.0.0.md`

---

## 8.6 Intelligence Procedures

Authorized actors may inspect:
- drift signals
- anomaly summaries
- recommendation queues
- decision intelligence summaries
- learning-oriented review surfaces

Recommendation visibility does not imply recommendation application authority.

Intelligence must remain separated from direct mutation unless explicitly governed elsewhere.

---

## 8.7 Governance & Docs Procedures

Authorized roles may:
- read approved canonical docs
- inspect active/deprecated references
- access migration notes
- access implementation mapping references

Documentation access itself must still respect sensitivity boundaries.

---

## 8.8 Security & Audit Procedures

Authorized roles may:
- inspect admin action history
- inspect access denials
- inspect role change audit
- inspect approval records
- inspect sensitive incident references
- export approved audit views where allowed

Sensitive audit data must remain role-scoped.

---

## 9. PROOF AND AUDIT REQUIREMENTS

Every meaningful mutating control action must produce a proof record.

## 9.1 Proof record components
A proof record should include, where applicable:
- timestamp
- actor identity reference
- actor role
- action type
- target domain
- before/after or equivalent effect summary
- success/failure outcome
- correlation or trace reference where available
- relevant version or configuration context where meaningful

## 9.2 Operator-facing proof output
The operator-facing proof message must be readable and sufficient to explain what happened.

## 9.3 Machine-readable evidence
A machine-readable event must exist for reliable audit and later analysis.

## 9.4 Failure proofing
Failed actions should still emit evidence indicating:
- attempted action
- failure status
- reason class if known
- whether state changed or not

## 9.5 No silent mutation
State-changing operations must not complete without evidence.

---

## 10. SAFETY RULES

### 10.1 No historical rewrite
Admin operations may not rewrite historical decision or outcome truth through normal control pathways.

### 10.2 No hidden mutation behind visibility actions
A view action must not secretly mutate operational state.

### 10.3 No uncontrolled high-impact action
High-blast-radius actions must be guarded.

### 10.4 Preserve diagnosability
Operational procedures must preserve enough evidence for review after faults and incidents.

### 10.5 Respect invariant escalation
If invariants are breached, recovery and continuation must respect invariant procedures.

### 10.6 Policy over convenience
Where convenience conflicts with safety and auditability, safety wins.

---

## 11. INCIDENT AND EMERGENCY PROCEDURES

### 11.1 Freeze on severe condition
The system may require or trigger freeze under severe conditions defined elsewhere.

Examples include:
- invariant breach
- dangerous runtime instability
- distribution safety risk
- severe incident requiring controlled halt

### 11.2 Incident visibility
Critical incidents should surface in the operational/admin alerting context.

### 11.3 Approval-gated resume
Certain incident classes may require higher-authority review before normal operation resumes.

### 11.4 Evidence-preserving recovery
Recovery should preserve enough evidence for diagnosis, not merely restore motion.

---

## 12. CHANGE GOVERNANCE PROCEDURES

### 12.1 Live operational changes
Some low-risk future-facing changes may be allowed without a code deployment, if policy explicitly permits them.

### 12.2 Deployment-linked changes
Behavior-changing system changes that alter strategy or governed architecture must follow change-control procedures.

### 12.3 Canonical consistency
Operational procedures must stay aligned with current active canonical documents and must not rely on deprecated assumptions.

### 12.4 Change documentation
Meaningful changes should map to changelog, governance or release evidence where applicable.

---

## 13. PRIVACY AND DATA EXPOSURE RULES

### 13.1 Minimum necessary exposure
Operators should only see the data needed for their role and task.

### 13.2 Identity protection
Sensitive user identity linkage must not leak through public or over-broad admin views.

### 13.3 Aggregates versus raw identity
Where possible, analytical access should prefer aggregates over raw sensitive identity-level exposure.

### 13.4 Affiliate isolation
Affiliate roles must not gain unrelated access to global analytics or sensitive internal datasets.

---

## 14. OPERATIONAL ROUTINES

### 14.1 Daily operator review
Authorized operators should routinely inspect:
- runtime health
- freeze/incident state
- route/publishing state
- recent important activity
- major anomaly or drift surfaces

### 14.2 Periodic analytical review
Authorized analytical roles should periodically review:
- rejection patterns
- performance drift
- outcome aggregates
- symbol/session patterns
- recommendation-quality indicators

### 14.3 Governance review cadence
Owner or governance-capable roles should periodically verify:
- canonical alignment
- audit health
- role visibility correctness
- deprecated vs active document consistency

---

## 15. IMPLEMENTATION GUARANTEES

If implemented according to this specification, the admin operations layer provides:

- governed human control over production behavior
- separation between visibility and mutation
- auditable change execution
- role-scoped safety boundaries
- evidence-preserving incident handling
- alignment with the newer canonical admin architecture

---

## 16. MIGRATION NOTES FROM LEGACY VERSION

The previous version was useful as a first operational baseline, but it had several limitations:
- older flat RBAC model
- insufficient distinction between action classes
- limited mapping to the newer hierarchical admin tree
- weaker separation between control, intelligence, analytics and governance
- too much Telegram-command framing instead of architecture-aligned operational domains
- insufficient treatment of affiliate-scoped roles and domain-specific admins
- insufficient emphasis on visibility-versus-mutation separation

This v2.0.0 document replaced the legacy operator-control framing with a governed, role-scoped, domain-structured operational procedure model aligned to the current BinaryBot architecture.

---

## 26. Admin Operator Workflow Clarifications from Admin UX Review

This section preserves the bounded workflow clarifications extracted from ADMIN_UX_V2_SPEC.md.

### 26.1 Workflow role
Admin workflows may organize command flows, review flows, filters, and control actions into more usable operator sequences.

### 26.2 Ownership boundary
Workflow organization does not transfer ownership away from the active canonical operation, governance, or deployment documents.

### 26.3 Evidence rule
Where admin UX proposes a workflow step, the canonical operation document set still governs what is permitted, auditable, and role-bounded.

---

## 27. VERSION HISTORY

| Version | Date | Description |
|---|---|---|
| 2.0.1 | 2026-09-01 | Proposed PATCH successor for canonical reference repair only; operational semantics unchanged. |
| 2.0.0 | 2026-07-12 | Active canonical operational procedure model before this proposed patch. |

---

End of ADMIN_OPERATIONS_SPEC_v2.0.1.md
