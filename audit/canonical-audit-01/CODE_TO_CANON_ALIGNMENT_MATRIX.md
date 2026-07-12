# CODE_TO_CANON_ALIGNMENT_MATRIX.md

**Audit ID:** canonical-audit-01  
**Date:** 2026-07-12  
**Scope:** send/core/, send/runtime/, send/intelligence/, send/schema/, send/config/, send/validation/, send/monitoring/, send/alerts/, send/experiments/, send/metrics/  

---

## Alignment Status Legend

- **ALIGNED**: Implementation matches governing spec (based on available evidence)
- **PARTIAL**: Implementation exists but does not fully cover canonical requirements
- **UNDOCUMENTED**: Implementation exists with no governing canonical specification
- **MISSING**: Canonical spec exists but implementation module/file is absent
- **CONFLICT**: Implementation contradicts canonical specification
- **UNVERIFIED**: Existence confirmed, but deep alignment inspection was not completed in this audit

---

## Core Module Alignment

### send/core/strategy_v2.py

| Field | Value |
|---|---|
| **Module / File** | `send/core/strategy_v2.py` |
| **Implemented Responsibility** | Strategy core: EMA/RSI indicators, scoring, buffer calculation, DecisionObject production |
| **Governing Specification** | `ALGO_SPEC_v2.0.0.md` (CAM-002), `DECISION_OBJECT_CANONICAL_SPEC_v1.0.0.md` (CAM-005), `SR_CORRIDOR_ENGINE_SPEC_v2.0.0.md` (CAM-004), `MODULE_INTERFACE_SPEC_v2.0.0.md` (CAM-020) |
| **Alignment Status** | **PARTIAL** |
| **Missing Implementation** | Adaptive Activity Gate (ADAPTIVE_ACTIVITY_GATE_SPEC.md / GAP-011); full DecisionObject field validation per spec (GAP-004) |
| **Undocumented Implementation** | `update_symbol_replacement_score()` function — calls into scan_scheduler (missing module, GAP-002); behavior not covered by any active canonical doc |
| **Contradiction** | None confirmed. Hardcoded `/opt/binarybot/` path references (CON-007) |
| **Risk Level** | MEDIUM |
| **Evidence** | File header: "Implements ALGO_SPEC.md (gates + scoring + buffer + expiry) under MODULE_INTERFACE_SPEC.md contract." function signatures match strategy spec domain. |

---

### send/core/fsm_runtime.py

| Field | Value |
|---|---|
| **Module / File** | `send/core/fsm_runtime.py` |
| **Implemented Responsibility** | FSM state management: WIDE_SCAN / WATCHLIST modes, watchlist lifecycle, state transitions, invariant enforcement |
| **Governing Specification** | `FSM_DECISION_ENGINE_SPEC_v1.0.0.md` (CAM-006), `DECISION_OBJECT_CANONICAL_SPEC_v1.0.0.md` (CAM-005), `SYSTEM_INVARIANTS_v2.0.0.md` (CAM-019) |
| **Alignment Status** | **PARTIAL** |
| **Missing Implementation** | Full state transition coverage per FSM spec not verified; recovery from corrupted state file not confirmed |
| **Undocumented Implementation** | `STATE_PATH = "/opt/binarybot/state/focus_state.json"` — hardcoded production path not documented in MODULE_INTERFACE_SPEC |
| **Contradiction** | None confirmed |
| **Risk Level** | MEDIUM |
| **Evidence** | `MAX_WATCHLIST = 2`, `mode: "WIDE_SCAN"`, `state: "IDLE"` match FSM spec domain. `enforce_invariants()` explicitly raises RuntimeError on watchlist overflow per SYSTEM_INVARIANTS. |

---

### send/core/signal_engine.py

