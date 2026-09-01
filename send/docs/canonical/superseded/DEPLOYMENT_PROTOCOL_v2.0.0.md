# DEPLOYMENT_PROTOCOL_v2.0.0

Version: 2.0.0  
Status: Active Canonical  
Path: /opt/binarybot/docs/canonical/active/DEPLOYMENT_PROTOCOL_v2.0.0.md

Linked Documents:
- SYSTEM_INVARIANTS_v2.0.0.md
- SYSTEM_ARCHITECTURE_MAP_v2.0.0.md
- MODULE_INTERFACE_SPEC_v2.0.0.md
- GOVERNANCE_AND_CHANGE_CONTROL_v2.0.0.md
- TEST_PLAN.md
- OBSERVABILITY_LOGGING_SPEC_v2.0.0.md
- FAILURE_RECOVERY_SPEC_v2.0.0.md
- DECISION_AUDIT_SPEC_v2.0.0.md
- SIGNAL_DISTRIBUTION_SPEC_v2.0.0.md
- PERFORMANCE_ANALYTICS_SPEC_v2.0.0.md
- OUTCOME_TRACKING_SPEC_v2.0.0.md
- TELEGRAM_UX_v2.0.0.md
- STRATEGY_PARAMETER_CONTROL_SPEC_v2.0.0.md

Depends on:
- SYSTEM_INVARIANTS_v2.0.0.md
- SYSTEM_ARCHITECTURE_MAP_v2.0.0.md
- MODULE_INTERFACE_SPEC_v2.0.0.md
- GOVERNANCE_AND_CHANGE_CONTROL_v2.0.0.md
- FAILURE_RECOVERY_SPEC_v2.0.0.md
- OBSERVABILITY_LOGGING_SPEC_v2.0.0.md

Code Alignment:
- bot_service.py
- core/signal_engine.py
- core/fsm_runtime.py
- core/strategy_v2.py
- core/distribution_router.py
- core/telegram_publisher.py
- core/observability_logger.py
- core/outcome_service.py
- core/analytics_engine.py
- deployment scripts
- service definitions
- restart wrappers
- audit/export scripts

## 0. Purpose

This document defines the canonical deployment and release protocol for BinaryBot / DROPi Signals.

Its role is to ensure that every production-affecting change is:
- documented before execution
- backed up before modification
- auditable before and after restart
- recoverable if abnormal behavior appears
- aligned with the active canonical architecture

Deployment is not a convenience action and not an experimentation surface. A deployment is a governed system mutation with mandatory proof.

This document does not define trading logic, UX wording, or signal scoring rules themselves. It defines how approved system changes are introduced into runtime safely.

## 1. Canonical Position

This document sits at the operational boundary between governance, implementation, runtime safety, restart control, observability, and rollback.

It exists to answer six questions:

1. When a change is allowed to reach runtime.
2. What evidence must exist before execution.
3. How patch execution must be performed.
4. What must be verified immediately after restart.
5. What conditions invalidate the deployment.
6. How rollback must be executed and proven.

If operational behavior conflicts with this document, runtime procedure must be corrected or this document must be canonically updated before further deployments proceed.

## 2. Final Principle

No deployment is valid if it changes live behavior without prior documentation alignment, backup protection, restart verification, and post-change proof.

A deployment is considered non-canonical if it introduces:
- undocumented production behavior
- patch execution without backup
- runtime mutation without audit trail
- restart without post-restart verification
- rollback impossibility
- hidden drift between docs, code, config, and live behavior

## 3. Deployment Scope

This protocol applies to:
- code patches
- runtime scripts
- orchestration scripts
- admin command surfaces
- config structure changes
- canonical documentation-linked releases
- restart-affecting operational procedures
- state-sensitive runtime changes
- deployment wrappers and rollback flows

This protocol applies whether the change is small or large. Severity changes validation depth, not the obligation to follow protocol.

## 4. Deployment Classes

### 4.1 Patch Deployment

A patch deployment is a narrow operational or implementation correction that does not intentionally change canonical strategy behavior or architectural ownership.

Typical examples:
- bug fix
- logging fix
- export fix
- admin command wiring correction
- restart wrapper correction
- proof-generation correction

Minimum requirements:
- documentation reference to the canonical area being fixed
- backup before modification
- pre-scan
- post-scan
- controlled restart
- post-restart audit
- output_docs evidence package

### 4.2 Minor Deployment

A minor deployment introduces bounded behavioral change within already approved architecture.

Typical examples:
- admin control surface improvement
- observability enrichment
- distribution rule refinement within existing canonical boundaries
- deployment tooling improvement
- state validation upgrade
- safe parameter-control pathway refinement

Minimum requirements:
- canonical docs aligned before code change
- explicit statement of intended behavioral delta
- backup before modification
- pre-scan
- post-scan
- controlled restart
- observability confirmation
- output_docs evidence package
- rollback-ready state

