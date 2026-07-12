RUNBOOK.md

BinaryBot — Operational Runbook
Version: 1.0.0
Status: Canonical

Linked Documents:
CHECKLIST.md
DEPLOYMENT_PROTOCOL.md
FAILURE_RECOVERY_SPEC_v2.0.0.md
SYSTEM_INVARIANTS_v2.0.0.md
OBSERVABILITY_LOGGING_SPEC_v2.0.0.md
SECURITY_MODEL.md

---

1. PURPOSE

The Runbook defines the exact operational procedures used to run BinaryBot in production.

It provides step-by-step instructions for:

- system startup
- normal operations
- incident handling
- debugging
- recovery
- emergency shutdown

The runbook is designed for operators, administrators, and system maintainers.

---

2. SYSTEM LOCATION

BinaryBot runtime environment:

/opt/binarybot/

Key directories:

/opt/binarybot/config
/opt/binarybot/observability
/opt/binarybot/analytics
/opt/binarybot/outcomes
/opt/binarybot/docs

Main runtime files:

strategy_v2.py
signal_engine.py
distribution_router.py
fsm_runtime.py
bot_service.py
analytics_engine.py

---

3. NORMAL SYSTEM STARTUP

Before starting the system:

Step 1 — connect to server

ssh root@server_ip

Step 2 — navigate to bot directory

cd /opt/binarybot

Step 3 — verify files exist

ls

Verify presence of:

- config/algo_params.json
- active_symbols.json
- focus_state.json
- dist_state.json

Step 4 — check disk usage

df -h

Disk usage must remain below 80%.

Step 5 — start the service

systemctl start binarybot

Step 6 — confirm system started

systemctl status binarybot

Expected result:

ENGINE STARTED
Algo Version: X.X.X
Mode: WIDE_SCAN

---

4. VERIFY ENGINE HEALTH

After startup verify logs.

Check logs:

tail -f /opt/binarybot/observability/engine_events.jsonl

Confirm:

- engine_start event present
- parameters loaded
- no errors

---

5. VERIFY SIGNAL ENGINE

Monitor first signals.

Check for:

- PRE signals
- CONFIRM signals
- OPEN_NOW signals

Verify:

- no duplicate signals
- no unexpected signal flood

If duplicates occur:

STOP ENGINE.

---

6. VERIFY TELEGRAM CONNECTION

Confirm bot connectivity.

Test commands:

/start
/admin
/buffer

Expected behavior:

- bot responds
- admin panel loads
- commands function

---

7. VERIFY DISTRIBUTION

Check Telegram channels.

Confirm:

- signals appear in correct tier channels
- no cross-channel leakage
- silent tiers remain silent

---

8. VERIFY FSM STATE

Inspect FSM state file:

cat focus_state.json

Confirm:

- watchlist size ≤ 2
- cooldown timestamps valid

If corrupted:

STOP ENGINE.

---

9. VERIFY ANALYTICS ENGINE

Check analytics directory:

ls /opt/binarybot/analytics

Verify analytics outputs exist.

Expected files:

aggregates.json
reports/

---

10. INCIDENT RESPONSE

If abnormal behavior occurs:

Examples:

- duplicate signals
- spike of signals
- API errors
- state corruption

Immediate steps:

Step 1 — freeze system

systemctl stop binarybot

Step 2 — inspect logs

cat /opt/binarybot/observability/*.jsonl

Step 3 — identify cause

Possible causes:

- API failure
- parameter corruption
- code regression

Step 4 — restore backup if necessary.

---

11. EMERGENCY SHUTDOWN

In case of critical failure:

Stop the system immediately.

systemctl stop binarybot

Confirm shutdown:

systemctl status binarybot

Expected:

inactive (dead)

---

12. ROLLBACK PROCEDURE

If new deployment fails:

Step 1 — stop engine

systemctl stop binarybot

Step 2 — restore backup files

Example:

cp strategy_v2.py.bak strategy_v2.py

Step 3 — restore previous configuration

cp algo_params_backup.json config/algo_params.json

Step 4 — restart engine

systemctl start binarybot

---

13. MONITORING COMMANDS

Useful commands for operators.

Check running service:

systemctl status binarybot

View logs:

tail -f /opt/binarybot/observability/*.jsonl

Check CPU usage:

top

Check disk usage:

df -h

---

14. SECURITY INCIDENT RESPONSE

If unauthorized access suspected:

Step 1 — revoke access

Disable Telegram admin permissions.

Step 2 — inspect logs

Look for:

admin_change
unauthorized_access

Step 3 — rotate credentials if required.

---

15. DAILY OPERATIONS

Daily operator tasks:

- review system logs
- review signal statistics
- verify API health
- verify disk usage
- verify analytics outputs

---

16. SYSTEM GUARANTEE

If the runbook procedures are followed:

- system remains stable
- incidents are resolved quickly
- deployments remain controlled
- operational risk is minimized

Runbook discipline ensures safe production operation.

---

End of RUNBOOK.md