# TEMPORAL_MARKET_BEHAVIOR_ANALYTICS_SPEC_v1.0.0

Canonical Name: TEMPORAL_MARKET_BEHAVIOR_ANALYTICS_SPEC  
Version: 1.0.0  
Status: TRANSITIONAL CANONICAL CANDIDATE — OWNER-DIRECTED — NOT ACTIVE UNTIL MASTER INDEX ACTIVATION  
Owner: BinaryBot / DROPi Signals  
Date: 2026-09-05  
Scope: Time-conditioned analysis of continuous market behavior, rhythm/frequency/sequence discovery, regime-aware temporal baselines, research-only pattern candidates

Linked active authorities:
- `CANONICAL_MASTER_INDEX_v2.0.0.md`
- `PERFORMANCE_ANALYTICS_SPEC_v3.0.0.md`
- `RESEARCH_AND_LEARNING_FRAMEWORK_SPEC_v3.0.0.md`
- `STRATEGY_INTELLIGENCE_SYSTEM_v3.0.0.md`
- `SYSTEM_INVARIANTS_v3.0.0.md`

Linked transitional candidates:
- `MARKET_BEHAVIOR_OBSERVATION_SPEC_v1.0.0.md`
- `STRATEGY_TRADING_WINDOW_INTELLIGENCE_SPEC_v1.0.0.md`
- `TEMPORAL_PATTERN_VALIDATION_SPEC_v1.0.0.md`

Governance issue: `#137`

---

## 0. Authority status

This document defines a missing temporal analytics domain requested by the Owner.

It is transitional until explicit Master Index activation.

It does not itself authorize runtime strategy influence, signal blocking, parameter mutation, provider changes, broker execution, or claims of predictive certainty.

---

## 1. Purpose

Temporal Market Behavior Analytics studies whether objective price behavior changes systematically with time and context.

It must analyze the market itself, not only the outcomes of our signals.

The primary questions are:

- Does EUR/USD or another governed symbol behave differently at different UTC hours?
- Does behavior differ by weekday, month, quarter or recurring calendar context?
- Do directional persistence, reversal frequency, range, volatility and sequence transitions show repeatable temporal structure?
- Do some temporal patterns survive across rolling windows and market regimes?
- Does the apparent time pattern remain after controlling for volatility, trend, structure or direction?
- Are there recurring behavior sequences that materially differ from the unconditional market baseline?

Temporal regularity is a hypothesis to be measured, not assumed.

---

## 2. Canonical position

Input authority:

`MARKET_BEHAVIOR_OBSERVATION_SPEC_v1.0.0`

Downstream consumers may include:

- Research and Learning;
- Strategy Trading Window Intelligence;
- Strategy Intelligence;
- future governed statistical/model systems.

Performance Analytics remains the authority for strategy/system performance. This document is the authority candidate for **unconditional and context-conditioned market behavior analytics**.

---

## 3. Fundamental separation

The system must maintain at least two distinct analytical questions:

### 3.1 Market behavior question

**What does price tend to do in this temporal/contextual condition, regardless of our strategy?**

### 3.2 Strategy performance question

**How does Strategy X perform when it acts in this temporal/contextual condition?**

The first belongs here.

The second belongs to Performance Analytics plus Strategy Trading Window Intelligence.

These must never be collapsed into one unlabeled metric.

---

## 4. Canonical time dimensions

UTC is the base authority.

Analytics must support segmentation by at least:

- UTC hour of day: 0–23;
- minute bucket where justified;
- weekday;
- day of month;
- ISO week number;
- week-of-month derived under an explicit definition if used;
- month;
- quarter;
- year.

Derived timezone/session views may include `Europe/London` or other explicit IANA zones, but must preserve:

- original UTC timestamp;
- timezone identifier;
- daylight-saving-safe derivation;
- derivation/version context.

Session labels must use an explicit session definition. They may not be guessed from informal market folklore.

---

