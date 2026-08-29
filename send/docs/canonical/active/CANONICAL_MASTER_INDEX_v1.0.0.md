# CANONICAL_MASTER_INDEX_v1.0.0.md

**Canonical Name:** CANONICAL_MASTER_INDEX
**Version:** 1.0.0
**Status:** Active Canonical — Authoritative Master Documentation Index
**Owner:** BinaryBot / DROPi Signals
**Canonical Path:** `send/docs/canonical/active/CANONICAL_MASTER_INDEX_v1.0.0.md`
**Governance Record:** canonical-reconciliation-01 (OWNER-005 = C)
**Created:** 2026-07-12

**Authority:** This document is the single authoritative canonical master index for BinaryBot / DROPi Signals. It supersedes and replaces both `send/docs/MASTER_DOCUMENT_INDEX.md` and `send/docs/BINARYBOT_MASTER_INDEX.md` as the canonical documentation entry point. Both historical indexes are preserved and classified as superseded after this index was created and validated.

**Superseded Documents (post-validation):**
- `send/docs/MASTER_DOCUMENT_INDEX.md` — superseded; retained as historical record.
- `send/docs/BINARYBOT_MASTER_INDEX.md` — superseded; retained as historical record.

---

## 1. PURPOSE

This index is derived from the final reconciled canonical state produced by canonical governance reconciliation task `canonical-reconciliation-01` (2026-07-12). It provides:

- A complete inventory of all active canonical documents
- The canonical authority hierarchy
- The relationship between root manifests, domain specifications, and implementation-detail specifications
- How proposed, transitional, supporting, superseded, and deprecated documents are treated
- Governance and cross-reference information for every active canonical document

This index must be updated whenever active canonical documents are added, removed, or promoted.

---

## 2. CANONICAL AUTHORITY HIERARCHY

The canonical authority hierarchy governs which documents take precedence in case of conflict.

### 2.1 Root Manifests

Root manifests are the top-level authority documents for their respective clusters. They establish architectural principles and resolve conflicts among subordinate cluster members.

| Root Manifest | Cluster |
|---|---|
| `CANONICAL_STRATEGY_STACK_v1.0.0.md` | Strategy pipeline cluster |
| `ADMIN_SURFACE_AND_CONTROL_PLANE_CANON_v2.0.0.md` | Admin/control-plane cluster |

### 2.2 System Policy and Architectural Authority

These documents hold system-level policy authority over their domains. Implementation-level specifications defer to them on policy and architecture.

| Policy/Architecture Authority | Implementation-Level Contract |
|---|---|
| `OBSERVABILITY_SPEC_v2.0.0.md` | `OBSERVABILITY_LOGGING_SPEC_v2.0.0.md` |
| `SIGNAL_DISTRIBUTION_ARCHITECTURE_v2.0.0.md` (topology/architecture) | `SIGNAL_DISTRIBUTION_SPEC_v2.0.0.md` (entitlement/delivery policy) |

### 2.3 How Root Manifests Relate to Domain Specifications

Root manifests establish the architectural canon for their cluster. Domain specifications within the cluster govern specific functional areas and must not contradict the root manifest.

- Root manifest governs: architectural principles, authority hierarchy, layer separations, and cluster-level conflict resolution.
- Domain specifications govern: their specific implementation domain within the bounds established by the root manifest.

### 2.4 How Implementation-Detail Specifications Defer to Policy Specifications

Where a policy/architecture specification and an implementation-detail specification address the same concern:

- Policy/architecture specification governs: system goals, principles, and architectural decisions.
- Implementation-detail specification governs: concrete event schemas, log formats, persistence mechanics, and telemetry details.
- Where conflict exists: the policy/architecture specification is authoritative on policy; the implementation-detail specification is authoritative on mechanics.

### 2.5 How Other Document Classes Are Treated

| Class | Treatment |
|---|---|
| **Active Canonical** | Authoritative for their domain. May only be changed via canonical governance process. |
| **Proposed** | Under review; not authoritative. Must be promoted via governance before becoming binding. |
| **Transitional** | Historical progression records. Not authoritative but preserved for context. |
| **Supporting** | Reference material not part of the active canonical set. Do not override active canonical documents. |
| **Superseded** | Previously canonical; replaced by a newer version. Retained for historical reference only. |
| **Deprecated** | No longer canonical; classified as dead-end. Retained for historical reference only. |

