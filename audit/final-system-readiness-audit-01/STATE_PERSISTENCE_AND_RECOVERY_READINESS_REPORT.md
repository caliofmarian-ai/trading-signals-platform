# STATE_PERSISTENCE_AND_RECOVERY_READINESS_REPORT.md

**Audit ID:** final-system-readiness-audit-01  
**Date:** 2026-07-13  
**Branch:** copilot/conduct-final-system-readiness-audit  
**HEAD Commit:** 5aa40f0

---

## 1. STATE/PERSISTENCE LOCATION INVENTORY

| Location | Canonical Path | Reader | Writer | Atomicity | Locking | Schema Validation | Corruption Behavior | Missing-File Behavior | Migration | Restart Behavior | Snapshot Coverage |
|---|---|---|---|---|---|---|---|---|---|---|---|
| FSM state | `{base}/state/focus_state.json` | `state_store.load_fsm_state` | `state_store.save_fsm_state` | Atomic (tmp+replace) | `with_lock("focus_state")` | `validate_fsm_state()` | Returns `{}` default (no auto-overwrite) | Creates default state | YES — migrates from root-level | YES — loads on restart | YES |
| Distribution state | `{base}/state/dist_state.json` | `state_store.load_dist_state` | `state_store.save_dist_state` | Atomic | `with_lock("dist_state")` | `validate_dist_state()` | Returns `{}` default | Creates default state | YES | YES — loads on restart | YES |
| Restart guard | `{base}/state/restart_guard.json` | `state_store.load_restart_guard_state` | `state_store.save_restart_guard_state` | Atomic | `with_lock("restart_guard")` | Implicit (dict fields) | Returns `{}` | Creates default state | NO (no legacy version) | YES — `record_start()` reads and updates | NO |
| Outcomes index | `{base}/state/outcomes.json` | `outcome_service._load_outcomes_index` | `outcome_service._save_outcomes_index` | Atomic | Implicit (single writer) | Implicit | Returns `{}` default | Returns `{}` | NO | YES — loads on first vote | NO |
| Trade journal | `{base}/state/trade_journal.json` | `state_store` | `state_store` | Atomic | YES | Implicit | Returns `{}` | Returns `{}` | NO | YES | NO |
| Open trades registry | `{base}/outcomes/open_now_registry.json` | `outcome_service._load_registry` | `outcome_service._save_registry` | Atomic | Implicit | Implicit | Returns `{}` | Returns `{}` | NO | YES | NO |
| Open trades telemetry | `{base}/observability/open_trades_registry.json` | `trade_temporal_telemetry._load_registry` | `trade_temporal_telemetry._save_registry` | Atomic | Implicit | Implicit | Returns default | Returns default | NO | YES | NO |
| Outcomes JSONL | `{base}/outcomes/outcomes.jsonl` | `analytics_engine`, `research_engine` | `outcome_service` | Append-only | Implicit | None (parsed at read) | `jsonl_parser` isolates malformed | Empty result | NO | Not loaded at restart | NO |
| Snapshots | `{base}/snapshots/*.json` | `snapshot_manager` | `snapshot_manager` | Atomic | None | `_validate_snapshot_payload()` | `SnapshotValidationError` | Returns None | NO | On request via restore | FULL (focus+dist) |

---

## 2. LIVE WRITE AUTHORITY — CANONICAL SEGMENTED PATHS

**BATCH-09 verified:** All live writes use canonical segmented paths under `storage.root_path()` or `state_store` helpers.

Evidence:
- `core.outcome_service` uses `storage.root_path("outcomes", ...)` — confirmed by `tests/batch_09/test_batch09_cleanup.py::TestSegmentedPathIsolation::test_outcomes_segment_is_canonical_write_authority` — PASS.
- `core.admin_commands` uses `_storage.root_path(...)` — confirmed by `tests/batch_09/test_batch09_cleanup.py::TestAdminCommandsPathConvergence` — PASS.
- `state_store.FOCUS_STATE_PATH` = `storage.state_path("focus_state.json")` — confirmed path under state segment.
- `state_store.DIST_STATE_PATH` = `storage.state_path("dist_state.json")` — confirmed.
- `observability_logger` uses `OBS_DIR` env var (defaults to `/opt/binarybot/observability` — env-overridable, not a hardcoded unconditional write).
- `bot_service.OUTCOMES_PATH` = `/opt/binarybot/state/outcomes.json` — RESIDUAL attribute; `bot_service` does NOT write to this path (BATCH-04/05 retirement). It is a module attribute retained for backwards compatibility documentation only.

**Confirmed:** No active hardcoded unconditional writes to `/opt/binarybot/` in production write paths.

---

## 3. `/opt/binarybot` OCCURRENCE CLASSIFICATION

