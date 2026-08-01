# Multi-Instance And Poller Audit

## Repository configuration
- `railway.json` declares `numReplicas: 1`.
- `runtime.system_boot.start_system()` starts one Telegram polling thread per runtime process.

## Verified risks
- Railway deploy overlap across old/new containers cannot be disproven from repository-only access.
- Cross-process state collision was previously possible because persisted UI state was written as whole-file replacement from in-memory state.

## Correction
- Poller startup now emits a structured startup record with PID and runtime instance identifier.
- A duplicate in-process poller guard now blocks accidental second `poll_updates()` startup in the same runtime process.
- Persisted UI state updates now merge under lock so one process cannot silently erase another process's independent session entries.

## Remaining invariant
- Single active poller per deployment remains the intended operating model.
- Temporary old/new deployment overlap is still an external platform risk and remains a live-acceptance item.
