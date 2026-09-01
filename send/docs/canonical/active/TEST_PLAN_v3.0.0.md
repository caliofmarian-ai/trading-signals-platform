# TEST_PLAN_v3.0.0

Version: 3.0.0  
Status: ACTIVE CANONICAL  
Owner: BinaryBot / DROPi Signals  
Scope: canonical validation protocol for strategy, Trade Physics, staged execution, evidence, telemetry, learned models and production readiness  
Supersedes: `TEST_PLAN_v2.0.0.md`  

Linked authorities:
- `SYSTEM_INVARIANTS_v3.0.0.md`
- `SYSTEM_ARCHITECTURE_MAP_v3.0.0.md`
- `CANONICAL_STRATEGY_STACK_v2.0.0.md`
- `ALGO_SPEC_v3.0.0.md`
- `TRADE_PHYSICS_MODEL_SPEC_v1.0.0.md`
- `TRADE_PHYSICS_INTELLIGENCE_SPEC_v1.0.0.md`
- `TIME_MODEL_UNIFIED_CANON_v3.0.0.md`
- `SR_CORRIDOR_ENGINE_SPEC_v3.0.0.md`
- `DECISION_OBJECT_CANONICAL_SPEC_v2.0.0.md`
- `FSM_DECISION_ENGINE_SPEC_v2.0.0.md`
- `SIGNAL_ENGINE_EXECUTION_SPEC_v3.0.0.md`
- `MODULE_INTERFACE_SPEC_v3.0.0.md`
- `EVENT_SCHEMA_SPEC_v3.0.0.md`
- `OBSERVABILITY_SPEC_v3.0.0.md`
- `TRADE_TEMPORAL_TELEMETRY_SPEC_v3.0.0.md`
- `OUTCOME_TRACKING_SPEC_v3.0.0.md`
- Analytics/Research/Intelligence successors
- `GOVERNANCE_AND_CHANGE_CONTROL_v2.0.0.md`
- `DEPLOYMENT_PROTOCOL_v2.0.0.md`
- `FAILURE_RECOVERY_SPEC_v2.0.0.md`

---

## 0. Authority and promotion status

This is the active canonical validation successor.

Promotion status: ACTIVE CANONICAL under `CANONICAL_ACTIVATION_RECORD_20260901.md` and `CANONICAL_MASTER_INDEX_v2.0.0.md`.

The major version adds required validation for:
- deterministic Trade Physics calculations;
- direction-aware speed/time semantics;
- exact FSM stage handoff;
- SignalEvent candidate vs publication truth;
- Trade Physics data lineage and ML anti-leakage;
- model calibration/readiness and no-fabrication rules.

---

## 1. Purpose

No behavior is trusted because it merely runs.

A behavior becomes trustworthy only when it is:
- explicitly testable;
- reproducible where required;
- invariant-safe;
- schema/contract compliant;
- observable;
- restart/recovery safe;
- distribution safe;
- lineage safe;
- validated at change-appropriate depth.

This plan defines what evidence is required before production trust.

---

## 2. Validation authority rule

Governance decides whether a change is allowed.
Deployment Protocol decides how approved change reaches runtime.
This Test Plan decides what must be proven before the resulting behavior is trusted.

No structural runtime rollout is valid without passing all affected categories below.

---

## 3. Validation environments

Canonical environments:
- DEV
- STAGING
- PROD

Rules:
- deterministic/behavioral tests pass in DEV/STAGING before production trust;
- live-only smoke checks may supplement but never replace replay/regression tests;
- external publication tests use isolated/test destinations;
- production subscriber surfaces are not a destructive test environment.

---

## 4. Test data

Allowed controlled evidence includes:
- recorded real candle datasets;
- sanitized production-like datasets;
- deterministic synthetic edge fixtures;
- bounded live current data for smoke checks;
- labeled telemetry datasets for post-trade analytics/model tests.

Synthetic fixtures may test edge cases, but model-quality claims require representative real labeled evidence.

---

## 5. Validation evidence package

