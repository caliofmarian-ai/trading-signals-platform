# OBSERVABILITY_LOGGING_SPEC_v3.0.0

Version: 3.0.0  
Status: ACTIVE CANONICAL  
Owner: BinaryBot / DROPi Signals  
Scope: implementation-level structured logging for strategy, Trade Physics, FSM, signal execution, distribution, telemetry, outcome and governance evidence  
Supersedes: `OBSERVABILITY_LOGGING_SPEC_v2.0.0.md`  

Linked proposed/current authorities:
- `EVENT_SCHEMA_SPEC_v3.0.0.md`
- `OBSERVABILITY_SPEC_v3.0.0.md`
- `ALGO_SPEC_v3.0.0.md`
- `TRADE_PHYSICS_MODEL_SPEC_v1.0.0.md`
- `TRADE_PHYSICS_INTELLIGENCE_SPEC_v1.0.0.md`
- `DECISION_OBJECT_CANONICAL_SPEC_v2.0.0.md`
- `FSM_DECISION_ENGINE_SPEC_v2.0.0.md`
- `SIGNAL_ENGINE_EXECUTION_SPEC_v3.0.0.md`
- `TRADE_TEMPORAL_TELEMETRY_SPEC_v3.0.0.md`
- `OUTCOME_TRACKING_SPEC_v3.0.0.md`

---

## 0. Authority and promotion status

This is the active canonical implementation-level logging contract.

Promotion status: ACTIVE CANONICAL under `CANONICAL_ACTIVATION_RECORD_20260901.md` and `CANONICAL_MASTER_INDEX_v2.0.0.md`.

It consolidates:
- explicit `signal_execution_result` logging;
- complete Trade Physics decision snapshots;
- model/version/readiness logging;
- telemetry label provenance;
- outcome truth separation.

---

## 1. Purpose

Every material decision, state change, execution result, distribution action, telemetry outcome, reconciliation mutation, model-readiness change, parameter/admin mutation and failure must produce structured evidence sufficient for replay/audit.

Logging is not optional decoration.

---

## 2. Structured format

Canonical logs should be machine-readable and append-oriented where practical, typically JSONL.

Each record must comply with `EVENT_SCHEMA_SPEC_v3.0.0` and include the common envelope plus domain payload.

Human-readable text may accompany structured evidence but may not replace it.

---

## 3. Common envelope implementation

Every structured log record must include at least:
- event id;
- event type;
- schema version;
- UTC timestamp;
- epoch timestamp;
- service/environment;
- run/cycle identity;
- source module/function;
- correlation fields applicable to the domain.

Recommended:
- trace id;
- strategy/version;
- git SHA;
- parameter hash;
- severity.

---

## 4. Decision logging

For each material strategy evaluation, log `decision_evaluated` with:
- symbol/direction/timeframe/candle context;
- strategy version;
- DecisionObject version/reference;
- requested/resulting strategic stage;
- classical `score_total` and component summary;
- hard/soft blockers;
- corridor/structural summary;
- time-model summary;
- Trade Physics snapshot/version;
- learned probability/model metadata when valid;
- rejection/promotion reason;
- stable correlation.

Negative outcomes must be logged, not inferred from absence of signal.

---

## 5. Required Trade Physics decision fields

Where Trade Physics evaluation is available, structured evidence must include or reference:
- `available_space`;
- `required_space`;
- `space_to_buffer_ratio`;
- `trade_space_margin_atr`;
- gross price speed where used;
- `directional_effective_speed`;
- `flow_efficiency`;
- `model_time_reach_ratio`;
- `time_to_buffer_ratio`;
- `directional_speed_ratio`;
- `movement_stress`;
- component values S/T/P/V;
- deterministic `TPS`;
- Trade Physics formula/version;
- weight/parameter version;
- feature schema version.

If any required input is unavailable, the log must show missingness/reason rather than invented zero/default values.

---

## 6. Learned probability logging

When a validated model produces `trade_success_probability`, log:
- probability;
- model id/version;
- calibration version;
- feature schema version;
- readiness state;
- prediction timestamp;
- OOD/degradation flags where available.

If no validated model exists, no fake probability is logged.

TPS must never be used as a substitute field for learned probability.

---

## 7. FSM logging

Each material FSM transition/handoff logs:
- signal/setup correlation;
- prior state;
- requested stage;
- accepted stage;
- resulting state;
- reason/reason family;
- state changed boolean;
- `stage_handoff_ready`;
- `trade_execution_ready`;
- focus/watchlist/cooldown/dedup context;
- persistence result where applicable.

No-op or blocker transitions must remain distinguishable from stage acceptance.

---

## 8. Signal execution logging

Primary event family:
- `signal_execution_result`.

Required fields:
- event/common envelope;
- `execution_attempt_id`;
- signal/setup correlation;
- symbol/timeframe/stage where applicable;
- execution phase;
- execution outcome;
- execution reason;
- `stage_handoff_ready`;
- `trade_execution_ready`;
- `signal_event_available`;
- destination state;
- candidate/payload reference where available;
- FSM handoff reference;
- DecisionObject/Trade Physics snapshot reference.

For POST_DISTRIBUTION EMITTED, include linked publication evidence.

---

## 9. Pre-distribution deferred logging

If valid SignalEvent candidate exists but distribution is intentionally disabled/not invoked:
- event type = `signal_execution_result`;
- phase = PRE_DISTRIBUTION;
- outcome = DEFERRED;
- destination state = PRE_DISTRIBUTION_UNRESOLVED;
- candidate available = true;
- reason explicitly describes deferred distribution.

Do not log EMITTED or external visibility.

