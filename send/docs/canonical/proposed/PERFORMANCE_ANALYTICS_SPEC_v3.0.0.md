# PERFORMANCE_ANALYTICS_SPEC_v3.0.0

Path: /opt/binarybot/docs/canonical/proposed/PERFORMANCE_ANALYTICS_SPEC_v3.0.0.md  
Version: 3.0.0  
Status: PROPOSED COMPLETE SUCCESSOR — NOT ACTIVE CANONICAL  
Owner: BinaryBot / DROPi Signals  
Scope: Multi-truth performance analytics, Trade Physics effectiveness, model calibration, drift, segmentation, evidence for research/governance

Supersession intent: `PERFORMANCE_ANALYTICS_SPEC_v2.0.0.md`
Governance basis: Change ID `20260901-TRADE-PHYSICS-01`; merged PR #78

---

## 0. PROMOTION STATUS

Until explicit promotion, v2.0.0 remains authoritative. This document does not authorize code or strategy mutation.

---

## 1. PURPOSE

Performance Analytics measures, compares, explains and monitors system performance across the full signal lifecycle while preserving distinct truth layers.

v3 adds first-class Trade Physics analytics so the project can determine from evidence whether:

- deterministic TPS adds value beyond classical score;
- its S/T/P/V components are useful;
- directional-speed time modeling improves decisions;
- structural-space constraints are protective;
- learned `trade_success_probability` is calibrated and stable;
- Trade Physics policy changes deserve governed experimentation.

---

## 2. CANONICAL POSITION

Analytics is downstream of:

- strategy/DecisionObject;
- FSM;
- signal execution;
- observability;
- telemetry;
- outcome reconciliation.

It is upstream of:

- Research/Learning;
- Strategy Intelligence;
- Autonomous Evolution;
- governance decisions.

Analytics does not produce or mutate the live decision.

---

## 3. TRUTH LAYERS

Mandatory separation remains:

1. Decision truth
2. Market truth
3. Signal/execution truth
4. Distribution truth
5. Operational/admin truth
6. Community truth
7. Business truth
8. Research/model truth

Trade Physics analytics must state which outcome truth is being used.

---

## 4. CORE PERFORMANCE DOMAINS

Analytics must cover at least:

- signal production/funnel;
- rejection/stage-of-death;
- decision quality;
- market outcomes;
- operational outcomes;
- segmented performance;
- expectancy/economic context;
- drift/stability;
- parameter/experiment impact;
- Trade Physics effectiveness;
- learned-model calibration/readiness;
- business/UX where applicable.

---

## 5. DECISION QUALITY ANALYTICS

Track at minimum:

- classical score distributions;
- TPS distributions;
- Trade Physics readiness/missingness;
- score/TPS disagreement;
- structural-space blocker counts;
- directional-speed/time blocker counts;
- S/T/P/V distributions;
- hard-blocker frequency;
- promoted/rejected outcomes by score and TPS bands.

The purpose is to understand selection behavior, not merely count final wins.

---

## 6. TRADE PHYSICS EFFECTIVENESS

Required questions:

- Does higher TPS correspond to better objective market outcomes?
- Is that relationship monotonic/stable?
- Which TPS bands are useful or misleading?
- Which component S/T/P/V has predictive value?
- Does `trade_space_margin_atr` add information beyond corridor validity?
- Does directional effective speed improve timing quality versus gross speed?
- Does movement stress identify unrealistic setups?
- Does TPS improve ranking beyond classical score?

No source-document expectation may be treated as proven until analytics supports it.

---

## 7. TPS BAND ANALYTICS

The deterministic source interpretation bands are:

- <30;
- 30–50;
- 50–65;
- 65–80;
- >=80.

Analytics may use these initial descriptive bands, but must not conclude they are optimal lifecycle thresholds.

Track per band:

- setup count;
- promotion rate;
- market-truth outcome rate;
- expectancy where meaningful;
- average excursion/path quality;
- rejection/blocker mix;
- symbol/session/regime breakdown.

