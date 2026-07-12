DATA_RETENTION_POLICY.md

BinaryBot — Data Retention, Archival & Purge Policy
Version: 1.0.0
Status: Canonical

Linked Documents:
OBSERVABILITY_LOGGING_SPEC_v2.0.0.md
EVENT_SCHEMA_SPEC_v2.0.0.md
PERFORMANCE_ANALYTICS_SPEC_v2.0.0.md
SECURITY_MODEL.md
FAILURE_RECOVERY_SPEC_v2.0.0.md
SYSTEM_INVARIANTS_v2.0.0.md
ADMIN_OPERATIONS_SPEC_v2.0.0.md
DEPLOYMENT_PROTOCOL.md
TEST_PLAN.md

---

1. PURPOSE

This document defines how long BinaryBot stores operational data and how data must be archived or purged.

The goals of the retention policy are:

- Prevent uncontrolled disk growth
- Preserve forensic evidence for debugging
- Preserve trading performance data for analytics
- Maintain operational transparency
- Ensure long-term research capability

All system data must follow defined retention rules.

If retention rules are violated, the system may lose auditability or suffer storage exhaustion.

---

2. DATA CATEGORIES

BinaryBot generates several categories of data.

Each category has a different retention policy.

Categories include:

1. Observability Logs
2. Engine Events
3. Distribution Logs
4. FSM State Logs
5. Admin Proof Logs
6. Outcome Voting Data
7. Analytics Aggregates
8. Configuration Snapshots
9. Crash Reports

Each category must be stored in a defined directory and retained for a defined period.

---

3. OBSERVABILITY LOGS

Directory:

/opt/binarybot/observability/

Examples:

engine_events.jsonl
distribution_events.jsonl
fsm_events.jsonl
admin_proofs.jsonl

These logs contain system behavior data.

Contents include:

- signal events
- FSM transitions
- distribution actions
- admin changes
- system warnings
- anomaly alerts

---

3.1 Retention Duration

Observability logs must be retained for:

30 days minimum.

This allows sufficient forensic debugging.

---

3.2 Rotation Policy

Logs must be rotated automatically.

Recommended rotation:

Daily log files.

Example structure:

observability/

engine_events_2026-03-01.jsonl
engine_events_2026-03-02.jsonl
engine_events_2026-03-03.jsonl

Rotation prevents very large files.

---

3.3 Purge Policy

Logs older than 30 days may be deleted automatically.

Deletion must occur via scheduled cleanup job.

Example schedule:

Once per day.

Deletion must produce a log entry.

---

4. ADMIN PROOF LOGS

Directory:

/opt/binarybot/observability/admin_proofs.jsonl

These logs contain critical administrative actions.

Examples:

- buffer mode change
- symbol selection change
- tier reset
- freeze/unfreeze
- deployment markers

---

4.1 Retention Duration

Admin proof logs must be retained for:

Minimum 1 year.

Recommended:

Permanent retention if disk capacity allows.

These logs provide governance evidence.

---

5. OUTCOME VOTING DATA

Directory:

/opt/binarybot/outcomes/outcomes.jsonl

These records contain:

signal_id
user_id
symbol
result (WIN / LOSE / MISSED)
timestamp

Outcome data is essential for performance analytics.

---

5.1 Retention Duration

Outcome records must be retained permanently.

Reason:

- required for long-term strategy evaluation
- required for analytics model training
- required for statistical validation

Outcome logs must never be automatically purged.

---

6. ANALYTICS AGGREGATES

Directory:

/opt/binarybot/analytics/

Examples:

aggregates.json
baselines.json
reports/

Aggregates summarize large datasets into metrics.

Examples:

- win rate
- symbol performance
- rejection breakdown
- signal frequency

---

6.1 Retention Duration

Analytics aggregates should be retained for:

Minimum 1 year.

Old aggregates may be archived.

---

6.2 Archive Policy

Older reports may be compressed.

Example format:

reports_2025_archive.zip

This preserves historical analytics without consuming large disk space.

---

7. CONFIGURATION SNAPSHOTS

Configuration includes:

algo_params.json
settings.json
active_symbols.json
channel_config.json

These files represent system state and operational parameters.

---

7.1 Snapshot Policy

Before deployment or parameter changes:

A configuration snapshot must be stored.

Directory:

/opt/binarybot/config_snapshots/

Example:

algo_params_2026-03-04.json
settings_2026-03-04.json

---

7.2 Retention Duration

Configuration snapshots must be retained for:

Minimum 6 months.

Recommended:

1 year.

Snapshots allow rollback during debugging.

---

8. CRASH REPORTS

Crash reports contain diagnostic information.

Examples:

- stack traces
- system exceptions
- API failures
- restart loops

Crash reports should be stored in:

/opt/binarybot/crash_reports/

---

8.1 Retention Duration

Crash reports must be retained for:

Minimum 90 days.

They are critical for diagnosing system failures.

---

9. STORAGE LIMIT PROTECTION

BinaryBot must prevent disk exhaustion.

Recommended safeguards:

- disk usage monitoring
- automatic cleanup tasks
- alert if disk usage exceeds threshold

Example threshold:

80% disk usage.

If exceeded:

Admin alert must be triggered.

---

10. AUTOMATED CLEANUP JOB

The server should run a scheduled cleanup process.

Example frequency:

Daily at 03:00 server time.

Cleanup tasks include:

- remove observability logs older than 30 days
- compress old analytics reports
- remove crash reports older than retention window

Cleanup activity must generate a log entry.

---

11. DATA INTEGRITY

Retention must never corrupt data.

Rules:

- no partial file deletion
- no modification of existing JSONL logs
- append-only structure preserved

Deletion operations must target full files only.

---

12. BACKUP RECOMMENDATIONS

Recommended backups include:

- configuration snapshots
- outcome logs
- analytics aggregates

Backups may be stored:

- offsite server
- encrypted storage
- secure cloud bucket

Backup frequency recommended:

Weekly.

---

13. PRIVACY PROTECTION

Outcome logs contain internal user IDs.

Rules:

- user IDs must never appear in public reports
- analytics must only show aggregated results
- private statistics accessible only to the respective user

Data privacy rules must follow SECURITY_MODEL.md.

---

14. RETENTION GUARANTEE

If this retention policy is implemented:

- disk growth remains controlled
- debugging remains possible
- analytics remains reliable
- governance evidence is preserved
- system integrity is protected

Data retention is essential for sustainable operation of BinaryBot.

---

End of DATA_RETENTION_POLICY.md