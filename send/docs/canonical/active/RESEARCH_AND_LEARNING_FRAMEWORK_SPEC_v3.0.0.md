# RESEARCH_AND_LEARNING_FRAMEWORK_SPEC_v3.0.0

Path: /opt/binarybot/docs/canonical/active/RESEARCH_AND_LEARNING_FRAMEWORK_SPEC_v3.0.0.md  
Version: 3.0.0  
Status: ACTIVE CANONICAL  
Owner: BinaryBot / DROPi Signals  
Scope: Evidence-led research, Trade Physics hypothesis/testing/model validation, experiment governance, learning without silent production mutation

Supersession intent: `RESEARCH_AND_LEARNING_FRAMEWORK_SPEC_v2.0.0.md`
Governance basis: Change ID `20260901-TRADE-PHYSICS-01`; merged PR #78

---

## 0. PROMOTION STATUS

Promotion status: ACTIVE CANONICAL under `CANONICAL_ACTIVATION_RECORD_20260901.md` and `CANONICAL_MASTER_INDEX_v2.0.0.md`.

---

## 1. PURPOSE

Research and Learning converts versioned runtime evidence into validated understanding, hypotheses, controlled experiments and governance-safe strategy/model improvement.

v3 makes Trade Physics a current research domain rather than a future-only idea.

Research must determine from real evidence:

- whether deterministic TPS adds measurable value;
- whether the proposed directional-speed model improves time feasibility;
- how S/T/P/V behave by regime;
- whether learned probability adds incremental value and is calibrated;
- which Trade Physics changes are safe to test or recommend.

---

## 2. CANONICAL POSITION

`Strategy -> DecisionObject -> FSM -> Execution -> Observability -> Telemetry -> Outcome -> Performance Analytics -> Research & Learning -> Strategy Intelligence / Autonomous Evolution / Governance`

Research does not create raw decision truth and cannot directly mutate production.

---

## 3. RESEARCH PHILOSOPHY

Research must be:

- evidence-led;
- version-aware;
- leakage-safe;
- truth-layer-aware;
- reproducible;
- confidence-rated;
- governed.

No strategic conclusion may be justified by isolated anecdotes, one streak or the existence of an AI model.

---

## 4. INPUT TRUTH DOMAINS

Research may consume:

- DecisionObject / Decision Audit;
- Trade Physics components/TPS/readiness;
- FSM and execution truth;
- objective telemetry;
- reconciled outcomes;
- Performance Analytics;
- observability/data-quality evidence;
- business/community evidence where separately labeled;
- model training/validation artifacts.

Every dataset must state source domain, version and derivation.

---

## 5. TRADE PHYSICS RESEARCH QUESTIONS

Mandatory questions include:

1. Does `space_to_buffer_ratio` correlate with objective outcome?
2. Does `trade_space_margin_atr` add value beyond corridor validity?
3. Does directional effective speed outperform gross speed for timing?
4. Are the 20-M1 linear recency weights appropriate?
5. Does `time_to_buffer_ratio` behave as expected?
6. Does movement stress identify unrealistic setups?
7. Are S/T/P/V caps well calibrated?
8. Do initial weights .35/.25/.20/.20 improve ranking?
9. Does TPS add value beyond classical score?
10. Which classical-score/TPS disagreement patterns are useful?
11. Does a learned model add incremental value beyond both baselines?
12. Is `trade_success_probability` calibrated and stable?

These are research questions, not pre-assumed truths.

---

## 6. HYPOTHESIS REGISTRY

Every meaningful Trade Physics change should link to a hypothesis containing:

- hypothesis id;
- title/category;
- rationale;
- evidence basis;
- affected formulas/parameters;
- symbols/sessions/regimes;
- expected effect;
- measurement plan;
- risk;
- minimum evidence target;
- approval status;
- conclusion.

Examples:

- directional speed reduces false temporal feasibility;
- S_cap 3.0 is too high/low for a regime;
- current TPS weights overemphasize space;
- learned probability improves calibration beyond TPS.

---

## 7. EVIDENCE CONFIDENCE

