# AUDIT_SCOPE

## Objective
Focused, evidence-based audit of historical and current Telegram admin authentication/login flow and admin UI behavior.

## Explicit constraints applied
- No application code changes.
- No Railway variable changes.
- No Telegram network actions beyond existing offline tests.
- No deployment actions.

## Evidence sources reviewed
- Current code: `send/core/bot_service.py`, `send/core/admin_commands.py`, `send/core/admin_permissions.py`, `send/core/admin_views.py`, `send/runtime/telegram_updates.py`, `send/core/telegram_runtime.py`, `send/core/telegram_targets.py`, `send/core/telegram_publisher.py`.
- Historical/deleted: `git show 0fb9112:send/core/bot_service.py`, `git show d7e7213:send/core/bot_service.py`, `git show 0fb9112:send/legacy/bot_control.py` (deleted in `63834b3`).
- Backup artifacts: `send/_archive/backups/bot_service.py.bak_step*`, `send/_archive/backups/admin_router.py.bak_step*`.
- Config/env: `.env.example`, `send/config/admin_roles.json`, `send/config/admin_permissions.json`, `send/config/.env.example`.
- Canonical docs: `send/docs/canonical/active/TELEGRAM_UX_v2.0.0.md`, `ADMIN_CONTROL_SPEC_v2.0.0.md`, `ADMIN_OPERATIONS_SPEC_v2.0.0.md`, `ROLE_AND_PERMISSION_MATRIX_SPEC_v2.0.0.md`, `SECURITY_MODEL_v2.0.0.md`.
- Prior audits/remediation: `audit/remediation-batch-05/*`, `audit/remediation-batch-09/*`, `audit/railway-runtime-telegram-health-audit-01/*`.
- Git history: unshallowed repository (`git fetch --unshallow origin`) and commit history checks.

## Commits analyzed (control-plane timeline)
- `0fb9112` — initial imported runtime with legacy panel and legacy `send/legacy/bot_control.py`.
- `13d755a` — BATCH-04 canonical flow.
- `d7e7213` — BATCH-05 control-plane consolidation and legacy panel retirement.
- `63834b3` — BATCH-09 deletion of `send/legacy/bot_control.py`.
- `49aaeb4` — Telegram runtime remediation; introduces `/start` `/help` `/status` and admin slash chat-context denial.