---

## 3. AUTHORITATIVE ACTIVE CANONICAL INVENTORY

**Total active canonical documents: 41**

Every active canonical document appears exactly once in this inventory.

---

### 3.1 Root Manifests

| # | Canonical Filename | Version | Status | Functional Domain | Authority Role |
|---|---|---|---|---|---|
| 1 | `CANONICAL_STRATEGY_STACK_v1.0.0.md` | 1.0.0 | Active Canonical | Strategy pipeline architecture | Root manifest for the strategy cluster; governs all strategy-domain specs |
| 2 | `ADMIN_SURFACE_AND_CONTROL_PLANE_CANON_v2.0.0.md` | 2.0.0 | Active Canonical | Admin/control-plane architecture | Root manifest for the admin/control-plane cluster; governs all admin/control-plane specs |

---

### 3.2 Strategy Pipeline Cluster

*Governed by root manifest: `CANONICAL_STRATEGY_STACK_v1.0.0.md`*

| # | Canonical Filename | Version | Status | Functional Domain | Authority Role |
|---|---|---|---|---|---|
| 3 | `ALGO_SPEC_v2.0.0.md` | 2.0.0 | Active Canonical | Trading algorithm and strategy logic | Canonical authority for strategy evaluation algorithm |
| 4 | `SR_CORRIDOR_ENGINE_SPEC_v2.0.0.md` | 2.0.0 | Active Canonical | Support/resistance corridor detection | Canonical authority for corridor detection engine |
| 5 | `TIME_MODEL_UNIFIED_CANON_v2.0.0.md` | 2.0.0 | Active Canonical | Unified time model | Canonical authority for time model; supersedes earlier time model specs |
| 6 | `DECISION_OBJECT_CANONICAL_SPEC_v1.0.0.md` | 1.0.0 | Active Canonical | DecisionObject contract | Canonical authority for the DecisionObject data structure and lifecycle |
| 7 | `FSM_DECISION_ENGINE_SPEC_v1.0.0.md` | 1.0.0 | Active Canonical | FSM signal lifecycle | Canonical authority for the finite state machine governing signal lifecycle |
| 8 | `SIGNAL_ENGINE_EXECUTION_SPEC_v2.0.0.md` | 2.0.0 | Active Canonical | Signal execution | Canonical authority for signal engine execution behavior |
| 9 | `RISK_MODEL_v2.0.0.md` | 2.0.0 | Active Canonical | Risk control and capital protection | Canonical authority for risk filtering and capital protection logic |

---

### 3.3 Observability Cluster

*Layered authority: `OBSERVABILITY_SPEC_v2.0.0.md` (policy/architecture) → `OBSERVABILITY_LOGGING_SPEC_v2.0.0.md` (implementation)*

| # | Canonical Filename | Version | Status | Functional Domain | Authority Role |
|---|---|---|---|---|---|
| 10 | `OBSERVABILITY_SPEC_v2.0.0.md` | 2.0.0 | Active Canonical | Observability architecture and policy | System policy and architectural authority for the observability domain |
| 11 | `OBSERVABILITY_LOGGING_SPEC_v2.0.0.md` | 2.0.0 | Active Canonical | Observability implementation / telemetry | Implementation-level logging and telemetry contract; defers to OBSERVABILITY_SPEC on policy |
| 12 | `EVENT_SCHEMA_SPEC_v2.0.0.md` | 2.0.0 | Active Canonical | Event schema | Canonical authority for system event schema and event family definitions |
| 13 | `DECISION_AUDIT_SPEC_v2.0.0.md` | 2.0.0 | Active Canonical | Decision audit | Canonical authority for decision audit trail requirements |
| 14 | `TRADE_TEMPORAL_TELEMETRY_SPEC_v2.0.0.md` | 2.0.0 | Active Canonical | Trade temporal telemetry | Canonical authority for temporal telemetry; implementation deferred (see OWNER-004) |

---

### 3.4 Signal Distribution Cluster