Every material validation package should include:
- test run id;
- environment;
- commit/version;
- canonical spec versions;
- parameter/config version/hash;
- fixture/dataset id/version;
- expected vs actual results;
- event/log evidence;
- pass/fail per category;
- failure summary;
- replay comparison where applicable.

Trade Physics/model tests additionally include:
- Trade Physics formula/feature version;
- model id/version when applicable;
- label definition/version;
- feature cutoff rule;
- calibration/readiness evidence.

---

## 6. Canonical test categories

Affected changes must cover:
1. structural/boot/config;
2. market input and indicator correctness;
3. SR/corridor structural geometry;
4. directional time model;
5. deterministic Trade Physics;
6. classical scoring + DecisionObject;
7. FSM exact-stage lifecycle;
8. Signal Engine execution semantics;
9. Distribution/external visibility;
10. Event Schema/Observability;
11. Telemetry and market labels;
12. Outcome reconciliation;
13. Trade Physics datasets/anti-leakage;
14. learned model training/evaluation/calibration/readiness;
15. analytics/research/intelligence;
16. persistence/restart/recovery;
17. stress/load/cadence;
18. replay/regression;
19. security/admin/control;
20. deployment/production-readiness.

---

## 7. Structural / boot / config validation

Prove:
- valid configuration loads;
- missing/invalid configuration fails explicitly;
- no hidden hardcoded adjustable threshold bypasses parameter control;
- strategy/version/formula/schema identities are coherent;
- required directories/stores are writable/recoverable;
- startup summary exposes enough version/config state for audit;
- no unavailable mandatory dependency is silently treated as healthy.

---

## 8. Market input / indicator validation

Prove with exact vectors:
- candle ordering contract;
- OHLC geometry validation;
- EMA/RSI/ATR correctness;
- activity/noise/spike metrics;
- buffer distance derivation;
- gross movement-speed calculation where used;
- no fabricated candles/indicators.

For numeric formulas use tolerance defined by implementation language precision; expected values must be computed independently from the production function where feasible.

---

## 9. SR / corridor / space validation

Required cases:
- BUY nearest relevant resistance chosen correctly;
- SELL nearest relevant support chosen correctly;
- no valid directional barrier -> explicit unavailable/degraded structural truth;
- enough structural room;
- exact boundary/marginal room;
- insufficient room;
- compressed/conflicted corridor;
- multi-level SR ordering;
- stale/wrong-side level rejection.

Trade Physics assertions:
- `available_space` is directional;
- `required_space = buffer_distance` under baseline contract;
- `space_to_buffer_ratio` exact;
- `trade_space_margin_atr` exact;
- structural blocker semantics match canon.

---

## 10. Directional effective speed validation

The promoted Time/Trade Physics implementation must have deterministic tests for:
- BUY movement counts only/primarily governed favorable directional deltas according to formula;
- SELL uses opposite favorable direction;
- recency weighting gives newer movement the governed weight;
- zero favorable motion;
- alternating/noisy movement;
- steady clean trend;
- gross speed vs directional speed separation;
- `flow_efficiency` bounds/zero-denominator behavior;
- newest-first input handled correctly.

A test must prove gross absolute speed cannot silently substitute for `directional_effective_speed`.

---

## 11. Time-model validation

Required exact assertions:
- `t_needed` uses canonical movement distance and directional effective speed;
- zero/nonpositive directional speed fails/degrades safely;
- `t_needed_adjusted` modifiers deterministic;
- `model_expiry` derivation follows active canon;
- `model_time_reach_ratio = t_needed_adjusted/model_expiry`;
- `time_to_buffer_ratio = model_expiry/t_needed_adjusted` when valid;
- reciprocal relation holds within numerical tolerance;
- ratio orientation is never swapped;
- `corridor_time_pressure`/`time_state` classifications match boundary cases;
- execution expiry remains downstream of model time.

---

## 12. Deterministic Trade Physics component validation

### 12.1 Space component
Verify:
`S = min(space_to_buffer_ratio, 3.0)/3.0`
for values below 0, 0, 1, 2, 3, above 3, with invalid-input handling explicitly tested.

### 12.2 Time component
Verify:
`T = min(time_to_buffer_ratio, 2.0)/2.0`
for boundary and cap cases.

