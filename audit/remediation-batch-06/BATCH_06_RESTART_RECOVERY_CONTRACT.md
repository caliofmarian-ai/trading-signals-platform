# BATCH_06_RESTART_RECOVERY_CONTRACT

- Owner decision applied: OWNER-003 = A
- Findings addressed: GAP-009, GAP-018

## Restart-guard contract after BATCH-06

1. `record_start()` is the only counter-mutating startup call.
2. `should_freeze()` is read-only and no longer records a second start.
3. Restart state persists under `state/restart_guard.json`.
4. `last_shutdown.kind` distinguishes `graceful` from `running` / `unknown`.
5. A previous graceful shutdown does not increment the crash-loop counter on the next boot.
6. A previous `running` / `unknown` shutdown counts as recovery-required restart evidence.
7. Corrupt restart-guard JSON fails safely via explicit validation error.

## Boot / recovery contract after BATCH-06

`runtime.system_boot.start_system()` now performs:

1. shutdown-hook registration
2. single startup recording
3. `recovery_started` event emission
4. FSM and distribution state validation through shared segmented-state loaders
5. crash-loop gating from the single recorded startup result
6. `recovery_completed` event emission with `HEALTHY`, `DEGRADED_SAFE`, or `UNSAFE_BLOCKED`
7. engine activation only after state validation and freeze checks pass

## Snapshot contract after BATCH-06

- `create_snapshot()` writes one validated snapshot file atomically.
- Snapshot payload includes schema version and created timestamp.
- `restore_snapshot()` validates snapshot structure/version before writing.
- Invalid snapshots are rejected before any live state write.
- Restore attempts roll back to pre-restore canonical state if a later write in the restore sequence fails.
- Graceful shutdown attempts a final snapshot before persisting the graceful-shutdown marker.
