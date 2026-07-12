# CANONICAL_DECISION_LOG.md

**Audit ID:** canonical-audit-01  
**Date:** 2026-07-12  
**Status:** Proposed decisions only — none executed  

> **SAFETY NOTE:** This document records proposed authority decisions. No document has been promoted, demoted, consolidated, deprecated, or overwritten as a result of this audit. Every decision below requires explicit owner approval before any action is taken.

---

## DEC-001

| Field | Value |
|---|---|
| **Decision ID** | DEC-001 |
| **Domain** | Community Feedback and Privacy |
| **Proposed Authoritative Document** | `send/docs/intake/COMMUNITY_FEEDBACK_AND_PRIVACY_SPEC.md` (pending promotion or major-merge) |
| **Documents It Would Supersede or Replace** | `send/docs/_deprecated/ELITE_FEEDBACK_SPEC.md`, `send/docs/_deprecated/ELITE_MEMBER_FEEDBACK_AND_LEADERBOARD_SPEC.md`, `send/docs/_deprecated/MEMBER_FEEDBACK_SPEC.md`, `send/docs/_deprecated/PRIVACY_AND_MEMBER_STATS_ACCESS_SPEC.md` |
| **Rationale** | CANON_BATCH_EVALUATION_v2.0.0.md evaluated this document as the strongest promote candidate in the intake batch. It defines a distinct canonical concern: privacy of member-level statistics, community feedback handling, visibility limits, pseudonymous references, and community-facing analytics — none of which is currently covered by any active canonical document. |
| **Consequences** | If promoted: establishes a new active canonical document for the community/privacy domain. If major-merged: relevant rules are absorbed into OUTCOME_TRACKING_SPEC_v2.0.0, TELEGRAM_UX_v2.0.0, and governance docs. The deprecated feedback/privacy docs in `_deprecated/` would be formally confirmed as superseded. |
| **Confidence Level** | HIGH (per CANON_BATCH_EVALUATION evidence) |
| **Owner Approval Required** | **Yes** — see OWNER-001 |

---

## DEC-002

| Field | Value |
|---|---|
| **Decision ID** | DEC-002 |
| **Domain** | Observability — Boundary Between OBSERVABILITY_SPEC and OBSERVABILITY_LOGGING_SPEC |
| **Proposed Authoritative Document** | `send/docs/canonical/active/OBSERVABILITY_SPEC_v2.0.0.md` as system-level root; `send/docs/canonical/active/OBSERVABILITY_LOGGING_SPEC_v2.0.0.md` as implementation-level detail |
| **Documents It Would Supersede or Replace** | None superseded — hierarchy clarification only |
| **Rationale** | OBSERVABILITY_SPEC cross-references OBSERVABILITY_LOGGING_SPEC, suggesting a layered relationship. The most logical interpretation is OBSERVABILITY_SPEC = system policy and observability architecture; OBSERVABILITY_LOGGING_SPEC = concrete telemetry, event logging, and auditability implementation contract. This is not currently declared in either document. |
| **Consequences** | Adds explicit deference clauses to both documents. Eliminates CON-001. No functional change to code. |
| **Confidence Level** | MEDIUM — interpretation is plausible but requires owner confirmation |
| **Owner Approval Required** | **Yes** — see OWNER-002 |

---

## DEC-003

| Field | Value |
|---|---|
| **Decision ID** | DEC-003 |
| **Domain** | Signal Distribution — Boundary Between SIGNAL_DISTRIBUTION_ARCHITECTURE and SIGNAL_DISTRIBUTION_SPEC |
| **Proposed Authoritative Document** | `send/docs/canonical/active/SIGNAL_DISTRIBUTION_SPEC_v2.0.0.md` for entitlement/delivery rules; `send/docs/canonical/active/SIGNAL_DISTRIBUTION_ARCHITECTURE_v2.0.0.md` for topology/routing architecture |
| **Documents It Would Supersede or Replace** | None superseded — hierarchy clarification only |
| **Rationale** | The most logical separation of concerns: ARCHITECTURE = how signals flow through the system (topology, routing, channels); SPEC = what rules govern delivery (entitlement, tiers, quotas, recovery). This separation is consistent with the layering approach used in other spec pairs (OBSERVABILITY_SPEC / OBSERVABILITY_LOGGING_SPEC). |
| **Consequences** | Adds explicit scope declarations and deference clauses to both documents. Eliminates CON-002. |
| **Confidence Level** | MEDIUM — interpretation is reasonable but requires owner confirmation |
| **Owner Approval Required** | **Yes** — see OWNER-003 |

