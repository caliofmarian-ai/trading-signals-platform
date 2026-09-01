# TRADE_PHYSICS_INTELLIGENCE_SPEC_v1.0.0

Path: /opt/binarybot/docs/canonical/active/TRADE_PHYSICS_INTELLIGENCE_SPEC_v1.0.0.md  
Version: 1.0.0  
Status: ACTIVE CANONICAL  
Owner: BinaryBot / DROPi Signals  
Scope: Trade Physics learned intelligence, feature lineage, probability calibration, model readiness, recommendations, governed adaptation

Source provenance:
- `send/docs/intake/AI_TRADE_PHYSICS_INTELLIGENCE_SPEC.md`
- relevant dataset/feature material from `AI_TRADE_PHYSICS_SPACE_MODEL_SPEC.md`
- relevant TPS component material from `TRADE_PHYSICS_SCORE_SPEC.md`
- Owner decision 2026-09-01: Trade Physics is current-scope now
- Change ID `20260901-TRADE-PHYSICS-01`

Authority relationship:
- `TRADE_PHYSICS_MODEL_SPEC_v1.0.0` owns deterministic Trade Physics mathematics and TPS.
- `ALGO_SPEC_v3.0.0` owns live strategy role.
- this document owns learned Trade Physics probability/calibration semantics.
- Research/Learning owns experiment/training evidence discipline.
- Performance Analytics owns outcome-linked performance measurement.
- Strategy Intelligence owns operator-facing interpretation and recommendation integration.
- Autonomous Evolution / Governance own proposal/approval/rollout boundaries.

---

## 1. PURPOSE

This document integrates the AI Trade Physics intelligence source into the current governed project scope.

Its purpose is to learn, from real decision-time Trade Physics features and real downstream outcomes, whether a setup has empirically favorable completion probability under specific market conditions.

It does not replace deterministic TPS.

It does not authorize autonomous production mutation.

It creates the current architecture required to:

- collect versioned Trade Physics features;
- link them to objective outcomes;
- train candidate models;
- validate/calibrate probability;
- detect drift;
- issue evidence-backed recommendations;
- support bounded governed evolution after human approval.

---

## 2. CURRENT-SCOPE PRINCIPLE

The prior intake timing that treated AI Trade Physics as a later/future phase is superseded by the Owner decision dated 2026-09-01.

Current-scope means the project must now implement the complete governed subsystem architecture, including explicit no-model/not-ready states.

Current-scope does **not** mean:

- fabricate a trained model;
- invent model weights;
- claim predictive accuracy without evidence;
- grant live authority before validation;
- bypass Owner/Admin governance.

A correctly implemented `UNTRAINED` or `INSUFFICIENT_DATA` state is a complete current system state, not a missing future upgrade.

---

## 3. FOUR-DIMENSION TRADE PHYSICS FEATURE MODEL

The source document defines four conceptual dimensions:

1. Energy
2. Space
3. Time
4. Flow

They are retained but reconciled to deterministic canonical features.

### 3.1 Energy

Source concept:

`E = buffer_distance / ATR`

Canonical mapping:

`energy_stress_ratio = movement_stress = required_space / atr_m5`

For Trade Physics v1, `required_space = buffer_distance`, so the two source primitives are mathematically equivalent.

The learned dataset must not duplicate them as independent information without an explicit reason.

### 3.2 Space

Source concept:

`S = available_space / required_space`

Canonical feature:

`reachability_ratio = space_to_buffer_ratio`

Structural source must remain Corridor Engine.

### 3.3 Time

Source concept:

available time / time needed.

Canonical feature:

`time_availability_ratio = time_to_buffer_ratio = model_expiry / t_needed_adjusted`

This is the reciprocal of `model_time_reach_ratio` for synchronized positive evidence.

### 3.4 Flow

Source concept:

momentum alignment / directional flow.

Canonical features include:

- `directional_effective_speed`;
- `weighted_gross_speed`;
- `flow_efficiency`;
- approved momentum/trend context;
- optional directional-speed ratio.

