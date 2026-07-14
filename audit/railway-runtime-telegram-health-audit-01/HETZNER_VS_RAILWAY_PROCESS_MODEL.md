# HETZNER_VS_RAILWAY_PROCESS_MODEL

## Current Railway model (confirmed)
- Single process command: `PYTHONPATH=send python -m scripts.railway_start`
- In-process daemon threads for engine, scheduler, optional Telegram polling.
- No separate bot command service, no separate alert/health sender process started by this command.

## Historical Hetzner evidence in repository
- Legacy Telegram runner existed: `send/legacy/bot_control.py` (deleted BATCH-09), using `python-telegram-bot` `run_polling()` and `/start` command.
- Legacy shell Telegram transport existed and still exists: `send/tg_send.sh` + `send/alerts/*.sh` with topic-based routing.
- Deprecated architecture doc references a systemd `ExecStart=/opt/binarybot/venv/bin/python /opt/binarybot/signal_engine.py`.

## Most likely historical process model (evidence-based inference)
- **Inference label:** probable, not directly reproducible from active runtime code.
- Hetzner likely used at least one non-Railway process outside current startup chain (legacy bot runner and/or shell alert scripts), which could explain remembered `/start` behavior and message-based system alerts.

## Key difference causing current behavior gap
- Railway starts only the canonical runtime path; legacy external runners/scripts are not started.
