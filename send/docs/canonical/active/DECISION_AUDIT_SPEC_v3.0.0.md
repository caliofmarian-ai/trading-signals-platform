# DECISION_AUDIT_SPEC_v3.0.0

Path: /opt/binarybot/docs/canonical/active/DECISION_AUDIT_SPEC_v3.0.0.md  
Version: 3.0.0  
Status: ACTIVE CANONICAL  
Owner: BinaryBot / DROPi Signals  
Scope: Pre-FSM strategy-decision audit, Trade Physics decision evidence, rejection taxonomy, lifecycle reasoning, downstream correlation

Supersedes: `DECISION_AUDIT_SPEC_v2.0.0.md`
Governance basis: Change ID `20260901-TRADE-PHYSICS-01`; merged PR #78

Linked documents:
- `canonical/active/ALGO_SPEC_v3.0.0.md`
- `canonical/active/SR_CORRIDOR_ENGINE_SPEC_v3.0.0.md`
- `canonical/active/TIME_MODEL_UNIFIED_CANON_v3.0.0.md`
- `canonical/active/TRADE_PHYSICS_MODEL_SPEC_v1.0.0.md`
- `canonical/active/DECISION_OBJECT_CANONICAL_SPEC_v2.0.0.md`
- active FSM/observability/event-schema versions until their staged/consolidated successors are promoted

---

## 0. PROMOTION STATUS

This is the active canonical successor to v2.0.0. Runtime changes remain subject to Governance, Test Plan, and Deployment Protocol controls.

---

## 1. PURPOSE

Decision Audit is the canonical record of **what the strategy decided at decision time and why**.

It records and correlates:

- candidate detection;
- Market Model evidence;
- SR/Corridor qualification;
- Time Model qualification;
- classical score;
- Trade Physics readiness, components and deterministic TPS;
- strategic gating/rejection/degradation;
- DecisionObject production;
- later FSM/lifecycle correlation without overwriting strategy truth.

The audit must answer why a candidate was promoted, rejected, delayed, stalled, killed, suppressed or never reached OPEN_NOW.

---

## 2. CANONICAL POSITION

Decision Audit is pre-FSM strategy truth.

Canonical order:

`Market -> Corridor -> Time -> Classical Score + Trade Physics -> DecisionObject -> Decision Audit truth -> FSM -> Signal Execution -> downstream evidence`

Decision Audit may later correlate FSM, distribution, telemetry and outcomes, but those layers never rewrite the historical strategy decision.

---

## 3. CORRECTION OF V2 LIFECYCLE DRIFT

The v2 document contained an internal ordering where `DECISION_OBJECT_PRODUCED` appeared before `SCORE_COMPUTED`.

That conflicts with the active Root Stack and ALGO architecture.

v3 corrects the lifecycle to:

```text
WIDE_SCAN
  ↓
CANDIDATE_DETECTED
  ↓
MARKET_CONTEXT_DERIVED
  ↓
CORRIDOR_QUALIFIED
  ↓
TIME_MODEL_QUALIFIED
  ↓
CLASSICAL_SCORE_COMPUTED
  ↓
TRADE_PHYSICS_EVALUATED
  ↓
STRATEGIC_GATES_EVALUATED
  ↓
DECISION_OBJECT_PRODUCED
  ↓
FSM_HANDOFF
  ↓
FSM / SIGNAL / DISTRIBUTION / TELEMETRY / OUTCOME CORRELATION
```

This ordering is mandatory if v3 is promoted.

---

## 4. DESIGN PRINCIPLES

1. Rejections are explicit, never inferred from silence.
2. Every material decision point is observable.
3. Strategy truth is immutable historical truth once recorded.
4. Audit events are correlation-ready.
5. Audit failure must not invent decision truth.
6. Classical score and Trade Physics remain distinguishable.
7. Learned probability, if available, is labeled separately from deterministic TPS.
8. Missing Trade Physics evidence is itself auditable evidence.

---

## 5. CORE QUESTIONS

Decision Audit must answer:

- What market/context evidence existed?
- Which directional structural barrier was selected?
- How much `available_space` existed?
- Was structure valid or constrained?
- What directional speed and time feasibility existed?
- What classical score was produced and from which components?
- Was Trade Physics READY?
- What S/T/P/V components and TPS were produced?
- Why was TPS unavailable if not READY?
- Did classical score and TPS agree or diverge?
- Which hard/soft gate controlled the strategy result?
- What DecisionObject was handed to FSM?
- What happened downstream without confusing downstream truth with the original decision?

---

## 6. CORE ENTITIES AND IDENTITIES

Audit must support stable identifiers for:

- candidate/setup;
- decision evaluation;
- strategy cycle/run;
- candle context;
- signal/opportunity identity when assigned;
- Trade Physics calculation/version;
- learned model identity when applicable.

At minimum preserve:

- symbol;
- direction;
- timeframe;
- candle/evaluation timestamp;
- candidate/setup id;
- correlation id;
- run/cycle id;
- signal id when available.

---

## 7. AUDIT EVENT CLASSES

The audit model must support at least:

- `candidate_detected`;
- `decision_evaluated`;
- `decision_rejected`;
- `decision_promoted` / equivalent stage-promotion truth;
- `decision_no_signal`;
- focus/watchlist decision evidence where strategically relevant;
- link/reference to FSM truth;
- downstream outcome linkage event/reference.

Exact event-family names must align with the active/consolidated Event Schema. Decision Audit does not invent duplicate event names independently.

---

## 8. DECISION_EVALUATED REQUIREMENTS

The decision evaluation must preserve pre-FSM evidence sufficient to reconstruct:

### Market

- trend/context;
- volatility/noise state;
- ATR;
- buffer distance;
- gross and directional movement speed where applicable.

### Structure

- corridor identity;
- directional barrier;
- `available_space`;
- feasibility/compression/conflict;
- structural reason.

### Time

- `t_needed`;
- `t_needed_adjusted`;
- `model_expiry`;
- `model_time_reach_ratio`;
- `time_to_buffer_ratio`;
- `corridor_time_pressure`;
- `time_state`.

### Classical score

- total;
- components;
- tier;
- blockers/penalties.

### Trade Physics

- readiness;
- required primitives;
- S/T/P/V;
- deterministic TPS;
- band;
- formula/spec version;
- missing/invalid reason when unavailable.

### Decision result

- strategic result/kind;
- reject/degrade semantics;
- DecisionObject schema/version/reference.

---

## 9. TRADE PHYSICS AUDIT CONTRACT

Trade Physics evidence must not be a single naked TPS number.

For a READY calculation, audit must be able to retain:

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
- S;
- T;
- P;
- V;
- TPS;
- TPS band;
- formula version.

For a non-READY calculation, audit must preserve:

- readiness state;
- missing/invalid source;
- upstream blocker;
- whether any partial metrics were diagnostic-only.

---

## 10. LEARNED PROBABILITY AUDIT CONTRACT

If `trade_success_probability` exists, Decision Audit must record separately:

- probability value;
- model id/version;
- feature schema version;
- readiness state;
- calibration/validation reference;
- authority mode;
- whether the value actually influenced the strategy decision.

A missing/untrained model is a valid current system state and must not be represented by a fake probability.

---

## 11. SCORE/TPS DISAGREEMENT ANALYSIS

Audit must enable later grouping of decisions into patterns such as:

- both strong;
- both weak;
- classical strong / TPS weak;
- classical weak / TPS strong;
- TPS unavailable.

No composite score may destroy the original values.

This evidence is required before any future policy that combines the two scores or assigns TPS-specific lifecycle thresholds.

---

## 12. REJECTION TAXONOMY

Existing rejection families remain valid and are extended with explicit Trade Physics-capable reasons.

### Score/classical

- score pre/confirm/open failure where active policy uses those thresholds.

### Structural

- structure reject;
- corridor reject;
- SR reject;
- `structural_space_insufficient`;
- `directional_barrier_unavailable`;
- compression/conflict rejection.

### Time

- time-model reject;
- feasibility reject;
- `directional_speed_unavailable`;
- time insufficient.

### Trade Physics

- `trade_physics_unavailable`;
- `trade_physics_invalid_evidence`;
- `trade_physics_unstable_market`;
- any future TPS policy rejection only when such policy is explicitly active.

### Operational

Distribution/dedup/channel failures remain operational and must not be mislabeled as strategic Trade Physics failure.

### Integrity

Missing candles, invalid shapes, adapter/schema failures and state corruption remain separate integrity reasons.

---

## 13. HARD VS SOFT BLOCKER DISTINCTION

Audit must distinguish:

- hard strategic blocker;
- soft/degradation reason;
- informational score weakness;
- operational downstream blocker;
- missing evidence.

A high TPS or classical score cannot erase a recorded hard blocker.

---

## 14. REQUIRED AUDIT ENVELOPE

Every material audit record must follow the active Event Schema envelope and include sufficient identity/context such as:

- event id/type/schema version;
- UTC/epoch timestamp;
- service/environment/module;
- run/cycle/correlation identifiers;
- symbol/direction/timeframe/candle context;
- strategy/DecisionObject/Trade Physics versions;
- structured payload.