---

## DEC-004

| Field | Value |
|---|---|
| **Decision ID** | DEC-004 |
| **Domain** | Master Index — Single Entry Point |
| **Proposed Authoritative Document** | `send/docs/canonical/active/CANONICAL_STRATEGY_STACK_v1.0.0.md` as the root strategy manifest; one of `MASTER_DOCUMENT_INDEX.md` or `BINARYBOT_MASTER_INDEX.md` as the master documentation index (owner to select) |
| **Documents It Would Supersede or Replace** | Whichever index is not selected would be deprecated in favor of the selected one |
| **Rationale** | Having two documents both claiming to be the "master index" creates navigational ambiguity. CANONICAL_STRATEGY_STACK covers only the strategy stack; the index should cover all documentation. One index should be designated primary. |
| **Consequences** | Eliminates CON-010. Clears the entry point for documentation navigation. |
| **Confidence Level** | HIGH |
| **Owner Approval Required** | **Yes** — see OWNER-005 |

---

## DEC-005

| Field | Value |
|---|---|
| **Decision ID** | DEC-005 |
| **Domain** | Governance Record Placement |
| **Proposed Authoritative Document** | N/A — organizational change only |
| **Documents It Would Supersede or Replace** | N/A |
| **Rationale** | `CANON_BATCH_EVALUATION_v2.0.0.md` is a governance record, not a canonical specification. It is currently in `send/docs/canonical/active/`, which implies it is an active specification. Moving it to a governance/records subfolder (e.g., `send/docs/canonical/governance_records/`) would correct the misclassification without affecting any canonical authority. |
| **Consequences** | Removes CANON_BATCH_EVALUATION from the active spec count. Establishes a governance_records subfolder for future audit and evaluation records. Eliminates CON-011. |
| **Confidence Level** | HIGH |
| **Owner Approval Required** | **No** — organizational only, does not change any authority decision |

---

## DEC-006

| Field | Value |
|---|---|
| **Decision ID** | DEC-006 |
| **Domain** | Intake Documents — Merge Execution |
| **Proposed Authoritative Document** | Target active docs per CANON_BATCH_EVALUATION verdicts |
| **Documents It Would Supersede or Replace** | Intake documents (in send/docs/intake/) would be formally classified as satellite/reference after their content is merged |
| **Rationale** | CANON_BATCH_EVALUATION_v2.0.0.md identified four documents that should be merged into active canonical documents: AI_STRATEGY_AUDITOR_SPEC, INTELLIGENCE_DATA_PIPELINE_DEFINITION, INTELLIGENCE_FILES_AND_MODULE_MAP, ADAPTIVE_ACTIVITY_GATE_SPEC. Executing these merges would extend the active canonical set with previously unrepresented rules. |
| **Consequences** | Active canonical documents (ALGO_SPEC, STRATEGY_INTELLIGENCE_SYSTEM, MODULE_INTERFACE_SPEC, RESEARCH_AND_LEARNING_FRAMEWORK_SPEC, PERFORMANCE_ANALYTICS_SPEC) would gain new sections. Intake docs would be classified as satellite reference. Enables GAP-011 resolution. |
| **Confidence Level** | HIGH (per CANON_BATCH_EVALUATION analysis) |
| **Owner Approval Required** | **Yes** — owner must approve any modification to active canonical documents |

