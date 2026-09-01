# SR_CORRIDOR_ENGINE_SPEC_v3.0.0

Path: /opt/binarybot/docs/canonical/active/SR_CORRIDOR_ENGINE_SPEC_v3.0.0.md  
Version: 3.0.0  
Status: ACTIVE CANONICAL  
Owner: BinaryBot / DROPi Signals  
Scope: Support/resistance, corridor interpretation, directional structural-space truth, Trade Physics structural handoff, pre-Time-Model feasibility

Supersedes: `SR_CORRIDOR_ENGINE_SPEC_v2.0.0.md`
Governance basis: Change ID `20260901-TRADE-PHYSICS-01`; merged PR #78

Linked documents:
- `canonical/active/ALGO_SPEC_v3.0.0.md`
- `canonical/active/TRADE_PHYSICS_MODEL_SPEC_v1.0.0.md`
- `canonical/superseded/TIME_MODEL_UNIFIED_CANON_v2.0.0.md`
- `canonical/superseded/DECISION_OBJECT_CANONICAL_SPEC_v1.0.0.md`
- `canonical/superseded/OBSERVABILITY_SPEC_v2.0.0.md`

---

## 0. PROMOTION STATUS

Promotion status: ACTIVE CANONICAL under `CANONICAL_ACTIVATION_RECORD_20260901.md` and `CANONICAL_MASTER_INDEX_v2.0.0.md`.

---

## 1. PURPOSE

SR / Corridor Engine is the canonical owner of structural market truth used by Binary Strategy V2.

It must:

- identify relevant support and resistance;
- define the active operational corridor;
- establish directional structural barriers;
- derive directional available space;
- classify structural feasibility, compression and conflict;
- supply explicit structural evidence to Time Model, Scoring, Trade Physics and DecisionObject.

It does not calculate TPS, model expiry, FSM state or signal delivery.

---

## 2. CORE PRINCIPLE

The locked order remains:

1. Market Model
2. SR / Corridor Engine
3. Time Model
4. Scoring Model including Trade Physics
5. DecisionObject
6. FSM
7. Signal Engine

Structure exists before time. `DecisionObject` exists before FSM.

No downstream layer may silently recreate SR truth from raw prices when the Corridor Engine should have supplied it.

---

## 3. RESPONSIBILITIES

The Corridor Engine owns four fundamental responsibilities:

1. structural identification;
2. corridor definition;
3. directional structural-space measurement;
4. semantic structural handoff.

The v3 structural contract makes directional space explicit because current Trade Physics requires a stable, auditable `available_space` input.

---

## 4. WHAT THIS LAYER IS NOT

It is not:

- Time Model;
- scoring engine;
- Trade Physics score calculator;
- DecisionObject assembler;
- FSM;
- Signal Engine;
- a visual-only line detector;
- an informal list of levels without semantic ownership.

It must not choose execution expiry or publish signals.

---

## 5. REQUIRED INPUT FAMILIES

The layer consumes synchronized real market evidence sufficient to interpret at minimum:

- current/evaluation price;
- intended setup direction;
- relevant support levels/zones;
- relevant resistance levels/zones;
- bands/ranges/corridor context;
- market structure landmarks;
- proximity context;
- current symbol, timeframe/candle identity and evaluation timestamp.

Inputs must refer to the same evaluation context as the Market Model result.

Missing structural evidence must be reported as unavailable; levels must never be invented.

---

## 6. CORRIDOR DEFINITION

A corridor is an operational structural region bounded by relevant SR landmarks in which setup feasibility is interpreted.

It is not merely a geometric shape. It provides:

- contextual localization;
- movement-space boundaries;
- compression/congestion interpretation;
- directional feasibility context;
- inputs to Time Model and Trade Physics.

The active corridor must be identified explicitly enough to reconstruct which structural boundaries were used.

---

## 7. REQUIRED CORRIDOR QUESTIONS

The engine must answer, for each evaluated setup:

- which corridor is active?
- what are its relevant lower and upper boundaries?
- where is current price within or relative to the corridor?
- which boundary is favorable/downstream in the intended direction?
- which boundary is adverse/opposing?
- what is the nearest relevant directional barrier?
- how much usable space exists before that barrier?
- is the corridor compressed?
- does structure conflict with the intended direction?
- is the setup structurally valid, constrained, degraded, conflicted or invalid?

---

## 8. DIRECTIONAL BARRIER CONTRACT