Flow features must be decision-time features only.

---

## 4. DETERMINISTIC TPS VS LEARNED PROBABILITY

Two different intake formulas were originally called TPS.

That conflict is resolved.

### 4.1 Deterministic TPS

`TPS` is the deterministic physical-feasibility score in `[0,100]`, owned by `TRADE_PHYSICS_MODEL_SPEC_v1.0.0`.

### 4.2 Learned output

The learned/calibrated output is:

`trade_success_probability`

Range when valid:

`0 <= trade_success_probability <= 1`

It must never be serialized under the field `TPS`.

---

## 5. SOURCE SIGMOID FORM

The intake AI source proposes conceptually:

`sigmoid(w1*(1/E) + w2*log(S) + w3*log(T) + w4*F)`

This is retained as a candidate functional form and research hypothesis, not as a production formula with invented constants.

Reasons:

- no validated `w1..w4` values are supplied by the source;
- no calibration sample is supplied;
- feature transformations require numerical guards;
- the source's `E`, `S`, `T`, `F` must be reconciled to canonical feature definitions.

If this model form is evaluated, weights must come from real training/validation or a separately governed explicit model configuration.

---

## 6. MODEL FAMILY

The source recommends Gradient Boosted Trees, including examples such as LightGBM and XGBoost, for tabular Trade Physics data.

Canonical interpretation:

- Gradient Boosted Trees are approved candidate model families;
- LightGBM/XGBoost are research/implementation candidates;
- no specific external library is canonical merely because it is named in the source;
- model-family selection must be recorded in model metadata and validation evidence.

Other model families may be evaluated through Research/Learning governance without redefining deterministic TPS.

---

## 7. FEATURE DATASET CONTRACT

A training row must be traceable to a decision-time setup and must contain versioned, leakage-safe features.

Required/important feature families include:

### Identity/context

- setup/candidate id;
- signal id if later assigned;
- symbol;
- direction;
- timeframe;
- candle/evaluation timestamp;
- session/regime labels;
- strategy/canonical versions.

### Market

- ATR;
- trend context;
- noise/volatility state;
- buffer distance.

### Structure

- available space;
- required space;
- space-to-buffer ratio;
- trade-space margin ATR;
- corridor regime;
- proximity/compression/conflict state.

### Time

- t_needed;
- t_needed_adjusted;
- model_expiry;
- model_time_reach_ratio;
- time_to_buffer_ratio;
- corridor time pressure;
- time state.

### Flow

- directional effective speed;
- weighted gross speed;
- flow efficiency;
- directional speed ratio;
- approved momentum context.

### Deterministic scoring

- S/T/P/V;
- deterministic TPS;
- classical score total/components;
- blocker/degrade semantics.

### Label linkage

- downstream market-truth outcome reference;
- telemetry lineage;
- reconciled operational outcome reference where separately analyzed;
- label definition/version.

Truth layers must be stored with labels; market truth and operator truth must not be silently merged.

---

## 8. FEATURE LINEAGE

Every model artifact must be traceable to:

- feature schema version;
- source event/DecisionObject schema version;
- deterministic Trade Physics version;
- strategy version;
- data extraction code/version;
- source time window;
- symbol/session universe;
- data cleaning/exclusion rules.

Feature lineage is mandatory because Trade Physics formulas themselves may evolve.

---

## 9. LEAKAGE PREVENTION

Training and validation must prohibit future information from entering decision-time features.

Examples of forbidden leakage:

- outcome result as an input feature;
- post-entry price checkpoints as decision features;
- final execution success that occurred after the decision;
- later corrected labels injected into historical feature values;
- post-signal Telegram/user reactions as market-decision features.

Label data may be joined downstream for training, but must remain clearly separated from features available at decision time.

---

## 10. OUTCOME LABELS

The primary learned probability target must be defined using a versioned objective label contract.

The project must distinguish possible targets such as:

- market-truth favorable outcome at canonical expiry;
- target/buffer reach before expiry;
- binary WIN/LOSS under a stated payout/execution convention;
- operational/admin-reconciled outcome.

