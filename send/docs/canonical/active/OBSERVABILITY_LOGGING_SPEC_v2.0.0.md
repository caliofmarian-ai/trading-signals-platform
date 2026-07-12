# OBSERVABILITY_LOGGING_SPEC_v2.0.0.md

BinaryBot — Observability, Telemetry, Logging & Auditability Specification  
Version: 2.0.0  
Status: CANONICAL  
Path: /opt/binarybot/docs/canonical/active/OBSERVABILITY_LOGGING_SPEC_v2.0.0.md

Linked Documents:
- DECISION_AUDIT_SPEC_v2.0.0.md
- TRADE_TEMPORAL_TELEMETRY_SPEC_v2.0.0.md
- SIGNAL_DISTRIBUTION_SPEC_v2.0.0.md
- TELEGRAM_UX_v2.0.0.md
- CHANNEL_CONFIG_SPEC_v2.0.0.md
- OUTCOME_TRACKING_SPEC_v2.0.0.md
- PERFORMANCE_ANALYTICS_SPEC_v2.0.0.md
- ADMIN_CONTROL_SPEC_v2.0.0.md
- ADMIN_OPERATIONS_SPEC_v2.0.0.md
- ROLE_AND_PERMISSION_MATRIX_SPEC_v2.0.0.md
- CONTROL_PANEL_HIERARCHY_AND_INTELLIGENCE_SPEC_v2.0.0.md
- GOVERNANCE_AND_CHANGE_CONTROL.md
- EVENT_SCHEMA_SPEC_v2.0.0.md
- FAILURE_RECOVERY_SPEC_v2.0.0.md
- SYSTEM_INVARIANTS_v2.0.0.md

---

## 1. PURPOSE

This document defines the canonical observability layer for BinaryBot.

It specifies:
- what must be observable
- which event families exist
- how telemetry and logs must be structured
- which persistence and retention guarantees must hold
- how anomalies, failures and governance-relevant actions are surfaced
- how the system supports forensic reconstruction, operational debugging and post-hoc analytics

Observability exists to ensure:
- no hidden logic
- no silent failures
- no invisible state corruption
- no unaudited control mutation
- no unverifiable distribution behavior
- no unverifiable signal-lifecycle claims

Core rule:
If a materially relevant event is not observable, it is treated as an observability failure.

---

## 2. PRINCIPLES

BinaryBot observability must follow these principles:

1. Every material decision path must produce observable evidence.
2. Every governed state transition must produce observable evidence.
3. Every distribution action must produce observable evidence.
4. Every user outcome interaction must produce observable evidence.
5. Every admin mutation must produce observable evidence.
6. Every critical failure must produce observable evidence.
7. No silent state changes are allowed.
8. Observability must not mutate trading behavior.
9. Logs must be append-oriented and reconstruction-safe.
10. Observability must support both machine analytics and human incident review.

---

## 3. OBSERVABILITY DOMAINS

The canonical observability layer is divided into the following domains:

### 3.1 Decision observability
Decision creation, rejection, scoring evidence, gating results and lifecycle evaluation evidence.

### 3.2 Temporal telemetry
Timing-sensitive signal, expiry and execution-window evidence.

### 3.3 FSM/state observability
Governed state transitions and trigger reasons.

### 3.4 Distribution observability
Route resolution, entitlement outcomes, publish attempts and delivery results.

### 3.5 Outcome observability
User-submitted results, validation decisions and aggregate linkage.

### 3.6 Admin/control observability
Governed control mutations, guarded actions and proof of change.

### 3.7 System/error observability
Runtime failures, crash loops, degraded dependencies and recovery evidence.

### 3.8 Research/analytics observability
Derived metrics, summaries and drift-relevant evidence generated from the base logs.

---

## 4. OBSERVABILITY IS A LAYER, NOT A FILE LIST

The older version framed observability primarily as a list of JSONL files.
Those files remain useful, but the canonical truth is now the observability contract, not merely the filenames.

Therefore:
- file names may evolve
- event streams may be split or merged operationally
- serialization may evolve
- storage backends may evolve

But the semantic obligation to emit observable evidence for governed events remains canonical.

