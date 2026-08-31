# OBSERVABILITY_LOGGING_SPEC_v3.0.0

BinaryBot — Observability, Telemetry, Logging & Auditability Specification  
Version: 3.0.0  
Status: PROPOSED COMPLETE SUCCESSOR — NOT ACTIVE CANONICAL  
Path: `send/docs/canonical/proposed/OBSERVABILITY_LOGGING_SPEC_v3.0.0.md`
Owner: BinaryBot / DROPi Signals

Supersession Intent: OBSERVABILITY_LOGGING_SPEC_v2.0.0.md

---

## 0. AUTHORITY DECLARATION AND PROMOTION STATUS

This document is the proposed **implementation-level logging and telemetry contract** for BinaryBot observability.

- It defers to `OBSERVABILITY_SPEC_v3.0.0.md` for system policy and observability architecture.
- It governs event-family logging obligations, telemetry structure, persistence/retention mechanics, anomaly surfacing and implementation-level evidence detail.
- `EVENT_SCHEMA_SPEC_v3.0.0.md` governs event envelope and field-level structural validity.
- No logging mechanic may contradict observability policy or event schema.

This is a complete proposed successor. Until explicit promotion, `OBSERVABILITY_LOGGING_SPEC_v2.0.0.md` remains active. Merge of this file alone does not authorize runtime changes.

Linked Documents:
- OBSERVABILITY_SPEC_v3.0.0.md
- EVENT_SCHEMA_SPEC_v3.0.0.md
- FSM_DECISION_ENGINE_SPEC_v2.0.0.md
- SIGNAL_ENGINE_EXECUTION_SPEC_v3.0.0.md
- MODULE_INTERFACE_SPEC_v3.0.0.md
- DECISION_AUDIT_SPEC_v2.0.0.md
- TRADE_TEMPORAL_TELEMETRY_SPEC_v2.0.0.md
- SIGNAL_DISTRIBUTION_SPEC_v2.0.0.md
- CHANNEL_CONFIG_SPEC_v2.0.0.md
- TELEGRAM_UX_v2.0.0.md
- OUTCOME_TRACKING_SPEC_v2.0.0.md
- PERFORMANCE_ANALYTICS_SPEC_v2.0.0.md
- ADMIN_CONTROL_SPEC_v2.0.0.md
- ADMIN_OPERATIONS_SPEC_v2.0.0.md
- ROLE_AND_PERMISSION_MATRIX_SPEC_v2.0.0.md
- CONTROL_PANEL_HIERARCHY_AND_INTELLIGENCE_SPEC_v2.0.0.md
- SYSTEM_INVARIANTS_v2.0.0.md
- FAILURE_RECOVERY_SPEC_v2.0.0.md
- GOVERNANCE_AND_CHANGE_CONTROL_v2.0.0.md

---

## 1. PURPOSE

This document defines:
- what must be logged/observable
- event-family logging obligations
- correlation mechanics
- persistence/retention principles
- anomaly/failure surfacing
- governance proof requirements
- execution-result logging after FSM handoff

Core rule:
**If a materially relevant event is not observable, it is an observability failure.**

---

## 2. PRINCIPLES

1. Every material decision path produces evidence.
2. Every governed FSM transition/handoff produces evidence.
3. Every material signal-engine execution attempt produces evidence.
4. Every governed distribution action produces evidence.
5. Every user outcome interaction produces evidence.
6. Every admin mutation produces evidence.
7. Every critical failure produces evidence.
8. No silent state changes.
9. Observability must not mutate trading behavior.
10. Logs are append-oriented and reconstruction-safe.
11. Evidence supports machine analytics and human incident review.
12. Truth domains remain separate and correlated, not flattened.

---

## 3. OBSERVABILITY DOMAINS

### 3.1 Decision observability
Decision creation, scoring/gating evidence, rejection and promotion truth.

### 3.2 Temporal telemetry
Timing-sensitive signal, expiry and execution-window evidence.

### 3.3 FSM/state observability
Transitions, trigger reasons, exact-stage handoff, readiness and suppression/block semantics.

### 3.4 Signal-execution observability
SignalEvent candidate construction and signal-engine execution outcomes.

### 3.5 Distribution observability
Route resolution, entitlement, publish attempts/results, route state and transport truth.

