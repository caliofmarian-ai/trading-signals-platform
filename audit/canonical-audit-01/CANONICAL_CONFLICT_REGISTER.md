# CANONICAL_CONFLICT_REGISTER.md

**Audit ID:** canonical-audit-01  
**Date:** 2026-07-12  
**Total Material Conflicts:** 12  

---

## Conflict Severity Scale

- **CRITICAL**: Causes or risks runtime failures or data corruption
- **HIGH**: Directly contradicts authoritative specification or blocks canonical consolidation
- **MEDIUM**: Ambiguous domain ownership or cross-reference inconsistency
- **LOW**: Minor labeling, naming, or organizational inconsistency

---

## CON-001

| Field | Value |
|---|---|
| **Conflict ID** | CON-001 |
| **Affected Documents** | `send/docs/canonical/active/OBSERVABILITY_SPEC_v2.0.0.md` (CAM-008); `send/docs/canonical/active/OBSERVABILITY_LOGGING_SPEC_v2.0.0.md` (CAM-009) |
| **Topic / Rule in Conflict** | Domain ownership of the observability layer |
| **Nature of Contradiction** | Both documents claim canonical authority over the observability domain. OBSERVABILITY_SPEC_v2.0.0 declares scope as "end-to-end observability, auditability, rejection analytics, and semantic traceability." OBSERVABILITY_LOGGING_SPEC_v2.0.0 declares scope as "Observability, Telemetry, Logging & Auditability Specification." Neither explicitly supersedes the other or defines an authoritative boundary between them. OBSERVABILITY_SPEC cross-references OBSERVABILITY_LOGGING_SPEC (suggesting LOGGING_SPEC is a sub-layer), but this hierarchy is not declared explicitly in either document. |
| **Operational / Architectural Risk** | MEDIUM — Implementers and future contributors cannot determine which document governs a specific observability rule. Changes to one may conflict with the other. |
| **Evidence** | OBSERVABILITY_SPEC header: "Scope: End-to-end observability, auditability, rejection analytics, and semantic traceability." OBSERVABILITY_LOGGING_SPEC header: "BinaryBot — Observability, Telemetry, Logging & Auditability Specification." Both are declared CANONICAL. Both cross-reference `send/core/observability_logger.py`. |
| **Recommended Resolution** | Establish explicit hierarchy: designate OBSERVABILITY_SPEC as the system-level policy root and OBSERVABILITY_LOGGING_SPEC as the implementation-level detail spec, with a deference clause in OBSERVABILITY_LOGGING_SPEC that reads "this document defines the implementation contract; policy authority resides in OBSERVABILITY_SPEC_v2.0.0." Or consolidate into a single document. Owner decision required. |
| **Owner Input Required** | **Yes** — see OWNER-002 |

---

## CON-002

| Field | Value |
|---|---|
| **Conflict ID** | CON-002 |
| **Affected Documents** | `send/docs/canonical/active/SIGNAL_DISTRIBUTION_ARCHITECTURE_v2.0.0.md` (CAM-010); `send/docs/canonical/active/SIGNAL_DISTRIBUTION_SPEC_v2.0.0.md` (CAM-011) |
| **Topic / Rule in Conflict** | Domain boundary between signal distribution architecture and distribution specification |
| **Nature of Contradiction** | Both documents address the signal distribution domain. SIGNAL_DISTRIBUTION_ARCHITECTURE focuses on system topology and routing architecture. SIGNAL_DISTRIBUTION_SPEC focuses on entitlement routing, delivery governance, and tier rules. The boundary between "architecture" and "spec" is not formally defined. ARCHITECTURE cross-references SPEC, but neither document declares precedence over the other. |
| **Operational / Architectural Risk** | MEDIUM — Ambiguous domain boundary increases risk of divergence when one document is updated without updating the other. |
| **Evidence** | SIGNAL_DISTRIBUTION_ARCHITECTURE header: "Status: Active Canonical." SIGNAL_DISTRIBUTION_SPEC header: "Status: CANONICAL." Both reference distribution_router.py. ARCHITECTURE lists SIGNAL_DISTRIBUTION_SPEC_v2.0.0.md as a linked document. |
| **Recommended Resolution** | Declare SIGNAL_DISTRIBUTION_SPEC as the authoritative delivery-and-entitlement ruleset and SIGNAL_DISTRIBUTION_ARCHITECTURE as the authoritative topology reference, with explicit cross-reference in each document to the other. Or consolidate. Owner decision required. |
| **Owner Input Required** | **Yes** — see OWNER-003 |

