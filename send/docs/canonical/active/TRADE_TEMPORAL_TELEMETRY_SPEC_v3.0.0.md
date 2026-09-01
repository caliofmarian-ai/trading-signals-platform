# TRADE_TEMPORAL_TELEMETRY_SPEC_v3.0.0

Version: 3.0.0  
Status: ACTIVE CANONICAL  
Owner: BinaryBot / DROPi Signals  
Scope: post-executable market truth, temporal checkpoints, Trade Physics feature/outcome lineage  
Supersedes: `TRADE_TEMPORAL_TELEMETRY_SPEC_v2.0.0.md`  

Linked authorities:
- `CANONICAL_STRATEGY_STACK_v2.0.0.md`
- `ALGO_SPEC_v3.0.0.md`
- `TRADE_PHYSICS_MODEL_SPEC_v1.0.0.md`
- `TRADE_PHYSICS_INTELLIGENCE_SPEC_v1.0.0.md`
- `TIME_MODEL_UNIFIED_CANON_v3.0.0.md`
- `SR_CORRIDOR_ENGINE_SPEC_v3.0.0.md`
- `DECISION_OBJECT_CANONICAL_SPEC_v2.0.0.md`
- `DECISION_AUDIT_SPEC_v3.0.0.md`
- `OUTCOME_TRACKING_SPEC_v3.0.0.md`
- Performance Analytics successor
- Event/Observability successors

---

## 0. Authority and promotion status

Promotion status: ACTIVE CANONICAL under `CANONICAL_ACTIVATION_RECORD_20260901.md` and `CANONICAL_MASTER_INDEX_v2.0.0.md`.

The major version is justified by structural expansion of the telemetry contract to make Trade Physics feature snapshots, feature-version lineage, label provenance, and learned-probability separation first-class current-scope requirements.

This document does not authorize broker execution, external publication, or model-based production mutation.

---

## 1. Purpose

Trade Temporal Telemetry records objective post-executable market truth for every canonical executable trade observation.

It must answer:
- what the market did after executable intent;
- whether direction was initially correct;
- whether expiry was appropriate;
- whether losses later recovered;
- how corridor/time/score/TPS conditions relate to market outcome;
- whether a failure reflects direction, timing, structure, flow, or noise;
- which Trade Physics features correlate with outcomes;
- whether a learned probability model is calibrated when one is valid and active.

Telemetry is market truth instrumentation. It is independent from Telegram reaction, operator outcome setting, community reports, or broker screenshots.

---

## 2. Canonical architectural position

Strategic order remains:

`Market -> SR/Corridor -> Time -> Scoring + Trade Physics -> DecisionObject -> FSM -> Signal Engine -> governed executable visibility -> Telemetry -> Outcome Reconciliation -> Analytics -> Research -> Intelligence`

Telemetry is downstream of executable signal truth.

It never rewrites:
- DecisionObject truth;
- FSM truth;
- signal-execution truth;
- distribution truth;
- operational/admin outcome truth.

It adds objective market evidence linked to those layers.

---

## 3. Telemetry eligibility

Baseline telemetry trade registration occurs only for an effective executable `OPEN_NOW` that satisfies the canonical execution/visibility boundary defined by the promoted Signal Engine/Event/Distribution contracts.

A mere internally constructed SignalEvent candidate is insufficient evidence of effective executable emission.

Telemetry must not create phantom executed-trade records from:
- PRE candidates;
- CONFIRM candidates;
- blocked/deferred internal candidates;
- failed publication attempts;
- debug-only objects.

If a later canonical broker-execution subsystem becomes authoritative, an additional broker-truth telemetry class may be introduced separately.

---

## 4. Core principles

1. One effective executable signal identity maps to one canonical telemetry outcome chain.
2. Telemetry market truth is independent of human execution behavior.
3. Raw price/timestamp evidence is preserved.
4. Derived classifications never rewrite raw truth.
5. Stable cross-layer identity is mandatory.
6. Trade Physics feature snapshots are immutable point-in-time evidence for a telemetry chain.
7. Feature formulas and model versions must be preserved so historical training/replay can be reconstructed.
8. Learned predictions, when present, are predictions—not labels and not market truth.
9. Training labels must be derived only from post-decision truth and must never leak into pre-decision features.

---

## 5. Required linkage

Every telemetry chain must be joinable with, where applicable:

### 5.1 Signal/execution identity
- `signal_id`
- `execution_attempt_id`
- `setup_correlation_id`
- executable stage (`OPEN_NOW` baseline)
- publication/visibility proof reference

### 5.2 Decision identity
- `decision_id` or equivalent stable decision reference
- `decision_object_version`
- decision timestamp
- strategy version
- parameter-set/version/hash when available

### 5.3 FSM identity
- relevant FSM state/path reference
- accepted stage
- transition reason

### 5.4 Audit/observability identity
- decision-audit reference
- event/trace/correlation identifiers
- telemetry spec version

A telemetry record without sufficient stable linkage is degraded and must not be treated as high-confidence training evidence.