---

## 8. CLASSICAL SCORE VS TPS MATRIX

Analytics must preserve a two-dimensional view such as:

- high classical / high TPS;
- high classical / low TPS;
- low classical / high TPS;
- low classical / low TPS;
- TPS unavailable.

This matrix is a core prerequisite before any future combined-score formula or TPS lifecycle threshold.

---

## 9. COMPONENT ANALYTICS

Analyze at minimum:

### Space

- available space;
- required space;
- space-to-buffer ratio;
- trade-space margin ATR;
- S component.

### Time

- directional speed;
- t_needed/t_needed_adjusted;
- model expiry;
- time ratios;
- T component.

### Flow/speed

- weighted gross speed;
- directional effective speed;
- flow efficiency;
- directional speed ratio;
- P component.

### Volatility realism

- movement stress;
- V component.

Analytics must detect redundant features/double counting rather than assume every metric contributes independently.

---

## 10. DIRECTIONAL SPEED MIGRATION ANALYTICS

Because proposed Time Model v3 changes `t_needed` from gross absolute speed to directional effective speed, replay and post-implementation analytics must compare:

- old gross-speed t_needed;
- new directional-speed t_needed;
- time-state changes;
- signal-volume changes;
- rejection changes;
- market-truth outcome changes;
- changes by direction/symbol/session/regime.

This comparison is mandatory before claiming improvement.

---

## 11. MARKET TRUTH ANALYTICS

Objective post-decision/post-emission evidence may include:

- expiry result;
- favorable/adverse excursion;
- target/buffer reach;
- time-to-target;
- time-to-failure;
- path efficiency/stability;
- false-start/reversal character.

Trade Physics quality claims should primarily use objective market truth where the target definition requires it.

---

## 12. OPERATIONAL TRUTH ANALYTICS

Track separately:

- WIN/LOSE/MISSED or equivalent reconciled outcomes;
- execution/missed rate;
- corrections/overrides;
- discrepancy rate versus telemetry.

Operational truth may reveal usability issues but must not silently become model-label truth.

---

## 13. SEGMENTATION

Trade Physics analytics must segment by relevant dimensions including:

- symbol;
- direction;
- timeframe;
- session;
- weekday;
- volatility regime;
- trend regime;
- corridor regime;
- noise state;
- buffer mode;
- classical score band;
- TPS band;
- readiness state;
- model version;
- probability band where valid.

Aggregate results alone are insufficient.

---

## 14. LEARNED PROBABILITY ANALYTICS

When a valid model exists, track:

- `trade_success_probability` distribution;
- observed outcome rate by probability bin;
- calibration error;
- ranking/discrimination metrics;
- model-versus-TPS baseline;
- model-versus-classical-score baseline;
- incremental value;
- error by symbol/session/regime;
- model readiness state;
- inference missing/error rate.

A probability that is not calibrated must not be presented as reliable certainty.

---

## 15. MODEL CALIBRATION

Calibration views must compare predicted probability to observed target frequency under the exact target-label definition.

Track over time and by segment.

Material overconfidence/underconfidence must surface to Strategy Intelligence and may trigger `SUSPENDED_DRIFT` or research review according to the model contract.

---

## 16. MODEL DRIFT

Track drift in:

- input feature distributions;
- S/T/P/V;
- TPS;
- label base rate;
- calibration;
- discrimination/ranking;
- missingness;
- symbol/session mix;
- strategy/canonical version.

Model drift is not identical to strategy drift and must be labeled separately.

---

## 17. STRATEGY DRIFT

Continue to monitor rolling-window drift in:

- signal frequency;
- funnel conversion;
- rejection rates;
- classical score calibration;
- TPS/outcome relationship;
- expectancy;
- drawdown/loss clusters;
- time/space blocker distribution;
- operational discrepancy.

---

## 18. REJECTION ANALYTICS

