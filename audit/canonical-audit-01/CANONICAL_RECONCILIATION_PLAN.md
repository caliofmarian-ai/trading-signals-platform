# CANONICAL_RECONCILIATION_PLAN.md

**Audit ID:** canonical-audit-01  
**Date:** 2026-07-12  

> **SAFETY NOTE:** This plan is non-destructive and non-executable until each phase receives explicit owner approval. No file modifications, deletions, or promotions should occur before the specified owner decisions are confirmed. Historical record must be preserved throughout.

---

## Phase 0 — Owner Decision Gate

**Objective:** Obtain owner direction on the 7 unresolved decisions before any reconciliation work begins.

**Inputs:**
- `audit/canonical-audit-01/OWNER_DECISIONS_REQUIRED.md`
- `audit/canonical-audit-01/CANONICAL_DECISION_LOG.md`
- `audit/canonical-audit-01/CANONICAL_CONFLICT_REGISTER.md`

**Actions:**
1. Owner reviews OWNER_DECISIONS_REQUIRED.md and provides explicit decisions for OWNER-001 through OWNER-007.
2. Record owner decisions in a new `audit/canonical-audit-01/OWNER_DECISION_RESPONSES.md` file.
3. Verify no action has been taken before owner responses are received.

**Outputs:**
- `audit/canonical-audit-01/OWNER_DECISION_RESPONSES.md` with confirmed decisions

**Validation Criteria:**
- All 7 OWNER decisions have explicit responses.
- Responses are recorded before Phase 1 begins.

**Rollback / Safety:**
- No changes to any source file until this phase is complete.

**Dependencies on Owner Decisions:**
- All phases depend on Phase 0 completion.

---

## Phase 1 — Critical Implementation Gap Resolution

**Objective:** Resolve CRITICAL and HIGH-risk implementation gaps that pose production reliability risk.

**Inputs:**
- Owner decision from OWNER-004 (missing modules)
- `send/docs/canonical/active/TRADE_TEMPORAL_TELEMETRY_SPEC_v2.0.0.md`
- `send/core/signal_engine.py`
- `send/core/fsm_runtime.py`

**Actions (per owner direction from OWNER-004):**
1. Implement `send/core/trade_temporal_telemetry.py` per TRADE_TEMPORAL_TELEMETRY_SPEC_v2.0.0.md (if Option A1 selected). — GAP-001
2. Resolve `scan_scheduler` dependency in `signal_engine.py`: either implement the module or refactor the call to use fsm_runtime state directly (per owner direction from OWNER-004). — GAP-002
3. Update `send/schema/params_schema.json` to match the validated parameter structure in `params_loader.py` and `algo_params.json`. — GAP-006, CON-005

**Outputs:**
- `send/core/trade_temporal_telemetry.py` (if implemented)
- Updated `send/schema/params_schema.json`
- Updated or refactored `send/core/signal_engine.py` scan_scheduler reference

**Validation Criteria:**
- Python import of `trade_temporal_telemetry` succeeds without ImportError.
- `params_schema.json` keys match `params_loader.py` REQUIRED_TOP_LEVEL_KEYS.
- No new functionality added beyond what specs define.

**Rollback / Safety:**
- Back up all modified files before changes (append to `send/_archive/backups/`).
- Changes limited to implementing documented canonical specs, not new logic.

**Dependencies on Owner Decisions:** OWNER-004 required.

---

## Phase 2 — Canonical Document Hierarchy Declarations

**Objective:** Add explicit hierarchy and scope declarations to documents with overlapping domains. No content removal, only additions.

**Inputs:**
- Owner decisions from OWNER-002 (observability boundary) and OWNER-003 (distribution boundary)
- `send/docs/canonical/active/OBSERVABILITY_SPEC_v2.0.0.md`
- `send/docs/canonical/active/OBSERVABILITY_LOGGING_SPEC_v2.0.0.md`
- `send/docs/canonical/active/SIGNAL_DISTRIBUTION_ARCHITECTURE_v2.0.0.md`
- `send/docs/canonical/active/SIGNAL_DISTRIBUTION_SPEC_v2.0.0.md`

