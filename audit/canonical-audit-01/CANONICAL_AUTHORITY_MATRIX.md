# CANONICAL_AUTHORITY_MATRIX.md

**Audit ID:** canonical-audit-01  
**Date:** 2026-07-12  
**Scope:** Full repository — send/docs/canonical/, send/docs/, send/docs/_deprecated/, send/docs/intake/, send/docs/proposed_intake/, send/core/, send/runtime/, send/intelligence/, send/config/, send/schema/  
**Auditor:** Canonical Audit Agent  

---

## Notes on Evidence Basis

- All version and status declarations are taken directly from file headers (first 30 lines).
- Implementation alignment is assessed by direct code inspection of send/core/, send/runtime/, send/intelligence/.
- Path references in documents point to `/opt/binarybot/…`; actual repository paths are under `send/`.
- Confidence levels: **HIGH** (explicit declaration + corroboration), **MEDIUM** (explicit declaration, limited corroboration), **LOW** (inferred, no explicit declaration or conflicting signals).

---

## SECTION 1 — Active Canonical Documents (send/docs/canonical/active/)

### CAM-001

| Field | Value |
|---|---|
| **Functional Domain** | Root Strategy Manifest / Document Authority Order |
| **Current Path** | `send/docs/canonical/active/CANONICAL_STRATEGY_STACK_v1.0.0.md` |
| **Title** | CANONICAL_STRATEGY_STACK_v1.0.0 |
| **Version** | 1.0.0 |
| **Declared Status** | Canonical Root Manifest |
| **Apparent Authority** | Root authority over the canonical document set and strategy stack ordering |
| **Overlapping / Conflicting Documents** | `send/docs/MASTER_DOCUMENT_INDEX.md`, `send/docs/BINARYBOT_MASTER_INDEX.md` (both claim to index the full doc set; neither explicitly defers to this manifest) |
| **Implementation References** | No direct code reference; governs document precedence only |
| **Proposed Classification** | **Authoritative** |
| **Confidence** | HIGH |
| **Evidence** | Explicitly declares itself the "root strategy stack manifest" with authority ordering. Referenced by ALGO_SPEC_v2.0.0.md and all other core active specs. v1.0.0 version is intentional — no v2 exists. |

---

### CAM-002

| Field | Value |
|---|---|
| **Functional Domain** | Strategy / Trading Logic — Signal Generation Algorithm |
| **Current Path** | `send/docs/canonical/active/ALGO_SPEC_v2.0.0.md` |
| **Title** | ALGO_SPEC_v2.0.0 |
| **Version** | 2.0.0 |
| **Declared Status** | Canonical Active Strategy Specification |
| **Apparent Authority** | Primary authority for strategy gates, scoring semantics, DecisionObject production contract |
| **Overlapping / Conflicting Documents** | `send/docs/_deprecated/ALGO_SPEC.pre_time_model_20260313_144002.md` (deprecated predecessor); `send/docs/_deprecated/legacy_strategy_duplicates/ALGO_SPEC.md` (deprecated duplicate); `send/docs/intake/ADAPTIVE_ACTIVITY_GATE_SPEC.md` (proposes rule addition not yet merged) |
| **Implementation References** | `send/core/strategy_v2.py` (file header cites ALGO_SPEC.md); `send/core/signal_engine.py` |
| **Proposed Classification** | **Authoritative** |
| **Confidence** | HIGH |
| **Evidence** | strategy_v2.py header: "Implements ALGO_SPEC.md (gates + scoring + buffer + expiry)". v2.0.0 supersedes pre_time_model version. Active doc declares clear scope. |

---

### CAM-003

| Field | Value |
|---|---|
| **Functional Domain** | Strategy / Trading Logic — Temporal Model |
| **Current Path** | `send/docs/canonical/active/TIME_MODEL_UNIFIED_CANON_v2.0.0.md` |
| **Title** | TIME_MODEL_UNIFIED_CANON_v2.0.0 |
| **Version** | 2.0.0 |
| **Declared Status** | Canonical Unified |
| **Apparent Authority** | Unified authority for strategy time model, execution time semantics, telemetry time semantics, and DecisionObject time contract |
| **Overlapping / Conflicting Documents** | `send/docs/canonical/superseded/TIME_MODEL_CANON_v1.0.0.md` (explicitly superseded); `send/docs/canonical/superseded/SIGNAL_TIME_MODEL_SPEC_v2.0.0.md` (superseded); `send/docs/canonical/superseded/signal_time_model_and_decision_object_v1.0.0.md` (superseded) |
| **Implementation References** | `send/core/strategy_v2.py`, `send/core/signal_engine.py` (time-aware logic); `send/core/trade_temporal_telemetry` (module referenced but **not present** in repository) |
| **Proposed Classification** | **Authoritative** |
| **Confidence** | HIGH |
| **Evidence** | Document explicitly lists superseded predecessors. Superseded folder contains older time model docs. Unified Canon is the merge document for three prior versions. |

---

### CAM-004

| Field | Value |
|---|---|
| **Functional Domain** | Strategy / Trading Logic — SR Corridor Detection |
| **Current Path** | `send/docs/canonical/active/SR_CORRIDOR_ENGINE_SPEC_v2.0.0.md` |
| **Title** | SR_CORRIDOR_ENGINE_SPEC_v2.0.0 |
| **Version** | 2.0.0 |
| **Declared Status** | Canonical Active Structural Specification |
| **Apparent Authority** | Canonical authority for support/resistance corridor interpretation, positioned before time model and before DecisionObject production |
| **Overlapping / Conflicting Documents** | `send/docs/_deprecated/SR_CORRIDOR_DETECTION_ENGINE_SPEC.pre_time_model_20260313_144917.md` (deprecated predecessor); `send/docs/SR_CORRIDOR_CODE_PATCH_PLAN.md` (patch plan — supporting role) |
| **Implementation References** | `send/core/strategy_v2.py` (corridor gate logic) |
| **Proposed Classification** | **Authoritative** |
| **Confidence** | HIGH |
| **Evidence** | Supersedes pre_time_model predecessor. Positioned in active canonical folder. Explicitly scopes corridor layer before time model in pipeline ordering. |

---

### CAM-005

