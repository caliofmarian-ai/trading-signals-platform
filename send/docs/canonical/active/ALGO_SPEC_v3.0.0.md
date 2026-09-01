# ALGO_SPEC_v3.0.0

Path: /opt/binarybot/docs/canonical/active/ALGO_SPEC_v3.0.0.md  
Version: 3.0.0  
Status: ACTIVE CANONICAL  
Owner: BinaryBot / DROPi Signals  
Scope: Strategic market model, corridor-first decision pipeline, classical scoring, current Trade Physics integration, DecisionObject production contract

Supersedes: `ALGO_SPEC_v2.0.0.md`

Governance basis:
- `GOVERNANCE_AND_CHANGE_CONTROL_v2.0.1.md`
- Owner decision 2026-09-01: complete Trade Physics integration is current-scope
- Change ID `20260901-TRADE-PHYSICS-01`
- merged governance PR #78

Linked documents:
- `canonical/superseded/CANONICAL_STRATEGY_STACK_v1.0.0.md`
- `canonical/superseded/TIME_MODEL_UNIFIED_CANON_v2.0.0.md`
- `canonical/superseded/SR_CORRIDOR_ENGINE_SPEC_v2.0.0.md`
- `canonical/active/TRADE_PHYSICS_MODEL_SPEC_v1.0.0.md`
- `canonical/superseded/DECISION_OBJECT_CANONICAL_SPEC_v1.0.0.md`
- `canonical/superseded/FSM_DECISION_ENGINE_SPEC_v1.0.0.md`
- `canonical/superseded/SIGNAL_ENGINE_EXECUTION_SPEC_v2.0.0.md`
- `canonical/superseded/OBSERVABILITY_SPEC_v2.0.0.md`

---

## 0. PROMOTION STATUS

This document is the active canonical successor to `ALGO_SPEC_v2.0.0.md`.

Promotion status: ACTIVE CANONICAL under `CANONICAL_ACTIVATION_RECORD_20260901.md` and `CANONICAL_MASTER_INDEX_v2.0.0.md`.

- `ALGO_SPEC_v2.0.0.md` is superseded and retained for historical provenance;
- this document does not authorize runtime changes;
- `TRADE_PHYSICS_MODEL_SPEC_v1.0.0.md` is active canonical under the executed 2026-09-01 promotion;
- PR #73 is historical and was closed without merge as superseded by the promoted canonical/runtime sequence.

---

## 1. PURPOSE

This document defines the canonical strategic model for Binary Strategy V2.

It governs:

- market-context derivation;
- structure-first interpretation;
- Time Model integration;
- classical score aggregation;
- mandatory current Trade Physics physical-feasibility evaluation;
- strategic gating before FSM;
- `DecisionObject` production;
- separation of strategy truth from FSM and Signal Engine truth.

Detailed Time Model mathematics remain owned by `TIME_MODEL_UNIFIED_CANON`.

Detailed SR/Corridor semantics remain owned by `SR_CORRIDOR_ENGINE_SPEC`.

Detailed Trade Physics mathematics are delegated to the active `TRADE_PHYSICS_MODEL_SPEC_v1.0.0`.

---

## 2. CORE ARCHITECTURAL PRINCIPLE

Binary Strategy V2 is:

- corridor-first;
- time-aware;
- scoring-driven;
- Trade-Physics-aware;
- DecisionObject-first relative to FSM.

The required order is:

1. Market Model
2. SR / Corridor Engine
3. Time Model
4. Scoring Model, including Trade Physics submodel
5. DecisionObject
6. FSM
7. Signal Engine

Trade Physics does not create a parallel path and does not bypass any stage.

---

## 3. OFFICIAL PIPELINE

```text
MARKET DATA
   ↓
MARKET MODEL
   ↓
SR / CORRIDOR ENGINE
   ↓
TIME MODEL
   ↓
SCORING MODEL
   ├── CLASSICAL STRATEGY SCORE
   └── TRADE PHYSICS / TPS
   ↓
DECISION OBJECT
   ↓
FSM DECISION
   ↓
SIGNAL ENGINE
```

Forbidden inversions include:

- Time Model before Corridor Engine;
- Trade Physics calculated primarily after DecisionObject/FSM;
- FSM before DecisionObject;
- direct strategy-to-signal emission;
- direct Signal Engine ownership of strategic TPS mathematics;
- use of generic `expiry_minutes` as sufficient model-time truth.

---

## 4. STRATEGIC RESPONSIBILITY

This specification is authoritative for:

