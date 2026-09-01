# DECISION_OBJECT_CANONICAL_SPEC_v2.0.0

Path: /opt/binarybot/docs/canonical/active/DECISION_OBJECT_CANONICAL_SPEC_v2.0.0.md  
Version: 2.0.0  
Status: ACTIVE CANONICAL  
Owner: BinaryBot / DROPi Signals  
Scope: Official strategic output contract between strategy/scoring and FSM, including complete current Trade Physics evidence

Supersession intent: `DECISION_OBJECT_CANONICAL_SPEC_v1.0.0.md`
Governance basis: Change ID `20260901-TRADE-PHYSICS-01`; merged PR #78

Linked proposed/current documents:
- `canonical/active/ALGO_SPEC_v3.0.0.md`
- `canonical/active/SR_CORRIDOR_ENGINE_SPEC_v3.0.0.md`
- `canonical/active/TIME_MODEL_UNIFIED_CANON_v3.0.0.md`
- `canonical/active/TRADE_PHYSICS_MODEL_SPEC_v1.0.0.md`
- `canonical/superseded/FSM_DECISION_ENGINE_SPEC_v1.0.0.md` until successor promotion
- `canonical/superseded/OBSERVABILITY_SPEC_v2.0.0.md` until successor promotion
- `canonical/superseded/DECISION_AUDIT_SPEC_v2.0.0.md` until successor promotion

---

## 0. PROMOTION STATUS

Promotion status: ACTIVE CANONICAL under `CANONICAL_ACTIVATION_RECORD_20260901.md` and `CANONICAL_MASTER_INDEX_v2.0.0.md`.

---

## 1. PURPOSE

`DecisionObject` is the standardized strategic truth produced after Market, Corridor, Time, classical scoring and Trade Physics evaluation, but before FSM.

It exists to separate:

- strategic mathematics;
- structural/time/Trade Physics evidence;
- operational FSM interpretation;
- Signal Engine execution semantics.

The v2 contract adds Trade Physics as a first-class strategic domain rather than an optional downstream debug field.

---

## 2. CORE PRINCIPLE

Official order:

1. Market Model
2. SR / Corridor Engine
3. Time Model
4. Classical Scoring + Trade Physics
5. `DecisionObject`
6. FSM
7. Signal Engine

Therefore:

- strategy/scoring produces Trade Physics truth;
- DecisionObject transports it;
- FSM interprets standardized evidence;
- Signal Engine does not recalculate TPS.

---

## 3. ROLE OF DECISIONOBJECT

DecisionObject has four fundamental roles:

1. **strategic standardization** — convert the complete strategic evaluation into one stable contract;
2. **FSM interface** — give FSM enough semantic truth without raw-candle rederivation;
3. **audit foundation** — make each decision reconstructable;
4. **truth-layer boundary** — separate deterministic strategy truth from learned/advisory intelligence and downstream execution truth.

---

## 4. WHAT DECISIONOBJECT IS NOT

It is not:

- final execution verdict;
- FSM state itself;
- Telegram payload;
- broker order;
- only a score;
- only TPS;
- only expiry;
- an opaque legacy dict;
- an AI prediction container without deterministic evidence.

---

## 5. REQUIRED TOP-LEVEL SEMANTIC DOMAINS

A canonical v2 DecisionObject must make the following domains recognizable:

```text
DecisionObject
├── setup
├── market_context
├── structure
├── time
├── score
│   ├── classical
│   └── trade_physics
├── strategic_flags
├── reject_semantics
├── fsm_inputs
├── observability
├── intelligence_context (optional/advisory)
└── metadata
```

Internal implementation shape may vary only if these semantic domains remain unambiguous and schema-versioned.

---

## 6. SETUP DOMAIN

Must identify the evaluation unambiguously.

Required families:

- symbol;
- direction;
- evaluation timestamp / candle timestamp;
- timeframe/context;
- cycle/run identifier;
- opportunity/setup identity where available;
- source/strategy version.