Trade Physics requires one exact directional structural barrier per evaluation when such a barrier can be established.

### 8.1 BUY

For BUY, the primary directional limiting barrier is the nearest relevant resistance / upper structural boundary above current price that the Corridor Engine deems structurally applicable.

### 8.2 SELL

For SELL, the primary directional limiting barrier is the nearest relevant support / lower structural boundary below current price that the Corridor Engine deems structurally applicable.

### 8.3 Selection rule

The engine must not blindly choose the numerically closest level if the level is not structurally relevant under corridor rules.

Barrier selection must preserve:

- direction;
- corridor membership/context;
- structural relevance;
- current price ordering;
- stable explanation/provenance.

If no valid directional barrier can be established, the engine must emit an explicit unavailable/invalid structural state rather than an infinite or fabricated distance.

---

## 9. AVAILABLE SPACE

### 9.1 Definition

`available_space` is the non-negative price distance from the evaluation price to the chosen directional limiting barrier.

For BUY:

`available_space = directional_resistance - current_price`

For SELL:

`available_space = current_price - directional_support`

The value is valid only when the chosen barrier is correctly ordered relative to price and is structurally relevant.

### 9.2 Units

`available_space` uses the same price-distance units as `buffer_distance` and ATR for the symbol.

### 9.3 Ownership

Corridor Engine owns `available_space` because it owns barrier selection.

Trade Physics may consume but must not reconstruct the barrier.

Signal Engine/FSM must not recompute it from raw SR arrays.

---

## 10. REQUIRED SPACE VS AVAILABLE SPACE

`required_space` is not owned by Corridor Engine.

For Trade Physics v1, `required_space = buffer_distance` is governed by Trade Physics / strategy canon.

Corridor Engine may receive `buffer_distance` downstream-compatible context to classify whether the available space is sufficient, but it must not redefine how buffer distance is calculated.

The structural comparison is:

- `available_space < required_space` => structurally constrained;
- `available_space == required_space` => marginal fit;
- `available_space > required_space` => sufficient raw directional space, subject to other structural conditions.

---

## 11. STRUCTURAL ROOM / CORRIDOR METRICS

The engine may expose additional metrics such as:

- corridor width;
- normalized position inside corridor;
- distance to lower/upper boundary;
- boundary proximity;
- room ratio;
- compression ratio/state;
- structural confidence;
- conflict flags.

These may support classical structure scoring and diagnostics.

They must remain distinguishable from Trade Physics `space_to_buffer_ratio`, whose formula belongs to the Trade Physics scoring submodel.

---

## 12. STRUCTURAL FEASIBILITY

Structural feasibility must be evaluated before complete temporal interpretation.

At minimum, a setup must not be declared structurally valid if:

- corridor itself is invalid;
- intended-direction barrier ordering is impossible/inconsistent;
- `available_space` cannot be established when required;
- available space is less than required space for current Trade Physics v1;
- structure is materially conflicted or hostile under the corridor rules.

Time cannot fully compensate for absent structural room.

---

## 13. STRUCTURAL OUTCOME FAMILIES

The canonical semantics must support at least:

- `VALID` / structurally valid;
- `CONSTRAINED`;
- `DEGRADED`;
- `CONFLICTED`;
- `INVALID`;
- `UNAVAILABLE` where evidence cannot establish structural truth.

Exact runtime enum names must be fixed consistently in the contract implementation, DecisionObject and event schema.

No normal valid state may be used merely to avoid exposing missing evidence.

---

## 14. BOUNDARY PROXIMITY AND COMPRESSION

Boundary proximity and compression are strategic evidence.

The layer must be able to describe:

- near favorable boundary;
- near opposing boundary;
- too constrained for healthy movement;
- centered/free structural position;
- compressed corridor;
- structurally open corridor.

This evidence must be explicit enough for decision explanation and analytics.

---

## 15. STRUCTURAL CONFLICT

Examples of conflict include:

- BUY setup immediately facing relevant resistance;
- SELL setup immediately facing relevant support;
- available space below required movement;
- compressed corridor inconsistent with intended move;
- selected barrier on the wrong side of price;
- inconsistent or stale structural context.

Conflicts must be preserved downstream as semantic evidence, not hidden in a low numeric score.

---

## 16. RELATION TO TIME MODEL

Time Model consumes already-derived structural truth.

The handoff must include sufficient information for time feasibility and pressure interpretation, including where relevant:

- corridor identity/width;
- structural feasibility;
- available directional space;
- boundary proximity;
- compression/conflict state.

Time Model must not define the corridor or reselect the barrier.

---

## 17. RELATION TO CLASSICAL SCORING

Classical scoring consumes structural quality and blocker semantics.

A strong arithmetic structure component cannot make an invalid corridor valid.

Classical structure score and Trade Physics space component are related but distinct:

- classical structure score summarizes structural quality;
- Trade Physics space component measures available directional room relative to required movement.

Both must retain provenance to avoid hidden double counting.

---

## 18. RELATION TO TRADE PHYSICS

Corridor Engine provides structural primitives only.

It provides:

- directional barrier identity/value;
- `available_space`;
- corridor/structural outcome;
- proximity/compression/conflict evidence.

Trade Physics owns derivation of:

- `required_space` from canonical buffer distance for v1;
- `space_to_buffer_ratio`;
- `trade_space_margin_atr`;
- normalized S component;
- deterministic TPS.

This boundary prevents duplicated formulas across modules.

---

## 19. RELATION TO DECISIONOBJECT

DecisionObject must receive stable structural evidence including at minimum:

- corridor summary/identity;
- lower/upper boundaries where available;
- chosen directional barrier;
- `available_space`;
- structural position;
- boundary proximity;
- feasibility state;
- compression/conflict flags;
- structural explanation/provenance.

Trade Physics evidence derived later in scoring must reference this structural source rather than copy a contradictory value.

---

## 20. EXPLANATION REQUIREMENT

The structural layer must produce human/audit-readable explanation semantics.

Examples:

- `BUY resistance at X leaves Y available space`;
- `SELL support at X leaves Y available space`;
- `available space below required buffer distance`;
- `corridor compressed`;
- `no valid directional barrier available`;
- `healthy structural room`.

Exact user-facing wording may be formatted downstream, but semantic reason codes and values must be preserved.

---

## 21. OBSERVABILITY REQUIREMENT

Observability must be able to reconstruct:

- which corridor was chosen;
- which barriers were considered/selected where required;
- the selected directional barrier;
- `available_space`;
- structural outcome;
- compression/conflict state;
- how structural truth affected Time Model, classical scoring and Trade Physics;
- why a setup was rejected/degraded structurally.

Structural truth must not remain a black box.

---

## 22. DATA VALIDITY AND LINEAGE

Every structural result used by Trade Physics must be attributable to:

- symbol;
- evaluation/candle timestamp;
- direction;
- source candle/context version where applicable;
- corridor/result schema version.

A Trade Physics evaluation must reject mismatched structural identity rather than combine evidence from different cycles.

---

## 23. FORBIDDEN STRUCTURAL PATTERNS

Forbidden:

- Time Model defining the corridor;
- Scoring/Trade Physics selecting its own competing SR barrier;
- Signal Engine deriving `available_space` from raw levels;
- FSM rederiving structure;
- infinite/huge synthetic available space when a barrier is missing;
- using stale/mismatched structure as current truth;
- treating `available_space < required_space` as healthy structure;
- hiding structural blocker semantics inside arithmetic score only.

---

## 24. CODE ALIGNMENT RULE

After promotion, code must answer clearly:

- where the active corridor is derived;
- how the directional barrier is selected;
- where `available_space` is calculated;
- how the value reaches Time Model and Scoring;
- how Trade Physics consumes it;
- how DecisionObject carries it;
- how observability proves it;
- how duplicated Signal Engine/FSM derivation is prevented.

---

## 25. VALIDATION REQUIREMENTS

At minimum test:

1. BUY selects a valid resistance above price;
2. SELL selects a valid support below price;
3. wrong-side barriers are rejected;
4. no valid barrier produces explicit unavailable state;
5. available-space arithmetic is exact;
6. units align with buffer distance and ATR;
7. constrained-space state when available < required;
8. same symbol/timestamp/direction identity is enforced;
9. compressed/conflicted structure cannot be silently marked valid;
10. downstream Time/Scoring/DecisionObject receive the same structural value.

---

## 26. FINAL PRINCIPLE

SR / Corridor Engine is the sole owner of directional structural-space truth.

For current Trade Physics integration it must answer one decisive question before time and scoring:

**How much real structural room exists in the intended direction before the nearest relevant barrier?**

That answer is exported as governed structural evidence. Trade Physics uses it; it does not reinvent it.
