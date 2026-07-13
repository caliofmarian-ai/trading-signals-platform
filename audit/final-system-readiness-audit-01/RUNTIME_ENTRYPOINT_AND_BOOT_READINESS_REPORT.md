# RUNTIME_ENTRYPOINT_AND_BOOT_READINESS_REPORT.md

**Audit ID:** final-system-readiness-audit-01  
**Date:** 2026-07-13  
**Branch:** copilot/conduct-final-system-readiness-audit  
**HEAD Commit:** 5aa40f0

---

## 1. RUNTIME ENTRY POINTS

### 1.1 Primary Runtime Entry Point: `send/runtime/system_boot.py`

**Command:** `PYTHONPATH=send python -m send.runtime.system_boot` or `cd send && python runtime/system_boot.py`  
**Entry function:** `start_system()`  
**Called as:** `if __name__ == "__main__": start_system()`

**Startup sequence:**
1. `_load_env_file()` — loads `.env` file from `BINARYBOT_ENV_FILE` or candidate paths (`{base}/.env`, `{base}/config/.env`) before any module that reads env vars at import time.
2. Module imports: `engine_loop`, `telegram_updates`, `distribution_scheduler`, `fsm_runtime`, `distribution_router`, `observability_logger`, `restart_guard`, `snapshot_manager`.
3. `_register_shutdown_hooks()` — registers SIGINT/SIGTERM handlers and `atexit` shutdown.
4. `record_start()` — records startup in restart_guard state file; detects crash loops.
5. `fsm_runtime.load_state()` — loads FSM state; validates; migrates from legacy if needed. **On failure: logs RECOVERY_VALIDATION_FAILED and returns (blocks engine start).**
6. `distribution_router.load_state()` — loads distribution state. **On failure: same block behavior.**
7. Crash-loop check: if `start_info["crash_loop"]` is True, logs CRASH_LOOP_DETECTED and returns (blocks engine start).
8. Starts three daemon threads:
   - `engine_thread` → `start_engine()` (engine_loop.py — ticks every 2s)
   - `telegram_thread` → `poll_updates()` (telegram_updates.py — polls Telegram API)
   - `scheduler_thread` → `scheduler_loop()` (distribution_scheduler.py — daily reset at 08:10 London)
9. Main thread: `while True: time.sleep(60)` — keeps alive.

**Required environment variables:**
- `TELEGRAM_BOT_TOKEN` — required at runtime (Telegram thread will raise RuntimeError if missing; engine and scheduler threads not blocked)
- `BINARYBOT_BASE_DIR` — optional; defaults to `send/` package directory (package-relative). **Must be set to Railway volume for production.**

**Optional environment variables:**
- `BINARYBOT_ENV_FILE` — path to a `.env` file to load before imports
- `OBS_DIR` — observability JSONL path prefix (defaults to `/opt/binarybot/observability` — must be set for Railway)
- `OUTCOMES_LOG` — path to outcomes.jsonl (defaults to `/opt/binarybot/outcomes/outcomes.jsonl` — must be set for Railway)
- `ANALYTICS_DIR` — analytics report directory (defaults to `/opt/binarybot/analytics` — must be set for Railway)
- `ADMIN_CONTROL_CHAT_ID` — Telegram admin group chat ID (defaults to 0 = all admin commands blocked/fail-closed)
- `OWNER_TELEGRAM_ID` — owner Telegram ID for role assignment
- `BOT_ENV`, `SERVICE_NAME`, `BOT_VERSION`, `GIT_SHA` — observability metadata, all optional

**Threads created:** 3 (all daemon — die with main process)  
**Network calls at startup:** None during import. Telegram polling thread will call `api.telegram.org/getUpdates` immediately on start.  
**Graceful shutdown:** SIGTERM/SIGINT triggers `_mark_graceful_shutdown()` → creates snapshot → marks graceful shutdown in restart_guard → `SystemExit(0)`.  
**Restart behavior:** On next start, `record_start()` sees last_shutdown.kind == "graceful" → does NOT count as crash → crash loop counter not incremented.  
**Crash loop behavior:** >3 counted restarts in 60s → `start_system()` returns without starting threads. System effectively dead until manual intervention (crash loop state reset).  
**Health/liveness:** No HTTP health endpoint. No liveness probe. Health inferred from observability JSONL events.

### 1.2 Engine Loop: `send/runtime/engine_loop.py`

**Entry function:** `start_engine()`  
**Called by:** `system_boot.py` in daemon thread  
**Tick interval:** 2 seconds (`ENGINE_TICK_SECONDS = 2`)  
**Work per tick:** `run_once(now_ts)` from `core.signal_engine`  
**Failure behavior:** Exceptions caught, logged as error event, loop continues.  
**Shutdown:** Daemon thread — terminates when main thread exits.

### 1.3 Telegram Polling: `send/runtime/telegram_updates.py`

**Entry function:** `poll_updates()`  
**Called by:** `system_boot.py` in daemon thread  
**Protocol:** Long-polling `getUpdates` (timeout=30s, poll interval 1.5s)  
**Failure mode if token missing:** `RuntimeError("TELEGRAM_BOT_TOKEN missing")` — thread crashes; main process continues (other threads unaffected).  
**Update dispatch:** Commands → `bot_service.handle_admin_command`; VOTE_ callbacks → `outcome_service`; OUTCOME: callbacks → `outcome_service`; retired callbacks → rejection message.

### 1.4 Distribution Scheduler: `send/runtime/distribution_scheduler.py`