**Actions (per owner directions from OWNER-002 and OWNER-003):**
1. If OWNER-002 = Option A (hierarchy): Add deference clause to OBSERVABILITY_LOGGING_SPEC declaring it defers to OBSERVABILITY_SPEC for system policy. Update OBSERVABILITY_SPEC to declare OBSERVABILITY_LOGGING_SPEC as its implementation-level companion. — CON-001
2. If OWNER-002 = Option B (consolidate): Merge both observability docs into one. Deprecate the merged document with an explicit supersession marker.
3. If OWNER-003 = Option A (declare boundary): Add explicit scope declarations to SIGNAL_DISTRIBUTION_ARCHITECTURE (topology) and SIGNAL_DISTRIBUTION_SPEC (entitlement/delivery). — CON-002
4. If OWNER-003 = Option B (consolidate): Merge both distribution docs into one.

**Outputs:**
- Updated active canonical documents with explicit hierarchy declarations.

**Validation Criteria:**
- Each updated document explicitly declares its scope and any deference relationships.
- No document references another as authoritative without explicit scope boundary.
- CON-001 and CON-002 are eliminated.

**Rollback / Safety:**
- Back up all modified documents before changes.
- Changes are additive (deference clauses) not deletive.

**Dependencies on Owner Decisions:** OWNER-002, OWNER-003.

---

## Phase 3 — New Canonical Document Promotions

**Objective:** Promote proposed and candidate documents to active canonical status per owner decisions.

**Inputs:**
- Owner decisions from OWNER-001 (community/privacy), OWNER-006 (security/risk), OWNER-007 (admin control plane)
- `send/docs/intake/COMMUNITY_FEEDBACK_AND_PRIVACY_SPEC.md`
- `send/docs/SECURITY_MODEL.md`
- `send/docs/RISK_MODEL.md`
- `send/docs/canonical/proposed/ADMIN_SURFACE_AND_CONTROL_PLANE_CANON_v1.0.0.md`

**Actions (per owner directions):**
1. If OWNER-001 = Promote: Create `send/docs/canonical/active/COMMUNITY_FEEDBACK_AND_PRIVACY_SPEC_v2.0.0.md` with updated header and version. Cross-reference relevant active docs. — GAP-010, DEC-001
2. If OWNER-001 = Major-Merge: Merge content from intake doc into OUTCOME_TRACKING_SPEC_v2.0.0, TELEGRAM_UX_v2.0.0, GOVERNANCE_AND_CHANGE_CONTROL_v2.0.0. Classify intake original as satellite reference.
3. If OWNER-006 = Promote both: Create `send/docs/canonical/active/SECURITY_MODEL_v2.0.0.md` and `send/docs/canonical/active/RISK_MODEL_v2.0.0.md`. Update CANONICAL_STRATEGY_STACK to reference new docs. — GAP-007, GAP-008
4. If OWNER-007 = Promote: Move `ADMIN_SURFACE_AND_CONTROL_PLANE_CANON_v1.0.0.md` to active/, update version to v2.0.0, update header. — DEC-010
5. Update CANONICAL_STRATEGY_STACK_v1.0.0 to reference any new active canonical documents.

**Outputs:**
- New active canonical documents (as approved)
- Updated CANONICAL_STRATEGY_STACK_v1.0.0

**Validation Criteria:**
- All new documents follow the canonical document header format (Path, Version, Status, Owner, Scope, Linked Documents, Depends on).
- CANONICAL_STRATEGY_STACK updated to reflect new documents.
- Deprecated intake originals correctly classified.

**Rollback / Safety:**
- New document creation is non-destructive. No existing file is modified without backup.
- If a promotion is reversed, delete the new active document and restore the original to intake status.

**Dependencies on Owner Decisions:** OWNER-001, OWNER-006, OWNER-007.

---

## Phase 4 — Intake Document Classification and CANON_BATCH_EVALUATION Execution

**Objective:** Execute the merge actions identified in CANON_BATCH_EVALUATION_v2.0.0.md for intake documents.