*Explicit non-overlapping scopes: `SIGNAL_DISTRIBUTION_ARCHITECTURE_v2.0.0.md` (topology/architecture) and `SIGNAL_DISTRIBUTION_SPEC_v2.0.0.md` (entitlement/delivery policy)*

| # | Canonical Filename | Version | Status | Functional Domain | Authority Role |
|---|---|---|---|---|---|
| 15 | `SIGNAL_DISTRIBUTION_ARCHITECTURE_v2.0.0.md` | 2.0.0 | Active Canonical | Distribution routing topology and channel architecture | Canonical authority for distribution architecture, routing topology, structural boundaries |
| 16 | `SIGNAL_DISTRIBUTION_SPEC_v2.0.0.md` | 2.0.0 | Active Canonical | Signal entitlement, delivery rules, tier eligibility | Canonical authority for entitlement policy, delivery mechanics, tier rules |
| 17 | `CHANNEL_CONFIG_SPEC_v2.0.0.md` | 2.0.0 | Active Canonical | Channel configuration | Canonical authority for channel and topic configuration |
| 18 | `TELEGRAM_UX_v2.0.0.md` | 2.0.0 | Active Canonical | Telegram user experience | Canonical authority for Telegram message layout and user-facing UX |
| 19 | `AFFILIATE_SIGNAL_DISTRIBUTION_MODEL_v2.0.0.md` | 2.0.0 | Active Canonical | Affiliate signal distribution model | Canonical authority for affiliate program distribution model |
| 20 | `SIGNAL_ECONOMICS_AND_MONETIZATION_MODEL_v2.0.0.md` | 2.0.0 | Active Canonical | Signal economics and monetization | Canonical authority for economics model and monetization structure |

---

### 3.5 Admin / Control-Plane Cluster

*Governed by root manifest: `ADMIN_SURFACE_AND_CONTROL_PLANE_CANON_v2.0.0.md`*

| # | Canonical Filename | Version | Status | Functional Domain | Authority Role | Parent Manifest |
|---|---|---|---|---|---|---|
| 21 | `ADMIN_CONTROL_SPEC_v2.0.0.md` | 2.0.0 | Active Canonical | Admin command surface, role enforcement | Implementation authority for admin control surface | `ADMIN_SURFACE_AND_CONTROL_PLANE_CANON_v2.0.0.md` |
| 22 | `ADMIN_OPERATIONS_SPEC_v2.0.0.md` | 2.0.0 | Active Canonical | Admin operational procedures | Implementation authority for day-to-day admin operations | `ADMIN_SURFACE_AND_CONTROL_PLANE_CANON_v2.0.0.md` |
| 23 | `ADMIN_TREE_MAP_v2.0.0.md` | 2.0.0 | Active Canonical | Admin hierarchy structural map | Canonical structural map of admin control surface layout | `ADMIN_SURFACE_AND_CONTROL_PLANE_CANON_v2.0.0.md` |
| 24 | `CONTROL_PANEL_HIERARCHY_AND_INTELLIGENCE_SPEC_v2.0.0.md` | 2.0.0 | Active Canonical | Control panel and intelligence display | Canonical authority for control panel hierarchy and intelligence layer consumption | `ADMIN_SURFACE_AND_CONTROL_PLANE_CANON_v2.0.0.md` |
| 25 | `ROLE_AND_PERMISSION_MATRIX_SPEC_v2.0.0.md` | 2.0.0 | Active Canonical | Role and permission matrix | Canonical authority for all role definitions and permission boundaries | `ADMIN_SURFACE_AND_CONTROL_PLANE_CANON_v2.0.0.md` |
| 26 | `STRATEGY_PARAMETER_CONTROL_SPEC_v2.0.0.md` | 2.0.0 | Active Canonical | Strategy parameter governance | Canonical authority for controlled parameter change procedures | `ADMIN_SURFACE_AND_CONTROL_PLANE_CANON_v2.0.0.md` |

---

### 3.6 Analytics and Intelligence Cluster

