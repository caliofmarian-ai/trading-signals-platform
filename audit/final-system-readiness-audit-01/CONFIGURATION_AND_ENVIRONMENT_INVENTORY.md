# CONFIGURATION_AND_ENVIRONMENT_INVENTORY.md

**Audit ID:** final-system-readiness-audit-01  
**Date:** 2026-07-13  
**Branch:** copilot/conduct-final-system-readiness-audit  
**HEAD Commit:** 5aa40f0

---

## 1. ENVIRONMENT VARIABLE INVENTORY

| Variable | Module(s) | Required/Optional | Default | Security Sensitive | Format | Missing Behavior | Malformed Behavior | Documented | Railway Suitability |
|---|---|---|---|---|---|---|---|---|---|
| `BINARYBOT_BASE_DIR` | core.storage | Optional | `send/` package directory | No | Absolute path to existing directory | Uses package dir (dev default — NOT production-safe) | `StoragePathError` raised at any path resolution | Implicit (code) | YES — set to persistent volume mount |
| `BINARYBOT_ENV_FILE` | runtime.system_boot | Optional | None | No | Absolute path to .env file | Env not loaded from file; normal OS env used | `RuntimeError` if not absolute path; `RuntimeError` if file missing | Implicit | YES |
| `TELEGRAM_BOT_TOKEN` | core.telegram_publisher, core.outcome_service, runtime.telegram_updates | Required for Telegram | `""` | YES — bot credential | `<token>` string (Telegram Bot API token) | Telegram operations silently fail or raise RuntimeError | Treated as string | Implicit | YES — Railway secret |
| `OWNER_TELEGRAM_ID` | core.admin_permissions | Required for owner role | `""` | YES — user ID | Integer string | Owner role never assigned (any user claiming owner is denied) | Ignored (empty string → no owner) | Implicit | YES — Railway variable |
| `ADMIN_CONTROL_CHAT_ID` | core.bot_service | Required for Admin access | `"0"` | YES — chat ID | Integer string | Admin access fails-closed (all admin blocked) | Parsed as int; malformed → likely 0 → fail-closed | Implicit | YES — Railway variable |
| `ADMIN_CONTROL_THREAD_ID` | core.bot_service | Optional | `"0"` | No | Integer string | No thread filtering (any thread accepted) | Parsed as int | Implicit | YES — Railway variable |
| `ELITE_CHANNEL_ID` | core.outcome_service | Required for outcome voting | `""` | No | String channel ID | Outcome voting config fails (`elite_channel_id_missing`) | Treated as string | Implicit | YES — Railway variable |
| `COMMUNITY_FEEDBACK_SALT` | core.outcome_service, core.analytics_engine | Required for vote privacy | `""` | YES — salt for pseudonymization | String | Outcome voting config fails (`community_feedback_salt_missing`); analytics member_ref returns None | Treated as string | Implicit | YES — Railway secret |
| `OBS_DIR` | core.observability_logger, core.analytics_engine, intelligence.research_engine | Optional (but required for Railway) | `/opt/binarybot/observability` | No | Absolute path string | Observability writes go to `/opt/binarybot/observability` (likely fails on Railway) | Treated as string path | Implicit | YES — MUST set for Railway |
| `OUTCOMES_LOG` | core.observability_logger, core.analytics_engine, intelligence.research_engine | Optional (but required for Railway) | `/opt/binarybot/outcomes/outcomes.jsonl` | No | Absolute file path | Outcomes log writes go to `/opt/binarybot/outcomes/` (likely fails on Railway) | Treated as string | Implicit | YES — MUST set for Railway |
| `ANALYTICS_DIR` | core.analytics_engine, intelligence.research_engine, intelligence.report_loader | Optional (but required for Railway) | `/opt/binarybot/analytics` | No | Absolute path string | Analytics reports go to `/opt/binarybot/analytics` (likely fails on Railway) | Treated as string | Implicit | YES — MUST set for Railway |
| `ALGO_PARAMS_PATH` | core.params_loader | Optional | `/opt/binarybot/config/algo_params.json` | No | Absolute file path | Falls back to default; if file missing, params validation fails | Treated as string | Implicit | YES — or use BINARYBOT_BASE_DIR |
| `ADMIN_ROLES_CONFIG` | core.admin_permissions | Optional | `/opt/binarybot/config/admin_roles.json` | No | Absolute file path | Falls back to default; if missing, uses hardcoded permission matrix | Treated as string | Implicit | YES — or use BINARYBOT_BASE_DIR |
| `ADMIN_PERMISSIONS_CONFIG` | core.admin_permissions | Optional | `/opt/binarybot/config/admin_permissions.json` | No | Absolute file path | Falls back to hardcoded permission matrix only | Treated as string | Implicit | YES — or use BINARYBOT_BASE_DIR |
| `STRATEGY_AUDITOR_SETTINGS` | tools.strategy_auditor_lib | Optional | Project-relative `config/intelligence_settings.json` | No | Absolute file path | Uses project-relative default | Treated as string | Implicit | YES |
| `BOT_ENV` | core.observability_logger | Optional | `"prod"` | No | String | Uses `"prod"` default | Treated as string | Implicit | YES |
| `SERVICE_NAME` | core.observability_logger | Optional | `"binarybot"` | No | String | Uses default | Treated as string | Implicit | YES |
| `BOT_VERSION` | core.observability_logger | Optional | `"0.0.0"` | No | Semver string | Uses `"0.0.0"` | Treated as string | Implicit | YES |
| `GIT_SHA` | core.observability_logger | Optional | `""` | No | Git SHA string | Empty string | Treated as string | Implicit | YES |
| `RUN_ID` | core.observability_logger | Optional | Auto-generated `run_YYYYMMDD_HHMMSS_<hex>` | No | String | Auto-generated | Treated as string | Implicit | YES |
| `TWELVE_DATA_API_KEY` | runtime.market_client | Required for live market data | None (not defaulted) | YES — API key | String | Market data requests fail (key sent as None) | Sent to API | Implicit | YES — Railway secret |
| `DIST_EVENTS_LOG` | core.observability_logger | Optional | `{OBS_DIR}/distribution_events.jsonl` | No | Absolute file path | Uses OBS_DIR-relative default | Treated as string | Implicit | YES |
| `FSM_EVENTS_LOG` | core.observability_logger | Optional | `{OBS_DIR}/fsm_events.jsonl` | No | Absolute file path | Uses OBS_DIR-relative default | Treated as string | Implicit | YES |
| `ENGINE_EVENTS_LOG` | core.observability_logger | Optional | `{OBS_DIR}/engine_events.jsonl` | No | Absolute file path | Uses OBS_DIR-relative default | Treated as string | Implicit | YES |
| `ADMIN_PROOFS_LOG` | core.observability_logger | Optional | `{OBS_DIR}/admin_proofs.jsonl` | No | Absolute file path | Uses OBS_DIR-relative default | Treated as string | Implicit | YES |
| `ERROR_EVENTS_LOG` | core.observability_logger | Optional | `{OBS_DIR}/error_events.jsonl` | No | Absolute file path | Uses OBS_DIR-relative default | Treated as string | Implicit | YES |
| `ADMIN_PROOF_CHAT_ID` | core.observability_logger | Optional | `""` | No | Telegram chat ID | Admin proofs not pushed to Telegram | Treated as string | Implicit | YES |
| `ADMIN_PROOF_THREAD_ID` | core.observability_logger | Optional | `""` | No | Telegram thread ID | No thread | Treated as string | Implicit | YES |
| `EVENT_SCHEMA_VERSION` | core.observability_logger | Optional | `"2.0.0"` | No | Semver string | Uses default | Treated as string | Implicit | YES |

