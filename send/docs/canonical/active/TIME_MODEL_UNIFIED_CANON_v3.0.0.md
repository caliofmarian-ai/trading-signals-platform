# TIME_MODEL_UNIFIED_CANON_v3.0.0

Path: /opt/binarybot/docs/canonical/proposed/TIME_MODEL_UNIFIED_CANON_v3.0.0.md  
Version: 3.0.0  
Status: PROPOSED COMPLETE SUCCESSOR — NOT ACTIVE CANONICAL  
Owner: BinaryBot / DROPi Signals  
Scope: Unified Model Time, Execution Time, Telemetry Time, directional-speed time feasibility, Trade Physics time handoff, DecisionObject time contract

Supersession intent: `TIME_MODEL_UNIFIED_CANON_v2.0.0.md`
Governance basis: Change ID `20260901-TRADE-PHYSICS-01`; merged PR #78

Linked documents:
- `canonical/proposed/ALGO_SPEC_v3.0.0.md`
- `canonical/proposed/SR_CORRIDOR_ENGINE_SPEC_v3.0.0.md`
- `canonical/proposed/TRADE_PHYSICS_MODEL_SPEC_v1.0.0.md`
- `canonical/active/DECISION_OBJECT_CANONICAL_SPEC_v1.0.0.md` until successor promotion
- `canonical/active/FSM_DECISION_ENGINE_SPEC_v1.0.0.md` until successor promotion
- `canonical/active/TRADE_TEMPORAL_TELEMETRY_SPEC_v2.0.0.md`

---

## 0. PROMOTION STATUS

This document is a complete proposed successor. Until explicit promotion, `TIME_MODEL_UNIFIED_CANON_v2.0.0.md` remains the sole active time authority and no runtime change is authorized by this file.

---

## 1. PURPOSE

This document is the proposed unified authority for all BinaryBot time semantics after current Trade Physics integration.

It preserves three distinct layers:

1. Model Time
2. Execution Time
3. Telemetry Time

and adds one structural improvement required by the Trade Physics intake source:

**time-to-move estimation must use directional effective speed as the primary movement speed when evaluating an intended BUY or SELL setup.**

Gross absolute price speed remains useful market context, but it must not overstate reachability when most movement is opposite to the intended direction.

---

## 2. WHY V3 IS STRUCTURAL

The v2 time canon uses conceptual `price_speed` as the movement rate in `t_needed`.

The current runtime Market Model estimates that speed using average absolute close-to-close movement, regardless of direction.

The Trade Physics intelligence source explicitly identifies `directional_effective_speed` as a critical improvement and defines `t_needed` from that directional speed.

This changes the mathematical input contract of Model Time and is therefore a MAJOR structural successor, not a patch-level wording change.

---

## 3. ANCHOR ARCHITECTURE TRUTHS

The following remain locked:

- Corridor Engine is before Time Model.
- Time Model is before Scoring.
- DecisionObject is produced after Scoring and before FSM.
- Signal Engine does not recalculate Model Time.

Official strategic order:

`Market Model -> SR/Corridor -> Time Model -> Scoring/Trade Physics -> DecisionObject -> FSM -> Signal Engine`

Directional effective speed is derived from Market Model candle evidence under the Trade Physics mathematical contract and is consumed by Time Model. This does not insert a new top-level pipeline stage.

---

## 4. CANONICAL TIME LAYERS

### 4.1 Model Time

Internal strategic time feasibility. It describes how long the intended directional move needs and whether that move fits the model window.

### 4.2 Execution Time

Downstream trader/execution-facing expiry semantics derived from Model Time and post-strategy/FSM context.

### 4.3 Telemetry Time

Post-emission observation schedule used for objective market-path evidence, calibration and outcome analysis.

These three layers are related but never interchangeable.

---

## 5. OFFICIAL VOCABULARY

### 5.1 Movement / strategy-time inputs