---

## CON-003

| Field | Value |
|---|---|
| **Conflict ID** | CON-003 |
| **Affected Documents** | `send/core/signal_engine.py`; `send/docs/canonical/active/TRADE_TEMPORAL_TELEMETRY_SPEC_v2.0.0.md` (CAM-023) |
| **Topic / Rule in Conflict** | Implementation existence of trade_temporal_telemetry module |
| **Nature of Contradiction** | `signal_engine.py` imports `from core import trade_temporal_telemetry` and calls `trade_temporal_telemetry.register_open_now_trade(event, now_ts)`. No file named `trade_temporal_telemetry.py` exists anywhere under `send/core/` or any other path in the repository. This creates a runtime ImportError when the relevant code path is executed. |
| **Operational / Architectural Risk** | **CRITICAL** — Missing module will cause a runtime error when signal_engine.py executes the open-trade registration path. This is a production reliability risk. |
| **Evidence** | `signal_engine.py` line: `from core import trade_temporal_telemetry`. `find send/core -name "trade_temporal_telemetry*"` returns no results. TRADE_TEMPORAL_TELEMETRY_SPEC_v2.0.0.md declares the domain as canonical active. |
| **Recommended Resolution** | Implement the missing `send/core/trade_temporal_telemetry.py` module per TRADE_TEMPORAL_TELEMETRY_SPEC_v2.0.0.md. This is an implementation gap, not a document conflict. Do not modify production code without owner direction. |
| **Owner Input Required** | **Yes** — implementation decision (see OWNER-004) |

---

## CON-004

| Field | Value |
|---|---|
| **Conflict ID** | CON-004 |
| **Affected Documents** | `send/core/signal_engine.py`; `send/core/` (module directory) |
| **Topic / Rule in Conflict** | Implementation existence of scan_scheduler module |
| **Nature of Contradiction** | `signal_engine.py` contains a conditional import: `from core.scan_scheduler import _focus_state_path`. No file named `scan_scheduler.py` exists anywhere in the repository. The import is inside a try block (so runtime impact may be suppressed), but the function `_focus_state_path` would not be available if the import fails. |
| **Operational / Architectural Risk** | **HIGH** — If the scan_scheduler path is executed, the ImportError is suppressed by the try/except wrapper, but the `path` variable remains unset, likely causing a downstream NameError or silent failure. No canonical spec for scan_scheduler was found in active documents. |
| **Evidence** | `signal_engine.py` line: `from core.scan_scheduler import _focus_state_path` (inside try block). No scan_scheduler.py found. No canonical spec references this module. |
| **Recommended Resolution** | Either implement `scan_scheduler.py` and add a canonical spec reference, or remove the dependency from signal_engine.py. Owner decision required. |
| **Owner Input Required** | **Yes** — see OWNER-004 |

---

## CON-005

