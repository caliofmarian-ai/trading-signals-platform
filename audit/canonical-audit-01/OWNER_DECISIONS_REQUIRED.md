# OWNER_DECISIONS_REQUIRED.md

**Audit ID:** canonical-audit-01  
**Date:** 2026-07-12  
**Total Decisions Requiring Owner Input:** 7  

> These decisions cannot be resolved safely from repository evidence alone. They require explicit owner direction before any action is taken.

---

## OWNER-001 — Community Feedback and Privacy Specification

**Decision:** Whether to promote COMMUNITY_FEEDBACK_AND_PRIVACY_SPEC.md to active canonical status, or perform a major-merge of its content into existing active documents.

**Clear Question:**  
Should `send/docs/intake/COMMUNITY_FEEDBACK_AND_PRIVACY_SPEC.md` be:  
(A) Promoted as a new active canonical document in `send/docs/canonical/active/`, or  
(B) Major-merged: its content distributed into OUTCOME_TRACKING_SPEC_v2.0.0, TELEGRAM_UX_v2.0.0, GOVERNANCE_AND_CHANGE_CONTROL_v2.0.0, and/or a new governance/privacy section?

**Available Options:**

| Option | Description |
|---|---|
| A — Promote | Create a new `COMMUNITY_FEEDBACK_AND_PRIVACY_SPEC_v2.0.0.md` in `send/docs/canonical/active/`. Formally supersedes deprecated feedback/privacy docs. Adds a new canonical root. |
| B — Major-Merge | Extract rules from the intake spec and merge into 3–4 existing active canonical documents. No new active document created. Intake doc classified as satellite reference. |

**Consequences:**

- **Option A**: Increases active canonical set by 1 document. Provides a dedicated canonical home for privacy/community concerns. Lower risk of scattered rules. Requires future maintenance of an additional active spec.
- **Option B**: Keeps active canonical set smaller. Risk of scattered rules across multiple docs if merge is not carefully executed. Does not increase active document count.

**Recommended Option:** Option A — Promote.  
**Reason:** The community feedback and privacy domain is sufficiently distinct (privacy limits, pseudonymous references, community-facing vs. admin-facing analytics boundaries) to warrant its own canonical specification. Merging into multiple existing docs increases the risk of scattered and inconsistent rules. CANON_BATCH_EVALUATION explicitly identified this as the strongest promote candidate.

**Why Owner Approval Is Required:** Promoting a new active canonical document is a governance decision. It changes the authoritative set and may create obligations on implementation. Only the owner can approve additions to the active canonical set.

**Related Decision Log Entry:** DEC-001  
**Related Gap:** GAP-010  

---

## OWNER-002 — Observability Domain Boundary

**Decision:** Whether to declare an explicit hierarchy between OBSERVABILITY_SPEC_v2.0.0.md and OBSERVABILITY_LOGGING_SPEC_v2.0.0.md, or consolidate them into a single document.

**Clear Question:**  
Should OBSERVABILITY_SPEC_v2.0.0.md and OBSERVABILITY_LOGGING_SPEC_v2.0.0.md:  
(A) Be assigned explicit layered roles: OBSERVABILITY_SPEC = system policy / architectural authority; OBSERVABILITY_LOGGING_SPEC = implementation-level detail contract, or  
(B) Be consolidated into a single authoritative observability document?

**Available Options:**

| Option | Description |
|---|---|
| A — Declare Hierarchy | Add explicit deference clauses: "OBSERVABILITY_LOGGING_SPEC defers to OBSERVABILITY_SPEC for policy." No content change required. |
| B — Consolidate | Merge both into one document. One of them is deprecated. |
| C — Status Quo | Leave both documents without explicit hierarchy. Continue current ambiguity. |

**Consequences:**

- **Option A**: Low effort. Eliminates CON-001 without content changes. Preserves both documents as active canonical.
- **Option B**: Reduces active document count by 1. Requires careful content merge to avoid losing detail. More effort.
- **Option C**: Ambiguity persists. Future contributors may make contradictory changes to the two specs.

**Recommended Option:** Option A — Declare Hierarchy.  
**Reason:** The cross-reference in OBSERVABILITY_SPEC to OBSERVABILITY_LOGGING_SPEC already implies a layered relationship. Formalizing it requires only adding deference clauses. Low risk, low effort.

**Why Owner Approval Is Required:** Declaring one canonical document to defer to another changes its authority status. This is a governance decision.

