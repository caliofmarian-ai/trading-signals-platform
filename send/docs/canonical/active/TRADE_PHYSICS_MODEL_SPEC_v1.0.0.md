# TRADE_PHYSICS_MODEL_SPEC_v1.0.0

Path: /opt/binarybot/docs/canonical/active/TRADE_PHYSICS_MODEL_SPEC_v1.0.0.md  
Version: 1.0.0  
Status: ACTIVE CANONICAL  
Owner: BinaryBot / DROPi Signals  
Change ID: 20260901-TRADE-PHYSICS-01  
Scope: Deterministic Trade Physics mathematics, physical-feasibility scoring, canonical Trade Physics feature contract, and separation between deterministic TPS and learned probability

Source provenance:
- `send/docs/intake/AI_TRADE_PHYSICS_SPACE_MODEL_SPEC.md`
- `send/docs/intake/TRADE_PHYSICS_SCORE_SPEC.md`
- `send/docs/intake/AI_TRADE_PHYSICS_INTELLIGENCE_SPEC.md`
- Owner decision dated 2026-09-01: Trade Physics is current-scope and must be integrated now, not retained as a future upgrade.

Authority relationship:
- `ALGO_SPEC` remains authoritative for the role of scoring inside the strategy and for how TPS affects strategic decision semantics.
- `SR_CORRIDOR_ENGINE_SPEC` remains authoritative for structural barrier and corridor truth.
- `TIME_MODEL_UNIFIED_CANON` remains authoritative for time-model mathematics and vocabulary.
- this document is the active detailed mathematical authority for Trade Physics metric derivation and deterministic TPS.
- `STRATEGY_INTELLIGENCE_SYSTEM`, `RESEARCH_AND_LEARNING_FRAMEWORK_SPEC`, `PERFORMANCE_ANALYTICS_SPEC`, and `AUTONOMOUS_STRATEGY_EVOLUTION_SYSTEM` remain authoritative for learned-model evidence, training, calibration, recommendations, and governed evolution.

This document does not authorize broker execution, distribution, or automatic production mutation.

---

## 1. PURPOSE

Trade Physics measures whether a setup is physically feasible under the observed market structure, time budget, directional movement and volatility scale.

The model exists because directional indicators alone do not answer four essential questions:

1. Is there enough structural space?
2. Is there enough time?
3. Is price moving efficiently enough in the intended direction?
4. Is the required movement realistic relative to volatility?

Trade Physics converts those questions into explicit evidence and one deterministic companion score: `TPS`.

The model is current-scope for Binary Strategy V2.

---

## 2. CANONICAL POSITION

The official strategy pipeline remains:

`MARKET DATA -> MARKET MODEL -> SR / CORRIDOR ENGINE -> TIME MODEL -> SCORING MODEL -> DECISION OBJECT -> FSM -> SIGNAL ENGINE`

Trade Physics is not a new top-level pipeline stage.

Trade Physics is a governed physical-feasibility submodel inside the strategic/scoring domain. It consumes upstream evidence from Market Model, SR/Corridor and Time Model before `DecisionObject` is produced.

Therefore:

- Trade Physics mathematics MUST NOT be owned by Signal Engine.
- Signal Engine may consume or log already-produced Trade Physics evidence but MUST NOT be the primary calculator of strategic TPS.
- FSM MUST NOT reconstruct Trade Physics from raw market inputs.
- Trade Physics evidence MUST be available before FSM through the strategic contract.

---

## 3. SOURCE RECONCILIATION DECISIONS

The intake sources contain overlapping and conflicting definitions. This active canon resolves them as follows.

### 3.1 One deterministic TPS

The canonical deterministic Trade Physics Score is the weighted `[0,100]` TPS from `TRADE_PHYSICS_SCORE_SPEC.md`.

The sigmoid output described in `AI_TRADE_PHYSICS_INTELLIGENCE_SPEC.md` MUST NOT also be named TPS.

### 3.2 Learned probability is separate

A learned/calibrated model output is named `trade_success_probability` in this specification.

It is a distinct value in `[0,1]` and MUST carry model/version/readiness provenance.

### 3.3 Active vocabulary wins

The following active canonical vocabulary is used:

- `buffer_distance`, not `buffer_price` as primary truth;
- `t_needed_adjusted`, not `t_needed_adj_min` as primary truth;
- `model_expiry`, not generic `expiry_minutes` as primary model-time truth;
- `model_time_reach_ratio` retains Time Model authority.

Legacy names may be mapped only in compatibility layers.

### 3.4 Deterministic score is not automatically empirical probability

`TPS` is a deterministic physical-feasibility score.

It MUST NOT be labeled an empirically calibrated probability unless outcome evidence demonstrates calibration.

`trade_success_probability` is reserved for learned/calibrated probability.

---

## 4. PRIMARY INPUT CONTRACT

A complete Trade Physics evaluation requires synchronized evidence for the same symbol, candle context, direction and evaluation timestamp.

Required inputs:

- `direction`
- `current_price`
- `available_space`
- `buffer_distance`
- `atr_m5`
- `model_expiry`
- `t_needed_adjusted`
- `price_speed`
- sufficient M1 close history for `directional_effective_speed`
- market noise/stability state

All numeric inputs MUST be finite.

The following MUST be strictly positive where used as denominators:

- `buffer_distance`
- `atr_m5`
- `model_expiry`
- `t_needed_adjusted`

Trade Physics MUST NOT invent missing market evidence.

If required evidence is unavailable, the evaluation state is `UNAVAILABLE` and no TPS may be fabricated from a partial subset.

---

## 5. STRUCTURAL SPACE MODEL

### 5.1 available_space

`available_space` is the directional distance from the current/evaluation price to the nearest relevant structural barrier in the intended trade direction.

For BUY:

- the nearest relevant resistance / upper structural boundary constrains available space.

For SELL:

- the nearest relevant support / lower structural boundary constrains available space.

The SR/Corridor Engine owns barrier selection and structural validity.

### 5.2 required_space

For Binary Strategy V2 Trade Physics v1:

`required_space = buffer_distance`

This relation preserves the intake model while using active canonical vocabulary.

A future change where required space differs from buffer distance is structural and requires a versioned canonical change.

### 5.3 space_to_buffer_ratio

`space_to_buffer_ratio = available_space / required_space`

Interpretation:

- `< 1.0` => structurally constrained; the required move does not fit before the directional barrier;
- `= 1.0` => marginal structural fit;
- `> 1.0` => sufficient structural room;
- values materially above `1.0` => progressively more structural room, subject to cap in normalized scoring.

### 5.4 trade_space_margin_atr

`trade_space_margin_atr = (available_space - required_space) / atr_m5`

Interpretation:

- `< 0` => insufficient structural room;
- `≈ 0` => tight/marginal room;
- `> 0` => positive room after volatility normalization.

### 5.5 Structural hard truth

If the SR/Corridor Engine declares the directional structure invalid or `available_space < required_space`, the setup is physically constrained regardless of a high arithmetic TPS produced from any other components.

Arithmetic score MUST NOT override a hard structural blocker.

---

## 6. TIME FEASIBILITY MODEL

Time Model remains the sole authority for canonical time mathematics.

Trade Physics consumes:

- `model_expiry`
- `t_needed_adjusted`
- `model_time_reach_ratio`
- `time_state`

### 6.1 time_to_buffer_ratio

To preserve the intake Trade Physics interpretation while respecting active time vocabulary:

`time_to_buffer_ratio = model_expiry / t_needed_adjusted`

For positive synchronized inputs:

`time_to_buffer_ratio = 1 / model_time_reach_ratio`

when `model_time_reach_ratio = t_needed_adjusted / model_expiry` is derived from the same evidence.

Interpretation:

- `< 1.0` => insufficient model time for the required move;
- `= 1.0` => exact/marginal time fit;
- `> 1.0` => positive time headroom.

### 6.2 No parallel time authority

Trade Physics MUST NOT redefine:

- how `model_expiry` is selected;
- how `t_needed_adjusted` is produced;
- Time Model state classification.

It only derives a Trade Physics-friendly reciprocal ratio from canonical time evidence.

---

## 7. DIRECTIONAL EFFECTIVE SPEED

The AI Trade Physics intake source requires speed to be:

- directional;
- recency-weighted;
- noise-aware;
- expressed as price distance per minute.