No unlabeled generic `success` target is allowed.

If multiple targets are modeled, they require distinct model identities/probability fields or target metadata.

Market truth should be preferred for strategy-quality learning when available and reliable, while operational truth remains separately valuable for execution analysis.

---

## 11. DATA READINESS

Training must not start merely because rows exist.

Readiness must consider:

- sample size;
- class balance;
- missingness;
- truth-label integrity;
- symbol/session representation;
- regime coverage;
- strategy-version consistency;
- feature-schema consistency;
- leakage audit;
- telemetry/outcome discrepancy rates.

Exact production minimum sample thresholds belong to Research/Learning / Statistical Proof governance and must not be invented by the runtime.

---

## 12. MODEL READINESS STATES

The current subsystem must expose explicit readiness.

Canonical proposed states:

- `UNTRAINED`
- `INSUFFICIENT_DATA`
- `TRAINING_FAILED`
- `TRAINED_UNVALIDATED`
- `VALIDATION_FAILED`
- `VALIDATED_RECOMMEND_ONLY`
- `APPROVED_FOR_BOUNDED_USE`
- `SUSPENDED_DRIFT`
- `INVALID_MODEL`

These states are operationally meaningful.

No probability is authoritative merely because a model file exists.

---

## 13. MODEL ARTIFACT CONTRACT

Every trained candidate model must have immutable/reviewable metadata including:

- model id;
- model version;
- model family/algorithm;
- training dataset id/version;
- feature schema version;
- target/label version;
- strategy/Trade Physics source versions;
- training window;
- validation window;
- hyperparameter/config reference;
- calibration method;
- evaluation metrics;
- readiness state;
- approval record;
- artifact checksum/location;
- created timestamp.

A model without this provenance is not governed Trade Physics intelligence.

---

## 14. VALIDATION

Validation must use out-of-sample or otherwise rigorously separated evidence.

Required evaluation families should include as applicable:

- discrimination/ranking metrics;
- probability calibration metrics;
- confusion/threshold analysis where thresholds are evaluated;
- per-symbol/session/regime stability;
- comparison against deterministic TPS alone;
- comparison against classical score alone;
- incremental-value analysis;
- drift sensitivity.

A model that performs well only in one narrow contaminated slice cannot be generalized silently.

---

## 15. CALIBRATION

If the output is called `trade_success_probability`, probability calibration must be measured.

The model must not report a raw arbitrary score as probability without calibration evidence or an explicit non-probability name.

Calibration evidence may include reliability curves/bins and appropriate statistical metrics under the research framework.

Calibration method/version must be recorded.

---

## 16. TRAINING / VALIDATION SPLIT DISCIPLINE

Splits must respect time ordering where necessary to avoid future-to-past contamination.

Random row shuffling alone may be insufficient for time-dependent market data.

Research must document:

- split method;
- cutoff dates/windows;
- overlapping-signal handling;
- symbol leakage considerations;
- regime shift considerations.

---

## 17. TRADE SUCCESS PROBABILITY CONTRACT

When a model is valid and permitted to infer:

- input must match the model's feature schema;
- all required features must be available or handled exactly as model metadata specifies;
- model id/version must accompany the output;
- readiness must be at least the required state for the intended usage;
- output must be finite and constrained to `[0,1]`;
- inference failure must be explicit.

No fallback guessed probability is allowed.

---

## 18. CURRENT AUTHORITY MODE

The subsystem is current-scope, but authority is bounded by evidence.

Default current authority after implementation:

- feature collection: enabled when canonically implemented;
- dataset construction: enabled under truth/retention rules;
- training/evaluation: enabled in research/staging environment;
- inference: allowed for validated model analysis/recommendation;
- deterministic strategy replacement: forbidden;
- silent live parameter mutation: forbidden;
- live decision weighting: requires separate active approval/bounds.

This implements the source's recommend-only / admin-approve safety concept while retaining future bounded use as governed, not automatic.

