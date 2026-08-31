# OBSERVABILITY_LOGGING_SPEC_v3.0.0.md

BinaryBot — Observability, Telemetry, Logging & Auditability Specification  
Version: 3.0.0  
Status: PROPOSED CANONICAL REPLACEMENT — OWNER REVIEW REQUIRED  
Proposed Path: `send/docs/canonical/proposed/OBSERVABILITY_LOGGING_SPEC_v3.0.0.md`  
Intended Active Path After Promotion: `send/docs/canonical/active/OBSERVABILITY_LOGGING_SPEC_v3.0.0.md`  
Owner: BinaryBot / DROPi Signals  
Governance Change: `CHANGE_ID 20260831-01`  
Supersedes upon promotion: `OBSERVABILITY_LOGGING_SPEC_v2.0.0.md`

---

## 0. PROPOSAL STATUS AND PRESERVATION RULE

This document is proposed only and is not active canonical truth until promoted.

It preserves the substantive v2.0.0 logging, retention, integrity, anomaly, decision, FSM, distribution, outcome, admin/control and analytics obligations unless explicitly clarified below.

The v3.0.0 change closes the missing post-FSM signal-execution observability layer and aligns implementation-level logging mechanics with:
- `OBSERVABILITY_SPEC_v2.0.0.md`;
- `SIGNAL_ENGINE_EXECUTION_SPEC_v2.0.0.md`;
- `FSM_DECISION_ENGINE_SPEC_v1.0.0.md`;
- proposed `EVENT_SCHEMA_SPEC_v3.0.0.md`;
- proposed `MODULE_INTERFACE_SPEC_v3.0.0.md`.

No runtime code change is authorized by this proposed document.

---

## 1. AUTHORITY DECLARATION

`OBSERVABILITY_SPEC_v2.0.0.md` remains the system policy and architecture authority for observability.

Upon promotion, this document becomes the implementation-level logging and telemetry contract and governs:
- event-family implementation mechanics;
- telemetry structure;
- structured logging requirements;
- persistence and retention mechanics;
- anomaly/error surfacing;
- execution-trace evidence;
- implementation-level correlation requirements.

Where policy conflicts with mechanics, `OBSERVABILITY_SPEC_v2.0.0.md` governs policy/architecture.

---

## 2. CORE PRINCIPLES

1. Every material decision path must produce observable evidence.
2. Every governed FSM/state transition must produce observable evidence.
3. Every materially relevant post-FSM signal-execution attempt must produce observable evidence.
4. Every distribution action must produce observable evidence.
5. Every user outcome interaction must produce observable evidence.
6. Every admin mutation must produce observable evidence.
7. Every critical failure must produce observable evidence.
8. No silent governed state change is allowed.
9. Observability must not mutate trading behavior.
10. Logs remain append-oriented and reconstruction-safe.
11. Strategy truth, FSM truth, execution truth and distribution truth must remain separately queryable.
12. A generic debug object is enrichment only; it cannot replace required semantic event families.

---

## 3. OBSERVABILITY DOMAINS

### 3.1 Decision observability
Strategy evaluation, DecisionObject evidence, scoring/gating evidence, promotion/rejection/no-signal evidence.

### 3.2 Temporal telemetry
Timing-sensitive signal, expiry and execution-window evidence.

### 3.3 FSM/state observability
Governed state transitions, lifecycle progression, blocking/suppression reasons, degradation/rejection semantics and persistence evidence.

### 3.4 Signal-execution observability — NEW explicit domain
Post-FSM execution gating, SignalEvent construction outcome, non-emission, block, skip, fail, defer and final emission outcome.

### 3.5 Distribution observability
Route resolution, entitlement decisions, publish attempts, route results and destination evidence.

### 3.6 Outcome observability
Outcome submission, validation, aggregation and reconciliation linkage.

### 3.7 Admin/control observability
Governed mutations, guarded actions and proof of change.

### 3.8 System/error observability
Runtime failures, dependency degradation, crash/recovery and invariant breaches.

### 3.9 Research/analytics observability
Derived metrics and summaries built from base evidence without mutating live behavior.

---

## 4. EVENT FORMAT BASELINE

Structured events remain the baseline.

Recommended storage remains:
- JSONL or equivalent structured append-oriented stream;
- one event record per material event;
- reconstruction-safe persistence.

