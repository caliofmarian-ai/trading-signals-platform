# SYSTEM_ARCHITECTURE_MAP_v3.0.0

Version: 3.0.0  
Status: ACTIVE CANONICAL  
Owner: BinaryBot / DROPi Signals  
Scope: top-level system architecture, layer ownership, current-scope Trade Physics, staged execution and evidence/intelligence flow  
Supersedes: `SYSTEM_ARCHITECTURE_MAP_v2.0.0.md`  

Linked proposed/current authorities:
- `CANONICAL_STRATEGY_STACK_v2.0.0.md`
- `SYSTEM_INVARIANTS_v3.0.0.md`
- `MODULE_INTERFACE_SPEC_v3.0.0.md`
- `EVENT_SCHEMA_SPEC_v3.0.0.md`
- `OBSERVABILITY_SPEC_v3.0.0.md`
- `DECISION_AUDIT_SPEC_v3.0.0.md`
- `TRADE_TEMPORAL_TELEMETRY_SPEC_v3.0.0.md`
- `OUTCOME_TRACKING_SPEC_v3.0.0.md`
- `TRADE_PHYSICS_MODEL_SPEC_v1.0.0.md`
- `TRADE_PHYSICS_INTELLIGENCE_SPEC_v1.0.0.md`
- `SIGNAL_DISTRIBUTION_ARCHITECTURE_v2.0.0.md`
- `SIGNAL_DISTRIBUTION_SPEC_v2.0.0.md`
- `STRATEGY_INTELLIGENCE_SYSTEM_v3.0.0.md`
- `AUTONOMOUS_STRATEGY_EVOLUTION_SYSTEM_v3.0.0.md`
- `GOVERNANCE_AND_CHANGE_CONTROL_v2.0.0.md`
- `TEST_PLAN_v3.0.0.md`

---

## 0. Authority and promotion status

This document is a complete proposed successor for the top-level system architecture map.

Promotion status: ACTIVE CANONICAL under `CANONICAL_ACTIVATION_RECORD_20260901.md` and `CANONICAL_MASTER_INDEX_v2.0.0.md`.

The major version is required because the architecture now explicitly includes:
- deterministic Trade Physics inside the runtime strategy path;
- Trade Physics Intelligence as a governed downstream learning/calibration subsystem;
- explicit DecisionObject -> FSM -> Signal Engine -> Distribution truth boundaries;
- SignalEvent candidate vs publication separation;
- market telemetry and operational outcome truth separation.

---

## 1. Purpose

This map defines the canonical architectural layers of BinaryBot / DROPi Signals and assigns each important concern one primary ownership home.

It prevents:
- duplicate ownership;
- hidden strategy logic in downstream modules;
- code-first subsystem growth;
- intelligence rewriting runtime truth;
- Signal Engine becoming a second strategy engine;
- distribution deciding validity;
- market and admin outcomes being merged;
- AI/model outputs gaining influence without readiness/governance.

Subsystem specifications govern their domains inside this architecture.

---

## 2. Final architecture principle

Every material truth must have:
- one primary owner;
- explicit upstream inputs;
- explicit downstream consumers;
- versioned contracts;
- observable handoffs;
- no silent authority transfer.

Higher analytical layers may interpret lower-layer evidence but may not rewrite historical lower-layer truth.

---

## 3. Canonical architecture layers

The v3 architecture is organized into ten primary layers:

1. MARKET / ENGINE INPUT
2. STRATEGY ENGINE
3. DECISION CONTRACT
4. FSM / LIFECYCLE
5. SIGNAL EXECUTION
6. DISTRIBUTION / EXTERNAL VISIBILITY
7. OBSERVABILITY / AUDIT / TELEMETRY / OUTCOME
8. ANALYTICS / RESEARCH / INTELLIGENCE
9. ADMIN / GOVERNANCE / CONTROL
10. RISK / SECURITY / DEPLOYMENT / RECOVERY

