# EVENT_SCHEMA_SPEC_v3.0.0

BinaryBot — Canonical Event Envelope, Correlation & Domain Schema Specification  
Version: 3.0.0  
Status: PROPOSED COMPLETE SUCCESSOR — NOT ACTIVE CANONICAL  
Path: `send/docs/canonical/proposed/EVENT_SCHEMA_SPEC_v3.0.0.md`
Owner: BinaryBot / DROPi Signals

Supersession Intent: EVENT_SCHEMA_SPEC_v2.0.0.md

Linked Documents:
- OBSERVABILITY_SPEC_v3.0.0.md
- OBSERVABILITY_LOGGING_SPEC_v3.0.0.md
- MODULE_INTERFACE_SPEC_v3.0.0.md
- FSM_DECISION_ENGINE_SPEC_v2.0.0.md
- SIGNAL_ENGINE_EXECUTION_SPEC_v3.0.0.md
- PERFORMANCE_ANALYTICS_SPEC_v2.0.0.md
- SIGNAL_DISTRIBUTION_SPEC_v2.0.0.md
- CHANNEL_CONFIG_SPEC_v2.0.0.md
- TELEGRAM_UX_v2.0.0.md
- DECISION_AUDIT_SPEC_v2.0.0.md
- TRADE_TEMPORAL_TELEMETRY_SPEC_v2.0.0.md
- OUTCOME_TRACKING_SPEC_v2.0.0.md
- ADMIN_CONTROL_SPEC_v2.0.0.md
- ADMIN_OPERATIONS_SPEC_v2.0.0.md
- ROLE_AND_PERMISSION_MATRIX_SPEC_v2.0.0.md
- SYSTEM_INVARIANTS_v2.0.0.md
- FAILURE_RECOVERY_SPEC_v2.0.0.md
- GOVERNANCE_AND_CHANGE_CONTROL_v2.0.0.md

---

## 0. AUTHORITY AND PROMOTION STATUS

This document defines the complete proposed schema contract for structured events. It is self-contained and does not require EVENT_SCHEMA v2 to supply omitted normative rules.

Until explicit promotion, `EVENT_SCHEMA_SPEC_v2.0.0.md` remains active. This proposal does not authorize runtime schema/code changes by itself.

The major version reflects a structural event-contract change: signal-engine execution truth becomes a first-class event domain through `signal_execution_result` and legacy `signal_emitted` becomes compatibility-only for new v3 behavior.

---

## 1. PURPOSE

This document governs:
- common event envelope
- cross-domain correlation
- canonical event-family naming
- required/optional fields
- execution phase/outcome schema
- privacy/integrity rules
- minimum domain payload obligations
- migration/compatibility behavior

Strong foundations preserved:
- structured append-oriented evidence
- globally unique event IDs
- stable signal identity
- dedup observability
- counter correctness
- schema version discipline
- if material truth is not logged, observability is defective

---

## 2. CORE PRINCIPLES

1. Every materially relevant event is structurally representable.
2. Every event is reconstructable in context.
3. No silent governed-state mutation.
4. No ambiguous signal identity for lifecycle events.
5. Strategy, FSM, signal execution, distribution, visibility and outcome truth remain distinct.
6. Schema supports forensic reconstruction, analytics and governance.
7. Schema leaks no secrets or unnecessary personal data.
8. Schema evolution requires visible versioning and migration awareness.
9. Schema-invalid events are not trustworthy canonical evidence.
10. Historical events retain original schema/version meaning.

---

## 3. CANONICAL POSITION IN THE STACK

High-level relation:

`Runtime Behavior -> Structured Event Emission -> Persisted Observability -> Reconciliation -> Analytics -> Research / Intelligence / Governance`

The schema does not dictate storage backend, report rendering or dashboard UX. It defines event meaning and structure.

---

## 4. EVENT MODEL OVERVIEW

Every event contains:
1. common envelope;
2. correlation context;
3. domain payload;
4. integrity/privacy constraints.

---

## 5. COMMON EVENT ENVELOPE

### 5.1 Required common fields

- `event_id: string` — globally unique; UUID4-style recommended
- `event_type: string`
- `schema_version: string` — for this contract `3.0.0`
- `ts_utc: string` — ISO 8601 UTC with `Z`
- `ts_epoch_ms: integer`
- `service: string` — baseline `binarybot`
- `env: string` — e.g. prod/staging/dev
- `run_id: string`
- `source: object`
  - `module: string`
  - `function: string`
  - `line: integer | null`
- `host: object`
  - `hostname: string`
  - `pid: integer`
  - `app_version: string`
  - `git_sha: string | null`

### 5.2 Recommended common fields

- `ts_local`
- `trace_id`
- `severity`
- `algo`
  - `algo_version`
  - `params_hash`
  - `params_hash8`

### 5.3 Reusable correlation fields

