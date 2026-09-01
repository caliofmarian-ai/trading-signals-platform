# CANONICAL_STRATEGY_STACK_v2.0.0

Version: 2.0.0  
Status: ACTIVE CANONICAL ROOT MANIFEST  
Owner: BinaryBot / DROPi Signals  
Scope: root strategy pipeline, Trade Physics integration, post-FSM execution handoff, canonical authority order and conflict resolution  
Supersedes: `CANONICAL_STRATEGY_STACK_v1.0.0.md`

---

## 0. Authority status

This document is the active root manifest for the strategy cluster.

`CANONICAL_STRATEGY_STACK_v1.0.0.md` is superseded and historical only.

This version consolidates two Owner-approved structural programs now in current canon:
1. staged signal execution / post-FSM observability remediation;
2. complete current-scope Trade Physics integration.

Documentation activation does not itself authorize runtime implementation; runtime remains gated by the post-promotion canon-to-code audit.

---

## 1. Purpose

This root manifest defines:
- the official strategic pipeline;
- root domain authorities;
- topic precedence;
- ownership boundaries;
- mandatory vocabulary;
- implementation/audit order;
- relationship between deterministic Trade Physics and learned intelligence;
- relationship between FSM stage handoff and downstream signal execution.

Its purpose is to prevent mixed-version reasoning, code-first drift, duplicate ownership and shortcut implementations.

---

## 2. Core principle

BinaryBot strategy is a layered system, not one opaque formula.

The runtime-critical strategic layers are:
- market model;
- SR/corridor structural model;
- time model;
- classical scoring;
- deterministic Trade Physics;
- DecisionObject;
- FSM operational lifecycle;
- Signal Engine execution;
- Distribution/visibility;
- Observability.

The learning/intelligence layers consume evidence downstream and may recommend controlled evolution without silently rewriting runtime truth.

---

## 3. Official strategy flow

The only official strategy flow is:

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
   ├── CLASSICAL SCORE
   └── DETERMINISTIC TRADE PHYSICS (TPS)
   ↓
DECISION OBJECT
   ↓
DECISION FSM
   ↓
SIGNAL ENGINE
   ↓
SIGNAL EVENT CANDIDATE / EXECUTION RESULT
   ↓
DISTRIBUTION ROUTER
   ↓
PUBLISHER / EXTERNAL VISIBILITY
   ↓