These layers interact, but ownership remains explicit.

---

## 4. Top-level runtime flow

```text
MARKET DATA
  -> MARKET MODEL
  -> SR / CORRIDOR
  -> TIME MODEL
  -> SCORING
       -> CLASSICAL SCORE
       -> DETERMINISTIC TRADE PHYSICS (TPS)
  -> DECISION OBJECT
  -> FSM
  -> SIGNAL ENGINE
  -> SIGNAL EVENT CANDIDATE / EXECUTION RESULT
  -> DISTRIBUTION ROUTER
  -> PUBLISHER / EXTERNAL VISIBILITY
```

Evidence and learning flow:

```text
DECISION / FSM / EXECUTION / ROUTE EVIDENCE
  -> OBSERVABILITY + DECISION AUDIT
  -> TRADE TEMPORAL TELEMETRY
  -> OUTCOME RECONCILIATION
  -> PERFORMANCE ANALYTICS
  -> RESEARCH & LEARNING
  -> TRADE PHYSICS / STRATEGY INTELLIGENCE
  -> CONTROLLED EVOLUTION / HUMAN GOVERNANCE
```

No downstream learning loop silently writes itself back into runtime strategy.

---

## 5. Layer 1 — Market / Engine Input

Primary responsibilities:
- normalized candle/market input;
- provider integrity;
- indicator evidence;
- ATR/volatility/activity/noise;
- trend/momentum context;
- buffer-distance inputs;
- gross price-movement context.

Canonical owner documents include ALGO/Market-related strategy contracts and Module Interface.

This layer does not decide final structural feasibility, TPS, FSM state or publication.

---

## 6. Layer 2 — Strategy Engine

The Strategy Engine contains four ordered sublayers:

### 6.1 Market Model
Transforms real market data into deterministic market context.

### 6.2 SR / Corridor
Owns:
- support/resistance interpretation;
- active corridor;
- directional barrier;
- `available_space`;
- structural feasibility/conflict/compression.

### 6.3 Time Model
Owns:
- direction-aware movement feasibility;
- `directional_effective_speed`;
- `flow_efficiency` relationship;
- `t_needed` / `t_needed_adjusted`;
- `model_expiry`;
- `model_time_reach_ratio`;
- `time_to_buffer_ratio` mapping;
- `corridor_time_pressure`;
- `time_state`.

### 6.4 Scoring + Deterministic Trade Physics
Owns:
- classical score;
- deterministic S/T/P/V components;
- deterministic `TPS` `[0,100]`;
- pre-DecisionObject strategic eligibility/blocker explanation.

Trade Physics is current runtime strategy, not future-only intelligence.

---

## 7. Deterministic Trade Physics position

`TRADE_PHYSICS_MODEL_SPEC_v1.0.0.md` is the mathematics authority for deterministic Trade Physics.

It consumes upstream Market/SR/Time evidence.

It does not:
- read future outcomes;
- train ML models;
- publish signals;
- own FSM state;
- own Distribution.

Its output is pre-FSM strategy truth.

---

## 8. Layer 3 — Decision Contract

`DecisionObject` is the canonical boundary between complete strategy truth and operational lifecycle control.

It contains recognizable domains for:
- setup identity;
- market context;
- structure;
- time;
- classical score;
- deterministic Trade Physics;
- optional validated learned probability;
- strategic flags/reject reasons;
- observability/version metadata.

DecisionObject is produced after scoring and before FSM.

---

## 9. Layer 4 — FSM / Lifecycle

FSM owns:
- operational lifecycle state;
- PRE/CONFIRM/OPEN_NOW progression;
- focus/watchlist/cooldown/duplicate rules assigned to lifecycle;
- requested stage;
- accepted stage;
- `stage_handoff_ready`;
- `trade_execution_ready`;
- operational reason/state transition.

FSM does not recalculate strategy mathematics or Trade Physics.

---

## 10. Layer 5 — Signal Execution