- `setup_correlation_id`
- `execution_attempt_id`
- `signal_id`
- `symbol`
- `timeframe`
- `candle_ts_utc`
- `candle_ts_epoch`
- `route`
- `destination_id`
- `stage`
- `user_id`
- `admin_actor_id`
- `message_id`
- `thread_id`

Events include only the fields required by their domain but must remain reconstructable.

---

## 6. CANONICAL EVENT FAMILIES

### 6.1 System lifecycle
- `engine_start`
- `engine_stop`
- `recovery_started`
- `recovery_completed`
- `dependency_degraded`
- `config_load_error`

### 6.2 Decision / strategy
- `decision_evaluated`
- `decision_promoted`
- `decision_rejected`
- `decision_no_signal`

### 6.3 FSM / state
- `fsm_transition`

### 6.4 Signal execution
- `signal_execution_result`
- `duplicate_suppressed` where engine-side suppression is represented as a dedicated compatibility/support event

### 6.5 External signal lifecycle visibility
- `signal_stage_visible`
- `signal_closed`

### 6.6 Distribution / route governance
- `route_publish_attempt`
- `route_publish_result`
- `route_reset`
- `route_state_changed`
- `route_mapping_invalid`

### 6.7 Outcome / reconciliation
- `outcome_submission_attempt`
- `outcome_submission_result`
- `outcome_reconciled`
- `membership_verification_failed`

### 6.8 Admin / control
- `admin_change`
- `guarded_action_review`
- `feature_toggle_changed`
- `ADMIN_VIEW_MEMBER_STATS` where member-stat privacy audit is applicable

### 6.9 Warning / anomaly / error
- `warning`
- `anomaly`
- `error`
- `invariant_breach`

### 6.10 Legacy compatibility event families

`signal_emitted` is **compatibility-only** for new v3 behavior.

Historical `signal_emitted` records remain valid evidence under their original schema/version but MUST NOT be silently reinterpreted as `signal_execution_result` or `signal_stage_visible`.

Generic legacy names such as `decision`, `signal_event`, `tier_publish`, or `tier_reset` may be retained temporarily by runtime migration adapters only with explicit compatibility status. They are not the primary v3 family names.

---

## 7. ENUMERATION BASELINES

### 7.1 Engine mode
- WIDE_SCAN
- FOCUS_MODE

### 7.2 Signal stage
- PRE
- CONFIRM
- OPEN_NOW

### 7.3 Decision result
- PRE
- CONFIRM
- OPEN_NOW
- REJECT
- NO_SIGNAL

### 7.4 FSM readiness booleans
- `stage_handoff_ready: boolean`
- `trade_execution_ready: boolean`

### 7.5 Signal execution phase
- PRE_DISTRIBUTION
- POST_DISTRIBUTION

### 7.6 Signal execution outcome
- EMITTED
- NOT_EMITTED
- BLOCKED
- SKIPPED
- FAILED
- DEFERRED

### 7.7 Pre-distribution destination state
- PRE_DISTRIBUTION_UNRESOLVED

Additional destination states may be defined by future governed changes; route-level detail remains distribution-owned.

### 7.8 Route state
- ACTIVE
- SILENT
- DISABLED

### 7.9 Publish result
- PUBLISHED
- SKIPPED_SILENT
- SKIPPED_LIMIT
- SKIPPED_DISABLED
- FAILED
- DUPLICATE_SUPPRESSED

### 7.10 Outcome
- WIN
- LOSE
- MISSED

### 7.11 Severity
- INFO
- WARN
- ERROR
- CRITICAL

### 7.12 Session
- ASIA
- LONDON
- NY
- UNKNOWN

Baseline business routes remain FREE/BASIC/PRO/ELITE where active distribution canon uses them; route-oriented naming is preferred over legacy tier-oriented naming.

---

## 8. CORRELATION RULES

### 8.1 Event identity
Every event has globally unique `event_id`.

### 8.2 Signal identity
The same trade idea preserves the same `signal_id` across:
- PRE
- CONFIRM
- OPEN_NOW
- FSM handoff evidence where signal identity exists
- `signal_execution_result`
- distribution events
- `signal_stage_visible`
- outcome/reconciliation where applicable

### 8.3 Execution attempt identity
Every materially relevant signal-engine execution attempt has `execution_attempt_id`.

A PRE_DISTRIBUTION checkpoint and later POST_DISTRIBUTION result for the same execution attempt MAY share the same `execution_attempt_id` and MUST remain individually unique events through separate `event_id` values.

### 8.4 Trace identity
`trace_id` SHOULD connect events in the same logical runtime flow when available.

### 8.5 Domain linkage
A visible published signal stage should be linkable to upstream decision, FSM handoff, execution evidence, route publish evidence, temporal evidence and later outcome where applicable.