| Field | Value |
|---|---|
| **Functional Domain** | Strategy / Contract — DecisionObject |
| **Current Path** | `send/docs/canonical/active/DECISION_OBJECT_CANONICAL_SPEC_v1.0.0.md` |
| **Title** | DECISION_OBJECT_CANONICAL_SPEC_v1.0.0 |
| **Version** | 1.0.0 |
| **Declared Status** | Canonical Active Contract Specification |
| **Apparent Authority** | Defines the DecisionObject as the official inter-layer contract between strategy stack and FSM |
| **Overlapping / Conflicting Documents** | `send/docs/DECISION_OBJECT_INTEGRATION_AUDIT.md` (audit supporting doc); `send/docs/_deprecated/_deprecated_DECISION_OBJECT_CANONICAL_SPEC_v1.0.0_pre_activation_20260314_203332.md` (deprecated pre-activation draft) |
| **Implementation References** | `send/core/strategy_v2.py` (produces decision dict); `send/core/fsm_runtime.py` (consumes `decision` dict with symbol, kind, signal_id, candle_ts fields) |
| **Proposed Classification** | **Authoritative** |
| **Confidence** | HIGH |
| **Evidence** | fsm_runtime.py consumes decision dict with fields matching the spec. Pre-activation deprecated predecessor confirms lineage. |

---

### CAM-006

| Field | Value |
|---|---|
| **Functional Domain** | Strategy / FSM — Decision Engine |
| **Current Path** | `send/docs/canonical/active/FSM_DECISION_ENGINE_SPEC_v1.0.0.md` |
| **Title** | FSM_DECISION_ENGINE_SPEC_v1.0.0 |
| **Version** | 1.0.0 |
| **Declared Status** | Canonical Active Decision Engine Specification |
| **Apparent Authority** | FSM state machine lifecycle, watchlist management, state transitions |
| **Overlapping / Conflicting Documents** | `send/docs/_deprecated/_deprecated_FSM_DECISION_ENGINE_SPEC_v1.0.0_pre_activation_20260314_203848.md` (deprecated); `send/docs/canonical/superseded/signal_time_model_and_decision_object_v1.0.0.md` (partially overlapping — contained FSM state definitions) |
| **Implementation References** | `send/core/fsm_runtime.py` (WIDE_SCAN/WATCHLIST modes, MAX_WATCHLIST=2, STATE_PATH, apply_transition) |
| **Proposed Classification** | **Authoritative** |
| **Confidence** | HIGH |
| **Evidence** | fsm_runtime.py directly implements FSM states (IDLE, WIDE_SCAN, WATCHLIST) with MAX_WATCHLIST=2 matching spec. |

---

### CAM-007

| Field | Value |
|---|---|
| **Functional Domain** | Signal Execution — Final Emission Layer |
| **Current Path** | `send/docs/canonical/active/SIGNAL_ENGINE_EXECUTION_SPEC_v2.0.0.md` |
| **Title** | SIGNAL_ENGINE_EXECUTION_SPEC_v2.0.0 |
| **Version** | 2.0.0 |
| **Declared Status** | Canonical Active Execution Specification |
| **Apparent Authority** | Signal execution layer after FSM: emission readiness, delivery contract, separation from strategy/FSM |
| **Overlapping / Conflicting Documents** | `send/docs/_deprecated/_deprecated_SIGNAL_ENGINE_EXECUTION_SPEC_v2.0.0_pre_activation_20260314_204239.md` (deprecated); `send/docs/CANONICAL_REFACTOR_PLAN_v1.0.0.md` (references SIGNAL_ENGINE_EXECUTION_SPEC_v1.0.0.md — version mismatch) |
| **Implementation References** | `send/core/signal_engine.py` (run_once function, signal emission logic) |
| **Proposed Classification** | **Authoritative** |
| **Confidence** | HIGH |
| **Evidence** | signal_engine.py is the direct implementation. Pre-activation deprecated predecessor confirms lineage. |

---

### CAM-008

| Field | Value |
|---|---|
| **Functional Domain** | Observability — Strategy and Pipeline Traceability |
| **Current Path** | `send/docs/canonical/active/OBSERVABILITY_SPEC_v2.0.0.md` |
| **Title** | OBSERVABILITY_SPEC_v2.0.0 |
| **Version** | 2.0.0 |
| **Declared Status** | Canonical Active Observability Specification |
| **Apparent Authority** | End-to-end observability across strategy, DecisionObject, FSM, signal execution; auditability and rejection analytics |
| **Overlapping / Conflicting Documents** | `send/docs/canonical/active/OBSERVABILITY_LOGGING_SPEC_v2.0.0.md` (significant domain overlap — both cover observability; scope boundary unclear); `send/docs/_deprecated/_deprecated_OBSERVABILITY_SPEC_v2.0.0_pre_activation_20260314_204716.md` (deprecated predecessor) |
| **Implementation References** | `send/core/observability_logger.py` |
| **Proposed Classification** | **Authoritative** (with unresolved overlap with CAM-009) |
| **Confidence** | MEDIUM |
| **Evidence** | observability_logger.py implements logging. However, OBSERVABILITY_SPEC and OBSERVABILITY_LOGGING_SPEC both claim the observability domain with no explicit deference statement between them. Owner resolution needed. |

---

### CAM-009

| Field | Value |
|---|---|
| **Functional Domain** | Observability — Telemetry, Logging, Auditability |
| **Current Path** | `send/docs/canonical/active/OBSERVABILITY_LOGGING_SPEC_v2.0.0.md` |
| **Title** | OBSERVABILITY_LOGGING_SPEC_v2.0.0 |
| **Version** | 2.0.0 |
| **Declared Status** | CANONICAL |
| **Apparent Authority** | Canonical observability layer: telemetry, logging, auditability |
| **Overlapping / Conflicting Documents** | `send/docs/canonical/active/OBSERVABILITY_SPEC_v2.0.0.md` (significant domain overlap — see CON-001) |
| **Implementation References** | `send/core/observability_logger.py` |
| **Proposed Classification** | **Authoritative** (with unresolved overlap with CAM-008) |
| **Confidence** | MEDIUM |
| **Evidence** | Both docs cover overlapping telemetry/logging concerns. Neither explicitly supersedes the other. The OBSERVABILITY_SPEC cross-references OBSERVABILITY_LOGGING_SPEC, suggesting LOGGING_SPEC may be implementation-level and OBSERVABILITY_SPEC is system-level, but this boundary is not explicit. |

---

### CAM-010

| Field | Value |
|---|---|
| **Functional Domain** | Signal Distribution — Architecture |
| **Current Path** | `send/docs/canonical/active/SIGNAL_DISTRIBUTION_ARCHITECTURE_v2.0.0.md` |
| **Title** | SIGNAL_DISTRIBUTION_ARCHITECTURE_v2.0.0 |
| **Version** | 2.0.0 |
| **Declared Status** | Active Canonical |
| **Apparent Authority** | Signal distribution architectural model |
| **Overlapping / Conflicting Documents** | `send/docs/canonical/active/SIGNAL_DISTRIBUTION_SPEC_v2.0.0.md` (closely related; both define distribution domain); `send/docs/canonical/deprecated/signal_distribution_architecture_legacy/SIGNAL_DISTRIBUTION_ARCHITECTURE_legacy_superseded_20260315_191028.md` (explicitly deprecated) |
| **Implementation References** | `send/core/distribution_router.py` |
| **Proposed Classification** | **Authoritative** (with unresolved boundary with CAM-011) |
| **Confidence** | MEDIUM |
| **Evidence** | Legacy deprecated with explicit supersession marker. Architecture doc cross-references the Spec doc. Boundary between architecture and spec docs is not formally defined. |