---

## 5. EVENT FORMAT BASELINE

Structured events remain the baseline.

Recommended baseline:
- JSONL
- one event per line
- append-oriented storage

Example:

```json
{"event_type":"signal_event","signal_identity":"abc123","stage":"PRE"}
```

The detailed event schema belongs to:
- `EVENT_SCHEMA_SPEC_v2.0.0.md`

This document defines the observability obligations and semantic event families.

---

## 6. MINIMUM CORRELATION FIELDS

To support forensic reconstruction, relevant events should carry enough correlation fields.

Common correlation fields may include:
- event_type
- timestamp_utc
- run_id
- trace_id
- signal_identity
- symbol
- timeframe
- stage
- route
- telegram_message_id
- user_id
- admin_actor_id

Not every event needs every field, but each event must contain enough context to be reconstructed and interpreted correctly.

---

## 7. DECISION OBSERVABILITY

Every symbol evaluation cycle that reaches a material decision boundary must emit observable evidence.

Typical decision evidence includes:
- symbol
- timeframe
- market timestamp / candle context
- score or score components where governed
- gating results
- rejection reasons
- selected expiry context
- buffer context where relevant
- decision result

Canonical decision result families may include:
- PRE
- CONFIRM
- OPEN_NOW
- REJECT
- NO_SIGNAL

This domain must align with:
- `DECISION_AUDIT_SPEC_v2.0.0.md`
- `TRADE_TEMPORAL_TELEMETRY_SPEC_v2.0.0.md`

---

## 8. REJECTION AND DECISION-AUDIT OBSERVABILITY

The older observability model logged “decision” at a high level.
The canonical model now requires richer rejection and decision-audit evidence.

Observable rejection classes may include:
- score insufficient
- gating failed
- spike veto
- SR veto
- feasibility failed
- focus rule rejected
- pre-stage denied
- confirm-stage denied
- open_now denied

The exact class set is defined by the decision-audit domain, but observability must record enough information to explain why a setup died or was not promoted.

Hard rule:
A materially relevant rejection path must not disappear without evidence.

---

## 9. TEMPORAL TELEMETRY OBSERVABILITY

Timing-sensitive behavior must produce dedicated evidence.

Typical temporal evidence may include:
- candle open/close reference
- signal creation time
- signal publish time
- expiry target
- outcome-activation window
- late signal suppression
- stale signal rejection
- timing drift or skew evidence

This domain aligns with:
- `TRADE_TEMPORAL_TELEMETRY_SPEC_v2.0.0.md`

---

## 10. FSM / STATE OBSERVABILITY

Every governed state transition must produce observable evidence.

Typical FSM/state event should include:
- previous state
- new state
- trigger reason
- signal_identity where applicable
- symbol
- timestamp
- transition result

Examples:
- IDLE → WATCHLIST
- WATCHLIST → PRE_VISIBLE
- PRE_VISIBLE → CONFIRM_VISIBLE
- CONFIRM_VISIBLE → OPEN_NOW_VISIBLE
- OPEN_NOW_VISIBLE → CLOSED
- any cooldown / suppression / dead-end transitions

No state transition may occur silently.

---

## 11. DISTRIBUTION OBSERVABILITY

Every governed distribution evaluation must produce observable evidence.

Typical fields include:
- route
- route_state_before
- route_state_after
- signal_identity
- stage
- delivery_decision
- counter_before
- counter_after
- destination mapping status
- transport result
- transport error where relevant

Canonical delivery decision families may include:
- PUBLISHED
- SKIPPED_SILENT
- SKIPPED_DISABLED
- SKIPPED_LIMIT
- FAILED
- DUPLICATE_SUPPRESSED

This domain aligns with:
- `SIGNAL_DISTRIBUTION_SPEC_v2.0.0.md`
- `CHANNEL_CONFIG_SPEC_v2.0.0.md`

---

## 12. RESET AND ROUTE-STATE OBSERVABILITY

Daily reset and route-state change behavior must be observable.

Observable events may include:
- daily_reset_executed
- route_became_silent
- route_reactivated
- route_disabled_by_config
- route_invalid_mapping
- reset_skipped_duplicate_guard