| Field | Value |
|---|---|
| **Module / File** | `send/core/signal_engine.py` |
| **Implemented Responsibility** | Signal engine tick: orchestrates one evaluation cycle — calls strategy, FSM, distribution, logging |
| **Governing Specification** | `SIGNAL_ENGINE_EXECUTION_SPEC_v2.0.0.md` (CAM-007), `CANONICAL_STRATEGY_STACK_v1.0.0.md` (CAM-001) |
| **Alignment Status** | **PARTIAL** |
| **Missing Implementation** | `trade_temporal_telemetry` module (GAP-001); `scan_scheduler` module (GAP-002); missing telemetry registration |
| **Undocumented Implementation** | `update_symbol_replacement_score()` — no canonical spec |
| **Contradiction** | Imports a missing module (`trade_temporal_telemetry`) — runtime risk (CON-003) |
| **Risk Level** | CRITICAL |
| **Evidence** | `from core import trade_temporal_telemetry` followed by `trade_temporal_telemetry.register_open_now_trade()` call. Module does not exist. |

---

### send/core/observability_logger.py

| Field | Value |
|---|---|
| **Module / File** | `send/core/observability_logger.py` |
| **Implemented Responsibility** | Event logging: structured event emission, error logging, telemetry |
| **Governing Specification** | `OBSERVABILITY_SPEC_v2.0.0.md` (CAM-008), `OBSERVABILITY_LOGGING_SPEC_v2.0.0.md` (CAM-009), `EVENT_SCHEMA_SPEC_v2.0.0.md` (CAM-016) |
| **Alignment Status** | **PARTIAL** |
| **Missing Implementation** | Event schema validation against full EVENT_SCHEMA_SPEC (only 4 types in event_schema.json, GAP-005); full telemetry field coverage per OBSERVABILITY_LOGGING_SPEC not verified |
| **Undocumented Implementation** | `SCHEMA_VERSION`, `SERVICE_NAME`, `ENV_NAME`, `BOT_VERSION`, `GIT_SHA` env vars — referenced in code; not individually governed in active doc |
| **Contradiction** | Implements both OBSERVABILITY_SPEC and OBSERVABILITY_LOGGING_SPEC domains — reflecting the CON-001 overlap |
| **Risk Level** | MEDIUM |
| **Evidence** | `SCHEMA_VERSION = os.getenv("EVENT_SCHEMA_VERSION", "1.0.0")`. `OBS_DIR = os.getenv("OBS_DIR", "/opt/binarybot/observability")`. |

---

### send/core/distribution_router.py

| Field | Value |
|---|---|
| **Module / File** | `send/core/distribution_router.py` |
| **Implemented Responsibility** | Tier-based signal distribution to Telegram channels; channel reset logic; distribution state management |
| **Governing Specification** | `SIGNAL_DISTRIBUTION_SPEC_v2.0.0.md` (CAM-011), `SIGNAL_DISTRIBUTION_ARCHITECTURE_v2.0.0.md` (CAM-010), `CHANNEL_CONFIG_SPEC_v2.0.0.md` (CAM-017) |
| **Alignment Status** | **PARTIAL** |
| **Missing Implementation** | Full entitlement routing model per spec not verified; affiliate scope routing not fully inspected |
| **Undocumented Implementation** | Hardcoded `RESET_HOUR = 8`, `RESET_MINUTE = 10` — daily reset time not found in any canonical doc |
| **Contradiction** | None confirmed |
| **Risk Level** | MEDIUM |
| **Evidence** | `CHANNEL_CONFIG_PATHS` matches CHANNEL_CONFIG_SPEC domain. `DIST_STATE_PATH` matches distribution state concept. `LONDON_TZ` hardcoded — timezone governance not found in active canonical doc. |

---

### send/core/storage.py

