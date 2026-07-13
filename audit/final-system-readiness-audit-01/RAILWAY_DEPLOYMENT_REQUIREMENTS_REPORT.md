# RAILWAY_DEPLOYMENT_REQUIREMENTS_REPORT.md

**Audit ID:** final-system-readiness-audit-01  
**Date:** 2026-07-13  
**Branch:** copilot/conduct-final-system-readiness-audit  
**HEAD Commit:** 5aa40f0

---

## NOTE: This report documents requirements only. No Railway configuration files are created. No deployment is performed.

---

## 1. PROCESS START COMMAND

**Primary runtime process:**
```
cd /app/send && python runtime/system_boot.py
```
or equivalently:
```
PYTHONPATH=/app/send python /app/send/runtime/system_boot.py
```

**Daily auditor (separate scheduled process):**
```
PYTHONPATH=/app/send python /app/send/tools/strategy_auditor_daily.py
```

---

## 2. PYTHON VERSION / RUNTIME

- Required: Python 3.12.x (tested with 3.12.3)
- ZoneInfo module required (standard library in Python 3.9+)
- All dependencies from `requirements-test.txt` / implied by source imports

**Dependencies required at runtime:**
- `requests` — HTTP client for Telegram and TwelveData
- `zoneinfo` — standard library (Python 3.9+)
- All stdlib modules used (json, os, threading, signal, time, hashlib, uuid, socket, datetime, dataclasses, pathlib, tempfile, math, typing, contextlib)

**No third-party ML/data science dependencies detected in production code.**

---

## 3. DEPENDENCY INSTALLATION

```
pip install requests
```

Or use `requirements-test.txt` which includes `requests` among other packages.

A minimal `requirements.txt` for production should be created during deployment preparation (not in this audit scope).

---

## 4. REQUIRED ENVIRONMENT VARIABLES (Secrets)

| Variable | Value Source | Railway Secret? |
|---|---|---|
| `TELEGRAM_BOT_TOKEN` | Telegram BotFather | YES — Railway Secret |
| `TWELVE_DATA_API_KEY` | TwelveData account | YES — Railway Secret |
| `COMMUNITY_FEEDBACK_SALT` | Generate random string | YES — Railway Secret |

---

## 5. REQUIRED ENVIRONMENT VARIABLES (Configuration)

| Variable | Example Value | Railway Variable |
|---|---|---|
| `BINARYBOT_BASE_DIR` | `/data` | YES |
| `OBS_DIR` | `/data/observability` | YES |
| `OUTCOMES_LOG` | `/data/outcomes/outcomes.jsonl` | YES |
| `ANALYTICS_DIR` | `/data/analytics` | YES |
| `DIST_EVENTS_LOG` | `/data/observability/distribution_events.jsonl` | YES |
| `FSM_EVENTS_LOG` | `/data/observability/fsm_events.jsonl` | YES |
| `ENGINE_EVENTS_LOG` | `/data/observability/engine_events.jsonl` | YES |
| `ADMIN_PROOFS_LOG` | `/data/observability/admin_proofs.jsonl` | YES |
| `ERROR_EVENTS_LOG` | `/data/observability/error_events.jsonl` | YES |
| `OWNER_TELEGRAM_ID` | Telegram user ID of owner | YES |
| `ADMIN_CONTROL_CHAT_ID` | Telegram chat ID of admin group | YES |
| `ADMIN_CONTROL_THREAD_ID` | Thread ID within admin group (0 if not threaded) | Optional |
| `ELITE_CHANNEL_ID` | Telegram ELITE channel ID (for outcome voting) | YES |
| `BOT_ENV` | `prod` | YES |
| `SERVICE_NAME` | `binarybot` | YES |
| `BOT_VERSION` | Release version string | Optional |
| `GIT_SHA` | Commit SHA | Optional |

---

## 6. PERSISTENT VOLUME REQUIREMENTS

**One persistent volume required.** Suggested Railway volume name: `binarybot-data`.  
**Mount path:** `/data`

**Volume structure (auto-created by application except config/):**
```
/data/
  config/          ← MUST BE SEEDED on first deploy (copy from send/config/)
    algo_params.json
    channel_config.json
    admin_settings.json
    admin_permissions.json
    admin_roles.json       ← must be updated with real Telegram user IDs
    active_symbols.json
    symbols.json
    intelligence_settings.json
  state/           ← auto-created on first boot
    focus_state.json
    dist_state.json
    restart_guard.json
    outcomes.json
    trade_journal.json
  outcomes/        ← auto-created on first write
    outcomes.jsonl
    open_now_registry.json
  observability/   ← auto-created on first write
    engine_events.jsonl
    fsm_events.jsonl
    distribution_events.jsonl
    admin_proofs.jsonl
    error_events.jsonl
  analytics/       ← auto-created by analytics_engine
    aggregates.json
    research_report.json
  snapshots/       ← auto-created by snapshot_manager
```