---

## 2. CONFIGURATION FILE INVENTORY

| File | Path (repo) | Schema | Loader | Writer | Runtime Consumer | Admin Consumer | Required/Optional | Mutable | Default Behavior | Persistence Req. | Deployment Init Required |
|---|---|---|---|---|---|---|---|---|---|---|---|
| `algo_params.json` | `send/config/algo_params.json` | `send/schema/params_schema.json` | `core.params_loader` | Admin via `admin_commands` | `core.signal_engine` | `admin_commands` | Required | Mutable | If missing, params validation fails; engine uses defaults from strategy_v2 | YES (persistent volume) | Pre-populate with canonical values |
| `channel_config.json` | `send/config/channel_config.json` | Informal (schema_version field) | `core.distribution_router` | Not written at runtime | `core.distribution_router` | `admin_commands` | Required for distribution | Mutable | Falls back to default limits if missing | YES | Pre-populate with channel IDs |
| `admin_settings.json` | `send/config/admin_settings.json` | Informal | `state_store.load_settings` | `admin_commands` | `core.signal_engine` | `admin_commands` | Optional | Mutable | Engine uses hardcoded defaults | YES | Copy from repo or create fresh |
| `admin_permissions.json` | `send/config/admin_permissions.json` | Informal | `core.admin_permissions` | Not written | `core.admin_permissions` | Reference only | Optional | Immutable (config) | Uses hardcoded permission matrix | YES | Deploy as-is |
| `admin_roles.json` | `send/config/admin_roles.json` | Informal | `core.admin_permissions` | Not written | `core.admin_permissions` | Reference only | Optional | Immutable (config) | Uses fallback (no role assignments) | YES | Deploy with owner/admin IDs |
| `active_symbols.json` | `send/config/active_symbols.json` (also `send/state/active_symbols.json`) | Informal | `state_store.load_active_symbols` | `admin_commands` | `core.signal_engine` | `admin_commands` | Required | Mutable | Empty symbol list if missing; no signals generated | YES | Deploy with symbol list |
| `symbols.json` | `send/config/symbols.json` | Informal | Admin reference | Read-only | Not consumed at runtime | Admin reference | Optional | Immutable | Reference only | Optional | Optional |
| `intelligence_settings.json` | `send/config/intelligence_settings.json` | Informal | `tools.strategy_auditor_lib` | Not written | `strategy_auditor_daily` | None | Required for auditor | Immutable | Auditor fails if missing | YES | Deploy as-is |
| `event_schema.json` | `send/schema/event_schema.json` | JSON Schema | `core.observability_logger` | Not written | `core.observability_logger` | None | Required | Immutable | Schema validation skipped if missing | YES (embedded in package) | No init required (in package) |
| `params_schema.json` | `send/schema/params_schema.json` | JSON Schema | `core.params_loader` | Not written | `core.params_loader` | None | Required | Immutable | Params validation fails if missing | YES (embedded in package) | No init required (in package) |

