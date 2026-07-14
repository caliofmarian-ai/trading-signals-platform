# ACTIVE_ORPHANED_DISABLED_COMPONENT_MATRIX

| Component | Status | Started by Railway start | Notes |
|---|---|---|---|
| `scripts.railway_start` | ACTIVE | yes | canonical Railway entrypoint |
| `runtime.system_boot` | ACTIVE | yes | main orchestrator |
| `runtime.engine_loop` | ACTIVE | yes | daemon thread |
| `runtime.telegram_updates` | ACTIVE/CONDITIONAL | conditional | requires `ENABLE_TELEGRAM=true` + token |
| `core.bot_service` | ACTIVE | via polling | command dispatcher for limited admin commands |
| `core.admin_commands` | ACTIVE | via bot_service | permission-guarded admin surface |
| `monitoring.restart_guard` | ACTIVE | yes | crash-loop governance |
| `runtime.runtime_status` | ACTIVE | yes | file-based status |
| `scripts.railway_healthcheck` | ACTIVE/ON-DEMAND | readiness called at start | liveness/readiness CLI, no notifier thread |
| `core.observability_logger.proof` Telegram relay | DORMANT | no | function exists; no active callers |
| `send/alerts/*.sh` and `send/tg_send.sh` | ORPHAN/MANUAL | no | no active Python callers |
| `send/legacy/bot_control.py` | DELETED | no | removed in BATCH-09 |
| `send/monitoring/health_check.py` | DELETED | no | removed in BATCH-09 |