Findings must be confidence-rated considering:

- sample size;
- label quality;
- missingness;
- discrepancy contamination;
- version consistency;
- regime stability;
- repeatability;
- out-of-sample performance;
- calibration.

Small-sample findings must not be promoted to production truth merely because effect size looks large.

---

## 8. TRADE PHYSICS DATASETS

Datasets must retain:

- setup/candidate identity;
- decision-time feature values;
- Trade Physics version;
- strategy/DecisionObject/event schema versions;
- objective outcome link;
- truth-layer label;
- feature schema;
- model target version;
- inclusion/exclusion reason.

No single JSONL file becomes canonical truth by existence alone.

---

## 9. LEAKAGE AUDIT

Before training, research must verify that features do not contain future information.

Mandatory checks include:

- no outcome result in feature set;
- no post-entry checkpoint in decision-time feature;
- no future candle-derived feature;
- no later model/reconciliation rewrite of historical feature values;
- correct temporal split;
- stable setup identity.

Leakage failure invalidates model evidence.

---

## 10. TARGET / LABEL GOVERNANCE

Each learned target must be explicitly defined and versioned.

Possible targets include:

- objective market outcome at canonical expiry;
- target/buffer reach before expiry;
- payout-adjusted binary result under stated execution assumptions;
- operational outcome as a separate target.

Models trained for different targets must not share one ambiguous probability field without target metadata.

---

## 11. BASELINES

Every learned Trade Physics experiment must compare against at least:

- classical score baseline;
- deterministic TPS baseline;
- simple/naive baseline appropriate to the target.

A complex model must show incremental value rather than merely produce a higher-looking score.

---

## 12. MODEL EXPERIMENTS

Candidate model families may include the Gradient Boosted Tree approaches named by the source and other approved research models.

An experiment must record:

- model family;
- features;
- hyperparameters/config;
- training/validation windows;
- target;
- metrics;
- calibration;
- result;
- reproducibility artifacts.

No model experiment automatically becomes production model authority.

---

## 13. TIME-AWARE VALIDATION

Market data is temporal.

Validation should prefer chronological/out-of-sample approaches appropriate to the research question.

Research must document:

- train window;
- validation/test window;
- overlapping setup handling;
- retraining boundary;
- regime changes;
- symbol coverage.

Random shuffling alone is not accepted as sufficient proof for time-dependent deployment.

---

## 14. CALIBRATION RESEARCH

For `trade_success_probability`, research must examine:

- observed frequency by probability band;
- calibration error;
- overconfidence/underconfidence;
- calibration by symbol/session/regime;
- stability over time;
- recalibration methods.

An uncalibrated raw model score must not be promoted as probability.

---

## 15. DETERMINISTIC TPS EXPERIMENTS

Research may test:

- S/T/P caps;
- weights;
- directional-speed lookback;
- recency weighting profile;
- alternate volatility transforms;
- future policy thresholds;
- combined classical/TPS policies.

Each is a governed experiment. Current defaults remain canonical until changed through approved versioning/control.

---

## 16. DIRECTIONAL SPEED EXPERIMENT

Because the proposed canonical v3 Time Model materially changes speed semantics, research must maintain an explicit comparison:

Control:
- prior gross absolute speed logic.

Treatment:
- directional, linear-recency-weighted 20-M1 speed.

Measure:
- t_needed differences;
- time-state differences;
- rejection/promotion differences;
- signal volume;
- market-truth outcomes;
- symbol/session/regime effects;
- false-feasibility reduction.

This experiment/replay is mandatory evidence for deployment review.

---

## 17. EXPERIMENT LIFECYCLE

Use governed lifecycle:

`PROPOSED -> REVIEWED -> APPROVED -> STAGED -> RUNNING -> EVALUATED -> ACCEPTED / REJECTED / EXTENDED`

Every experiment requires:

- owner/reviewer;
- scope;
- change definition;
- success/failure criteria;
- rollback criteria;
- sample/evidence target;
- time window;
- final conclusion.

---

## 18. RESEARCH READINESS

