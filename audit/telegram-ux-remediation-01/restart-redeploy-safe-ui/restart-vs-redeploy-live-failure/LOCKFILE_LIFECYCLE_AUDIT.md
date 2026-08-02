# LOCKFILE_LIFECYCLE_AUDIT.md
# Issue #31 — Lockfile Lifecycle Audit

## Lock Implementation (Pre-Fix)

- **File**: `send/core/storage.py` → `with_lock()`
- **Mechanism**: `os.O_CREAT | os.O_EXCL | os.O_WRONLY` atomic create
- **Content**: `pid=<PID> ts=<TIMESTAMP>\n`
- **Cleanup**: `finally: os.remove(lock_path)` — requires process to complete normally

## Failure Modes Confirmed

| Scenario | Pre-Fix Behavior | Post-Fix Behavior |
|---------|-----------------|-----------------|
| Process killed with SIGKILL | Lock file remains permanently | Detected via dead PID check |
| SIGTERM with timeout → SIGKILL | Lock file may remain | Detected via dead PID check |
| Railway Restart (same container) | Stale lock survives | Reclaimed on first contention |
| Railway Redeploy (new container) | Fresh filesystem | Fresh filesystem (unchanged) |
| Different Railway deployment | Lock file from old deploy | Detected via deployment ID |
| Lock older than 300s | Never reclaimed | Age threshold reclaim |

## Lock Files Affected

The following lock files can become stale:

- `state/.locks/telegram_ui_state.lock` — most impactful (used per-command)
- `state/.locks/restart_guard.lock` — critical (used during startup)
- `state/.locks/focus_state.lock` — less frequent (used during engine updates)
- `state/.locks/dist_state.lock` — less frequent

## Post-Fix Lock Ownership Metadata

```
pid=<PID> ts=<UNIX_TIMESTAMP> deploy=<RAILWAY_DEPLOYMENT_ID> host=<HOSTNAME>
```

## Reclaim Decision Tree

```
Lock file exists?
  → NO → acquire immediately
  → YES
    → deployment ID different from current? → STALE (reclaim)
    → age > 300s? → STALE (reclaim)
    → PID ≤ 0? → STALE (reclaim)
    → PID not alive (ProcessLookupError)? → STALE (reclaim)
    → all checks pass (live PID, same deployment) → NOT STALE (wait)
    → waited ≥ timeout? → TimeoutError (never stale reclaim would help)
```

## State Path

`state/.locks/` is under `BINARYBOT_BASE_DIR/state/.locks/` when `BINARYBOT_BASE_DIR` is set,
or under the package directory otherwise. On Railway with no persistent volume, this is the
container's ephemeral filesystem — cleared on Redeploy, but **not on Restart**.
