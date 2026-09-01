# EVENT_SCHEMA_SPEC_v3.0.0

BinaryBot — Canonical Event Envelope, Correlation & Domain Schema Specification  
Version: 3.0.0  
Status: ACTIVE CANONICAL  
Owner: BinaryBot / DROPi Signals  
Supersedes: `EVENT_SCHEMA_SPEC_v2.0.0.md`  

Scope includes:
- common event envelope;
- cross-domain correlation;
- decision/FSM/execution/distribution/outcome/admin events;
- staged-execution truth separation;
- Trade Physics evidence/version lineage;
- learned-probability identity separation.

Linked proposed/current authorities:
- Root Strategy Stack successor
- `ALGO_SPEC_v3.0.0.md`
- `TRADE_PHYSICS_MODEL_SPEC_v1.0.0.md`
- `TRADE_PHYSICS_INTELLIGENCE_SPEC_v1.0.0.md`
- `DECISION_OBJECT_CANONICAL_SPEC_v2.0.0.md`
- `FSM_DECISION_ENGINE_SPEC_v2.0.0.md`
- `SIGNAL_ENGINE_EXECUTION_SPEC_v3.0.0.md`
- `MODULE_INTERFACE_SPEC_v3.0.0.md`
- `OBSERVABILITY_SPEC_v3.0.0.md`
- `OBSERVABILITY_LOGGING_SPEC_v3.0.0.md`
- `TRADE_TEMPORAL_TELEMETRY_SPEC_v3.0.0.md`
- `OUTCOME_TRACKING_SPEC_v3.0.0.md`
- Distribution/Channel/Admin/Security canonical documents

---

## 0. Authority and promotion status

This document is the active canonical successor and does not depend on v2 to supply omitted normative behavior.

Promotion status: ACTIVE CANONICAL under `CANONICAL_ACTIVATION_RECORD_20260901.md` and `CANONICAL_MASTER_INDEX_v2.0.0.md`.

The major version is required because:
- post-FSM signal-execution truth becomes a first-class event domain;
- legacy `signal_emitted` semantics are clarified/reduced to compatibility for new behavior;
- Trade Physics and learned-model evidence require explicit schema/version separation.

---

## 1. Core principles

1. Every materially relevant governed event must be structurally representable.
2. Every event must be reconstructable in context.
3. No silent governed-state mutation.
4. Stable signal identity across one trade idea lifecycle.
5. Strategy, FSM, Signal Engine, Distribution, visibility, telemetry and operational outcomes are separate truth domains.
6. Deterministic TPS and learned probability are separate values with separate semantics.
7. Historical events retain original schema meaning.
8. Schema evolution is versioned and migration-aware.
9. Invalid or insufficiently correlated events are degraded evidence.
10. Secrets and unnecessary personal data are forbidden.

---

## 2. Common envelope

Every canonical event includes:
- `event_id: string` — globally unique;
- `event_type: string`;
- `schema_version: string`;
- `ts_utc: string` — ISO-8601 UTC;
- `ts_epoch_ms: integer`;
- `service: string`;
- `env: string`;
- `run_id: string`;
- `source.module: string`;
- `source.function: string`;
- `source.line: integer|null`;
- host/process/application version context where available.

Recommended:
- `trace_id`;
- severity;
- git SHA;
- algo/strategy version;
- parameter hash/version.

---

## 3. Reusable correlation fields

Depending on domain:
- `setup_correlation_id`;
- `decision_id`;
- `decision_audit_id`;
- `execution_attempt_id`;
- `signal_id`;
- `symbol`;
- `direction`;
- `timeframe`;
- candle timestamp;
- `stage`;
- route/destination identifiers;
- telemetry record id;
- outcome/reconciliation id;
- admin actor id;
- message/thread id where operationally required.

Events need only applicable fields, but must remain reconstructable.

---

## 4. Canonical event families

### 4.1 System lifecycle
- `engine_start`
- `engine_stop`
- `recovery_started`
- `recovery_completed`
- `dependency_degraded`
- `config_load_error`

### 4.2 Decision / strategy
- `candidate_detected` where separately materialized
- `decision_evaluated`
- `decision_promoted`
- `decision_rejected`
- `decision_no_signal`

### 4.3 FSM
- `fsm_transition`

### 4.4 Signal execution
- `signal_execution_result`
- `duplicate_suppressed` where engine-side dedicated compatibility/support evidence is used

### 4.5 External lifecycle visibility
- `signal_stage_visible`
- `signal_closed`

### 4.6 Distribution
- `route_publish_attempt`
- `route_publish_result`
- `route_reset`
- `route_state_changed`
- `route_mapping_invalid`

### 4.7 Telemetry / outcome
- telemetry events defined by the telemetry implementation contract where eventized
- `outcome_submission_attempt`
- `outcome_submission_result`
- `outcome_reconciled`
- membership verification failure where applicable