The active runtime currently uses an undirected average absolute close-to-close movement for `price_speed`. That value may remain as gross movement context but does not fully satisfy directional Trade Physics.

### 7.1 Canonical v1 deterministic algorithm

This section is a technical reconciliation in this active specification because the intake source defines the concept but does not provide exact weights.

Use the most recent 20 completed M1 intervals, matching the current Market Model speed horizon.

Let chronological closes be `c_0 ... c_20`, oldest to newest.

For each interval `i = 1..20`:

For BUY:

`directional_delta_i = max(c_i - c_(i-1), 0)`

For SELL:

`directional_delta_i = max(c_(i-1) - c_i, 0)`

Gross movement:

`gross_delta_i = abs(c_i - c_(i-1))`

Recency weights:

`w_i = i`

so the newest interval receives weight 20 and the oldest receives weight 1.

Weighted time in minutes:

`weighted_time = sum(w_i)`

because every interval is one minute.

Directional effective speed:

`directional_effective_speed = sum(w_i * directional_delta_i) / weighted_time`

Weighted gross speed:

`weighted_gross_speed = sum(w_i * gross_delta_i) / weighted_time`

This algorithm is deterministic, directional and recency-weighted.

### 7.2 Noise-aware rule

If the Market Model declares the synchronized market evidence `UNSTABLE`, Trade Physics readiness is false for decision influence.

The raw directional/gross speed values may still be retained for diagnostics, but the model MUST NOT present a normal ready TPS as if noise were absent.

This uses the existing Market Model noise authority rather than inventing an independent hidden denoising threshold.

### 7.3 flow_efficiency

If `weighted_gross_speed > 0`:

`flow_efficiency = directional_effective_speed / weighted_gross_speed`

Range:

`0 <= flow_efficiency <= 1`

Interpretation:

- near `1.0` => movement is strongly aligned with the intended direction;
- around `0.5` => mixed/choppy directional efficiency;
- near `0.0` => little useful directional movement.

If gross speed is zero, flow efficiency is unavailable rather than fabricated.

---

## 8. SPEED NORMALIZATION FOR DETERMINISTIC TPS

The deterministic TPS source document defines speed relative to ATR.

### 8.1 atr_speed_reference

For Trade Physics v1:

`reference_minutes = 5`

`atr_speed_reference = atr_m5 / reference_minutes`

### 8.2 directional_speed_ratio

`directional_speed_ratio = directional_effective_speed / atr_speed_reference`

This intentionally differs from the current undocumented Signal Engine implementation that uses a buffer/expiry required-speed reference.

The undocumented runtime formula MUST NOT become canonical by existence alone.

---

## 9. VOLATILITY / MOVEMENT STRESS

### 9.1 movement_stress

`movement_stress = required_space / atr_m5`

Given the v1 relation `required_space = buffer_distance`, this is also the primitive represented conceptually as Buffer-ATR Energy in the AI intake document.

### 9.2 volatility_efficiency

`V = 1 / (1 + movement_stress)`

Interpretation:

- larger movement stress => lower volatility efficiency;
- smaller movement stress => higher volatility efficiency.

### 9.3 No double counting of E and V

The AI intake variable `E = buffer_distance / ATR` and deterministic `movement_stress` are the same primitive under the v1 required-space relation.

Therefore E MUST NOT be independently weighted again in deterministic TPS.

For AI feature naming, the primitive may be exposed as `energy_stress_ratio = movement_stress` with explicit provenance.

---

## 10. NORMALIZED DETERMINISTIC TPS COMPONENTS

### 10.1 Space component S

`S_cap = 3.0`

`S = clamp(space_to_buffer_ratio, 0, S_cap) / S_cap`

### 10.2 Time component T

`T_cap = 2.0`

`T = clamp(time_to_buffer_ratio, 0, T_cap) / T_cap`

### 10.3 Directional speed component P

`P_cap = 2.0`

`P = clamp(directional_speed_ratio, 0, P_cap) / P_cap`

### 10.4 Volatility efficiency component V

`V = 1 / (1 + movement_stress)`

For valid non-negative movement stress, V is in `(0,1]`.

---

## 11. DETERMINISTIC TPS FORMULA