**Inputs:**
- `send/docs/canonical/active/CANON_BATCH_EVALUATION_v2.0.0.md` (verdicts)
- `send/docs/intake/ADAPTIVE_ACTIVITY_GATE_SPEC.md`
- `send/docs/intake/AI_STRATEGY_AUDITOR_SPEC.md`
- `send/docs/intake/INTELLIGENCE_DATA_PIPELINE_DEFINITION.md`
- `send/docs/intake/INTELLIGENCE_FILES_AND_MODULE_MAP.md`
- Target active docs per CANON_BATCH_EVALUATION verdict table

**Actions:**
1. Merge `ADAPTIVE_ACTIVITY_GATE_SPEC.md` content into `ALGO_SPEC_v2.0.0.md`, `DECISION_AUDIT_SPEC_v2.0.0.md`, `TRADE_TEMPORAL_TELEMETRY_SPEC_v2.0.0.md`. — GAP-011, DEC-006
2. Merge `AI_STRATEGY_AUDITOR_SPEC.md` selected sections into `RESEARCH_AND_LEARNING_FRAMEWORK_SPEC_v2.0.0.md`, `PERFORMANCE_ANALYTICS_SPEC_v2.0.0.md`, `STRATEGY_INTELLIGENCE_SYSTEM_v2.0.0.md`. — DEC-006
3. Merge `INTELLIGENCE_DATA_PIPELINE_DEFINITION.md` into `STRATEGY_INTELLIGENCE_SYSTEM_v2.0.0.md`, `MODULE_INTERFACE_SPEC_v2.0.0.md`, `OBSERVABILITY_SPEC_v2.0.0.md`. — DEC-006
4. Merge `INTELLIGENCE_FILES_AND_MODULE_MAP.md` into `MODULE_INTERFACE_SPEC_v2.0.0.md`, `STRATEGY_INTELLIGENCE_SYSTEM_v2.0.0.md`. — DEC-006
5. Classify remaining intake docs as satellite reference or proposed/future-state per CANON_BATCH_EVALUATION verdicts.
6. Move `CANON_BATCH_EVALUATION_v2.0.0.md` from `send/docs/canonical/active/` to `send/docs/canonical/governance_records/`. — DEC-005, CON-011

**Outputs:**
- Updated active canonical documents (ALGO_SPEC, RESEARCH_AND_LEARNING, PERFORMANCE_ANALYTICS, STRATEGY_INTELLIGENCE_SYSTEM, MODULE_INTERFACE_SPEC, OBSERVABILITY_SPEC)
- Classified intake documents (satellite/proposed status markers added)
- `send/docs/canonical/governance_records/` subfolder created

**Validation Criteria:**
- All merged content is clearly attributed (section markers identify source document).
- No information lost in merge process.
- Intake originals retained with satellite/proposed classification header added.
- CANON_BATCH_EVALUATION moved to governance_records folder.

**Rollback / Safety:**
- Back up all modified active docs before merge.
- Do not remove any intake original file.
- Add classification headers to intake originals rather than modifying content.

**Dependencies on Owner Decisions:** Owner approval of DEC-006 needed.

---

## Phase 5 — Cross-Reference Repair

**Objective:** Update all obsolete and broken cross-references in supporting documents.

**Inputs:**
- `audit/canonical-audit-01/CANONICAL_GAP_ANALYSIS.md` (GAP-013)
- `audit/canonical-audit-01/CANONICAL_CONFLICT_REGISTER.md` (CON-008)
- All supporting documents with stale references

**Actions:**
1. Update `send/docs/CANONICAL_REFACTOR_PLAN_v1.0.0.md`: replace `SIGNAL_ENGINE_EXECUTION_SPEC_v1.0.0.md` with `v2.0.0`; replace `SIGNAL_TIME_MODEL_SPEC_v2.0.0.md` with `TIME_MODEL_UNIFIED_CANON_v2.0.0.md`. — CON-008, GAP-013
2. Update `send/docs/DOCUMENT_LAYER_INDEX.md`: replace `PARAMS_REFERENCE.md` with `STRATEGY_PARAMETER_CONTROL_SPEC_v2.0.0.md`. — CON-008, GAP-013
3. Update `send/docs/FORMAL_SPEC.md`: replace `PARAMS_REFERENCE.md` reference. — GAP-013
4. Update `send/core/params_loader.py` comment: replace `PARAMS_REFERENCE.md` with `STRATEGY_PARAMETER_CONTROL_SPEC_v2.0.0.md`. — CON-008
5. Update `send/docs/DOCUMENT_IMPLEMENTATION_MATRIX.md`: replace `admin_router.py` and `callback_router.py` with actual module names. — CON-006
6. Update `DOCUMENT_STATUS_POLICY.md` vocabulary to align with canonical status vocabulary used in active docs. — CON-009
7. Supersede/update one of the two master index documents per OWNER-005 decision. — CON-010, DEC-004