---

## 3. PERSISTENT PATH INVENTORY

| Path Segment | Canonical Env Var | Default (no env var) | Contents | Writer | Persistence Required |
|---|---|---|---|---|---|
| `{base}/state/focus_state.json` | `BINARYBOT_BASE_DIR` | `send/state/focus_state.json` | FSM state per symbol | `state_store` | YES — persistent volume |
| `{base}/state/dist_state.json` | `BINARYBOT_BASE_DIR` | `send/state/dist_state.json` | Distribution tier state | `state_store` | YES |
| `{base}/state/restart_guard.json` | `BINARYBOT_BASE_DIR` | `send/state/restart_guard.json` | Restart history | `restart_guard` | YES |
| `{base}/state/outcomes.json` | `BINARYBOT_BASE_DIR` | `send/state/outcomes.json` | Outcome index | `outcome_service` | YES |
| `{base}/state/trade_journal.json` | `BINARYBOT_BASE_DIR` | `send/state/trade_journal.json` | Trade journal | `state_store` | YES |
| `{base}/outcomes/outcomes.jsonl` | `OUTCOMES_LOG` | `/opt/binarybot/outcomes/outcomes.jsonl` | Outcome records (append-only) | `outcome_service` | YES |
| `{base}/outcomes/open_now_registry.json` | `BINARYBOT_BASE_DIR` | `send/outcomes/open_now_registry.json` | Open trades registry | `outcome_service` | YES |
| `{base}/observability/engine_events.jsonl` | `ENGINE_EVENTS_LOG` | `/opt/binarybot/observability/engine_events.jsonl` | Engine events | `observability_logger` | YES |
| `{base}/observability/distribution_events.jsonl` | `DIST_EVENTS_LOG` | `/opt/binarybot/observability/distribution_events.jsonl` | Distribution events | `observability_logger` | YES |
| `{base}/observability/fsm_events.jsonl` | `FSM_EVENTS_LOG` | `/opt/binarybot/observability/fsm_events.jsonl` | FSM events | `observability_logger` | YES |
| `{base}/observability/admin_proofs.jsonl` | `ADMIN_PROOFS_LOG` | `/opt/binarybot/observability/admin_proofs.jsonl` | Admin proof log | `observability_logger` | YES |
| `{base}/observability/error_events.jsonl` | `ERROR_EVENTS_LOG` | `/opt/binarybot/observability/error_events.jsonl` | Error events | `observability_logger` | YES |
| `{base}/analytics/aggregates.json` | `ANALYTICS_DIR` | `/opt/binarybot/analytics/aggregates.json` | Analytics aggregates | `analytics_engine` | YES |
| `{base}/analytics/research_report.json` | `ANALYTICS_DIR` | `/opt/binarybot/analytics/research_report.json` | Research report | `research_engine` | YES |
| `{base}/snapshots/` | `BINARYBOT_BASE_DIR` | `send/snapshots/` | State snapshots | `snapshot_manager` | YES |

