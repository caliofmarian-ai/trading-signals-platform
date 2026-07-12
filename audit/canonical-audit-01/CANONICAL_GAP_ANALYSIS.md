# CANONICAL_GAP_ANALYSIS.md

**Audit ID:** canonical-audit-01  
**Date:** 2026-07-12  
**Total Gaps Identified:** 18  

---

## GAP Classification

- **DOMAIN-GAP**: A functional domain exists in the system but has no authoritative canonical specification.
- **SPEC-GAP**: A canonical requirement is not reflected in code (implementation missing).
- **CODE-GAP**: Code behavior exists with no governing canonical document.
- **REF-GAP**: A broken or obsolete cross-reference.
- **INTERFACE-GAP**: An interface is undefined or inconsistently defined.
- **SCHEMA-GAP**: Inconsistent schemas, parameters, statuses, or events.

---

## GAP-001 — Missing Module: trade_temporal_telemetry

| Field | Value |
|---|---|
| **Gap ID** | GAP-001 |
| **Gap Type** | SPEC-GAP (canonical requirement not in code) |
| **Domain** | Trade Temporal Telemetry |
| **Governing Specification** | `send/docs/canonical/active/TRADE_TEMPORAL_TELEMETRY_SPEC_v2.0.0.md` (CAM-023) |
| **Description** | `signal_engine.py` imports and calls `trade_temporal_telemetry.register_open_now_trade()`. The module `send/core/trade_temporal_telemetry.py` does not exist in the repository. The TRADE_TEMPORAL_TELEMETRY_SPEC_v2.0.0 is an active canonical spec for this domain. |
| **Risk** | CRITICAL — Runtime ImportError when the open-trade registration code path is reached |
| **Evidence** | `signal_engine.py`: `from core import trade_temporal_telemetry`. No such file found. |
| **Recommended Action** | Implement `send/core/trade_temporal_telemetry.py` per the spec. Requires owner direction (see OWNER-004). |

---

## GAP-002 — Missing Module: scan_scheduler

| Field | Value |
|---|---|
| **Gap ID** | GAP-002 |
| **Gap Type** | CODE-GAP (code references a module with no canonical spec or implementation) |
| **Domain** | Symbol Scanning Scheduler |
| **Governing Specification** | None found — no canonical spec for scan_scheduler |
| **Description** | `signal_engine.py` conditionally imports `from core.scan_scheduler import _focus_state_path`. No `scan_scheduler.py` module exists. No canonical specification for a scanning scheduler was found in any document. The FSM_DECISION_ENGINE_SPEC defines focus state management but does not define a separate scan_scheduler module. |
| **Risk** | HIGH — Missing import is wrapped in try/except, suppressing the error, but the missing `path` variable causes silent failure in symbol replacement score update |
| **Evidence** | `signal_engine.py` function `update_symbol_replacement_score` imports from `core.scan_scheduler`. No file found. No spec reference found. |
| **Recommended Action** | Either implement scan_scheduler.py and add a canonical spec reference, or refactor signal_engine.py to derive the state path from fsm_runtime directly. |

---

## GAP-003 — Missing Implementation: Test Suite

| Field | Value |
|---|---|
| **Gap ID** | GAP-003 |
| **Gap Type** | SPEC-GAP |
| **Domain** | Testing and Validation |
| **Governing Specification** | `send/docs/canonical/active/TEST_PLAN_v2.0.0.md` (CAM-036) |
| **Description** | TEST_PLAN_v2.0.0 is an active canonical document defining the system validation plan. No test files were found anywhere in the repository (no `tests/`, `test_*.py`, or `*_test.py` files). The `send/validation/statistical_proof.py` implements statistical proof logic but is not a test file in the conventional sense. |
| **Risk** | HIGH — Without automated tests, regressions cannot be detected. Canonical invariants (SYSTEM_INVARIANTS_v2.0.0.md) cannot be verified programmatically. |
| **Evidence** | `find send -name "test_*.py" -o -name "*_test.py"` returns no results. TEST_PLAN_v2.0.0.md is active canonical. |
| **Recommended Action** | Implement test suite per TEST_PLAN_v2.0.0.md. Owner prioritization required. |

---

## GAP-004 — SPEC-GAP: DecisionObject Contract Not Fully Enforced in Code