- `buffer_distance`
- `price_speed` — gross/absolute movement-speed context
- `directional_effective_speed` — intended-direction recency-weighted movement speed
- `weighted_gross_speed`
- `flow_efficiency`
- `t_needed`
- `t_needed_adjusted`

### 5.2 Model Time

- `model_expiry`
- `model_time_reach_ratio`
- `corridor_time_pressure`
- `time_state`

### 5.3 Trade Physics time view

- `time_to_buffer_ratio`

### 5.4 Execution Time

- `confirm_expiry_min_minutes`
- `confirm_expiry_max_minutes`
- `open_now_expiry_minutes`

### 5.5 Telemetry Time

- `telemetry_checkpoints`
- `expected_expiry_ts`
- `checkpoint_ts`
- `post_expiry_checkpoints`

---

## 6. FORBIDDEN PRIMARY TERMS

The following remain non-canonical as unqualified primary model-time terms:

- `expiry`
- `expiry_minutes`
- `trade_expiry_minutes`
- `model_expiry_minutes`
- `t_needed_minutes`
- `t_needed_adjusted_minutes`
- `buffer_price`
- `t_needed_adj_min`

They may appear only in compatibility/migration mappings or where an explicitly external execution duration uses the `_minutes` suffix.

---

## 7. CANONICAL RELATION BETWEEN TIME METRICS

The proposed v3 Model Time chain is:

```text
real M1/M5 market evidence
        ↓
gross price_speed + directional_effective_speed
        ↓
SR / corridor structural truth
        ↓
buffer_distance
        ↓
t_needed = buffer_distance / directional_effective_speed
        ↓
t_needed_adjusted
        ↓
model_expiry
        ↓
model_time_reach_ratio = t_needed_adjusted / model_expiry
        ↓
time_to_buffer_ratio = model_expiry / t_needed_adjusted
        ↓
corridor_time_pressure
        ↓
time_state
        ↓
DecisionObject / FSM influence
        ↓
execution expiry derivation
        ↓
telemetry schedule
```

`model_time_reach_ratio` and `time_to_buffer_ratio` are reciprocal views of the same synchronized positive evidence and MUST NOT be confused.

---

## 8. BUFFER DISTANCE

`buffer_distance` is the canonical price distance relevant to setup validation / required movement.

It remains a strategy/market-derived input and the canonical term.

`buffer_price` is legacy compatibility vocabulary only.

Trade Physics v1 uses:

`required_space = buffer_distance`

but Time Model remains focused on movement time, not structural-space scoring.

---

## 9. GROSS PRICE SPEED

`price_speed` is retained as gross movement-rate context.

It may be derived from absolute price movement and is useful for:

- activity diagnostics;
- volatility/movement context;
- comparison to directional speed;
- flow-efficiency derivation;
- analytics.

It is no longer the preferred primary denominator speed for intended-direction `t_needed` in the proposed v3 model.

A high gross speed with low directional speed can indicate choppy or opposing movement and must not falsely imply fast reachability.

---

## 10. DIRECTIONAL EFFECTIVE SPEED

`directional_effective_speed` is the primary intended-direction movement-rate input for Model Time.

Its exact deterministic v1 derivation is governed by `TRADE_PHYSICS_MODEL_SPEC_v1.0.0`:

- most recent 20 completed M1 intervals;
- BUY counts positive close-to-close movement only;
- SELL counts negative-direction movement only;
- linear recency weights 1..20, newest highest;
- value expressed as price distance per minute.

The Time Model consumes this derived value; it does not independently choose different weights.

If the Trade Physics speed contract changes, Time Model must be version-audited because `t_needed` depends on it.

---

## 11. FLOW EFFICIENCY CONTEXT

`flow_efficiency = directional_effective_speed / weighted_gross_speed` when weighted gross speed is positive.

Time Model may use flow efficiency as explanatory/adjustment context only when the exact adjustment is canonically specified.

v3 does not invent an additional hidden flow multiplier inside `t_needed_adjusted`.

If flow efficiency is unavailable, the system must expose missing speed evidence rather than fabricate a value.

---

