# CANONICAL_ANALYSIS.md

BinaryBot — Telegram Application Reconstruction  
Audit: telegram-application-reconstruction-01  
Status: RECONSTRUCTION ANALYSIS

---

## 1. CANONICAL DOCUMENTS ANALYZED

The following canonical active documents were read in full before any code modification:

| Document | Version | Relevance |
|---|---|---|
| TELEGRAM_UX_v2.0.0.md | 2.0.0 | Primary UX specification; defines all Telegram interaction domains |
| ROLE_AND_PERMISSION_MATRIX_SPEC_v2.0.0.md | 2.0.0 | Defines canonical role hierarchy and permission domains |
| CONTROL_PANEL_HIERARCHY_AND_INTELLIGENCE_SPEC_v2.0.0.md | 2.0.0 | Defines control panel structure, intelligence/insight axis |
| ADMIN_TREE_MAP_v2.0.0.md | 2.0.0 | Structural navigation map of the admin control surface |
| ADMIN_CONTROL_SPEC_v2.0.0.md | 2.0.0 | Admin surface sections, operator visibility/control model |
| ADMIN_OPERATIONS_SPEC_v2.0.0.md | 2.0.0 | Governed operational control procedures |
| AFFILIATE_SIGNAL_DISTRIBUTION_MODEL_v2.0.0.md | 2.0.0 | Affiliate participation and isolation model |
| ADMIN_SURFACE_AND_CONTROL_PLANE_CANON_v2.0.0.md | 2.0.0 | Root manifest for admin/control-plane cluster |

---

## 2. CANONICAL TELEGRAM UX DOMAINS (FROM TELEGRAM_UX_v2.0.0.md §3)

The canonical UX is divided into six distinct domains:

| Domain | Canonical Purpose |
|---|---|
| Live Signal UX | Signal delivery (PRE → CONFIRM → OPEN_NOW) to trading destinations |
| Outcome UX | Post-signal outcome capture (WIN/LOSE/MISSED) for eligible destinations |
| System Alert UX | Operational alerts, failures, critical state messages |
| Admin UX | Private role-scoped operator control and visibility flows |
| Research/Summary UX | Report and insight delivery to authorized roles |
| Documentation UX | Governed in-bot access to canonical specs and references |

---

## 3. CANONICAL ADMIN ENTRY POINT (FROM ADMIN_TREE_MAP_v2.0.0.md §3)

The canonical root entry is `/admin`.

The root must render a **role-appropriate navigation tree** and summary context, not a flat unrestricted menu. This is the primary gap between the pre-reconstruction implementation and the canonical specification.

---

## 4. CANONICAL ADMIN TREE (FROM ADMIN_TREE_MAP_v2.0.0.md §4)

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

Each root node has canonically defined purpose and sub-structure (see ADMIN_TREE_MAP_v2.0.0.md §6).

---

## 5. CANONICAL ROLE FAMILY (FROM ROLE_AND_PERMISSION_MATRIX_SPEC_v2.0.0.md §3)

| Role | Canonical Label | Hierarchy Position |
|---|---|---|
| OWNER | Owner | Supreme governance authority |
| PRIMARY_ADMIN | Primary Admin | Highest day-to-day operator |
| STRATEGY_ADMIN | Functional Admin (Operations) | Domain-specific: strategy/operations |
| RESEARCH_ADMIN | Functional Admin (Research) | Domain-specific: research/analytics |
| ANALYST | Analyst / Read-only Specialist | Read-only research and diagnostics |
| MODERATOR | Support / Moderator | Limited community/support |
| AFFILIATE_ADMIN | Affiliate Admin | Scoped affiliate program |
| USER | User | Non-admin consumer |

---

## 6. CANONICAL ROLE-PANEL VISIBILITY (FROM ADMIN_TREE_MAP_v2.0.0.md §7)