Signal Engine owns:
- exact-stage FSM handoff validation;
- SignalEvent candidate construction;
- engine-side duplicate protection;
- execution outcome classification;
- Distribution handoff;
- execution observability.

Signal Engine must not:
- recompute TPS;
- change DecisionObject truth;
- infer publication success from candidate creation;
- select subscriber entitlements;
- execute broker trades unless a separately governed broker layer is introduced.

---

## 11. Candidate vs delivery boundary

A `SignalEvent` is an internal candidate for Distribution.

It is not proof of:
- route selection;
- Telegram delivery;
- subscriber visibility;
- operational outcome;
- broker execution.

Execution truth distinguishes:
- EMITTED
- NOT_EMITTED
- BLOCKED
- SKIPPED
- FAILED
- DEFERRED

EMITTED requires downstream successful publication evidence.

---

## 12. Layer 6 — Distribution / External Visibility

Distribution Router owns:
- route selection;
- entitlement;
- destination mapping;
- route state;
- route-level dedup/counters;
- publish/skip decision.

Publisher/transport owns actual transport call/result.

External visibility exists only after governed successful publication evidence.

Distribution does not reinterpret classical score/TPS or create strategic validity.

---

## 13. Layer 7 — Observability / Audit / Telemetry / Outcome

This evidence layer is internally separated.

### 13.1 Observability
Records structured factual evidence across every material layer.

### 13.2 Decision Audit
Explains pre-FSM strategy decision/rejection truth.

### 13.3 Trade Temporal Telemetry
Owns objective post-executable market truth and market labels.

### 13.4 Outcome Reconciliation
Owns operational/admin WIN/LOSE/MISSED truth.

Market labels and operational labels are separate and joinable.

---

## 14. Event-truth separation

The architecture distinguishes:
- strategy decision event;
- FSM event;
- Signal Engine execution event;
- route publication event;
- external visibility event;
- market telemetry result;
- operational/admin outcome.

They must never be collapsed into one generic signal result.

---

## 15. Layer 8 — Analytics / Research / Intelligence

### 15.1 Performance Analytics
Measures truth-layer-separated performance, TPS calibration and model metrics.

### 15.2 Research & Learning
Owns hypotheses, experiments, evidence confidence and controlled investigation.

### 15.3 Trade Physics Intelligence
Owns:
- feature datasets;
- anti-leakage lineage;
- training/evaluation/calibration;
- model registry;
- `trade_success_probability`;
- readiness/drift/OOD governance.

### 15.4 Strategy Intelligence
Turns evidence into operator-facing diagnostics/recommendations.

### 15.5 Autonomous Strategy Evolution
Builds governed experiment/rollout recommendations but does not silently mutate production.

---

## 16. Learned probability boundary

`trade_success_probability` is distinct from deterministic TPS.

A prediction may exist only if:
- a real model exists;
- feature schema/version is known;
- validation/calibration evidence exists;
- readiness permits prediction use.

Absence of a validated model produces no fabricated probability.

---

## 17. Layer 9 — Admin / Governance / Control

Admin/control plane owns:
- roles/permissions;
- control surfaces;
- proof logging of mutations;
- approved parameter changes;
- model readiness/approval views;
- rollback/reset operations where governed;
- human review.

Admin does not own strategy truth.

No control surface may expose authority broader than Governance/Role/Parameter canon permits.

---

## 18. Trade Physics control-plane position

The control plane should be able to expose, role permitting:
- deterministic TPS and component explanations;
- formula/version;
- model readiness;
- model version/calibration/drift state;
- recommendation-only findings;
- approved tunable parameter values.

It must not expose structural formula mutation as if it were ordinary threshold tuning.

---

## 19. Layer 10 — Risk / Security / Deployment / Recovery

### Risk
Owns protective exposure/capital rules and post-signal constraints assigned by risk canon.

### Security
Owns credential/data/model-artifact protection and authorization/security rules.

### Deployment
Owns controlled rollout/restart/rollback protocol.