| File | Pattern | Classification |
|---|---|---|
| `send/core/fsm_runtime.py` | Header comment `# /opt/binarybot/core/fsm_runtime.py` | Documentation comment only — DEAD REFERENCE |
| `send/core/observability_logger.py` | `OBS_DIR = os.getenv("OBS_DIR", "/opt/binarybot/observability")` | ENVIRONMENT-OVERRIDABLE DEFAULT — not a hardcoded write |
| `send/core/observability_logger.py` | `OUTCOMES_LOG = os.getenv("OUTCOMES_LOG", os.path.join("/opt/binarybot/outcomes", ...))` | ENVIRONMENT-OVERRIDABLE DEFAULT |
| `send/core/telegram_publisher.py` | Header comment only | DEAD REFERENCE (documentation) |
| `send/core/params_loader.py` | Header comment + `DEFAULT_PARAMS_PATH = os.getenv("ALGO_PARAMS_PATH", "/opt/binarybot/config/algo_params.json")` | ENVIRONMENT-OVERRIDABLE DEFAULT |
| `send/core/distribution_router.py` | Header comment + fallback in `CHANNEL_CONFIG_PATHS` list | MIGRATION-ONLY COMPATIBILITY PATH (last resort in list) |
| `send/core/admin_permissions.py` | `os.getenv("ADMIN_ROLES_CONFIG", "/opt/binarybot/config/admin_roles.json")` | ENVIRONMENT-OVERRIDABLE DEFAULT |
| `send/core/admin_permissions.py` | `os.getenv("ADMIN_PERMISSIONS_CONFIG", "/opt/binarybot/config/admin_permissions.json")` | ENVIRONMENT-OVERRIDABLE DEFAULT |
| `send/core/candle_adapter.py` | Header comment only | DEAD REFERENCE |
| `send/core/bot_service.py` | `OUTCOMES_PATH = "/opt/binarybot/state/outcomes.json"` | MODULE ATTRIBUTE — bot_service does NOT write to this path (retired BATCH-04/05); DOCUMENTATION REMNANT |
| `send/core/storage.py` | Header comment only | DEAD REFERENCE |
| `send/core/analytics_engine.py` | `_OBS_DIR = os.getenv("OBS_DIR", "/opt/binarybot/observability")` | ENVIRONMENT-OVERRIDABLE DEFAULT |
| `send/core/analytics_engine.py` | `_OUTCOMES_LOG = os.getenv("OUTCOMES_LOG", ...)` | ENVIRONMENT-OVERRIDABLE DEFAULT |
| `send/core/analytics_engine.py` | `_ANALYTICS_BASE = os.getenv("ANALYTICS_DIR", "/opt/binarybot/analytics")` | ENVIRONMENT-OVERRIDABLE DEFAULT |
| `send/core/signal_engine.py` | Header comment only | DEAD REFERENCE |
| `send/core/strategy_v2.py` | Header comment only | DEAD REFERENCE |
| `send/intelligence/risk_monitor.py` | Header comment only | DEAD REFERENCE |
| `send/intelligence/strategy_optimizer.py` | Header comment only | DEAD REFERENCE |
| `send/intelligence/report_loader.py` | `_ANALYTICS_BASE = os.getenv("ANALYTICS_DIR", "/opt/binarybot/analytics")` | ENVIRONMENT-OVERRIDABLE DEFAULT |
| `send/intelligence/adaptive_params.py` | Header comment only | DEAD REFERENCE |
| `send/intelligence/research_engine.py` | Header comment + env-var defaults | ENVIRONMENT-OVERRIDABLE DEFAULT |

**Summary:** 
- ACTIVE LIVE PATHS: 0 (no unconditional hardcoded writes)
- ENVIRONMENT-OVERRIDABLE DEFAULTS: 10 (all overridable via env vars)
- DOCUMENTATION/HEADER COMMENTS: 9 (no runtime impact)
- MODULE ATTRIBUTE REMNANT (no write): 1 (`bot_service.OUTCOMES_PATH`)
- MIGRATION COMPATIBILITY: 1 (`distribution_router` last-resort fallback)

---

## 4. ATOMICITY AND LOCKING ASSESSMENT

- `storage.save_json_atomic()`: writes to temp file → fsync → `os.replace()` → fsync directory. Atomic on POSIX/Linux filesystems.
- `storage.with_lock()`: cross-process lockfile using `O_CREAT | O_EXCL`. Times out after 10 seconds. Works for single-host deployment.
- `storage.append_jsonl()`: append-only; flush+fsync per write. No lock — relies on OS-level atomicity for single-writer assumption.
- Snapshot creation: atomic write of snapshot JSON; non-atomic relative to the state files being snapshotted (race window exists on shutdown).

**Locking gap:** `outcomes.jsonl` uses append-only without explicit cross-process lock. If multiple writers exist (unlikely in current architecture — single process), there is a potential interleave risk. Current architecture has one outcome writer (`outcome_service`), so this is not a live risk.

---

## 5. SNAPSHOT/RESTORE

- `snapshot_manager.create_snapshot()`: reads FSM state and distribution state; validates; writes atomic JSON to `{base}/snapshots/` with timestamp filename.
- `snapshot_manager.restore_snapshot()`: reads latest snapshot; validates schema version; validates state contents; atomically writes FSM and dist state files. Rollback on failed write (restores pre-restore state).
- Schema version: `1.0.0` — must match `SNAPSHOT_SCHEMA_VERSION`.
- Confirmed by `tests/canonical/persistence/test_state_snapshot_recovery.py::test_snapshot_restore_rolls_back_on_failed_write` — PASS.

---

## 6. VERDICT

| Dimension | Verdict | Notes |
|---|---|---|
| State and persistence readiness | READY | Atomic writes, cross-process locks, schema validation, corruption recovery all implemented and tested |
| FSM/watchlist lifecycle readiness | READY | Load, validate, migrate, save, snapshot all implemented; crash-loop detection active |
| Restart/recovery readiness | READY | Restart guard, graceful shutdown marker, crash-loop detection, state migration all verified |
| Snapshot/restore readiness | READY | Create and restore with schema validation and rollback-on-failure verified |
