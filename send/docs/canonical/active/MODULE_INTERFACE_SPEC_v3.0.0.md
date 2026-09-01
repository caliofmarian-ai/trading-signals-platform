# MODULE_INTERFACE_SPEC_v3.0.0

Version: 3.0.0  
Status: ACTIVE CANONICAL  
Owner: BinaryBot / DROPi Signals  
Scope: canonical module ownership, shared contracts and interfaces across strategy, Trade Physics, FSM, Signal Engine, Distribution, Telemetry, Outcome, Analytics and Intelligence  
Supersedes: `MODULE_INTERFACE_SPEC_v2.0.0.md`  

Linked proposed/current authorities:
- Root Strategy Stack successor
- `ALGO_SPEC_v3.0.0.md`
- `TRADE_PHYSICS_MODEL_SPEC_v1.0.0.md`
- `TRADE_PHYSICS_INTELLIGENCE_SPEC_v1.0.0.md`
- `SR_CORRIDOR_ENGINE_SPEC_v3.0.0.md`
- `TIME_MODEL_UNIFIED_CANON_v3.0.0.md`
- `DECISION_OBJECT_CANONICAL_SPEC_v2.0.0.md`
- `FSM_DECISION_ENGINE_SPEC_v2.0.0.md`
- `SIGNAL_ENGINE_EXECUTION_SPEC_v3.0.0.md`
- `EVENT_SCHEMA_SPEC_v3.0.0.md`
- `OBSERVABILITY_SPEC_v3.0.0.md`
- `TRADE_TEMPORAL_TELEMETRY_SPEC_v3.0.0.md`
- `OUTCOME_TRACKING_SPEC_v3.0.0.md`
- Distribution / Admin / Analytics / Research / Intelligence canonical docs

---

## 0. Authority and promotion status

This is the complete proposed successor for module ownership/interface truth.

Promotion status: ACTIVE CANONICAL under `CANONICAL_ACTIVATION_RECORD_20260901.md` and `CANONICAL_MASTER_INDEX_v2.0.0.md`.

The major version consolidates:
- explicit FSM execution handoff semantics;
- PRE/CONFIRM/OPEN_NOW SignalEvent candidate interfaces;
- current-scope Trade Physics ownership/contract boundaries;
- learned probability/model lineage interfaces;
- clearer truth separation among Signal Engine, Distribution, Telemetry and Outcome.

---

## 1. Purpose

This document defines:
- which module owns which truth;
- what each major module consumes/produces;
- shared data contracts;
- forbidden cross-layer shortcuts;
- canonical boundaries required for testability, auditability and safe evolution.

No module may silently absorb another module’s canonical responsibility merely because runtime code currently mixes concerns.

---

## 2. Canonical strategic pipeline

`Market Data -> Market Model -> SR/Corridor -> Time Model -> Scoring + Trade Physics -> DecisionObject -> FSM -> Signal Engine -> SignalEvent -> Distribution Router -> Publisher/External Surface`

Downstream evidence chain:

`External Executable Truth -> Trade Temporal Telemetry -> Outcome Reconciliation -> Performance Analytics -> Research -> Strategy Intelligence -> Controlled Evolution`

---

## 3. Core module ownership map

### 3.1 Market Model
Owns:
- raw-to-derived market context;
- EMA/RSI/ATR/activity/noise evidence;
- buffer distance derivation under strategy parameter contract;
- gross/non-directional price movement context;
- direction-aware movement evidence required upstream by Time/Trade Physics, where implementation assigns it here.

Does not own:
- corridor structure;
- final time feasibility;
- TPS;
- FSM;
- signal emission.

### 3.2 SR / Corridor Engine
Owns:
- support/resistance landmarks;
- active corridor/structural interpretation;
- directional barrier selection;
- `available_space`;
- structural feasibility/conflict/compression;
- corridor evidence for downstream Time/Scoring.

Does not own TPS aggregation or execution.

### 3.3 Time Model
Owns:
- `directional_effective_speed` if canonical implementation places final derivation here from Market evidence;
- `flow_efficiency` derivation boundary as governed;
- `t_needed`;
- `t_needed_adjusted`;
- `model_expiry`;
- `model_time_reach_ratio`;
- `time_to_buffer_ratio` compatibility/convenience relation where consumed by Trade Physics;
- `corridor_time_pressure`;
- `time_state`;
- execution-time derivation contract downstream from model time.