### Recovery
Owns restart/recovery/failure restoration rules.

These layers may block or govern operations but must remain observable and may not secretly redefine strategy mathematics.

---

## 20. Cross-layer dependency rules

Mandatory:
1. Strategy consumes real market evidence, not future labels.
2. SR precedes Time.
3. Time precedes Scoring/TPS.
4. Scoring/TPS precedes DecisionObject.
5. DecisionObject precedes FSM.
6. FSM precedes Signal Engine candidate construction.
7. Signal Engine precedes Distribution.
8. Distribution precedes external visibility proof.
9. Telemetry labels occur after executable truth.
10. Intelligence/evolution is downstream of evidence and upstream only through governed proposals/approvals.

---

## 21. Data lineage architecture

For model/research reproducibility, the system must preserve:
- feature cutoff timestamp;
- feature/formula version;
- DecisionObject version;
- signal/execution identity;
- market label provenance;
- operational label provenance;
- model id/version/calibration/readiness;
- parameter/config version.

No downstream label may leak into pre-trade feature truth.

---

## 22. Canonical ownership table

| Concern | Primary owner |
|---|---|
| Market context / ATR / raw indicators | Market Model / ALGO |
| Directional structural barrier/space | SR/Corridor |
| Directional time feasibility | Time Model |
| Classical score | ALGO / Scoring |
| Deterministic TPS | Trade Physics Model / Scoring |
| Pre-FSM strategy contract | DecisionObject |
| Operational stage handoff | FSM |
| SignalEvent candidate / execution outcome | Signal Engine |
| Route/destination publication | Distribution |
| External visibility proof | Distribution/Publisher + Event/Observability |
| Objective market outcome | Trade Temporal Telemetry |
| Operational/admin outcome | Outcome Reconciliation |
| Model training/calibration/readiness | Trade Physics Intelligence |
| Performance interpretation | Performance Analytics |
| Hypotheses/experiments | Research & Learning |
| Strategy diagnostics | Strategy Intelligence |
| Governed evolution proposals | Autonomous Evolution |
| Mutation authority/process | Admin/Governance/Parameter Control |

---

## 23. Forbidden ownership patterns

Forbidden:
- Signal Engine owns/recomputes TPS;
- FSM reconstructs strategy math;
- Distribution decides signal validity from raw indicators;
- Telemetry overwrites DecisionObject;
- Outcome overwrites market telemetry;
- Intelligence invents missing raw evidence;
- ML prediction called TPS;
- model silently changes production behavior;
- Admin bypasses permission/governance;
- broker execution hidden inside Signal Engine/Publisher without separate canon.

---

## 24. Document classification rule

Before adding a new canonical document, determine whether the concern is already owned by an existing domain.

Prefer extension of the existing owner document unless the concern has:
- distinct stable truth;
- distinct lifecycle;
- distinct authority boundary;
- enough independent scope to justify a new domain.

This is why deterministic Trade Physics and Trade Physics Intelligence have separate authorities: one is runtime mathematics, the other is downstream model/data/readiness governance.

---

## 25. Runtime mapping rule

Code modules are implementations of canonical ownership, not authority themselves.

After promotion, code audit must identify:
- modules that own too much;
- duplicate formulas;
- missing contracts;
- stale vocabulary;
- hidden shortcuts;
- incorrectly located TPS calculation;
- schema/event drift.

---

## 26. Promotion / migration rule

On v3 promotion:
- v2 moves to superseded storage;
- all active references are repaired to final successor versions;
- Root Stack/Master Index/System Invariants/Test Plan must be mutually compatible;
- runtime code remains unchanged until post-promotion audit.

---

## 27. Final principle

BinaryBot v3 architecture treats Trade Physics as first-class current strategy truth while keeping learned intelligence downstream and governed. The strategy becomes more physically aware without sacrificing the strict ownership chain from DecisionObject through FSM, Signal Engine, Distribution and evidence layers.