TELEMETRY / OUTCOME / ANALYTICS / RESEARCH / INTELLIGENCE
```

No document or runtime path may invert or bypass this order without a new governed structural change.

---

## 4. Active runtime root canonical set

The active runtime root set is:

1. `ALGO_SPEC_v3.0.0.md`
2. `SR_CORRIDOR_ENGINE_SPEC_v3.0.0.md`
3. `TIME_MODEL_UNIFIED_CANON_v3.0.0.md`
4. `TRADE_PHYSICS_MODEL_SPEC_v1.0.0.md`
5. `DECISION_OBJECT_CANONICAL_SPEC_v2.0.0.md`
6. `FSM_DECISION_ENGINE_SPEC_v2.0.0.md`
7. `SIGNAL_ENGINE_EXECUTION_SPEC_v3.0.0.md`
8. `OBSERVABILITY_SPEC_v3.0.0.md`

These documents define the primary normative runtime strategy stack.

---

## 5. Active supporting/adjacent canonical authorities

### System / interface / validation
- `SYSTEM_ARCHITECTURE_MAP_v3.0.0.md`
- `SYSTEM_INVARIANTS_v3.0.0.md`
- `TEST_PLAN_v3.0.0.md`
- `MODULE_INTERFACE_SPEC_v3.0.0.md`

### Observability / decision evidence
- `EVENT_SCHEMA_SPEC_v3.0.0.md`
- `OBSERVABILITY_LOGGING_SPEC_v3.0.0.md`
- `DECISION_AUDIT_SPEC_v3.0.0.md`
- `TRADE_TEMPORAL_TELEMETRY_SPEC_v3.0.0.md`

### Risk / outcomes / feedback
- `RISK_MODEL_v3.0.0.md`
- `OUTCOME_TRACKING_SPEC_v3.0.0.md`
- `COMMUNITY_FEEDBACK_AND_PRIVACY_SPEC_v3.0.0.md`

### Distribution / external surfaces
- `SIGNAL_DISTRIBUTION_ARCHITECTURE_v2.0.1.md`
- `SIGNAL_DISTRIBUTION_SPEC_v2.0.1.md`
- `CHANNEL_CONFIG_SPEC_v2.0.1.md`
- `TELEGRAM_UX_v2.0.1.md`

### Admin / human control plane
- `ADMIN_SURFACE_AND_CONTROL_PLANE_CANON_v2.0.1.md`
- `ADMIN_CONTROL_SPEC_v2.0.1.md`
- `ADMIN_OPERATIONS_SPEC_v2.0.1.md`
- `ADMIN_TREE_MAP_v2.0.1.md`
- `CONTROL_PANEL_HIERARCHY_AND_INTELLIGENCE_SPEC_v2.0.1.md`
- `ROLE_AND_PERMISSION_MATRIX_SPEC_v2.0.1.md`
- `STRATEGY_PARAMETER_CONTROL_SPEC_v3.0.0.md`
- `HUMAN_COMPREHENSION_AND_SELF_EXPLAINING_CONTROL_SURFACE_CANON_v1.0.1.md`

### Analytics / research / intelligence
- `PERFORMANCE_ANALYTICS_SPEC_v3.0.0.md`
- `RESEARCH_AND_LEARNING_FRAMEWORK_SPEC_v3.0.0.md`
- `TRADE_PHYSICS_INTELLIGENCE_SPEC_v1.0.0.md`
- `STRATEGY_INTELLIGENCE_SYSTEM_v3.0.0.md`
- `AUTONOMOUS_STRATEGY_EVOLUTION_SYSTEM_v3.0.0.md`

### Commercial / affiliate
- `AFFILIATE_SIGNAL_DISTRIBUTION_MODEL_v2.0.1.md`
- `SIGNAL_ECONOMICS_AND_MONETIZATION_MODEL_v2.0.1.md`

### Governance / operations / safety
- `FAILURE_RECOVERY_SPEC_v2.0.1.md`
- `DEPLOYMENT_PROTOCOL_v2.0.1.md`
- `SECURITY_MODEL_v2.0.1.md`
- `GOVERNANCE_AND_CHANGE_CONTROL_v2.0.1.md`

Supporting authorities may refine their bounded mechanics but may not contradict runtime root authorities.

---

## 6. Authority order

When conflict exists:

### Level 1 — Root strategy authorities
- ALGO
- SR/Corridor
- Time Model
- Trade Physics Model
- DecisionObject
- FSM
- Signal Engine
- Observability Policy

### Level 2 — System/interface/schema/domain supporting canon
- System Architecture Map
- System Invariants
- Test Plan
- Module Interface
- Event Schema
- Observability Logging
- Decision Audit
- Telemetry
- Risk
- Outcome / Community Feedback according to truth-domain ownership
- Distribution
- Governance / Deployment / Recovery / Security

### Level 3 — Analytics/research/intelligence canon
- Performance Analytics
- Research & Learning
- Trade Physics Intelligence
- Strategy Intelligence
- Autonomous Evolution

These layers may interpret/evaluate root truth but do not silently redefine runtime formulas or lifecycle ownership.

### Level 4 — Proposed/transitional/supporting records
Not authoritative unless explicitly promoted into active canon.

### Level 5 — Superseded/deprecated/historical/intake
Context only; never primary implementation authority.

---

## 7. Market Model ownership

Market Model owns raw-to-derived market context, including:
- price/indicator context;
- ATR;
- volatility/activity/noise;
- buffer distance derivation under strategy parameters;
- gross market movement/speed context;
- direction-aware movement inputs as assigned by implementation contract.

Market Model does not own corridor, final time feasibility, TPS, FSM or signal execution.

---

## 8. SR/Corridor ownership

SR/Corridor owns structural truth:
- support/resistance landmarks;
- active corridor;
- directional relevant barrier;
- `available_space`;
- structural position/proximity;
- structural feasibility/conflict/compression.

Canonical Trade Physics structural relation:

`available_space = directional distance to nearest relevant structural barrier`

BUY -> relevant resistance direction.  
SELL -> relevant support direction.

---

## 9. Time Model ownership

Time Model owns:
- direction-aware movement feasibility;
- `directional_effective_speed` under its final canonical derivation;
- `flow_efficiency` relationship;
- `t_needed`;
- `t_needed_adjusted`;
- `model_expiry`;
- `model_time_reach_ratio`;
- `time_to_buffer_ratio` relation used by Trade Physics;
- `corridor_time_pressure`;
- `time_state`;
- governed execution-expiry derivation.

Canonical ratio orientation:

`model_time_reach_ratio = t_needed_adjusted / model_expiry`

and, when synchronized and valid:

`time_to_buffer_ratio = model_expiry / t_needed_adjusted = 1 / model_time_reach_ratio`

Neither may silently substitute for the other.

---

## 10. Deterministic Trade Physics ownership

`TRADE_PHYSICS_MODEL_SPEC_v1.0.0.md` owns deterministic physical-feasibility mathematics.

Core evidence:
- structural space;
- temporal feasibility;
- direction-aware speed;
- volatility/movement stress.

Canonical components:
- S = Space
- T = Time
- P = Price Speed
- V = Volatility Efficiency

Canonical deterministic score:

`TPS = 100 * (0.35*S + 0.25*T + 0.20*P + 0.20*V)`

bounded to `[0,100]`.

TPS is computed before DecisionObject.

Signal Engine, FSM, Distribution, Telemetry and Outcome do not recompute TPS.

---

## 11. Classical score and TPS separation

The classical strategy score and TPS are distinct first-class strategic metrics.

Classical score measures established signal/context quality.  
TPS measures deterministic physical feasibility.

There is no canonical combined score unless a future governed change defines one explicitly.

TPS interpretation bands do not automatically become PRE/CONFIRM/OPEN_NOW stage thresholds.

---

## 12. Learned probability separation

`trade_success_probability` is distinct from TPS.

Rules:
- TPS: deterministic `[0,100]`;
- learned probability: `[0,1]`;
- learned probability requires validated model/version/calibration/readiness;
- no model -> no fabricated probability;
- the old Intake sigmoid value must not remain another metric called TPS.

Trade Physics Intelligence owns learned-model lifecycle, not deterministic strategy mathematics.

---

## 13. DecisionObject ownership

DecisionObject is produced after complete strategic evaluation and before FSM.

It must contain recognizable domains for:
- setup identity;
- market context;
- structure;
- time;
- classical score;
- deterministic Trade Physics;
- optional valid learned prediction;
- strategic flags/reject semantics;
- FSM inputs/readiness;
- observability/version metadata.

DecisionObject is immutable pre-FSM truth for an evaluation.

---

## 14. FSM ownership

FSM consumes DecisionObject and owns operational lifecycle interpretation.

It must expose:
- requested stage;
- accepted stage;
- `stage_handoff_ready`;
- `trade_execution_ready`;
- reason/state transition;
- lifecycle/focus/watchlist/cooldown/duplicate truth.

PRE/CONFIRM may be handoff-ready but are never final trade-execution-ready.

FSM does not recalculate strategy/Trade Physics mathematics.

---

## 15. Signal Engine ownership

Signal Engine consumes explicit FSM handoff and owns:
- exact-stage validation;
- SignalEvent candidate construction;
- engine duplicate protection;
- execution outcome;
- Distribution handoff;
- execution observability.

Signal Engine must not recompute TPS.

SignalEvent construction is not publication.

---

## 16. Signal execution outcome families

Signal Engine truth distinguishes:
- EMITTED
- NOT_EMITTED
- BLOCKED
- SKIPPED
- FAILED
- DEFERRED

EMITTED requires downstream successful publication evidence.

A valid candidate while Distribution is intentionally not invoked is DEFERRED, not EMITTED.

---

## 17. Distribution ownership

Distribution ownership is governed by:
- `SIGNAL_DISTRIBUTION_ARCHITECTURE_v2.0.1.md` for topology/module boundaries;
- `SIGNAL_DISTRIBUTION_SPEC_v2.0.1.md` for entitlement/delivery policy.

Distribution owns:
- route selection;
- entitlement;
- destination mapping;
- route state;
- route-level dedup/counters;
- publish/skip policy.

It consumes validated SignalEvent candidates and does not decide strategic validity/TPS.

---

## 18. External visibility boundary

A stage becomes externally visible only after governed successful publication evidence.

Internal candidate creation, FSM acceptance or route intent does not prove external visibility.

---

## 19. Telemetry / outcome / community truth

`TRADE_TEMPORAL_TELEMETRY_SPEC_v3.0.0.md` owns objective post-executable market truth and labels.

`OUTCOME_TRACKING_SPEC_v3.0.0.md` owns operational/admin WIN/LOSE/MISSED reconciliation truth.

`COMMUNITY_FEEDBACK_AND_PRIVACY_SPEC_v3.0.0.md` owns self-reported member/community execution experience and privacy.

These truth layers remain distinct, labeled and joinable; none silently overwrites the others.

Trade Physics feature snapshots must be preserved with version/provenance for later research/modeling.

---

## 20. Trade Physics Intelligence ownership

`TRADE_PHYSICS_INTELLIGENCE_SPEC_v1.0.0.md` makes AI/calibration infrastructure current-scope:
- feature datasets;
- lineage/anti-leakage;
- training/evaluation;
- calibration;
- model registry;
- readiness states;
- drift/OOD monitoring;
- governed recommendations.

It may not silently modify production strategy.

---

## 21. Official vocabulary lock

Primary strategy vocabulary includes:

### Market/structure
- `buffer_distance`
- `available_space`
- `required_space`
- `space_to_buffer_ratio`
- `trade_space_margin_atr`
- support/resistance/corridor terms

### Speed/time
- gross price speed/context
- `directional_effective_speed`
- `flow_efficiency`
- `t_needed`
- `t_needed_adjusted`
- `model_expiry`
- `model_time_reach_ratio`
- `time_to_buffer_ratio`
- `corridor_time_pressure`
- `time_state`

### Scoring
- `score_total`
- score components
- `TPS`
- TPS S/T/P/V components
- `movement_stress`

### Learned intelligence
- `trade_success_probability`
- model/version/calibration/readiness

### FSM/execution
- requested/accepted stage
- `stage_handoff_ready`
- `trade_execution_ready`
- execution outcome families

---

## 22. Forbidden primary/ambiguous terms

Forbidden as primary active truth unless compatibility-mapped:
- `buffer_price` replacing `buffer_distance`;
- `expiry_minutes` as total time-model truth;
- `expiry_reach_ratio` as primary time term;
- learned probability called TPS;
- generic dict as final strategy contract;
- transition event treated as exact-stage acceptance;
- SignalEvent candidate treated as delivered signal.

---

## 23. Topic precedence

### Time mathematics conflicts
1. Time Model
2. ALGO
3. Trade Physics Model only for its consumption/mapping of canonical time evidence

### Structural-space conflicts
1. SR/Corridor
2. Trade Physics Model for derived space metrics
3. ALGO

### Deterministic TPS conflicts
1. Trade Physics Model
2. ALGO
3. DecisionObject/Analytics as consumers

### Learned model/probability conflicts
1. Trade Physics Intelligence
2. Research/Strategy Intelligence
3. Analytics as measurement consumer

### Strategy output conflicts
1. DecisionObject
2. ALGO / Trade Physics Model
3. FSM

### FSM handoff conflicts
1. FSM
2. Module Interface
3. Signal Engine

### Signal-execution conflicts
1. Signal Engine
2. Module Interface
3. Event/Observability

### Distribution conflicts
1. Distribution Architecture for topology/ownership
2. Distribution Spec for entitlement/delivery policy
3. Channel Config / Telegram UX as bounded consumers

### Truth-label conflicts
1. Telemetry for objective market truth
2. Outcome Tracking for operational/admin reconciliation
3. Community Feedback for self-reported member experience

---

## 24. Root implementation rule

No code patch may be based primarily on:
- Intake files;
- deprecated/superseded docs;
- runtime behavior that contradicts active canon;
- proposed docs that have not been promoted.

Every code change must cite the active root/domain authority relevant to the change.

---

## 25. Root audit rule

Future audits follow:
1. read current Master Index;
2. read current Root Strategy Stack;
3. identify relevant root/domain authorities;
4. read supporting interface/schema/invariant/governance docs;
5. map runtime implementation;
6. consult Intake/historical docs only for provenance.

Runtime is never used to override canon merely because it already exists.

---

## 26. Known implementation drift for immediate post-promotion audit

At minimum:
- TPS currently computed in/around Signal Engine rather than canonical scoring ownership;
- current TPS speed component differs from canonical ATR-reference formula;
- current Market Model gross speed is not the complete directional effective speed contract;
- Event runtime schema is drifted from canonical semantic event families;
- PRE/CONFIRM candidate handoff behavior requires re-audit;
- current post-FSM execution observability requires dedicated event implementation.

These findings authorize no code change until the post-promotion canon-to-code audit is completed.

---

## 27. Activation result

This version is activated as part of the atomic 2026-09-01 canonical promotion. The active graph must maintain:
- one Root Stack;
- one active version per canonical domain;
- superseded versions outside active truth;
- exact final successor references;
- Trade Physics as current-scope canon;
- staged-execution and Trade Physics semantics in one coherent graph;
- `RISK_MODEL_v3.0.0.md`;
- `COMMUNITY_FEEDBACK_AND_PRIVACY_SPEC_v3.0.0.md`;
- all final reference-repair successors;
- `SYSTEM_ARCHITECTURE_MAP_v3.0.0.md`, `SYSTEM_INVARIANTS_v3.0.0.md`, and `TEST_PLAN_v3.0.0.md`;
- runtime untouched until post-promotion audit.

---

## 28. Final principle

Binary Strategy V2 is corridor-first, directional-time-aware, dual-score-aware (classical score + deterministic TPS), DecisionObject-first and FSM-governed.

Trade Physics is part of the current strategy stack now. Learned probability is current-scope intelligence infrastructure but remains evidence/readiness governed. Signal execution remains downstream of explicit FSM handoff and cannot confuse an internal candidate with delivery.