---

## 6. Immutable pre-trade strategy snapshot

At trade registration, telemetry must preserve a compact immutable snapshot sufficient to reconstruct the pre-trade reasoning state.

Minimum domains:

### 6.1 Market
- symbol
- timeframe
- direction
- entry price
- ATR evidence
- volatility/activity state
- gross price speed where available
- `directional_effective_speed`
- `flow_efficiency`

### 6.2 Structural/space
- directional structural barrier identity/reference where available
- `available_space`
- `required_space`
- `space_to_buffer_ratio`
- `trade_space_margin_atr`
- corridor/structure state

### 6.3 Time
- `t_needed`
- `t_needed_adjusted`
- `model_expiry`
- `model_time_reach_ratio`
- `time_to_buffer_ratio`
- `corridor_time_pressure`
- `time_state`
- final executable expiry semantics

### 6.4 Trade Physics
- deterministic `TPS`
- `TPS_S`
- `TPS_T`
- `TPS_P`
- `TPS_V`
- `movement_stress`
- Trade Physics formula/version
- Trade Physics parameter/weight version

### 6.5 Classical strategy scoring
- `score_total`
- score component snapshot
- score tier/band
- relevant hard blockers should be absent for executable signal but any degraded warnings remain traceable

### 6.6 Learned intelligence, only when valid
- `trade_success_probability` if and only if a validated model actually produced it
- model id/version
- feature schema version
- calibration version
- readiness state

If no validated model exists, these learned fields are `null`/absent. The system must never fabricate a default probability.

---

## 7. Trade lifecycle phases

### 7.1 Phase 1 — Trade registration

Triggered at effective executable `OPEN_NOW` truth.

Record at minimum:
- identities from section 5;
- entry price;
- open timestamp;
- executable expiry duration;
- expiry timestamp;
- immutable pre-trade snapshot from section 6.

An open-trade registry may be used operationally, provided restart recovery and exactly-once finalization are governed.

### 7.2 Phase 2 — MID_EXPIRY

`mid_expiry_ts = open_ts + expiry_duration / 2`

Record:
- mid timestamp;
- mid price;
- directional delta from entry;
- `mid_direction_correct`;
- optional favorable/adverse excursion-to-date.

Purpose:
- early directional health;
- entry timing diagnosis;
- separation of immediate failure vs later reversal.

### 7.3 Phase 3 — Official expiry

Record:
- expiry timestamp;
- expiry price;
- `result_at_expiry`.

For BUY:
- price > entry -> WIN
- price < entry -> LOSS
- equal -> DRAW

For SELL:
- price < entry -> WIN
- price > entry -> LOSS
- equal -> DRAW

`DRAW` must remain distinct in raw telemetry.

### 7.4 Phase 4 — Post-expiry checkpoints

Required baseline checkpoints:
- +1 minute
- +3 minutes
- +5 minutes

Record checkpoint prices and directional would-win flags.

Derived recovery classification may include:
- `NO_RECOVERY`
- `RECOVERED_AT_1M`
- `RECOVERED_AT_3M`
- `RECOVERED_AT_5M`
- `EARLY_CORRECT_THEN_REVERSED`

Post-expiry recovery never rewrites `result_at_expiry`.

---

## 8. Official market label contract

Raw canonical market label:

`result_at_expiry = WIN | LOSS | DRAW`

This is the primary market-truth label for baseline supervised outcome analysis.

Additional labels may be derived, but must declare derivation/version:
- binary win/loss label with DRAW policy stated explicitly;
- recovery class;
- directional-thesis class;
- timing-mismatch class;
- path-stability class.

No dataset may silently map DRAW, MISSED, or disputed operational truth into a market WIN/LOSS label.

---

## 9. Training-label provenance and anti-leakage

Every ML-ready example must record:
- label name;
- label source truth domain;
- label derivation version;
- label observation timestamp/window;
- feature cutoff timestamp;
- feature schema version.

Hard rule:

**No feature may contain information observed after the decision/executable cutoff when training a pre-trade probability model.**

Therefore the following are labels/downstream evidence, not pre-trade features:
- expiry result;
- post-expiry recovery;
- future price checkpoints;
- later admin outcome;
- later community report.

Telemetry may store them together for lineage, but dataset builders must preserve temporal separation.

---

## 10. Temporal data model

Recommended raw finalized store remains append-oriented/analytics-friendly, e.g. JSONL.

A canonical finalized record must include:

### Identity
- signal/execution/decision correlation
- symbol
- timeframe
- direction

### Timing
- open timestamp
- expiry duration/timestamp
- midpoint timestamp
- checkpoint timestamps

### Prices
- entry
- midpoint
- expiry
- post-expiry checkpoints

### Raw market outcome
- result at expiry

### Derived market context
- would-win checkpoint flags
- recovery class
- optional path metrics

### Strategy/Trade Physics snapshot
- classical score
- TPS and components
- space/time/speed/flow/stress features
- corridor/time states
- relevant versions

### Optional learned prediction snapshot
- probability
- model/version/calibration/readiness