### 4.3 Major Deployment

A major deployment changes architecture, ownership boundaries, or core system behavior.

Typical examples:
- pipeline order change
- new module ownership boundary
- state model redesign
- event contract redesign
- new distribution architecture layer
- strategic lifecycle redesign

Minimum requirements:
- canonical documents updated first
- governance approval path satisfied
- dependency impact explicit
- test plan coverage explicit
- backup before modification
- pre-scan
- post-scan
- controlled restart
- deep post-restart audit
- rollback-ready state
- output_docs evidence package

## 5. Canonical Preconditions

No deployment may begin unless all of the following are true:

1. The relevant canonical documents already describe the intended system truth.
2. The change purpose is named explicitly.
3. The target files or target operational surfaces are identified explicitly.
4. A rollback path exists.
5. A backup path exists.
6. An audit/export path exists in output_docs.
7. Restart method is known in advance.
8. Success criteria are stated in advance.

If any of the above is missing, deployment must not proceed.

## 6. Mandatory Evidence Package

Every deployment must produce a proof package in the standard output location.

Minimum required artifacts:
- step report
- before snapshot
- after snapshot
- diff or equivalent delta proof
- pre-scan evidence
- post-scan evidence
- restart evidence
- post-restart audit evidence
- rollback evidence if failure occurs

If command output is large, it must be exported into files rather than relied upon as terminal-only output.

The purpose of the evidence package is not convenience. It is auditability, reproducibility, and operator protection.

## 7. Standard Output Location Rule

Deployment evidence must be written to the standard output_docs structure.

The deployment workflow must not depend on scrollback memory or incomplete terminal history.

Minimum rule:
- every deployment step has its own named output bundle
- every bundle contains enough evidence to reconstruct what changed
- every bundle identifies the canonical basis for the change
- every bundle states whether the intended result was achieved

## 8. Backup Rule

No production-affecting mutation may occur without backup created first.

Backup must cover, as relevant:
- files to be modified
- state files at risk
- config files at risk
- scripts being replaced
- docs being replaced or deprecated
- service definitions if touched

Backup location must be explicit and time-scoped.

A backup is invalid if:
- it is created after mutation
- it is incomplete relative to touched surfaces
- it cannot support rollback
- it is not referenced in the step report

## 9. Pre-Deployment Scan Rule

Before mutation, the operator must scan the relevant target surface and record the current state.

The pre-scan must answer:
- what exists now
- where the target currently lives
- what content is being replaced or affected
- whether dependent docs or modules already exist
- whether the intended target path is correct
- whether naming/versioning is already occupied

No patch should be written blindly against assumed content.

## 10. Change Execution Rule

A deployment patch must modify only the declared target surfaces required by the approved purpose.

Execution must:
- be step-named
- be bounded in scope
- produce evidence files
- avoid hidden side effects
- avoid undeclared cross-surface mutation
- preserve rollback capability

A deployment step is invalid if it claims one purpose but changes unrelated surfaces without declaration.

## 11. Documentation-First Rule

When the change affects architecture, contracts, governance, state ownership, deployment protocol, observability semantics, distribution policy, or other canonical behavior, documentation must be aligned before code implementation.

Code must not become the source of truth ahead of canonical docs in these cases.

This rule exists to prevent silent architecture drift.

## 12. Restart Rule

Where a deployment affects runtime behavior, restart must be treated as an auditable phase, not as an informal follow-up.

Restart procedure must:
1. preserve rollback readiness
2. use the intended service control path
3. verify startup health
4. verify no immediate crash loop
5. verify expected modules initialize correctly
6. verify no obvious invariant break appears
7. produce restart evidence in output_docs

A restart is not considered complete merely because a process appears running.

## 13. Post-Restart Audit Rule

After restart, the system must be checked against the stated success criteria.

Audit depth depends on the change, but must typically include:
- service alive state
- absence of crash loop
- expected command surface available if affected
- expected module load behavior if affected
- no obvious state corruption
- no obvious routing corruption
- no duplicate emission anomaly
- no immediate invariant break visible in logs or structured outputs

A deployment remains provisional until post-restart audit passes.

## 14. Failure Conditions

Deployment is considered failed if any of the following occurs:
- target content not applied as intended
- wrong files mutated
- active canonical path missing after deployment
- deprecated move incomplete where applicable
- service fails to start
- restart enters crash loop
- expected feature absent after restart
- logs show immediate invariant break
- state corruption appears
- routing corruption appears
- duplicate or anomalous signal behavior appears
- audit evidence is missing or contradictory

Failure requires explicit acknowledgement in the step report.

## 15. Rollback Rule

If deployment failure occurs, rollback must be executed using the prepared backup path.