| Field | Value |
|---|---|
| **Conflict ID** | CON-005 |
| **Affected Documents** | `send/schema/params_schema.json`; `send/config/algo_params.json`; `send/core/params_loader.py` |
| **Topic / Rule in Conflict** | Parameter schema key naming and structure |
| **Nature of Contradiction** | `params_schema.json` defines top-level keys: `algo_version`, `strategy_v2`, `buffer_multipliers`, `expiry_limits_minutes`, `score_thresholds`. However, `algo_params.json` uses: `algo_version`, `thresholds`, `weights`, `expiry`, `buffer`, `gates`. `params_loader.py` validates against the actual `algo_params.json` structure (thresholds, weights, expiry, buffer, gates). The JSON schema file (`params_schema.json`) is therefore inconsistent with both the runtime config and the runtime validator — making the schema file misleading or obsolete. |
| **Operational / Architectural Risk** | **HIGH** — Any tooling that validates `algo_params.json` against `params_schema.json` will produce false errors. The schema file cannot be used for validation without causing incorrect rejections. |
| **Evidence** | `params_schema.json` keys: strategy_v2, buffer_multipliers, expiry_limits_minutes, score_thresholds. `algo_params.json` keys: thresholds, weights, expiry, buffer, gates. `params_loader.py` REQUIRED_TOP_LEVEL_KEYS: thresholds, weights, expiry, buffer, gates. |
| **Recommended Resolution** | Update `params_schema.json` to match the actual schema validated by `params_loader.py` and used in `algo_params.json`. This is a schema maintenance issue. |
| **Owner Input Required** | **No** — low-risk schema sync; however, do not modify production code per task safety rules |

---

## CON-006

| Field | Value |
|---|---|
| **Conflict ID** | CON-006 |
| **Affected Documents** | `send/docs/DOCUMENT_IMPLEMENTATION_MATRIX.md`; `send/core/` (module directory) |
| **Topic / Rule in Conflict** | Referenced modules that do not exist in the codebase |
| **Nature of Contradiction** | `DOCUMENT_IMPLEMENTATION_MATRIX.md` lists `core/admin_router.py` and `core/callback_router.py` as "ACTIVE" modules. Neither file exists in the repository. `send/core/admin_commands.py` and `send/core/admin_views.py` appear to handle related functions, but they are not the same modules. Similarly, `ADMIN_CALLBACK_MAP.md` references callback_router.py. |
| **Operational / Architectural Risk** | MEDIUM — The matrix is a supporting document, not a canonical specification. However, it creates false confidence in module coverage and may mislead future contributors. |
| **Evidence** | `DOCUMENT_IMPLEMENTATION_MATRIX.md` rows: `core/admin_router.py | ACTIVE` and `core/callback_router.py | ACTIVE`. `find send/core -name "admin_router*" -o -name "callback_router*"` returns no results. |
| **Recommended Resolution** | Update DOCUMENT_IMPLEMENTATION_MATRIX.md to reflect actual module names. Owner approval not strictly required for a supporting document update, but should be tracked. |
| **Owner Input Required** | **No** (supporting document correction only) |

---

## CON-007

| Field | Value |
|---|---|
| **Conflict ID** | CON-007 |
| **Affected Documents** | All active canonical documents; `send/core/`, `send/runtime/` source files |
| **Topic / Rule in Conflict** | Path references: `/opt/binarybot/` vs actual repository path |
| **Nature of Contradiction** | All canonical documents reference paths beginning with `/opt/binarybot/` (e.g., `/opt/binarybot/docs/canonical/active/ALGO_SPEC_v2.0.0.md`, `/opt/binarybot/core/signal_engine.py`). The actual repository clone is at `/home/runner/work/trading-signals-platform/trading-signals-platform/send/`. Source files also use hardcoded `/opt/binarybot/` paths for runtime state, config, and observability directories. This is the production deployment path (Railway/server), but it creates a mismatch between repository documentation paths and repository file paths. |
| **Operational / Architectural Risk** | MEDIUM — Path mismatch does not cause runtime errors in production if the deployment target is `/opt/binarybot/`. However, it makes it impossible to verify documentation path references during repository inspection without path translation. |
| **Evidence** | `signal_engine.py` comment: `# /opt/binarybot/core/signal_engine.py`. ALGO_SPEC_v2.0.0.md Path header: `/opt/binarybot/docs/canonical/active/ALGO_SPEC_v2.0.0.md`. Repository clone path: `.../send/`. |
| **Recommended Resolution** | Document the deployment path mapping (repository `send/` → production `/opt/binarybot/`) in a root-level README or DEPLOYMENT_PROTOCOL. Do not change production path references without verifying the deployment target. |
| **Owner Input Required** | **No** — documentation note only |