All downstream domains must refer to this same setup identity.

---

## 7. MARKET CONTEXT DOMAIN

Must expose enough market truth used by the strategy, including as applicable:

- latest price;
- trend context;
- volatility state;
- noise state;
- ATR evidence;
- `buffer_distance`;
- gross `price_speed`;
- `directional_effective_speed`;
- `weighted_gross_speed`;
- `flow_efficiency`;
- target-distance context.

The market domain carries evidence; it does not contain final FSM semantics.

---

## 8. STRUCTURE DOMAIN

Must expose at minimum:

- corridor identity/summary;
- relevant lower/upper boundaries where available;
- chosen directional barrier;
- directional barrier type/reference;
- `available_space`;
- structural position;
- boundary proximity;
- compression/pressure state;
- feasibility state;
- conflict flags;
- structural explanation/provenance.

Trade Physics `available_space` must be traceable to this structural domain.

---

## 9. TIME DOMAIN

Must use the unified v3 time vocabulary once promoted:

- `buffer_distance` reference;
- `directional_effective_speed` reference;
- `t_needed`;
- `t_needed_adjusted`;
- `model_expiry`;
- `model_time_reach_ratio`;
- `time_to_buffer_ratio`;
- `corridor_time_pressure`;
- `time_state`;
- time evidence readiness/invalidity where applicable.

Execution-time fields remain separate from model time.

No generic `expiry_minutes` may represent the entire time domain.

---

## 10. SCORE DOMAIN

Score must distinguish two complementary strategic truths.

### 10.1 Classical score

Must support:

- `score_total`;
- normalized score;
- component map;
- penalties;
- score tier;
- score explanation;
- eligibility/blocker relation.

### 10.2 Trade Physics score

Must be a recognized nested domain rather than an opaque debug attachment.

Required fields when the model is READY:

- readiness state;
- `available_space` reference;
- `required_space`;
- `space_to_buffer_ratio`;
- `trade_space_margin_atr`;
- `time_to_buffer_ratio`;
- `directional_effective_speed` reference;
- `weighted_gross_speed` reference;
- `flow_efficiency`;
- `atr_speed_reference`;
- `directional_speed_ratio`;
- `movement_stress`;
- normalized `S`;
- normalized `T`;
- normalized `P`;
- normalized `V`;
- deterministic `TPS` in `[0,100]`;
- TPS interpretation band;
- Trade Physics schema/model version;
- explanation/provenance.

When not READY, the domain must expose readiness and reason without fabricating a normal TPS.

---

## 11. TRADE PHYSICS READINESS CONTRACT

DecisionObject must distinguish physical-feasibility readiness from arithmetic score existence.

Proposed readiness families:

- `READY`;
- `UNAVAILABLE_MISSING_STRUCTURE`;
- `UNAVAILABLE_MISSING_TIME`;
- `UNAVAILABLE_MISSING_ATR`;
- `UNAVAILABLE_MISSING_SPEED`;
- `BLOCKED_UNSTABLE_MARKET`;
- `INVALID_EVIDENCE`.

Final enum names must be synchronized across Trade Physics model, DecisionObject implementation, Decision Audit and Event Schema before promotion.

No downstream layer may treat a non-READY object as if TPS were valid merely because a legacy field exists.

---

## 12. SCORE DISAGREEMENT CONTRACT

DecisionObject must preserve classical-score/TPS disagreement.

It may expose a categorical explanation such as:

- `ALIGNED_STRONG`;
- `ALIGNED_WEAK`;
- `CLASSICAL_STRONG_TPS_WEAK`;
- `CLASSICAL_WEAK_TPS_STRONG`;
- `TPS_UNAVAILABLE`.

These labels are optional until separately standardized; the mandatory requirement is that both underlying scores and explanations remain distinct and reconstructable.

The contract MUST NOT replace them with an undocumented composite score.

---

