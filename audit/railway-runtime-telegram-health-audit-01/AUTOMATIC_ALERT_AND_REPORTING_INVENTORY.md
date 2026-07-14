# AUTOMATIC_ALERT_AND_REPORTING_INVENTORY

## Active automatic reporting paths
- JSONL observability via `core.observability_logger`:
  - engine/fsm/distribution/admin_proofs/error/outcomes sinks
- Runtime recovery and crash-loop events logged from `system_boot` and `restart_guard`

## Telegram automatic reporting in active code
- `observability_logger.proof()` can Telegram-send to `ADMIN_PROOF_CHAT_ID`.
- **Active caller count in runtime code: 0** (only archived/deprecated references).

## Legacy/manual scripts present but not wired
- `send/alerts/send_system.sh`
- `send/alerts/send_error.sh`
- `send/alerts/send_signal.sh`
- `send/alerts/send_result.sh`
- `send/alerts/send_stats.sh`
- `send/alerts/send_billing.sh`
- `send/tg_send.sh`

These rely on `/opt/binarybot/.env` + `TELEGRAM_ADMIN_CHAT_ID`/`TOPIC_*`, but no active Python caller invokes them.

## Startup/live/recovery notifications
- No active startup/recovery Telegram message sender in current runtime startup chain.