| Field | Value |
|---|---|
| **Gap ID** | GAP-004 |
| **Gap Type** | SPEC-GAP |
| **Domain** | DecisionObject Contract |
| **Governing Specification** | `send/docs/canonical/active/DECISION_OBJECT_CANONICAL_SPEC_v1.0.0.md` (CAM-005) |
| **Description** | The DECISION_OBJECT_CANONICAL_SPEC defines a formal contract for the DecisionObject. `fsm_runtime.py` consumes `decision.get("symbol")`, `decision.get("kind")`, `decision.get("signal_id")`, `decision.get("candle_ts")`. `strategy_v2.py` produces decision dictionaries, but the exact field set and validation against the canonical contract was not fully verified in this audit. The spec defines additional required fields and constraints that may not be enforced in code. |
| **Risk** | MEDIUM — If strategy_v2.py omits required DecisionObject fields, fsm_runtime.py silently uses None values, causing incorrect FSM transitions. |
| **Evidence** | fsm_runtime.py consumes 4 fields via `.get()` with no validation. DECISION_OBJECT_CANONICAL_SPEC declares a full contract with required fields, types, and invariants. Full contract comparison was not performed (code inspection limitation). |
| **Recommended Action** | Perform line-by-line comparison of DecisionObject fields produced by strategy_v2.py against DECISION_OBJECT_CANONICAL_SPEC. Add validation in fsm_runtime.py. |

---

## GAP-005 — SPEC-GAP: Event Schema JSON File Incomplete

| Field | Value |
|---|---|
| **Gap ID** | GAP-005 |
| **Gap Type** | SCHEMA-GAP |
| **Domain** | Event Schema |
| **Governing Specification** | `send/docs/canonical/active/EVENT_SCHEMA_SPEC_v2.0.0.md` (CAM-016) |
| **Description** | `send/schema/event_schema.json` defines only 4 event types: `system_boot`, `engine_start`, `tier_reset`, `error`. The EVENT_SCHEMA_SPEC_v2.0.0 defines a comprehensive event schema covering all system events across strategy, FSM, distribution, and admin layers. The JSON schema file is severely incomplete relative to the canonical spec. |
| **Risk** | MEDIUM — Schema validation tooling (if implemented) would accept invalid events or reject valid events. Event producers may not log required fields. |
| **Evidence** | `event_schema.json` contains 4 event types. EVENT_SCHEMA_SPEC_v2.0.0 is a full active canonical spec covering many more event types. |
| **Recommended Action** | Expand `send/schema/event_schema.json` to cover all event types defined in EVENT_SCHEMA_SPEC_v2.0.0.md. |

---

## GAP-006 — SCHEMA-GAP: params_schema.json Inconsistent with Runtime

| Field | Value |
|---|---|
| **Gap ID** | GAP-006 |
| **Gap Type** | SCHEMA-GAP |
| **Domain** | Parameter Schema |
| **Governing Specification** | `send/docs/canonical/active/STRATEGY_PARAMETER_CONTROL_SPEC_v2.0.0.md` (CAM-032) |
| **Description** | `send/schema/params_schema.json` defines keys (`strategy_v2`, `buffer_multipliers`, `expiry_limits_minutes`, `score_thresholds`) that do not match `send/config/algo_params.json` actual keys (`thresholds`, `weights`, `expiry`, `buffer`, `gates`) or the validation in `send/core/params_loader.py`. The schema file is inconsistent with the runtime system. (See also CON-005.) |
| **Risk** | HIGH — Misleading schema file; any validation tool using this schema will fail against the real config |
| **Evidence** | params_schema.json keys vs algo_params.json keys — confirmed mismatch via direct inspection. |
| **Recommended Action** | Align params_schema.json with params_loader.py REQUIRED_TOP_LEVEL_KEYS and REQUIRED_NESTED_KEYS. |

---

## GAP-007 — DOMAIN-GAP: No Canonical Security Specification

| Field | Value |
|---|---|
| **Gap ID** | GAP-007 |
| **Gap Type** | DOMAIN-GAP |
| **Domain** | Security |
| **Governing Specification** | `send/docs/SECURITY_MODEL.md` (root-level, not in active canonical set) |
| **Description** | `send/docs/SECURITY_MODEL.md` exists at the root docs level but has not been promoted to the active canonical set. No file in `send/docs/canonical/active/` covers security policies, threat model, or access security rules. The ROLE_AND_PERMISSION_MATRIX_SPEC_v2.0.0 covers access control but not the broader security model. |
| **Risk** | MEDIUM — Security requirements may not be consistently applied across implementation. |
| **Evidence** | `find send/docs/canonical/active -name "*SECURITY*"` returns nothing. SECURITY_MODEL.md exists in root docs. |
| **Recommended Action** | Evaluate SECURITY_MODEL.md for promotion to active canonical set or merge relevant rules into SYSTEM_INVARIANTS_v2.0.0 or GOVERNANCE_AND_CHANGE_CONTROL_v2.0.0. Owner decision required. |