- Market Model input/output semantics;
- context derivation;
- structure-first interpretation;
- placement and role of Trade Physics;
- classical score role;
- relationship between classical score and deterministic TPS;
- strategic hard-gating semantics;
- production of the strategic contract consumed by FSM.

It does not redefine:

- detailed SR barrier selection;
- detailed time mathematics;
- FSM state transitions;
- signal delivery;
- AI training methodology beyond the live-strategy authority boundary.

---

## 5. MARKET MODEL INPUTS

The Market Model consumes synchronized real market evidence.

Input families may include:

- M1 candle history;
- M5 candle history;
- latest price;
- support/resistance evidence;
- volatility evidence;
- trend evidence;
- momentum evidence;
- configured buffer mode;
- market noise/instability evidence.

No market value may be invented because another layer expects it.

---

## 6. MARKET CONTEXT DERIVATION

The Market Model must derive at minimum:

- `latest_price`;
- `direction_bias`;
- `trend_context`;
- `volatility_state`;
- `noise_context`;
- `atr_m5` or equivalent canonical ATR evidence;
- `buffer_distance`;
- gross `price_speed` context;
- sufficient close history or derived values for Trade Physics directional-speed evaluation.

For current Trade Physics integration, the strategic stack must additionally be able to produce:

- `directional_effective_speed`;
- `weighted_gross_speed`;
- `flow_efficiency`.

Their detailed formula is governed by `TRADE_PHYSICS_MODEL_SPEC_v1.0.0`.

---

## 7. SR / CORRIDOR FIRST PRINCIPLE

Before temporal or score conclusions, the strategy must establish the relevant directional structure.

The strategy requires the Corridor Engine to determine enough structural truth to answer:

- what is the relevant corridor?
- what is the nearest directional structural barrier?
- is structure valid?
- what is the available directional movement distance?
- is the setup compressed or constrained?

For Trade Physics, Corridor output must make `available_space` derivable without Signal Engine reconstructing support/resistance logic.

No valid current Trade Physics evaluation exists without structural evidence.

---

## 8. TIME MODEL INTEGRATION

After structure is established, the strategy consumes canonical Time Model concepts:

- `t_needed`;
- `t_needed_adjusted`;
- `model_expiry`;
- `model_time_reach_ratio`;
- `corridor_time_pressure`;
- `time_state`.

Trade Physics derives:

`time_to_buffer_ratio = model_expiry / t_needed_adjusted`

for positive synchronized values.

This is a Trade Physics reciprocal view over Time Model truth, not a competing time authority.

---

## 9. TIME-STRUCTURE INTERPRETATION

The canonical order remains:

**corridor first, time second, score third**.

A setup cannot be rescued by arithmetic scoring when:

- structure is invalid;
- required space does not fit;
- time is infeasible;
- required evidence is materially missing.

Trade Physics must preserve these blockers rather than average them away.

---

## 10. SCORING MODEL ROLE

The Scoring Model now has two complementary outputs:

1. **Classical Strategy Score**
2. **Deterministic Trade Physics Score (TPS)**

The Classical Strategy Score measures the current rule-based quality aggregation across trend, momentum, candle behavior, structure and time.

TPS measures physical feasibility across:

- structural space;
- available time;
- directional speed/flow;
- volatility/movement stress.

The two scores are distinct truths and MUST NOT be silently collapsed into one number.

---

## 11. CLASSICAL SCORE COMPONENT FAMILIES

The classical score must continue to preserve recognisable components covering:

- context/trend quality;
- momentum quality;
- candle/body expansion quality where used;
- structure/corridor quality;
- time-feasibility quality;
- penalties/blockers where required.

The current active implementation may use specific allocations such as trend/RSI/body/structure/time, but any future change to those allocations remains independently governed.

Trade Physics does not erase classical score provenance.

---

## 12. TRADE PHYSICS SUBMODEL

Trade Physics is current-scope and mandatory in the active strategic contract; implementation remains governed by the active change, test, and deployment controls.

Detailed formulas are governed by `TRADE_PHYSICS_MODEL_SPEC_v1.0.0`.

Required evidence includes at minimum:

- `available_space`;
- `required_space`;
- `space_to_buffer_ratio`;
- `trade_space_margin_atr`;
- `time_to_buffer_ratio`;
- `directional_effective_speed`;
- `flow_efficiency`;
- `directional_speed_ratio`;
- `movement_stress`;
- normalized components `S`, `T`, `P`, `V`;
- deterministic `TPS`;
- readiness and interpretation band.

---

## 13. DETERMINISTIC TPS ROLE

