# ADMIN_CONTROL_SPEC_v2.0.1.md

BinaryBot — Admin Control Surface Specification  
Version: 2.0.1  
Status: ACTIVE CANONICAL  
Path: `send/docs/canonical/active/ADMIN_CONTROL_SPEC_v2.0.1.md`  
Supersedes: `ADMIN_CONTROL_SPEC_v2.0.0.md`  

Linked Documents:
- ADMIN_SURFACE_AND_CONTROL_PLANE_CANON_v2.0.1.md
- ADMIN_OPERATIONS_SPEC_v2.0.1.md
- ADMIN_TREE_MAP_v2.0.1.md
- CONTROL_PANEL_HIERARCHY_AND_INTELLIGENCE_SPEC_v2.0.1.md
- ROLE_AND_PERMISSION_MATRIX_SPEC_v2.0.1.md
- TELEGRAM_UX_v2.0.1.md
- SIGNAL_DISTRIBUTION_SPEC_v2.0.1.md
- CHANNEL_CONFIG_SPEC_v2.0.1.md
- DECISION_AUDIT_SPEC_v3.0.0.md
- TRADE_TEMPORAL_TELEMETRY_SPEC_v3.0.0.md
- OUTCOME_TRACKING_SPEC_v3.0.0.md
- COMMUNITY_FEEDBACK_AND_PRIVACY_SPEC_v3.0.0.md
- PERFORMANCE_ANALYTICS_SPEC_v3.0.0.md
- RESEARCH_AND_LEARNING_FRAMEWORK_SPEC_v3.0.0.md
- STRATEGY_INTELLIGENCE_SYSTEM_v3.0.0.md
- TRADE_PHYSICS_INTELLIGENCE_SPEC_v1.0.0.md
- AUTONOMOUS_STRATEGY_EVOLUTION_SYSTEM_v3.0.0.md
- OBSERVABILITY_LOGGING_SPEC_v3.0.0.md
- EVENT_SCHEMA_SPEC_v3.0.0.md
- GOVERNANCE_AND_CHANGE_CONTROL_v2.0.1.md
- HUMAN_COMPREHENSION_AND_SELF_EXPLAINING_CONTROL_SURFACE_CANON_v1.0.1.md

---

## 0. Patch status

`ADMIN_CONTROL_SPEC_v2.0.1.md` is active canonical under the executed atomic promotion; `ADMIN_CONTROL_SPEC_v2.0.0.md` is superseded.

This v2.0.1 successor preserves the admin control model, roles/action boundaries and operator capabilities of v2.0.0. Changes are reference/truth-source alignment only.

No new permission or production mutation authority is created.

---

## 1. Purpose

This document defines the canonical admin control surface through which authorized human roles can:
- inspect live operational state;
- inspect decision/signal lifecycle state;
- manage future symbol/coverage scope where authorized;
- manage distribution configuration/publication readiness where authorized;
- inspect research, analytics, audit, Trade Physics and intelligence outputs;
- trigger approved operational actions;
- access canonical documentation/proof artifacts;
- supervise affiliate/distribution/admin activity according to role.

Detailed permission authority remains in:
- `ADMIN_OPERATIONS_SPEC_v2.0.1.md`;
- `ROLE_AND_PERMISSION_MATRIX_SPEC_v2.0.1.md`;
- `CONTROL_PANEL_HIERARCHY_AND_INTELLIGENCE_SPEC_v2.0.1.md`.

This document defines what the admin surface exposes and what safety principles apply; it does not create permissions by itself.

---

## 2. Canonical Position and Truth Domains

The admin surface is not Strategy, FSM, Signal Engine, Distribution, Telemetry or Intelligence authority.

It exposes governed views over distinct truth domains.

### Operational Truth
Service health, engine state, queue/routing state, cooldown, incidents, freezes, recovery and process health.

### Decision / Strategy Truth
DecisionObject, score, TPS/Trade Physics readiness where active, gates, rejection reasons, PRE/CONFIRM/OPEN_NOW strategic state and supporting model evidence.

### FSM / Execution Truth
Requested/accepted stage, lifecycle state, stage handoff readiness, trade-execution readiness, Signal Engine execution outcome and blockers where authorized.

### Market / Timing Truth
Corridor, directional structural space, Time Model state, model expiry, temporal pressure and objective post-trade telemetry.

### Outcome / Feedback Truth
This domain MUST remain source-separated:
- objective market outcome -> Trade Temporal Telemetry;
- operational/admin reconciliation -> Outcome Tracking;
- community/member self-report -> Community Feedback.

The UI must not collapse these into one unlabeled “result”.

### Research / Learning Truth
Performance analytics, TPS/model calibration analytics, rejection analytics, experiment history, intelligence summaries and evolution recommendations.

### Distribution Truth
Route state, entitlement, destination mapping, route publish evidence, affiliate routing and publication health.