| Field | Value |
|---|---|
| **Module / File** | `send/core/storage.py` |
| **Implemented Responsibility** | Atomic JSON persistence, JSONL append-only logging, cross-process locking |
| **Governing Specification** | `MODULE_INTERFACE_SPEC_v2.0.0.md` (CAM-020), `STATE_PERSISTENCE_SPEC.md` (GAP-015 — not in active canonical set) |
| **Alignment Status** | **PARTIAL** |
| **Missing Implementation** | Canonical persistence spec not in active set (GAP-015) — cannot confirm full spec alignment |
| **Undocumented Implementation** | File lock mechanism (lockfiles) — not found in any active canonical spec |
| **Contradiction** | None confirmed |
| **Risk Level** | LOW |
| **Evidence** | File header: "BinaryBot — Atomic Persistence Layer (canonical). Hard rules: no module writes JSON directly; JSON writes must be atomic; JSONL is append-only." These match MODULE_INTERFACE_SPEC principles. |

---

### send/core/candle_adapter.py

| Field | Value |
|---|---|
| **Module / File** | `send/core/candle_adapter.py` |
| **Implemented Responsibility** | Candle normalization and validation: converts external candle payloads to internal format |
| **Governing Specification** | `MODULE_INTERFACE_SPEC_v2.0.0.md` (CAM-020), `ALGO_SPEC_v2.0.0.md` (CAM-002) |
| **Alignment Status** | **PARTIAL** |
| **Missing Implementation** | Full input validation contract per MODULE_INTERFACE_SPEC not verified |
| **Undocumented Implementation** | Multi-key fallback for candle fields (`_pick()`) — normalizes various upstream formats |
| **Contradiction** | None confirmed |
| **Risk Level** | LOW |
| **Evidence** | File header: "BinaryBot — Candle Adapter (normalize + validate). Canonical helper to convert external candle payloads into internal Candle dicts." |

---

### send/core/params_loader.py

| Field | Value |
|---|---|
| **Module / File** | `send/core/params_loader.py` |
| **Implemented Responsibility** | Loads and validates algo_params.json; enforces required key presence and structural validity |
| **Governing Specification** | `STRATEGY_PARAMETER_CONTROL_SPEC_v2.0.0.md` (CAM-032), `SYSTEM_INVARIANTS_v2.0.0.md` (CAM-019) |
| **Alignment Status** | **PARTIAL** |
| **Missing Implementation** | `params_schema.json` validation not integrated (GAP-006); comment still references old `PARAMS_REFERENCE.md` name (CON-008) |
| **Undocumented Implementation** | `_validate_no_hardcoded_leaks()` — validates against key smuggling; not explicitly described in active canonical spec |
| **Contradiction** | Comment references `PARAMS_REFERENCE.md` (superseded doc name) — CON-008 |
| **Risk Level** | MEDIUM |
| **Evidence** | `REQUIRED_TOP_LEVEL_KEYS` matches algo_params.json actual keys. `REQUIRED_NESTED_KEYS` validates nested structure. Comment: `# Canonical references: PARAMS_REFERENCE.md, SYSTEM_INVARIANTS.md (INV-30/31/32)`. |

---

### send/core/admin_commands.py

| Field | Value |
|---|---|
| **Module / File** | `send/core/admin_commands.py` |
| **Implemented Responsibility** | Admin command handling: strategy status, symbol management, param adjustments, report retrieval |
| **Governing Specification** | `ADMIN_CONTROL_SPEC_v2.0.0.md` (CAM-012), `ADMIN_OPERATIONS_SPEC_v2.0.0.md` (CAM-013), `ROLE_AND_PERMISSION_MATRIX_SPEC_v2.0.0.md` (CAM-015) |
| **Alignment Status** | **PARTIAL** |
| **Missing Implementation** | No formal admin command interface definition (GAP-014); full command-permission matrix verification not performed |
| **Undocumented Implementation** | Hardcoded directory paths (`CONFIG_DIR`, `OBS_DIR`, `REPORTS_DIR`); `ADMIN_EVENTS_PATH`, `ADMIN_PROOFS_PATH`, `ENGINE_EVENTS_PATH` — operational paths not verified against canonical spec |
| **Contradiction** | None confirmed |
| **Risk Level** | MEDIUM |
| **Evidence** | Imports from admin_permissions (has_permission, require_permission) and admin_views — matches hierarchical admin spec architecture. ADMIN_PROOFS_PATH exists for audit trail. |