Trade Physics research may be classified as:

- data collection only;
- research-ready;
- model-training-ready;
- validation-ready;
- recommend-only evidence;
- staged-experiment-ready;
- insufficient/invalid evidence.

Research readiness is distinct from model readiness and production rollout readiness.

---

## 19. MODEL READINESS REVIEW

Research provides evidence used to assign/review model states such as:

- UNTRAINED;
- INSUFFICIENT_DATA;
- TRAINED_UNVALIDATED;
- VALIDATED_RECOMMEND_ONLY;
- APPROVED_FOR_BOUNDED_USE;
- SUSPENDED_DRIFT.

Research must not set a high-authority state without the required governance approval.

---

## 20. FEATURE IMPORTANCE / INTERPRETATION

Feature importance may be analyzed, but it is not causal proof.

Research should compare:

- importance across folds/windows;
- stability by regime;
- redundancy/correlation;
- ablation results;
- incremental value.

Special attention is required for related features such as movement stress, buffer/ATR energy and V to avoid treating mathematically transformed duplicates as independent discoveries.

---

## 21. DRIFT RESEARCH

Research must localize:

- strategy drift;
- Trade Physics feature drift;
- model drift;
- label/base-rate drift;
- symbol/session drift;
- instrumentation drift;
- operational discrepancy drift.

A model problem must not automatically be diagnosed as a strategy problem.

---

## 22. RECOMMENDATION OUTPUT

Research may produce:

- finding;
- hypothesis;
- confidence-rated conclusion;
- experiment proposal;
- parameter/model recommendation;
- risk flag;
- rollback recommendation;
- instrumentation-first recommendation.

It does not apply production changes.

---

## 23. ANTI-ILLUSION RULES

Forbidden research conclusions include:

- “TPS is a probability” without calibration;
- “AI improves the strategy” without a baseline/out-of-sample comparison;
- “feature X causes wins” from feature importance alone;
- “weight should change” from one short window;
- “model is safe” while data leakage exists;
- “overall result is strong” while one regime dominates the sample;
- hiding failed experiments.

---

## 24. REPRODUCIBILITY

A research result must be reproducible from:

- dataset/version;
- feature schema;
- model/config;
- code/analysis version;
- windows;
- target definition;
- random seed where relevant;
- exclusion rules.

If the result cannot be reconstructed, it is not sufficient evidence for governance.

---

## 25. RELATION TO STRATEGY INTELLIGENCE

Research sends confidence-rated findings and experiment results to Strategy Intelligence.

Strategy Intelligence may translate them into operator-readable recommendations but must preserve the research evidence link.

---

## 26. RELATION TO AUTONOMOUS EVOLUTION

Autonomous Evolution consumes accepted/review-ready findings to propose staged changes.

Research remains responsible for evidence quality; Autonomous Evolution remains responsible for change proposal packaging/readiness.

Neither may silently bypass Owner approval.

---

## 27. FORBIDDEN PATTERNS

Forbidden:

- direct research-to-production mutation;
- unlabeled truth blending;
- future leakage;
- model without baseline comparison;
- hidden failed experiments;
- changing historical DecisionObjects during retrospective analysis;
- using current outcome label to alter decision-time features;
- treating intake expectations as empirical proof.

---

## 28. VALIDATION REQUIREMENTS

At minimum:

1. hypothesis registry works for Trade Physics changes;
2. dataset lineage is complete;
3. leakage audit blocks invalid model experiments;
4. chronological validation is supported;
5. baselines include classical score and TPS;
6. calibration study is reproducible;
7. directional-speed control/treatment replay is available;
8. failed experiments remain recorded;
9. confidence/sample context reaches recommendation consumers;
10. research cannot mutate production directly.

---

## 29. FINAL PRINCIPLE

Trade Physics is current-scope, but its improvement loop remains scientific and governed:

`MEASURE -> HYPOTHESIZE -> TEST -> VALIDATE -> EXPLAIN -> RECOMMEND -> GOVERN`.

The project may learn continuously, but it must never confuse learning speed with permission to rewrite production truth.