## 5. Required interaction dimensions

Single-dimensional averages are insufficient.

The analytics system must support combinations such as:

- hour × weekday;
- hour × month;
- weekday × month;
- hour × direction/state;
- hour × volatility regime;
- hour × trend regime;
- hour × noise/chop regime;
- hour × structural/corridor regime;
- weekday × volatility regime;
- weekday × trend regime;
- month × volatility regime;
- temporal bucket × behavior-sequence class.

Higher-order interactions may be explored only with explicit sample-size and multiple-testing discipline.

---

## 6. Required behavior domains

Temporal analysis must be able to characterize at least:

### 6.1 Movement magnitude

- price displacement distributions;
- pip-equivalent displacement where defined;
- percentage/log-return distributions where appropriate;
- high-low range;
- close-to-close movement;
- median, mean and selected quantiles.

### 6.2 Volatility and range rhythm

- realized range/volatility by temporal bucket;
- compression frequency;
- expansion frequency;
- expansion after compression;
- volatility acceleration/deceleration;
- time-of-day volatility profile;
- weekday/month stability of those profiles.

### 6.3 Directional persistence

- same-direction run frequency;
- run duration distribution;
- run magnitude distribution;
- continuation probability after formally defined states;
- directional transition matrix.

### 6.4 Reversal behavior

- reversal frequency;
- time to first reversal;
- reversal magnitude;
- reversal after extension;
- reversal after failed breakout;
- persistence-versus-reversal balance.

### 6.5 Impulse / pullback behavior

- impulse frequency;
- impulse duration/magnitude;
- pullback frequency;
- pullback depth/duration;
- impulse/pullback ratio;
- continuation after pullback.

### 6.6 Breakout behavior

Where a versioned boundary exists:

- breakout frequency;
- continuation after breakout;
- retest frequency;
- false-break frequency;
- average favorable/adverse excursion after breakout.

### 6.7 Structural reaction behavior

Where versioned structural evidence exists:

- price reaction near support/resistance/corridor boundaries;
- bounce versus penetration frequency;
- approach speed;
- repeated-test behavior;
- reaction duration and magnitude.

---

## 7. Analysis horizons

Behavior must be analyzable over multiple future horizons when source cadence permits.

Candidate horizons include:

- 30 seconds;
- 1 minute;
- 2 minutes;
- 5 minutes;
- 10 minutes;
- 15 minutes;
- 30 minutes;
- 60 minutes.

Shorter horizons such as 2s/10s may be analyzed only if the raw observation cadence genuinely supports them.

Each horizon is a separate target/view. Results for one horizon must not be generalized to another without evidence.

---

## 8. Distribution-first rule

Temporal analytics must not rely only on averages.

For each relevant metric/bucket, preserve where appropriate:

- sample count;
- mean;
- median;
- quantiles;
- dispersion;
- skew/asymmetry indicators where justified;
- min/max only when meaningful and not misleading;
- missing/incomplete sample count;
- data-quality state.

Averages can hide bimodal, fat-tailed or regime-dependent behavior.

---

## 9. Baseline comparisons

Every temporal claim must identify its baseline.

At minimum support:

### 9.1 Unconditional baseline

All valid observations in the declared dataset/window.

### 9.2 Time-matched baseline

The same metric in comparable time buckets.

### 9.3 Regime-matched baseline

The same metric under comparable volatility/trend/structure regimes.

### 9.4 Direction/state-matched baseline

Comparable pre-anchor directional state where applicable.

A temporal bucket must not be declared unusual merely because it contains a different market-regime mix.

---

## 10. Rolling temporal windows

Analytics must support rolling-window views so temporal behavior can be checked for persistence or drift.

Useful descriptive windows may include:

- recent 7 days;
- 30 days;
- 90 days;
- 180 days;
- 365 days;
- all available history.

These are reporting windows, not canonical minimum proof thresholds.

Exact evidence sufficiency is governed by Temporal Pattern Validation / Research requirements.

