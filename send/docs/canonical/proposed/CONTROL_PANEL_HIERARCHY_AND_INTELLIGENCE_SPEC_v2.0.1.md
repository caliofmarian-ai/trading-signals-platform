# CONTROL_PANEL_HIERARCHY_AND_INTELLIGENCE_SPEC_v2.0.1.md

BinaryBot — Control Panel Hierarchy and Intelligence Specification  
Version: 2.0.1  
Status: PROPOSED PATCH SUCCESSOR — NOT ACTIVE CANONICAL  
Path: /opt/binarybot/docs/canonical/proposed/CONTROL_PANEL_HIERARCHY_AND_INTELLIGENCE_SPEC_v2.0.1.md  
Supersession Intent: `CONTROL_PANEL_HIERARCHY_AND_INTELLIGENCE_SPEC_v2.0.0.md`

Linked Documents:
- ADMIN_CONTROL_SPEC_v2.0.1.md
- ROLE_AND_PERMISSION_MATRIX_SPEC_v2.0.1.md
- ADMIN_TREE_MAP_v2.0.1.md
- ADMIN_OPERATIONS_SPEC_v2.0.1.md
- GOVERNANCE_AND_CHANGE_CONTROL_v2.0.1.md
- DECISION_AUDIT_SPEC_v3.0.0.md
- SIGNAL_DISTRIBUTION_SPEC_v2.0.1.md
- CHANNEL_CONFIG_SPEC_v2.0.1.md
- OBSERVABILITY_LOGGING_SPEC_v3.0.0.md
- RESEARCH_AND_LEARNING_FRAMEWORK_SPEC_v3.0.0.md
- STRATEGY_INTELLIGENCE_SYSTEM_v3.0.0.md
- PERFORMANCE_ANALYTICS_SPEC_v3.0.0.md
- OUTCOME_TRACKING_SPEC_v3.0.0.md
- HUMAN_COMPREHENSION_AND_SELF_EXPLAINING_CONTROL_SURFACE_CANON_v1.0.1.md

---

## 0. PATCH SCOPE

This successor preserves the hierarchy, visibility model, action types, RBAC boundaries and intelligence/control separation of v2.0.0.

The patch only updates normative references and version/status/path metadata. No new control, permission, panel authority, mutation path, or automatic intelligence-to-production pathway is introduced.

Until explicit active promotion, `CONTROL_PANEL_HIERARCHY_AND_INTELLIGENCE_SPEC_v2.0.0.md` remains authoritative.

---

## 1. PURPOSE

This document defines the canonical hierarchy, visibility model, control surfaces and intelligence surfaces of the BinaryBot control panel.

The control panel is the governed human control system through which authorized actors can:

- monitor operational state
- supervise strategy behavior without violating historical truth
- control future-facing operational state
- control publication and distribution readiness
- inspect decision and rejection logic
- analyze observability and performance outputs
- supervise affiliate and commercial functions within scoped boundaries
- access research and intelligence outputs according to role and scope
- administer approved platform operations

This document must remain aligned with:

- `ADMIN_CONTROL_SPEC_v2.0.1.md`
- `ROLE_AND_PERMISSION_MATRIX_SPEC_v2.0.1.md`
- `ADMIN_TREE_MAP_v2.0.1.md`
- `ADMIN_OPERATIONS_SPEC_v2.0.1.md`
- `GOVERNANCE_AND_CHANGE_CONTROL_v2.0.1.md`
- `DECISION_AUDIT_SPEC_v3.0.0.md`
- `OBSERVABILITY_LOGGING_SPEC_v3.0.0.md`

The v2 hierarchy replaced the older flatter panel framing with:

- governed layer separation
- clearer distinction between control surfaces and intelligence surfaces
- explicit owner → primary admin → functional admin structure
- explicit affiliate isolation
- explicit read/write/governance separation
- alignment with decision-audit and observability architecture
- compatibility with AI/research/reporting layers without collapsing RBAC boundaries

---

## 2. CORE DESIGN POSITION

The control panel is not merely an admin menu.

It is the operational governance interface of BinaryBot.

That means:

- it must reflect canonical authority boundaries
- it must distinguish visibility from control
- it must distinguish operational control from governance authority
- it must distinguish decision inspection from decision mutation
- it must distinguish research insight from production authority
- it must remain fully auditable for every privileged action

The panel is therefore modeled on two major axes:

1. **Control Hierarchy Axis** — who may act
2. **Intelligence & Insight Axis** — what system truth can be inspected

These two axes intersect, but they are not the same thing.

---

## 3. CANONICAL PANEL AXES

### 3.1 Control Hierarchy Axis
Defines the authority-bearing operational layers.