Rollback must:
1. stop unsafe runtime if needed
2. restore affected files or states
3. restore expected operational layout
4. restart cleanly if runtime was affected
5. verify post-rollback stability
6. generate rollback evidence

Rollback is not optional where runtime safety or canonical integrity is compromised.

## 16. State Protection Rule

Deployments must preserve the integrity of state-bearing surfaces.

This includes, where relevant:
- FSM state
- cooldown-related persistence
- focus/watchlist state
- symbol activation state
- distribution state
- persisted analytics/research state if touched
- proof/audit logs that should remain intact

A deployment must not casually erase or overwrite persistent state unless the change explicitly governs that action and the rollback path is proven.

## 17. Config Safety Rule

Configuration must not drift silently during deployment.

If a deployment changes config shape, expected keys, default semantics, or loader behavior, the deployment must explicitly prove:
- compatibility expectations
- migration behavior if any
- failure behavior if config is invalid
- post-restart load correctness

Config mutation without explicit validation is non-canonical.

## 18. Service Control Rule

Service control commands and wrappers used during deployment must be explicit, consistent, and auditable.

The deployment package must make clear:
- what service or process was targeted
- how stop/start/restart was performed
- whether wrapper scripts were used
- what evidence confirms the result

The operator must not rely on assumption or memory for service identity.

## 19. Scope Integrity Rule

A deployment step must do exactly what its stated purpose claims.

If the stated purpose is:
- promote a canonical doc
- deprecate a legacy doc
- patch a command
- repair a service wrapper
- align a module boundary

then the executed mutation must match that purpose closely.

Scope inflation without declaration breaks auditability.

## 20. Naming and Versioning Rule

Deployment artifacts must preserve canonical naming discipline.

This includes:
- correct versioned canonical file names
- correct active/deprecated folder placement
- explicit superseded timestamps for deprecated documents
- consistent step IDs for reports
- stable output_docs naming

A change is operationally weaker if the naming layer is ambiguous, even when content is technically correct.

## 21. Active/Deprecated Transition Rule

When a root or legacy document is replaced by a canonical active version:
1. the active canonical target must already exist correctly
2. the legacy source must be backed up
3. the legacy source may then be moved to canonical/deprecated
4. the move must be proven in output_docs
5. post-checks must confirm active present, deprecated present, old root removed

No legacy deprecation step is valid if active canonical placement is still uncertain.

## 22. Deployment Proof Standard

A deployment is considered operationally proven only when an independent reviewer can inspect the generated evidence and answer:
- what was intended
- what was changed
- what existed before
- what exists after
- whether restart was healthy
- whether the goal was achieved
- whether rollback was available

If the answer to these questions is not reconstructable from the artifact bundle, the deployment is under-proven.

## 23. Forbidden Deployment Behaviors

The following are non-canonical:
- editing production-affecting files without backup
- patching against assumed content without scan
- skipping output_docs evidence
- restarting without audit
- declaring success without post-checks
- changing more than the declared target without stating so
- relying on terminal scrollback as sole proof
- implementing architecture before documenting it canonically
- treating deployment as informal experimentation
- leaving ambiguous whether rollback is possible

## 24. Canonical Deployment Sequence

The canonical deployment sequence is:

1. define purpose
2. identify canonical basis
3. identify target surfaces
4. prepare backup path
5. prepare output_docs path
6. scan current state
7. execute bounded mutation
8. export before/after/diff evidence
9. restart if runtime-affecting
10. perform post-restart audit
11. declare success or failure explicitly
12. rollback if failure criteria are met

This sequence may be expanded, but not violated.

## 25. Minimal Step Report Structure

Each deployment step should record at minimum:
- step ID
- timestamp
- purpose
- targets
- backup location
- before evidence file
- after evidence file
- diff evidence file
- restart evidence
- post-check results
- final result statement

This creates uniform operational reading across all patch steps.

## 26. Relationship to Test and Governance

This protocol does not replace governance and does not replace testing.

Governance decides whether a change is allowed.  
Testing increases confidence that the change behaves correctly.  
Deployment protocol controls how the approved change reaches runtime safely.

All three are required for disciplined evolution.

## 27. Relationship to Observability and Recovery

This protocol depends on observability and recovery, but does not replace them.

Observability provides proof.  
Recovery provides fallback.  
Deployment protocol binds both into the execution pathway.

A system without this binding is operationally fragile even if each document exists separately.

## 28. Success Standard

A deployment is successful only when:
- the declared target was changed correctly
- evidence bundle is complete
- backup exists
- restart behavior is healthy if runtime-affecting
- post-restart audit passes
- no failure condition is triggered
- canonical integrity is preserved

Anything less is incomplete success at best and deployment failure at worst.

## 29. Final Enforcement Statement

No future production-affecting deployment may bypass the rules in this document.

If a faster path conflicts with this protocol, the faster path is non-canonical.

Operational speed is permitted only inside canonical control, never instead of it.