Baseline reset reference remains aligned with the distribution/config stack:
- 08:10 Europe/London

If the configured reset reference changes later, observability must surface the new truth clearly.

---

## 13. OUTCOME OBSERVABILITY

Outcome flows must be observable.

Typical outcome-related events include:
- outcome_panel_enabled
- outcome_submission_attempt
- outcome_submission_accepted
- outcome_submission_rejected
- outcome_window_closed
- duplicate_outcome_suppressed
- membership_verification_failed

Typical fields include:
- signal_identity
- user_id
- outcome_value
- validation_result
- timestamp
- entitlement/membership context where relevant

Canonical baseline outcome values remain:
- WIN
- LOSE
- MISSED

This domain aligns with:
- `OUTCOME_TRACKING_SPEC_v2.0.0.md`
- `PERFORMANCE_ANALYTICS_SPEC_v2.0.0.md`

---

## 14. ADMIN / CONTROL OBSERVABILITY

Every mutating admin or control action must produce observable evidence.

Typical action families include:
- symbol activation change
- route enable/disable change
- distribution reset
- parameter update
- guarded action approval/denial
- feature toggle mutation
- document-state management action where governed

Observable fields should include:
- admin_actor_id
- role/scope context
- action name
- before_state
- after_state
- approval context if guarded
- timestamp
- result

This domain aligns with:
- `ADMIN_CONTROL_SPEC_v2.0.0.md`
- `ADMIN_OPERATIONS_SPEC_v2.0.0.md`

---

## 15. SYSTEM / ERROR OBSERVABILITY

Critical runtime failures must be observable.

Typical system/error events include:
- engine_start
- engine_stop
- dependency_degraded
- telegram_publish_error
- storage_write_error
- config_load_error
- permission_error
- invariant_breach
- crash_loop_detected
- recovery_started
- recovery_completed

Severity families may include:
- INFO
- WARNING
- ERROR
- CRITICAL

Errors must not fail silently.
A failure that prevented an expected observable event should itself generate an observable failure event where possible.

---

## 16. ANOMALY OBSERVABILITY

BinaryBot must emit warnings or anomaly events when invariants are threatened.

Illustrative anomaly classes:
- WATCHLIST_OVERFLOW
- OPEN_NOW_WITHOUT_VALID_PATH
- COOLDOWN_BYPASS
- DUPLICATE_SIGNAL_ATTEMPT
- PARAMETER_MISSING
- ROUTE_COUNTER_CORRUPTION_SUSPECTED
- OUTCOME_LINKAGE_BROKEN
- TELEGRAM_DELIVERY_MISMATCH

These anomalies indicate possible logic faults, policy faults or production degradation.

---

## 17. DEDUPLICATION OBSERVABILITY

Deduplication behavior must itself be observable.

Legacy intuition remains valid:
- engine-side dedup often centers around symbol + candle context + stage
- distribution-side dedup centers around route + signal_identity + stage

Each dedup-relevant event should record:
- dedup basis or dedup class
- whether duplicate was detected
- action taken
- preserved signal identity where relevant

Duplicate suppression must not be invisible.

---

## 18. STORAGE BASELINE

The older file-based baseline remains acceptable.

Typical storage families may include paths such as:
- `/opt/binarybot/observability/`
- `/opt/binarybot/outcomes/`
- `/opt/binarybot/analytics/`

Example file families may include:
- engine_events.jsonl
- fsm_events.jsonl
- distribution_events.jsonl
- admin_proofs.jsonl
- error_events.jsonl
- outcomes.jsonl

However, these filenames are implementation/storage conventions, not the full canonical truth.

---

## 19. APPEND AND INTEGRITY RULES

Observability storage must preserve reconstruction integrity.

Hard requirements:
- append-oriented event recording
- no silent in-place deletion of historical evidence
- event order should be reconstructable
- writes should be durable enough for incident analysis
- corruption or write failure must itself be surfaced where possible

The observability layer is not allowed to quietly rewrite history.

---

## 20. LOG ROTATION

Log rotation is required to prevent uncontrolled disk growth.

