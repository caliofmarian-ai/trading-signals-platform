# TEMPORAL_PATTERN_VALIDATION_SPEC_v1.0.0

Canonical Name: TEMPORAL_PATTERN_VALIDATION_SPEC  
Version: 1.0.0  
Status: TRANSITIONAL CANONICAL CANDIDATE — OWNER-DIRECTED — NOT ACTIVE UNTIL MASTER INDEX ACTIVATION  
Owner: BinaryBot / DROPi Signals  
Date: 2026-09-05  
Scope: Statistical/research validation discipline for temporal market-behavior and strategy trading-window patterns, anti-overfitting controls, chronological validation, stability/drift and promotion boundaries

Linked active authorities:
- `CANONICAL_MASTER_INDEX_v2.0.0.md`
- `PERFORMANCE_ANALYTICS_SPEC_v3.0.0.md`
- `RESEARCH_AND_LEARNING_FRAMEWORK_SPEC_v3.0.0.md`
- `STRATEGY_INTELLIGENCE_SYSTEM_v3.0.0.md`
- `AUTONOMOUS_STRATEGY_EVOLUTION_SYSTEM_v3.0.0.md`
- `GOVERNANCE_AND_CHANGE_CONTROL_v2.0.1.md`
- `STRATEGY_PARAMETER_CONTROL_SPEC_v3.0.0.md`
- `SYSTEM_INVARIANTS_v3.0.0.md`

Linked transitional candidates:
- `MARKET_BEHAVIOR_OBSERVATION_SPEC_v1.0.0.md`
- `TEMPORAL_MARKET_BEHAVIOR_ANALYTICS_SPEC_v1.0.0.md`
- `STRATEGY_TRADING_WINDOW_INTELLIGENCE_SPEC_v1.0.0.md`

Governance issue: `#137`

---

## 0. Authority status

This document defines the validation boundary required before temporal market patterns or strategy trading windows may be treated as durable research findings or considered for future production influence.

It is transitional until explicit activation.

It does not define fixed universal p-value, sample-size or confidence thresholds. Such thresholds must be justified by the exact research target and any future statistical-proof authority rather than invented here.

---

## 1. Purpose

Markets contain noise, regime changes and many opportunities for accidental correlations.

If the project searches across:

- 24 hours;
- 5 weekdays;
- 12 months;
- multiple directions;
- many volatility/trend regimes;
- score/TPS bands;
- many price sequences;
- many future horizons;

then some apparently excellent patterns will arise by chance.

This document exists to prevent the system from turning those accidental patterns into trading rules.

The governing question is:

**What evidence is required before an observed temporal pattern is allowed to become a validated research finding, advisory intelligence, or future governed strategy gate?**

---

## 2. Canonical position

Input candidates may come from:

- Temporal Market Behavior Analytics;
- Performance Analytics;
- Strategy Trading Window Intelligence;
- Research experiments;
- replay/backtest analysis.

Validated outputs may flow to:

- Research and Learning;
- Strategy Intelligence;
- Autonomous Evolution proposal packaging;
- Owner/governance review.

No output flows directly to live strategy authority.

---

## 3. Pattern classes

This document applies to at least:

### 3.1 Calendar/time patterns

- hour-of-day effect;
- weekday effect;
- month/quarter effect;
- hour × weekday;
- hour × month;
- weekday × month;
- session/timezone-derived effects.

### 3.2 Market-behavior patterns

- directional persistence;
- reversal tendency;
- impulse/pullback sequences;
- compression/expansion;
- breakout/retest/failure;
- extension/mean-reversion;
- state-transition patterns.

### 3.3 Strategy-conditioned patterns

- favorable/unfavorable hours for Strategy X;
- direction-specific trading windows;
- regime-conditioned strategy windows;
- score/TPS/time interactions;
- pattern-conditioned strategy performance.

### 3.4 Learned/model-discovered patterns

Any machine-learned or AI-assisted temporal relationship remains subject to the same evidence, leakage, validation and governance requirements.

---

## 4. Required pattern identity

Every candidate must have a stable pattern definition containing at minimum:

- pattern id;
- pattern version;
- owner/research source;
- symbol(s);
- provider/data provenance;
- strategy/version if strategy-conditioned;
- pre-anchor feature definition;
- temporal bucket definition;
- timezone authority;
- market-regime/context definition;
- direction if relevant;
- target/future horizon;
- target-label definition;
- discovery dataset/window;
- code/detector version;
- inclusion/exclusion rules.