---

## 19. CALIBRATION ENGINE

The current architecture must include a calibration function/subsystem capable of:

- comparing predicted probability to realized market truth;
- measuring error by score/probability band;
- measuring error by symbol/session/regime;
- detecting persistent overconfidence/underconfidence;
- producing retraining/review recommendations;
- detecting model drift;
- preserving model-version-specific evidence.

The calibration engine does not itself alter production strategy.

---

## 20. PARAMETER RECOMMENDATIONS

The source document proposes that intelligence may recommend changes such as:

- Trade Physics weights;
- thresholds;
- buffer behavior;
- expiry/time treatment;
- feature/model calibration.

Canonical boundary:

- AI may recommend;
- Research may test;
- Autonomous Evolution may package a proposal;
- Owner/Admin governance approves/rejects;
- Parameter Control applies only values explicitly classified as tunable;
- structural formula changes require canonical versioning.

---

## 21. RECOMMENDATION RECORD

Every meaningful recommendation should contain:

- recommendation id;
- model/evidence basis;
- hypothesis/category;
- current value/behavior;
- proposed value/behavior;
- expected effect;
- uncertainty/confidence;
- affected symbols/regimes;
- validation plan;
- risk;
- rollback plan;
- approval state.

Opaque “AI says change X” is forbidden.

---

## 22. SAFETY MODES

The intake source identifies safety modes such as:

- recommend-only;
- admin approval;
- bounded auto-adjust.

Canonical current interpretation:

### RECOMMEND_ONLY

May generate evidence-backed recommendations. No production mutation.

### ADMIN_APPROVAL_REQUIRED

An authorized human may approve a governed staged/production change through the existing change-control path.

### BOUNDED_USE

May exist only if separate active canon defines:

- exact eligible parameters/actions;
- numeric bounds;
- sample/readiness requirements;
- rate limits;
- rollback trigger;
- audit events;
- Owner override.

No generic self-modifying mode is allowed.

---

## 23. DRIFT DETECTION

Model drift must be measured separately from strategy drift.

Detect possible drift in:

- feature distributions;
- TPS component distributions;
- probability calibration;
- ranking quality;
- symbol/session behavior;
- regime composition;
- missingness;
- outcome base rate.

A material drift condition may move readiness to `SUSPENDED_DRIFT` and must remove any bounded live influence until reviewed.

---

## 24. RETRAINING

Retraining may be triggered/proposed by:

- sufficient new evidence;
- calibration degradation;
- feature-schema change;
- strategy-version change;
- sustained drift;
- approved research experiment.

A retrained model is a new model version/artifact. It does not overwrite provenance of the old one.

Promotion of a new model to any authority state requires validation and approval.

---

## 25. RELATION TO DETERMINISTIC TPS

The intelligence subsystem must explicitly compare itself to deterministic TPS.

Research questions include:

- does learned probability add predictive information beyond TPS?
- which TPS components matter most?
- does the model simply rediscover TPS weights?
- where do model and TPS disagree?
- are disagreements stable by regime?

A learned model is not automatically superior because it is AI/ML.

---

## 26. RELATION TO CLASSICAL SCORE

The model may use classical score/components as features only if:

- they existed at decision time;
- lineage/version is recorded;
- leakage is absent.

Analytics must test incremental value against both:

- classical score baseline;
- deterministic TPS baseline.

---

## 27. RELATION TO DECISIONOBJECT

DecisionObject may carry learned context only as a distinct intelligence domain.

Required when probability exists:

- probability;
- model id/version;
- readiness;
- feature schema;
- authority/influence marker.

Historical DecisionObject must remain immutable after later model retraining.

If retrospective inference is performed for research, it must be stored as derived research truth, not rewritten into the original decision record.

---

## 28. RELATION TO PERFORMANCE ANALYTICS

Performance Analytics must support:

- performance by TPS band;
- performance by probability band;
- calibration by band;
- classical-score/TPS/model disagreement;
- missing/not-ready rates;
- model version comparisons;
- outcome truth separation;
- segment/regime analysis.