---

## 10. Distribution logging

Each material route action logs:
- route publish attempt/result;
- signal id/stage;
- route/destination;
- route state;
- policy/entitlement result;
- counter before/after where governed;
- dedup state;
- transport result;
- failure/skip reason;
- message id where available after success.

Exact route truth belongs here, not in Signal Engine logs.

---

## 11. External visibility logging

When a stage becomes externally visible, log `signal_stage_visible` with:
- signal id;
- stage;
- successful route/destination evidence;
- message id where available;
- timestamp;
- correlation to execution attempt and route result.

Candidate construction alone never produces visibility evidence.

---

## 12. Telemetry logging

Telemetry logs/records must preserve:
- signal/execution/decision linkage;
- pre-trade Trade Physics snapshot/version;
- feature cutoff timestamp;
- raw checkpoint prices/timestamps;
- official market result;
- derived recovery/path classifications;
- label source/version;
- optional prediction/model snapshot.

Post-trade labels must not be written into fields representing pre-trade features.

---

## 13. Outcome reconciliation logging

Every mutation logs:
- signal id;
- actor/role;
- authorization result;
- requested outcome;
- previous outcome;
- final outcome;
- reconciliation status;
- reason/correction/dispute metadata;
- telemetry reference/discrepancy where applicable;
- persistence result.

No silent overwrite is allowed.

---

## 14. Model lifecycle logging

Current-scope Trade Physics Intelligence must produce structured evidence for:
- dataset materialization/version;
- feature schema/version;
- training run identity;
- train/validation/test windows;
- evaluation metrics;
- calibration result;
- model registry entry/version;
- readiness transition;
- drift/OOD event;
- recommendation;
- approval/rejection;
- rollback/demotion.

These records must support reproduction and governance audit.

---

## 15. Parameter/control logging

Every strategy/model parameter mutation attempt must log:
- actor/role;
- parameter group/key;
- old value;
- proposed value;
- final accepted value;
- validation result;
- approval state;
- persistence result;
- reload/activation result;
- rollback result where applicable.

Structural formula changes such as TPS weight/formula redesign are not ordinary runtime parameter mutations unless separately authorized.

---

## 16. Error/failure logging

Material failures must be structured and classified by domain.

Examples:
- market data unavailable;
- strategy input invalid;
- Trade Physics input missing;
- DecisionObject schema invalid;
- FSM persistence failure;
- candidate serialization failure;
- distribution transport failure;
- telemetry checkpoint failure;
- outcome persistence failure;
- model artifact/registry failure;
- schema validation failure.

Technical failure must not be mislabeled as strategy rejection.

---

## 17. Logging failure behavior

Logging itself should not silently crash the trading engine unless the governing invariant explicitly requires fail-closed behavior for that evidence class.

When evidence write fails:
- failure must be surfaced through fallback/health evidence where possible;
- affected truth must be marked degraded;
- downstream analytics/model training must not treat missing evidence as normal data.

---

## 18. Truth-layer separation in storage

Logs may share a physical store but must preserve domain labels.

Never conflate:
- strategy decision;
- Trade Physics score;
- learned probability;
- FSM state;
- execution outcome;
- route result;
- market outcome;
- operational outcome;
- model readiness.

---

## 19. Stable identity and dedup

Logging must preserve:
- unique event identity;
- stable signal identity;
- stable execution attempt identity;
- idempotence for repeated persistence attempts where applicable.

Duplicate suppression itself must be observable.

---

## 20. Storage/rotation

Implementation may use separate domain JSONL files or an equivalent structured backend.

Requirements:
- append/replay friendliness;
- durable persistence;
- restart-safe behavior;
- retention sufficient for audits/research/model reproducibility;
- rotation/compression without silent loss of required provenance.

File paths are implementation details unless separately locked by canonical operations/storage docs.

---

## 21. Privacy/security

Never log:
- API keys;
- tokens;
- passwords;
- secret config values;
- unnecessary personal data.

Role-aware private operational identifiers may be logged only when required by governance/privacy canon.

---

## 22. Schema validation

Every structured record must validate against the promoted Event Schema/runtime implementation mapping.

A logging writer must not silently coerce invalid semantic values into a valid-looking event.

Range checks include:
- TPS `[0,100]`;
- learned probability `[0,1]`;
- valid stage/outcome enums;
- consistent signal identity/correlation;
- Trade Physics version metadata where required.

---

## 23. Historical compatibility

Historical logs retain original schema meaning.

Migration adapters may map old names into new analytical views, but raw historical records must not be rewritten as if they had originally emitted v3 semantics.

---

## 24. Forbidden logging patterns

Forbidden:
- only human-readable prose for material events;
- opaque debug blob as sole execution/Trade Physics evidence;
- TPS without deterministic identity/version where reproducibility is required;
- learned probability without model/readiness metadata;
- candidate construction logged as successful external emission;
- market and operational outcomes stored under one unlabeled `result` field;
- post-trade labels leaking into pre-trade feature snapshots;
- silent parameter/model changes.

---

## 25. Implementation alignment checklist

After promotion, implementation must demonstrate:
- `decision_evaluated` includes Trade Physics evidence/version;
- FSM handoff is explicit;
- `signal_execution_result` is persisted;
- route results remain route-owned;
- external visibility has distinct evidence;
- telemetry stores feature/label provenance;
- outcome reconciliation remains distinct;
- model lifecycle/readiness is auditable;
- schema validation detects drift.

---

## 26. Final principle

If a material system truth is not recorded in structured, correlated, versioned evidence, the system cannot safely use that truth for forensic audit, performance analytics, research, or AI learning.