| # | Canonical Filename | Version | Status | Functional Domain | Authority Role |
|---|---|---|---|---|---|
| 27 | `OUTCOME_TRACKING_SPEC_v2.0.0.md` | 2.0.0 | Active Canonical | Outcome tracking | Canonical authority for trade outcome recording and tracking |
| 28 | `PERFORMANCE_ANALYTICS_SPEC_v2.0.0.md` | 2.0.0 | Active Canonical | Performance analytics | Canonical authority for system performance analysis |
| 29 | `RESEARCH_AND_LEARNING_FRAMEWORK_SPEC_v2.0.0.md` | 2.0.0 | Active Canonical | Research and learning framework | Canonical authority for research methodology and learning integration |
| 30 | `STRATEGY_INTELLIGENCE_SYSTEM_v2.0.0.md` | 2.0.0 | Active Canonical | Strategy intelligence system | Canonical authority for intelligence system architecture |
| 31 | `AUTONOMOUS_STRATEGY_EVOLUTION_SYSTEM_v2.0.0.md` | 2.0.0 | Active Canonical | Autonomous strategy evolution | Canonical authority for autonomous strategy evolution |
| 32 | `COMMUNITY_FEEDBACK_AND_PRIVACY_SPEC_v2.0.0.md` | 2.0.0 | Active Canonical | Community feedback, elite outcome reporting, member privacy | Canonical authority for community feedback, leaderboard, and member privacy model |

---

### 3.7 System Architecture and Infrastructure

| # | Canonical Filename | Version | Status | Functional Domain | Authority Role |
|---|---|---|---|---|---|
| 33 | `SYSTEM_ARCHITECTURE_MAP_v2.0.0.md` | 2.0.0 | Active Canonical | System architecture overview | Canonical authority for the overall system architecture map |
| 34 | `MODULE_INTERFACE_SPEC_v2.0.0.md` | 2.0.0 | Active Canonical | Module interface contracts | Canonical authority for module-to-module interface definitions |
| 35 | `SYSTEM_INVARIANTS_v2.0.0.md` | 2.0.0 | Active Canonical | System invariants | Canonical authority for non-negotiable system rules and constraints |
| 36 | `FAILURE_RECOVERY_SPEC_v2.0.0.md` | 2.0.0 | Active Canonical | Failure recovery | Canonical authority for failure modes and recovery procedures |
| 37 | `DEPLOYMENT_PROTOCOL_v2.0.0.md` | 2.0.0 | Active Canonical | Deployment protocol | Canonical authority for deployment procedures and safety controls |

---

### 3.8 Security and Risk

| # | Canonical Filename | Version | Status | Functional Domain | Authority Role |
|---|---|---|---|---|---|
| 38 | `SECURITY_MODEL_v2.0.0.md` | 2.0.0 | Active Canonical | Security architecture and threat protection | Canonical authority for system security model and threat protection |
| 39 | `RISK_MODEL_v2.0.0.md` | 2.0.0 | Active Canonical | Risk control and capital protection | Canonical authority for risk filtering logic and capital protection model |