Admin surfaces expose these domains without changing their owners.

---

## 3. Design Principles

### Role-scoped visibility
Only authorized data/actions are shown.

### No hidden mutation
Every future-behavior mutation is explicit, logged and attributable.

### Future-facing control
Admin changes future behavior/configuration; historical truth is not silently rewritten.

### Truth-domain separation
Operational, strategy, FSM/execution, market telemetry, operational outcomes, community feedback, distribution and research truth remain distinguishable.

### Auditability first
Mutating actions record actor, timestamp, scope and result.

### Read-only by default
Unsafe write access is never the default interaction pattern.

### Canonical-document-driven control and comprehension
Panels map to active canonical ownership and provide contextual explanations for material terms/metrics/controls.

---

## 4. Primary Entry Points

Logical areas remain:
- Admin Home;
- Operations;
- Symbols & Coverage;
- Decision Visibility;
- Distribution Control;
- Research & Analytics;
- Intelligence;
- Affiliate / Partner Oversight;
- Documentation & Governance;
- System Health & Recovery.

Telegram presentation belongs to `TELEGRAM_UX_v2.0.1.md`.
Hierarchy belongs to `ADMIN_TREE_MAP_v2.0.1.md` and `CONTROL_PANEL_HIERARCHY_AND_INTELLIGENCE_SPEC_v2.0.1.md`.

---

## 5. Admin Home

Role-appropriate summary may show:
- system/engine status;
- signal pipeline state;
- operational mode;
- coverage scope;
- incidents/freezes;
- focus/readiness highlights;
- recent important admin actions;
- recent distribution events;
- links to specialized panels.

It is a launch/summary surface, not a replacement for specialized panels.

---

## 6. Operations Panel

Role-scoped visibility includes:
- engine running/paused/frozen;
- watchdog/process health;
- restart/recovery state;
- incidents;
- cooldown state;
- queue pressure;
- publishing state;
- restrictions/warnings.

Where authorized, controlled actions may include:
- pause approved future activity;
- freeze selected distribution outputs;
- disable publication pathways;
- acknowledge incidents;
- trigger approved recovery workflows;
- request diagnostic snapshots.

No undocumented “magic” controls are allowed.

---

## 7. Symbols & Coverage Panel

Controls future monitoring/publication coverage.

May show/manage where permitted:
- active/disabled symbols;
- symbol groups;
- market/category activation;
- coverage limits;
- support constraints;
- readiness restrictions.

Rules:
- changes prospective;
- changes audited;
- historical decisions/outcomes unchanged;
- symbol availability distinct from decision readiness.

---

## 8. Decision Visibility Panel

Authorized users may inspect:
- candidate/DecisionObject state;
- rejection reasons;
- gate results;
- classical score composition;
- TPS and S/T/P/V evidence where active;
- Trade Physics readiness;
- learned probability plus model/readiness provenance when valid;
- focus state;
- PRE/CONFIRM/OPEN_NOW strategy progression;
- FSM requested/accepted stage and reasons;
- why an opportunity is blocked/delayed/degraded/rejected;
- Signal Engine execution outcome where relevant.

Visibility is not override authority.

Data aligns with:
- `DECISION_AUDIT_SPEC_v3.0.0.md`;
- `TRADE_TEMPORAL_TELEMETRY_SPEC_v3.0.0.md`;
- `OBSERVABILITY_LOGGING_SPEC_v3.0.0.md`.

---

## 9. Distribution Control Panel

May expose:
- route/channel availability;
- topic/route health;
- entitlement state;
- publication readiness;
- mute/freeze state;
- affiliate/partner distribution visibility;
- dispatch audit status;
- fallback/degraded state.

It does not decide signal validity.

Aligns with:
- `SIGNAL_DISTRIBUTION_ARCHITECTURE_v2.0.1.md`;
- `SIGNAL_DISTRIBUTION_SPEC_v2.0.1.md`;
- `CHANNEL_CONFIG_SPEC_v2.0.1.md`;
- `TELEGRAM_UX_v2.0.1.md`.

---

## 10. Research & Analytics Panel

May expose:
- signal counts by lifecycle stage;
- rejection analytics;
- symbol/session performance;
- objective market outcome distributions;
- operational outcome distributions;
- community feedback distributions;
- TPS distributions/components;
- model calibration/readiness/drift analytics;
- experiments;
- temporal patterns;
- authorized channel/affiliate performance.

Truth source must be labelled.

Aligns with:
- `OUTCOME_TRACKING_SPEC_v3.0.0.md`;
- `COMMUNITY_FEEDBACK_AND_PRIVACY_SPEC_v3.0.0.md`;
- `PERFORMANCE_ANALYTICS_SPEC_v3.0.0.md`;
- `RESEARCH_AND_LEARNING_FRAMEWORK_SPEC_v3.0.0.md`.