---

## 11. Cross-window stability

For any candidate temporal behavior, measure whether the effect:

- persists in recent and older windows;
- changes sign;
- weakens materially;
- depends on one month/session/regime;
- appears only because of one exceptional event cluster;
- survives provider/version boundaries.

Required stability labels may include descriptive states such as:

- INSUFFICIENT_DATA;
- OBSERVED;
- UNSTABLE;
- RECURRING;
- DEGRADING;
- DRIFTED;

These labels are descriptive research states, not live trading authority.

---

## 12. Sequence analytics

The system must support analysis of deterministic pre-anchor sequence classes.

Example research questions:

- after N same-direction candles, what is the future displacement distribution?
- after compression followed by expansion, how often does continuation occur?
- after breakout and retest, what is the future path distribution?
- after a large extension relative to recent volatility, how frequently does mean reversion occur?
- after alternating/choppy transitions, how long does choppiness persist?

Sequence classes must be versioned and defined before future outcomes are inspected for classification.

No hindsight-defined pattern is valid evidence.

---

## 13. Transition matrices

Where market states are versionedly defined, analytics may build transition matrices such as:

`UP -> UP / DOWN / FLAT`

`LOW_VOL -> LOW_VOL / NORMAL_VOL / HIGH_VOL`

`COMPRESSION -> COMPRESSION / EXPANSION`

`BREAKOUT -> CONTINUATION / RETEST / FAILURE`

Each matrix must state:

- state definitions;
- interval/horizon;
- sample count;
- observation window;
- provider/version scope.

A transition frequency is not automatically a calibrated prediction probability.

---

## 14. Temporal pattern candidate output

Analytics may emit **pattern candidates** for Research.

A candidate should include:

- pattern/candidate id;
- symbol;
- source provider/version;
- temporal bucket(s);
- pre-anchor behavior definition;
- market regime context;
- target horizon;
- observed distribution;
- baseline distribution;
- effect size or difference summary;
- sample count;
- data-quality state;
- time windows compared;
- stability summary;
- derivation/code version;
- status `RESEARCH_ONLY`.

A pattern candidate is not a strategy rule.

---

## 15. Example analytical output semantics

A valid descriptive statement may be:

> Under detector version X, EUR/USD observations matching context C during Tuesday 09:00–10:00 UTC showed a higher 5-minute continuation frequency than the matched baseline in the declared historical window, with sample N and stated uncertainty.

An invalid statement is:

> EUR/USD will go up Tuesday at 09:00.

The analytics system describes measured distributions and conditional frequencies, not certainty.

---

## 16. Calendar-pattern caution

Calendar patterns are especially vulnerable to false discovery.

The system must assume that apparent hour/day/month effects may be caused by:

- regime mix;
- macro-event concentration;
- provider coverage differences;
- daylight-saving/session shifts;
- structural market changes;
- limited sample size;
- repeated hypothesis testing;
- one exceptional period.

Therefore no calendar effect becomes a strategy influence without Temporal Pattern Validation.

---

## 17. Macro/news boundary

This document does not define a macroeconomic-news feed.

If future research correlates temporal behavior with scheduled news/events, those events require their own objective source/provenance authority.

Do not infer a news cause merely from a timestamp pattern.

---

## 18. Strategy-selection-bias protection

Temporal Market Behavior Analytics must be runnable on all valid observations, not only:

- OPEN_NOW signals;
- high-score decisions;
- profitable outcomes;
- watchlist periods;
- hand-selected chart examples.

The unconditional market dataset is mandatory for a valid baseline.

Strategy-conditioned slices may be added later and must remain explicitly labeled.

---

## 19. Version awareness

Every temporal analytical result must be attributable to:

- raw market dataset/version or deterministic extraction window;
- provider identity/version boundary where available;
- market-observation spec version;
- behavior-feature/detector version;
- timezone/session derivation version;
- analysis code/version;
- start/end timestamps;
- symbol/timeframe/cadence.