## 13. STRATEGIC FLAGS DOMAIN

Must express relevant strategic booleans/categories, for example:

- valid structure;
- sufficient structural space;
- feasible time;
- Trade Physics ready;
- physically constrained;
- unstable market;
- degraded setup;
- low confidence;
- rejectable;
- borderline;
- learned probability available/validated where applicable.

Flags summarize; they do not replace source evidence.

---

## 14. REJECT SEMANTICS DOMAIN

DecisionObject must explicitly express rejection/degradation semantics.

Required families may include:

- reject reason;
- reject category;
- reject stage;
- degradation reason;
- hard blockers;
- soft blockers;
- missing-evidence reason.

Trade Physics-related examples include:

- insufficient structural space;
- missing directional barrier;
- invalid ATR;
- missing directional speed;
- time infeasible;
- unstable market.

A high numeric score cannot erase a hard blocker.

---

## 15. FSM INPUT READINESS

DecisionObject must give FSM standardized inputs sufficient to distinguish:

- accepted strategy setup;
- wait/build state;
- degraded setup;
- rejected setup;
- missing/incomplete evidence;
- hard physical infeasibility.

FSM must not parse raw candles or recalculate Trade Physics.

Which Trade Physics fields directly affect an FSM transition must be explicitly defined in the FSM successor/policy; mere field presence is not permission for new hidden FSM thresholds.

---

## 16. OBSERVABILITY DOMAIN

DecisionObject must be able to supply audit/observability with:

- setup correlation;
- structural explanation;
- time explanation;
- classical score explanation;
- Trade Physics primitives/components/TPS;
- Trade Physics readiness/reason;
- blocker/degrade reasons;
- model/feature/version identifiers;
- learned probability provenance if present;
- indication of which evidence actually influenced the decision.

No critical Trade Physics truth may exist only in an unstructured `debug` map.

---

## 17. INTELLIGENCE CONTEXT DOMAIN

Learned Trade Physics intelligence is distinct from deterministic strategy truth.

If available, an optional `intelligence_context` may include:

- `trade_success_probability`;
- model id/version;
- feature schema version;
- training/validation reference;
- readiness state;
- calibration state;
- confidence/quality metadata;
- authority mode such as recommend-only / bounded-use if canonically approved.

The learned probability MUST NOT be stored in the deterministic `TPS` field.

If model readiness is insufficient, DecisionObject may record readiness but must not fabricate probability.

---

## 18. AI AUTHORITY BOUNDARY

DecisionObject may carry validated learned evidence, but it does not grant that evidence authority.

Live decision influence is allowed only when active strategy/intelligence/governance canon explicitly authorizes it.

By default during current integration:

- deterministic TPS is current strategy evidence;
- learned `trade_success_probability` is advisory unless a separately promoted decision policy says otherwise.

---

## 19. EXECUTION TIME DOMAIN

Where execution-time semantics are included, they must be distinct:

- confirm minimum expiry;
- confirm maximum expiry;
- open-now exact expiry.

They are downstream derivatives of Model Time and must not be used to overwrite historical decision-time Trade Physics inputs.

---

## 20. METADATA DOMAIN

Must support:

- DecisionObject schema version;
- producer module;
- strategy version;
- canonical spec version;
- Trade Physics model/spec version;
- Market/Corridor/Time/Scoring schema versions;
- compatibility/migration markers;
- audit correlation IDs;
- cycle identifiers.

This metadata is necessary for replay and model-dataset lineage.

---

## 21. REQUIRED CANONICAL TRUTHS

This v2 proposal locks the following if promoted:

1. DecisionObject remains before FSM.
2. It is the official strategy output.
3. Corridor remains before Time.
4. Classical score and deterministic TPS are distinct score truths.
5. Trade Physics is calculated before DecisionObject.
6. Trade Physics readiness is explicit.
7. Deterministic TPS is `[0,100]` and is not learned probability.
8. Learned probability, if present, has separate identity/provenance/readiness.
9. Reject/degrade semantics are explicit.
10. Signal Engine must not reconstruct strategic TPS.

