# CANONICAL_SUPERSESSION_REGISTER.md

**Governance Record:** canonical-reconciliation-01  
**Date:** 2026-07-12  
**Source Audit:** canonical-audit-01  

---

## Summary

This document records all documents that were classified as superseded or that had their supersession status confirmed during canonical governance reconciliation task `canonical-reconciliation-01`.

---

## New Supersessions Applied in This Task

### OWNER-005: Historical Master Indexes → CANONICAL_MASTER_INDEX_v1.0.0.md

| Superseded Document | Superseded By | Date | Retained |
|---|---|---|---|
| `send/docs/MASTER_DOCUMENT_INDEX.md` | `send/docs/canonical/active/CANONICAL_MASTER_INDEX_v1.0.0.md` | 2026-07-12 | Yes |
| `send/docs/BINARYBOT_MASTER_INDEX.md` | `send/docs/canonical/active/CANONICAL_MASTER_INDEX_v1.0.0.md` | 2026-07-12 | Yes |

**Condition applied:** Superseded header added to both documents only after `CANONICAL_MASTER_INDEX_v1.0.0.md` was created and validated (41 active documents, each appearing exactly once).

---

### OWNER-001: Legacy Feedback and Privacy Documents → COMMUNITY_FEEDBACK_AND_PRIVACY_SPEC_v2.0.0.md

| Superseded Document | Superseded By | Date | Retained |
|---|---|---|---|
| `send/docs/intake/COMMUNITY_FEEDBACK_AND_PRIVACY_SPEC.md` | `send/docs/canonical/active/COMMUNITY_FEEDBACK_AND_PRIVACY_SPEC_v2.0.0.md` | 2026-07-12 | Yes (intake source) |
| `send/docs/_deprecated/ELITE_FEEDBACK_SPEC.md` | `send/docs/canonical/active/COMMUNITY_FEEDBACK_AND_PRIVACY_SPEC_v2.0.0.md` | 2026-07-12 | Yes (deprecated) |
| `send/docs/_deprecated/ELITE_MEMBER_FEEDBACK_AND_LEADERBOARD_SPEC.md` | `send/docs/canonical/active/COMMUNITY_FEEDBACK_AND_PRIVACY_SPEC_v2.0.0.md` | 2026-07-12 | Yes (deprecated) |
| `send/docs/_deprecated/MEMBER_FEEDBACK_SPEC.md` | `send/docs/canonical/active/COMMUNITY_FEEDBACK_AND_PRIVACY_SPEC_v2.0.0.md` | 2026-07-12 | Yes (deprecated) |
| `send/docs/_deprecated/PRIVACY_AND_MEMBER_STATS_ACCESS_SPEC.md` | `send/docs/canonical/active/COMMUNITY_FEEDBACK_AND_PRIVACY_SPEC_v2.0.0.md` | 2026-07-12 | Yes (deprecated) |

---

### OWNER-006: Root-Level Security and Risk Documents → Canonical Active v2.0.0

| Superseded Document | Superseded By | Date | Retained |
|---|---|---|---|
| `send/docs/SECURITY_MODEL.md` | `send/docs/canonical/active/SECURITY_MODEL_v2.0.0.md` | 2026-07-12 | Yes (root-level source) |
| `send/docs/RISK_MODEL.md` | `send/docs/canonical/active/RISK_MODEL_v2.0.0.md` | 2026-07-12 | Yes (root-level source) |

---

### OWNER-007: Proposed Admin Canon v1.0.0 → Active Canon v2.0.0

| Superseded Document | Superseded By | Date | Retained |
|---|---|---|---|
| `send/docs/canonical/proposed/ADMIN_SURFACE_AND_CONTROL_PLANE_CANON_v1.0.0.md` | `send/docs/canonical/active/ADMIN_SURFACE_AND_CONTROL_PLANE_CANON_v2.0.0.md` | 2026-07-12 | Yes (proposed source) |

---

## Previously Existing Supersessions (Confirmed Preserved)

The following documents were already classified as superseded prior to this task. Their status is confirmed unchanged.

| Location | Count | Classification |
|---|---|---|
| `send/docs/canonical/superseded/` | 3 | Superseded canonical documents |
| `send/docs/canonical/deprecated/` | 11 | Deprecated canonical documents |
| `send/docs/_deprecated/` | ~25 | Deprecated root-level documents |
| `send/docs/_deprecated/legacy_strategy_duplicates/` | ~19 | Legacy duplicate documents |
| `send/docs/_deprecated/backups/` | ~7 | Backup documents |

---

## Supersession Integrity Rules

1. No superseded or deprecated document has been deleted.
2. All supersession relationships are traceable to an approved owner decision.
3. The CANONICAL_MASTER_INDEX_v1.0.0.md was validated before superseded headers were applied to the two historical master indexes.
4. No document has been classified as superseded without a replacement being created and validated first.

---

*End of CANONICAL_SUPERSESSION_REGISTER.md*