### 8.6 Contextual sufficiency
Syntactically valid JSON without sufficient correlation is a schema quality failure.

---

## 9. PRIVACY AND DATA MINIMIZATION

Hard rules:
- no secrets
- no API keys/tokens/credentials
- no unnecessary personal names, usernames, phone numbers
- no public user-identifiable data

Numeric Telegram IDs may be used only where operationally necessary in governed private evidence.

---

## 10. SCHEMA EVOLUTION

Schema changes require:
- version bump
- migration awareness
- updated linked references where relevant
- preserved/documented supersession of prior invariants
- explicit compatibility policy for renamed/retired event families

Breaking semantic changes require major-version discipline.

---

## 11. SYSTEM LIFECYCLE EVENTS

### `engine_start`
Context/payload includes as applicable:
- engine_mode
- loop_interval_ms
- selected symbol count
- buffer mode
- config health
- startup snapshot

### `engine_stop`
- reason
- uptime_sec
- last engine_mode

### recovery/dependency events
- recovery_scope
- reason
- result
- degraded_components

---

## 12. DECISION EVENTS

### 12.1 `decision_evaluated`
Required contextual fields:
- symbol
- timeframe
- candle context

Payload:
- decision_result
- score_total where relevant
- buffer_mode / canonical buffer semantics
- expiry/model timing where relevant
- session
- structured gates/evidence
- dedup context

This event is pre-FSM strategy truth. It MUST NOT be overloaded as the sole record of downstream execution truth.

### 12.2 `decision_promoted`
- signal_id
- decision_result
- score_total where relevant
- promotion reason/context

### 12.3 `decision_rejected`
- rejection_reason
- rejection_class
- relevant gate/evidence

### 12.4 `decision_no_signal`
Used when evaluation completes with no actionable signal and no meaningful rejection class.

---

## 13. FSM / STATE EVENTS

### 13.1 `fsm_transition`
Required/conditional payload:
- from_state
- to_state
- reason
- requested_stage where applicable
- accepted_stage where applicable
- `stage_handoff_ready`
- `trade_execution_ready`
- signal_id where applicable
- watchlist/focus context where relevant
- cooldown context where relevant
- invariant checks
- persisted state result where relevant

A transition event is FSM truth. It does not itself prove publication or SignalEvent construction.

---

## 14. SIGNAL EXECUTION EVENTS

### 14.1 `signal_execution_result`

Purpose: represent signal-engine execution truth after FSM handoff and distinctly from strategy/FSM/route truth.

Required contextual fields:
- `execution_attempt_id`
- `symbol`
- common envelope timestamps/run_id

Required when attempt concerns actionable lifecycle stage:
- `signal_id`
- `stage: PRE | CONFIRM | OPEN_NOW`
- `timeframe` where originating contract provides it

Optional when no actionable signal identity exists:
- `setup_correlation_id`

Required payload:
- `execution_phase: PRE_DISTRIBUTION | POST_DISTRIBUTION`
- `execution_outcome: EMITTED | NOT_EMITTED | BLOCKED | SKIPPED | FAILED | DEFERRED`
- `execution_reason: string`
- `stage_handoff_ready: boolean`
- `trade_execution_ready: boolean`
- `signal_event_available: boolean`
- `destination_state: string`

Conditionally required:
- candidate/payload reference when `signal_event_available=true`
- distribution references for POST_DISTRIBUTION results derived from downstream evidence
- publication evidence reference(s) when `execution_outcome=EMITTED`

Recommended:
- FSM handoff reference/summary
- DecisionObject reference/summary
- blocker/failure detail
- candidate schema version

### 14.2 PRE_DISTRIBUTION mapping

If a valid SignalEvent exists while distribution is intentionally disabled/not invoked:
- phase = PRE_DISTRIBUTION
- outcome = DEFERRED
- signal_event_available = true
- destination_state = PRE_DISTRIBUTION_UNRESOLVED

EMITTED is forbidden in PRE_DISTRIBUTION.

If candidate cannot be formed:
- NOT_EMITTED may represent non-technical absence;
- BLOCKED may represent explicit rule/invariant blocker;
- SKIPPED may represent explicit flow skip;
- FAILED may represent technical execution-layer failure.

### 14.3 POST_DISTRIBUTION mapping

EMITTED is allowed only if linked downstream evidence proves at least one authorized publication succeeded.

Mixed route results MAY yield execution outcome EMITTED when at least one authorized route published successfully, provided all per-route failures/skips remain intact in route events.

Signal-engine event must never fabricate per-route detail.

---

## 15. SIGNAL LIFECYCLE VISIBILITY EVENTS

### 15.1 `signal_stage_visible`
Used when a lifecycle stage becomes externally visible through governed successful publication.

Required payload/context:
- signal_id
- stage
- route/destination reference
- message_id where available
- visibility_result
- correlation to successful publication evidence