---

## DEC-007

| Field | Value |
|---|---|
| **Decision ID** | DEC-007 |
| **Domain** | Security Specification |
| **Proposed Authoritative Document** | `send/docs/SECURITY_MODEL.md` — candidate for promotion to active canonical set |
| **Documents It Would Supersede or Replace** | None currently in active set |
| **Rationale** | Security is a required canonical domain with no active canonical specification (GAP-007). SECURITY_MODEL.md exists in root docs and addresses this domain. It either should be promoted to active canonical status or its rules should be merged into SYSTEM_INVARIANTS_v2.0.0 and GOVERNANCE_AND_CHANGE_CONTROL_v2.0.0. |
| **Consequences** | If promoted: establishes SECURITY_MODEL as an active canonical document. If merged: security rules absorbed into existing active docs. Either path eliminates GAP-007. |
| **Confidence Level** | MEDIUM (document content not fully inspected) |
| **Owner Approval Required** | **Yes** |

---

## DEC-008

| Field | Value |
|---|---|
| **Decision ID** | DEC-008 |
| **Domain** | Risk Specification |
| **Proposed Authoritative Document** | `send/docs/RISK_MODEL.md` — candidate for promotion to active canonical set |
| **Documents It Would Supersede or Replace** | None currently in active set |
| **Rationale** | Risk management is a required canonical domain with no active canonical specification (GAP-008). RISK_MODEL.md exists in root docs. Multiple deprecated documents referenced it as an authority. |
| **Consequences** | If promoted: establishes RISK_MODEL as an active canonical document. If merged: risk rules absorbed into SYSTEM_INVARIANTS or ALGO_SPEC. Either path eliminates GAP-008. |
| **Confidence Level** | MEDIUM (document content not fully inspected) |
| **Owner Approval Required** | **Yes** |

---

## DEC-009

| Field | Value |
|---|---|
| **Decision ID** | DEC-009 |
| **Domain** | State Persistence Specification |
| **Proposed Authoritative Document** | `send/docs/STATE_PERSISTENCE_SPEC.md` — candidate for promotion to active canonical set |
| **Documents It Would Supersede or Replace** | None currently in active set |
| **Rationale** | State persistence is governed by `send/core/storage.py`, which is one of the most critical infrastructure modules. No active canonical document governs the persistence contract (GAP-015). STATE_PERSISTENCE_SPEC.md exists in root docs. |
| **Consequences** | If promoted: establishes canonical governance for the persistence layer. Enables full MODULE_INTERFACE_SPEC alignment for storage.py. |
| **Confidence Level** | MEDIUM (document content not fully inspected) |
| **Owner Approval Required** | **Yes** |

---

## DEC-010

| Field | Value |
|---|---|
| **Decision ID** | DEC-010 |
| **Domain** | Proposed Admin Control Plane Canon |
| **Proposed Authoritative Document** | `send/docs/canonical/proposed/ADMIN_SURFACE_AND_CONTROL_PLANE_CANON_v1.0.0.md` — pending promotion or rejection |
| **Documents It Would Supersede or Replace** | If promoted as a root manifest: ADMIN_CONTROL_SPEC_v2.0.0.md and related admin docs would become sub-specifications under this root. |
| **Rationale** | The proposed document aims to unify the admin/control-plane canonical cluster under a single root, similar to how CANONICAL_STRATEGY_STACK unifies the strategy cluster. It depends on all active admin specs and proposes to add a governing layer above them. |
| **Consequences** | If promoted: establishes a unified admin canonical root. If rejected: admin domain remains governed by the current cluster of ADMIN_CONTROL_SPEC, ADMIN_OPERATIONS_SPEC, ADMIN_TREE_MAP, CONTROL_PANEL_HIERARCHY_AND_INTELLIGENCE_SPEC. |
| **Confidence Level** | MEDIUM |
| **Owner Approval Required** | **Yes** |

---

*End of CANONICAL_DECISION_LOG.md*
