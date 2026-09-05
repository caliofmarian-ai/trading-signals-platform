# STRATEGY_TRADING_WINDOW_INTELLIGENCE_SPEC_v1.0.0

Canonical Name: STRATEGY_TRADING_WINDOW_INTELLIGENCE_SPEC  
Version: 1.0.0  
Status: TRANSITIONAL CANONICAL CANDIDATE — OWNER-DIRECTED — NOT ACTIVE UNTIL MASTER INDEX ACTIVATION  
Owner: BinaryBot / DROPi Signals  
Date: 2026-09-05  
Scope: Strategy-specific temporal suitability intelligence, market-versus-strategy comparison, favorable/unfavorable trading-window evidence, staged authority from observation to future governed gating

Linked active authorities:
- `CANONICAL_MASTER_INDEX_v2.0.0.md`
- `ALGO_SPEC_v3.0.0.md`
- `DECISION_OBJECT_CANONICAL_SPEC_v2.0.0.md`
- `TRADE_TEMPORAL_TELEMETRY_SPEC_v3.0.0.md`
- `OUTCOME_TRACKING_SPEC_v3.0.0.md`
- `PERFORMANCE_ANALYTICS_SPEC_v3.0.0.md`
- `RESEARCH_AND_LEARNING_FRAMEWORK_SPEC_v3.0.0.md`
- `STRATEGY_INTELLIGENCE_SYSTEM_v3.0.0.md`
- `STRATEGY_PARAMETER_CONTROL_SPEC_v3.0.0.md`
- `GOVERNANCE_AND_CHANGE_CONTROL_v2.0.1.md`
- `SYSTEM_INVARIANTS_v3.0.0.md`

Linked transitional candidates:
- `MARKET_BEHAVIOR_OBSERVATION_SPEC_v1.0.0.md`
- `TEMPORAL_MARKET_BEHAVIOR_ANALYTICS_SPEC_v1.0.0.md`
- `TEMPORAL_PATTERN_VALIDATION_SPEC_v1.0.0.md`

Governance issue: `#137`

---

## 0. Authority status

This document captures the Owner requirement to determine **when a given strategy is historically well matched or poorly matched to the current temporal/market context**.

It is transitional until explicit activation.

Its initial authority mode is observational/advisory only. It does not authorize automatic trade blocking, trade forcing, strategy mutation or broker execution.

---

## 1. Purpose

The system must learn whether the same strategy behaves differently depending on:

- hour of day;
- weekday;
- month/quarter;
- market regime;
- direction;
- structural context;
- volatility/noise state;
- score/TPS state;
- recurring price-behavior sequence.

The objective is not simply to find periods where price moves more.

The objective is to determine:

**When is Strategy X historically better or worse suited to the actual market behavior present at that time?**

---

## 2. Canonical position

Strategy Trading Window Intelligence is downstream of two evidence families:

### 2.1 Market behavior evidence

`Market Behavior Observation -> Temporal Market Behavior Analytics`

### 2.2 Strategy evidence

`Strategy -> DecisionObject -> FSM -> Signal/Execution -> Trade Temporal Telemetry -> Objective Outcomes -> Performance Analytics`

Strategy Trading Window Intelligence compares these domains while keeping their truths distinct.

It is an intelligence/research layer, not an upstream strategy authority by default.

---

## 3. Core distinction: favorable market vs favorable strategy window

A period of high market activity is not automatically favorable for every strategy.

Examples of distinct possibilities:

- high volatility may help a breakout/continuation strategy but hurt a mean-reversion strategy;
- low volatility may starve one strategy but improve another's structural reliability;
- a particular hour may have strong directional continuation but poor entry timing for the current binary strategy;
- BUY and SELL behavior may differ within the same temporal bucket.

Therefore every trading-window finding must be **strategy-specific and version-specific**.

---

## 4. Strategy identity requirements

Every strategy-conditioned temporal analysis must include at minimum:

- strategy family;
- strategy implementation/version;
- canonical specification/version;
- parameter-set/version/hash where available;
- symbol;
- timeframe;
- direction where applicable;
- relevant model/TPS version where applicable;
- analysis window.