A pattern definition cannot be silently edited after seeing validation results. A material definition change creates a new pattern version.

---

## 5. Candidate lifecycle

Temporal patterns should use a governed lifecycle such as:

`DISCOVERED -> DESCRIPTIVE -> REPLICATION_PENDING -> REPLICATED -> OUT_OF_SAMPLE_VALIDATED -> STABLE_RESEARCH_FINDING -> GOVERNANCE_ELIGIBLE`

Failure states include:

- `INSUFFICIENT_DATA`;
- `INVALID_DATA`;
- `CONFOUNDED`;
- `NOT_REPLICATED`;
- `OUT_OF_SAMPLE_FAILED`;
- `UNSTABLE`;
- `DRIFTED`;
- `INVALIDATED`;
- `SUSPENDED`.

None of the positive states automatically grants live strategy authority.

---

## 6. Discovery versus proof separation

The dataset used to discover a pattern must not be silently reused as its sole final proof.

At minimum distinguish:

- discovery window;
- replication window;
- out-of-sample validation/test window.

When data is scarce, a walk-forward or other chronologically valid research design may be used, but the reuse/overlap must be explicit.

An in-sample descriptive result is not out-of-sample validation.

---

## 7. Chronological validation

Market data is time-dependent.

Validation must respect chronology.

Preferred approaches include, as appropriate:

- fixed historical discovery followed by later validation;
- rolling/walk-forward evaluation;
- expanding-window evaluation;
- predeclared future holdout;
- blocked time-series validation.

Random shuffling alone is not sufficient evidence for a temporal trading pattern.

---

## 8. Overlapping-label protection

Future outcome horizons may overlap between neighboring observations.

For example, observations every minute with a 15-minute future target are not 15 independent samples per 15 minutes.

Validation must account for overlapping targets when estimating effective evidence strength.

Where appropriate, research should use:

- non-overlapping anchors;
- purged validation windows;
- embargo/separation periods;
- clustered/robust uncertainty methods;
- explicit effective-sample caveats.

The exact method must match the research target.

---

## 9. Sample-size discipline

Every finding must expose sample size.

Multiple sample counts may be required:

- raw observations;
- eligible observations;
- independent/non-overlapping observations where relevant;
- strategy evaluations;
- executable signals;
- finalized objective outcomes;
- validation-period observations.

No fixed universal `N` is declared by this document.

Instead, sample adequacy must consider:

- effect size;
- outcome base rate;
- dependence/overlap;
- number of tested hypotheses;
- regime coverage;
- stability across windows;
- target variance;
- data quality.

A tiny sample must remain explicitly insufficient even if its observed percentage is extreme.

---

## 10. Multiple-testing / data-snooping discipline

The system must record the search space used to discover temporal patterns.

If research tests many combinations, it must not report only the best result as if it had been the only hypothesis.

Required controls include at least one appropriate discipline such as:

- pre-registration/predefinition of a limited hypothesis family;
- separate untouched validation data;
- false-discovery-rate or family-wise correction where statistical testing is used;
- nested validation for model/parameter selection;
- explicit exploratory status until independent replication.

The chosen method must be recorded.

---

## 11. Effect-size requirement

Statistical significance alone is insufficient.

Every candidate must state a practical effect relative to an explicit baseline, such as:

- difference in continuation/reversal frequency;
- change in median future displacement;
- change in MFE/MAE distribution;
- strategy outcome difference versus matched baseline;
- funnel conversion difference;
- reduction/increase in adverse behavior.

A tiny but statistically detectable effect may still be irrelevant to trading decisions.

---

## 12. Baseline discipline

Pattern validation must identify the baseline being beaten or differed from.

Potential baselines include:

- unconditional market baseline;
- same-regime baseline;
- same-direction/state baseline;
- same strategy across all times;
- naive continuation/reversion baseline;
- current canonical strategy without temporal influence.

Changing the baseline after seeing results must be disclosed and may require a new pattern version.

---

## 13. Confidence and uncertainty

Validated outputs must include uncertainty appropriate to the metric.

Depending on the target, research may use:

- confidence intervals;
- bootstrap intervals compatible with temporal dependence;
- Bayesian credible intervals where governed;
- effect-size intervals;
- calibration error intervals;
- robust/clustered uncertainty methods.

The specific method must be recorded with version/provenance.

A point estimate alone must not be presented as certainty.

---

## 14. Stability across time

A temporal pattern intended for strategy use must demonstrate more than one favorable aggregate window.

Validation should examine:

- month-to-month behavior;
- quarter-to-quarter behavior where history permits;
- rolling-window behavior;
- pre/post-regime change behavior;
- recent versus long-history behavior;
- sign consistency;
- effect-size stability;
- sample stability.

A pattern driven by one exceptional month is not stable evidence.

---

## 15. Regime robustness and confounding

A calendar pattern may be a proxy for another market condition.

Validation must test plausible confounders such as:

- volatility/activity mix;
- trend regime;
- noise/chop regime;
- structural/corridor regime;
- direction;
- provider coverage;
- data-quality state;
- strategy-version changes;
- daylight-saving/session definition changes.

If the temporal effect disappears after matched-regime comparison, it must be labeled confounded or narrowed to the actual context.

---

## 16. Provider/version robustness

Patterns may be invalidated by data-source changes.

Every validation must preserve:

- provider identity;
- provider boundary dates;
- symbol normalization version;
- sampling/candle derivation version;
- feature/detector version.

A pattern discovered across mixed providers without explicit handling is degraded evidence.

---

## 17. Timezone and DST validation

For local/session patterns, validation must prove that calendar grouping is timezone-aware.

Checks must include:

- UTC source authority;
- IANA timezone identity;
- DST transition dates;
- repeated/missing local clock hours;
- session definition version.

A fixed-offset bug must not be mistaken for a market pattern.

---

## 18. Leakage prevention

Pre-anchor features may contain only evidence available at or before the anchor timestamp.

Forbidden leakage includes:

- future high/low inside a feature;
- future candle close;
- expiry outcome;
- future reversal label;
- post-signal checkpoints;
- later operator/community outcomes;
- detector definitions that use the future to decide whether the pre-anchor pattern existed.

Any leakage invalidates the affected finding.

---

## 19. Pattern detector freeze

Before out-of-sample validation, the material pattern detector must be frozen/versioned.

If the detector is tuned using validation results, the validation set has become part of model selection and can no longer serve as untouched final proof.

A further holdout or new future evidence is then required.

---

## 20. Strategy-specific validation

For Strategy Trading Window Intelligence, validation must be attributable to the exact strategy version.

A favorable temporal window for one strategy/version does not transfer automatically to:

- another strategy;
- a future major strategy version;
- another symbol;
- another direction;
- another timeframe.

Transfer requires independent evidence or an explicitly justified shared model.

---

## 21. Objective outcome authority

When validating strategy success, use the declared objective market target from Trade Temporal Telemetry or another explicitly governed market-truth target.

Do not silently use:

- community votes;
- operator MISSED status;
- manual later exit;
- unlabeled mixed outcome files.

Different targets produce different findings and must have distinct identity.

---

## 22. Probability boundary

Conditional historical frequency may be a descriptive estimator, but it is not automatically a calibrated forward probability.

To present a value as `probability` for live decision support, the system must additionally prove:

- target definition;
- out-of-sample calibration;
- discrimination/ranking value where applicable;
- model/version identity;
- readiness state;
- current drift state;
- scope validity.

No pattern result may claim certainty about the next price movement.

---

## 23. Drift and expiration

Validated patterns are not permanent truth.

Every validated/advisory pattern needs ongoing monitoring for:

- effect-size decay;
- sign reversal;
- calibration deterioration;
- regime dependence change;
- provider/data changes;
- strategy-version changes;
- sample-mix changes.

Possible states:

- STABLE;
- WEAKENING;
- DRIFTED;
- EXPIRED;
- SUSPENDED_PENDING_REVIEW.

A drifted pattern must lose advisory/live eligibility according to its authority mode.

---

## 24. Promotion to advisory intelligence

A pattern may become advisory only when:

- data quality is acceptable;
- definition is frozen/versioned;
- sufficient evidence exists for its target;
- discovery and validation are separated;
- effect is practically meaningful;
- out-of-sample evidence supports it;
- major confounding is addressed;
- time/regime stability is acceptable;
- uncertainty is exposed;
- current drift does not invalidate it;
- Owner/governance requirements are satisfied.