---

## GAP-008 — DOMAIN-GAP: No Canonical Risk Specification

| Field | Value |
|---|---|
| **Gap ID** | GAP-008 |
| **Gap Type** | DOMAIN-GAP |
| **Domain** | Risk Management |
| **Governing Specification** | `send/docs/RISK_MODEL.md` (root-level, not in active canonical set) |
| **Description** | `send/docs/RISK_MODEL.md` exists but has not been promoted to the active canonical set. No document in `send/docs/canonical/active/` governs risk management rules, risk limits, or risk parameters. |
| **Risk** | MEDIUM — Risk management rules may not be consistently implemented. |
| **Evidence** | `find send/docs/canonical/active -name "*RISK*"` returns nothing. RISK_MODEL.md exists in root docs. Multiple deprecated docs referenced RISK_MODEL.md. |
| **Recommended Action** | Evaluate RISK_MODEL.md for promotion to active canonical set. Owner decision required. |

---

## GAP-009 — DOMAIN-GAP: No Canonical Data Retention Specification

| Field | Value |
|---|---|
| **Gap ID** | GAP-009 |
| **Gap Type** | DOMAIN-GAP |
| **Domain** | Data Retention |
| **Governing Specification** | `send/docs/DATA_RETENTION_POLICY.md` (root-level, status not declared) |
| **Description** | A data retention policy document exists but has no canonical status and is not in the active canonical set. No active canonical document governs data retention rules for telemetry, events, or state files. |
| **Risk** | LOW — No immediate runtime risk but creates compliance and operational ambiguity. |
| **Evidence** | DATA_RETENTION_POLICY.md in root docs. No canonical active counterpart. |
| **Recommended Action** | Declare DATA_RETENTION_POLICY.md canonical status and promote if appropriate. |

---

## GAP-010 — DOMAIN-GAP: Community Feedback and Privacy — No Active Canonical Resolution

| Field | Value |
|---|---|
| **Gap ID** | GAP-010 |
| **Gap Type** | DOMAIN-GAP |
| **Domain** | Community Feedback and Privacy |
| **Governing Specification** | `send/docs/intake/COMMUNITY_FEEDBACK_AND_PRIVACY_SPEC.md` (evaluated as PROMOTE_OR_MAJOR_MERGE by CANON_BATCH_EVALUATION) |
| **Description** | CANON_BATCH_EVALUATION_v2.0.0 identified COMMUNITY_FEEDBACK_AND_PRIVACY_SPEC.md as the strongest promote candidate because it defines a distinct canonical concern (privacy, feedback visibility, pseudonymous references, community-facing analytics). The decision to promote or major-merge has not been executed. There is no active canonical document governing this domain. There are also older deprecated docs: `send/docs/_deprecated/ELITE_FEEDBACK_SPEC.md`, `ELITE_MEMBER_FEEDBACK_AND_LEADERBOARD_SPEC.md`, `MEMBER_FEEDBACK_SPEC.md`, `PRIVACY_AND_MEMBER_STATS_ACCESS_SPEC.md` — all of which address overlapping topics. |
| **Risk** | MEDIUM — Community feedback and privacy rules are not canonically governed. |
| **Evidence** | CANON_BATCH_EVALUATION_v2.0.0.md verdict: PROMOTE_OR_MAJOR_MERGE. Deprecated feedback/privacy docs in `send/docs/_deprecated/`. No active canonical coverage. |
| **Recommended Action** | Owner decision required on promote vs. major-merge path (see OWNER-001). |

---

## GAP-011 — SPEC-GAP: Adaptive Activity Gate Not Merged into Active Canon