---

### send/core/admin_permissions.py

| Field | Value |
|---|---|
| **Module / File** | `send/core/admin_permissions.py` |
| **Implemented Responsibility** | Role loading, permission checking, affiliate scope, identity debugging |
| **Governing Specification** | `ROLE_AND_PERMISSION_MATRIX_SPEC_v2.0.0.md` (CAM-015), `AFFILIATE_SIGNAL_DISTRIBUTION_MODEL_v2.0.0.md` (CAM-033) |
| **Alignment Status** | **PARTIAL** |
| **Missing Implementation** | Role schema validation per GAP-018 |
| **Undocumented Implementation** | `ROLES_CONFIG_PATH` — actual path not confirmed in active canonical spec |
| **Contradiction** | None confirmed |
| **Risk Level** | LOW |
| **Evidence** | Functions: `has_permission`, `get_primary_role`, `get_affiliate_scope`, `load_roles_config` match spec domain. |

---

### send/core/admin_views.py

| Field | Value |
|---|---|
| **Module / File** | `send/core/admin_views.py` |
| **Implemented Responsibility** | Admin UI view rendering for Telegram |
| **Governing Specification** | `CONTROL_PANEL_HIERARCHY_AND_INTELLIGENCE_SPEC_v2.0.0.md` (CAM-035), `TELEGRAM_UX_v2.0.0.md` (CAM-018), `ADMIN_CONTROL_SPEC_v2.0.0.md` (CAM-012) |
| **Alignment Status** | **UNVERIFIED** |
| **Missing Implementation** | Not inspected in detail |
| **Undocumented Implementation** | Not inspected in detail |
| **Contradiction** | None confirmed |
| **Risk Level** | LOW |
| **Evidence** | Confirmed existence; imports align with admin domain. |

---

### send/core/outcome_service.py

| Field | Value |
|---|---|
| **Module / File** | `send/core/outcome_service.py` |
| **Implemented Responsibility** | Signal outcome recording |
| **Governing Specification** | `OUTCOME_TRACKING_SPEC_v2.0.0.md` (CAM-024) |
| **Alignment Status** | **UNVERIFIED** |
| **Missing Implementation** | Not inspected in detail |
| **Undocumented Implementation** | Not inspected in detail |
| **Contradiction** | None confirmed |
| **Risk Level** | LOW |
| **Evidence** | Confirmed existence; module name matches spec domain. |

---

### send/core/analytics_engine.py

| Field | Value |
|---|---|
| **Module / File** | `send/core/analytics_engine.py` |
| **Implemented Responsibility** | Analytics computation |
| **Governing Specification** | `PERFORMANCE_ANALYTICS_SPEC_v2.0.0.md` (CAM-025) |
| **Alignment Status** | **UNVERIFIED** |
| **Missing Implementation** | Not inspected in detail |
| **Undocumented Implementation** | Not inspected in detail |
| **Contradiction** | None confirmed |
| **Risk Level** | LOW |
| **Evidence** | Confirmed existence. |

---

### send/core/telegram_publisher.py

| Field | Value |
|---|---|
| **Module / File** | `send/core/telegram_publisher.py` |
| **Implemented Responsibility** | Telegram message publishing |
| **Governing Specification** | `TELEGRAM_UX_v2.0.0.md` (CAM-018), `SIGNAL_DISTRIBUTION_SPEC_v2.0.0.md` (CAM-011) |
| **Alignment Status** | **UNVERIFIED** |
| **Missing Implementation** | Not inspected in detail |
| **Undocumented Implementation** | Not inspected in detail |
| **Contradiction** | None confirmed |
| **Risk Level** | LOW |
| **Evidence** | Confirmed existence. |

