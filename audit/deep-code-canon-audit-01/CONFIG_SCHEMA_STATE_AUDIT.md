# CONFIG_SCHEMA_STATE_AUDIT

## 1. Configuration sources
- Environment-driven:
  - `TWELVE_DATA_API_KEY` (`runtime/market_client.py:5-18`)
  - `TELEGRAM_BOT_TOKEN` (`core/telegram_publisher.py:9-14`, `runtime/telegram_updates.py:16-23`, `core/outcome_service.py:21-23`)
  - admin/role overrides (`admin_permissions.py:173-181`, `distribution_router.py:102-145`, `bot_service.py:31-39`)
- File-driven:
  - `config/algo_params.json`, `channel_config.json`, `admin_roles.json`, `admin_permissions.json`, `admin_settings.json`, `active_symbols.json`, `symbols.json`, `intelligence_settings.json`
- State-driven:
  - `state/focus_state.json`, `dist_state.json`, `restart_guard.json`, `outcomes.json`, `event_store.json`, `trade_journal.json`, plus `outcomes/open_now_registry.json`

## 2. `params_schema.json` vs `algo_params.json` vs runtime readers
### Confirmed mismatch
| Contract | Keys present |
|---|---|
| `schema/params_schema.json` | `strategy_v2`, `buffer_multipliers`, `expiry_limits_minutes`, `score_thresholds` |
| `config/algo_params.json` | `thresholds`, `weights`, `expiry`, `buffer`, `gates` |
| `core/params_loader.py` required keys | `algo_version`, `thresholds`, `weights`, `expiry`, `buffer`, `gates` |
| `core/strategy_v2.py` runtime reads | `strategy_v2`, `score_thresholds`, `expiry_limits_minutes`, `buffer_multipliers`, `spike_filters` |

### Consequence
- `params_loader` and `admin_commands` validate/mutate one shape.
- `strategy_v2` executes another shape and falls back to hardcoded defaults.
- `algo_params.json` therefore does not drive live thresholds/buffer multipliers as canon intends.

## 3. `params_loader.py` validation logic
- Strengths:
  - Required top-level and nested key enforcement (`params_loader.py:24-39,73-99`).
  - Threshold ordering and range checks (`110-126`).
  - Expiry and buffer sanity checks (`129-158`).
  - Secret-like key guardrail (`160-168`).
- Gaps:
  - No JSON-schema validation against `schema/params_schema.json`.
  - Not invoked by `admin_commands.py` before writes.
  - Comments cite superseded `PARAMS_REFERENCE.md` rather than active canon.

## 4. `channel_config.json` audit
### File shape
`channel_config.json:4-21` stores:
- channel IDs
- admin group/topic
- tier limits
- reset timezone/time
- Telegram formatting hints

### Runtime loader behavior
`distribution_router.load_config()` (`distribution_router.py:91-145`):
- reads channel IDs from file if present
- ignores file `ADMIN_GROUP_ID` and `SIGNALS_LIVE_TOPIC_ID`
- ignores file `FREE_LIMIT` / `BASIC_LIMIT` / `PRO_LIMIT` / `ELITE_LIMIT`
- ignores file `TZ`, `RESET_TIME`, `PARSE_MODE`, `DISABLE_WEB_PREVIEW`
- instead uses env/default values for admin and limits

### Risk
- File is not the effective source of truth required by canon.

## 5. Admin role/permission config audit
- `admin_roles.json` is loaded by `admin_permissions.py` and optionally amended by env `OWNER_TELEGRAM_ID` (`admin_permissions.py:149-181`).
- `admin_permissions.json` is never read by runtime code.
- Result: split config files exist, but only one is effective.

## 6. `admin_settings.json` audit
- File defines min/max thresholds, SR, spike limits, feature flags, engine monitoring.
- `admin_commands.py` only reads `engine_tick_interval` for status display (`184-192`).
- Actual command validation uses hardcoded numeric ranges (`346-370`) rather than `admin_settings.json`.
- Risk: documented admin limits are not enforced as configuration.

## 7. Active symbols and symbols files
- `config/active_symbols.json` and `config/symbols.json` both store `forex`/`crypto` arrays.
- `signal_engine._load_active_symbols()` accepts either `{symbols:[...]}` or bucketed `{forex,crypto}` (`signal_engine.py:70-94`).
- `admin_commands._save_active_symbols()` may preserve first bucket or save a flat list, depending on existing shape (`admin_commands.py:123-139`).
- `bot_service` separately expects `/opt/binarybot/symbols.json` and `/opt/binarybot/active_symbols.json` in root paths (`bot_service.py:21-23,104-123`).
- Risk: file shape and path drift can silently change runtime symbol coverage.

## 8. State schema audit
### `state/focus_state.json`
- Matches `fsm_runtime` default fields, but version is `1.0` not `1.0.0`.
- No release/cooldown completion semantics visible in state mutations.

### `state/dist_state.json`
- Active file uses `last_reset_london_date` and flat `dedup` key map.
- `state_store.default_dist_state()` instead uses `last_reset_epoch` and comments suggest nested dedup structure.

### `state/restart_guard.json`
- Active file only stores `starts` and `last_updated_ts` in sample; code expects `version`, `window_seconds`, `max_restarts` as well (`restart_guard.py:26-33`).

### `state/event_store.json`
- Empty array; not used by active logger.

### `outcomes/open_now_registry.json`
- Valid registry entries mirror `outcome_service.register_open_now()` data model.

## 9. Validation bypasses and unsafe fallbacks
- `admin_commands._safe_write_json()` is non-atomic, unlocked (`53-56`).
- `signal_engine.update_symbol_replacement_score()` writes state with `os.replace` but without `fsync` (`34-38`).
- `health_check.py`, `aggregates_writer.py`, `snapshot_manager.py`, `trade_journal.py` all perform direct file writes outside `core.storage`.
- `bot_service.in_admin_context()` fail-opens if admin chat env var is unset (`79-82`).
- `distribution_router._limit()` accepts magic strings `UNLIMITED|NONE|INF` without audit (`126-136`).

## 10. Migration / consolidation risks
- Two state abstractions (`core/*` and `state_store/*`) define different paths and defaults.
- Two admin/control abstractions (`admin_commands/*` and `bot_service.py`/`legacy/bot_control.py`) mutate different files.
- Two outcome stores (`outcomes/*.jsonl` and `state/outcomes.json`) exist.

## 11. Priority findings
1. **CRITICAL**: parameter schema split means live strategy does not follow operator-visible config.
2. **HIGH**: channel config file is not authoritative at runtime.
3. **HIGH**: admin writes are unsafe and bypass canonical validation.
4. **HIGH**: state schemas drift across active modules and `state_store` facade.