| Field | Value |
|---|---|
| **Gap ID** | GAP-011 |
| **Gap Type** | SPEC-GAP |
| **Domain** | Strategy Activity Gate |
| **Governing Specification** | `send/docs/intake/ADAPTIVE_ACTIVITY_GATE_SPEC.md` (evaluated as MERGE_INTO_ACTIVE by CANON_BATCH_EVALUATION) |
| **Description** | ADAPTIVE_ACTIVITY_GATE_SPEC.md proposes replacing the static `MIN_AVG_RANGE` filter with a volatility-normalized activity detection mechanism. CANON_BATCH_EVALUATION evaluated this as MERGE_INTO_ACTIVE (target: ALGO_SPEC, DECISION_AUDIT_SPEC, TRADE_TEMPORAL_TELEMETRY_SPEC). The merge has not been executed. The strategy currently implements a static `min_avg_range` gate (see params_schema.json: `strategy_v2.min_avg_range`). |
| **Risk** | MEDIUM — The static gate may underperform in certain market conditions per the proposed spec. |
| **Evidence** | params_schema.json: `min_avg_range`. ADAPTIVE_ACTIVITY_GATE_SPEC.md proposes dynamic replacement. CANON_BATCH_EVALUATION verdict: MERGE_INTO_ACTIVE. |
| **Recommended Action** | Owner to approve merge of ADAPTIVE_ACTIVITY_GATE_SPEC content into ALGO_SPEC and related active docs before implementation. |

---

## GAP-012 — CODE-GAP: Intelligence Modules Without Clear Canonical Governance

| Field | Value |
|---|---|
| **Gap ID** | GAP-012 |
| **Gap Type** | CODE-GAP |
| **Domain** | Intelligence Layer |
| **Governing Specification** | `send/docs/canonical/active/STRATEGY_INTELLIGENCE_SYSTEM_v2.0.0.md` (CAM-027) and related intelligence docs |
| **Description** | The `send/intelligence/` module contains 9 Python files: `adaptive_params.py`, `bottleneck_detector.py`, `heatmap.py`, `report_loader.py`, `research_engine.py`, `risk_monitor.py`, `signal_diagnostics.py`, `strategy_optimizer.py`, `symbol_health.py`. While STRATEGY_INTELLIGENCE_SYSTEM_v2.0.0 is the governing canonical spec, the specific function-level contracts for each intelligence module are not individually specified. The relationship between intake docs (AI_STRATEGY_AUDITOR_SPEC, INTELLIGENCE_FILES_AND_MODULE_MAP) and these modules is pending merge decisions. |
| **Risk** | MEDIUM — Intelligence modules may diverge from intended behavior without granular specs. |
| **Evidence** | Intelligence module files confirmed present. CANON_BATCH_EVALUATION recommends merging INTELLIGENCE_FILES_AND_MODULE_MAP and AI_STRATEGY_AUDITOR_SPEC content into active docs. |
| **Recommended Action** | Execute CANON_BATCH_EVALUATION merge recommendations. |

---

## GAP-013 — REF-GAP: Broken Cross-References to Superseded Document Names

| Field | Value |
|---|---|
| **Gap ID** | GAP-013 |
| **Gap Type** | REF-GAP |
| **Domain** | Cross-Reference Integrity |
| **Description** | Multiple documents contain cross-references to document names that have been superseded or renamed. Specifically: (1) `CANONICAL_REFACTOR_PLAN_v1.0.0.md` references `SIGNAL_ENGINE_EXECUTION_SPEC_v1.0.0.md` (now v2.0.0) and `SIGNAL_TIME_MODEL_SPEC_v2.0.0.md` (now in superseded/). (2) `DOCUMENT_LAYER_INDEX.md` references `PARAMS_REFERENCE.md` (superseded by STRATEGY_PARAMETER_CONTROL_SPEC_v2.0.0.md). (3) `params_loader.py` comment references `PARAMS_REFERENCE.md`. (4) `FORMAL_SPEC.md` references `PARAMS_REFERENCE.md`. |
| **Risk** | LOW — Navigation hazard only |
| **Evidence** | Direct document inspection confirmed in CON-008. |
| **Recommended Action** | Update all broken references during documentation reconciliation phase. |

---

## GAP-014 — INTERFACE-GAP: No Formal API Definition for Admin Telegram Commands

| Field | Value |
|---|---|
| **Gap ID** | GAP-014 |
| **Gap Type** | INTERFACE-GAP |
| **Domain** | Admin Command Interface |
| **Governing Specification** | `send/docs/ADMIN_CALLBACK_MAP.md` (supporting only, references missing module) |
| **Description** | `send/docs/ADMIN_CALLBACK_MAP.md` attempts to define the mapping of Telegram admin callbacks, but it references `callback_router.py` which does not exist. `send/core/admin_commands.py` implements command handling logic, but there is no formal, version-controlled interface definition for the admin command API (command names, parameters, permissions, responses). |
| **Risk** | MEDIUM — Admin command interface changes cannot be validated against a canonical contract. |
| **Evidence** | ADMIN_CALLBACK_MAP.md references callback_router.py (missing). admin_commands.py exists with command implementations but no formal interface spec. |
| **Recommended Action** | Define a formal admin command interface spec or update ADMIN_CALLBACK_MAP.md to reference actual implementation. |

