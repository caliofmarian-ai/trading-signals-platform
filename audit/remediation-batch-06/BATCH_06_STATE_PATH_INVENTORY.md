# BATCH_06_STATE_PATH_INVENTORY

- Owner decision applied: OWNER-003 = A
- Prior decision applied: OWNER-004 (do not create `scan_scheduler`; refactor to canonical FSM access)
- Findings addressed: GAP-002, GAP-009, GAP-014, GAP-018

## Before-state inventory

| Logical domain | Before live/read paths | Before writers/readers | Canonical owner | Persistence / atomicity before | Restart / snapshot behavior before | Duplication risk before | BATCH-06 canonical path |
|---|---|---|---|---|---|---|---|
| FSM runtime state | `send/state/focus_state.json`; legacy code also assumed `/opt/binarybot/state/focus_state.json`; compatibility root path family effectively `/opt/binarybot/focus_state.json` through `state_store` drift | Writers/readers: `core/fsm_runtime.py`, `core/signal_engine.py:update_symbol_replacement_score()`, `snapshots/snapshot_manager.py` | `core/fsm_runtime.py` via `state_store` | Mixed: direct `storage.save_json_atomic`, one broken manual `os.replace`, no shared validation contract | Restored by ad-hoc load; no release/cooldown lifecycle; snapshot used raw file copy | HIGH — duplicate path family and direct file bypass | `state/focus_state.json` only for live writes; optional legacy root read only for controlled migration |
| Distribution route state | `send/state/dist_state.json`; hardcoded `/opt/binarybot/state/dist_state.json`; root-level `/opt/binarybot/dist_state.json` compatibility drift in `state_store` | Writers/readers: `core/distribution_router.py`, `snapshots/snapshot_manager.py`, `state_store/state_store.py` | Distribution state owner (`core/distribution_router.py` through `state_store`) | Atomic in router, conflicting schema/defaults in `state_store` | Restored by raw file load; snapshot copied raw JSON | MEDIUM — same domain had multiple schema/path definitions | `state/dist_state.json` only for live writes; optional legacy root read only for migration |
| Restart guard state | `send/state/restart_guard.json`; hardcoded `/opt/binarybot/state/restart_guard.json`; legacy root family `/opt/binarybot/restart_guard.json` | Writers/readers: `monitoring/restart_guard.py`, `runtime/system_boot.py` | `monitoring/restart_guard.py` via `state_store` | Atomic writes, but boot called `record_start()` twice and state schema was under-specified | Restart detection double-counted; no graceful-shutdown marker; no snapshot integration | HIGH — incorrect semantics plus path drift | `state/restart_guard.json` only for live writes; optional legacy root read only for migration |
| Active symbols config | `send/config/active_symbols.json`; `state_store` previously pointed to `/opt/binarybot/active_symbols.json` | Readers: `core/signal_engine.py`; writers: `core/admin_commands.py`; stale alternate path in `state_store` | Config/state owner (config layer) | Reader side had no migration contract | Restart-safe only because config file is static-ish | MEDIUM — root-level compatibility path existed in code | `config/active_symbols.json` only; optional legacy root read only for migration |
| Runtime settings / buffer mode compatibility | `core/signal_engine.py` used `config/settings.json`; `state_store` used root `/opt/binarybot/settings.json`; canonical admin settings already lived at `config/admin_settings.json` | Reader: `core/signal_engine.py`; readers/writers for admin settings: `core/admin_commands.py` | Config layer | No shared validator; missing file silently defaulted | Restart-safe only via default fallback | MEDIUM — split between nonexistent `settings.json`, root compatibility path, and `admin_settings.json` | `config/admin_settings.json` with optional root `settings.json` migration shim |
| Snapshots | `send/snapshots/snapshot_*.json` under runtime root; raw JSON copy/restore | `snapshots/snapshot_manager.py`; shutdown/restore flows | `snapshots/snapshot_manager.py` | Create was non-atomic; restore wrote files directly without rollback | Invalid snapshot could overwrite current files; no schema/version validation | HIGH — partial restore/write risk | `snapshots/snapshot_<ts>.json` written atomically, validated before restore |

## Root-level mutable compatibility paths located during re-inspection

These were the live legacy compatibility paths discovered in code before BATCH-06 and are now treated as migration-only sources:

- `/opt/binarybot/focus_state.json`
- `/opt/binarybot/dist_state.json`
- `/opt/binarybot/restart_guard.json`
- `/opt/binarybot/active_symbols.json`
- `/opt/binarybot/settings.json`

## Active status after BATCH-06

- Live reads/writes now converge on segmented canonical targets under `config/`, `state/`, and `snapshots/`.
- Legacy root-level compatibility paths are **read-only migration shims**.
- Legacy compatibility paths are never written after successful migration.
- Dual-state conflicts fail clearly; identical dual-state files are accepted but normalized onto the segmented canonical target.