## 12. RAW TIME ESTIMATION

### 12.1 t_needed

For a directional BUY/SELL setup:

`t_needed = buffer_distance / directional_effective_speed`

when both values are finite and strictly positive.

This implements the critical directional-speed improvement from the Trade Physics intake source.

### 12.2 Zero or unavailable directional speed

If `directional_effective_speed <= 0` or unavailable:

- a finite favorable `t_needed` MUST NOT be fabricated;
- Model Time must expose an unavailable/infeasible speed condition;
- scoring and DecisionObject must receive that condition explicitly.

An implementation may internally represent the mathematical limit as infinity, but the external semantic contract must be explicit rather than rely on non-JSON-safe infinity.

### 12.3 Gross speed must not substitute silently

If directional speed is unavailable, gross `price_speed` may be recorded for diagnostics but MUST NOT silently substitute as the canonical `t_needed` denominator.

---

## 13. ADJUSTED TIME ESTIMATION

`t_needed_adjusted` is the context-adjusted time requirement derived from `t_needed`.

Allowed adjustment families may include those already established in the time/strategy canon:

- trend context;
- volatility context;
- structural/corridor context;
- feasibility modifiers;
- risk-aware bias.

Any exact multiplier that materially changes behavior must be explicitly defined and versioned.

No hidden Trade Physics multiplier may be inserted under the name `t_needed_adjusted`.

---

## 14. MODEL EXPIRY

`model_expiry` is the internal model horizon within which the opportunity is considered feasible.

It is used for:

- feasibility;
- scoring;
- corridor/time interaction;
- temporal gating;
- DecisionObject evidence;
- FSM interpretation;
- analytics.

It is not automatically the external trader expiry.

---

## 15. MODEL TIME REACH RATIO

Canonical formula:

`model_time_reach_ratio = t_needed_adjusted / model_expiry`

for finite positive values.

Interpretation:

- lower ratio => target/move is more comfortably reachable;
- ratio near 1 => marginal/tight reachability;
- ratio above the accepted feasibility boundary => insufficient model time.

The exact feasibility boundary and time-state mapping must remain canonically explicit in the implementation contract.

---

## 16. TRADE PHYSICS TIME-TO-BUFFER RATIO

Trade Physics needs the intuitive available-time / required-time orientation:

`time_to_buffer_ratio = model_expiry / t_needed_adjusted`

For synchronized positive values:

`time_to_buffer_ratio = 1 / model_time_reach_ratio`

Interpretation:

- `< 1` => not enough model time;
- `= 1` => marginal exact fit;
- `> 1` => positive time headroom.

Ownership rule:

- Time Model owns the underlying time values and ratio orientation definitions;
- Trade Physics consumes `time_to_buffer_ratio` to normalize its T component;
- no second expiry/t_needed calculation is allowed in Signal Engine.

---

## 17. CORRIDOR TIME PRESSURE

`corridor_time_pressure` expresses temporal criticality in relation to already-derived structure.

Inputs may include:

- `buffer_distance`;
- `directional_effective_speed`;
- optional gross `price_speed` context;
- `t_needed_adjusted`;
- `model_expiry`;
- `model_time_reach_ratio`;
- corridor geometry/width;
- boundary proximity/compression.

It may influence maturity, readiness and execution-expiry derivation.

Time Model does not reselect structural barriers.

---

## 18. TIME STATE

`time_state` is the discrete temporal state of the opportunity.

Recognized conceptual values remain:

- EARLY
- BUILDING
- READY
- CRITICAL
- LATE
- EXPIRED

An implementation may add an explicit unavailable/invalid state if needed to represent missing directional speed or invalid time evidence; if so, the enum must be synchronized with DecisionObject/Event Schema.

Time state influences strategy/FSM semantics but does not itself emit a signal.

---

## 19. STRUCTURAL FEASIBILITY PRECONDITION

Time Model consumes structural truth from Corridor Engine.

If structural truth is invalid or unavailable where required:

- Time Model must not invent a corridor;
- a normal ready temporal result must not disguise structural invalidity;
- downstream scoring must retain the upstream blocker.

The model may still calculate diagnostic time values where meaningful, but authoritative feasibility remains conditioned on valid structure.

---

## 20. EXECUTION TIME PRINCIPLE

Execution Time is downstream from Model Time.

The strategy first produces Model Time.

Only later does the decision/execution layer derive trader-facing duration semantics.

Trade Physics does not collapse Model Time into execution expiry.

---

## 21. CONFIRM EXECUTION TIME

CONFIRM may expose an execution duration interval:

- `confirm_expiry_min_minutes`
- `confirm_expiry_max_minutes`

The range is derived from Model Time under the execution-time contract.

The detailed derivation must be deterministic and governed; it is not equivalent to simply copying `model_expiry`.

---

## 22. OPEN_NOW EXECUTION TIME

OPEN_NOW may expose:

`open_now_expiry_minutes`

This value is derived downstream from Model Time and relevant execution/maturity context.

Fractional values are allowed where the model requires precision.

No arbitrary rounding is canonical.

---

## 23. EXECUTION CONSISTENCY RULE

When all three values exist:

`confirm_expiry_min_minutes <= open_now_expiry_minutes <= confirm_expiry_max_minutes`

Violation is an explicit time-contract inconsistency that must be observable.

---

## 24. TELEMETRY TIME MODEL

Telemetry Time defines post-emission observation checkpoints.

Typical checkpoints may include:

- midpoint;
- at-expiry;
- post-expiry +1m;
- post-expiry +3m;
- post-expiry +5m.

Telemetry supports:

- result observation;
- path analysis;
- expiry calibration;
- Trade Physics outcome correlation;
- separation of bad direction from bad timing;
- learned-model datasets.

Telemetry Time does not redefine the decision-time features.

---

## 25. RELATION BETWEEN TIME LAYERS

```text
MODEL TIME
  directional feasibility + pressure
        ↓
EXECUTION TIME
  trader/execution-facing duration
        ↓
TELEMETRY TIME
  objective observation schedule
```

The layers must remain labeled in analytics and datasets.

---

## 26. RELATION TO TRADE PHYSICS

Trade Physics consumes Time Model evidence; it does not own model-time calculation.

Required handoff includes:

- `t_needed`;
- `t_needed_adjusted`;
- `model_expiry`;
- `model_time_reach_ratio`;
- `time_to_buffer_ratio`;
- `corridor_time_pressure`;
- `time_state`;
- relevant speed provenance/version.

TPS T-component is derived from `time_to_buffer_ratio` under Trade Physics canon.

No TPS score may be calculated using legacy generic `expiry_minutes` as the primary model-time source after v3 promotion.

---

## 27. RELATION TO DECISIONOBJECT

DecisionObject must separate:

### Strategy movement metrics

- `buffer_distance`
- `price_speed` (gross context)
- `directional_effective_speed`
- `weighted_gross_speed`
- `flow_efficiency`
- `t_needed`
- `t_needed_adjusted`

### Model Time

- `model_expiry`
- `model_time_reach_ratio`
- `time_to_buffer_ratio`
- `corridor_time_pressure`
- `time_state`

### Execution Time

- `confirm_expiry_min_minutes`
- `confirm_expiry_max_minutes`
- `open_now_expiry_minutes`

### Telemetry Time

- telemetry checkpoint schedule/reference.

One ambiguous `expiry` field cannot represent all layers.

---

## 28. RELATION TO FSM

FSM consumes standardized DecisionObject/post-strategy time truth.

FSM must not:

- recompute directional speed;
- recalculate `t_needed` from candles;
- redefine model expiry;
- invert ratios ad hoc;
- repair missing Time Model evidence.

FSM may interpret readiness/maturity according to its own canonical state contract.

---

## 29. RELATION TO SIGNAL ENGINE

Signal Engine does not recalculate Model Time or Trade Physics time ratios.

It consumes already-established post-strategy/FSM semantics and may carry time evidence into downstream payload/observability.