### 3.6 Outcome observability
User outcomes, validation and reconciliation.

### 3.7 Admin/control observability
Governed mutations and guarded actions.

### 3.8 System/error observability
Runtime failures, dependencies, recovery and invariant breaches.

### 3.9 Research/analytics observability
Derived metrics/summaries traceable to base evidence.

---

## 4. OBSERVABILITY IS A LAYER, NOT A FILE LIST

Storage filenames/backends may evolve. Semantic obligations do not.

Operational implementations may use split or merged JSONL streams, databases or equivalent append/reconstruction-safe storage, provided event semantics remain canonical.

---

## 5. EVENT FORMAT BASELINE

Structured events are baseline.

Recommended implementation:
- JSONL
- one event per record
- append-oriented storage

All canonical events must validate against `EVENT_SCHEMA_SPEC_v3.0.0.md` after that schema becomes active.

---

## 6. MINIMUM CORRELATION FIELDS

Relevant events carry enough context for reconstruction. Common fields include:
- event_id
- event_type
- schema_version
- timestamp fields
- run_id
- trace_id where available
- signal_id where applicable
- symbol
- timeframe
- candle context
- stage
- execution_attempt_id for execution domain
- route/destination references for distribution domain
- user/admin identifiers only where governed and private

Not every event needs every field; every event needs sufficient context.

---

## 7. DECISION OBSERVABILITY

Every symbol evaluation cycle that reaches a material decision boundary emits evidence including, as applicable:
- symbol/timeframe/candle context
- score/components
- gating results
- rejection reasons
- expiry/timing context
- buffer context
- decision result

Canonical decision families include:
- PRE
- CONFIRM
- OPEN_NOW
- REJECT
- NO_SIGNAL

Decision evidence remains strategy truth and must not be overloaded with downstream execution truth.

---

## 8. REJECTION AND DECISION-AUDIT OBSERVABILITY

Material rejection paths must not disappear.

Observable rejection classes may include score/gate/spike/SR/feasibility/focus/stage denial classes as governed by Decision Audit and strategy canon.

Observability records enough evidence to explain why a setup died or was not promoted.

---

## 9. TEMPORAL TELEMETRY

Timing-sensitive evidence includes where applicable:
- candle reference
- decision/signal creation time
- publication time
- expiry target
- outcome activation window
- stale/late suppression
- timing drift/skew

This remains aligned with trade-temporal telemetry canon.

---

## 10. FSM / STATE OBSERVABILITY

Every governed FSM transition and every materially relevant exact-stage handoff emits evidence.

Minimum semantics where applicable:
- previous state
- new state
- trigger/reason
- requested_stage
- accepted_stage
- signal_id
- state_changed
- `stage_handoff_ready`
- `trade_execution_ready`
- lifecycle/identity continuity status
- blocker/suppression class
- persisted status

No state transition occurs silently.
No transition event alone may be logged as proof of stage release.

---

## 11. SIGNAL EXECUTION OBSERVABILITY

Every material execution attempt must produce `signal_execution_result` after the v3 schema is active.

Required correlation:
- common envelope
- `execution_attempt_id`
- symbol
- signal_id where applicable
- stage where applicable
- timeframe where applicable
- run_id
- timestamp

Required payload:
- `execution_phase`
- `execution_outcome`
- `execution_reason`
- `stage_handoff_ready`
- `trade_execution_ready`
- `signal_event_available`
- `destination_state`

Conditionally required:
- candidate/payload reference when SignalEvent exists
- distribution reference(s) in POST_DISTRIBUTION when downstream evidence exists

Recommended:
- FSM handoff reference/summary
- DecisionObject reference/summary
- blocker/failure detail
- candidate schema version

---

## 12. EXECUTION PHASE RULES

### 12.1 PRE_DISTRIBUTION

When SignalEvent exists but routing is intentionally disabled/not invoked:
- `execution_phase = PRE_DISTRIBUTION`
- `execution_outcome = DEFERRED`
- `destination_state = PRE_DISTRIBUTION_UNRESOLVED`
- `signal_event_available = true`

No route_publish_attempt/result may be fabricated.  
No external visibility may be claimed.  
EMITTED is forbidden.