**Related Decision Log Entry:** DEC-002  
**Related Conflict:** CON-001  

---

## OWNER-003 — Signal Distribution Domain Boundary

**Decision:** Whether to declare an explicit scope boundary between SIGNAL_DISTRIBUTION_ARCHITECTURE_v2.0.0.md and SIGNAL_DISTRIBUTION_SPEC_v2.0.0.md, or consolidate them.

**Clear Question:**  
Should the two signal distribution documents have explicitly declared, non-overlapping scopes, or should they be consolidated?

**Available Options:**

| Option | Description |
|---|---|
| A — Declare Boundary | ARCHITECTURE = routing topology and channel architecture; SPEC = entitlement, delivery, tier rules. Add scope declarations to each. |
| B — Consolidate | Merge into one signal distribution canonical document. |
| C — Status Quo | Leave both documents as-is. |

**Consequences:**

- **Option A**: Low effort. Eliminates CON-002. Preserves both documents.
- **Option B**: Reduces active document count by 1. Requires content merge.
- **Option C**: Ambiguity persists.

**Recommended Option:** Option A — Declare Boundary.  
**Reason:** The two documents address complementary aspects (topology vs. delivery rules). Their coexistence is justified if scopes are clearly defined.

**Why Owner Approval Is Required:** Governance decision affecting canonical authority.

**Related Decision Log Entry:** DEC-003  
**Related Conflict:** CON-002  

---

## OWNER-004 — Missing Implementation Modules (trade_temporal_telemetry and scan_scheduler)

**Decision:** How to resolve the critical missing implementation modules referenced in `send/core/signal_engine.py`.

**Clear Question:**  
How should the two missing modules be handled?

**A: trade_temporal_telemetry** — `signal_engine.py` imports and calls `trade_temporal_telemetry.register_open_now_trade()`. The module does not exist. `TRADE_TEMPORAL_TELEMETRY_SPEC_v2.0.0.md` governs this domain.

**B: scan_scheduler** — `signal_engine.py` conditionally imports `from core.scan_scheduler import _focus_state_path`. No module or canonical spec exists for this.

**Available Options for A (trade_temporal_telemetry):**

| Option | Description |
|---|---|
| A1 — Implement module | Implement `send/core/trade_temporal_telemetry.py` per TRADE_TEMPORAL_TELEMETRY_SPEC_v2.0.0.md |
| A2 — Remove import | Remove the trade_temporal_telemetry import and call from signal_engine.py if telemetry is not currently needed |

**Available Options for B (scan_scheduler):**

| Option | Description |
|---|---|
| B1 — Implement module + spec | Implement `send/core/scan_scheduler.py` and add canonical spec reference |
| B2 — Refactor away | Replace the scan_scheduler dependency in signal_engine.py with direct fsm_runtime state path access |
| B3 — Remove call | Remove the update_symbol_replacement_score function if it is not currently needed |

**Consequences:**

- **A1**: Resolves CRITICAL runtime risk (CON-003, GAP-001). Requires implementation work.
- **A2**: Removes functionality. Must confirm the call is not required for production.
- **B1**: Resolves GAP-002. Requires implementation and documentation work.
- **B2**: Simplifies dependency. Lower risk.
- **B3**: Removes functionality. Must confirm not needed.

**Recommended Options:** A1 (implement per existing spec) and B2 (refactor to use fsm_runtime directly).  
**Reason:** trade_temporal_telemetry is governed by an active canonical spec and is called unconditionally — it must be implemented. scan_scheduler has no canonical spec and the functionality can be derived from fsm_runtime state.

**Why Owner Approval Is Required:** Implementation decisions that affect production code require owner direction.

**Related Conflicts:** CON-003, CON-004  
**Related Gaps:** GAP-001, GAP-002  

---

## OWNER-005 — Master Documentation Index

**Decision:** Which document should serve as the single master documentation index.

**Clear Question:**  
Should the master documentation index be:  
(A) `send/docs/MASTER_DOCUMENT_INDEX.md`, or  
(B) `send/docs/BINARYBOT_MASTER_INDEX.md`?  
The non-selected document should be deprecated.

**Available Options:**