Baseline operational parameters may include:
- max_file_size = 100MB
- max_files = 30
- compression = gzip

Rotation must not destroy required auditability prematurely.
Archive policy must remain compatible with retention and analytics needs.

---

## 21. RETENTION PRINCIPLES

Retention must reflect business, audit and analytics needs.

Legacy baseline remains directionally valid:
- engine logs: ~30 days
- distribution logs: ~30 days
- error logs: ~60 days
- admin proofs: long-lived / effectively permanent where required

However, actual retention policy must not delete logs still needed for:
- incident analysis
- strategy learning
- performance analytics
- governance review

---

## 22. TELEGRAM DEBUG / DIAGNOSTIC MIRRORING

The system may mirror selected decision/debug content into Telegram diagnostic destinations.

Examples may include:
- score breakdown
- gate results
- buffer calculation
- expiry calculation
- rejection summaries

These messages are secondary observability surfaces.
They do not replace the canonical persisted logs.

If Telegram debug views and persisted observability disagree, persisted observability is the source of truth unless proven corrupted.

---

## 23. LOG INTEGRITY RULE

Every materially visible action should be traceable across the relevant observability domains.

Examples:
- a visible Telegram signal should correlate to decision evidence, distribution evidence and any relevant timing/state evidence
- a route silence should correlate to counter and route-state evidence
- an accepted outcome should correlate to the signal identity and validation path
- an admin mutation should correlate to before/after state evidence

Missing expected evidence is itself an observability defect.

---

## 24. ANALYTICS DEPENDENCY

Analytics, summaries and intelligence outputs depend on base observability.

Typical source domains include:
- decision evidence
- distribution evidence
- FSM/state evidence
- temporal telemetry
- outcome evidence
- admin/control mutation evidence

These sources power:
- performance metrics
- conversion funnels
- route health summaries
- rejection analytics
- drift detection
- operational intelligence summaries

This domain aligns with:
- `PERFORMANCE_ANALYTICS_SPEC_v2.0.0.md`
- `CONTROL_PANEL_HIERARCHY_AND_INTELLIGENCE_SPEC_v2.0.0.md`

---

## 25. GOVERNANCE REQUIREMENTS

Observability is part of governance, not just debugging.

Therefore:
- control mutations must be provable
- delivery claims must be provable
- route entitlement behavior must be provable
- rejection behavior must be explainable
- changes to important config should be auditable
- incident review must have enough evidence to reach grounded conclusions

Observability that is too shallow for governance is not sufficient.

---

## 26. MIGRATION NOTES FROM LEGACY VERSION

The legacy observability specification established strong foundational ideas:
- no hidden logic
- no silent failures
- JSONL structured logs
- append-only intuition
- decision / FSM / distribution / outcome / error logging families
- deduplication visibility
- crash-loop detection
- retention and rotation baselines

However, it was still centered on a flatter event-file inventory and did not yet fully reflect:
- the new decision-audit model
- temporal telemetry as its own canonical domain
- route-governance distribution semantics
- role-scoped admin/control mutation auditability
- stronger link between observability and governance

This v2.0.0 specification preserves the strong foundations while upgrading observability into a broader canonical layer centered on:
- richer decision/rejection evidence
- explicit temporal telemetry
- governed distribution observability
- admin/control auditability
- analytics-ready correlation
- governance-grade reconstruction

---

End of OBSERVABILITY_LOGGING_SPEC_v2.0.0.md

## 21. Community Feedback and Member-Stats Observability Events

This section integrates bounded observability requirements from the merged Community Feedback and Privacy intake.

### 21.1 Feedback correlation key
All feedback entries must reference SIGNAL_ID. If SIGNAL_ID is missing, the event must be rejected, quarantined, or explicitly marked as non-correlatable according to downstream handling policy.

### 21.2 Required observability fields
Feedback/member-stat observability should capture at minimum timestamp_utc, signal_id, actor/member reference, event class, and action/result metadata needed for auditability.

### 21.3 Administrative audit event
ADMIN_VIEW_MEMBER_STATS is a required audit-grade observability event whenever an operator/admin accesses member statistics or related private feedback surfaces.