Deterministic TPS is a physical-feasibility companion score in `[0,100]`.

It is not automatically an empirical probability.

It does not replace `score_total`.

It does not create undocumented PRE/CONFIRM/OPEN_NOW thresholds.

Its current strategic role is:

- mandatory current physical-feasibility evidence;
- mandatory visibility in the strategic contract;
- contributor to explanation and analytics;
- reinforcement of hard structural/time truth;
- companion signal-quality context alongside classical score.

A future change that uses TPS-specific lifecycle thresholds or combines TPS numerically with classical score is a governed strategy change, not an implicit consequence of this integration.

---

## 14. HARD PHYSICAL FEASIBILITY RULES

Trade Physics cannot override hard upstream truth.

At minimum:

- if structure is invalid, the strategy is not eligible;
- if `available_space < required_space`, the setup is structurally constrained;
- if Time Model declares the setup infeasible, the setup is not eligible;
- if Market Model is unstable under canonical noise rules, the setup is blocked/degraded according to active strategy policy;
- if mandatory Trade Physics evidence is unavailable, the strategy must expose explicit unavailability rather than fabricate TPS.

A high TPS arithmetic result can never override a hard blocker that should have made TPS non-authoritative.

---

## 15. TRADE PHYSICS READINESS AS STRATEGIC EVIDENCE

The strategy must carry a recognized Trade Physics readiness state.

Canonical readiness families include:

- READY;
- unavailable due to structure;
- unavailable due to time;
- unavailable due to ATR/volatility evidence;
- unavailable due to speed evidence;
- blocked by unstable market;
- invalid evidence.

The exact enum belongs to the Trade Physics/DecisionObject contract successor set.

When readiness is not READY:

- TPS must not be fabricated;
- the DecisionObject must expose why;
- the strategy must not pretend full physical feasibility was evaluated.

---

## 16. SCORE DISAGREEMENT PRINCIPLE

Classical score and TPS may disagree.

Examples:

- high classical score + weak TPS;
- moderate classical score + strong TPS;
- strong TPS + hard structural blocker due inconsistent/missing evidence (invalid state that must be surfaced);
- strong classical score + poor directional flow.

The system must preserve disagreement rather than hide it in one opaque composite.

Analytics must later evaluate which disagreement patterns are predictive.

---

## 17. STRATEGIC GATING BEFORE DECISIONOBJECT

Before `DecisionObject`, the strategy must apply explicit gating for conditions such as:

- invalid market evidence;
- invalid structure;
- insufficient directional structural space;
- severe temporal infeasibility;
- unstable/noisy market state where canonically blocked;
- incomplete mandatory Trade Physics evidence;
- contradictions among context, structure, time and physical feasibility.

Reject/degrade semantics must remain explicit.

---

## 18. DECISIONOBJECT PRODUCTION CONTRACT

The official strategy output is `DecisionObject`.

It is produced:

- after Market Model;
- after Corridor;
- after Time Model;
- after classical score;
- after Trade Physics evaluation;
- before FSM.

It must preserve enough semantic evidence to reconstruct:

- context;
- structure;
- time;
- classical score;
- Trade Physics;
- blockers/degradation;
- strategy result.

---

## 19. REQUIRED DECISIONOBJECT SCORE SEMANTICS

The strategic contract must distinguish at minimum:

### Classical score

- `score_total`;
- normalized score;
- classical components;
- score tier;
- penalties/blockers where applicable.

### Trade Physics

- readiness;
- TPS;
- TPS band;
- primitive/normalized components;
- physical-feasibility explanation;
- provenance/version.

No field called TPS may contain learned probability.

---

## 20. RELATION TO FSM

FSM consumes the complete strategic truth.

FSM does not own:

- TPS formula;
- speed formula;
- structural-space derivation;
- learned probability training.

FSM may use strategic blockers/readiness as standardized inputs once their mapping is defined by the FSM/DecisionObject successor contracts.

---

## 21. RELATION TO SIGNAL ENGINE

Signal Engine is downstream of FSM.

It may:

- carry Trade Physics evidence into signal/observability payloads;
- correlate TPS with later delivery/outcome truth;
- expose already-produced TPS for diagnostics.

It MUST NOT:

- remain the primary calculator of strategic TPS;
- calculate a different TPS formula;
- repair missing strategy evidence ad hoc;
- overwrite DecisionObject Trade Physics truth.

Any runtime TPS calculation inside Signal Engine that remains primary strategic TPS ownership is implementation drift requiring governed remediation against the active canon.

---

## 22. LEARNED TRADE SUCCESS PROBABILITY