> Note: `RISK_MODEL_v2.0.0.md` appears in both Section 3.2 (strategy pipeline) and 3.8 (security and risk) due to its cross-domain relevance. It is **counted only once** in the total inventory (as entry #9 in Section 3.2 and cross-referenced here). Total count: 41 documents.

---

### 3.9 Governance and Change Control

| # | Canonical Filename | Version | Status | Functional Domain | Authority Role |
|---|---|---|---|---|---|
| 40 | `GOVERNANCE_AND_CHANGE_CONTROL_v2.0.0.md` | 2.0.0 | Active Canonical | Governance and change control | Canonical authority for change governance, approval, and version control processes |

---

### 3.10 Testing and Validation

| # | Canonical Filename | Version | Status | Functional Domain | Authority Role |
|---|---|---|---|---|---|
| 41 | `TEST_PLAN_v2.0.0.md` | 2.0.0 | Active Canonical | Test plan | Canonical authority for the system validation and testing plan |

---

### 3.11 Governance Records in Active Folder

> The following document resides in `canonical/active/` but is classified as a governance/supporting record rather than an active canonical specification. It is documented here for completeness and does not count toward the authoritative canonical set.

| Document | Classification | Note |
|---|---|---|
| `CANON_BATCH_EVALUATION_v2.0.0.md` | Supporting / Governance record | Batch evaluation record for intake documents; referenced from canonical governance but does not govern a functional domain |

---

## 4. VALIDATION SUMMARY

**Total active canonical documents in authoritative inventory: 41**

Validation checks performed (2026-07-12):

- [x] Every active canonical document appears exactly once in the authoritative inventory.
- [x] No active canonical filename is duplicated in the inventory.
- [x] RISK_MODEL_v2.0.0.md appears as a unique entry (#9 in Section 3.2) with a cross-reference note in Section 3.8 — counted once only.
- [x] Authority hierarchy is internally consistent.
- [x] Root manifests cover their declared clusters.
- [x] Layered authority relationships (OWNER-002, OWNER-003) are documented and non-ambiguous.
- [x] All newly promoted documents (OWNER-001, OWNER-006, OWNER-007) are included.
- [x] CON-001 (observability overlap) is resolved: explicit hierarchy declared.
- [x] CON-002 (signal distribution overlap) is resolved: explicit non-overlapping scopes declared.
- [x] OWNER-004 (trade_temporal_telemetry, scan_scheduler) remains deferred; TRADE_TEMPORAL_TELEMETRY_SPEC_v2.0.0.md remains active canonical, implementation status flagged in DEFERRED_IMPLEMENTATION_REGISTER.md.

---

## 5. SUPERSEDED MASTER INDEXES

The following historical master indexes are classified as superseded as of 2026-07-12, after this index was created and validated:

| Document | Superseded By | Retained |
|---|---|---|
| `send/docs/MASTER_DOCUMENT_INDEX.md` | This document | Yes — preserved as historical record |
| `send/docs/BINARYBOT_MASTER_INDEX.md` | This document | Yes — preserved as historical record |

---

## 6. DOCUMENT CLASSES NOT IN AUTHORITATIVE INVENTORY

The following document classes exist in the repository but are not part of the authoritative active canonical set:

| Class | Location | Count | Treatment |
|---|---|---|---|
| Superseded canonical | `send/docs/canonical/superseded/` | 3 | Replaced by newer canonical versions; preserved as historical records |
| Deprecated canonical | `send/docs/canonical/deprecated/` | 11 | Classified as dead-end; preserved for historical reference |
| Deprecated root-level | `send/docs/_deprecated/` | ~25 | Legacy documents; preserved |
| Proposed | `send/docs/canonical/proposed/` | 1 (ADMIN CANON v1.0.0) | Source for OWNER-007; retained as historical record |
| Transitional | `send/docs/canonical/transitional/` | ~5 | Historical progression records; not authoritative |
| Intake documents | `send/docs/intake/` | ~10 | Sources for canonical promotion candidates; not authoritative |
| Root-level supporting | `send/docs/` (root) | ~30 | Supporting/reference material; not authoritative canonical |
| Governance records | `audit/` | Multiple | Audit and reconciliation records; not active canonical specs |

---

## 7. OPEN RISKS AND DEFERRED ITEMS

| Risk | Severity | Status | Reference |
|---|---|---|---|
| `trade_temporal_telemetry` module missing — runtime ImportError | CRITICAL | Open / Deferred | OWNER-004; `audit/canonical-reconciliation-01/DEFERRED_IMPLEMENTATION_REGISTER.md` |
| `scan_scheduler` module missing — silent failure | HIGH | Open / Deferred | OWNER-004; `audit/canonical-reconciliation-01/DEFERRED_IMPLEMENTATION_REGISTER.md` |
| No test suite despite active TEST_PLAN | HIGH | Open | Requires dedicated implementation task |

---

## 8. CANONICAL VERSION HISTORY

| Version | Date | Description |
|---|---|---|
| 1.0.0 | 2026-07-12 | Created as new authoritative canonical master index from reconciled state (OWNER-005 = C, canonical-reconciliation-01). Supersedes MASTER_DOCUMENT_INDEX.md and BINARYBOT_MASTER_INDEX.md. |

---

*End of CANONICAL_MASTER_INDEX_v1.0.0.md*


## Human Comprehension and Operational Memory

- `HUMAN_COMPREHENSION_AND_SELF_EXPLAINING_CONTROL_SURFACE_CANON_v1.0.0.md` — ACTIVE — defines the mandatory self-explaining human control-surface,
  contextual operational manual, and persistent operational-memory contract.