---

## CON-008

| Field | Value |
|---|---|
| **Conflict ID** | CON-008 |
| **Affected Documents** | `send/docs/CANONICAL_REFACTOR_PLAN_v1.0.0.md`; `send/docs/DOCUMENT_LAYER_INDEX.md`; `send/docs/FORMAL_SPEC.md` |
| **Topic / Rule in Conflict** | Obsolete document name references in supporting docs |
| **Nature of Contradiction** | Several root-level supporting documents reference document names that are now superseded. `CANONICAL_REFACTOR_PLAN_v1.0.0.md` references `SIGNAL_ENGINE_EXECUTION_SPEC_v1.0.0.md` (current is v2.0.0) and `SIGNAL_TIME_MODEL_SPEC_v2.0.0.md` (now in superseded/). `DOCUMENT_LAYER_INDEX.md` references `PARAMS_REFERENCE.md` (now superseded by STRATEGY_PARAMETER_CONTROL_SPEC_v2.0.0.md). `params_loader.py` comment references `PARAMS_REFERENCE.md`. |
| **Operational / Architectural Risk** | LOW — These are supporting/satellite documents. The stale references do not affect runtime behavior but create navigational confusion. |
| **Evidence** | `CANONICAL_REFACTOR_PLAN_v1.0.0.md` depends: `SIGNAL_ENGINE_EXECUTION_SPEC_v1.0.0.md`, `SIGNAL_TIME_MODEL_SPEC_v2.0.0.md`. `DOCUMENT_LAYER_INDEX.md` ENGINE LAYER: `PARAMS_REFERENCE.md`. `params_loader.py` comment: "# Canonical references: PARAMS_REFERENCE.md". |
| **Recommended Resolution** | Update obsolete references in supporting documents to point to current canonical document names. Track in reconciliation plan. |
| **Owner Input Required** | **No** |

---

## CON-009

| Field | Value |
|---|---|
| **Conflict ID** | CON-009 |
| **Affected Documents** | `send/docs/DOCUMENT_STATUS_POLICY.md`; active canonical documents |
| **Topic / Rule in Conflict** | Status vocabulary mismatch |
| **Nature of Contradiction** | `DOCUMENT_STATUS_POLICY.md` defines four status values: ACTIVE, PARTIAL, LEGACY, ARCHIVED. Active canonical documents use a different vocabulary: "CANONICAL", "Active Canonical", "Canonical Active Strategy Specification", "Canonical Root Manifest", "Canonical Unified". The two vocabularies are incompatible and cannot be reconciled without a policy revision. The GOVERNANCE_AND_CHANGE_CONTROL_v2.0.0.md document presumably defines the correct governance vocabulary, but `DOCUMENT_STATUS_POLICY.md` has not been updated to match. |
| **Operational / Architectural Risk** | LOW — Does not affect runtime. Creates confusion about which status vocabulary governs document lifecycle. |
| **Evidence** | DOCUMENT_STATUS_POLICY.md status types: ACTIVE, PARTIAL, LEGACY, ARCHIVED. ADMIN_CONTROL_SPEC_v2.0.0.md Status: CANONICAL. ALGO_SPEC_v2.0.0.md Status: Canonical Active Strategy Specification. |
| **Recommended Resolution** | Supersede or update DOCUMENT_STATUS_POLICY.md to align with the vocabulary used in active canonical documents and GOVERNANCE_AND_CHANGE_CONTROL_v2.0.0.md. |
| **Owner Input Required** | **No** |

---

## CON-010