---

### CAM-011

| Field | Value |
|---|---|
| **Functional Domain** | Signal Distribution — Entitlement Routing and Delivery |
| **Current Path** | `send/docs/canonical/active/SIGNAL_DISTRIBUTION_SPEC_v2.0.0.md` |
| **Title** | SIGNAL_DISTRIBUTION_SPEC_v2.0.0 |
| **Version** | 2.0.0 |
| **Declared Status** | CANONICAL |
| **Apparent Authority** | Signal distribution, entitlement routing, delivery governance |
| **Overlapping / Conflicting Documents** | `send/docs/canonical/active/SIGNAL_DISTRIBUTION_ARCHITECTURE_v2.0.0.md` (CAM-010) |
| **Implementation References** | `send/core/distribution_router.py` |
| **Proposed Classification** | **Authoritative** (with unresolved boundary with CAM-010) |
| **Confidence** | MEDIUM |
| **Evidence** | Both docs address distribution domain. SPEC focuses on entitlement/routing/delivery; ARCHITECTURE focuses on system-level topology. Overlap is material but may be intentional layering. |

---

### CAM-012

| Field | Value |
|---|---|
| **Functional Domain** | Admin Control Surface |
| **Current Path** | `send/docs/canonical/active/ADMIN_CONTROL_SPEC_v2.0.0.md` |
| **Title** | ADMIN_CONTROL_SPEC_v2.0.0 |
| **Version** | 2.0.0 |
| **Declared Status** | CANONICAL |
| **Apparent Authority** | Admin control surface specification |
| **Overlapping / Conflicting Documents** | `send/docs/canonical/deprecated/admin_ux_v2_legacy/ADMIN_UX_V2_SPEC_legacy_superseded_20260318_050000.md` (explicitly superseded by this doc); `send/docs/canonical/proposed/ADMIN_SURFACE_AND_CONTROL_PLANE_CANON_v1.0.0.md` (proposed root doc that would extend/overlay this) |
| **Implementation References** | `send/core/admin_commands.py`, `send/core/admin_permissions.py`, `send/core/admin_views.py` |
| **Proposed Classification** | **Authoritative** |
| **Confidence** | HIGH |
| **Evidence** | Legacy explicitly names this spec as superseding. Implementation files exist and match the domain. |

---

### CAM-013

| Field | Value |
|---|---|
| **Functional Domain** | Admin Operations |
| **Current Path** | `send/docs/canonical/active/ADMIN_OPERATIONS_SPEC_v2.0.0.md` |
| **Title** | ADMIN_OPERATIONS_SPEC_v2.0.0 |
| **Version** | 2.0.0 |
| **Declared Status** | CANONICAL |
| **Apparent Authority** | Admin operational procedures |
| **Overlapping / Conflicting Documents** | `send/docs/canonical/deprecated/admin_ux_v2_legacy/ADMIN_UX_V2_SPEC_legacy_superseded_20260318_050000.md` (deprecated, superseded by this + ADMIN_CONTROL_SPEC) |
| **Implementation References** | `send/core/admin_commands.py` |
| **Proposed Classification** | **Authoritative** |
| **Confidence** | HIGH |
| **Evidence** | Deprecated predecessor explicitly names both ADMIN_CONTROL_SPEC and ADMIN_OPERATIONS_SPEC as successors. |

---

### CAM-014

| Field | Value |
|---|---|
| **Functional Domain** | Admin Hierarchy / Tree Map |
| **Current Path** | `send/docs/canonical/active/ADMIN_TREE_MAP_v2.0.0.md` |
| **Title** | ADMIN_TREE_MAP_v2.0.0 |
| **Version** | 2.0.0 |
| **Declared Status** | CANONICAL |
| **Apparent Authority** | Admin tree structure and hierarchy |
| **Overlapping / Conflicting Documents** | `send/docs/_deprecated/legacy_strategy_duplicates/ADMIN_TREE_MAP.md` (deprecated duplicate) |
| **Implementation References** | Indirect — admin_commands.py role routing |
| **Proposed Classification** | **Authoritative** |
| **Confidence** | HIGH |
| **Evidence** | Deprecated duplicate in legacy_strategy_duplicates. Active v2.0.0 is the current version. |

---

### CAM-015

| Field | Value |
|---|---|
| **Functional Domain** | Roles and Permissions |
| **Current Path** | `send/docs/canonical/active/ROLE_AND_PERMISSION_MATRIX_SPEC_v2.0.0.md` |
| **Title** | ROLE_AND_PERMISSION_MATRIX_SPEC_v2.0.0 |
| **Version** | 2.0.0 |
| **Declared Status** | CANONICAL |
| **Apparent Authority** | Role definitions, permission matrix, access governance |
| **Overlapping / Conflicting Documents** | `send/docs/_deprecated/legacy_strategy_duplicates/ROLE_AND_PERMISSION_MATRIX_SPEC.md` (deprecated duplicate) |
| **Implementation References** | `send/core/admin_permissions.py` (load_roles_config, has_permission, get_primary_role) |
| **Proposed Classification** | **Authoritative** |
| **Confidence** | HIGH |
| **Evidence** | admin_permissions.py directly implements role/permission loading. Deprecated duplicate exists in legacy folder. |

---

### CAM-016

| Field | Value |
|---|---|
| **Functional Domain** | Event Schema |
| **Current Path** | `send/docs/canonical/active/EVENT_SCHEMA_SPEC_v2.0.0.md` |
| **Title** | EVENT_SCHEMA_SPEC_v2.0.0 |
| **Version** | 2.0.0 |
| **Declared Status** | CANONICAL |
| **Apparent Authority** | Canonical event schema for all system events |
| **Overlapping / Conflicting Documents** | `send/docs/_deprecated/EVENT_SCHEMA_SPEC_v1.0.0.md` (deprecated v1.0.0); `send/schema/event_schema.json` (JSON schema file — covers only 4 event types, much narrower than canonical spec) |
| **Implementation References** | `send/schema/event_schema.json`, `send/core/observability_logger.py` |
| **Proposed Classification** | **Authoritative** |
| **Confidence** | HIGH |
| **Evidence** | v1.0.0 predecessor in deprecated folder. event_schema.json partial implementation (4 types defined). |

---

### CAM-017