| Role | Visible Admin Panels |
|---|---|
| OWNER | All 11 canonical panels |
| PRIMARY_ADMIN | All 11 canonical panels |
| STRATEGY_ADMIN (Functional Admin - Operations) | Operations, Symbols & Coverage, Decision Visibility |
| RESEARCH_ADMIN (Functional Admin - Research) | Decision Visibility (read), Research & Analytics, Intelligence |
| ANALYST | Decision Visibility (read), Research & Analytics (read), Intelligence (read) |
| MODERATOR | System Health (limited) |
| AFFILIATE_ADMIN | Affiliate / Partner |
| USER | None |

Source: ADMIN_TREE_MAP_v2.0.0.md §7.1–§7.6; CONTROL_PANEL_HIERARCHY_AND_INTELLIGENCE_SPEC_v2.0.0.md §4–§10.

---

## 7. PRE-RECONSTRUCTION GAPS IDENTIFIED

### GAP-R01: Flat non-canonical admin home
**Canonical requirement**: Role-scoped hierarchical navigation tree (12 nodes)
**Pre-reconstruction state**: Flat menu of 14 functional buttons (Status, Strategy, Thresholds, S/R, Spike Filter, Symbols, Engine, Debug, Reports, Files, Documents, Diagnose, Runtime Audit, Roles, Affiliate)
**Impact**: No canonical tree structure; no role-scoped visibility; canonical domains not separated

### GAP-R02: Missing canonical panel nodes
**Canonical requirement**: Dedicated panels for Decision Visibility, Distribution Control, Research & Analytics (as top-level), Intelligence, System Health, Governance & Docs, Security & Audit
**Pre-reconstruction state**: Decision Visibility backed only by `/debug`; Distribution Control absent; Research & Analytics as `/report`; Intelligence absent; System Health merged with Engine/Diagnose; Governance & Docs as file browser; Security & Audit as `/audit_runtime`
**Impact**: Canonical domain separation absent from UX

### GAP-R03: No role-scoped rendering of admin home
**Canonical requirement**: A role must see only the panels their permissions allow (TELEGRAM_UX_v2.0.0.md §15.2, ADMIN_TREE_MAP_v2.0.0.md §7)
**Pre-reconstruction state**: Same flat menu rendered for all roles
**Impact**: Lower-privileged roles see controls they should not see; canonical invisible-by-default rule violated

### GAP-R04: Commands as primary interaction model
**Canonical requirement**: Buttons are the primary interaction model; commands remain optional shortcuts (TELEGRAM_UX_v2.0.0.md §16)
**Pre-reconstruction state**: Commands are primary; button navigation secondary and incomplete
**Impact**: Application does not behave as a coherent app; commands drive UX instead of inline navigation

---

## 8. EXPLICITLY DEFINED VS. IMPLEMENTATION DECISIONS

### Explicitly defined by canonical documents:
- All 12 root tree nodes and their canonical purposes (ADMIN_TREE_MAP_v2.0.0.md §5)
- Role hierarchy (ROLE_AND_PERMISSION_MATRIX_SPEC_v2.0.0.md §3–§4)
- Role-panel visibility rules (ADMIN_TREE_MAP_v2.0.0.md §7)
- Six UX domains (TELEGRAM_UX_v2.0.0.md §3)
- Admin entry via `/admin` (ADMIN_TREE_MAP_v2.0.0.md §3)
- Role-scoped rendering requirement (TELEGRAM_UX_v2.0.0.md §15.2)
- Button-primary interaction model (TELEGRAM_UX_v2.0.0.md §18)
- Invisible-by-default for unauthorized capability (ROLE_AND_PERMISSION_MATRIX_SPEC_v2.0.0.md §2.7)
- Signal lifecycle: PRE → CONFIRM → OPEN_NOW → OUTCOME_PANEL (TELEGRAM_UX_v2.0.0.md §5.3)
- Outcome options: WIN, LOSE, MISSED (TELEGRAM_UX_v2.0.0.md §14.5)
- Admin UX isolation from public channels (TELEGRAM_UX_v2.0.0.md §21.1)

### Not explicitly defined by canonical documents (implementation decisions required):
See IMPLEMENTATION_PLAN.md §5 for explicit documentation of each implementation decision.