Detailed canonical event names and payload contracts are governed by proposed `EVENT_SCHEMA_SPEC_v3.0.0.md` after promotion.

Example execution evidence:

```json
{
  "event_type": "signal_execution_result",
  "setup_correlation_id": "example-setup",
  "signal_id": "example-signal-id",
  "symbol": "EUR/USD",
  "direction": "BUY",
  "timeframe": "M1",
  "stage": "CONFIRM",
  "data": {
    "execution_outcome": "DEFERRED",
    "reason": "DISTRIBUTION_DISABLED",
    "fsm_outcome": "CONFIRM",
    "fsm_reason_family": "EXECUTION_PROGRESS",
    "fsm_execution_readiness": true,
    "fsm_degraded": false,
    "fsm_rejected": false,
    "fsm_handoff_disposition": "ACCEPTED",
    "destination_class": "DISTRIBUTION_DISABLED",
    "distribution_authorized": false,
    "distribution_attempted": false
  }
}
```

This is a semantic illustration, not authorization to hardcode values in runtime.

---

## 5. MINIMUM CORRELATION

To satisfy the root observability policy, materially relevant setup/execution evidence must support correlation of at least:
- setup correlation id;
- symbol;
- side/direction;
- timeframe or relevant temporal context;
- evaluation timestamp;
- cycle/run id where available;
- stage identifier where applicable;
- outcome family.

Additional common fields may include:
- event_id;
- trace_id;
- candidate/decision audit id;
- signal_id;
- execution_attempt_id;
- candle timestamp;
- route;
- destination class/id;
- message_id where applicable.

Not every event requires every field, but no materially relevant event may be ambiguous in context.

---

## 6. DECISION OBSERVABILITY

Every material strategy decision boundary must emit decision evidence.

Decision evidence may include:
- setup correlation id;
- symbol/timeframe/direction;
- market/candle context;
- score and governed components;
- gates;
- rejection semantics;
- model expiry/timing context;
- buffer context;
- DecisionObject representation/reference;
- decision result.

Canonical strategy decision families include:
- PRE;
- CONFIRM;
- OPEN_NOW;
- REJECT;
- NO_SIGNAL.

Hard separation rule:
A strategy decision event must not be used as the canonical container for the signal engine's post-FSM execution result.

---

## 7. REJECTION AND DECISION-AUDIT OBSERVABILITY

Material rejection must never disappear through absence of signal output.

Observable causes may include:
- score insufficient;
- structural/corridor gate failure;
- time feasibility failure;
- instability/spike veto;
- focus/watchlist restriction;
- pre-stage denial;
- confirm-stage denial;
- open-now denial.

Decision audit remains the authority for strategy-decision reason taxonomy.

Operational execution blockers must be logged separately in the signal-execution domain.

---

## 8. TEMPORAL TELEMETRY

The v2.0.0 temporal telemetry obligations remain preserved.

Timing-sensitive evidence may include:
- candle timing;
- signal creation time;
- publish time;
- expiry target;
- stale/late suppression;
- drift/skew evidence;
- outcome-activation timing.

---

## 9. FSM / STATE OBSERVABILITY

Every governed transition or materially relevant suppression result must be observable.

The FSM evidence required by the active root FSM specification must remain reconstructable, including:
- state/outcome;
- reason family;
- execution readiness;
- degradation status;
- rejection status;
- explanation snippets;
- handoff readiness;
- previous/resulting persisted state where relevant.

Additional context should include:
- setup correlation id;
- symbol/direction;
- requested stage where applicable;
- signal identity where applicable;
- timestamp;
- stage-acceptance disposition;
- state-change/persistence result.

Examples include:
- focus/watchlist entry;
- confirmation progression;
- cooldown block;
- watchlist-capacity suppression;
- duplicate stage/candle suppression;
- identity-continuity rejection;
- lifecycle-path rejection;
- degraded progression.

A transition event by itself must not be interpreted as proof that the requested stage was accepted for SignalEvent construction.

---

## 10. SIGNAL-EXECUTION OBSERVABILITY — NEW

### 10.1 Mandatory execution evidence

Every materially relevant post-FSM execution evaluation must produce a canonical `signal_execution_result` event once v3.0.0 is promoted and implemented.