---

## 29. RELATION TO RESEARCH AND LEARNING

Research/Learning owns:

- hypothesis registry;
- experiment design;
- evidence confidence;
- sample adequacy;
- training/validation methodology review;
- model-comparison study;
- conclusion/recommendation quality.

Trade Physics Intelligence consumes those governance capabilities rather than creating a second research system.

---

## 30. RELATION TO AUTONOMOUS EVOLUTION

Autonomous Evolution may:

- monitor model performance;
- detect candidate parameter/model improvements;
- simulate alternatives;
- package recommendations;
- recommend rollback/suspension.

It may not silently push production strategy or model authority changes.

---

## 31. OBSERVABILITY

Intelligence operations must be auditable where material, including:

- dataset build/version;
- training start/result;
- validation result;
- model registration;
- readiness transition;
- inference failure;
- recommendation creation;
- approval/rejection;
- bounded-use activation/deactivation;
- drift suspension;
- rollback.

Exact event families must be integrated into the consolidated Event Schema rather than invented as unvalidated ad hoc logs.

---

## 32. SECURITY AND DATA GOVERNANCE

Model training data must follow active security/privacy/retention policy.

The Trade Physics model does not require personally identifying member data for market prediction.

Market/decision/outcome datasets should avoid unnecessary user identity.

Model artifacts and mutable control surfaces require appropriate role/permission protection.

---

## 33. FAILURE HANDLING

If training, model loading or inference fails:

- deterministic strategy continues according to its own active canon;
- no guessed probability is inserted;
- readiness moves to an appropriate non-authoritative state;
- failure is observable;
- any bounded influence fails closed/disabled;
- last-known model may only remain usable if active policy explicitly permits and its validity/readiness is still intact.

---

## 34. FORBIDDEN PATTERNS

Forbidden:

- same field name TPS for deterministic and learned outputs;
- invented `w1..w4` treated as trained truth;
- probability claim without calibration evidence;
- training on mixed/unlabeled truth layers;
- future outcome leakage;
- hidden model version;
- training artifact directly deployed without validation;
- live mutation from recommendation without governance;
- auto-adjust without explicit bounds;
- retrospective model inference overwriting original DecisionObject;
- silently using community reports as objective market labels;
- declaring AI superior without baseline comparison.

---

## 35. IMPLEMENTATION PHASES AFTER PROMOTION

Current-scope implementation sequence:

1. canonical Trade Physics features in DecisionObject/events;
2. outcome/telemetry lineage;
3. versioned dataset builder;
4. model registry/readiness state store;
5. candidate training pipeline;
6. validation/calibration pipeline;
7. probability inference interface;
8. analytics comparison views;
9. recommendation/calibration engine;
10. admin/governance review surfaces;
11. only then any separately approved bounded influence.

These are current implementation work items after canon, not deferred undefined upgrades.

---

## 36. VALIDATION REQUIREMENTS

At minimum:

1. dataset rows reproduce decision-time source features exactly;
2. no post-outcome fields appear as features;
3. model artifact has complete provenance;
4. untrained state works without breaking deterministic strategy;
5. probability absent when model is not ready;
6. output is distinct from TPS;
7. calibration is measured before probability is called validated;
8. time-aware validation prevents obvious leakage;
9. model comparisons include classical score and TPS baselines;
10. readiness transitions are auditable;
11. drift can suspend authority;
12. recommendations cannot mutate production directly;
13. model rollback/version recovery is testable.

---

## 37. FINAL PRINCIPLE

Trade Physics Intelligence is now part of the current system architecture.

Its job is not to replace governed strategy with an opaque AI.

Its job is:

`DETERMINISTIC TRADE PHYSICS + REAL OUTCOMES -> VERSIONED DATASET -> VALIDATED MODEL -> CALIBRATED trade_success_probability -> EXPLAINABLE RECOMMENDATION -> GOVERNED ACTION`

If evidence is not ready, the correct output is a truthful not-ready state, never an invented probability.