### 3.2 Intelligence & Insight Axis
Defines the research, diagnostics, audit and interpretability layers that expose system truth.

### 3.3 Commercial / Affiliate Axis
Defines the scoped partner-facing layer for referral and affiliate functions.

### 3.4 Documentation / Governance Axis
Defines the panel surfaces that expose governed references, procedures and change-control context to authorized roles.

---

## 4. CANONICAL TOP-LEVEL PANEL STRUCTURE

The canonical control panel is structured conceptually as follows:

```text
CONTROL PANEL
├── Owner Layer
├── Primary Admin Layer
├── Functional Admin Layer
│   ├── Operations Surface
│   ├── Distribution Surface
│   ├── Observability Surface
│   ├── Research Surface
│   ├── Affiliate Program Operations Surface
│   └── Support / Community Surface
├── Analyst / Read-Only Surface
├── Affiliate / Influencer Surface
├── Intelligence Layer
│   ├── Decision Intelligence
│   ├── Debug & Rejection Visibility
│   ├── Performance & Outcome Analytics
│   ├── Drift / Anomaly / Recommendation Summaries
│   └── Research & Learning Views
├── Governance / Documentation Layer
└── Security / Audit Layer
```

Important:

- not every role sees every top-level node
- some layers are visibility-only for certain roles
- some nodes are absent rather than disabled when unauthorized
- governance and security nodes are not ordinary operational menus

---

## 5. ROLE-HIERARCHY VIEW OF THE PANEL

The control panel hierarchy must align with the canonical role system.

Primary role families:

- **Owner**
- **Primary Admin**
- **Functional Admin**
- **Analyst / Read-only specialist**
- **Support / Moderator-style limited role**
- **Affiliate Admin**
- **User**

Important hierarchy rule:

Higher placement in the hierarchy does not erase governance rules, scope restrictions or audit requirements.

---

## 6. OWNER LAYER

The Owner Layer is the supreme governance and oversight layer.

It provides access to all governed surfaces, including:

- system-wide operational control
- strategy oversight
- distribution oversight
- research and intelligence oversight
- affiliate oversight
- audit and governance records
- role and hierarchy supervision
- security-sensitive views as allowed by security policy

Typical Owner-facing surfaces include:

- global system summary
- admin hierarchy control
- governed configuration control
- cross-domain visibility dashboards
- approval queues for governance-bound changes
- research and intelligence meta-summary
- high-sensitivity audit visibility

Restrictions:

- the Owner must still act through governed interfaces
- the Owner must not depend on hidden undocumented commands
- the Owner should not silently rewrite historical records

---

## 7. PRIMARY ADMIN LAYER

The Primary Admin Layer is the principal day-to-day operational layer below the Owner.

This layer is designed for broad operational control, but not unrestricted governance control.

Primary Admin surfaces may include:

- operational health summary
- distribution readiness summary
- approved future-facing control actions
- admin coordination tools
- incident triage views
- scoped research and intelligence views needed for daily operation
- operational dashboards spanning multiple functional domains

Restrictions:

- no silent governance rule mutation
- no undocumented role-architecture mutation
- no Owner-reserved approval powers unless explicitly delegated

---

## 8. FUNCTIONAL ADMIN LAYER

The Functional Admin Layer is domain-specialized.

It must be split into explicit domain surfaces rather than a generic undifferentiated admin bucket.

Canonical functional surfaces include:

### 8.1 Operations Surface
Used for operational continuity and approved system-state control.

Typical contents:

- status summary
- service health
- freeze / pause / readiness views
- restart and recovery actions where authorized
- incident context

### 8.2 Distribution Surface
Used for publication, routing and distribution control.

Typical contents:

- channel readiness
- routing assignments
- publish-state control
- distribution health
- channel-tier configuration views

### 8.3 Observability Surface
Used for inspection of logs, incidents, metrics and diagnostics.

Typical contents:

- service-level summaries
- alert views
- diagnostic log summaries
- incident timelines
- audit-linked observability references

### 8.4 Research Surface
Used for governed analytical review.

Typical contents:

- performance summaries
- rejection analytics
- outcome analytics
- experiment candidate reviews
- report export or review views

### 8.5 Affiliate Program Operations Surface
Used only by authorized roles handling affiliate operations.

Typical contents:

- affiliate onboarding workflow views
- campaign status summaries
- commission processing support views
- scoped partner issue handling

### 8.6 Support / Community Surface
Used for limited community or support functions if implemented.

Typical contents:

- user support workflows
- moderation summaries
- limited communication controls
- issue escalation routing

Important restrictions:

- a functional admin sees only assigned surfaces
- functional authority is scoped by domain
- no functional admin has automatic all-domain access
- no functional admin has automatic governance authority

