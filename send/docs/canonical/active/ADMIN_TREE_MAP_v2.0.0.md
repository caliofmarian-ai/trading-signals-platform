# ADMIN_TREE_MAP_v2.0.0.md

BinaryBot — Admin Tree Map  
Version: 2.0.0  
Status: CANONICAL  
Path: /opt/binarybot/docs/canonical/active/ADMIN_TREE_MAP_v2.0.0.md

Linked Documents:
- ADMIN_CONTROL_SPEC_v2.0.0.md
- ROLE_AND_PERMISSION_MATRIX_SPEC_v2.0.0.md
- CONTROL_PANEL_HIERARCHY_AND_INTELLIGENCE_SPEC_v2.0.0.md
- ADMIN_OPERATIONS_SPEC_v2.0.0.md
- TELEGRAM_UX_v2.0.0.md
- SIGNAL_DISTRIBUTION_SPEC_v2.0.0.md
- CHANNEL_CONFIG_SPEC_v2.0.0.md
- DECISION_AUDIT_SPEC_v2.0.0.md
- OBSERVABILITY_LOGGING_SPEC_v2.0.0.md
- GOVERNANCE_AND_CHANGE_CONTROL.md

---

## 1. PURPOSE

This document defines the canonical structural map of the BinaryBot admin tree.

The admin tree map is the navigation and surface-organization reference for the operator control environment.  
It describes:

- top-level admin entry points
- second-level and third-level branches
- conceptual grouping of operational, analytical, governance and affiliate surfaces
- separation between visibility surfaces and control surfaces
- where major control and intelligence functions live in the admin environment

This document is a map, not a full permission matrix and not a full behavior specification.

Authority and action boundaries belong primarily to:

- `ROLE_AND_PERMISSION_MATRIX_SPEC_v2.0.0.md`
- `CONTROL_PANEL_HIERARCHY_AND_INTELLIGENCE_SPEC_v2.0.0.md`
- `ADMIN_CONTROL_SPEC_v2.0.0.md`
- `ADMIN_OPERATIONS_SPEC_v2.0.0.md`

---

## 2. DESIGN PRINCIPLES

The admin tree must obey the following principles:

### 2.1 Role-scoped navigation
A user must only see the branches relevant to their role and scope.

### 2.2 Domain separation
Operations, distribution, decision visibility, research, affiliate and governance branches must remain clearly separated.

### 2.3 Visibility versus control separation
Diagnostic and intelligence branches must not be confused with mutating operational controls.

### 2.4 Future-facing mutation only
Control branches affect future operation and future configuration, not historical truth.

### 2.5 Audit-first control actions
Any mutating action reachable from the tree must be auditable.

### 2.6 Canonical consistency
The tree must match the canonical admin architecture and must not reflect obsolete menu assumptions from legacy documents.

---

## 3. ROOT ENTRY

The canonical root entry remains:

`/admin`

This is the governed entry point into the BinaryBot control environment.

The root must render a role-appropriate navigation tree and summary context rather than a flat unrestricted menu.

---

## 4. CANONICAL ROOT TREE

```text
/admin
├── Home
├── Operations
├── Symbols & Coverage
├── Decision Visibility
├── Distribution Control
├── Research & Analytics
├── Intelligence
├── Affiliate / Partner
├── Roles & Identity
├── System Health
├── Governance & Docs
└── Security & Audit
```

Important rules:

- not every actor sees every root node
- some root nodes are hidden entirely for unauthorized roles
- root order may be adapted in UI, but conceptual grouping must remain stable
- root naming may be slightly adapted in Telegram UX, but semantic meaning must stay canonical

---

## 5. ROOT NODE DEFINITIONS

### 5.1 Home
Top-level summary and launch surface.

Purpose:
- show current operational snapshot
- show urgent notices
- show recent important state
- provide quick navigation into allowed subtrees

### 5.2 Operations
Operational state and approved future-facing controls.

Purpose:
- engine state
- incident and freeze visibility
- operational actions where authorized
- continuity and recovery pathways

### 5.3 Symbols & Coverage
Coverage and symbol activation surface.

Purpose:
- active scope
- allowed future coverage
- symbol grouping
- prospective symbol enable/disable management

### 5.4 Decision Visibility
Interpretability and decision-state inspection surface.