**Outputs:**
- Updated supporting documents with correct cross-references
- Aligned status vocabulary

**Validation Criteria:**
- No document references a document name that does not exist in the repository (excluding superseded/ folder references to historical docs).
- Status vocabulary in DOCUMENT_STATUS_POLICY matches active canonical docs.
- Exactly one master index document is designated primary.

**Rollback / Safety:**
- Back up all modified documents.
- Changes are reference updates only — no content deletion.

**Dependencies on Owner Decisions:** OWNER-005 for master index selection.

---

## Phase 6 — Schema and Interface Alignment

**Objective:** Align schema files with their governing specifications and runtime implementations.

**Inputs:**
- `send/schema/event_schema.json`
- `send/schema/params_schema.json`
- `send/docs/canonical/active/EVENT_SCHEMA_SPEC_v2.0.0.md`
- `send/docs/canonical/active/STRATEGY_PARAMETER_CONTROL_SPEC_v2.0.0.md`
- `send/core/params_loader.py`

**Actions:**
1. Expand `send/schema/event_schema.json` to cover all event types defined in EVENT_SCHEMA_SPEC_v2.0.0.md. — GAP-005
2. Align `send/schema/params_schema.json` with the actual runtime parameter structure (matching params_loader.py validation). — GAP-006, CON-005
3. Define a formal admin command interface spec or update `ADMIN_CALLBACK_MAP.md` to reference actual modules. — GAP-014
4. Verify `send/config/admin_roles.json` and `send/config/admin_permissions.json` schema against ROLE_AND_PERMISSION_MATRIX_SPEC_v2.0.0.md. — GAP-018

**Outputs:**
- Updated `send/schema/event_schema.json`
- Updated `send/schema/params_schema.json`
- Admin interface definition (new doc or updated ADMIN_CALLBACK_MAP.md)

**Validation Criteria:**
- `params_schema.json` keys match `algo_params.json` structure and `params_loader.py` required keys.
- `event_schema.json` schema_version updated to 2.0.0 and covers at minimum all event types emitted by `observability_logger.py`.
- CON-005 and GAP-005 eliminated.

**Rollback / Safety:**
- Back up schema files before modification.
- Schema changes are non-breaking if only additions.

**Dependencies on Owner Decisions:** None required (schema maintenance).

---

## Phase 7 — Implementation Alignment

**Objective:** Align implementation modules with canonical specifications for unverified and partial-alignment modules.

**Inputs:**
- `audit/canonical-audit-01/CODE_TO_CANON_ALIGNMENT_MATRIX.md` (UNVERIFIED and PARTIAL entries)
- Active canonical documents for each domain

**Actions:**
1. Perform detailed alignment review of all UNVERIFIED modules against their governing specifications.
2. Verify intelligence modules (`send/intelligence/`) against `STRATEGY_INTELLIGENCE_SYSTEM_v2.0.0.md`, `RESEARCH_AND_LEARNING_FRAMEWORK_SPEC_v2.0.0.md`, `PERFORMANCE_ANALYTICS_SPEC_v2.0.0.md`. — GAP-012
3. Verify `send/core/distribution_router.py` hardcoded RESET_HOUR=8 and LONDON_TZ against SIGNAL_DISTRIBUTION_SPEC_v2.0.0.md and CHANNEL_CONFIG_SPEC_v2.0.0.md.
4. Verify `send/core/admin_commands.py` hardcoded paths against ADMIN_OPERATIONS_SPEC_v2.0.0.md.
5. Verify `send/validation/statistical_proof.py` against PERFORMANCE_ANALYTICS_SPEC_v2.0.0.md.
6. Update CODE_TO_CANON_ALIGNMENT_MATRIX.md with findings.
7. File implementation gap issues per findings.