It must distinguish:
- `EMITTED`;
- `NOT_EMITTED`;
- `BLOCKED`;
- `SKIPPED`;
- `FAILED`;
- `DEFERRED`.

### 10.2 Minimum trace

For each relevant execution attempt, observability must be able to reconstruct at minimum:
- execution attempt id;
- setup correlation id;
- signal id where an actionable lifecycle identity exists;
- symbol;
- side/direction;
- timeframe/temporal context;
- stage where applicable;
- execution outcome;
- reason/blocker/failure detail;
- timestamp;
- destination/channel class;
- payload, payload version or payload reference/status;
- FSM outcome;
- FSM reason family;
- FSM execution readiness;
- FSM degradation/rejection status;
- FSM handoff disposition/reason;
- explanation snippets directly or by correlated FSM evidence reference;
- whether distribution was authorized;
- whether distribution was attempted.

This implements the delivery-trace obligation from `SIGNAL_ENGINE_EXECUTION_SPEC_v2.0.0.md` without falsely calling a non-emitted path an emitted signal.

### 10.3 Pre-distribution destination semantics

If no concrete destination exists because routing has not started or distribution is disabled, the trace must use an explicit semantic destination class such as:
- `UNRESOLVED_PRE_DISTRIBUTION`;
- `DISTRIBUTION_DISABLED`.

Omission is not acceptable when the event is intended as the execution trace.

### 10.4 Candidate construction is not delivery

A validated PRE, CONFIRM or OPEN_NOW SignalEvent may exist internally only after explicit FSM acceptance while execution remains `DEFERRED` because distribution is not authorized.

SignalEvent construction alone:
- does not prove external visibility;
- does not prove a Telegram send;
- does not consume entitlement;
- does not register an outcome;
- does not justify `LIVE_SENT` or equivalent successful-delivery state.

### 10.5 No fabricated evidence

If required real evidence is unavailable, logging must record non-emission/failure semantics according to the approved execution contract.

The observability layer must never fabricate price, direction, expiry, signal identity, destination or payload data merely to fill a schema.

---

## 11. DISTRIBUTION OBSERVABILITY

The v2.0.0 distribution observability obligations remain preserved.

Every governed distribution evaluation must record enough evidence to reconstruct:
- route;
- route state before/after;
- signal identity;
- stage;
- destination mapping status;
- delivery decision;
- counter before/after;
- transport result/error;
- dedup result.

Per-route result families remain distinct from signal-engine execution outcomes.

Examples include:
- PUBLISHED;
- SKIPPED_SILENT;
- SKIPPED_DISABLED;
- SKIPPED_LIMIT;
- FAILED;
- DUPLICATE_SUPPRESSED.

---

## 12. RESET / ROUTE-STATE OBSERVABILITY

Daily reset, route silence/reactivation, invalid mapping and reset idempotency remain observable under the active distribution/configuration canon.

The baseline reset reference remains 08:10 Europe/London unless superseded elsewhere canonically.

---

## 13. OUTCOME OBSERVABILITY

The v2.0.0 outcome-observability obligations remain preserved.

Outcome evidence must remain linked to the governed signal identity and validation/eligibility context.

Outcome interaction must not be activated by an internal SignalEvent candidate when no governed external OPEN_NOW delivery occurred.

---

## 14. ADMIN / CONTROL OBSERVABILITY

Every mutating admin/control action remains proof-logged with sufficient before/after, actor, scope, approval and result context.

No admin command may bypass the canonical strategy/FSM/execution/distribution truth boundaries.

---

## 15. SYSTEM / ERROR OBSERVABILITY

Critical runtime failures remain observable.

Typical categories include:
- engine lifecycle;
- dependency degradation;
- storage errors;
- config errors;
- permission errors;
- invariant breaches;
- crash loops;
- recovery start/completion.

Errors preventing expected canonical evidence should themselves generate observable failure evidence where possible.

---

## 16. ANOMALY OBSERVABILITY

The v2 anomaly principle remains preserved.

Examples may include:
- WATCHLIST_OVERFLOW;
- OPEN_NOW_WITHOUT_VALID_PATH;
- COOLDOWN_BYPASS;
- DUPLICATE_SIGNAL_ATTEMPT;
- PARAMETER_MISSING;
- ROUTE_COUNTER_CORRUPTION_SUSPECTED;
- OUTCOME_LINKAGE_BROKEN;
- TELEGRAM_DELIVERY_MISMATCH;
- EXECUTION_WITHOUT_FSM_ACCEPTANCE;
- EXTERNAL_VISIBILITY_WITHOUT_EXECUTION_TRACE.