Purpose:
- why a signal passed, failed, downgraded or died
- lifecycle state
- readiness progression
- gate and rejection visibility

### 5.5 Distribution Control
Routing and publishing surface.

Purpose:
- channels
- destinations
- route state
- publication readiness
- distribution diagnostics

### 5.6 Research & Analytics
Structured analytical review surface.

Purpose:
- performance summaries
- rejection analytics
- outcome analytics
- report review and export

### 5.7 Intelligence
Higher-order intelligence and recommendation summaries.

Purpose:
- drift signals
- anomaly summaries
- recommendation candidates
- learning and research intelligence views

### 5.8 Affiliate / Partner
Commercial partner-facing or affiliate-operations surface.

Purpose:
- scoped referral visibility
- campaign metrics
- affiliate support workflows
- commission-oriented summaries within allowed scope

### 5.9 Roles & Identity
Identity and role-awareness surface.

Purpose:
- current actor identity
- scoped membership views
- role matrix visibility where allowed
- role-linked references

### 5.10 System Health
Technical health and operational diagnostics surface.

Purpose:
- service health
- observability summaries
- recent errors
- diagnostics and recovery references

### 5.11 Governance & Docs
Canonical references and governed documentation surface.

Purpose:
- active canonical specs
- implementation references
- change-control references
- migration and deprecation notes

### 5.12 Security & Audit
Privileged action history and sensitive oversight surface.

Purpose:
- admin action history
- access denials
- role-change audit
- approval-chain references
- security-sensitive audit summaries

---

## 6. DETAILED TREE MAP

### 6.1 Home

```text
/admin/home
├── Summary
├── Urgent Notices
├── Recent Important Actions
├── Current Mode
├── Coverage Snapshot
├── Publishing Snapshot
└── Quick Links
```

### 6.2 Operations

```text
/admin/operations
├── Engine State
├── Runtime Status
├── Freeze / Pause State
├── Incident Queue
├── Recovery Actions
├── Restart / Guarded Restart
├── Operational Restrictions
└── Ops Notes
```

### 6.3 Symbols & Coverage

```text
/admin/symbols
├── Active Symbols
├── Available Symbols
├── Symbol Groups
├── Coverage Rules
├── Enable / Disable Scope
├── Save Coverage Selection
└── Coverage Diagnostics
```

### 6.4 Decision Visibility

```text
/admin/decision
├── Current Candidate
├── Last Decision
├── Decision Object View
├── Lifecycle State
├── Gate Results
├── Reject Reasons
├── Score Composition
├── Corridor / Timing Context
└── Focus / Feasibility State
```

### 6.5 Distribution Control

```text
/admin/distribution
├── Route Status
├── Channel Readiness
├── Tier Routing
├── Destinations
├── Publication Controls
├── Dedup / Dispatch Diagnostics
├── Route Restrictions
└── Distribution Notes
```

### 6.6 Research & Analytics

```text
/admin/research
├── Latest Summary
├── Daily / Periodic Reports
├── Performance Trends
├── Reject Analytics
├── Outcome Analytics
├── Symbol / Session Analytics
├── Export Views
└── Research Notes
```

### 6.7 Intelligence

```text
/admin/intelligence
├── Decision Intelligence
├── Debug Dashboard
├── Drift Signals
├── Anomaly Summaries
├── Recommendation Queue
├── Learning Views
└── Intelligence Notes
```

### 6.8 Affiliate / Partner

```text
/admin/affiliate
├── My Scope
├── My Referrals
├── Active Referred Users
├── Conversion Summary
├── Commission Summary
├── Campaign Status
├── Support / Escalation
└── Affiliate Docs
```

### 6.9 Roles & Identity

```text
/admin/roles
├── My Identity
├── My Role
├── Scope Summary
├── Visible Matrix
├── Managed Members
├── Role References
└── Reload / Refresh Identity View
```

### 6.10 System Health

```text
/admin/system
├── Health Summary
├── Observability Summary
├── Last Errors
├── Alerts
├── Incident References
├── Diagnostics
├── Restart Guard
└── Recovery References
```

### 6.11 Governance & Docs

```text
/admin/docs
├── Active Canonical Specs
├── Telegram UX
├── Architecture Mapping
├── Master Index
├── Implementation Matrix
├── Change-Control References
├── Deprecation Notes
└── Migration Notes
```

