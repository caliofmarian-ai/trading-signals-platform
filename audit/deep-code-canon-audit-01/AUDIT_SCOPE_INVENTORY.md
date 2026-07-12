# AUDIT_SCOPE_INVENTORY

## Scope statement
- Canon inspected: all 42 files under `send/docs/canonical/active/`.
- Authoritative canonical specs covered: 41.
- Non-authoritative file inspected but excluded from compliance scoring: `send/docs/canonical/active/CANON_BATCH_EVALUATION_v2.0.0.md` (governance/evaluation record per `audit/canonical-reconciliation-01/RECONCILIATION_SUMMARY.md:94-100`).
- Prior audit/governance inputs inspected:
  - `audit/canonical-reconciliation-01/DEFERRED_IMPLEMENTATION_REGISTER.md`
  - `audit/canonical-reconciliation-01/RECONCILIATION_SUMMARY.md`
  - `audit/canonical-audit-01/CANONICAL_GAP_ANALYSIS.md`
- Implementation inspected: all 59 Python files under `send/` (excluding `venv/`, `__pycache__`) and all 20 JSON files under `send/`.

## Implementation directory inventory
| Directory | Python | JSON | Other | Notes |
|---|---:|---:|---:|---|
| `send/core` | 17 | 0 | 5 | Core runtime/control-plane logic; highest audit depth |
| `send/runtime` | 6 | 0 | 2 | Boot, loops, polling, scheduler |
| `send/intelligence` | 10 | 0 | 0 | Research/intelligence/optimization |
| `send/monitoring` | 3 | 0 | 0 | Restart/health |
| `send/experiments` | 3 | 0 | 0 | Offline experimentation |
| `send/tools` | 2 | 0 | 0 | Daily audit tooling |
| `send/validation` | 2 | 0 | 0 | Statistical proof layer; one file effectively absent/empty in tree audit |
| `send/alerts` | 2 | 0 | 6 | Alert math utilities |
| `send/journal` | 2 | 0 | 1 | Trade journal |
| `send/metrics` | 3 | 0 | 0 | Runtime metrics |
| `send/model_registry` | 2 | 0 | 0 | Model/version registry |
| `send/state_store` | 3 | 0 | 0 | Alternate persistence abstraction |
| `send/snapshots` | 2 | 0 | 0 | Snapshot/restore |
| `send/legacy` | 1 | 0 | 0 | Legacy Telegram bot |
| `send/schema` | 1 | 2 | 0 | Schema/docs helpers |
| `send/config` | 0 | 8 | 2 | Runtime config/state-like JSON |
| `send/state` | 0 | 8 | 0 | Persisted sample/current state |
| `send/outcomes` | 0 | 1 | 1 | Outcome registry sample/current state |
| `send/analytics` | 0 | 1 | 1 | Generated report sample |
| `send/docs` | 0 | 0 | 228 | Canonical and non-canonical documentation |

## Runtime entry points
| Entry point | Reachability | Notes |
|---|---|---|
| `send/runtime/system_boot.py:start_system()` | Primary runtime entry point | Starts engine, Telegram poller, distribution scheduler (`system_boot.py:51-88`) |
| `send/runtime/engine_loop.py:start_engine()` | Called by boot thread | Calls `core.signal_engine.run_once()` every 2s (`engine_loop.py:11-31`) |
| `send/runtime/telegram_updates.py:poll_updates()` | Called by boot thread | Long-poll Telegram updates (`telegram_updates.py:28-68`) |
| `send/runtime/distribution_scheduler.py:scheduler_loop()` | Called by boot thread | Daily reset helper (`distribution_scheduler.py:21-60`) |
| `send/tools/strategy_auditor_daily.py:run_auditor()` | Operational script | Broken package import (`strategy_auditor_daily.py:4-9`) |
| `send/legacy/bot_control.py:main()` | Orphan/legacy | Separate Telegram bot stack using `python-telegram-bot` |

## Operational scripts / offline tools
- `send/tools/strategy_auditor_daily.py`
- `send/tools/strategy_auditor_lib.py`
- `send/experiments/experiment_runner.py`
- `send/experiments/parameter_search.py`
- `send/snapshots/snapshot_manager.py`
- `send/monitoring/health_check.py`
- `send/metrics/aggregates_writer.py`

## Schemas and config files inspected
- Schemas:
  - `send/schema/params_schema.json`
  - `send/schema/event_schema.json`
- Config:
  - `send/config/algo_params.json`
  - `send/config/channel_config.json`
  - `send/config/admin_roles.json`
  - `send/config/admin_permissions.json`
  - `send/config/admin_settings.json`
  - `send/config/active_symbols.json`
  - `send/config/symbols.json`
  - `send/config/intelligence_settings.json`