### 12.3 Price-speed component
Baseline reference:
`atr_speed_reference = atr_m5/5`

Verify:
`directional_speed_ratio = directional_effective_speed/atr_speed_reference`
`P = min(directional_speed_ratio,2.0)/2.0`

Test explicitly that legacy/current runtime `buffer_distance/model_expiry` reference does **not** silently remain after remediation unless canon is changed again.

### 12.4 Volatility-efficiency component
Verify:
`movement_stress = required_space/atr_m5`
`V = 1/(1+movement_stress)`

### 12.5 Missing/invalid evidence
Invalid ATR, missing structural space, invalid timing or nonfinite values must not yield fabricated neutral components.

---

## 13. TPS formula validation

Canonical deterministic formula:

`TPS_raw = 0.35*S + 0.25*T + 0.20*P + 0.20*V`
`TPS = clamp(100*TPS_raw, 0, 100)`

Required:
- exact component-weight tests;
- all-zero/all-one vectors;
- cap behavior;
- numerical example from Intake normalized to canonical vocabulary;
- randomized property tests confirming bounds `[0,100]`;
- deterministic replay;
- formula/version attached to output;
- no second TPS formula in any runtime module.

Repository-wide test should fail if Signal Engine contains an independent TPS formula after migration, unless it is only a compatibility parser/reference with no calculation authority.

---

## 14. Classical score + TPS separation validation

Prove:
- classical score still computes independently;
- TPS computes independently;
- DecisionObject contains both with unambiguous names;
- no hidden combined score exists;
- TPS interpretation bands alone do not change PRE/CONFIRM/OPEN_NOW thresholds;
- hard blockers remain effective even with high arithmetic score/TPS.

---

## 15. Learned probability identity validation

When no validated model exists:
- no `trade_success_probability` is emitted/fabricated;
- TPS is not divided by 100 and mislabeled as probability;
- no default 0.5 or 0 is injected.

When a validated model exists:
- probability range `[0,1]`;
- model/version/calibration/readiness metadata present;
- exact feature schema used;
- invalid/outdated model readiness blocks influence according to canon.

---

## 16. DecisionObject validation

Prove pipeline order:
- Market -> SR -> Time -> Scoring/TPS -> DecisionObject -> FSM.

DecisionObject must include:
- stable setup identity;
- market context;
- structure;
- time;
- classical score;
- deterministic Trade Physics;
- optional valid learned probability;
- reject/degradation semantics;
- schema/version/correlation.

Mutation after creation must be prevented where contract is immutable.

---

## 17. FSM exact-stage validation

Required cases for PRE/CONFIRM/OPEN_NOW:
- accepted exact stage;
- duplicate same-stage/candle;
- cooldown;
- watchlist full;
- invalid lifecycle path;
- signal id discontinuity;
- stale focus;
- no-op transition.

Assertions:
- `requested_stage` correct;
- `accepted_stage` correct/null;
- `stage_handoff_ready` correct;
- `trade_execution_ready` false for PRE/CONFIRM;
- OPEN_NOW trade readiness only after valid path;
- transition-event existence never automatically means handoff.

---

## 18. Signal Engine execution validation

Required:
- SignalEvent constructed only after exact-stage handoff;
- PRE candidate supported when accepted;
- CONFIRM candidate supported when accepted;
- OPEN_NOW candidate supported when accepted;
- blockers/duplicates do not construct released candidate;
- Signal Engine consumes DecisionObject TPS snapshot without recomputation;
- candidate schema coherent;
- stable signal identity preserved.

Execution outcome cases:
- NOT_EMITTED;
- BLOCKED;
- SKIPPED;
- FAILED;
- DEFERRED;
- EMITTED only with downstream success evidence.

---

## 19. Pre-distribution deferred validation

With Distribution intentionally not invoked:
- valid SignalEvent candidate exists;
- `signal_execution_result.execution_phase = PRE_DISTRIBUTION`;
- outcome = DEFERRED;
- destination = PRE_DISTRIBUTION_UNRESOLVED;
- no route call;
- no Telegram message;
- no external visibility event;
- no outcome registration;
- no broker action.