### Version/provenance
- telemetry spec version
- strategy version
- DecisionObject version
- Trade Physics formula version
- feature schema version
- source provider/feed reference when available

---

## 11. Derived temporal metrics

Telemetry must support derivation of at least:

- Early Direction Accuracy
- Expiry Miss Distance
- Post-Expiry Recovery
- Temporal Continuation Strength
- Temporal Stability Profile

Optional but high-value current-scope metrics:
- Maximum Favorable Excursion (MFE)
- Maximum Adverse Excursion (MAE)
- full price path or sampled path where storage permits

These enrich research and model validation but do not alter official expiry result.

---

## 12. Failure classification support

Loss/recovery analysis may use evidence-backed classes such as:
- insufficient structural space
- temporal mismatch / expiry too short
- slow directional movement
- reversal after entry
- spike/noise
- wrong directional thesis
- late entry
- corridor invalidation
- flow deterioration

Classification must reference actual pre-trade and post-trade evidence and a taxonomy version.

It is explanatory analytics, not raw market truth.

---

## 13. Trade Physics validation analytics requirements

Telemetry must enable evaluation of:

- outcome by TPS band;
- calibration of TPS against realized market truth;
- each component S/T/P/V against outcomes;
- `space_to_buffer_ratio` outcome curves;
- `trade_space_margin_atr` outcome curves;
- `directional_speed_ratio` and `flow_efficiency` outcome curves;
- `movement_stress` outcome curves;
- interaction of classical score and TPS;
- interaction of corridor regime, time state and TPS;
- symbol/session/regime stability of these relationships.

The system must not assume that Intake interpretation bands are empirically correct until telemetry validates them.

---

## 14. Learned model calibration requirements

When `trade_success_probability` exists, telemetry must support:
- predicted probability vs realized market label;
- calibration curves/bins;
- Brier/log-loss or other approved probabilistic metrics;
- discrimination metrics where appropriate;
- segment-specific calibration;
- drift detection;
- missingness and out-of-distribution flags.

A model that is poorly calibrated or outside its approved readiness scope must be downgraded by Intelligence/Governance and must not silently retain influence.

---

## 15. Relationship to Outcome Reconciliation

Telemetry answers:

**What did the market objectively do?**

Outcome Reconciliation answers:

**What did the operator/admin execution path record?**

Examples:
- telemetry LOSS, admin WIN after late/manual exit;
- telemetry WIN, admin MISSED because no entry occurred.

Both truths remain stored, labeled and joinable.

---

## 16. Relationship to Decision Audit

Decision Audit preserves what the strategy believed and why before FSM/execution.

Telemetry preserves what happened after effective executable truth.

Telemetry must never back-edit Decision Audit.

---

## 17. Data integrity rules

### Rule 1 — Exactly one canonical final telemetry chain per effective executable signal identity
Retries must be idempotent.

### Rule 2 — Market feed authority
Evaluation prices must use the governed market-data authority.

### Rule 3 — Raw truth preservation
Raw prices/timestamps/results are immutable evidence.

### Rule 4 — Joinability
Missing identity/correlation degrades confidence and may disqualify a record from model training.

### Rule 5 — Versioned feature semantics
The same field name must not change formula silently across historical records.

### Rule 6 — No fabricated fields
Unavailable feature/model outputs remain missing/null with explicit reason where needed.

### Rule 7 — No user-report substitution
Community/admin reports cannot replace market-price-derived labels.

---

## 18. Adaptive activity telemetry

Normalized activity ratio, volatility reference scale, activity gate result and downstream actionability effect may be captured when they are part of the pre-trade decision snapshot.

They are strategy evidence, not independent strategy authority.

---

## 19. Storage and scale

Raw telemetry should remain:
- durable;
- append-oriented;
- replayable;
- versioned;
- suitable for longitudinal datasets;
- restart/recovery safe.

Rotation/compression/aggregation may be added without deleting raw provenance required for audit and model reproducibility.

---

## 20. Implementation sequence after promotion

1. enforce effective-executable eligibility and stable identity;
2. persist immutable pre-trade snapshot including full Trade Physics fields;
3. preserve current midpoint/expiry/post-expiry checkpoints;
4. add feature/version provenance;
5. build deterministic dataset materialization with leakage tests;
6. validate TPS empirically before changing stage gates;
7. only then train/evaluate learned models;
8. expose model output only under approved readiness state.

---

## 21. Non-goals

This document does not define:
- strategy formulas beyond consuming their snapshots;
- FSM transition rules;
- distribution routing;
- Telegram UX;
- operational/admin outcome authority;
- broker execution truth;
- autonomous parameter mutation.

---

## 22. Final principle

Trade Temporal Telemetry is the objective post-executable evidence system that lets BinaryBot test whether its structural, temporal, classical-score and Trade Physics beliefs match what the market actually did.

It is the principal label/provenance source for Trade Physics research and learned probability validation, while preserving strict separation between pre-trade features, post-trade labels, and operational/admin truth.