- State/persistence samples/current files:
  - `send/state/active_symbols.json`
  - `send/state/dist_state.json`
  - `send/state/event_store.json`
  - `send/state/focus_state.json`
  - `send/state/outcomes.json`
  - `send/state/restart_guard.json`
  - `send/state/state_store.json`
  - `send/state/trade_journal.json`
  - `send/outcomes/open_now_registry.json`
  - `send/analytics/reports/daily_strategy_audit_2026-03-06.json`

## Persistence/state stores
| Path family | Writer(s) | Observed issues |
|---|---|---|
| `/opt/binarybot/state/focus_state.json` | `core.fsm_runtime`, `core.signal_engine.update_symbol_replacement_score`, `snapshots.snapshot_manager` | Multiple access paths; nonexistent `scan_scheduler` ref; no watchlist release path |
| `/opt/binarybot/state/dist_state.json` | `core.distribution_router`, `state_store.state_store`, `snapshots.snapshot_manager` | Duplicate schemas (`last_reset_london_date` vs `last_reset_epoch`) |
| `/opt/binarybot/outcomes/open_now_registry.json` | `core.outcome_service` | Separate from missing canonical temporal telemetry module |
| `/opt/binarybot/outcomes/outcomes.jsonl` | `core.outcome_service`, `observability_logger` | Valid path, but event taxonomy mismatch for some outcome events |
| `/opt/binarybot/outcomes/outcomes_index.json` | `core.outcome_service` | Locking present |
| `/opt/binarybot/config/algo_params.json` | `core.admin_commands`, `core.params_loader` | Writer and reader expect different schemas |
| `/opt/binarybot/config/active_symbols.json` | `core.admin_commands`, `core.signal_engine` | Dual format support; no canonical schema enforcement |
| `/opt/binarybot/settings.json` / `config/settings.json` | `core.bot_service`, `state_store.state_store`, `core.signal_engine` (via missing `config_path`) | Path-family drift |

## Integrations
- Telegram Bot API: `core.telegram_publisher`, `runtime.telegram_updates`, `core.outcome_service`, `legacy.bot_control`
- Market data API: TwelveData via `runtime.market_client`
- Filesystem persistence: `core.storage`, `state_store.event_store`, `snapshots.snapshot_manager`, `journal.trade_journal`, `metrics.aggregates_writer`
- Admin control plane: Telegram command/callback handling split across `core.admin_commands`, `core.admin_permissions`, `core.admin_views`, and older `core.bot_service`

