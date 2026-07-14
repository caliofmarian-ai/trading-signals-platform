# HEALTH_MONITORING_INVENTORY

| Mechanism | Entry | Trigger | Output | Active in Railway start | Telegram send |
|---|---|---|---|---|---|
| Railway readiness check | `scripts.railway_healthcheck.readiness_report` | startup preflight | return payload / exception | yes (called by `railway_start`) | no |
| Railway liveness check | `scripts.railway_healthcheck.liveness_report` | on-demand CLI | return payload / exception | no auto-thread | no |
| Runtime status file | `runtime.runtime_status.write_status` | startup/running/stopping/stopped transitions | `state/runtime_status.json` | yes | no |
| Restart guard | `monitoring.restart_guard.record_start/should_freeze` | startup and readiness | state + events | yes | no |
| Recovery event logging | `system_boot.start_system` | startup recovery flow | `engine_events.jsonl` / `error_events.jsonl` | yes | no |
| Deleted health monitor | `monitoring/health_check.py` (removed in BATCH-09) | periodic health snapshot | `monitoring/health_status.json` | no | no |

## Summary
Current active health model is file/event based; no active periodic Telegram health notifier is started by Railway runtime.