Does not own scoring/TPS or FSM state transitions.

### 3.4 Scoring / Trade Physics
Owns:
- classical score aggregation;
- deterministic Trade Physics S/T/P/V computation;
- deterministic `TPS` `[0,100]`;
- score/TPS explanation bands;
- strategic gating that is explicitly assigned before DecisionObject.

Does not own:
- learned probability model training;
- FSM state;
- Signal Engine execution;
- route policy.

### 3.5 DecisionObject Producer
Owns:
- standardization of complete pre-FSM strategic truth;
- stable schema/version;
- market/structure/time/classical-score/Trade-Physics domains;
- reject/degradation semantics;
- optional learned-probability snapshot when valid;
- metadata/correlation.

### 3.6 FSM
Owns:
- operational state interpretation;
- lifecycle transition rules;
- requested vs accepted stage;
- focus/watchlist/cooldown lifecycle semantics;
- `stage_handoff_ready`;
- `trade_execution_ready`;
- explicit post-FSM handoff to Signal Engine.

FSM does not recalculate market/time/TPS.

### 3.7 Signal Engine
Owns:
- exact-stage handoff validation;
- SignalEvent candidate construction;
- engine-level duplicate protection;
- execution outcome classification;
- downstream Distribution handoff;
- signal-execution observability.

Signal Engine consumes but does not recompute TPS/Trade Physics.

### 3.8 Distribution Router
Owns:
- route selection;
- entitlement;
- route state/policy;
- destination mapping;
- route counters/dedup where governed;
- publisher invocation decision.

### 3.9 Publisher / Telegram Transport
Owns:
- channel/API transport execution;
- transport-specific message result;
- returned message identifiers/errors.

Does not decide signal validity.

### 3.10 Trade Temporal Telemetry
Owns:
- objective post-executable price checkpoints;
- market outcome labels;
- immutable pre-trade snapshot lineage;
- Trade Physics feature/outcome provenance;
- temporal/recovery derived evidence.

### 3.11 Outcome Reconciliation
Owns:
- admin/operational WIN/LOSE/MISSED truth;
- reconciliation/dispute/override lifecycle;
- operational discrepancy vs telemetry.

Does not own objective market label.

### 3.12 Performance Analytics
Owns:
- labeled metrics and segmented performance interpretation;
- Trade Physics calibration analysis;
- model performance/calibration reporting;
- truth-layer-separated dashboards/aggregates.

### 3.13 Research & Learning
Owns:
- hypotheses;
- experiments;
- evidence confidence;
- controlled dataset research;
- strategy/model investigation proposals.

### 3.14 Trade Physics Intelligence / Strategy Intelligence
Owns:
- dataset materialization;
- training/evaluation/calibration pipelines;
- model registry;
- `trade_success_probability` prediction when a valid model is ready;
- readiness/drift monitoring;
- governed recommendations.

Does not silently mutate production strategy.

### 3.15 Autonomous Strategy Evolution
Owns:
- proposal lifecycle from evidence to governed experiment/rollout recommendation;
- not direct unapproved production mutation.

---

## 4. Shared contract: MarketModelResult

Minimum semantic domains:
- symbol/evaluation timestamp;
- direction bias/context;
- latest price;
- ATR/volatility/activity/noise evidence;
- buffer distance;
- gross price speed;
- direction-aware movement inputs needed by Time/Trade Physics;
- indicator evidence;
- schema/version.

No downstream module should scrape raw candles again merely to recreate already-owned Market truth unless explicit replay/testing contract requires it.

---

## 5. Shared contract: CorridorResult

Minimum semantic domains:
- signal/setup identity context;
- structural landmarks;
- active corridor/boundary summary;
- directional nearest relevant barrier;
- `available_space`;
- structural room/feasibility;
- conflict/compression flags;
- explanation;
- schema/version.

---

## 6. Shared contract: TimeModelResult

Minimum semantic domains:
- `directional_effective_speed`;
- gross speed reference where applicable;
- `flow_efficiency`;
- `t_needed`;
- `t_needed_adjusted`;
- `model_expiry`;
- `model_time_reach_ratio`;
- `time_to_buffer_ratio` when valid;
- `corridor_time_pressure`;
- `time_state`;
- temporal feasibility;
- schema/version.