| Field | Value |
|---|---|
| **Conflict ID** | CON-010 |
| **Affected Documents** | `send/docs/MASTER_DOCUMENT_INDEX.md`; `send/docs/BINARYBOT_MASTER_INDEX.md`; `send/docs/canonical/active/CANONICAL_STRATEGY_STACK_v1.0.0.md` |
| **Topic / Rule in Conflict** | Duplicate index documents with no deference declaration |
| **Nature of Contradiction** | Three documents claim to be the master index of the documentation system: `MASTER_DOCUMENT_INDEX.md` (Version 1.0.0, Canonical), `BINARYBOT_MASTER_INDEX.md` (Version 1.0, Canonical), and `CANONICAL_STRATEGY_STACK_v1.0.0.md` (the root manifest). None of the three explicitly defers to any other. CANONICAL_STRATEGY_STACK is the narrowest (strategy stack only), while the other two claim to index all documentation. |
| **Operational / Architectural Risk** | MEDIUM — Contributors may update one index but not the others, causing divergence. The entry point for documentation navigation is ambiguous. |
| **Evidence** | MASTER_DOCUMENT_INDEX.md: "This document provides a complete index of all canonical documentation used by BinaryBot." BINARYBOT_MASTER_INDEX.md: "This document is the master index of the BinaryBot documentation library." CANONICAL_STRATEGY_STACK: "este manifestul root al stack-ului strategic BinaryBot." |
| **Recommended Resolution** | Consolidate into a single master index. Designate either MASTER_DOCUMENT_INDEX or BINARYBOT_MASTER_INDEX as the single entry point. Deprecate the other. Update CANONICAL_STRATEGY_STACK to cross-reference the selected master index. |
| **Owner Input Required** | **Yes** — see OWNER-005 |

---

## CON-011

| Field | Value |
|---|---|
| **Conflict ID** | CON-011 |
| **Affected Documents** | `send/docs/canonical/active/CANON_BATCH_EVALUATION_v2.0.0.md` (CAM-037); `send/docs/canonical/active/` (active folder) |
| **Topic / Rule in Conflict** | Governance record file misplaced in active canonical folder |
| **Nature of Contradiction** | `CANON_BATCH_EVALUATION_v2.0.0.md` is a documentation governance record, not a canonical specification. It explicitly declares it is "documentation-governance only" and "does not patch code." Placing it in the `active/` folder alongside specification documents implies it is an active specification, which it is not. |
| **Operational / Architectural Risk** | LOW — Governance record misclassification does not affect runtime, but it inflates the apparent size of the active canonical set and may cause confusion. |
| **Evidence** | CANON_BATCH_EVALUATION_v2.0.0.md: "This evaluation is documentation-governance only. It does not patch code and does not itself promote any document." File location: `send/docs/canonical/active/`. |
| **Recommended Resolution** | Move CANON_BATCH_EVALUATION_v2.0.0.md to a governance/records subfolder (e.g., `send/docs/canonical/governance_records/`). Update any references. |
| **Owner Input Required** | **No** (organizational, not a policy change) |

---

## CON-012

| Field | Value |
|---|---|
| **Conflict ID** | CON-012 |
| **Affected Documents** | `send/core/strategy_v2.py`; `send/core/strategy_v2 - Copy.py` |
| **Topic / Rule in Conflict** | Duplicate production source file in core module directory |
| **Nature of Contradiction** | `send/core/strategy_v2 - Copy.py` is an exact duplicate of `send/core/strategy_v2.py` (confirmed in DOCUMENT_INVENTORY.md, duplicate group 014). This file is in the active `core/` module directory alongside production code. If any import mechanism were to load it (e.g., a glob-based test runner), it could shadow or conflict with the canonical module. |
| **Operational / Architectural Risk** | MEDIUM — The file is not a standard Python module name and will not be automatically imported by Python's module system due to the space in the filename. However, it is a maintenance hazard and violates the principle of clean production code directories. |
| **Evidence** | DOCUMENT_INVENTORY.md group 014: `send/core/strategy_v2 - Copy.py`; `send/core/strategy_v2.py`; `send/core/strategy_v2.py.bak_decision_audit` — all exact duplicates. |
| **Recommended Resolution** | Move `strategy_v2 - Copy.py` and `strategy_v2.py.bak_decision_audit` to `send/_archive/backups/` to keep the production module directory clean. Do not delete (preserve history per safety rules). |
| **Owner Input Required** | **No** (maintenance, not a policy change) |

---

*End of CANONICAL_CONFLICT_REGISTER.md*