---

## 9. ANALYST / READ-ONLY SURFACE

This surface is intended for research-oriented or diagnostic specialists who require insight without control mutation.

It may include:

- read-only performance dashboards
- read-only rejection analytics
- read-only observability summaries
- governed exports
- historical diagnostic comparisons
- recommendation review surfaces where visibility is allowed

It must not include:

- parameter mutation
- distribution mutation
- role management
- governance-sensitive write controls

---

## 10. AFFILIATE / INFLUENCER SURFACE

The Affiliate / Influencer Surface exists for commercial partner-facing use.

This is not a technical admin surface.

It must be strictly isolated from global control surfaces.

Permitted affiliate-facing sections may include:

- my referrals
- active referred users summary
- conversion summary
- commission summary
- affiliate campaign summary
- support / contact workflow
- approved affiliate documentation

Affiliate roles may inspect only their own scoped network or assigned scope.

Affiliate roles must not access:

- strategy internals
- engine diagnostics
- global admin data
- full-system research views
- unrelated user data
- role-management controls

---

## 11. INTELLIGENCE LAYER

The Intelligence Layer exposes system truth in interpretable form.

It is not equivalent to broad control authority.

Canonical sublayers include:

### 11.1 Decision Intelligence
Provides interpretable views into decision formation and gate outcomes.

Examples:

- decision-object visibility
- precondition summaries
- feasibility and corridor interpretations
- score composition views
- gate pass/fail summaries

### 11.2 Debug & Rejection Visibility
Provides explicit visibility into why signals were rejected or died.

Examples:

- rejection reason breakdown
- lifecycle failure views
- PRE / CONFIRM / OPEN_NOW failure segmentation
- gate-specific rejection counts
- symbol/session rejection patterns

This sublayer must align with `DECISION_AUDIT_SPEC_v3.0.0.md`.

### 11.3 Performance & Outcome Analytics
Provides governed review of system results.

Examples:

- outcome summaries
- cohort comparisons
- signal quality trends
- performance by session / symbol / route
- channel outcome differences where applicable

### 11.4 Drift / Anomaly / Recommendation Summaries
Provides intelligence outputs for higher-order operational awareness.

Examples:

- unusual rejection spikes
- distribution anomalies
- drift indicators
- candidate recommendation summaries
- confidence-qualified research prompts

### 11.5 Research & Learning Views
Provides long-form or aggregated learning-oriented surfaces.

Examples:

- strategy learning summaries
- longitudinal performance views
- hypothesis review boards
- governed experiment candidate dashboards

Important rule:

Reading intelligence does not automatically authorize acting on it.

---

## 12. GOVERNANCE / DOCUMENTATION LAYER

The panel must include a governed reference layer for authorized roles.

This layer may expose:

- active canonical specifications
- approved playbooks
- change-control status
- migration notices
- deprecation notes
- implementation alignment summaries

This layer exists to keep operators aligned with canonical truth and to reduce undocumented drift.

Access must be role-scoped.

---

## 13. SECURITY / AUDIT LAYER

The panel must expose security and audit surfaces only to authorized roles.

This layer may include:

- privileged action logs
- change history summaries
- role change audit trail
- security-sensitive incident references
- access-denial summaries
- approval-chain references

This is not a general-purpose operational panel.

It is a governed oversight surface.

---

## 14. PANEL VISIBILITY RULES

The panel must obey the following visibility rules:

### 14.1 Role-scoped visibility
A role sees only nodes relevant to its permissions and scope.

### 14.2 Invisible-by-default for unauthorized capability
Sensitive controls should usually be absent, not merely disabled.

### 14.3 Read versus write separation
A user may see a surface without seeing its mutating controls.

### 14.4 Domain separation
Distribution views do not imply strategy control.
Research views do not imply governance rights.
Affiliate views do not imply admin rights.

### 14.5 Governance separation
Approval surfaces are not ordinary operational controls.

### 14.6 Audit-first mutation
Every privileged mutating action launched from the panel must be audited.

---

## 15. PANEL ACTION TYPES

Every panel action must belong to a defined action type.

Canonical action types:

- **Inspect**
- **Control**
- **Manage**
- **Approve**
- **Export**
- **Acknowledge**
- **Escalate**

### 15.1 Inspect
Read-only examination of system state or governed outputs.

### 15.2 Control
Future-facing operational state mutation within authorized scope.

### 15.3 Manage
Administrative maintenance of assigned entities, users or configurations.

### 15.4 Approve
Governance-bound action requiring stronger authority.

### 15.5 Export
Governed extraction of allowed reports or data views.