| Field | Value |
|---|---|
| **Functional Domain** | Channel Configuration |
| **Current Path** | `send/docs/canonical/active/CHANNEL_CONFIG_SPEC_v2.0.0.md` |
| **Title** | CHANNEL_CONFIG_SPEC_v2.0.0 |
| **Version** | 2.0.0 |
| **Declared Status** | CANONICAL |
| **Apparent Authority** | Telegram channel configuration and tier rules |
| **Overlapping / Conflicting Documents** | `send/docs/_deprecated/legacy_strategy_duplicates/CHANNEL_CONFIG_SPEC.md` (deprecated duplicate) |
| **Implementation References** | `send/config/channel_config.json`, `send/core/distribution_router.py` |
| **Proposed Classification** | **Authoritative** |
| **Confidence** | HIGH |
| **Evidence** | channel_config.json exists as the runtime configuration file. Deprecated duplicate in legacy folder. |

---

### CAM-018

| Field | Value |
|---|---|
| **Functional Domain** | Telegram UX |
| **Current Path** | `send/docs/canonical/active/TELEGRAM_UX_v2.0.0.md` |
| **Title** | TELEGRAM_UX_v2.0.0 |
| **Version** | 2.0.0 |
| **Declared Status** | CANONICAL |
| **Apparent Authority** | Telegram user experience specification |
| **Overlapping / Conflicting Documents** | `send/docs/_deprecated/legacy_strategy_duplicates/TELEGRAM_UX.md` (deprecated duplicate) |
| **Implementation References** | `send/core/telegram_publisher.py`, `send/runtime/telegram_updates.py` |
| **Proposed Classification** | **Authoritative** |
| **Confidence** | HIGH |
| **Evidence** | Implementation files exist. Deprecated duplicate confirms lineage. |

---

### CAM-019

| Field | Value |
|---|---|
| **Functional Domain** | System Invariants |
| **Current Path** | `send/docs/canonical/active/SYSTEM_INVARIANTS_v2.0.0.md` |
| **Title** | SYSTEM_INVARIANTS_v2.0.0 |
| **Version** | 2.0.0 |
| **Declared Status** | CANONICAL |
| **Apparent Authority** | Non-negotiable system invariants governing all layers |
| **Overlapping / Conflicting Documents** | `send/core/fsm_runtime.py` enforce_invariants() function (implements partial invariants); no deprecated predecessor found in active path |
| **Implementation References** | `send/core/fsm_runtime.py` (enforce_invariants), `send/core/params_loader.py` (param validation) |
| **Proposed Classification** | **Authoritative** |
| **Confidence** | HIGH |
| **Evidence** | fsm_runtime.py has explicit invariant enforcement (MAX_WATCHLIST overflow check). params_loader validates required keys. |

---

### CAM-020

| Field | Value |
|---|---|
| **Functional Domain** | Module Interface Contract |
| **Current Path** | `send/docs/canonical/active/MODULE_INTERFACE_SPEC_v2.0.0.md` |
| **Title** | MODULE_INTERFACE_SPEC_v2.0.0 |
| **Version** | 2.0.0 |
| **Declared Status** | Active Canonical |
| **Apparent Authority** | Module boundary contracts and interface definitions |
| **Overlapping / Conflicting Documents** | `send/docs/canonical/deprecated/module_interface_legacy/MODULE_INTERFACE_SPEC_legacy_superseded_20260315_165429.md` (explicitly deprecated) |
| **Implementation References** | `send/core/storage.py`, `send/core/candle_adapter.py`, `send/core/params_loader.py`, `send/core/strategy_v2.py`, `send/core/fsm_runtime.py` (listed in doc header) |
| **Proposed Classification** | **Authoritative** |
| **Confidence** | HIGH |
| **Evidence** | Module references in doc header match actual files. Legacy deprecated with explicit supersession. |

---

### CAM-021

| Field | Value |
|---|---|
| **Functional Domain** | Decision Audit |
| **Current Path** | `send/docs/canonical/active/DECISION_AUDIT_SPEC_v2.0.0.md` |
| **Title** | DECISION_AUDIT_SPEC_v2.0.0 |
| **Version** | 2.0.0 |
| **Declared Status** | Active Canonical |
| **Apparent Authority** | Decision audit layer — structured recording of decision evidence |
| **Overlapping / Conflicting Documents** | `send/docs/DECISION_OBJECT_INTEGRATION_AUDIT.md` (satellite audit document) |
| **Implementation References** | `send/core/observability_logger.py` (audit event logging); `send/core/admin_commands.py` (ADMIN_PROOFS_PATH for admin events) |
| **Proposed Classification** | **Authoritative** |
| **Confidence** | HIGH |
| **Evidence** | ADMIN_PROOFS_PATH (/opt/binarybot/observability/admin_proofs.jsonl) in admin_commands.py aligns with audit logging concept. |

---

### CAM-022

| Field | Value |
|---|---|
| **Functional Domain** | Failure Recovery |
| **Current Path** | `send/docs/canonical/active/FAILURE_RECOVERY_SPEC_v2.0.0.md` |
| **Title** | FAILURE_RECOVERY_SPEC_v2.0.0 |
| **Version** | 2.0.0 |
| **Declared Status** | CANONICAL |
| **Apparent Authority** | Failure recovery procedures and error handling |
| **Overlapping / Conflicting Documents** | `send/docs/_deprecated/legacy_strategy_duplicates/FAILURE_RECOVERY_SPEC.md` (deprecated) |
| **Implementation References** | `send/monitoring/restart_guard.py`, `send/runtime/engine_loop.py` (exception handling) |
| **Proposed Classification** | **Authoritative** |
| **Confidence** | HIGH |
| **Evidence** | engine_loop.py has exception handling aligned with recovery model. restart_guard.py implements monitoring. |

---

### CAM-023

| Field | Value |
|---|---|
| **Functional Domain** | Trade Temporal Telemetry |
| **Current Path** | `send/docs/canonical/active/TRADE_TEMPORAL_TELEMETRY_SPEC_v2.0.0.md` |
| **Title** | TRADE_TEMPORAL_TELEMETRY_SPEC_v2.0.0 |
| **Version** | 2.0.0 |
| **Declared Status** | Active Canonical |
| **Apparent Authority** | Trade temporal telemetry — time-stamped event recording for signals |
| **Overlapping / Conflicting Documents** | `send/docs/_deprecated/legacy_strategy_duplicates/TRADE_TEMPORAL_TELEMETRY_SPEC.md` (deprecated) |
| **Implementation References** | `send/core/trade_temporal_telemetry` — **MODULE MISSING**: referenced in signal_engine.py but no file found in repository |
| **Proposed Classification** | **Authoritative** |
| **Confidence** | MEDIUM |
| **Evidence** | signal_engine.py imports `from core import trade_temporal_telemetry` and calls `trade_temporal_telemetry.register_open_now_trade()`. The module file does not exist — critical implementation gap. |