---

### send/core/bot_service.py

| Field | Value |
|---|---|
| **Module / File** | `send/core/bot_service.py` |
| **Implemented Responsibility** | Bot service orchestration |
| **Governing Specification** | `SYSTEM_ARCHITECTURE_MAP_v2.0.0.md` (CAM-029), `MODULE_INTERFACE_SPEC_v2.0.0.md` (CAM-020) |
| **Alignment Status** | **UNVERIFIED** |
| **Missing Implementation** | Not inspected in detail |
| **Undocumented Implementation** | Not inspected in detail |
| **Contradiction** | None confirmed |
| **Risk Level** | LOW |
| **Evidence** | Confirmed existence. |

---

## Runtime Module Alignment

### send/runtime/engine_loop.py

| Field | Value |
|---|---|
| **Module / File** | `send/runtime/engine_loop.py` |
| **Implemented Responsibility** | Main engine loop: calls run_once() every 2 seconds, handles errors |
| **Governing Specification** | `SIGNAL_ENGINE_EXECUTION_SPEC_v2.0.0.md` (CAM-007), `SYSTEM_INVARIANTS_v2.0.0.md` (CAM-019) |
| **Alignment Status** | **PARTIAL** |
| **Missing Implementation** | ENGINE_TICK_SECONDS=2 not verified against any canonical spec |
| **Undocumented Implementation** | Hardcoded tick interval |
| **Contradiction** | None confirmed |
| **Risk Level** | LOW |
| **Evidence** | `ENGINE_TICK_SECONDS = 2`. Imports `run_once` from `core.signal_engine`. Logs engine_start event via observability_logger. |

---

### send/runtime/system_boot.py

| Field | Value |
|---|---|
| **Module / File** | `send/runtime/system_boot.py` |
| **Implemented Responsibility** | System boot: loads .env file into environment before runtime imports |
| **Governing Specification** | `DEPLOYMENT_PROTOCOL_v2.0.0.md` (CAM-031) |
| **Alignment Status** | **PARTIAL** |
| **Missing Implementation** | Full boot sequence per DEPLOYMENT_PROTOCOL not verified |
| **Undocumented Implementation** | Boot path: `/opt/binarybot/.env` hardcoded |
| **Contradiction** | None confirmed |
| **Risk Level** | LOW |
| **Evidence** | `env_path = Path("/opt/binarybot/.env")`. Boot sequence implementation confirmed. |

---

### send/runtime/market_client.py, distribution_scheduler.py, telegram_updates.py

| Field | Value |
|---|---|
| **Module / File** | `send/runtime/market_client.py`, `send/runtime/distribution_scheduler.py`, `send/runtime/telegram_updates.py` |
| **Implemented Responsibility** | Market data fetching, distribution scheduling, Telegram update handling |
| **Governing Specification** | `SYSTEM_ARCHITECTURE_MAP_v2.0.0.md` (CAM-029), `SIGNAL_DISTRIBUTION_ARCHITECTURE_v2.0.0.md` (CAM-010) |
| **Alignment Status** | **UNVERIFIED** |
| **Missing Implementation** | Not inspected in detail |
| **Undocumented Implementation** | Not inspected in detail |
| **Contradiction** | None confirmed |
| **Risk Level** | LOW |
| **Evidence** | Confirmed existence. |

---

## Intelligence Module Alignment

### send/intelligence/* (9 modules)