---

## GAP-015 — DOMAIN-GAP: State Persistence Not in Active Canonical Set

| Field | Value |
|---|---|
| **Gap ID** | GAP-015 |
| **Gap Type** | DOMAIN-GAP |
| **Domain** | State Persistence |
| **Governing Specification** | `send/docs/STATE_PERSISTENCE_SPEC.md` (root-level, not in active canonical set) |
| **Description** | `STATE_PERSISTENCE_SPEC.md` exists in the root docs but has not been promoted to the active canonical set. `send/core/storage.py` implements atomic JSON persistence, but the canonical spec governing persistence rules, file paths, locking strategy, and recovery from corruption is not in the active canonical folder. |
| **Risk** | MEDIUM — Persistence rules may be inconsistently applied as the system grows. |
| **Evidence** | STATE_PERSISTENCE_SPEC.md in root docs. send/core/storage.py implements the domain. No active canonical doc found for this domain. |
| **Recommended Action** | Evaluate STATE_PERSISTENCE_SPEC.md for promotion to active canonical set. |

---

## GAP-016 — DOMAIN-GAP: Monitoring and Alerting Not in Active Canonical Set

| Field | Value |
|---|---|
| **Gap ID** | GAP-016 |
| **Gap Type** | DOMAIN-GAP |
| **Domain** | Monitoring and Alerting |
| **Governing Specification** | `send/docs/MONITORING_ALERTS_SPEC.md` (root-level, not in active canonical set) |
| **Description** | `MONITORING_ALERTS_SPEC.md` exists in root docs but is not in the active canonical set. `send/monitoring/health_check.py` and `send/monitoring/restart_guard.py` implement monitoring. The canonical specification for alert thresholds, monitoring intervals, and escalation paths is not active-canonical. |
| **Risk** | LOW — Monitoring configuration may not align with intended specification. |
| **Evidence** | MONITORING_ALERTS_SPEC.md present in root docs. Monitoring files present in send/monitoring/. |
| **Recommended Action** | Evaluate MONITORING_ALERTS_SPEC.md for promotion or reference in active canonical system architecture docs. |

---

## GAP-017 — CODE-GAP: Legacy Module in Production Path

| Field | Value |
|---|---|
| **Gap ID** | GAP-017 |
| **Gap Type** | CODE-GAP |
| **Domain** | Code Hygiene |
| **Description** | `send/legacy/bot_control.py` exists in the `send/legacy/` directory. The MODULE_INTERFACE_SPEC_v2.0.0 governs module interfaces, but there is no specification for what `legacy/` modules are permitted to do. The presence of `send/legacy/bot_control.py` in the active codebase (not in `_archive/`) may represent technical debt or a module that should be retired. |
| **Risk** | LOW — Legacy module is in a clearly named directory, reducing confusion risk. |
| **Evidence** | send/legacy/bot_control.py exists. No canonical spec references the `legacy/` module path. |
| **Recommended Action** | Clarify whether `send/legacy/bot_control.py` is still needed or should be archived. |

---

## GAP-018 — SCHEMA-GAP: Inconsistent Role/Permission Configuration Files

| Field | Value |
|---|---|
| **Gap ID** | GAP-018 |
| **Gap Type** | SCHEMA-GAP |
| **Domain** | Role and Permission Schema |
| **Governing Specification** | `send/docs/canonical/active/ROLE_AND_PERMISSION_MATRIX_SPEC_v2.0.0.md` (CAM-015) |
| **Description** | Two configuration files exist for roles and permissions: `send/config/admin_roles.json` and `send/config/admin_permissions.json`. `admin_permissions.py` references `ROLES_CONFIG_PATH`. The canonical spec governs role definitions and permission matrices, but the split between two config files and the canonical schema for each was not verified in this audit. The relationship between `admin_roles.json` and `admin_permissions.json` may create ambiguity. |
| **Risk** | MEDIUM — Role/permission configuration split may cause inconsistent access control if one file is updated without the other. |
| **Evidence** | send/config/admin_roles.json and send/config/admin_permissions.json both exist. admin_permissions.py: `ROLES_CONFIG_PATH` (path not yet confirmed against both files). |
| **Recommended Action** | Verify that admin_roles.json and admin_permissions.json are both governed by ROLE_AND_PERMISSION_MATRIX_SPEC_v2.0.0.md and that the canonical spec defines the expected schema for each file. |

---

*End of CANONICAL_GAP_ANALYSIS.md*