The current project also includes Trade Physics intelligence/calibration as a current-scope subsystem.

A learned result, when valid, is distinct from TPS:

- deterministic score: `TPS` in `[0,100]`;
- learned/calibrated result: `trade_success_probability` in `[0,1]`.

By default, learned output is advisory/recommendation evidence unless a separate active versioned strategy policy authorizes live decision influence.

The strategy must never interpret an untrained or unvalidated model as authoritative probability.

---

## 23. AI READINESS BOUNDARY

The strategic stack may receive learned probability only with explicit model readiness/provenance.

States below validation must not influence live decisions as probability truth.

The system must support current architecture even when the model is:

- untrained;
- data-insufficient;
- trained but unvalidated;
- suspended due to drift.

This is current integration with evidence discipline, not postponement of the subsystem.

---

## 24. OBSERVABILITY RELATION

The strategy must provide enough evidence for observability and Decision Audit to answer:

- why structure passed/failed;
- why time passed/failed;
- whether Trade Physics was ready;
- what TPS and components were produced;
- why TPS was unavailable;
- where classical score and TPS disagreed;
- whether learned probability existed and what readiness/model produced it;
- which truth actually influenced the current decision.

Trade Physics must not exist only as an optional debug field.

---

## 25. PERFORMANCE / RESEARCH RELATION

Trade Physics evidence must be retainable for outcome-linked analytics.

Required research questions include:

- which TPS bands correlate with real market outcomes?
- which components carry predictive information?
- does TPS add value beyond the classical score?
- which score/TPS disagreement patterns are useful?
- how does Trade Physics behave by symbol/session/regime?
- is `trade_success_probability` calibrated?
- is model drift present?

Analytics findings may recommend policy changes but may not silently alter strategy behavior.

---

## 26. PARAMETER GOVERNANCE

Trade Physics mathematical constants are not automatically ordinary runtime parameters.

Caps, weights, speed lookback and recency profile become controllable only if a successor `STRATEGY_PARAMETER_CONTROL_SPEC` explicitly authorizes:

- allowed ranges;
- actor permissions;
- persistence;
- proof logging;
- rollback;
- evidence requirements.

Until then, the promoted Trade Physics contract defines them structurally.

---

## 27. FORBIDDEN LEGACY / DRIFT PATTERNS

Forbidden as active canonical behavior:

- primary TPS math in Signal Engine;
- TPS derived from different formulas in different modules;
- learned probability stored under TPS;
- `buffer_price` as primary canonical field;
- generic `expiry_minutes` used instead of model time for TPS;
- required-speed-reference substitution when canonical TPS specifies ATR speed reference;
- missing component silently treated as zero unless the canon explicitly defines a blocker state;
- combining `score_total` and TPS with undocumented coefficients;
- AI live influence without model readiness and governance.

---

## 28. CODE ALIGNMENT RULE

Every implementation patch under this active canon must prove:

- Market Model produces required Trade Physics speed evidence;
- Corridor produces exact directional available-space evidence;
- Time Model remains sole owner of time math;
- Scoring Model calculates TPS before DecisionObject;
- DecisionObject carries Trade Physics truth;
- FSM consumes standardized strategy truth only;
- Signal Engine no longer owns strategic TPS calculation;
- event/observability schema reflects canonical fields;
- analytics/intelligence preserve lineage and truth-layer labels.

---

## 29. PATCH PRIORITIES DERIVED FROM THIS SUCCESSOR

Implementation order under this active successor should be:

1. Market Model directional/gross speed evidence;
2. Corridor available-space contract;
3. Time Model Trade Physics mapping verification;
4. Scoring Model TPS integration;
5. DecisionObject contract expansion;
6. Decision Audit / Event Schema / Observability expansion;
7. Signal Engine removal of duplicated strategic TPS ownership;
8. telemetry/outcome/analytics dataset alignment;
9. current-scope AI/calibration readiness pipeline;
10. replay and runtime validation.

No broker/distribution activation is implied.

---

## 30. FINAL PRINCIPLE

Binary Strategy V2 evaluates a setup using two complementary strategic views:

**Classical Strategy Quality**

and

**Trade Physics Physical Feasibility**.

The current governed chain is:

`MARKET -> STRUCTURE -> TIME -> CLASSICAL SCORE + TPS -> DECISIONOBJECT -> FSM -> SIGNAL ENGINE`

Trade Physics is part of the current strategy contract.

It is not a future-only upgrade, but it also does not justify invented thresholds, fabricated probability, or uncontrolled AI authority.