The canonical initial weights are sourced from `TRADE_PHYSICS_SCORE_SPEC.md`:

- `wS = 0.35`
- `wT = 0.25`
- `wP = 0.20`
- `wV = 0.20`

Constraint:

`wS + wT + wP + wV = 1.0`

Formula:

`TPS_raw = wS*S + wT*T + wP*P + wV*V`

`TPS = 100 * TPS_raw`

With valid component inputs:

`0 <= TPS <= 100`

The implementation MUST use deterministic arithmetic and MUST NOT substitute learned probability into this field.

---

## 12. TPS INTERPRETATION BANDS

The source document provides the following descriptive bands:

- `TPS < 30` => physically weak;
- `30 <= TPS < 50` => weak;
- `50 <= TPS < 65` => moderate;
- `65 <= TPS < 80` => strong;
- `TPS >= 80` => excellent physical conditions.

These are **interpretation bands**, not automatically lifecycle thresholds.

No PRE / CONFIRM / OPEN_NOW gate may be silently inferred from these bands.

Any lifecycle threshold derived from TPS requires explicit ALGO/parameter governance and replay evidence.

---

## 13. CURRENT DECISION ROLE

Trade Physics is current-scope and mandatory in the active strategic contract; implementation remains governed by active change, test, and deployment controls.

The initial current role is:

1. mandatory physical-feasibility calculation for every setup with complete evidence;
2. explicit physical-feasibility evidence in scoring and `DecisionObject`;
3. hard respect for existing structural and temporal blockers;
4. deterministic companion TPS alongside the existing strategy score;
5. no silent replacement of `score_total`;
6. no independent lifecycle promotion based only on TPS until an explicit versioned decision policy is approved.

This is not a future-upgrade classification. TPS is part of the current strategy evaluation.

The distinction is that current integration does not invent unsupported lifecycle thresholds.

---

## 14. TRADE PHYSICS READINESS

A Trade Physics evaluation must expose one of the following canonical readiness states:

- `READY`
- `UNAVAILABLE_MISSING_STRUCTURE`
- `UNAVAILABLE_MISSING_TIME`
- `UNAVAILABLE_MISSING_ATR`
- `UNAVAILABLE_MISSING_SPEED`
- `BLOCKED_UNSTABLE_MARKET`
- `INVALID_EVIDENCE`

A normal numeric TPS MUST only be authoritative when the deterministic components are valid and synchronized.

Any adjustment to the exact state enum requires versioned canonical review/change control, and missing evidence MUST remain explicit.

---

## 15. DECISIONOBJECT CONTRACT

The canonical strategic contract must expose a recognizable Trade Physics domain or score subdomain containing at minimum:

- readiness state;
- `available_space`;
- `required_space`;
- `space_to_buffer_ratio`;
- `trade_space_margin_atr`;
- `time_to_buffer_ratio`;
- `directional_effective_speed`;
- `weighted_gross_speed`;
- `flow_efficiency`;
- `atr_speed_reference`;
- `directional_speed_ratio`;
- `movement_stress`;
- normalized components `S`, `T`, `P`, `V`;
- `TPS`;
- TPS interpretation band;
- source/provenance references sufficient for audit.

FSM receives the standardized strategic truth and MUST NOT rederive these values from candles.

---

## 16. DECISION AUDIT AND OBSERVABILITY

Decision audit must preserve enough information to answer:

- Was Trade Physics ready?
- Which primitive or component failed?
- Was the setup physically constrained by space?
- Was it temporally constrained?
- Was directional flow weak?
- Was movement stress high?
- What TPS and band were produced?
- Did the classical score and TPS disagree?
- Did a hard blocker override a high TPS?

Trade Physics truth MUST NOT live only in an opaque debug blob.

Schema evolution must be versioned under Event Schema governance.

---

## 17. PERFORMANCE ANALYTICS DATASET

The current analytics/research dataset must be able to retain, with setup/signal lineage:

- symbol;
- direction;
- timeframe/context;
- market regime;
- volatility regime;
- corridor regime;
- `available_space`;
- `required_space`;
- `space_to_buffer_ratio`;
- `trade_space_margin_atr`;
- `model_expiry`;
- `t_needed_adjusted`;
- `time_to_buffer_ratio`;
- `directional_effective_speed`;
- `weighted_gross_speed`;
- `flow_efficiency`;
- `atr_m5`;
- `movement_stress`;
- `S`, `T`, `P`, `V`;
- `TPS`;
- classical score and score components;
- DecisionObject result;
- FSM result;
- signal/execution result;
- telemetry truth;
- reconciled outcome truth;
- model/feature schema versions.

Truth layers MUST remain labeled.

---

## 18. LEARNED TRADE PHYSICS INTELLIGENCE

The AI Trade Physics intake document is current-scope as an intelligence/calibration subsystem.

### 18.1 Four-dimensional feature interpretation

The learned model may use four conceptual dimensions:

- Energy / movement stress;
- Space / reachability;
- Time / available-to-needed relation;
- Flow / directional alignment.

Canonical feature mappings for v1:

- `energy_stress_ratio = movement_stress`;
- `reachability_ratio = space_to_buffer_ratio`;
- `time_availability_ratio = time_to_buffer_ratio`;
- `flow_efficiency` plus other approved momentum/context features.

### 18.2 Learned output

The learned probability field is:

`trade_success_probability`

with range `[0,1]` when a validated model produces it.

It is not TPS.

### 18.3 Model family

The intake source recommends Gradient Boosted Trees such as LightGBM or XGBoost for tabular data.

This specification treats those as approved research candidates, not as a locked library dependency.

The trained model identity must include at minimum:

- model id;
- algorithm/family;
- training dataset version;
- feature schema version;
- training window;
- validation window;
- calibration method;
- quality metrics;
- approval/readiness state.

---

## 19. AI READINESS STATES

The learned subsystem is part of the current architecture even when no valid trained model exists.

It must expose explicit readiness rather than pretending success probability exists.

Canonical readiness states:

- `UNTRAINED`
- `INSUFFICIENT_DATA`
- `TRAINED_UNVALIDATED`
- `VALIDATED_RECOMMEND_ONLY`
- `APPROVED_FOR_BOUNDED_USE`
- `SUSPENDED_DRIFT`
- `INVALID_MODEL`

A state below validated readiness MUST NOT influence live decisions as probability authority.

This is current integration with evidence gating, not postponement to an undefined future upgrade.

---

## 20. SELF-LEARNING / CALIBRATION ARCHITECTURE

The current governed intelligence flow is:

`Decision / Trade Physics Evidence`
`-> Outcome / Telemetry Lineage`
`-> Performance Dataset`
`-> Research / Model Training`
`-> Calibration / Validation`
`-> Strategy Intelligence Recommendation`
`-> Autonomous Evolution Proposal`
`-> Owner/Admin Approval`
`-> Controlled Strategy Change if separately authorized`

AI MUST NOT silently mutate production strategy.

The integration must support:

- recommend-only;
- admin/owner approval;
- bounded use only when a separate active canonical contract defines bounds.

---

## 21. LEARNED SIGMOID SOURCE FORMULA

The intake AI document proposes conceptually:

`sigmoid(w1*(1/E) + w2*log(S) + w3*log(T) + w4*F)`

This formula is retained as source provenance and a candidate model structure, but it is NOT the deterministic TPS formula.

The source does not define validated weights or calibration evidence.

Therefore no fixed production `w1..w4` may be invented and presented as trained truth.

If this functional form is used, weights must be learned or otherwise governed through the Research/Learning and validation process and the resulting output is `trade_success_probability`.

---

## 22. PARAMETER GOVERNANCE

The following deterministic defaults are structural model constants in this active v1 contract:

- `S_cap = 3.0`
- `T_cap = 2.0`
- `P_cap = 2.0`
- `reference_minutes = 5`
- `wS = 0.35`
- `wT = 0.25`
- `wP = 0.20`
- `wV = 0.20`
- directional-speed lookback = 20 M1 intervals;
- linear recency weights `1..20`.

These values MUST NOT automatically become freely tunable merely because they are numeric.

Any runtime control surface for these values requires explicit `STRATEGY_PARAMETER_CONTROL_SPEC` authorization, bounds, audit logging, rollback and evidence requirements.

---

## 23. FORBIDDEN PATTERNS

The following are non-canonical:

- calculating primary strategic TPS inside Signal Engine after DecisionObject/FSM;
- two different values named TPS;
- treating deterministic TPS as calibrated probability without evidence;
- using `buffer_price` as primary canonical vocabulary;
- using generic `expiry_minutes` as the primary model-time source;
- using an inverse time ratio without explicit naming/orientation;
- silently substituting buffer/expiry required-speed normalization for ATR speed normalization;
- partial TPS averaging when a required component is missing;
- letting AI change live strategy without governed authority;
- training on unlabeled/mixed truth layers;
- leaking future outcome data into decision-time features;
- hiding model/version provenance;
- hardcoding a learned model claim without real training evidence.

---

## 24. REQUIRED CODE REALIGNMENT UNDER ACTIVE CANON

Code changes remain subject to canonical Governance, Test Plan, and Deployment Protocol controls.

The governed implementation audit must at minimum inspect and reconcile:

- `send/core/market_model.py` for directional/gross speed evidence;
- `send/core/sr_corridor_engine.py` for exact available-space contract;
- `send/core/time_model.py` for canonical time evidence consumption;
- `send/core/scoring_model.py` for primary TPS calculation;
- `send/core/decision_object.py` and decision assembly for Trade Physics contract;
- `send/core/signal_engine.py` to remove ownership of primary TPS math and retain downstream consumption only;
- `send/schema/event_schema.json` for versioned Trade Physics evidence;
- telemetry/outcome/analytics/intelligence modules;
- strategy parameter schema where authorized;
- tests and replay evidence.

Existing undocumented TPS runtime behavior is evidence of drift, not authority.

---

## 25. VALIDATION REQUIREMENTS

Required deterministic tests include:

1. hand-calculated source example reproduces expected TPS under canonical v1 formulas;
2. BUY and SELL directional speed symmetry;
3. recency weighting gives greater influence to newer aligned movement;
4. zero gross movement produces unavailable flow efficiency without division by zero;
5. invalid/zero ATR blocks normal TPS;
6. zero/missing buffer distance blocks normal TPS;
7. missing structural barrier produces explicit unavailable state;
8. `space_to_buffer_ratio < 1` cannot be overridden by high arithmetic components;
9. time ratio is reciprocal-consistent with active `model_time_reach_ratio` when synchronized;
10. deterministic TPS stays in `[0,100]`;
11. event/DecisionObject values preserve exact calculation lineage;
12. learned probability never overwrites TPS;
13. untrained/invalid AI states cannot influence live probability authority;
14. replay shows exactly which prior decisions would change when future TPS decision-policy influence is separately authorized.

---

## 26. CURRENT STATUS AND POST-ACTIVATION GOVERNANCE

Status now: ACTIVE CANONICAL under `CANONICAL_ACTIVATION_RECORD_20260901.md` and `CANONICAL_MASTER_INDEX_v2.0.0.md`.

The executed 2026-09-01 activation record confirms this document is active; the promoted graph resolved the following activation prerequisites:

- ALGO successor must define TPS current decision role;
- SR/Corridor successor must expose required structural inputs unambiguously;
- Time Model successor/reference update must formalize Trade Physics consumption without duplicate time authority;
- DecisionObject successor must carry Trade Physics evidence;
- observability/event schema and analytics/intelligence contracts must be reconciled;
- prior `CANON_BATCH_EVALUATION_v2.0.0` future-state classification must be superseded/amended;
- Root Stack and Master Index must be updated consistently;
- complete canonical audit must pass.

Canonical activation alone does not authorize runtime modification; code changes remain subject to Governance, Test Plan, Deployment Protocol, and canon-to-code audit controls.

---

## 27. FINAL PRINCIPLE

Trade Physics is a current Binary Strategy V2 capability.

Its deterministic truth is:

`STRUCTURAL SPACE + TIME FEASIBILITY + DIRECTIONAL SPEED + VOLATILITY REALISM -> TPS`

Its learned intelligence truth is:

`TRADE PHYSICS EVIDENCE + REAL OUTCOMES -> VALIDATED trade_success_probability -> GOVERNED RECOMMENDATION`

The two truths are related but MUST remain distinguishable.

Deterministic TPS is not learned probability.
Learned probability is not allowed to silently rewrite deterministic strategy truth.