**Outputs:**
- Updated `audit/canonical-audit-01/CODE_TO_CANON_ALIGNMENT_MATRIX.md`
- List of new implementation gaps (if found)

**Validation Criteria:**
- All modules have a confirmed alignment status (no UNVERIFIED entries remain).
- Any new gaps are documented and tracked.

**Rollback / Safety:**
- This phase is inspection-only. No code changes unless directed by owner.

**Dependencies on Owner Decisions:** Phase 1 must be complete (critical gaps resolved).

---

## Phase 8 — Repository Hygiene

**Objective:** Clean production module directory of non-source artifacts. Establish governance records subfolder.

**Inputs:**
- `send/core/strategy_v2 - Copy.py` (duplicate artifact in production directory)
- `send/core/strategy_v2.py.bak_decision_audit` (backup in production directory)
- `send/docs/canonical/active/CANON_BATCH_EVALUATION_v2.0.0.md`

**Actions:**
1. Move `send/core/strategy_v2 - Copy.py` to `send/_archive/backups/`. — CON-012
2. Move `send/core/strategy_v2.py.bak_decision_audit` to `send/_archive/backups/`. — CON-012
3. Create `send/docs/canonical/governance_records/` directory.
4. Move `send/docs/canonical/active/CANON_BATCH_EVALUATION_v2.0.0.md` to `send/docs/canonical/governance_records/`. — DEC-005, CON-011
5. Clarify status of `send/legacy/bot_control.py` — move to `send/_archive/` if no longer needed, or add canonical reference. — GAP-017

**Outputs:**
- Clean `send/core/` directory (only active source files)
- `send/docs/canonical/governance_records/` subfolder
- Resolved CON-011, CON-012

**Validation Criteria:**
- `send/core/` contains only active Python source files.
- `send/docs/canonical/active/` contains only active canonical specification documents.
- All moved files remain accessible in their new locations.
- No file is deleted.

**Rollback / Safety:**
- Files are moved, not deleted. Move is reversible by returning to original location.

**Dependencies on Owner Decisions:** None strictly required, but OWNER-007 resolution should be confirmed before changing active/ folder contents.

---

## Phase 9 — Validation and Final Audit

**Objective:** Verify that all reconciliation actions are complete, consistent, and have not introduced new issues.

**Inputs:**
- All modified documents and code
- `audit/canonical-audit-01/` audit documents

**Actions:**
1. Verify all Markdown links in updated documents resolve to existing files.
2. Verify all cross-references use current canonical document names.
3. Verify that no existing source file has been deleted.
4. Verify application code changes are limited to those approved in Phase 1.
5. Verify all material conflicts in CANONICAL_CONFLICT_REGISTER.md are resolved or have documented open status.
6. Update `audit/canonical-audit-01/` documents to reflect resolved items.
7. Run a complete canonical document inventory against the updated active/ folder.

**Outputs:**
- `audit/canonical-audit-01/RECONCILIATION_VALIDATION_REPORT.md`
- Updated conflict register with resolved/open status per item

**Validation Criteria:**
- Conflict register shows RESOLVED or OPEN (with owner tracking) for all 12 conflicts.
- Gap analysis shows RESOLVED or TRACKED for all 18 gaps.
- No new conflicts introduced.
- All mandatory safety rules (Rule 1–11 from problem statement) verified.

**Rollback / Safety:**
- If validation reveals new conflicts, stop and document before proceeding.

**Dependencies on Owner Decisions:** All phases must be complete.

---

## Phase 10 — Historical Preservation Confirmation

**Objective:** Confirm that no historical documents have been lost and the record is complete.

**Actions:**
1. Verify `send/docs/_deprecated/` contents are intact.
2. Verify `send/docs/canonical/superseded/` contents are intact.
3. Verify `send/docs/canonical/deprecated/` contents are intact.
4. Verify `send/_archive/backups/` has received all newly moved files.
5. Confirm DOCUMENT_INVENTORY.md baseline is preserved for comparison.

**Outputs:**
- Historical preservation confirmation statement

**Validation Criteria:**
- Every file that existed at audit start is still accessible.
- All moved files are in their new locations.
- No content has been deleted.

---

*End of CANONICAL_RECONCILIATION_PLAN.md*