### 4.8 Admin/control/governance
- `admin_change`
- `guarded_action_review`
- `feature_toggle_changed`
- parameter/model approval events where governed by their owner documents

### 4.9 Warning/anomaly/error
- `warning`
- `anomaly`
- `error`
- `invariant_breach`

---

## 5. Legacy compatibility event families

`signal_emitted` is compatibility/history only for new v3 behavior.

New primary truth uses:
- `signal_execution_result` — Signal Engine truth;
- `route_publish_result` — route publication truth;
- `signal_stage_visible` — governed external visibility.

Historical `signal_emitted` events remain valid under their original schema and must not be silently reinterpreted.

Legacy generic names such as `decision`, `signal_event`, `tier_publish`, `tier_reset` may exist in explicit migration adapters only; they are not primary v3 names.

---

## 6. Core enumerations

### Signal stage
- PRE
- CONFIRM
- OPEN_NOW

### Decision result
- PRE
- CONFIRM
- OPEN_NOW
- REJECT
- NO_SIGNAL

### FSM readiness
- `stage_handoff_ready: boolean`
- `trade_execution_ready: boolean`

### Signal execution phase
- PRE_DISTRIBUTION
- POST_DISTRIBUTION

### Signal execution outcome
- EMITTED
- NOT_EMITTED
- BLOCKED
- SKIPPED
- FAILED
- DEFERRED

### Pre-distribution destination state
- PRE_DISTRIBUTION_UNRESOLVED

### Route state baseline
- ACTIVE
- SILENT
- DISABLED

### Publish result baseline
- PUBLISHED
- SKIPPED_SILENT
- SKIPPED_LIMIT
- SKIPPED_DISABLED
- FAILED
- DUPLICATE_SUPPRESSED

### Operational outcome baseline
- WIN
- LOSE
- MISSED

### Market telemetry result baseline
- WIN
- LOSS
- DRAW

These outcome vocabularies are not interchangeable.

---

## 7. Stable identity rules

The same trade idea preserves one stable `signal_id` across:
- PRE;
- CONFIRM;
- OPEN_NOW;
- FSM handoff evidence where identity exists;
- signal-execution events;
- distribution events;
- visibility events;
- telemetry/outcome linkage.

Every material signal-execution attempt receives `execution_attempt_id`.

Pre- and post-distribution events for the same attempt may share `execution_attempt_id`, while each event retains unique `event_id`.

---

## 8. Decision event contract

### `decision_evaluated`
Represents pre-FSM strategy truth after Market, SR/Corridor, Time, Scoring and Trade Physics evaluation and DecisionObject production.

Required contextual domains:
- symbol;
- direction;
- timeframe/candle context;
- decision result;
- classical score where available;
- structured gates/evidence;
- strategy/DecisionObject version;
- stable correlation.

### Trade Physics decision payload
When Trade Physics is available, decision evidence must support:
- deterministic `TPS` `[0,100]`;
- `TPS_S`, `TPS_T`, `TPS_P`, `TPS_V` or equivalent structured component fields;
- `available_space`;
- `required_space`;
- `space_to_buffer_ratio`;
- `trade_space_margin_atr`;
- `directional_effective_speed`;
- `flow_efficiency`;
- `time_to_buffer_ratio`;
- `movement_stress`;
- Trade Physics formula/version;
- feature schema/version.

### Learned probability payload
When a validated learned model actually produced a prediction, evidence may include:
- `trade_success_probability` `[0,1]`;
- model id/version;
- calibration version;
- readiness state;
- feature schema version.

If no validated model exists, prediction fields remain absent/null. The system must never reuse TPS as learned probability.

`decision_evaluated` must not be overloaded as downstream execution truth.

---

## 9. Decision promotion/rejection/no-signal

### `decision_promoted`
Supports:
- signal id when assigned;
- from/to or resulting stage;
- score/TPS summary where relevant;
- promotion reason;
- correlation.

### `decision_rejected`
Supports:
- rejection family/reason/taxonomy version;
- relevant structural/time/classical-score/Trade-Physics evidence;
- explicit blocker rather than inferred absence.

### `decision_no_signal`
Used when evaluation completes without actionable stage and without a stronger explicit rejection class.

---

## 10. FSM event contract

`fsm_transition` supports:
- from/to state;
- requested stage;
- accepted stage;
- reason/reason family;
- `stage_handoff_ready`;
- `trade_execution_ready`;
- signal id where applicable;
- watchlist/focus/cooldown context;
- persisted-state result where relevant.

FSM events may reference DecisionObject/Trade Physics snapshot identity, but FSM must not recompute strategic mathematics.

Transition existence alone does not prove stage acceptance, SignalEvent construction, or publication.

---

## 11. `signal_execution_result`

Purpose: represent Signal Engine truth after FSM handoff, distinct from strategy/FSM/route truth.

Required contextual fields:
- `execution_attempt_id`;
- symbol;
- common timestamps/run identity.