### 15.2 `signal_closed`
- signal_id
- close_reason
- close timestamp

### 15.3 Legacy `signal_emitted`
Compatibility-only for new v3 behavior.

A SignalEvent candidate built pre-distribution MUST produce neither `signal_stage_visible` nor a new primary `signal_emitted` proof.

---

## 16. DISTRIBUTION / ROUTE EVENTS

### 16.1 `route_publish_attempt`
Required:
- route
- signal_id
- stage
- destination_id where resolved

Payload:
- route_state_before
- counter_before
- limit where applicable
- mapping status
- dedup context

### 16.2 `route_publish_result`
Payload:
- publish_result
- route_state before/after
- counter before/after
- counted
- transport result
- dedup evidence

### 16.3 `route_reset`
- reset reference
- effective date
- route before/after state/counters
- idempotence
- persisted status

### 16.4 `route_state_changed`
- route
- from_state
- to_state
- reason

### 16.5 `route_mapping_invalid`
- route
- mapping status
- reason

Route events are the source of exact route/destination publication truth.

---

## 17. OUTCOME EVENTS

### `outcome_submission_attempt`
- signal_id
- user_id
- route/entitlement context where relevant
- outcome
- eligibility window
- submission channel
- membership result where relevant

### `outcome_submission_result`
- accepted
- rejected_reason where applicable
- policy context
- aggregate snapshot where applicable

### `outcome_reconciled`
- signal_id
- operational outcome
- telemetry outcome where available
- discrepancy status
- reconciliation result

### `membership_verification_failed`
- route
- user_id
- failure_reason

---

## 18. ADMIN / CONTROL EVENTS

### `admin_change`
Required admin_actor_id and payload action/before/after/scope/proof/persisted.

### `guarded_action_review`
- action
- requested_by
- review_result
- reason

### `feature_toggle_changed`
- toggle_name
- before/after
- scope
- persisted

### `ADMIN_VIEW_MEMBER_STATS`
Audit-grade evidence for authorized access to private member statistics/feedback surfaces.

---

## 19. WARNING / ANOMALY / ERROR EVENTS

### warning
- severity
- code
- message
- context

### anomaly
- code
- message
- suspected impact
- context

### error
- severity
- error_type
- message
- stack where available
- context

### invariant_breach
- invariant name
- breach reason
- context
- severity

---

## 20. DEDUPLICATION RULES

Baseline:
- engine-side: symbol + candle context + stage, or stronger governed key
- distribution-side: route + signal_id + stage, or stronger governed key

Every dedup-relevant event records:
- dedup key/class
- owning layer
- duplicate detected
- action taken
- preserved signal identity

Duplicate suppression must be observable and must not silently mutate lifecycle identity.

---

## 21. COUNTER / ENTITLEMENT INTEGRITY

Only successful OPEN_NOW publication to a limited governed route may consume entitlement where distribution canon requires it.

Evidence includes:
- stage
- publish_result
- counted
- counter_before/after
- route

SignalEvent construction or execution outcome DEFERRED never consumes publication entitlement.

---

## 22. PERSISTENCE / STORAGE COMPATIBILITY

JSONL split by domain remains acceptable but not mandatory.

Whichever storage is used must:
- preserve reconstructability
- avoid silent evidence deletion/rewrites
- preserve domain meaning
- surface write failures where possible

---

## 23. INTEGRITY RULES

Hard rules:
1. stable signal_id across same trade idea;
2. globally unique event_id;
3. execution attempt identity preserved across its checkpoints;
4. dedup observable;
5. entitlement mutation provable;
6. state mutations reconstructable;
7. schema-invalid events are not canonical proof;
8. historical events retain their original schema meaning;
9. execution truth cannot exist solely in generic DecisionObject debug;
10. SignalEvent candidate cannot be represented as successful external delivery.

---

## 24. MIGRATION REQUIREMENTS

Before active promotion/implementation:
1. this complete v3 schema is approved/promoted;
2. OBSERVABILITY v3, OBSERVABILITY_LOGGING v3, MODULE_INTERFACE v3, FSM v2 and SIGNAL_ENGINE_EXECUTION v3 align;
3. legacy `signal_emitted` status is documented as compatibility-only for new v3 behavior;
4. generic runtime event aliases receive explicit migration mappings;
5. runtime `send/schema/event_schema.json` is changed only in a later code PR;
6. schema-validation tests cover all execution phases/outcomes;
7. historical events are not silently reinterpreted;
8. active canonical references are repaired atomically.

---

## 25. NO-CODE / NO-DISTRIBUTION RULE

This proposed document authorizes no runtime code changes and no distribution activation.

Until promotion:
- EVENT_SCHEMA v2 remains active;
- runtime schema remains unchanged;
- PR #73 remains blocked.

---

End of EVENT_SCHEMA_SPEC_v3.0.0.