| Field | Value |
|---|---|
| **Module / File** | `send/intelligence/adaptive_params.py`, `bottleneck_detector.py`, `heatmap.py`, `report_loader.py`, `research_engine.py`, `risk_monitor.py`, `signal_diagnostics.py`, `strategy_optimizer.py`, `symbol_health.py` |
| **Implemented Responsibility** | Adaptive parameter management, bottleneck detection, heatmap analysis, report loading, research, risk monitoring, signal diagnostics, strategy optimization, symbol health |
| **Governing Specification** | `STRATEGY_INTELLIGENCE_SYSTEM_v2.0.0.md` (CAM-027), `RESEARCH_AND_LEARNING_FRAMEWORK_SPEC_v2.0.0.md` (CAM-026), `PERFORMANCE_ANALYTICS_SPEC_v2.0.0.md` (CAM-025) |
| **Alignment Status** | **UNVERIFIED** |
| **Missing Implementation** | Module-level specs not individually defined (GAP-012). Intake docs (INTELLIGENCE_FILES_AND_MODULE_MAP, AI_STRATEGY_AUDITOR_SPEC) pending merge decisions per CANON_BATCH_EVALUATION. |
| **Undocumented Implementation** | `risk_monitor.py` — no active canonical risk spec (GAP-008) |
| **Contradiction** | None confirmed |
| **Risk Level** | MEDIUM (due to missing module-level specs) |
| **Evidence** | All 9 files confirmed to exist. Module names align with intelligence spec domains. |

---

## Schema and Config Alignment

### send/schema/event_schema.json

| Field | Value |
|---|---|
| **Module / File** | `send/schema/event_schema.json` |
| **Implemented Responsibility** | Event type definitions for validation |
| **Governing Specification** | `EVENT_SCHEMA_SPEC_v2.0.0.md` (CAM-016) |
| **Alignment Status** | **PARTIAL** |
| **Missing Implementation** | Only 4 event types defined; canonical spec covers many more (GAP-005) |
| **Contradiction** | Schema version 1.0.0 in file vs EVENT_SCHEMA_SPEC v2.0.0 |
| **Risk Level** | MEDIUM |
| **Evidence** | Confirmed content: 4 event types only. |

---

### send/schema/params_schema.json

| Field | Value |
|---|---|
| **Module / File** | `send/schema/params_schema.json` |
| **Implemented Responsibility** | Parameter validation schema |
| **Governing Specification** | `STRATEGY_PARAMETER_CONTROL_SPEC_v2.0.0.md` (CAM-032) |
| **Alignment Status** | **CONFLICT** |
| **Missing Implementation** | Schema keys do not match runtime keys (GAP-006, CON-005) |
| **Contradiction** | Schema defines `strategy_v2`, `buffer_multipliers`, `score_thresholds`; runtime uses `thresholds`, `weights`, `buffer`, `gates` |
| **Risk Level** | HIGH |
| **Evidence** | Direct inspection of params_schema.json vs algo_params.json vs params_loader.py. |

---

### send/config/algo_params.json

| Field | Value |
|---|---|
| **Module / File** | `send/config/algo_params.json` |
| **Implemented Responsibility** | Runtime algorithm parameters |
| **Governing Specification** | `STRATEGY_PARAMETER_CONTROL_SPEC_v2.0.0.md` (CAM-032) |
| **Alignment Status** | **ALIGNED** (with params_loader.py; not with params_schema.json) |
| **Missing Implementation** | None identified in this audit |
| **Contradiction** | Inconsistent with params_schema.json (CON-005) |
| **Risk Level** | MEDIUM |
| **Evidence** | algo_params.json keys match params_loader.py REQUIRED_TOP_LEVEL_KEYS. |

---

### send/config/channel_config.json

| Field | Value |
|---|---|
| **Module / File** | `send/config/channel_config.json` |
| **Implemented Responsibility** | Channel configuration for Telegram distribution tiers |
| **Governing Specification** | `CHANNEL_CONFIG_SPEC_v2.0.0.md` (CAM-017) |
| **Alignment Status** | **UNVERIFIED** |
| **Missing Implementation** | Not inspected in detail |
| **Contradiction** | None confirmed |
| **Risk Level** | LOW |
| **Evidence** | File confirmed to exist. distribution_router.py loads from CHANNEL_CONFIG_PATHS. |

