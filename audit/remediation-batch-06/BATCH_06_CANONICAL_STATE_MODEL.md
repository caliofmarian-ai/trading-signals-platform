# BATCH_06_CANONICAL_STATE_MODEL

- Owner decision applied: OWNER-003 = A
- Prior decision applied: OWNER-004

## Canonical segmented model adopted in BATCH-06

### Live mutable authorities

| Domain | Canonical live path | Live writer |
|---|---|---|
| FSM state | `state/focus_state.json` | `state_store.save_fsm_state()` via `core.fsm_runtime` |
| Distribution state | `state/dist_state.json` | `state_store.save_dist_state()` via `core/distribution_router` |
| Restart guard state | `state/restart_guard.json` | `state_store.save_restart_guard_state()` via `monitoring.restart_guard` |
| Active symbols config | `config/active_symbols.json` | existing config writers (BATCH-05 path preserved) |
| Runtime settings compatibility | `config/admin_settings.json` | existing admin settings writer path preserved |
| Snapshots | `snapshots/snapshot_<ts>.json` | `snapshots/snapshot_manager.create_snapshot()` |

## Single-authority rules now enforced

1. Each BATCH-06 mutable artifact has one canonical segmented write path.
2. Root-level compatibility paths are migration sources only.
3. `state_store.state_store` is the shared validation and migration layer for FSM, distribution, restart, active-symbol, and runtime-settings state.
4. `core.fsm_runtime`, `core.distribution_router`, `monitoring.restart_guard`, and `snapshots.snapshot_manager` now share the same path/schema lifecycle contract.
5. No BATCH-06 live write updates any root-level compatibility file.

## Canonical lifecycle properties

- JSON state is validated before use.
- Invalid canonical JSON is rejected clearly.
- Missing optional state initializes from canonical defaults.
- Identical dual-state canonical+legacy files are accepted and normalized.
- Conflicting dual-state files fail clearly.
- Writes remain atomic through `core.storage.save_json_atomic()`.
- Snapshots are written atomically and validated before restore.