---

### CAM-024

| Field | Value |
|---|---|
| **Functional Domain** | Outcome Tracking |
| **Current Path** | `send/docs/canonical/active/OUTCOME_TRACKING_SPEC_v2.0.0.md` |
| **Title** | OUTCOME_TRACKING_SPEC_v2.0.0 |
| **Version** | 2.0.0 |
| **Declared Status** | Active Canonical |
| **Apparent Authority** | Signal outcome recording and result tracking |
| **Overlapping / Conflicting Documents** | `send/docs/_deprecated/legacy_strategy_duplicates/OUTCOME_TRACKING_SPEC.md` (deprecated) |
| **Implementation References** | `send/core/outcome_service.py` |
| **Proposed Classification** | **Authoritative** |
| **Confidence** | HIGH |
| **Evidence** | outcome_service.py implements domain. Deprecated duplicate confirms lineage. |

---

### CAM-025

| Field | Value |
|---|---|
| **Functional Domain** | Performance Analytics |
| **Current Path** | `send/docs/canonical/active/PERFORMANCE_ANALYTICS_SPEC_v2.0.0.md` |
| **Title** | PERFORMANCE_ANALYTICS_SPEC_v2.0.0 |
| **Version** | 2.0.0 |
| **Declared Status** | Active Canonical |
| **Apparent Authority** | Performance analytics and statistical measurement |
| **Overlapping / Conflicting Documents** | `send/docs/_deprecated/legacy_strategy_duplicates/PERFORMANCE_ANALYTICS_SPEC.md` (deprecated); `send/docs/canonical/deprecated/statistical_proof_layer_legacy/STATISTICAL_PROOF_LAYER_legacy_superseded_20260318_050000.md` (deprecated, superseded by this + RESEARCH_AND_LEARNING + STRATEGY_INTELLIGENCE) |
| **Implementation References** | `send/core/analytics_engine.py`, `send/intelligence/signal_diagnostics.py` |
| **Proposed Classification** | **Authoritative** |
| **Confidence** | HIGH |
| **Evidence** | Analytics implementation files exist. STATISTICAL_PROOF_LAYER explicitly names this doc as superseding it. |

---

### CAM-026

| Field | Value |
|---|---|
| **Functional Domain** | Research and Learning Framework |
| **Current Path** | `send/docs/canonical/active/RESEARCH_AND_LEARNING_FRAMEWORK_SPEC_v2.0.0.md` |
| **Title** | RESEARCH_AND_LEARNING_FRAMEWORK_SPEC_v2.0.0 |
| **Version** | 2.0.0 |
| **Declared Status** | Active Canonical |
| **Apparent Authority** | Strategy research and learning framework |
| **Overlapping / Conflicting Documents** | `send/docs/_deprecated/legacy_strategy_duplicates/RESEARCH_AND_LEARNING_FRAMEWORK_SPEC.md` (deprecated) |
| **Implementation References** | `send/intelligence/research_engine.py`, `send/intelligence/strategy_optimizer.py` |
| **Proposed Classification** | **Authoritative** |
| **Confidence** | HIGH |
| **Evidence** | research_engine.py and strategy_optimizer.py exist. Deprecated duplicate in legacy folder. |

---

### CAM-027

| Field | Value |
|---|---|
| **Functional Domain** | Strategy Intelligence System |
| **Current Path** | `send/docs/canonical/active/STRATEGY_INTELLIGENCE_SYSTEM_v2.0.0.md` |
| **Title** | STRATEGY_INTELLIGENCE_SYSTEM_v2.0.0 |
| **Version** | 2.0.0 |
| **Declared Status** | Active Canonical |
| **Apparent Authority** | Strategy intelligence layer — adaptive behavior, bottleneck detection |
| **Overlapping / Conflicting Documents** | `send/docs/_deprecated/legacy_strategy_duplicates/STRATEGY_INTELLIGENCE_SYSTEM.md` (deprecated); `send/docs/intake/INTELLIGENCE_LAYER_ARCHITECTURE.md` (KEEP_OUTSIDE_ACTIVE per CANON_BATCH_EVALUATION); `send/docs/intake/AI_TRADING_INTELLIGENCE_ARCHITECTURE.md` (KEEP_OUTSIDE_ACTIVE per CANON_BATCH_EVALUATION) |
| **Implementation References** | `send/intelligence/bottleneck_detector.py`, `send/intelligence/heatmap.py`, `send/intelligence/symbol_health.py`, `send/intelligence/adaptive_params.py` |
| **Proposed Classification** | **Authoritative** |
| **Confidence** | HIGH |
| **Evidence** | Intelligence module files exist. CANON_BATCH_EVALUATION explicitly classifies related intake docs as satellite to this. |

---

### CAM-028

| Field | Value |
|---|---|
| **Functional Domain** | Autonomous Strategy Evolution |
| **Current Path** | `send/docs/canonical/active/AUTONOMOUS_STRATEGY_EVOLUTION_SYSTEM_v2.0.0.md` |
| **Title** | AUTONOMOUS_STRATEGY_EVOLUTION_SYSTEM_v2.0.0 |
| **Version** | 2.0.0 |
| **Declared Status** | Active Canonical |
| **Apparent Authority** | Autonomous strategy evolution and self-improvement rules |
| **Overlapping / Conflicting Documents** | `send/docs/_deprecated/legacy_strategy_duplicates/AUTONOMOUS_STRATEGY_EVOLUTION_SYSTEM.md` (deprecated) |
| **Implementation References** | `send/intelligence/strategy_optimizer.py` (partial) |
| **Proposed Classification** | **Authoritative** |
| **Confidence** | MEDIUM |
| **Evidence** | strategy_optimizer.py exists. Spec is marked active canonical. Deprecated duplicate in legacy. Full implementation alignment not inspected. |

---

### CAM-029

| Field | Value |
|---|---|
| **Functional Domain** | System Architecture Map |
| **Current Path** | `send/docs/canonical/active/SYSTEM_ARCHITECTURE_MAP_v2.0.0.md` |
| **Title** | SYSTEM_ARCHITECTURE_MAP_v2.0.0 |
| **Version** | 2.0.0 |
| **Declared Status** | Active Canonical |
| **Apparent Authority** | System-level architecture map |
| **Overlapping / Conflicting Documents** | `send/docs/canonical/deprecated/system_architecture_map_legacy/SYSTEM_ARCHITECTURE_MAP_legacy_superseded_20260315_170930.md` (explicitly deprecated) |
| **Implementation References** | Architectural overview — no direct single file |
| **Proposed Classification** | **Authoritative** |
| **Confidence** | HIGH |
| **Evidence** | Legacy deprecated with explicit supersession marker. |