## Canonical spec -> implementation area map
| Canonical spec | Primary implementation area(s) |
|---|---|
| ADMIN_CONTROL_SPEC_v2.0.0 | `core/admin_commands.py`, `core/admin_permissions.py`, `core/admin_views.py`, `core/bot_service.py` |
| ADMIN_OPERATIONS_SPEC_v2.0.0 | Same admin cluster plus `runtime/telegram_updates.py` |
| ADMIN_SURFACE_AND_CONTROL_PLANE_CANON_v2.0.0 | `core/admin_*`, `core/bot_service.py`, `legacy/bot_control.py` |
| ADMIN_TREE_MAP_v2.0.0 | `core/admin_views.py`, `core/bot_service.py` |
| AFFILIATE_SIGNAL_DISTRIBUTION_MODEL_v2.0.0 | `core/admin_permissions.py`, `core/admin_commands.py` |
| ALGO_SPEC_v2.0.0 | `core/strategy_v2.py`, `core/signal_engine.py`, `core/candle_adapter.py` |
| AUTONOMOUS_STRATEGY_EVOLUTION_SYSTEM_v2.0.0 | `intelligence/*`, `experiments/*`, `model_registry/registry.py` |
| CANONICAL_MASTER_INDEX_v1.0.0 | Documentation/governance only |
| CANONICAL_STRATEGY_STACK_v1.0.0 | `core/strategy_v2.py`, `core/fsm_runtime.py`, `core/signal_engine.py` |
| CHANNEL_CONFIG_SPEC_v2.0.0 | `core/distribution_router.py`, `config/channel_config.json`, `state/state_store.json` |
| COMMUNITY_FEEDBACK_AND_PRIVACY_SPEC_v2.0.0 | `core/outcome_service.py`, `runtime/telegram_updates.py`, `core/bot_service.py` |
| CONTROL_PANEL_HIERARCHY_AND_INTELLIGENCE_SPEC_v2.0.0 | `core/admin_*`, `core/bot_service.py`, `intelligence/*` |
| DECISION_AUDIT_SPEC_v2.0.0 | `core/signal_engine.py`, `core/observability_logger.py`, `tools/strategy_auditor_lib.py` |
| DECISION_OBJECT_CANONICAL_SPEC_v1.0.0 | `core/strategy_v2.py`, `core/fsm_runtime.py` |
| DEPLOYMENT_PROTOCOL_v2.0.0 | No dedicated code; partial operational scripts only |
| EVENT_SCHEMA_SPEC_v2.0.0 | `core/observability_logger.py`, `schema/event_schema.json`, all event emitters |
| FAILURE_RECOVERY_SPEC_v2.0.0 | `monitoring/restart_guard.py`, `snapshots/snapshot_manager.py`, `core/storage.py` |
| FSM_DECISION_ENGINE_SPEC_v1.0.0 | `core/fsm_runtime.py`, `core/signal_engine.py` |
| GOVERNANCE_AND_CHANGE_CONTROL_v2.0.0 | `core/params_loader.py`, `model_registry/registry.py`, audit docs |
| MODULE_INTERFACE_SPEC_v2.0.0 | All `core/*`, `runtime/*`, `intelligence/*` interfaces |
| OBSERVABILITY_LOGGING_SPEC_v2.0.0 | `core/observability_logger.py`, emitters in `core/*`, `monitoring/*`, `intelligence/*` |
| OBSERVABILITY_SPEC_v2.0.0 | Same as above |
| OUTCOME_TRACKING_SPEC_v2.0.0 | `core/outcome_service.py`, `runtime/telegram_updates.py`, `core/distribution_router.py` |
| PERFORMANCE_ANALYTICS_SPEC_v2.0.0 | `core/analytics_engine.py`, `intelligence/research_engine.py`, `tools/strategy_auditor_lib.py` |
| RESEARCH_AND_LEARNING_FRAMEWORK_SPEC_v2.0.0 | `intelligence/*`, `experiments/*`, `tools/strategy_auditor_lib.py` |
| RISK_MODEL_v2.0.0 | `core/strategy_v2.py`, `intelligence/risk_monitor.py`, `core/distribution_router.py` |
| ROLE_AND_PERMISSION_MATRIX_SPEC_v2.0.0 | `core/admin_permissions.py`, `config/admin_roles.json`, `config/admin_permissions.json` |
| SECURITY_MODEL_v2.0.0 | `core/admin_permissions.py`, `core/outcome_service.py`, `runtime/telegram_updates.py`, `core/bot_service.py` |
| SIGNAL_DISTRIBUTION_ARCHITECTURE_v2.0.0 | `core/distribution_router.py`, `core/telegram_publisher.py` |
| SIGNAL_DISTRIBUTION_SPEC_v2.0.0 | `core/distribution_router.py`, `config/channel_config.json`, `state/dist_state.json` |
| SIGNAL_ECONOMICS_AND_MONETIZATION_MODEL_v2.0.0 | `core/distribution_router.py`, `core/admin_permissions.py` |
| SIGNAL_ENGINE_EXECUTION_SPEC_v2.0.0 | `core/signal_engine.py`, `runtime/engine_loop.py` |
| SR_CORRIDOR_ENGINE_SPEC_v2.0.0 | `core/strategy_v2.py` |
| STRATEGY_INTELLIGENCE_SYSTEM_v2.0.0 | `intelligence/*`, `tools/strategy_auditor_*`, `config/intelligence_settings.json` |
| STRATEGY_PARAMETER_CONTROL_SPEC_v2.0.0 | `core/params_loader.py`, `core/admin_commands.py`, `config/algo_params.json`, `schema/params_schema.json` |
| SYSTEM_ARCHITECTURE_MAP_v2.0.0 | All runtime/core layers |
| SYSTEM_INVARIANTS_v2.0.0 | All runtime/core/state layers |
| TELEGRAM_UX_v2.0.0 | `core/distribution_router.py`, `core/admin_views.py`, `core/bot_service.py`, `runtime/telegram_updates.py` |
| TEST_PLAN_v2.0.0 | No implementation; no tests present |
| TIME_MODEL_UNIFIED_CANON_v2.0.0 | `core/strategy_v2.py`, `core/signal_engine.py` TPS extraction |
| TRADE_TEMPORAL_TELEMETRY_SPEC_v2.0.0 | Missing `core/trade_temporal_telemetry.py`; partial adjacency in `core/outcome_service.py` |

## Inspection status / depth
- Deep read: all files listed explicitly in the user prompt; all canonical specs; all JSON configs/state files.
- Additional targeted verification:
  - import verification of all Python modules (`python importlib` sweep)
  - missing internal import sweep
  - event-type vs observability taxonomy comparison
  - duplicate-file comparison (`strategy_v2.py` vs `strategy_v2 - Copy.py`)

## Explicit exclusions
| Exclusion | Reason |
|---|---|
| `send/venv/` | Third-party environment; not repository implementation |
| `__pycache__`, `*.pyc` | Generated artifacts |
| Non-`send/` application-adjacent files (except requested prior audits) | Outside requested implementation scope |
| `CANON_BATCH_EVALUATION_v2.0.0.md` from compliance counts | Inspected, but governance/evaluation record rather than one of the 41 authoritative specs |