Exact envelope fields remain owned by Event Schema.

---

## 15. TRUTH-LAYER SEPARATION

Decision Audit = what strategy believed at decision time.

FSM event = operational state interpretation.

Signal execution event = signal-engine action/non-action truth.

Distribution event = route/publish truth.

Telemetry = what market did later.

Outcome reconciliation = operator/reconciled result.

Analytics/research = interpretation.

Learned model = derived intelligence.

No layer overwrites another.

---

## 16. OUTCOME LINKAGE

Later telemetry/outcomes may be linked using stable setup/signal/correlation identity.

The link enables questions such as:

- how do TPS bands correlate with market truth?
- which Trade Physics components are predictive?
- does directional speed improve timing quality?
- are constrained-space rejects protective?
- which classical/TPS disagreement pattern performs best?

Outcome linkage adds evidence; it does not mutate historical decision fields.

---

## 17. ANALYTICS REQUIREMENTS

Decision Audit must support aggregation by:

- symbol;
- direction;
- session/timeframe;
- market/volatility regime;
- corridor regime;
- classical score band;
- TPS band;
- Trade Physics readiness;
- rejection reason;
- directional speed/flow band;
- movement-stress band;
- model version;
- learned probability band/readiness when valid.

---

## 18. PARAMETER/EXPERIMENT CORRELATION

Any future TPS cap/weight/threshold experiment must be linked to:

- parameter/config version;
- experiment/hypothesis id;
- before/after or branch identity;
- evidence window;
- approval state.

Decision Audit must make it possible to attribute behavior to the actual version in force.

---

## 19. STAGE-OF-DEATH ANALYSIS

The audit system must localize where setups die:

- Market/context;
- Structure/Corridor;
- Time;
- Classical score;
- Trade Physics readiness/physical feasibility;
- strategic gate;
- focus/watchlist;
- FSM;
- Signal Engine;
- Distribution.

These stages must not be collapsed into generic `NO_SIGNAL`.

---

## 20. OBSERVABILITY FAILURE

If audit/logging infrastructure fails:

- strategy truth must not be fabricated;
- logging failure must itself be observable/recoverable where possible;
- engine behavior must follow active failure-recovery policy;
- later analytics must be able to distinguish missing instrumentation from genuine absence of events.

---

## 21. PRIVACY / DATA MINIMIZATION

Trade Physics decision evidence is market/strategy data and may be retained for research under storage/retention policy.

User/member identity is not required for decision-time Trade Physics truth and must not be added unnecessarily.

Operational/community truth remains separately governed.

---

## 22. FORBIDDEN AUDIT PATTERNS

Forbidden:

- DecisionObject logged before scoring/TPS evaluation in the promoted v3 pipeline;
- TPS without components/readiness/version;
- learned probability stored as TPS;
- generic `expiry_minutes` treated as model-time truth;
- Signal Engine-derived TPS overwriting pre-FSM strategy audit;
- downstream outcome changing historical decision fields;
- opaque debug blob as sole Trade Physics evidence;
- missing evidence silently represented as zero;
- distribution failure labeled as strategy rejection;
- retrospective feature leakage into decision-time records.

---

## 23. CODE ALIGNMENT RULE

Under this active canon, code must demonstrate:

- decision audit occurs from the final pre-FSM DecisionObject;
- score is computed before DecisionObject;
- Trade Physics is computed before DecisionObject;
- exact source values/versions are captured;
- event schema validation passes;
- downstream events link rather than overwrite;
- legacy TPS logging in Signal Engine no longer acts as primary decision truth.

---

## 24. VALIDATION REQUIREMENTS

At minimum:

1. lifecycle order test proves scoring/TPS before DecisionObject;
2. READY Trade Physics audit reproduces exact calculation values;
3. non-READY reason is explicit;
4. high score/TPS cannot hide blockers;
5. model-time and execution-time values are distinguishable;
6. learned probability requires model provenance;
7. downstream outcome linkage leaves original decision immutable;
8. stage-of-death aggregation distinguishes strategy, FSM, execution and distribution;
9. replay across versions remains attributable;
10. missing observability is detectable as instrumentation failure.

---

## 25. FINAL PRINCIPLE

Decision Audit must preserve the complete pre-FSM reasoning chain:

`MARKET -> STRUCTURE -> DIRECTIONAL TIME -> CLASSICAL SCORE -> TRADE PHYSICS -> DECISIONOBJECT`

Only after that truth exists may FSM and downstream systems add their own truth.

The audit exists so the project can improve from evidence without rewriting history or confusing a strong-looking score with proven market success.