---

## 22. FORBIDDEN CONTRACT PATTERNS

Forbidden:

- legacy dict without semantic schema;
- strategy output reduced to score + expiry;
- TPS stored only inside debug;
- two meanings under `TPS`;
- missing structure/time/Trade Physics domain;
- learned probability without model identity;
- non-READY Trade Physics represented by a plausible numeric TPS;
- composite score hiding classical/TPS disagreement;
- FSM rederiving strategy math;
- Signal Engine overwriting DecisionObject TPS;
- generic expiry used as total time truth.

---

## 23. RELATION TO FSM

FSM consumes DecisionObject; it does not replace it.

FSM may:

- interpret strategy readiness;
- classify operational state;
- wait/degrade/reject/confirm/open according to its own active contract;
- emit explanation.

FSM may not:

- calculate directional speed;
- choose structural barriers;
- calculate TPS;
- train/calibrate probability;
- change score weights.

---

## 24. RELATION TO SIGNAL ENGINE

Signal Engine consumes post-FSM semantics in a flow where DecisionObject already exists.

Signal Engine may propagate:

- score snapshot;
- TPS snapshot;
- Trade Physics explanation/reference;
- model-time and execution-time evidence;
- learned probability snapshot where allowed.

It must not recalculate or redefine those truths.

---

## 25. RELATION TO DECISION AUDIT

Decision Audit uses DecisionObject as primary pre-FSM strategy truth.

Audit must be able to distinguish:

- Market truth used at decision time;
- Corridor structural truth;
- Time Model truth;
- classical score;
- deterministic Trade Physics;
- learned advisory context;
- reject/degrade result.

Downstream outcome or telemetry must never rewrite the historical DecisionObject.

---

## 26. DATASET / REPLAY REQUIREMENT

A serialized DecisionObject used for research/replay must retain enough versioned information to reproduce or explain:

- classical score;
- TPS;
- structural and time blockers;
- speed evidence;
- model readiness/probability state.

Future-outcome labels must remain downstream and separate to prevent leakage.

---

## 27. MIGRATION RULE

Runtime legacy data may temporarily contain:

- `buffer_price`;
- generic `expiry_minutes`;
- TPS calculated in Signal Engine;
- old debug maps.

Migration must normalize these into the v2 semantic contract.

Compatibility layers may read legacy fields but may not preserve them as canonical authority.

Direction:

`legacy output -> normalized complete DecisionObject -> FSM`

---

## 28. CODE ALIGNMENT RULE

After promotion, implementation must answer:

- where Trade Physics is calculated before DecisionObject;
- which exact structural/time/speed evidence was used;
- how readiness is represented;
- how classical score and TPS remain separate;
- what FSM receives;
- what Signal Engine receives without recomputation;
- how audit/event schema serialize the same truth;
- how learned probability provenance is represented.

---

## 29. VALIDATION REQUIREMENTS

At minimum:

1. DecisionObject cannot be created with mismatched market/corridor/time identities;
2. READY Trade Physics contains complete required metrics;
3. non-READY Trade Physics does not fabricate normal TPS;
4. deterministic TPS is exactly the scoring output;
5. Signal Engine cannot overwrite it;
6. learned probability uses a distinct field;
7. model id/readiness required whenever learned probability exists;
8. hard blockers remain visible even with high score/TPS;
9. serialization/deserialization preserves all values and versions;
10. replay can explain classical-score/TPS disagreement.

---

## 30. FINAL PRINCIPLE

`DecisionObject` is the canonical boundary between mathematical strategy truth and operational FSM truth.

After Trade Physics integration, the strategic truth is no longer complete unless it can explain:

**what the market looked like, where the structural room was, whether there was enough directional time/flow, what the classical score said, what Trade Physics said, and why the setup was accepted, degraded or rejected.**
