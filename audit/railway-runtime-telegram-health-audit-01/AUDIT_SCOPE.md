# AUDIT_SCOPE

## Task framing
Focused repository-only audit of Railway runtime startup, Telegram command runner, health/failure observability, automatic reporting, admin proof routing, and historical Hetzner behavior.

## Explicit non-goals
- No application logic changes
- No strategy changes (WIDE/FOCUS untouched)
- No cadence changes for Twelve Data
- No deployment/Railway access

## Evidence sources
- Runtime and startup code:
  - `/home/runner/work/trading-signals-platform/trading-signals-platform/scripts/railway_start.py`
  - `/home/runner/work/trading-signals-platform/trading-signals-platform/send/runtime/system_boot.py`
  - `/home/runner/work/trading-signals-platform/trading-signals-platform/send/runtime/telegram_updates.py`
  - `/home/runner/work/trading-signals-platform/trading-signals-platform/send/core/bot_service.py`
  - `/home/runner/work/trading-signals-platform/trading-signals-platform/send/core/admin_commands.py`
  - `/home/runner/work/trading-signals-platform/trading-signals-platform/send/core/observability_logger.py`
- Monitoring/alerts artifacts:
  - `/home/runner/work/trading-signals-platform/trading-signals-platform/send/monitoring/restart_guard.py`
  - `/home/runner/work/trading-signals-platform/trading-signals-platform/send/alerts/*.sh`
  - `/home/runner/work/trading-signals-platform/trading-signals-platform/send/tg_send.sh`
- Canonical and audit records:
  - `/home/runner/work/trading-signals-platform/trading-signals-platform/send/docs/canonical/active/CANONICAL_MASTER_INDEX_v1.0.0.md`
  - batch/final/railway audit packages under `/home/runner/work/trading-signals-platform/trading-signals-platform/audit/`
- Git history:
  - BATCH-05/BATCH-09 commits and deleted-file snapshots

## Validation executed
- Full suite: `PYTHONPATH=send python -m pytest -q` → **302 passed**
- Targeted: telegram/admin/startup/health/observability/recovery tests → **113 passed**
- Import/syntax checks on scoped modules via `py_compile` → pass