Advisory status still does not change the live strategy.

---

## 25. Promotion toward live strategy influence

Live temporal gating is a future, higher-authority change.

Before any temporal pattern can block, permit, weight or modify a signal, require at minimum:

1. validated research finding;
2. exact strategy/version scope;
3. exact temporal/context rule;
4. proof target and baseline;
5. out-of-sample validation;
6. current stability/drift review;
7. strategy-impact simulation/replay;
8. signal-volume impact;
9. risk analysis;
10. false-negative/opportunity-cost analysis;
11. parameter/control-plane classification;
12. Owner approval;
13. canonical specification/version change;
14. regression/acceptance tests;
15. staged/shadow deployment first;
16. rollback path.

No earlier lifecycle state can directly activate a production gate.

---

## 26. AI/automated discovery boundary

AI may help:

- search for patterns;
- cluster states;
- rank hypotheses;
- identify interactions;
- summarize evidence;
- propose validation plans.

AI may not:

- hide the number of hypotheses searched;
- invent market observations;
- declare its own finding validated;
- tune and validate on the same hidden dataset while claiming out-of-sample proof;
- directly modify production strategy.

AI-generated candidates start as exploratory research evidence.

---

## 27. Reproducibility

Every validated result must be reconstructable from:

- raw/derived dataset identity;
- provider/source boundaries;
- pattern definition/version;
- feature/detector version;
- strategy version if applicable;
- target definition;
- discovery/validation windows;
- inclusion/exclusion rules;
- statistical/analytical method;
- code/analysis version;
- relevant random seed if used.

If the result cannot be reconstructed, it is not governance-grade evidence.

---

## 28. Evidence report contract

A temporal validation report should state at minimum:

- pattern id/version;
- research question;
- status;
- source truth domains;
- discovery window/sample;
- validation window/sample;
- target/baseline;
- observed effect;
- uncertainty/confidence method;
- multiple-testing treatment;
- regime/confounder analysis;
- rolling/stability evidence;
- data-quality issues;
- leakage audit result;
- provider/version context;
- conclusion;
- limitations;
- recommended next state;
- authority explicitly `RESEARCH/ADVISORY`, not production unless separately governed.

---

## 29. Forbidden conclusions

Forbidden:

- `3/3 wins means this hour is best`;
- `this pattern always repeats`;
- `Tuesday causes price to rise` from temporal correlation;
- `historical 70% means the next trade has 70% probability` without calibrated model evidence;
- selecting the best of hundreds of tests without disclosure;
- hiding failed validation periods;
- using future data in pre-anchor features;
- promoting an in-sample finding directly to live strategy;
- keeping a drifted pattern active because it once worked;
- changing the pattern definition after validation without versioning.

---

## 30. Implementation sequence after activation

1. Create stable pattern registry/identity.
2. Capture discovery search-space metadata.
3. Implement chronological dataset splitting.
4. Add overlap/leakage guards.
5. Add baseline/effect-size reporting.
6. Add sample/uncertainty reporting.
7. Add rolling/regime stability analysis.
8. Add out-of-sample validation state machine.
9. Feed only qualified findings into advisory intelligence.
10. Keep live temporal gating disabled until separately promoted.

---

## 31. Validation requirements

At minimum prove:

1. discovery and final validation windows are distinguishable;
2. future data cannot enter pre-anchor features;
3. overlapping outcome windows are not treated naively as independent evidence;
4. search-space/multiple-testing context is recorded;
5. sample size and effect size are both visible;
6. unstable patterns cannot become advisory;
7. provider/timezone/strategy-version boundaries are preserved;
8. a failed out-of-sample test blocks promotion;
9. drift can suspend a previously validated pattern;
10. no validated pattern becomes live strategy authority without separate governance.

---

## 32. Final principle

The system should search aggressively for useful temporal structure but promote conclusions conservatively.

Canonical research chain:

`DISCOVER -> DEFINE -> FREEZE -> REPLICATE -> VALIDATE OUT OF SAMPLE -> TEST STABILITY -> ADVISE -> GOVERN -> ONLY THEN CONSIDER LIVE INFLUENCE`.

A pattern is valuable only when it survives the process designed to prove that it is not an illusion.