Results from incompatible strategy versions must not be silently aggregated.

---

## 5. Required temporal dimensions

For each strategy, analysis must support at least:

- UTC hour;
- weekday;
- month;
- quarter;
- year/window context;
- session where governed;
- hour × weekday;
- hour × month;
- weekday × month.

Additional context interactions should include where sample size allows:

- hour × direction;
- hour × volatility regime;
- hour × trend regime;
- hour × noise state;
- hour × corridor/structure state;
- hour × classical score band;
- hour × TPS band;
- hour × behavior-sequence class;
- weekday × regime;
- month × regime.

High-dimensional combinations require stricter sample and validation discipline.

---

## 6. Required strategy evidence

Trading-window analysis must be able to inspect, where available:

### 6.1 Strategy selection/funnel

- evaluations;
- NO_SIGNAL;
- REJECT;
- PRE;
- CONFIRM;
- OPEN_NOW;
- exact-stage handoff;
- execution/distribution eligibility;
- publication where relevant.

### 6.2 Decision quality

- classical score distribution;
- TPS distribution/readiness;
- hard blockers;
- corridor/space evidence;
- Time Model evidence;
- market regime;
- direction;
- score/TPS disagreement.

### 6.3 Objective market outcome

For effective executable signals, use governed market truth such as:

- WIN / LOSS / DRAW at canonical expiry;
- MFE / MAE where available;
- midpoint and post-expiry behavior;
- favorable/adverse path;
- recovery/timing-mismatch evidence.

Community self-report must not substitute for objective market truth.

### 6.4 Market baseline

For the same temporal/contextual period, compare against unconditional or matched market behavior from Temporal Market Behavior Analytics.

---

## 7. Why the market baseline is mandatory

Suppose BUY signals win more often during Tuesday 09:00–10:00 UTC.

That observation alone does not prove strategy edge.

The system must ask:

- was EUR/USD generally rising more often during that context anyway?
- did the strategy select better-than-baseline moments?
- did its selected signals improve continuation probability, excursion or timing relative to matched market states?
- did the effect persist outside the discovery window?

The strategy must be evaluated against the market behavior it was exposed to, not only against its own past signals.

---

## 8. Trading-window evidence package

A strategy-specific temporal evidence package should include:

### Identity

- strategy/version;
- canonical spec;
- symbol/timeframe;
- direction where applicable;
- temporal bucket;
- regime/context;
- analysis window/version.

### Sample

- total market observations in comparable context;
- strategy evaluations;
- actionable-stage counts;
- effective executable signals;
- objective finalized outcomes;
- incomplete/missing outcomes;
- data-quality exclusions.

### Strategy behavior

- funnel conversion;
- score/TPS distributions;
- blocker distribution;
- strategy-selected market-state distribution;
- signal frequency.

### Objective performance

- market-truth outcome distribution;
- MFE/MAE/path metrics where available;
- direction-specific continuation/reversal behavior;
- expiry/timing quality.

### Baseline comparison

- unconditional market behavior;
- matched-regime market behavior;
- strategy-selected versus baseline effect;
- uncertainty/sample context.

### Stability

- recent window;
- medium window;
- longer historical window;
- cross-month/regime consistency;
- drift state.

---

## 9. No canonical numeric suitability formula yet

This v1 document intentionally does **not** define a universal `Trading Suitability Score 0–100` formula.

No evidence currently establishes canonical weights for:

- win rate;
- market continuation;
- MFE/MAE;
- score/TPS;
- sample size;
- volatility regime;
- pattern stability;
- funnel conversion.

Inventing those weights now would convert an analytical idea into unsupported strategy authority.

A future numeric suitability score requires its own governed, empirically validated definition.

Until then, intelligence must expose component evidence and bounded categorical readiness/suitability states.

---

## 10. Initial suitability states

The initial intelligence layer may classify a strategy/time/context combination with states such as:

- `UNAVAILABLE` — required evidence cannot be produced;
- `INSUFFICIENT_DATA` — evidence exists but is not adequate for interpretation;
- `RESEARCH_ONLY` — descriptive difference observed but not validated;
- `UNSTABLE` — apparent effect changes materially across windows/regimes;
- `ADVISORY_FAVORABLE` — validated evidence suggests better-than-baseline suitability, advisory only;
- `ADVISORY_NEUTRAL` — no material validated advantage/disadvantage established;
- `ADVISORY_UNFAVORABLE` — validated evidence suggests worse-than-baseline suitability, advisory only;
- `DRIFTED` — previously validated pattern is no longer stable;
- `SUSPENDED` — evidence/data quality is not trustworthy.

Exact transitions and proof requirements are governed by Temporal Pattern Validation and Research.

---

## 11. Authority modes

Temporal strategy intelligence must have explicit authority mode.

### 11.1 `OBSERVE`

Default initial mode.

The system:

- collects evidence;
- computes descriptive strategy/time context;
- does not influence decisions or signals.

### 11.2 `ADVISORY`

Permitted only after sufficient governed validation.

The system may display to Owner/Admin:

- favorable/neutral/unfavorable context;
- evidence summary;
- sample/readiness;
- pattern stability;
- risk/limitations.

It still does not change the live strategy.

### 11.3 `GOVERNED_GATE`

Future-only until separately approved.

A temporal finding may influence live signal eligibility only after:

- exact pattern/context specification;
- out-of-sample validation;
- stability evidence;
- strategy-version attribution;
- risk review;
- parameter/control-plane classification;
- Owner approval;
- versioned canon update;
- regression tests;
- rollback plan;
- bounded deployment/experiment.

This document does not activate `GOVERNED_GATE`.

---

## 12. Direction-specific intelligence

BUY and SELL must be analyzed separately where direction matters.

An hour may be:

- favorable for BUY;
- neutral for SELL;
- unfavorable for a different strategy.

Combining directions may hide a real asymmetry.

No symmetric behavior may be assumed without evidence.

---

## 13. Strategy-specific intelligence

Different strategy families must maintain separate temporal evidence.

Future example:

- Binary Strategy: advisory favorable;
- Forex Trend Strategy: advisory favorable/strong under its own evidence;
- Mean Reversion Strategy: advisory unfavorable.

One strategy's trading window must never become a global market rule.

---

## 14. Regime-conditioned suitability

A time bucket alone may be confounded by the market regimes usually present there.

The intelligence layer must support suitability conditioned on:

- volatility/activity;
- trend;
- noise/chop;
- structure/corridor;
- directional flow;
- behavior pattern;
- data/provider state.

A temporal conclusion should prefer matched-context evidence over a raw hour-only average when possible.

---

## 15. Pattern-conditioned suitability

The system may ask questions such as:

> When this formally defined price sequence occurs at this hour/weekday under this regime, how has Strategy X behaved relative to the matched market baseline?

The sequence must be defined before its future label and validated under Temporal Pattern Validation.

No hand-drawn hindsight pattern is admissible as production evidence.

---

## 16. Rolling-window and drift requirements

Trading-window intelligence must distinguish historical averages from current behavior.

Support rolling descriptive views such as:

- 7d;
- 30d;
- 90d;
- 180d;
- 365d;
- all history.

These are views, not proof thresholds.

The system must identify when:

- a formerly favorable window weakens;
- a formerly unfavorable window recovers;
- a pattern depends on one old period;
- market structure changes;
- strategy-version changes invalidate comparability.

Drift may downgrade or suspend advisory status.

---

## 17. Sample and uncertainty display

Every strategy trading-window output must show enough context to prevent small-sample illusion.

At minimum expose:

- N market observations;
- N strategy evaluations;
- N executable signals;
- N finalized objective outcomes;
- missing/incomplete counts;
- analysis window;
- validation state;
- stability/drift state.

A `3/3` result must not be presented as stronger evidence than a materially larger and validated sample merely because the percentage is 100%.

---

## 18. Objective market truth boundary

Strategy suitability claims concerning trade success must use the appropriate objective market outcome target.

Do not mix:

- MARKET_TRUTH;
- OPERATIONAL_TRUTH;
- COMMUNITY_TRUTH.

MISSED is not market LOSS.

Community votes are not strategy success labels.

Operational manual exits are not canonical expiry market outcomes unless explicitly analyzed as a separate target.

---