---

### CAM-030

| Field | Value |
|---|---|
| **Functional Domain** | Governance and Change Control |
| **Current Path** | `send/docs/canonical/active/GOVERNANCE_AND_CHANGE_CONTROL_v2.0.0.md` |
| **Title** | GOVERNANCE_AND_CHANGE_CONTROL_v2.0.0 |
| **Version** | 2.0.0 |
| **Declared Status** | Active Canonical |
| **Apparent Authority** | Change governance, authority model |
| **Overlapping / Conflicting Documents** | `send/docs/canonical/deprecated/governance_and_change_control_legacy/GOVERNANCE_AND_CHANGE_CONTROL_legacy_superseded_20260315_172424.md` (explicitly deprecated) |
| **Implementation References** | Governance process — no direct code reference |
| **Proposed Classification** | **Authoritative** |
| **Confidence** | HIGH |
| **Evidence** | Legacy deprecated with explicit supersession marker. |

---

### CAM-031

| Field | Value |
|---|---|
| **Functional Domain** | Deployment Protocol |
| **Current Path** | `send/docs/canonical/active/DEPLOYMENT_PROTOCOL_v2.0.0.md` |
| **Title** | DEPLOYMENT_PROTOCOL_v2.0.0 |
| **Version** | 2.0.0 |
| **Declared Status** | Active Canonical |
| **Apparent Authority** | Deployment and release governance |
| **Overlapping / Conflicting Documents** | `send/docs/canonical/deprecated/deployment_protocol_legacy/DEPLOYMENT_PROTOCOL_legacy_superseded_20260315_183646.md` (explicitly deprecated) |
| **Implementation References** | `send/runtime/system_boot.py` |
| **Proposed Classification** | **Authoritative** |
| **Confidence** | HIGH |
| **Evidence** | Legacy deprecated with explicit supersession. system_boot.py implements boot sequence. |

---

### CAM-032

| Field | Value |
|---|---|
| **Functional Domain** | Strategy Parameter Control |
| **Current Path** | `send/docs/canonical/active/STRATEGY_PARAMETER_CONTROL_SPEC_v2.0.0.md` |
| **Title** | STRATEGY_PARAMETER_CONTROL_SPEC_v2.0.0 |
| **Version** | 2.0.0 |
| **Declared Status** | Active Canonical |
| **Apparent Authority** | Strategy parameter management and control rules |
| **Overlapping / Conflicting Documents** | `send/docs/canonical/deprecated/params_reference_legacy/PARAMS_REFERENCE_legacy_superseded_20260316_092136.md` (explicitly superseded by this); `send/core/params_loader.py` references `PARAMS_REFERENCE.md` (old name) in comment |
| **Implementation References** | `send/core/params_loader.py`, `send/config/algo_params.json` |
| **Proposed Classification** | **Authoritative** |
| **Confidence** | HIGH |
| **Evidence** | Legacy explicitly superseded. params_loader.py and algo_params.json exist. |

---

### CAM-033

| Field | Value |
|---|---|
| **Functional Domain** | Affiliate Signal Distribution Model |
| **Current Path** | `send/docs/canonical/active/AFFILIATE_SIGNAL_DISTRIBUTION_MODEL_v2.0.0.md` |
| **Title** | AFFILIATE_SIGNAL_DISTRIBUTION_MODEL_v2.0.0 |
| **Version** | 2.0.0 |
| **Declared Status** | Active Canonical |
| **Apparent Authority** | Affiliate access model for signal distribution |
| **Overlapping / Conflicting Documents** | `send/docs/canonical/deprecated/affiliate_signal_distribution_model_legacy/AFFILIATE_SIGNAL_DISTRIBUTION_MODEL_legacy_superseded_20260315_202514.md` (explicitly deprecated) |
| **Implementation References** | `send/core/admin_permissions.py` (get_affiliate_scope) |
| **Proposed Classification** | **Authoritative** |
| **Confidence** | HIGH |
| **Evidence** | Legacy deprecated with explicit supersession. admin_permissions.py has get_affiliate_scope. |

---

### CAM-034

| Field | Value |
|---|---|
| **Functional Domain** | Signal Economics and Monetization |
| **Current Path** | `send/docs/canonical/active/SIGNAL_ECONOMICS_AND_MONETIZATION_MODEL_v2.0.0.md` |
| **Title** | SIGNAL_ECONOMICS_AND_MONETIZATION_MODEL_v2.0.0 |
| **Version** | 2.0.0 |
| **Declared Status** | Active Canonical |
| **Apparent Authority** | Signal monetization and economics model |
| **Overlapping / Conflicting Documents** | `send/docs/canonical/deprecated/signal_economics_and_monetization_model_legacy/SIGNAL_ECONOMICS_AND_MONETIZATION_MODEL_legacy_superseded_20260315_200915.md` (explicitly deprecated) |
| **Implementation References** | No direct implementation file found |
| **Proposed Classification** | **Authoritative** |
| **Confidence** | MEDIUM |
| **Evidence** | Legacy deprecated with supersession. No direct implementation module found. |

---

### CAM-035

| Field | Value |
|---|---|
| **Functional Domain** | Control Panel Hierarchy and Intelligence |
| **Current Path** | `send/docs/canonical/active/CONTROL_PANEL_HIERARCHY_AND_INTELLIGENCE_SPEC_v2.0.0.md` |
| **Title** | CONTROL_PANEL_HIERARCHY_AND_INTELLIGENCE_SPEC_v2.0.0 |
| **Version** | 2.0.0 |
| **Declared Status** | CANONICAL |
| **Apparent Authority** | Admin control panel hierarchy and intelligence display |
| **Overlapping / Conflicting Documents** | `send/docs/_deprecated/legacy_strategy_duplicates/CONTROL_PANEL_HIERARCHY_AND_INTELLIGENCE_SPEC.md` (deprecated duplicate) |
| **Implementation References** | `send/core/admin_views.py` |
| **Proposed Classification** | **Authoritative** |
| **Confidence** | HIGH |
| **Evidence** | admin_views.py implements the admin panel view layer. Deprecated duplicate in legacy folder. |

---

### CAM-036

| Field | Value |
|---|---|
| **Functional Domain** | Test Plan |
| **Current Path** | `send/docs/canonical/active/TEST_PLAN_v2.0.0.md` |
| **Title** | TEST_PLAN_v2.0.0 |
| **Version** | 2.0.0 |
| **Declared Status** | Active Canonical |
| **Apparent Authority** | System validation and test plan |
| **Overlapping / Conflicting Documents** | `send/docs/canonical/deprecated/test_plan_legacy/TEST_PLAN_legacy_superseded_20260315_211213.md` (explicitly deprecated) |
| **Implementation References** | No test files found in repository under standard paths |
| **Proposed Classification** | **Authoritative** |
| **Confidence** | MEDIUM |
| **Evidence** | Legacy deprecated with explicit supersession. No test files found — gap between spec and implementation. |