**Entry function:** `scheduler_loop()`  
**Called by:** `system_boot.py` in daemon thread  
**Schedule:** Daily reset at 08:10 London time (Europe/London timezone)  
**Work:** `distribution_router` daily reset  
**Failure behavior:** Exceptions caught and logged; loop continues.

### 1.5 Analytics/Research Entry Points

**Daily auditor:**  
- Entry: `PYTHONPATH=send python -m tools.strategy_auditor_daily` or `python send/tools/strategy_auditor_daily.py`
- Dependencies: `send/config/intelligence_settings.json`, observability JSONL files
- Network: none
- Failure: RuntimeError with clear message if settings file missing

**Research engine:** No standalone entry point. Called programmatically from analytics workflows.  
**Analytics engine:** No standalone entry point. Called programmatically.

### 1.6 Admin Command Paths
- All admin commands dispatched through `core.admin_commands.handle_admin_command`
- Requires: ADMIN_CONTROL_CHAT_ID to be non-zero and matching the incoming chat_id
- Commands: /settings, /params, /symbols, /debug, /report, /help, /system, /restart, /strategy (and sub-commands)

---

## 2. BOOT READINESS AUDIT

### 2.1 Core Import Safety
All 15 core production modules tested under `PYTHONPATH=send python -c "__import__('<module>')"`:

| Module | Import Result |
|---|---|
| core.storage | OK |
| core.signal_engine | OK |
| core.strategy_v2 | OK |
| core.fsm_runtime | OK |
| core.distribution_router | OK |
| core.observability_logger | OK |
| core.outcome_service | OK |
| core.admin_permissions | OK |
| core.params_loader | OK |
| core.trade_temporal_telemetry | OK |
| core.analytics_engine | OK |
| intelligence.research_engine | OK |
| state_store.state_store | OK |
| snapshots.snapshot_manager | OK |
| monitoring.restart_guard | OK |

**Result:** No import-time errors. All modules boot-safe.

### 2.2 Import-Time Side Effects
- No import-time network calls detected in any production module.
- No import-time uncontrolled threads detected.
- `observability_logger.py` initializes `_RUN` context at import time (hostname, pid, timestamp) — this is safe module-level state, not a network call.
- `state_store.py` calls `storage.state_path()` and `storage.config_path()` at module load (path resolution only, no I/O).
- Confirmed by `tests/canonical/unit/test_boot_and_market_data.py::test_imports_are_boot_safe` — PASS.

### 2.3 Configuration Loading at Boot
- `params_loader.py`: loads `algo_params.json` lazily on first call; fails clearly with validated error if schema invalid.
- `admin_permissions.py`: loads `admin_roles.json` and `admin_permissions.json` via `lru_cache` on first permission check.
- `distribution_router.py`: loads `channel_config.json` via `load_state()` call in `system_boot.py` startup.
- `fsm_runtime.py`: loads `focus_state.json` via `load_state()` call in `system_boot.py` startup.

### 2.4 Missing-Config Failure Behavior
- Missing `algo_params.json`: `config_path()` raises `StoragePathError` if config directory does not exist; if file missing, `storage.load_json()` returns `{}` (empty default), which then fails params validation.
- Missing `channel_config.json`: `distribution_router._load_channel_config()` tries multiple paths; falls back to hardcoded `/opt/binarybot/config/` paths; if all fail, uses default limits.
- Missing `TELEGRAM_BOT_TOKEN`: Telegram thread raises RuntimeError on first poll attempt.
- Missing `BINARYBOT_BASE_DIR` with non-existent `/opt/binarybot/observability`: observability writes will fail when first event is emitted.

### 2.5 State Initialization and Migration
- On first boot with no state files: `load_json()` returns `{}` default → `state_store` creates default state structures.
- Migration from legacy paths: `state_store.py` detects legacy `focus_state.json` at root level and migrates to `state/focus_state.json`.
- Migration conflict detection: if both legacy and canonical paths have state, `StateConflictError` is raised and system blocks.
- Confirmed by `tests/canonical/persistence/test_state_snapshot_recovery.py` — all 3 tests PASS.

### 2.6 Restart Guard Behavior
- On clean start: `record_start()` creates or updates restart_guard state; counts restart if last shutdown was not graceful.
- On crash loop (>3 counted restarts in 60s): `start_system()` returns without starting engine/telegram/scheduler threads.
- Crash loop detection confirmed by `tests/batch_06/` tests — all PASS.

### 2.7 Repository-Local Production State Creation
- Default storage path is `_PACKAGE_BASE_DIR` (the `send/` directory) if `BINARYBOT_BASE_DIR` is not set.
- At test time, tests use fixtures and isolated paths — no production state written to repository.
- Confirmed by `tests/batch_09/test_batch09_cleanup.py::TestNoCommittedArtifacts` — 5 tests PASS.
- **Deployment requirement:** Set `BINARYBOT_BASE_DIR` to Railway persistent volume. Otherwise state writes go to the `send/` package directory which is ephemeral on Railway.

---

## 3. VERDICT

| Dimension | Verdict | Notes |
|---|---|---|
| Runtime import readiness | READY | All 15 core modules import cleanly; no import-time side effects |
| Runtime boot readiness | CONDITIONALLY READY | Boot sequence coherent; missing BINARYBOT_BASE_DIR + OBS_DIR + OUTCOMES_LOG will cause observability write failures at runtime; requires env var configuration before deployment |