| Option | Description |
|---|---|
| A — Select MASTER_DOCUMENT_INDEX | Retain MASTER_DOCUMENT_INDEX.md as the primary index. Deprecate BINARYBOT_MASTER_INDEX.md. |
| B — Select BINARYBOT_MASTER_INDEX | Retain BINARYBOT_MASTER_INDEX.md as the primary index. Deprecate MASTER_DOCUMENT_INDEX.md. |
| C — Consolidate into one new doc | Merge both into a single canonical index document. |

**Consequences:**

- **Option A or B**: One index document deprecated. Single entry point established. Eliminates CON-010.
- **Option C**: More effort; clean result.

**Recommended Option:** Option A — Select MASTER_DOCUMENT_INDEX.md.  
**Reason:** MASTER_DOCUMENT_INDEX.md has a more structured version declaration (Version 1.0.0 with Owner declared) and is more recently structured. However, this is a style preference; both documents are similar in quality. Owner should confirm.

**Why Owner Approval Is Required:** Deprecating an existing document is a governance action.

**Related Decision Log Entry:** DEC-004  
**Related Conflict:** CON-010  

---

## OWNER-006 — Canonical Status of Security and Risk Documents

**Decision:** Whether SECURITY_MODEL.md and RISK_MODEL.md should be promoted to active canonical status.

**Clear Question:**  
Should `send/docs/SECURITY_MODEL.md` and `send/docs/RISK_MODEL.md` be:  
(A) Promoted to active canonical documents in `send/docs/canonical/active/`, or  
(B) Merged into existing active documents (SYSTEM_INVARIANTS_v2.0.0, GOVERNANCE_AND_CHANGE_CONTROL_v2.0.0), or  
(C) Left in their current root-level position as supporting references?

**Available Options:**

| Option | Description |
|---|---|
| A — Promote both | Add both to active canonical set as new v2.0.0 specs |
| B — Merge into active | Absorb rules into existing active specs |
| C — Leave as supporting | Retain in root docs, classify as supporting references |

**Consequences:**

- **Option A**: Expands active canonical set. Establishes security and risk as formal canonical domains.
- **Option B**: Keeps active set smaller. Risk of diluting security/risk rules across other docs.
- **Option C**: Leaves security and risk without canonical governance.

**Recommended Option:** Option A — Promote both, with version update to v2.0.0.  
**Reason:** Security and risk are primary system concerns. Having them as active canonical specifications ensures they are maintained alongside the system. The current root-level placement reduces their visibility and governance.

**Why Owner Approval Is Required:** Adding documents to the active canonical set is a governance decision that establishes new authority.

**Related Decisions:** DEC-007, DEC-008  
**Related Gaps:** GAP-007, GAP-008  

---

## OWNER-007 — Proposed Admin Control Plane Canon Promotion

**Decision:** Whether to promote `send/docs/canonical/proposed/ADMIN_SURFACE_AND_CONTROL_PLANE_CANON_v1.0.0.md` to active canonical status.

**Clear Question:**  
Should the proposed ADMIN_SURFACE_AND_CONTROL_PLANE_CANON document be:  
(A) Promoted to active canonical status as the root manifest for the admin/control-plane cluster, or  
(B) Rejected and the current cluster of admin specs (ADMIN_CONTROL_SPEC, ADMIN_OPERATIONS_SPEC, ADMIN_TREE_MAP, CONTROL_PANEL_HIERARCHY_AND_INTELLIGENCE_SPEC) retained as the governing set without a root manifest?

**Available Options:**

| Option | Description |
|---|---|
| A — Promote | Move to active/, update version to v2.0.0, establish as admin cluster root manifest analogous to CANONICAL_STRATEGY_STACK |
| B — Reject | Discard the proposed document or reclassify as satellite reference |

**Consequences:**

- **Option A**: Provides a unified entry point for the admin domain, similar to CANONICAL_STRATEGY_STACK for the strategy domain. Adds one document to active canonical set. The proposed doc references all active admin specs — only governance work required, no code change.
- **Option B**: Admin domain remains governed by the existing cluster. No new document required.

**Recommended Option:** Option A — Promote.  
**Reason:** The admin cluster currently has 4+ active canonical documents with no root manifest declaring their relationships and authority order. A root manifest would reduce ambiguity, consistent with the CANONICAL_STRATEGY_STACK pattern. The proposed document appears ready for promotion.

**Why Owner Approval Is Required:** Promoting from proposed to active canonical requires governance approval.

**Related Decision Log Entry:** DEC-010  

---

*End of OWNER_DECISIONS_REQUIRED.md*