Time Model must not expose ambiguous primary `expiry_minutes` in place of model-time semantics.

---

## 7. Shared contract: TradePhysicsResult

Canonical deterministic Trade Physics result must include:
- S/T/P/V components;
- `TPS` `[0,100]`;
- input evidence or stable references for space/time/speed/stress;
- `space_to_buffer_ratio`;
- `trade_space_margin_atr`;
- `directional_speed_ratio`;
- `movement_stress`;
- formula/version;
- weights/parameter version;
- explanation band;
- availability/degradation reason if incomplete.

This result is produced before DecisionObject.

---

## 8. Shared contract: ScoringResult

ScoringResult must preserve:
- classical score total;
- classical component breakdown;
- eligibility/hard blockers;
- score tier/explanation;
- TradePhysicsResult or explicit attached/reference domain;
- schema/version.

Classical score and TPS remain separate metrics unless a future canonical combined-score formula explicitly supersedes this rule.

---

## 9. Shared contract: LearnedTradePhysicsPrediction

Optional current-scope contract, valid only under an approved model readiness state.

Minimum fields:
- `trade_success_probability` `[0,1]`;
- model id/version;
- calibration version;
- feature schema version;
- readiness state;
- prediction timestamp;
- degradation/OOD flags where available.

If no validated model is ready, producer returns no prediction rather than a fabricated placeholder.

---

## 10. Shared contract: DecisionObject

DecisionObject is the canonical strategy-to-FSM object.

Required semantic domains:
- setup identity;
- market context;
- structure;
- time;
- classical score;
- deterministic Trade Physics;
- optional learned probability prediction;
- strategic flags;
- reject/degradation semantics;
- requested stage/readiness for FSM;
- observability metadata;
- schema/version.

DecisionObject is immutable strategy truth for that evaluation.

---

## 11. Shared contract: FSMExecutionHandoff

Minimum semantics:
- `requested_stage: PRE|CONFIRM|OPEN_NOW|None`;
- `accepted_stage: PRE|CONFIRM|OPEN_NOW|None`;
- `signal_id: string|None`;
- prior/resulting state;
- `state_changed: bool`;
- `reason: string`;
- `reason_family: string|None`;
- transition event/reference;
- `stage_handoff_ready: bool`;
- `trade_execution_ready: bool`;
- blocker/duplicate/focus/cooldown context where applicable.

Rules:
- transition-event existence alone is not acceptance;
- PRE/CONFIRM can be handoff-ready while trade-execution-ready is false;
- OPEN_NOW may be trade-execution-ready after full lifecycle validity.

---

## 12. Shared contract: SignalEvent

SignalEvent is the canonical engine-to-distribution candidate object.

Minimum semantic fields:
- event/schema version;
- stable `signal_id`;
- symbol;
- timeframe;
- direction;
- stage PRE/CONFIRM/OPEN_NOW;
- candle/setup correlation;
- score summary;
- Trade Physics snapshot/reference;
- canonical buffer semantics (`buffer_distance`, not legacy `buffer_price` as primary truth);
- timing/execution expiry semantics where applicable;
- created timestamp;
- payload/metadata.

SignalEvent creation does not authorize distribution or prove publication.

---

## 13. Shared contract: SignalExecutionResult

Minimum fields:
- `execution_attempt_id`;
- signal/setup correlation;
- stage;
- execution phase;
- execution outcome;
- reason;
- `stage_handoff_ready`;
- `trade_execution_ready`;
- SignalEvent availability;
- destination state;
- candidate reference;
- FSM/DecisionObject references;
- publication evidence reference where EMITTED.

---

## 14. Shared contract: RoutePublishResult

Distribution-owned fields include:
- route/destination;
- signal id/stage;
- route state;
- policy/entitlement result;
- publish result;
- transport result;
- counters/dedup;
- message id/error where applicable.

Signal Engine must not manufacture these fields before route evaluation.

---

## 15. Shared contract: TelemetryTradeRecord

Minimum domains:
- signal/execution/decision identity;
- immutable pre-trade DecisionObject/Trade Physics snapshot;
- feature/version provenance;
- entry/open/expiry/checkpoint timing;
- raw checkpoint prices;
- market WIN/LOSS/DRAW;
- recovery/path derived evidence;
- label source/version;
- optional learned prediction snapshot/version.