---

### send/config/admin_roles.json, admin_permissions.json

| Field | Value |
|---|---|
| **Module / File** | `send/config/admin_roles.json`, `send/config/admin_permissions.json` |
| **Implemented Responsibility** | Role and permission configuration |
| **Governing Specification** | `ROLE_AND_PERMISSION_MATRIX_SPEC_v2.0.0.md` (CAM-015) |
| **Alignment Status** | **UNVERIFIED** |
| **Missing Implementation** | Schema for each file not verified against spec (GAP-018) |
| **Contradiction** | None confirmed |
| **Risk Level** | MEDIUM |
| **Evidence** | Both files confirmed to exist. admin_permissions.py references ROLES_CONFIG_PATH. |

---

## Monitoring and Validation Module Alignment

### send/monitoring/health_check.py, restart_guard.py

| Field | Value |
|---|---|
| **Module / File** | `send/monitoring/health_check.py`, `send/monitoring/restart_guard.py` |
| **Implemented Responsibility** | System health monitoring and automatic restart |
| **Governing Specification** | `FAILURE_RECOVERY_SPEC_v2.0.0.md` (CAM-022), `MONITORING_ALERTS_SPEC.md` (GAP-016 — not in active canonical) |
| **Alignment Status** | **UNVERIFIED** |
| **Missing Implementation** | Not inspected in detail |
| **Contradiction** | None confirmed |
| **Risk Level** | LOW |
| **Evidence** | Confirmed existence. |

---

### send/validation/statistical_proof.py

| Field | Value |
|---|---|
| **Module / File** | `send/validation/statistical_proof.py` |
| **Implemented Responsibility** | Statistical proof computation for strategy validation |
| **Governing Specification** | `PERFORMANCE_ANALYTICS_SPEC_v2.0.0.md` (CAM-025), `RESEARCH_AND_LEARNING_FRAMEWORK_SPEC_v2.0.0.md` (CAM-026) |
| **Alignment Status** | **UNVERIFIED** |
| **Missing Implementation** | Superseded STATISTICAL_PROOF_LAYER was replaced by three active specs; full alignment with the new specs not verified |
| **Contradiction** | None confirmed |
| **Risk Level** | MEDIUM |
| **Evidence** | Confirmed existence. STATISTICAL_PROOF_LAYER_legacy_superseded.md named PERFORMANCE_ANALYTICS_SPEC, RESEARCH_AND_LEARNING_FRAMEWORK_SPEC, STRATEGY_INTELLIGENCE_SYSTEM as successors. |

---

## Modules Without Governing Canonical Specification

| Module | Description | Risk | Gap ID |
|---|---|---|---|
| `send/experiments/experiment_runner.py` | Experiment execution | LOW | GAP-012 (partial) |
| `send/experiments/parameter_search.py` | Parameter search | LOW | GAP-012 (partial) |
| `send/journal/trade_journal.py` | Trade journal | LOW | None identified |
| `send/legacy/bot_control.py` | Legacy bot control | LOW | GAP-017 |
| `send/metrics/aggregates_writer.py` | Metrics aggregation | LOW | None identified |
| `send/metrics/metrics_collector.py` | Metrics collection | LOW | None identified |
| `send/model_registry/registry.py` | Model registry | LOW | None identified |
| `send/snapshots/snapshot_manager.py` | State snapshots | LOW | None identified |
| `send/state_store/event_store.py` | Event storage | LOW | None identified |
| `send/state_store/state_store.py` | State storage | LOW | None identified |
| `send/alerts/alert_engine.py` | Alert engine | LOW | None identified |
| `send/tools/strategy_auditor_daily.py` | Daily strategy audit | LOW | None identified |
| `send/tools/strategy_auditor_lib.py` | Audit library | LOW | None identified |

---

*End of CODE_TO_CANON_ALIGNMENT_MATRIX.md*