If no candidate exists:
- NOT_EMITTED, BLOCKED, SKIPPED or FAILED may be used only according to the execution contract and with explicit reason.

### 12.2 POST_DISTRIBUTION

When downstream distribution evidence exists:
- `execution_phase = POST_DISTRIBUTION`
- event references relevant distribution evidence;
- EMITTED requires proof of at least one successful authorized publication;
- exact route-level success/failure/skip remains in route events.

The same `execution_attempt_id` may correlate pre- and post-distribution checkpoints.

---

## 13. READINESS LOGGING

`stage_handoff_ready` and `trade_execution_ready` must remain distinct.

- PRE: may have stage_handoff_ready=true; trade_execution_ready=false.
- CONFIRM: may have stage_handoff_ready=true; trade_execution_ready=false.
- OPEN_NOW: may have both true after valid acceptance/actionability.

No logger, report or dashboard may infer one from the other incorrectly.

---

## 14. EXECUTION OUTCOME SEPARATION

Signal-engine outcomes:
- EMITTED
- NOT_EMITTED
- BLOCKED
- SKIPPED
- FAILED
- DEFERRED

Route publish outcomes remain owned by distribution events and must not be used as substitutes for execution outcomes.

SignalEvent construction alone is never EMITTED.

---

## 15. DISTRIBUTION OBSERVABILITY

Every governed distribution evaluation must produce route-level evidence.

Typical fields:
- route
- route state before/after
- signal_id
- stage
- delivery decision
- counter before/after
- destination mapping status
- transport result/error
- dedup evidence

Canonical publish-result families remain defined by distribution/event-schema contracts, including PUBLISHED, skip families, FAILED and DUPLICATE_SUPPRESSED.

---

## 16. RESET AND ROUTE-STATE OBSERVABILITY

Daily reset and route-state changes are observable.

Events may include:
- route_reset
- route_state_changed
- route_mapping_invalid
- duplicate reset suppression

The effective reset reference must match active distribution/config truth and be explicitly logged.

---

## 17. OUTCOME OBSERVABILITY

Outcome flows are observable, including:
- panel/eligibility activation where governed
- submission attempt/result
- window closure
- duplicate suppression
- membership verification failure
- reconciliation

Required correlation includes signal identity and governed user context.

Baseline outcome values:
- WIN
- LOSE
- MISSED

---

## 18. ADMIN / CONTROL OBSERVABILITY

Every mutating admin/control action produces evidence including:
- admin_actor_id
- role/scope
- action
- before/after state
- approval context where guarded
- timestamp
- result
- persisted/proof status

Admin evidence does not expose secrets or unauthorized private data.

---

## 19. SYSTEM / ERROR OBSERVABILITY

Critical events include:
- engine_start / engine_stop
- dependency_degraded
- telegram_publish_error
- storage_write_error
- config_load_error
- permission_error
- invariant_breach
- crash_loop_detected
- recovery_started/completed

Severity baseline:
- INFO
- WARNING/WARN according to schema normalization
- ERROR
- CRITICAL

Errors must not fail silently.

---

## 20. ANOMALY OBSERVABILITY

Invariant threats emit warnings/anomalies, e.g.:
- WATCHLIST_OVERFLOW
- OPEN_NOW_WITHOUT_VALID_PATH
- COOLDOWN_BYPASS
- DUPLICATE_SIGNAL_ATTEMPT
- PARAMETER_MISSING
- ROUTE_COUNTER_CORRUPTION_SUSPECTED
- OUTCOME_LINKAGE_BROKEN
- TELEGRAM_DELIVERY_MISMATCH
- STAGE_HANDOFF_INCONSISTENT
- EMITTED_WITHOUT_PUBLICATION_EVIDENCE

---

## 21. DEDUPLICATION OBSERVABILITY

Dedup must itself be observable.

Baseline ownership:
- engine-side: symbol/candle/stage or stronger governed key
- distribution-side: route/signal_id/stage or stronger governed key

Record:
- dedup class/key basis
- duplicate detected or not
- action taken
- signal identity
- owning layer

---

## 22. STORAGE BASELINE

Acceptable storage families may include:
- `/opt/binarybot/observability/`
- `/opt/binarybot/outcomes/`
- `/opt/binarybot/analytics/`