This is mandatory before #73 or successor code can be considered aligned.

---

## 20. Distribution / external visibility validation

Using isolated test routes:
- candidate released to router;
- ACTIVE/SILENT/DISABLED behavior;
- entitlement/counter logic;
- duplicate route suppression;
- publication success/failure;
- exact route event evidence;
- external `signal_stage_visible` only after success;
- EMITTED only when publication evidence exists;
- no Signal Engine strategic re-evaluation.

Counter consumption must occur only under canonical successful-publication rules.

---

## 21. Event Schema / Observability validation

Schema tests cover:
- `decision_evaluated` Trade Physics fields/version;
- FSM handoff fields;
- `signal_execution_result` fields/outcomes/phases;
- route event fields;
- external visibility fields;
- telemetry label/provenance fields;
- outcome reconciliation fields;
- learned probability metadata.

Negative schema tests:
- TPS outside `[0,100]`;
- probability outside `[0,1]`;
- probability without model metadata;
- invalid enum;
- signal identity mismatch;
- execution EMITTED without publication reference;
- ambiguous market/operational result fields.

---

## 22. Telemetry validation

For effective executable OPEN_NOW:
- exactly one telemetry chain;
- correct immutable pre-trade snapshot;
- midpoint/expiry/+1/+3/+5 checkpoints;
- BUY/SELL market WIN/LOSS/DRAW correctness;
- recovery classification correctness;
- restart-safe pending checkpoint behavior;
- formula/feature/model version preservation.

A mere internal candidate must not create an executed-trade telemetry record.

---

## 23. Outcome reconciliation validation

Prove:
- authorized actor required;
- stable signal identity required;
- WIN/LOSE/MISSED stored operationally;
- duplicate mutation idempotent;
- override preserves previous outcome;
- telemetry disagreement becomes discrepancy, not overwrite;
- MISSED is not market LOSS;
- decision/market/operational truths remain independently retrievable.

---

## 24. Dataset anti-leakage validation

Dataset builder tests must prove:
- all pre-trade features have timestamp <= feature cutoff;
- label observation occurs after cutoff;
- expiry/post-expiry/admin outcomes never enter pre-trade features;
- random shuffled identifiers do not leak target;
- train/validation/test time windows are separated as governed;
- feature schema/version deterministic;
- rows with insufficient correlation/missing mandatory features are rejected/degraded explicitly;
- target truth layer is named.

A deliberate leakage fixture must be detected and fail validation.

---

## 25. Model training/evaluation validation

When model pipeline is implemented:
- reproducible dataset version;
- deterministic/random seed policy documented where applicable;
- model artifact hash/version;
- train/validation/test separation;
- baseline comparison;
- discrimination metrics appropriate to model;
- calibration metrics/curve;
- Brier/log-loss or approved equivalent;
- segment performance;
- overfit checks;
- model registry write/read;
- invalid artifact handling.

No model is promoted because training completes successfully alone.

---

## 26. Model readiness validation

Test state transitions such as:
- UNTRAINED;
- INSUFFICIENT_DATA;
- TRAINED_UNVALIDATED;
- VALIDATED_RECOMMEND_ONLY;
- approved bounded state where separately authorized;
- DEGRADED/DRIFTED/REVOKED where defined.

Prove:
- unauthorized transition rejected;
- readiness evidence/proofs exist;
- model influence is bounded by readiness;
- drift can demote/restrict model;
- absence of model remains safe.

---

## 27. Analytics / research validation

Validate:
- TPS band outcome analytics;
- S/T/P/V component analysis;
- classical score vs TPS analysis;
- probability calibration analytics;
- symbol/session/regime segmentation;
- truth-layer labels;
- hypothesis/experiment records;
- sample-size/confidence evidence;
- no causal claim from correlation-only metric without stated caveat.

---

## 28. Persistence / restart validation

Required restart cases:
- active focus/watchlist;
- cooldown;
- accepted PRE/CONFIRM lifecycle;
- pending SignalEvent/execution evidence where persisted;
- distribution counters/state;
- pending telemetry checkpoints;
- outcome reconciliation queue;
- model registry/readiness state.