---

## 16. Shared contract: OutcomeRecord

Minimum domains:
- signal identity;
- operational outcome WIN/LOSE/MISSED;
- actor/authorization;
- set/reconciliation timestamps;
- reconciliation status;
- previous outcome/correction history;
- telemetry linkage/discrepancy;
- correlation/version.

---

## 17. Shared contract: ModelArtifact / ModelReadiness

Trade Physics Intelligence must support canonical model registry metadata:
- model id/version;
- feature schema version;
- training/evaluation data windows;
- training code/config/version references;
- calibration version;
- evaluation metrics;
- readiness state;
- approval state;
- drift/degradation status;
- artifact/provenance reference.

---

## 18. Shared contract: Research/Experiment records

Research/learning interfaces must preserve:
- hypothesis id;
- evidence basis;
- target metric/truth layer;
- sample/data version;
- proposed change;
- success/failure/rollback criteria;
- approval/lifecycle status;
- final conclusion.

---

## 19. Signal Engine module boundary

`signal_engine.py` owns:
- scan orchestration/cadence where repository architecture assigns it;
- strategy invocation;
- FSM invocation/orchestration boundary;
- exact handoff validation;
- SignalEvent construction;
- engine dedup;
- execution-result evidence.

It does not own:
- Trade Physics formula;
- route/tier policy;
- Telegram formatting;
- market telemetry labels;
- outcome reconciliation;
- model training.

Any current TPS calculation in Signal Engine is implementation drift against the proposed target contract.

---

## 20. Distribution module boundary

`distribution_router.route(event, now_ts)` or equivalent consumes a validated SignalEvent.

Distribution does not decide whether TPS/score made the setup strategically valid; that truth is upstream.

Distribution only decides governed route behavior for an already-valid lifecycle stage.

---

## 21. Telemetry and model-data boundary

Telemetry consumes immutable upstream feature snapshots and later market evidence.

Dataset builders consume telemetry/decision/outcome evidence but must enforce temporal anti-leakage.

Model training never reads future label data as if it were a pre-trade feature.

---

## 22. Parameter boundary

Runtime parameter control may manage only explicitly tunable values.

Structural formulas/ownership such as:
- TPS formula shape;
- deterministic/learned identity split;
- feature formulas;
- model readiness gates

are not ordinary live parameters without separate canonical authorization.

---

## 23. Error/degradation interfaces

Modules must fail explicitly when required real evidence is unavailable.

They must not:
- invent zero TPS;
- invent probability 0.5;
- invent structural room;
- silently substitute gross speed for directional speed;
- silently invert time-ratio orientation;
- fall back to legacy buffer vocabulary as primary truth.

Unavailable evidence must carry reason/degradation state.

---

## 24. Versioning/provenance

All cross-module contracts must expose sufficient version metadata to reconstruct:
- strategy version;
- contract/schema version;
- Trade Physics formula/feature version;
- model version/readiness when applicable;
- parameter/config version/hash.

No formula or field meaning may change silently under the same version identity.

---

## 25. Forbidden cross-layer patterns

Forbidden:
- Time Model deriving corridor from scratch;
- Scoring bypassing structural/time truth;
- Signal Engine recomputing TPS;
- FSM recomputing strategy math;
- Distribution recomputing signal validity;
- Telemetry rewriting DecisionObject;
- Outcome rewriting market telemetry;
- Intelligence writing production parameters without governance;
- generic dicts replacing explicit shared contracts;
- duplicate canonical ownership for the same truth.

---

## 26. Code alignment requirements

After promotion, code audit must map each module/function to these owners/contracts and identify:
- missing contract fields;
- legacy vocabulary;
- duplicated formulas;
- hidden shortcuts;
- schema mismatch;
- current TPS in wrong module;
- missing Trade Physics version lineage;
- missing explicit FSM handoff.

No implementation change occurs before that post-promotion audit.

---

## 27. Final principle

A module may consume another layer’s truth, but it may not silently become the owner of that truth.

Trade Physics integration is canonical only when structural space, directional time, deterministic TPS, DecisionObject transport, execution consumption, telemetry labels and learned-model readiness all have single, explicit owners connected by versioned interfaces.