Mixing incompatible derivations without labeling is forbidden.

---

## 20. Data quality and completeness

Each temporal bucket must expose enough evidence to distinguish:

- true low activity;
- missing data;
- stale feed;
- provider outage;
- cadence gap;
- incomplete future horizon;
- insufficient history.

Missing observations must not reduce a denominator silently.

---

## 21. Relationship to Performance Analytics

Performance Analytics asks how the strategy/system performed.

Temporal Market Behavior Analytics asks how the market behaved.

Performance Analytics may consume temporal market baselines to answer questions such as:

- does the strategy outperform the market's unconditional continuation rate in this hour?
- is a strategy loss cluster caused by strategy selection or a broader reversal-prone market period?

The market baseline remains distinct from strategy performance truth.

---

## 22. Relationship to Strategy Trading Window Intelligence

Strategy Trading Window Intelligence consumes validated or appropriately qualified temporal market behavior plus strategy-specific evidence.

This document does **not** declare a time favorable or unfavorable for a specific strategy.

It supplies the market-behavior side of that later comparison.

---

## 23. Relationship to Research and Learning

Research owns hypothesis testing and validation discipline.

Temporal analytics provides measurable candidates and reproducible evidence packages.

Research determines whether an observed temporal difference is:

- likely noise;
- confounded;
- unstable;
- replicated;
- out-of-sample validated;
- worthy of controlled strategy research.

---

## 24. No automatic influence

Initial authority mode after future activation:

`OBSERVATIONAL_RESEARCH_ONLY`

Temporal analytics may not automatically:

- increase/decrease score;
- change TPS;
- change SR/corridor rules;
- alter Execution Time;
- change strategy parameters;
- block a technically valid signal;
- force a signal;
- change provider;
- enable broker execution.

---

## 25. Forbidden patterns

Forbidden:

- declaring an hour/day/month favorable based on a few examples;
- hiding sample size;
- comparing temporal buckets with incompatible data quality;
- selecting only profitable periods;
- treating one rolling window as permanent law;
- using future data to define the pre-anchor pattern;
- confusing market movement frequency with strategy win rate;
- silently changing bucket/timezone definitions;
- presenting conditional frequency as certainty;
- automatically gating trades from an unvalidated pattern.

---

## 26. Implementation sequence after activation

1. Consume continuous Market Behavior Observation data.
2. Materialize UTC/timezone-safe calendar dimensions.
3. Compute basic movement/range/volatility distributions.
4. Add persistence/reversal/impulse/compression metrics.
5. Build hour/weekday/month and interaction matrices.
6. Add matched baselines and regime controls.
7. Add rolling-window stability views.
8. Add sequence/transition analytics.
9. Emit pattern candidates with full provenance.
10. Route candidates to Temporal Pattern Validation / Research.
11. Keep strategy influence disabled.

---

## 27. Validation requirements

At minimum prove:

1. analytics can run on market periods with zero strategy signals;
2. hour/weekday/month derivation is UTC-authoritative and DST safe;
3. missing/cadence-gap evidence is visible;
4. unconditional and regime-matched baselines are distinct;
5. results expose sample counts and window boundaries;
6. sequence classification uses only pre-anchor evidence;
7. future path is label/downstream evidence only;
8. rolling windows reveal instability/drift rather than hiding it;
9. strategy outcomes are not required to compute market behavior;
10. no temporal result mutates live strategy.

---

## 28. Final principle

Time may contain useful structure, but the system must **measure the market before judging the strategy**.

Canonical analytical chain:

`CONTINUOUS MARKET TRUTH -> TIME/REGIME SEGMENTATION -> BEHAVIOR DISTRIBUTIONS -> MATCHED BASELINES -> PATTERN CANDIDATES -> VALIDATION`.

Only after this chain is trustworthy may strategy-specific temporal suitability be evaluated.