No restart may produce duplicate visible OPEN_NOW or lose critical version/provenance state.

---

## 29. Failure recovery validation

Inject failures in:
- market data;
- structural data;
- time/TP calculation;
- DecisionObject serialization;
- FSM persistence;
- SignalEvent creation;
- observability write;
- distribution transport;
- telemetry storage;
- outcome storage;
- model artifact load/registry.

Prove:
- error classified in correct domain;
- no false strategic rejection/publication/outcome;
- safe degraded/freeze behavior;
- evidence retained;
- recovery does not bypass invariants.

---

## 30. Stress / cadence validation

For target scan cadence (including configured 2-second target where applicable), measure:
- decision cycle duration;
- Trade Physics overhead;
- observability overhead;
- focus/wide-scan starvation;
- memory/log growth;
- duplicate suppression under rapid cycles;
- provider limits;
- queue/backpressure.

Performance optimization may not remove required evidence or change formulas.

---

## 31. Replay / regression validation

Use fixed datasets to compare:
- baseline active strategy;
- new Trade Physics-enabled implementation;
- lifecycle progression;
- signal counts;
- TPS vectors;
- score/TPS distributions;
- rejection reasons;
- event sequences;
- telemetry linkage.

Every intentional behavior change must be attributable to promoted canon; unexplained changes are regressions.

---

## 32. Security / admin validation

Prove:
- role permissions for parameter/model controls;
- no unauthorized formula/weight mutation;
- no secret leakage in logs/model artifacts;
- model registry/artifact integrity checks;
- admin change proof logs;
- rollback controls;
- human-facing explanation does not grant mutation authority.

---

## 33. Human-comprehension validation

Control surfaces displaying Trade Physics must explain:
- TPS meaning/range;
- component meanings;
- deterministic formula/version ownership;
- distinction from `trade_success_probability`;
- model readiness/version when probability shown;
- whether values are informational, gating, or recommendation-only;
- unavailable/unknown reasons.

No naked unexplained TPS/probability control is acceptable where operational interpretation matters.

---

## 34. Deployment-readiness gate

Before governed rollout, require:
- canonical promotion complete;
- code-to-canon audit complete;
- affected unit/integration tests pass;
- replay/regression pass;
- event/schema validation pass;
- restart/recovery pass;
- Distribution test isolated and pass where affected;
- model pipeline tests pass if model feature included;
- rollback baseline prepared;
- monitoring window/failure triggers defined.

---

## 35. Production smoke validation

Production smoke checks may confirm:
- service boots;
- real market data present/current;
- versions/config visible;
- scan cycles occur;
- no schema/log crash;
- expected non-publication remains non-publication when Distribution disabled;
- no broker execution;
- no unexpected model influence.

Smoke success does not replace full validation.

---

## 36. Hard failure triggers

Validation must halt rollout on:
- formula mismatch;
- time-ratio inversion;
- TPS duplicate implementation with divergent math;
- probability fabrication;
- target leakage;
- exact-stage handoff violation;
- candidate logged as delivered without proof;
- duplicate external OPEN_NOW;
- signal identity break;
- market/operational truth collapse;
- schema invalidity;
- unobservable material failure;
- unauthorized parameter/model mutation;
- failed rollback/restart safety.

---

## 37. Evidence retention

Test evidence must be retained long enough for:
- PR/release review;
- rollback analysis;
- regression comparison;
- governance audit;
- model reproducibility.

Transient console-only PASS is insufficient for structural releases.

---

## 38. Relationship to #73

PR #73 or successor runtime work remains blocked until:
1. the combined canonical set is promoted active;
2. active canon is re-audited;
3. code is audited against active contracts;
4. implementation is corrected accordingly;
5. this v3 test plan is executed against the resulting code.

---

## 39. Final principle

Trade Physics and staged execution are trustworthy only when their formulas, ownership, lifecycle semantics, evidence lineage and model boundaries are independently proven—not merely described.

Every intentional runtime behavior must be reproducible from active canon plus explicit real inputs/state, and every learned claim must be supported by leakage-safe labeled evidence and governed readiness.