**Config seeding requirement:** The config directory must be populated with config files before the process starts on first deploy. This is a deployment-time procedure (copy from repository to volume).

---

## 7. INITIALIZATION / MIGRATION COMMANDS

**First deployment only:**
1. Copy `send/config/` contents to `/data/config/`
2. Update `admin_roles.json` with real Telegram user IDs
3. Verify `channel_config.json` has correct channel IDs (already committed)

**Migration:** Handled automatically by `state_store` on first boot (legacy path migration).

---

## 8. PROCESS COUNT

- 1 main Python process
- 3 daemon threads within main process (engine_loop, telegram_updates, distribution_scheduler)
- 1 optional separate process for daily auditor (scheduled)

---

## 9. RESTART POLICY

- Railway's automatic restart policy is compatible with the system's restart guard.
- The restart guard detects crash loops (>3 counted restarts in 60s) and blocks further engine starts.
- `SIGTERM` is handled gracefully: snapshot created, restart guard marked as graceful, clean exit.
- Recommendation: Railway restart policy = `always` or `on-failure`.

---

## 10. HEALTH CHECK / LIVENESS

- **No HTTP health endpoint currently exists.**
- Liveness must be inferred from observability JSONL event recency.
- Railway TCP health checks: not applicable (no inbound server).
- **Recommendation:** Create a minimal health check file writer (writes a timestamp to `/data/health.json` every N seconds) as a lightweight liveness signal. This is a future enhancement, not a current blocker.

---

## 11. LOGGING

- All structured events written to JSONL files on persistent volume.
- `print()` / `traceback.print_exc()` used in `strategy_auditor_daily.py` — goes to Railway stdout.
- No centralized log shipper required; JSONL files accessible via Railway volume.

---

## 12. GRACEFUL SHUTDOWN

- `SIGTERM` → `_handle_shutdown_signal()` → snapshot → mark graceful shutdown → `SystemExit(0)`.
- Daemon threads terminate when main process exits.
- Railway stop: sends SIGTERM → graceful shutdown within typical Railway grace period (10-30s).

---

## 13. STARTUP ORDERING

No external startup dependencies. The process is self-contained once environment is configured.

**Order:**
1. `_load_env_file()` — env vars loaded
2. Module imports
3. `record_start()` — restart guard state updated
4. `fsm_runtime.load_state()` — state loaded and validated
5. `distribution_router.load_state()` — distribution state loaded
6. Crash-loop check
7. Thread start: engine_loop, telegram_updates, distribution_scheduler

---

## 14. SCHEDULED JOBS

- `distribution_scheduler` (inline, thread): daily reset at 08:10 London. No external scheduler needed.
- `strategy_auditor_daily`: must be scheduled externally (Railway cron or second process). Daily execution recommended at 09:00 London time.

---

## 15. TELEGRAM POLLING / WEBHOOK ASSUMPTIONS

- Current implementation: **long-polling only** (`getUpdates` with timeout=30s).
- No webhook support implemented.
- Railway is compatible with long-polling (outbound HTTPS only, no inbound port required for bot updates).

---

## 16. FILESYSTEM PERSISTENCE ASSUMPTIONS

- All persistence via local filesystem on persistent volume.
- No in-memory-only state (all critical state persisted).
- Assumption: persistent volume survives Railway redeployments.

---

## 17. IS REPOSITORY EVIDENCE SUFFICIENT TO CREATE A DEPLOYMENT PLAN?

**YES.** The repository contains sufficient evidence to create a complete Railway deployment plan:
- Process start command is deterministic.
- Required env vars are enumerated.
- Persistent path structure is known.
- Config seeding requirements are clear.
- Restart behavior is documented and implemented.
- Graceful shutdown is implemented.

---

## 18. VERDICT

| Dimension | Verdict | Notes |
|---|---|---|
| Railway deployment readiness | CONDITIONALLY READY | All code complete; requires env var configuration, persistent volume setup, config seeding, and credential provisioning. No HTTP health endpoint exists (recommendation for future). |
