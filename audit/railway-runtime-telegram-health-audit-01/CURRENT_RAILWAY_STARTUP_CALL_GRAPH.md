# CURRENT_RAILWAY_STARTUP_CALL_GRAPH

## Railway start command
`PYTHONPATH=send python -m scripts.railway_start` (`railway.json`)

## Exact call graph
1. `scripts.railway_start.main()`
2. `resolve_base_dir(require_explicit=True)`
3. `apply_path_contract(base_dir)`
4. `initialize_for_railway(base_dir)`
5. `readiness_report(base_dir)`
6. `runtime.system_boot.start_system()`

## `start_system()` flow (same process)
- Registers SIGINT/SIGTERM + atexit shutdown hooks
- Calls `record_start()` (restart guard)
- Writes runtime status: `starting`
- Logs `recovery_started`
- Loads FSM + distribution state
- Crash-loop gate (`start_info["crash_loop"]`)
- Logs `recovery_completed`
- Logs `engine_start`
- Starts daemon threads:
  - `runtime.engine_loop.start_engine`
  - `runtime.telegram_updates.poll_updates` (only if `ENABLE_TELEGRAM=true` and token present)
  - `runtime.distribution_scheduler.scheduler_loop`
- Writes runtime status: `running`
- Main thread sleeps forever (`while True: sleep(60)`)

## Startup wiring verdict
- **System boot started:** yes
- **Engine loop started:** yes (daemon thread)
- **Telegram polling started:** conditional
- **Telegram command dispatch started:** only through `poll_updates -> process_update -> bot_service.process_update`
- **Health monitoring started:** no dedicated runtime health monitor thread; only startup readiness gate + runtime status + restart_guard
- **Alert routing started:** no dedicated alert worker
- **Admin proof routing started:** only JSONL writes in command path; Telegram proof relay function exists but is not called
- **Startup/restart Telegram notification started:** no

## Blocking/starvation analysis
- Boot is sequential until thread startup; state-load/crash-loop failures block all loops.
- After startup, components run in daemon threads in one process.
- Engine 429 loops can cause high error frequency and I/O pressure but do not directly stop polling thread.