---

### CAM-037

| Field | Value |
|---|---|
| **Functional Domain** | Governance / Batch Evaluation Record |
| **Current Path** | `send/docs/canonical/active/CANON_BATCH_EVALUATION_v2.0.0.md` |
| **Title** | CANON_BATCH_EVALUATION_v2.0.0 |
| **Version** | Not declared (no standard header) |
| **Declared Status** | Not declared as canonical spec |
| **Apparent Authority** | Governance record of canonical evaluation verdicts for intake documents |
| **Overlapping / Conflicting Documents** | None directly — it evaluates other docs |
| **Implementation References** | None |
| **Proposed Classification** | **Supporting** (governance record, not a specification) |
| **Confidence** | HIGH |
| **Evidence** | Document explicitly states it is "documentation-governance only" and "does not patch code." Misplaced in active/ folder; should be in a governance/records subfolder. |

---

## SECTION 2 — Proposed Documents

### CAM-038

| Field | Value |
|---|---|
| **Functional Domain** | Admin Control Plane — Unified Root Canon |
| **Current Path** | `send/docs/canonical/proposed/ADMIN_SURFACE_AND_CONTROL_PLANE_CANON_v1.0.0.md` |
| **Title** | ADMIN_SURFACE_AND_CONTROL_PLANE_CANON_v1.0.0 |
| **Version** | 1.0.0 |
| **Declared Status** | Proposed Canonical Root Document |
| **Apparent Authority** | Proposed: to unify admin/control-plane domains under a single root |
| **Overlapping / Conflicting Documents** | `ADMIN_CONTROL_SPEC_v2.0.0.md` (CAM-012), `ADMIN_OPERATIONS_SPEC_v2.0.0.md` (CAM-013), `ADMIN_TREE_MAP_v2.0.0.md` (CAM-014), `CONTROL_PANEL_HIERARCHY_AND_INTELLIGENCE_SPEC_v2.0.0.md` (CAM-035) |
| **Implementation References** | Proposed — no implementation alignment yet |
| **Proposed Classification** | **Proposed** |
| **Confidence** | HIGH |
| **Evidence** | Declared status is explicitly "Proposed Canonical Root Document." Has not been promoted. Owner decision required before promotion. |

---

## SECTION 3 — Superseded Documents

### CAM-039

| Field | Value |
|---|---|
| **Functional Domain** | Time Model (legacy) |
| **Current Path** | `send/docs/canonical/superseded/SIGNAL_TIME_MODEL_SPEC_v2.0.0.md` |
| **Title** | SIGNAL_TIME_MODEL_SPEC_v2.0.0 |
| **Version** | 2.0.0 |
| **Declared Status** | Canonical (but in superseded folder) |
| **Apparent Authority** | Superseded by TIME_MODEL_UNIFIED_CANON_v2.0.0.md |
| **Overlapping / Conflicting Documents** | `TIME_MODEL_UNIFIED_CANON_v2.0.0.md` (CAM-003) — supersedes this |
| **Implementation References** | Historical only |
| **Proposed Classification** | **Superseded** |
| **Confidence** | HIGH |
| **Evidence** | File is in the superseded/ folder. TIME_MODEL_UNIFIED_CANON_v2.0.0.md is the unified successor. |

---

### CAM-040

| Field | Value |
|---|---|
| **Functional Domain** | Time Model (legacy v1) |
| **Current Path** | `send/docs/canonical/superseded/TIME_MODEL_CANON_v1.0.0.md` |
| **Title** | TIME_MODEL_CANON_v1.0.0 |
| **Version** | 1.0.0 |
| **Declared Status** | Canonical (but in superseded folder) |
| **Apparent Authority** | Superseded by TIME_MODEL_UNIFIED_CANON_v2.0.0.md |
| **Overlapping / Conflicting Documents** | `TIME_MODEL_UNIFIED_CANON_v2.0.0.md` (CAM-003) |
| **Implementation References** | Historical only |
| **Proposed Classification** | **Superseded** |
| **Confidence** | HIGH |
| **Evidence** | In superseded/ folder. Transitional WAVE1 patch spec depends on this. |

---

### CAM-041

| Field | Value |
|---|---|
| **Functional Domain** | Time Model + DecisionObject (combined legacy) |
| **Current Path** | `send/docs/canonical/superseded/signal_time_model_and_decision_object_v1.0.0.md` |
| **Title** | signal_time_model_and_decision_object_v1.0.0 |
| **Version** | 1.0.0 |
| **Declared Status** | Canonical (but in superseded folder) |
| **Apparent Authority** | Superseded — combined doc split into TIME_MODEL_UNIFIED_CANON and DECISION_OBJECT_CANONICAL_SPEC |
| **Overlapping / Conflicting Documents** | `TIME_MODEL_UNIFIED_CANON_v2.0.0.md` (CAM-003), `DECISION_OBJECT_CANONICAL_SPEC_v1.0.0.md` (CAM-005) |
| **Implementation References** | Historical only |
| **Proposed Classification** | **Superseded** |
| **Confidence** | HIGH |
| **Evidence** | In superseded/ folder. Successor documents explicitly cover the split domains. |

---

## SECTION 4 — Transitional Documents

### CAM-042

| Field | Value |
|---|---|
| **Functional Domain** | Wave 1 Time Model Patch |
| **Current Path** | `send/docs/canonical/transitional/WAVE1_TIME_MODEL_PATCH_SPEC_v1.0.0.md` |
| **Title** | WAVE1_TIME_MODEL_PATCH_SPEC_v1.0.0 |
| **Version** | 1.0.0 |
| **Declared Status** | Canonical Patch Specification |
| **Apparent Authority** | Wave 1 documentation alignment patch for time model |
| **Overlapping / Conflicting Documents** | References `TIME_MODEL_CANON_v1.0.0.md` (now superseded by CAM-003) |
| **Implementation References** | Historical — documents patch applied to update docs for time model |
| **Proposed Classification** | **Transitional** (patch process complete; doc is historical record) |
| **Confidence** | MEDIUM |
| **Evidence** | Declared status is "Canonical Patch Specification". Time model unification has been completed. This patch spec's work is done. |

---

## SECTION 5 — Intake Documents (send/docs/intake/ and send/docs/proposed_intake/)

Note: CANON_BATCH_EVALUATION_v2.0.0.md (CAM-037) has evaluated all intake documents. Classifications below reflect that evaluation.

### CAM-043 through CAM-052