---

## 11. Intelligence Panel

May expose:
- strategy intelligence;
- Trade Physics intelligence/model readiness;
- anomalies;
- recommendation queues;
- experiment candidates;
- approval-needed items;
- learning snapshots;
- drift warnings;
- change-risk notices.

Recommendations do not auto-modify production.

Aligns with:
- `STRATEGY_INTELLIGENCE_SYSTEM_v3.0.0.md`;
- `TRADE_PHYSICS_INTELLIGENCE_SPEC_v1.0.0.md`;
- `AUTONOMOUS_STRATEGY_EVOLUTION_SYSTEM_v3.0.0.md`;
- `GOVERNANCE_AND_CHANGE_CONTROL_v2.0.1.md`.

---

## 12. Affiliate / Partner Oversight

Role-scoped affiliate area may expose:
- affiliate status;
- partner routing visibility;
- referral counts;
- commission summaries;
- campaign state;
- limited support actions;
- abuse indicators;
- payout/accrual review.

Affiliate scope never grants unrestricted system admin or strategy access.

---

## 13. Documentation & Governance

The admin surface must provide governed access to:
- active canonical documents;
- implementation/alignment matrices;
- change-control references;
- governance/audit records;
- approved playbooks;
- version references.

Superseded/deprecated/intake documents must not be presented as current truth. If shown for provenance, their status must be explicit.

---

## 14. System Health & Recovery

May expose:
- service/dependency health;
- restart history;
- incidents;
- degraded mode;
- authorized recovery procedures;
- latest proof/audit snapshot;
- alert acknowledgements.

Recovery actions remain governed and logged.

---

## 15. Role-Scoped Visibility Model

Conceptual role family remains:
- Owner;
- Primary Admin;
- Functional Admin;
- Affiliate Admin;
- read-only/analyst-style roles;
- limited support/moderation roles where retained.

Exact permissions belong to `ROLE_AND_PERMISSION_MATRIX_SPEC_v2.0.1.md`.

Owner may view all panels and approve owner-reserved actions under Governance.
Primary Admin may operate full control surface except owner-reserved governance powers.
Functional Admin is domain-scoped.
Affiliate Admin is affiliate-scoped.
Read-only roles inspect only permitted surfaces.

Invisible controls are preferred where a role should not know a capability exists.

---

## 16. Action Classes

- Read actions: no mutation.
- Operational controls: governed future operation/routing/readiness mutation.
- Governance-bound actions: stronger approval/justification required.
- Emergency actions: only documented emergency procedures.

UI must distinguish action classes.

---

## 17. Required Audit Trail

Every mutating admin action records:
- actor identity;
- role;
- timestamp;
- action;
- target scope;
- justification where required;
- approval context where required;
- result;
- downstream effect status if known.

---

## 18. Prohibited Behaviors

Admin surface MUST NOT:
- expose unauthorized controls;
- rewrite historical decision/telemetry/outcome/community truth;
- bypass readiness gates without governed emergency policy;
- auto-accept intelligence recommendations into production;
- silently alter distribution scope;
- mix affiliate role with unrestricted admin;
- rely on superseded documents as current truth;
- present research inference as execution fact;
- fabricate TPS/model probability/readiness;
- collapse truth sources into one ambiguous result.

---

## 19. Minimum Implementation Guarantee

Correct implementation produces:
- governed operator control;
- role-scoped visibility/actionability;
- auditable future-facing mutation;
- truth-domain separation;
- consistent canonical documentation access;
- analytics/intelligence visibility without shadow authority;
- compatibility with Trade Physics and staged execution.

---

## 20. Self-Explaining Admin Surface Requirement

Stable admin surfaces comply with `HUMAN_COMPREHENSION_AND_SELF_EXPLAINING_CONTROL_SURFACE_CANON_v1.0.1.md`.

Subsystem names, states, parameters, thresholds, metrics, controls and acronyms must not be treated as self-evident when interpretation matters to safe operation/governance.

A displayed definition does not grant mutation authority.

---

## 21. PATCH Migration Note

v2.0.1 preserves v2.0.0 control-plane behavior and role/action classes.

Changes are limited to:
- final successor references;
- explicit multi-truth outcome/feedback display semantics;
- explicit Trade Physics/TPS/model-readiness visibility as governed information;
- staged-execution truth visibility;
- Human Comprehension v1.0.1 reference alignment.

No new admin permission, route authority, strategy override or automatic model mutation is introduced.

---

## 22. Version History

| Version | Date | Description |
|---|---|---|
| 2.0.1 | 2026-09-01 | Proposed PATCH: reference and truth-domain presentation alignment for Trade Physics/staged execution. |
| 2.0.0 | 2026-07-12 | Active canonical admin control surface specification. |

---

End of ADMIN_CONTROL_SPEC_v2.0.1.md