Example streams:
- engine_events.jsonl
- fsm_events.jsonl
- execution_events.jsonl
- distribution_events.jsonl
- admin_proofs.jsonl
- error_events.jsonl
- outcomes.jsonl

Filenames are implementation conventions, not semantic authority.

---

## 23. APPEND AND INTEGRITY RULES

Hard requirements:
- append-oriented recording
- no silent historical deletion/rewrite
- reconstructable ordering
- sufficient durability for incident analysis
- write/corruption failures surfaced where possible
- schema-invalid events not treated as trustworthy canonical evidence

---

## 24. LOG ROTATION

Rotation is required to control storage growth.

Directional baseline may include:
- max file size ~100MB
- max files ~30
- gzip compression

Rotation must not destroy evidence still required by retention, incident, analytics or governance obligations.

---

## 25. RETENTION PRINCIPLES

Directional baseline remains:
- engine/execution/distribution logs ~30 days minimum operational window unless stronger policy applies
- error logs ~60 days directional baseline
- admin proofs long-lived where required

Retention may be longer when needed for incidents, learning, analytics or governance.

---

## 26. TELEGRAM DEBUG / DIAGNOSTIC MIRRORING

Selected structured evidence may be mirrored into Telegram diagnostics, including score/gates/buffer/expiry/rejection/execution summaries.

Telegram mirrors are secondary surfaces and never replace persisted evidence.

---

## 27. LOG INTEGRITY / CROSS-DOMAIN TRACE RULE

Every materially visible action must correlate across relevant domains.

Examples:
- visible signal stage -> decision + FSM + execution + distribution + visibility evidence
- route silence -> route-state/counter evidence
- accepted outcome -> signal/publication linkage + validation
- admin mutation -> before/after + actor + proof

Missing expected evidence is an observability defect.

---

## 28. ANALYTICS DEPENDENCY

Analytics/intelligence derive from base observability domains:
- decision
- FSM
- execution
- distribution
- temporal telemetry
- outcomes
- admin/control

Derived layers must not rewrite base truth.

---

## 29. GOVERNANCE REQUIREMENTS

Observability is governance infrastructure.

Therefore:
- control mutations are provable
- delivery claims are provable
- execution outcomes are provable
- route entitlement behavior is provable
- rejection behavior is explainable
- important config changes are auditable
- incident review has sufficient evidence

---

## 30. LEGACY EVENT COMPATIBILITY

Historical records retain their original schema/version meaning.

Legacy `signal_emitted`:
- may remain readable as v2/historical evidence;
- must not be silently reinterpreted as v3 `signal_execution_result` or `signal_stage_visible`;
- after v3 migration, it is compatibility-only for new behavior unless a specific migration contract says otherwise.

Generic runtime event names may coexist temporarily only with explicit compatibility status and migration tests.

---

## 31. COMMUNITY FEEDBACK AND MEMBER-STATS OBSERVABILITY

Existing bounded requirements remain:
- feedback entries reference `signal_id`; missing identity is rejected/quarantined/marked non-correlatable according to policy;
- feedback/member-stat evidence captures timestamp, signal identity, actor/member reference, event class, action/result metadata;
- `ADMIN_VIEW_MEMBER_STATS` is an audit-grade event whenever authorized operators access private member-stat/feedback surfaces.

These requirements do not alter signal execution truth.

---

## 32. FAILURE LOGGING

Failure to persist a materially required `signal_execution_result` or other governed event must itself be surfaced as an observability failure where possible, without mutating the underlying trading decision merely to compensate for missing logging.

---

## 33. PROMOTION AND MIGRATION RULE

At promotion:
- v3 becomes the sole active logging/telemetry authority;
- v2 moves to `canonical/superseded` with traceability;
- all active references are repaired atomically;
- EVENT_SCHEMA v3 and OBSERVABILITY v3 must be promoted compatibly;
- runtime logging changes occur only in a later code PR after post-promotion canonical re-audit;
- historical event meaning is preserved.

---

## 34. FINAL RULE

If a materially relevant strategy, FSM, execution, distribution, outcome, admin or failure event cannot be reconstructed from governed evidence, observability is non-compliant.

End of OBSERVABILITY_LOGGING_SPEC_v3.0.0.