Required for actionable lifecycle attempt:
- `signal_id`;
- stage;
- timeframe/context where available.

Required payload:
- `execution_phase`;
- `execution_outcome`;
- `execution_reason`;
- `stage_handoff_ready`;
- `trade_execution_ready`;
- `signal_event_available`;
- `destination_state`.

Recommended/conditional:
- setup correlation;
- FSM handoff reference;
- DecisionObject reference;
- Trade Physics snapshot/reference;
- candidate/payload schema/version;
- distribution/publication references for POST_DISTRIBUTION outcomes.

### PRE_DISTRIBUTION
If valid SignalEvent exists while distribution is intentionally not invoked:
- phase = PRE_DISTRIBUTION;
- outcome = DEFERRED;
- signal_event_available = true;
- destination_state = PRE_DISTRIBUTION_UNRESOLVED.

EMITTED is forbidden at this phase.

### POST_DISTRIBUTION
EMITTED requires evidence of at least one authorized successful publication.

---

## 12. External visibility events

`signal_stage_visible` represents governed external visibility after successful publication.

Required:
- signal id;
- stage;
- route/destination reference;
- publication evidence reference;
- message id where available;
- visibility result.

SignalEvent candidate creation does not create visibility truth.

---

## 13. Distribution event contract

### `route_publish_attempt`
- route;
- signal id;
- stage;
- destination id where resolved;
- route state/counters/mapping/dedup context.

### `route_publish_result`
- result;
- route state before/after;
- counters before/after;
- counted boolean;
- transport result;
- dedup evidence.

Route events are exact route/destination publication truth.

---

## 14. Telemetry lineage schema requirements

Telemetry evidence must support stable linkage to:
- signal/execution/decision identity;
- immutable pre-trade Trade Physics snapshot/version;
- objective market result;
- feature cutoff timestamp;
- label observation timestamp;
- label derivation version;
- optional model prediction snapshot/version.

Post-trade labels must never be represented as pre-trade features.

---

## 15. Outcome/reconciliation schema requirements

Operational outcome events must preserve:
- signal id;
- actor/authorization context;
- requested/final outcome;
- previous outcome where applicable;
- reconciliation status;
- timestamp/correlation;
- telemetry reference where available;
- discrepancy classification where applicable.

Operational WIN/LOSE/MISSED must not overwrite market WIN/LOSS/DRAW.

---

## 16. Model/readiness event evidence

When Trade Physics Intelligence emits governed model lifecycle evidence, Event Schema must be able to represent at least:
- model id/version;
- feature schema version;
- training/evaluation window reference;
- readiness state;
- calibration version;
- drift/validation status;
- recommendation/approval linkage.

Exact model-registry event names may be defined by Intelligence/Observability owner docs, but fields must not be hidden in unstructured text.

---

## 17. Admin/control event requirements

`admin_change` or domain-specific governed events must preserve:
- actor;
- action;
- target;
- before/after where applicable;
- validation result;
- authorization result;
- persistence/reload result where applicable;
- correlation/proof reference.

No admin action may silently change model/TPS/strategy parameters.

---

## 18. Privacy and minimization

Forbidden:
- API keys;
- tokens;
- credentials;
- unnecessary names/usernames/phone numbers;
- public exposure of private member identifiers.

Numeric platform IDs may appear only where operationally required and governed.

---

## 19. Schema evolution

Every semantic schema change requires:
- explicit version bump;
- migration note;
- linked-document repair;
- compatibility policy;
- preserved historical meaning.

Breaking changes require major-version discipline.

No field may silently change formula/meaning across schema versions.

---

## 20. Validation and failure behavior

An event is degraded/invalid when:
- required fields are absent;
- enumeration invalid;
- stable identity inconsistent;
- impossible value range occurs;
- Trade Physics formula/version missing where required;
- learned probability is present without model/version/readiness metadata;
- schema version and payload semantics conflict.

Invalid events must not be silently accepted as canonical evidence.

---

## 21. Forbidden schema patterns

Forbidden:
- one generic `decision` blob for all truth layers;
- using `TPS` to mean learned probability;
- using `signal_emitted` as both candidate and publication truth;
- embedding all execution truth only under debug;
- conflating route result with Signal Engine result;
- conflating market outcome with operational outcome;
- unversioned Trade Physics formula changes;
- post-outcome data appearing as pre-trade feature without explicit downstream labeling.

---

## 22. Runtime schema alignment

After promotion, `send/schema/event_schema.json` must be re-audited against this canonical spec.

Runtime schema is implementation, not authority.

Any runtime event type/field drift must be corrected only after canonical promotion and test-plan approval.

---

## 23. Final principle

Event Schema v3 must make the complete system reconstructable without collapsing truth layers.

For Trade Physics specifically, deterministic TPS, its component/formula version, learned probability, model readiness, telemetry labels and operational outcomes must remain separately identifiable and correlation-safe across the entire lifecycle.
