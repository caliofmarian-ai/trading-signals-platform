# STARTUP_AND_SHUTDOWN_CONTRACT.md

## Start sequence
1. Resolve `BINARYBOT_BASE_DIR`.
2. Apply the Railway path contract (`scripts.railway_common.apply_path_contract`).
3. Seed and validate runtime directories/config (`scripts.railway_init`).
4. Run bounded readiness validation (`scripts.railway_healthcheck --mode readiness`).
5. Import `runtime.system_boot`.
6. Record runtime status (`state/runtime_status.json`).
7. Start engine loop and scheduler.
8. Start Telegram polling only when explicitly enabled and token-backed.

## Shutdown sequence
- `SIGINT` / `SIGTERM` are handled by `runtime.system_boot`.
- Runtime status is updated to `stopping` then `stopped`.
- Snapshot creation is attempted.
- Restart guard is marked graceful.
- Process exits `0` on graceful termination.

## Failure behavior
- Invalid config/state: startup blocked with non-zero exit.
- Crash-loop freeze: readiness/start blocked.
- Missing market-data credential: readiness/start blocked.
- Telegram disabled: boot continues without Telegram thread.
