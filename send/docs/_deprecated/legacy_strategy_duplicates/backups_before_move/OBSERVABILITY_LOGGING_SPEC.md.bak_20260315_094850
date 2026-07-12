# OBSERVABILITY_LOGGING_SPEC.md
BinaryBot — Observability, Telemetry & Logging Specification
Version: 1.1.0
Status: Canonical

Linked Documents:
- EVENT_SCHEMA_SPEC.md
- RUNTIME_EXECUTION_TIMELINE.md
- ARCHITECTURE_CODE_MAPPING.md
- FAILURE_RECOVERY_SPEC.md
- SIGNAL_DISTRIBUTION_SPEC.md
- TELEGRAM_UX.md
- PERFORMANCE_ANALYTICS_SPEC.md
- FSM_SPEC.md
- ALGO_SPEC.md
- SYSTEM_INVARIANTS.md

---

# 1. PURPOSE

This document defines the complete observability and logging architecture of BinaryBot.

It specifies:

- what events must be logged
- how logs must be structured
- where logs must be stored
- how logs rotate and persist
- how anomalies are detected
- how logs are used for analytics and debugging

Observability guarantees:

- no hidden logic
- no silent failures
- no invisible state corruption
- no undetected duplicate signals
- full forensic traceability
- reproducible system behavior

Core rule:

If an event is not logged, it is considered not to have happened.

---

# 2. LOGGING PRINCIPLES

BinaryBot logging must follow these principles:

1. Every signal decision must produce a log event.
2. Every FSM transition must produce a log event.
3. Every distribution action must produce a log event.
4. Every user outcome must produce a log event.
5. Every configuration change must produce a log event.
6. Every system error must produce a log event.
7. No silent state changes are allowed.

Logging must never alter trading behavior.

Logging must be append-only.

---

# 3. EVENT FORMAT (JSONL)

BinaryBot uses structured logging in JSONL format.

Definition:

One event per line.

Example:

{"event_type":"signal_event","symbol":"EURUSD","stage":"PRE"}

Events follow the canonical schema defined in:

EVENT_SCHEMA_SPEC.md

---

# 4. LOG DIRECTORY STRUCTURE

All observability logs are stored in:

/opt/binarybot/observability/

Files:

engine_events.jsonl  
fsm_events.jsonl  
distribution_events.jsonl  
admin_proofs.jsonl  
error_events.jsonl  

Outcome feedback:

/opt/binarybot/outcomes/outcomes.jsonl

Analytics outputs:

/opt/binarybot/analytics/

---

# 5. ENGINE EVENTS

File:

engine_events.jsonl

Contains:

engine_start  
engine_stop  
decision  
signal_event  

Example:

engine_start  
decision  
signal_event(PRE)  
signal_event(CONFIRM)  
signal_event(OPEN_NOW)

Fields follow EVENT_SCHEMA_SPEC.md.

---

# 6. DECISION LOGGING

Every symbol evaluation cycle must log a decision event.

Event:

decision

Includes:

symbol  
candle timestamp  
trend classification  
score  
buffer  
expiry  
gate results  
decision result

Decision types:

PRE  
CONFIRM  
OPEN_NOW  
REJECT  
NO_SIGNAL  

These logs enable full reconstruction of strategy behavior.

---

# 7. FSM STATE LOGGING

File:

fsm_events.jsonl

Event:

fsm_transition

Each transition logs:

symbol  
previous state  
new state  
trigger reason  
timestamp  

Example transitions:

IDLE → WATCHLIST  
WATCHLIST → LIVE_SENT  
LIVE_SENT → COOLDOWN  

No state transition may occur without a corresponding log.

---

# 8. DISTRIBUTION LOGGING

File:

distribution_events.jsonl

Event:

tier_publish

Logs each distribution attempt.

Fields:

tier  
signal_id  
stage  
publish_decision  
counter_before  
counter_after  
telegram_result  

Possible publish decisions:

PUBLISHED  
SKIPPED_LIMIT  
SKIPPED_SILENT  
FAILED  
DUPLICATE_SUPPRESSED  

---

# 9. TIER RESET LOGGING

Event:

tier_reset

Triggered daily at:

08:10 Europe/London

Logs:

tier counters before reset  
tier counters after reset  
reset timestamp  

This guarantees traceability of distribution limits.

---

# 10. USER OUTCOME LOGGING

File:

/opt/binarybot/outcomes/outcomes.jsonl

Event:

user_outcome

Contains:

signal_id  
user_id  
outcome  
vote timestamp  

Possible outcomes:

WIN  
LOSE  
MISSED  

User identity beyond Telegram ID must not be stored.

---

# 11. ADMIN ACTION LOGGING

File:

admin_proofs.jsonl

Event:

admin_change

Logged actions include:

buffer mode changes  
symbol selection changes  
tier configuration changes  
manual resets  

Fields:

admin user id  
before state  
after state  
timestamp  

This provides governance traceability.

---

# 12. ERROR LOGGING

File:

error_events.jsonl

Event:

error

Contains:

severity  
error type  
module name  
stack trace  
context  

Severity levels:

INFO  
WARNING  
ERROR  
CRITICAL  

Errors must never crash the engine silently.

---

# 13. ANOMALY DETECTION

BinaryBot must log warnings when invariants are violated.

Examples:

WATCHLIST_OVERFLOW  
OPEN_NOW_WITHOUT_PRE  
COOLDOWN_BYPASS  
DUPLICATE_SIGNAL_ATTEMPT  
PARAMETER_MISSING  

These warnings indicate potential logic faults.

---

# 14. DEDUPLICATION OBSERVABILITY

Engine dedup key:

symbol + candle_timestamp + stage

Distribution dedup key:

tier + signal_id + stage

Each dedup check must log:

dedup key  
duplicate detected  
action taken  

Example:

duplicate suppressed.

---

# 15. CRASH DETECTION

If the engine restarts more than:

3 times in 60 seconds

Log:

CRASH_LOOP_DETECTED

Severity:

CRITICAL

Optional response:

halt engine.

---

# 16. LOG ROTATION

To prevent disk overflow:

Log rotation must be enabled.

Recommended parameters:

max_file_size = 100MB  
max_files = 30  
compression = gzip  

Old logs must be archived automatically.

---

# 17. LOG RETENTION

Recommended retention:

engine logs: 30 days  
distribution logs: 30 days  
error logs: 60 days  
admin proofs: permanent  

Retention must not delete logs required for analytics.

---

# 18. CORRELATION FIELDS

To allow debugging and analytics correlation, events may include:

signal_id  
trace_id  
run_id  
symbol  
tier  
user_id  

These fields allow cross-log reconstruction of signal lifecycle.

---

# 19. TELEGRAM DEBUG CHANNEL

The Telegram debug topic (BUFFER_LOGS) mirrors internal decisions.

Content includes:

score breakdown  
gate results  
buffer calculation  
expiry calculation  

These messages are informational and must match decision logs.

---

# 20. LOG INTEGRITY RULE

Every signal visible in Telegram must have:

decision log  
FSM transition log  
distribution log  

Missing logs indicate observability failure.

---

# 21. ANALYTICS DEPENDENCY

Analytics engine relies on observability logs.

Data sources:

engine_events.jsonl  
distribution_events.jsonl  
fsm_events.jsonl  
outcomes.jsonl  

These logs power:

performance metrics  
symbol ranking  
conversion funnels  
drift detection  

Defined in:

PERFORMANCE_ANALYTICS_SPEC.md

---

# 22. OBSERVABILITY GUARANTEE

If this specification is implemented correctly:

every decision is traceable  
every state transition is visible  
every signal distribution is auditable  
every anomaly is detectable  

BinaryBot becomes a transparent, debuggable and production-grade system.

---

End of OBSERVABILITY_LOGGING_SPEC.md