The current legacy/undocumented TPS extraction path that derives time ratio from generic `expiry_minutes` must be removed or converted to compatibility-only behavior after canonical implementation.

---

## 30. OBSERVABILITY REQUIREMENT

The system must be able to log distinctly:

- gross `price_speed`;
- `directional_effective_speed`;
- speed derivation version/provenance;
- `buffer_distance`;
- `t_needed`;
- `t_needed_adjusted`;
- `model_expiry`;
- `model_time_reach_ratio`;
- `time_to_buffer_ratio`;
- `corridor_time_pressure`;
- `time_state`;
- execution expiry fields;
- telemetry schedule/reference.

Missing/invalid directional speed must be visible.

---

## 31. LEGACY TERM / FORMULA MAPPING

Vocabulary mapping:

- `buffer_price` -> `buffer_distance`
- `t_needed_minutes` -> `t_needed`
- `t_needed_adj_min` / `t_needed_adjusted_minutes` -> `t_needed_adjusted`
- `model_expiry_minutes` -> `model_expiry`

Formula migration:

- old conceptual `t_needed = buffer_distance / gross price_speed`
- proposed v3 `t_needed = buffer_distance / directional_effective_speed`

Gross speed remains observable context; it is not silently discarded.

---

## 32. DATA VALIDITY AND SYNCHRONIZATION

Time inputs must describe the same:

- symbol;
- direction;
- evaluation/candle timestamp;
- strategy cycle;
- market/corridor evidence generation.

Mismatched evidence must fail closed/unavailable rather than produce a blended ratio.

All denominators must be finite and positive.

---

## 33. FORBIDDEN TIME PATTERNS

Forbidden:

- Time Model before Corridor;
- gross absolute speed silently standing in for directional speed after v3 promotion;
- Signal Engine recalculating authoritative time ratios;
- `expiry_minutes` used as model expiry without explicit compatibility mapping;
- ratio orientation left unlabeled;
- missing directional speed replaced by arbitrary minimum speed;
- negative/zero denominator coerced into plausible finite time;
- execution expiry used as training feature if it was produced after the decision point and would cause leakage for the target being modeled;
- learned-model output modifying Model Time without separate canonical authorization.

---

## 34. IMPLEMENTATION RULE

After promotion, implementation must:

1. derive deterministic directional speed from real M1 candles using the promoted formula;
2. keep gross speed as separate context;
3. use directional speed in `t_needed`;
4. preserve existing adjustment/model-expiry semantics unless separately changed;
5. expose reciprocal `time_to_buffer_ratio` consistently;
6. transport all time truth through DecisionObject;
7. remove duplicated downstream calculation;
8. add exact tests and replay evidence.

---

## 35. VALIDATION REQUIREMENTS

At minimum:

1. BUY time uses only positive-direction weighted movement;
2. SELL time uses only sell-direction weighted movement;
3. opposing high gross volatility cannot falsely produce a fast directional t_needed;
4. zero directional speed yields explicit unavailable/infeasible semantics;
5. `t_needed = buffer_distance / directional_effective_speed` exactly;
6. reciprocal consistency: `time_to_buffer_ratio * model_time_reach_ratio = 1` within numeric tolerance for synchronized positive values;
7. structural invalidity remains visible;
8. DecisionObject transports exact time evidence;
9. Signal Engine does not recompute it;
10. execution expiry remains distinct from model expiry;
11. replay quantifies behavior changes versus gross-speed v2.

---

## 36. FINAL PRINCIPLE

The BinaryBot Time Model remains one unified, layered time authority.

Trade Physics strengthens it by making movement-time feasibility directional:

**the relevant question is not how much the price moves in total, but how efficiently it is moving toward the intended trade direction.**

The canonical proposed chain is:

`buffer_distance / directional_effective_speed -> t_needed -> adjusted time -> model_expiry -> reachability -> Trade Physics time ratio -> time state`.

Execution Time and Telemetry Time remain downstream and separate.