The 10 intake documents (and their duplicates in `proposed_intake/STEP_120A_INTAKE_STAGE_AND_REFERENCE_AUDIT_20260316_064927/`) have been evaluated in CANON_BATCH_EVALUATION_v2.0.0.md. Verdicts:

| File | Batch Verdict | Proposed Classification |
|---|---|---|
| `ADAPTIVE_ACTIVITY_GATE_SPEC.md` | MERGE_INTO_ACTIVE (into ALGO_SPEC, DECISION_AUDIT_SPEC, TRADE_TEMPORAL_TELEMETRY_SPEC) | **Proposed** (pending merge) |
| `AI_STRATEGY_AUDITOR_SPEC.md` | MERGE_INTO_ACTIVE (into RESEARCH, PERFORMANCE_ANALYTICS, STRATEGY_INTELLIGENCE) | **Proposed** (pending merge) |
| `AI_TRADE_PHYSICS_INTELLIGENCE_SPEC.md` | PROPOSED_FUTURE_STATE | **Proposed** |
| `AI_TRADE_PHYSICS_SPACE_MODEL_SPEC.md` | KEEP_OUTSIDE_ACTIVE | **Supporting** |
| `AI_TRADING_INTELLIGENCE_ARCHITECTURE.md` | KEEP_OUTSIDE_ACTIVE | **Supporting** |
| `COMMUNITY_FEEDBACK_AND_PRIVACY_SPEC.md` | PROMOTE_OR_MAJOR_MERGE | **Proposed** (pending owner decision — see OWNER-001) |
| `INTELLIGENCE_DATA_PIPELINE_DEFINITION.md` | MERGE_INTO_ACTIVE | **Proposed** (pending merge) |
| `INTELLIGENCE_FILES_AND_MODULE_MAP.md` | MERGE_INTO_ACTIVE | **Proposed** (pending merge) |
| `INTELLIGENCE_LAYER_ARCHITECTURE.md` | KEEP_OUTSIDE_ACTIVE | **Supporting** |
| `TRADE_PHYSICS_SCORE_SPEC.md` | PROPOSED_FUTURE_STATE | **Proposed** |

---

## SECTION 6 — Root-Level Documentation (send/docs/)

| File | Status | Proposed Classification | Notes |
|---|---|---|---|
| `MASTER_DOCUMENT_INDEX.md` | Declared Canonical | **Supporting** | Version 1.0.0; index only; overlaps with BINARYBOT_MASTER_INDEX.md |
| `BINARYBOT_MASTER_INDEX.md` | Declared Canonical | **Supporting** | Overlaps with MASTER_DOCUMENT_INDEX.md — duplicate index concern |
| `DOCUMENT_LAYER_INDEX.md` | Version 1.0 | **Supporting** | References old doc names (PARAMS_REFERENCE.md) not current v2 names |
| `DOCUMENT_STATUS_POLICY.md` | No version | **Supporting** | Defines ACTIVE/PARTIAL/LEGACY/ARCHIVED — does not match canonical status vocabulary in active docs |
| `FORMAL_SPEC.md` | Canonical Formal Layer | **Supporting** | Mathematical formalization; references old doc names |
| `CANONICAL_CODE_ALIGNMENT_AUDIT_v1.0.0.md` | Satellite/Non-Canonical (self-declared) | **Supporting** | Audit framework |
| `CANONICAL_CODE_ALIGNMENT_MATRIX_v1.0.0.md` | Satellite/Non-Canonical (self-declared) | **Supporting** | Code↔doc alignment matrix |
| `CANONICAL_DOC_CONFLICT_RESOLUTION_PLAN_v1.0.0.md` | Satellite/Non-Canonical (self-declared) | **Supporting** | Historical conflict resolution plan |
| `CANONICAL_DOC_REALITY_REPORT_v1.0.0.md` | Satellite/Non-Canonical (self-declared) | **Supporting** | Historical reality audit |
| `CANONICAL_REFACTOR_PLAN_v1.0.0.md` | Canonical Refactor Blueprint | **Supporting** | Refactor plan; references v1 signal spec name |
| `DOCUMENT_NORMALIZATION_AND_DEPRECATION_PLAN_v1.0.0.md` | Satellite/Non-Canonical (self-declared) | **Supporting** | Governance plan |
| `IMPLEMENTATION_STEP_PLAN_v1.0.0.md` | (not inspected in full) | **Supporting** | Step execution plan |
| `CHANGELOG.md` | — | **Supporting** | Historical record |
| `CHECKLIST.md` | — | **Supporting** | Operational checklist |
| `DATA_RETENTION_POLICY.md` | — | **Supporting** | Unverified policy |
| `DECISION_OBJECT_INTEGRATION_AUDIT.md` | — | **Supporting** | Audit record |
| `DOCUMENTATION_GAP_ANALYSIS.md` | Satellite/Non-Canonical (self-declared) | **Supporting** | Gap analysis |
| `DOCUMENT_IMPLEMENTATION_MATRIX.md` | — | **Supporting** | References non-existent files (admin_router.py, callback_router.py) |
| `MONITORING_ALERTS_SPEC.md` | — | **Unresolved** | Not cross-referenced from active docs; scope unclear |
| `RELEASE_VERSIONING_POLICY.md` | — | **Supporting** | |
| `RISK_MODEL.md` | — | **Unresolved** | No active canonical risk spec found; may be authoritative in its domain |
| `RUNBOOK.md` | — | **Supporting** | |
| `RUNTIME_EXECUTION_TIMELINE.md` | — | **Supporting** | Referenced in DOCUMENT_LAYER_INDEX |
| `SECURITY_MODEL.md` | — | **Unresolved** | No active canonical security spec found; may be authoritative |
| `SIGNAL_DEBUG_DASHBOARD_SPEC.md` | — | **Unresolved** | Not in active canonical set |
| `SR_CORRIDOR_CODE_PATCH_PLAN.md` | — | **Supporting** | Patch plan for corridor code |
| `STATE_PERSISTENCE_SPEC.md` | — | **Unresolved** | Not in active canonical set; relates to storage |
| `WEIGHTED_TRUE_MOVEMENT_ACTIVITY_MODEL.md` | — | **Unresolved** | Not evaluated by CANON_BATCH_EVALUATION |
| `ADMIN_CALLBACK_MAP.md` | — | **Supporting** | References non-existent callback_router.py |

---

## SECTION 7 — Legacy/Deprecated Documents (send/docs/_deprecated/)

All documents in `send/docs/_deprecated/` are classified as **Deprecated** or **Superseded**. They are preserved as historical record and must not be used as active truth. See CANONICAL_CONFLICT_REGISTER.md for specific conflicts involving these documents.

---

*End of CANONICAL_AUTHORITY_MATRIX.md*