---

## 4. CONFIGURATION DRIFT / MULTIPLE SOURCES OF TRUTH

**FINDING — Path Authority Split (OF-09-002):**
The system has two separate mechanisms for path resolution:
1. `BINARYBOT_BASE_DIR` → used by `storage.base_dir()` → controls state, config, and some path resolution.
2. `OBS_DIR`, `OUTCOMES_LOG`, `ANALYTICS_DIR`, `DIST_EVENTS_LOG`, `FSM_EVENTS_LOG`, `ENGINE_EVENTS_LOG`, `ADMIN_PROOFS_LOG`, `ERROR_EVENTS_LOG` → separate env vars defaulting to `/opt/binarybot/...` paths.

These two mechanisms can produce **split storage roots** at deployment time if only `BINARYBOT_BASE_DIR` is set without the observability-specific vars (or vice versa). For a coherent deployment, both the base dir AND all observability/outcomes/analytics path vars must be consistently configured.

**Consequence:** If only `BINARYBOT_BASE_DIR` is set (e.g., `/data`), state and config files go to `/data/state/`, `/data/config/` — but observability events go to `/opt/binarybot/observability/` (likely missing on Railway) unless OBS_DIR is also set to `/data/observability`.

**Mitigation:** At Railway deployment, set ALL the following env vars consistently:
```
BINARYBOT_BASE_DIR=/data
OBS_DIR=/data/observability
OUTCOMES_LOG=/data/outcomes/outcomes.jsonl
ANALYTICS_DIR=/data/analytics
DIST_EVENTS_LOG=/data/observability/distribution_events.jsonl
FSM_EVENTS_LOG=/data/observability/fsm_events.jsonl
ENGINE_EVENTS_LOG=/data/observability/engine_events.jsonl
ADMIN_PROOFS_LOG=/data/observability/admin_proofs.jsonl
ERROR_EVENTS_LOG=/data/observability/error_events.jsonl
```

---

## 5. RAILWAY VOLUME REQUIREMENTS

One persistent volume is required. Suggested mount path: `/data`

Required subdirectories (auto-created by application on first write):
- `/data/state/` — FSM, distribution, restart guard, outcomes index, trade journal
- `/data/config/` — config files (must be seeded from repository on first deploy)
- `/data/outcomes/` — outcomes.jsonl, open_now_registry.json
- `/data/observability/` — all JSONL event logs
- `/data/analytics/` — analytics and research reports
- `/data/snapshots/` — state snapshots

**Config seeding:** Config files in `send/config/` must be copied to `/data/config/` on first deployment before the process starts, or a start script must handle this.

---

## 6. VERDICT

| Dimension | Verdict | Notes |
|---|---|---|
| Configuration readiness | CONDITIONALLY READY | Config files and schema present; path authority split between BINARYBOT_BASE_DIR and OBS_DIR/OUTCOMES_LOG/ANALYTICS_DIR requires careful env var alignment at deployment |