Track rejection counts/rates by reason and stage, including Trade Physics-capable reasons:

- structural-space insufficient;
- directional barrier unavailable;
- time infeasible;
- directional speed unavailable;
- Trade Physics not ready;
- unstable market;
- classical score failure;
- downstream focus/FSM/execution/distribution reasons separately.

Research should be able to ask whether a rejection is protective or overly harsh.

---

## 19. LIFECYCLE CONVERSION

Track at minimum:

`CANDIDATE -> STRATEGY EVALUATED -> PRE -> CONFIRM -> OPEN_NOW -> EXECUTION/DISTRIBUTION -> TELEMETRY -> OUTCOME -> ANALYTICS`

Do not mix a strategy drop with an execution/distribution drop.

Trade Physics should be analyzable by stage of death.

---

## 20. EXPECTANCY

Where expectancy is computed, it must state:

- truth layer;
- payout/execution assumptions;
- symbol/session/score/TPS segment;
- sample size/window.

TPS itself is not profit expectancy.

---

## 21. PARAMETER IMPACT

Any experiment/tuning involving Trade Physics must support before/after or control/treatment analysis for:

- deterministic weights;
- caps;
- speed lookback/recency profile;
- future TPS policy thresholds;
- model features/hyperparameters;
- calibration method.

Analysis must include side effects on signal volume, blockers and other truth layers.

---

## 22. SAMPLE AND CONFIDENCE DISCIPLINE

Analytics must expose sample counts and confidence/uncertainty sufficient for Research/Learning to assess evidence.

Small samples must not be visually presented as equivalent to stable evidence.

Exact proof thresholds remain governed by Research/Statistical Proof canon.

---

## 23. DATA QUALITY

Analytics must track:

- missing Trade Physics fields;
- mismatched strategy/schema versions;
- missing outcomes;
- telemetry gaps;
- model inference failures;
- duplicate identities;
- invalid ATR/speed/structure evidence.

Poor data quality must be distinguishable from poor strategy performance.

---

## 24. REPORTS / DASHBOARDS

Trade Physics analytics surfaces should support:

- TPS health summary;
- score/TPS matrix;
- component bottlenecks;
- directional-time comparison;
- symbol/session heatmaps;
- model calibration/drift;
- not-ready/missing evidence;
- experiment impact;
- recommendations linked to evidence.

Views must label truth layer and versions.

---

## 25. RESEARCH / INTELLIGENCE OUTPUT

Analytics may generate evidence packages for Research/Intelligence but must not directly change strategy.

Outputs should include:

- finding;
- metrics/window/sample;
- segment;
- confidence indicators;
- version context;
- suspected cause;
- recommended research question.

---

## 26. FORBIDDEN PATTERNS

Forbidden:

- declaring TPS a calibrated probability based only on score bands;
- using operational/community outcome as unlabeled objective target;
- hiding sample size;
- aggregating incompatible strategy/model versions without labels;
- future information in decision-time feature analytics;
- model metric reported without model id/readiness;
- analytics silently mutating parameters;
- one overall win rate replacing component/segment analysis.

---

## 27. VALIDATION REQUIREMENTS

At minimum:

1. every TPS analytics row links to the exact DecisionObject/version;
2. market/operational truth remain distinct;
3. component calculations match decision-time values;
4. score/TPS disagreement matrix is reproducible;
5. directional-speed migration replay is available;
6. model calibration bins use the declared target;
7. drift is model-version-aware;
8. missing data rates are visible;
9. experiment analytics are attributable;
10. no analytics action directly mutates production.

---

## 28. FINAL PRINCIPLE

Trade Physics becomes valuable only if the project can prove what it adds.

Performance Analytics therefore treats TPS and learned probability as measurable hypotheses against real truth, not as magic scores.

The required evidence chain is:

`Decision-time Trade Physics -> Objective/Operational Outcomes -> Segmented Analytics -> Research -> Governed Improvement`.
