# PRODUCTION_PROCESS_MODEL.md

## Recommended initial architecture
- **One Railway service**.
- Service type: **worker-style Python process** with no inbound HTTP server.
- Start command: `PYTHONPATH=send python -m scripts.railway_start`.

## Process layout
- Main foreground process: `runtime.system_boot.start_system()`.
- Daemon thread: engine loop (`runtime.engine_loop.start_engine`).
- Daemon thread: distribution scheduler (`runtime.distribution_scheduler.scheduler_loop`).
- Optional daemon thread: Telegram polling (`runtime.telegram_updates.poll_updates`) only when `ENABLE_TELEGRAM=true` and `TELEGRAM_BOT_TOKEN` is present.
- Optional separate scheduled Railway job: `PYTHONPATH=send python -m tools.strategy_auditor_daily`.

## Why one service
- Repository evidence shows one coherent boot path.
- No inbound web server is required.
- Analytics/research are filesystem-driven and can remain inline or scheduled later.
- Adding more services now would add operational complexity without a code-level need.