---

## 17. DEDUPLICATION OBSERVABILITY

Deduplication itself must remain observable.

At minimum:
- engine/stage dedup evidence;
- distribution route + signal_id + stage dedup evidence;
- duplicate detected flag;
- action taken;
- stable signal identity.

Duplicate/suppressed stage evidence must not be mislabeled as accepted execution.

---

## 18. STORAGE, ROTATION AND RETENTION

The substantive v2.0.0 storage, append-integrity, rotation and retention principles remain preserved.

Implementation conventions may evolve, but must preserve:
- append-oriented reconstruction;
- no silent historical rewrite;
- durable incident evidence;
- bounded storage growth;
- retention sufficient for audit, analytics and governance.

---

## 19. TELEGRAM DEBUG / DIAGNOSTIC MIRRORING

Diagnostic Telegram surfaces remain secondary views only.

They may display structured derived evidence but do not replace persisted canonical observability.

A debug message must never be treated as proof that an external governed signal stage was delivered unless corresponding canonical distribution evidence exists.

---

## 20. END-TO-END LOG INTEGRITY

A material signal lifecycle must be reconstructable across the applicable layers:

`decision evidence -> FSM evidence -> signal_execution_result -> route evidence -> external visibility evidence -> outcome/reconciliation`

A setup that dies earlier must still be reconstructable up to its stage of death.

Missing expected evidence is an observability defect.

---

## 21. ANALYTICS DEPENDENCY

Analytics and intelligence are downstream consumers of observability.

They may consume:
- decision evidence;
- FSM/state evidence;
- signal-execution evidence;
- distribution evidence;
- temporal telemetry;
- outcome evidence;
- admin/control evidence.

They must not mutate live trading behavior from observability processing alone.

---

## 22. GOVERNANCE REQUIREMENTS

Observability must provide enough evidence to prove:
- what strategy decided;
- what FSM outcome/reason/readiness/degradation/rejection semantics existed;
- what exact actionable stage FSM accepted, blocked, suppressed or rejected;
- what signal engine attempted and why;
- whether a canonical SignalEvent existed;
- whether distribution was authorized/attempted;
- where a signal was routed;
- whether delivery succeeded;
- whether entitlement changed;
- whether an outcome became eligible;
- what admin/control mutations occurred.

Shallow logging insufficient for these questions is not canonically adequate.

---

## 23. LEGACY EVENT MIGRATION

The current runtime schema may contain generic/legacy event families including:
- `decision`;
- `signal_event`;
- `tier_publish`;
- `tier_reset`.

After v3 promotion, these may remain only as explicit temporary compatibility aliases.

They must not remain the hidden primary semantic model.

Migration target:
- strategy decision events use canonical decision families;
- post-FSM execution uses `signal_execution_result`;
- real emission uses the approved `signal_emitted` boundary;
- distribution uses route-oriented event families.

The runtime schema validator must be updated only after canonical v3 promotion.

---

## 24. V3 MIGRATION SUMMARY

v3.0.0 preserves the established v2 observability system while adding the missing explicit signal-execution observability domain.

Primary v3 changes:
- mandatory `signal_execution_result` evidence;
- explicit execution outcome families;
- explicit root FSM semantic output and stage-acceptance correlation;
- explicit setup-correlation and direction requirements;
- explicit destination/payload trace before route selection;
- strict truth-layer separation;
- no false external-delivery semantics from internal SignalEvent construction;
- migration away from generic legacy runtime event families as primary truth.

---

## 25. PROMOTION GATE

This document may be promoted only when:
- `EVENT_SCHEMA_SPEC_v3.0.0.md` defines matching event semantics;
- `MODULE_INTERFACE_SPEC_v3.0.0.md` defines matching FSM/execution handoff semantics;
- Owner review accepts the contract;
- supersession and master-index updates are prepared;
- no runtime/code change is bundled into the canonical promotion.

Until promotion, `OBSERVABILITY_LOGGING_SPEC_v2.0.0.md` remains active.