### 15.6 Acknowledge
Operational acknowledgment of incidents, alerts or queued notices.

### 15.7 Escalate
Formal forwarding of an issue or decision to a higher authority layer.

---

## 16. TELEGRAM CONTROL INTERFACE

The control panel may be exposed through Telegram, but Telegram is only an interface layer, not the architecture itself.

Telegram commands must map to governed panel actions.

Illustrative command families may include:

- `/admin`
- `/status`
- `/ops`
- `/distribution`
- `/research`
- `/audit`
- `/affiliates`
- `/help`

Important:

- command exposure must remain role-scoped
- command results must respect visibility rules
- commands must not bypass approval or audit requirements
- the existence of a Telegram command does not grant universal access to that capability

---

## 17. AUDIT REQUIREMENTS FOR PANEL ACTIONS

Every privileged panel action must produce an audit trail.

Minimum fields:

- timestamp
- actor identity
- resolved role
- resolved scope
- surface or panel node
- action type
- requested action
- target entity
- before/after state where applicable
- approval context where applicable
- result

This must remain aligned with `OBSERVABILITY_LOGGING_SPEC_v3.0.0.md` and related audit specs.

---

## 18. PROHIBITED PANEL ANTI-PATTERNS

The control panel must not:

- collapse all admin functions into one unrestricted super-menu
- expose affiliate roles to technical admin surfaces
- conflate analytics visibility with strategy mutation rights
- allow operational roles to silently rewrite historical truth
- hide critical governance changes from audit
- expose security-sensitive controls casually
- treat read-only research roles as de facto admins
- allow undocumented backdoor control paths outside governed architecture

---

## 19. RELATION TO AI / RESEARCH EXPANSION

The panel may expose governed AI, research and reporting capabilities as those capabilities become active under their own canonical authorities.

Examples:

- strategy auditor summaries
- recommendation assistants
- longitudinal learning surfaces
- rejection intelligence views
- experiment candidate suggestion systems
- affiliate performance intelligence summaries

All such surfaces must obey:

- RBAC
- domain separation
- auditability
- governance boundaries
- affiliate isolation
- read/write distinction

New intelligence does not justify weaker control discipline.

---

## 20. MIGRATION NOTES FROM LEGACY VERSION

The legacy version was useful as an initial structure but had these limitations:

- mixed Romanian and English framing
- flatter admin/control assumptions
- insufficient distinction between control and intelligence
- insufficient governance/documentation layering
- simplified affiliate framing
- command-centric rather than authority-centric modeling
- weaker integration with the newer decision-audit architecture

The v2.0.0 specification replaced that with a clearer canonical model centered on:

- governed hierarchy
- scoped panel visibility
- control/intelligence separation
- affiliate isolation
- audit-first privileged operations
- compatibility with the broader post-legacy BinaryBot architecture

---

## 21. MINIMUM IMPLEMENTATION GUARANTEE

If implemented correctly, this specification ensures that the BinaryBot control panel becomes:

- a governed operational cockpit
- a safe multi-role control environment
- a visible but scoped intelligence interface
- a clean bridge between operations, research and audit
- a scalable admin architecture for future expansion

---

## 22. CONTROL-PLANE UX CLARIFICATIONS FROM ADMIN UX REVIEW

### 22.1 Hierarchical fit
Admin UX concepts are acceptable only where they preserve the active control-plane hierarchy and intelligence layering already defined in canonical active docs.

### 22.2 Presentation vs authority
Panels, tabs, dashboards, and grouping concepts are presentation aids; they do not redefine authority, permissions, or intelligence ownership.

### 22.3 Merge rule
Any useful concepts extracted from ADMIN_UX_V2_SPEC.md are subordinate to this canonical control-panel hierarchy.

---

## 23. HUMAN COMPREHENSION LAYER

The control-panel hierarchy MUST expose its operational meaning according to `HUMAN_COMPREHENSION_AND_SELF_EXPLAINING_CONTROL_SURFACE_CANON_v1.0.1.md`.

The panel MUST function as persistent operational memory for authorized users.

A returning authorized user MUST NOT require historical chat conversations or developer memory to understand a stable branch, its important states, or the consequences of permitted controls.

Explanation visibility does not imply mutation or governance authority.

---

## 24. VERSION HISTORY

| Version | Date | Description |
|---|---|---|
| 2.0.1 | 2026-09-01 | Proposed PATCH successor for canonical reference repair only; hierarchy, permission and control semantics unchanged. |
| 2.0.0 | 2026-07-12 | Active canonical control-panel hierarchy before this proposed patch. |

---

End of CONTROL_PANEL_HIERARCHY_AND_INTELLIGENCE_SPEC_v2.0.1.md
