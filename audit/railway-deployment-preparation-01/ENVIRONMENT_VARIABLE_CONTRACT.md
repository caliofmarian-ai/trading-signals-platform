# ENVIRONMENT_VARIABLE_CONTRACT.md

## Mode-defining variables
| Variable | Required | Secret | Purpose | Missing behavior | Railway location |
|---|---:|---:|---|---|---|
| `BINARYBOT_BASE_DIR` | Yes | No | Absolute persistent-volume root | init/start fail clearly | Variable |
| `SHADOW_MODE` | Yes | No | Must be `true` for Railway shadow deployment | readiness/start fail clearly | Variable |
| `ENABLE_BROKER_EXECUTION` | Yes (`false`) | No | Explicit shadow safety guard | readiness/start fail clearly if true | Variable |
| `ENABLE_TELEGRAM` | Yes | No | Enables optional Telegram polling/publication | defaults safe only if set false | Variable |

## Required for market data readiness
| Variable | Required | Secret | Purpose | Missing behavior | Railway location |
|---|---:|---:|---|---|---|
| `TWELVE_DATA_API_KEY` | Yes | Yes | Twelve Data API credential | readiness/start fail clearly; `market_client` raises before any request | Secret |

## Required only for Telegram-enabled mode
| Variable | Required | Secret | Purpose | Missing behavior | Railway location |
|---|---:|---:|---|---|---|
| `TELEGRAM_BOT_TOKEN` | Yes when `ENABLE_TELEGRAM=true` | Yes | Telegram Bot API credential | readiness/start fail clearly; runtime skips Telegram when disabled | Secret |
| `FREE_CHANNEL_ID` | Optional override | No | Free tier target channel | falls back to seeded config | Variable |
| `BASIC_CHANNEL_ID` | Optional override | No | Basic tier target channel | falls back to seeded config | Variable |
| `PRO_CHANNEL_ID` | Optional override | No | Pro tier target channel | falls back to seeded config | Variable |
| `ELITE_CHANNEL_ID` | Required for outcome voting; optional for boot | No | Elite tier / outcome-vote context | outcome voting unavailable if missing | Variable |
| `ADMIN_SUPERGROUP_ID` / `ADMIN_GROUP_ID` | Optional override | No | Admin group routing | admin routing falls back to config/fail-closed | Variable |
| `SIGNALS_LIVE_TOPIC_ID` | Optional override | No | Admin thread routing | admin topic routing falls back to config | Variable |
| `COMMUNITY_FEEDBACK_SALT` | Required for outcome voting | Yes | Outcome pseudonymization salt (32+ chars) | outcome voting unavailable if missing | Secret |

## Optional metadata and control variables
- `SERVICE_NAME`, `BOT_ENV`, `BOT_VERSION`, `GIT_SHA`, `RUN_ID`
- `OWNER_TELEGRAM_ID`, `ADMIN_CONTROL_CHAT_ID`, `ADMIN_CONTROL_THREAD_ID`
- `FREE_LIMIT`, `BASIC_LIMIT`, `PRO_LIMIT`, `ELITE_LIMIT`
- `ADMIN_PROOF_CHAT_ID`, `ADMIN_PROOF_THREAD_ID`, `EVENT_SCHEMA_VERSION`
- `BINARYBOT_ENV_FILE`

## Optional path overrides
These are auto-derived from `BINARYBOT_BASE_DIR` by `scripts.railway_common.apply_path_contract()` when absent:
- `OBS_DIR`
- `OUTCOMES_LOG`
- `ANALYTICS_DIR`
- `DIST_EVENTS_LOG`
- `FSM_EVENTS_LOG`
- `ENGINE_EVENTS_LOG`
- `ADMIN_PROOFS_LOG`
- `ERROR_EVENTS_LOG`
- `ALGO_PARAMS_PATH`
- `ADMIN_ROLES_CONFIG`
- `ADMIN_PERMISSIONS_CONFIG`
- `STRATEGY_AUDITOR_SETTINGS`

## `.env.example`
- Root file: `/.env.example`
- Contains only safe placeholders.
- No real secrets, tokens, or live identifiers are included.