## 19. Temporal suitability versus execution timing

Trading-window suitability and Execution Time are distinct.

Trading-window intelligence asks whether the broader temporal/contextual environment is historically suitable for a strategy.

Execution Time determines the governed trader-facing expiry/timing for a specific signal.

A favorable trading window cannot invent missing Execution Time calibration.

An unfavorable research finding cannot silently override canonical execution timing.

---

## 20. Owner/Admin presentation

Future operator surfaces should present evidence compactly, for example:

`Strategy temporal context: RESEARCH_ONLY / ADVISORY_FAVORABLE / ADVISORY_UNFAVORABLE`

with drill-down for:

- temporal bucket;
- market regime;
- sample counts;
- market baseline;
- strategy result;
- stability;
- validation status;
- version/provenance;
- authority mode.

Do not display a precise probability or 0–100 suitability score unless a separately validated model/score authority exists.

---

## 21. Relationship to Strategy Intelligence

This document defines a bounded specialized subsystem within the broader Strategy Intelligence mission.

Strategy Intelligence may summarize trading-window evidence and route recommendations.

It must preserve:

- strategy identity;
- temporal/context identity;
- baseline;
- sample;
- confidence/validation state;
- authority mode.

---

## 22. Relationship to Research and Learning

Research owns the scientific transition from descriptive observation to validated finding.

Trading-window intelligence may consume only appropriately qualified research results for advisory status.

A raw analytics difference remains `RESEARCH_ONLY` until validation requirements are met.

---

## 23. Relationship to Autonomous Evolution

Autonomous Evolution may later package a validated temporal finding into a proposal for bounded experimentation.

It may not directly activate a temporal gate.

Owner/governance approval remains mandatory.

---

## 24. Anti-overfitting rules

Forbidden:

- searching hundreds of time/context combinations and presenting only the best one without multiple-testing context;
- choosing time buckets after seeing outcomes and treating them as predeclared rules;
- using the same data for discovery and final proof without disclosure;
- ignoring months/regimes where the pattern fails;
- treating a high historical win rate as guaranteed future performance;
- applying one strategy's result to another strategy;
- combining incompatible strategy versions;
- silently optimizing thresholds to fit a temporal pocket.

---

## 25. No automatic strategy mutation

Initial and advisory temporal intelligence may not automatically:

- change PRE/CONFIRM/OPEN thresholds;
- modify TPS weights/caps;
- modify SR/corridor requirements;
- modify Execution Time calibration;
- change active symbols;
- change provider;
- force OPEN_NOW;
- suppress OPEN_NOW as a live rule;
- enable broker execution.

Any future temporal live gate is a separate governed change.

---

## 26. Implementation sequence after activation

1. Ensure Market Behavior Observation is collecting replayable evidence.
2. Ensure Temporal Market Behavior Analytics produces unconditional/matched baselines.
3. Join strategy decisions/outcomes by explicit time/symbol/version context.
4. Produce strategy-specific temporal descriptive reports.
5. Add direction/regime/score/TPS segmentation.
6. Route candidate advantages/disadvantages to Temporal Pattern Validation.
7. Keep authority mode `OBSERVE`.
8. Promote only validated findings to `ADVISORY` through governance.
9. Build Owner/Admin visibility.
10. Consider `GOVERNED_GATE` only through a future separate canon/change request.

---

## 27. Validation requirements

At minimum prove:

1. one temporal bucket can have different suitability states for different strategies;
2. BUY and SELL can remain separate;
3. strategy performance is compared with an unconditional/matched market baseline;
4. objective outcome truth is not mixed with community/operational truth;
5. sample counts and missingness are visible;
6. incompatible strategy versions are not silently aggregated;
7. observed patterns cannot skip Research/Temporal Pattern Validation;
8. advisory mode cannot mutate or block live strategy;
9. drift can downgrade a previously favorable finding;
10. broker execution remains unchanged.

---

## 28. Final principle

The correct trading question is not only:

**Is there a technically valid setup?**

It is eventually:

**Is there a technically valid setup in a market/time context where this exact strategy has a validated, stable and measurable advantage over the relevant baseline?**

The project must earn that second answer from data before it is allowed to influence production.