### 6.12 Security & Audit

```text
/admin/audit
├── Admin Action Log
├── Access Denials
├── Role Change Audit
├── Approval Records
├── Sensitive Incident References
├── Audit Exports
└── Security Notes
```

---

## 7. ROLE-SCOPED TREE VISIBILITY

The full tree is canonical, but rendered visibility depends on role.

### 7.1 Owner
May see all root branches and all governed sub-branches.

### 7.2 Primary Admin
May see nearly all operational and analytical branches, except Owner-reserved governance-sensitive controls where policy restricts them.

### 7.3 Functional Admin
Sees only the domain branches assigned to their function, plus allowed summary/home views.

Examples:
- Operations Admin → Home, Operations, System Health, selected Audit references
- Distribution Admin → Home, Distribution Control, selected Research/Intelligence views related to routing
- Research Admin → Home, Research & Analytics, Intelligence, selected Decision Visibility surfaces

### 7.4 Affiliate Admin
Sees only the affiliate subtree plus limited home/support/documentation views as policy allows.

### 7.5 Analyst / Read-only specialist
Sees read-only subsets of Decision Visibility, Research & Analytics, Intelligence and selected System Health surfaces.

### 7.6 Support / Moderator-style limited role
Sees only the limited support/community branches and any minimal status/doc surfaces required by policy.

---

## 8. TREE MAPPING RULES

The admin tree must obey these structural rules:

### 8.1 No legacy flat menu fallback
The canonical tree must not degrade into a flat command dump.

### 8.2 No mixed semantic levels
A top-level node should represent a domain, not a random single metric.

### 8.3 No hidden mutating control behind diagnostic labels
A diagnostic submenu must not secretly contain unrelated control actions without clear labeling.

### 8.4 No affiliate leakage
Affiliate-facing branches must remain isolated from global admin domains.

### 8.5 No historical truth mutation branches
There must be no menu branch whose implied purpose is rewriting historical decision or outcome truth.

### 8.6 No undocumented branches
Every visible stable branch must correspond to a canonical concept or approved implementation mapping.

---

## 9. TELEGRAM UX MAPPING NOTE

Telegram may render this tree as:

- command groups
- inline keyboard menus
- paged submenus
- role-scoped quick actions
- contextual drill-down screens

However, Telegram presentation may compress or rename branches for usability only if:

- canonical meaning remains intact
- role scoping remains intact
- auditability remains intact
- control versus visibility distinction remains intact

Canonical architecture is defined here; presentation details belong to `TELEGRAM_UX_v2.0.0.md`.

---

## 10. RELATION TO OTHER SPECS

This document maps where things live.

It does not fully define:

- permissions
- action authorization
- audit schemas
- business rules for each branch
- operational procedures
- strategy decision semantics

Those belong to the linked specifications.

This document must therefore be used together with:

- `ADMIN_CONTROL_SPEC_v2.0.0.md`
- `ROLE_AND_PERMISSION_MATRIX_SPEC_v2.0.0.md`
- `CONTROL_PANEL_HIERARCHY_AND_INTELLIGENCE_SPEC_v2.0.0.md`
- `ADMIN_OPERATIONS_SPEC_v2.0.0.md`
- `OBSERVABILITY_LOGGING_SPEC_v2.0.0.md`

---

## 11. MIGRATION NOTES FROM LEGACY VERSION

The legacy tree was useful as a compact operator sketch, but it had several limitations:

- too flat at root level
- mixed operational, analytical and governance concepts together
- insufficient distinction between visibility and control
- affiliate tree too small and under-modeled
- no explicit Security & Audit root
- no explicit Decision Visibility domain
- insufficient mapping to the newer canonical architecture

This v2.0.0 tree replaces the legacy layout with a more governed domain structure aligned to the modern BinaryBot admin architecture.

---

## 12. MINIMUM IMPLEMENTATION GUARANTEE

If implemented correctly, this admin tree map provides:

- a stable navigation blueprint
- clean domain grouping
- compatibility with role-scoped rendering
- safer separation of visibility and control
- proper alignment with admin, audit and intelligence architecture

---

End of ADMIN_TREE_MAP_v2.0.0.md
