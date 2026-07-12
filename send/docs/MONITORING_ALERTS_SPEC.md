MONITORING_ALERTS_SPEC.md

BinaryBot — Monitoring, Alerting & Operational Warning System
Version: 1.0.0
Status: Canonical

Linked Documents:
OBSERVABILITY_LOGGING_SPEC_v2.0.0.md
EVENT_SCHEMA_SPEC_v2.0.0.md
FAILURE_RECOVERY_SPEC_v2.0.0.md
SECURITY_MODEL.md
SYSTEM_INVARIANTS_v2.0.0.md
PERFORMANCE_ANALYTICS_SPEC_v2.0.0.md
ADMIN_OPERATIONS_SPEC_v2.0.0.md
TEST_PLAN.md

---

1. PURPOSE

This document defines how BinaryBot detects operational problems and alerts administrators.

Monitoring ensures that:

- engine failures are detected immediately
- abnormal trading behavior is flagged
- infrastructure problems are visible
- security anomalies are reported
- operational issues are resolved quickly

Without monitoring, failures may remain invisible.

Monitoring transforms observability data into actionable alerts.

---

2. ALERT DELIVERY CHANNEL

All alerts must be delivered to the admin control environment.

Recommended location:

Telegram Admin Supergroup
Topic:

ADMIN_ALERTS

Alert messages must also be logged to observability logs.

Alert channels must never include public users.

---

3. ALERT SEVERITY LEVELS

BinaryBot uses four severity levels.

INFO
WARNING
ERROR
CRITICAL

Each severity indicates the urgency of the situation.

---

3.1 INFO

Informational messages.

Examples:

- engine started
- tier reset executed
- configuration loaded
- analytics report generated

INFO alerts require no action.

---

3.2 WARNING

Indicates unusual behavior but not system failure.

Examples:

- watchlist approaching limit
- signal frequency spike
- API latency increase
- outcome anomaly detected

Warnings should be reviewed but do not require immediate intervention.

---

3.3 ERROR

Indicates operational failure affecting functionality.

Examples:

- API request failure
- distribution publish failure
- configuration load error
- file write failure

Errors require administrator attention.

---

3.4 CRITICAL

Indicates severe failure or security risk.

Examples:

- engine crash
- invariant violation
- crash loop detected
- configuration tampering detected
- disk space critical

Critical alerts must trigger immediate investigation.

---

4. ENGINE MONITORING ALERTS

The system must monitor the core engine runtime.

---

4.1 Engine Start

Alert type:

INFO

Example:

ENGINE STARTED
version=1.0.0
mode=WIDE_SCAN

---

4.2 Engine Stop

Alert type:

WARNING

Unexpected engine stops must trigger alerts.

Example:

ENGINE STOPPED unexpectedly.

---

4.3 Crash Detection

Alert type:

CRITICAL

Example:

ENGINE CRASH DETECTED
module=signal_engine.py

Stack trace reference stored in logs.

---

4.4 Crash Loop Detection

If the engine restarts more than 3 times within 60 seconds.

Alert:

CRITICAL

Example:

CRASH LOOP DETECTED
restart_count=4

The system should enter Freeze Mode automatically.

---

5. SIGNAL ENGINE ALERTS

Monitoring of trading behavior.

---

5.1 Signal Frequency Spike

If signals per hour suddenly double the historical baseline.

Alert type:

WARNING

Example:

SIGNAL FREQUENCY SPIKE
expected=8/h
observed=17/h

---

5.2 No Signals for Extended Period

If the engine runs for extended time without signals.

Example threshold:

6 hours without signals.

Alert type:

WARNING

Possible causes:

- market conditions
- API issues
- strategy malfunction

---

5.3 Duplicate Signal Detection

If deduplication blocks repeated signals.

Alert type:

ERROR

Example:

DUPLICATE OPEN BLOCKED
symbol=EURUSD

---

6. DISTRIBUTION ALERTS

Distribution router must report publishing failures.

---

6.1 Telegram Publish Failure

Alert type:

ERROR

Example:

TELEGRAM PUBLISH FAILED
tier=FREE
symbol=EURUSD

---

6.2 Tier Silent Mode Triggered

When a tier reaches its OPEN_NOW limit.

Alert type:

INFO

Example:

FREE tier entered SILENT mode.

---

6.3 Tier Reset Executed

Daily reset event.

Alert type:

INFO

Example:

TIER RESET EXECUTED
time=08:10 Europe/London

---

7. API MONITORING ALERTS

External market data APIs must be monitored.

---

7.1 API Timeout

Alert type:

WARNING

Example:

API TIMEOUT
provider=TwelveData

---

7.2 API Unavailable

Alert type:

ERROR

Example:

API UNAVAILABLE
duration=120 seconds

---

7.3 API Rate Limit

Alert type:

WARNING

Example:

API RATE LIMIT REACHED

---

8. SECURITY ALERTS

Security anomalies must generate alerts.

---

8.1 Unauthorized Admin Access Attempt

Alert type:

CRITICAL

Example:

UNAUTHORIZED ADMIN ACCESS
user_id=123456789

---

8.2 Role Escalation Attempt

Alert type:

CRITICAL

Example:

ROLE ESCALATION ATTEMPT

---

8.3 Configuration Tampering

Alert type:

CRITICAL

Example:

CONFIG INTEGRITY FAILURE

---

9. OUTCOME SYSTEM ALERTS

Outcome voting anomalies must be monitored.

---

9.1 Vote Flooding

If too many votes appear in a short time window.

Alert type:

WARNING

Example:

OUTCOME VOTE SURGE
signal_id=XXXX

---

9.2 Suspicious Outcome Patterns

Example:

- same user voting unusually often
- vote distribution inconsistent

Alert type:

WARNING

---

10. STORAGE ALERTS

Disk usage must be monitored.

---

10.1 Disk Usage Warning

Threshold:

80% disk capacity.

Alert type:

WARNING

---

10.2 Disk Usage Critical

Threshold:

90% disk capacity.

Alert type:

CRITICAL

System may stop logging to protect stability.

---

11. ALERT RATE LIMITING

To prevent alert spam:

Similar alerts within a short period must be grouped.

Example:

Multiple API timeouts within 60 seconds → single alert summary.

---

12. ALERT MESSAGE FORMAT

Each alert message must include:

timestamp
severity level
event type
relevant parameters

Example:

[CRITICAL]
ENGINE CRASH DETECTED
timestamp=2026-03-05T12:10:22Z

---

13. ALERT GUARANTEE

If this monitoring system is implemented:

- failures become visible immediately
- anomalies are detected early
- administrators can react quickly
- operational reliability increases

Monitoring ensures BinaryBot operates safely in production.

---

End of MONITORING_ALERTS_SPEC.md