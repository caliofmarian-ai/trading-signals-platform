# MARKET_BEHAVIOR_OBSERVATION_SPEC_v1.0.0

Canonical Name: MARKET_BEHAVIOR_OBSERVATION_SPEC  
Version: 1.0.0  
Status: TRANSITIONAL CANONICAL CANDIDATE — OWNER-DIRECTED — NOT ACTIVE UNTIL MASTER INDEX ACTIVATION  
Owner: BinaryBot / DROPi Signals  
Date: 2026-09-05  
Scope: Continuous objective market-price observation, raw evidence preservation, time/context derivation, behavior-feature materialization independent of signal production

Linked active authorities:
- `CANONICAL_MASTER_INDEX_v2.0.0.md`
- `OBSERVABILITY_SPEC_v3.0.0.md`
- `OBSERVABILITY_LOGGING_SPEC_v3.0.0.md`
- `EVENT_SCHEMA_SPEC_v3.0.0.md`
- `TRADE_TEMPORAL_TELEMETRY_SPEC_v3.0.0.md`
- `PERFORMANCE_ANALYTICS_SPEC_v3.0.0.md`
- `RESEARCH_AND_LEARNING_FRAMEWORK_SPEC_v3.0.0.md`
- `STRATEGY_INTELLIGENCE_SYSTEM_v3.0.0.md`
- `SYSTEM_INVARIANTS_v3.0.0.md`

Related transitional candidates:
- `TEMPORAL_MARKET_BEHAVIOR_ANALYTICS_SPEC_v1.0.0.md`
- `STRATEGY_TRADING_WINDOW_INTELLIGENCE_SPEC_v1.0.0.md`
- `TEMPORAL_PATTERN_VALIDATION_SPEC_v1.0.0.md`

Governance issue: `#137`

---

## 0. Authority status

This document captures an Owner-directed canonical gap discovered after the 2026-09-01 active-canon promotion.

It is deliberately transitional until explicit activation through the canonical governance process and Master Index update.

It does not itself authorize runtime implementation, provider expansion, strategy mutation, signal publication, broker execution, or automated temporal gating.

---

## 1. Purpose

The system must preserve enough objective market evidence to study **how price itself behaves through time**, even when no strategy candidate, PRE, CONFIRM or OPEN_NOW exists.

The purpose is to prevent the project from collecting only strategy-conditioned evidence and thereby losing information about:

- ordinary market movement;
- directional persistence;
- reversals;
- impulse and pullback structure;
- compression and expansion;
- volatility rhythms;
- range behavior;
- breakout and false-break behavior;
- support/resistance reactions;
- repeated price sequences;
- temporal regularities by hour, weekday, month and other calendar contexts;
- future comparison between unconditional market behavior and strategy-selected behavior.

The observation layer answers:

**What did the governed market feed objectively show, independent of whether our strategy liked it?**

---

## 2. Canonical position

The observation layer is upstream of temporal behavior analytics and independent from the strategy decision lifecycle.

Conceptual chain:

`Governed Market Provider -> Raw Market Observation -> Market Behavior Evidence -> Temporal Market Behavior Analytics -> Research / Strategy Trading Window Intelligence`

The strategy chain remains separate:

`Governed Market Provider -> Strategy -> DecisionObject -> FSM -> Signal Execution -> Trade Temporal Telemetry -> Outcomes -> Performance Analytics`

The two chains may later be joined by timestamp, symbol, provider/version and other explicit correlation fields, but one must never overwrite the other.

---

## 3. Truth-domain classification

This document creates an explicit **continuous market-observation truth** domain.

It is objective market evidence derived from the governed market-data provider.

It is not:

- strategy decision truth;
- signal truth;
- distribution truth;
- operational/admin truth;
- community truth;
- research conclusion;
- learned prediction;
- broker execution truth.

A derived market-behavior metric remains derived market evidence and must retain lineage to its source observations and derivation version.

---

## 4. Observation eligibility

Market-behavior observation is not conditional on a signal.

When the governed provider is active and valid market evidence is available for a governed symbol, the observation system may collect that evidence regardless of whether the strategy produces:

- NO_SIGNAL;
- REJECT;
- PRE;
- CONFIRM;
- OPEN_NOW;
- no strategy evaluation at all.

This independence is mandatory to avoid strategy-selection bias in later market-behavior research.

---

## 5. Market-provider authority

Only the currently governed market-data authority may supply canonical observations for a given evidence stream.

Rules:

1. Provider provenance is mandatory.
2. Provider streams must not be silently mixed.
3. Provider switching creates an explicit provenance boundary.
4. Symbol normalization must be explicit and deterministic.
5. Provider timestamps and observed timestamps must be preserved where available.
6. Missing market evidence remains missing; no provider fallback may fabricate continuity.
7. Any alternative provider comparison must be a separately labeled research dataset, not silent production fusion.

Current runtime provider policy remains governed elsewhere and is not modified by this document.

---

## 6. Canonical time basis

UTC is the authoritative temporal basis for all raw observations.

Each observation must preserve sufficient time evidence to reconstruct calendar and local/session projections.

Minimum canonical timing fields where available:

- source/provider timestamp;
- observation/ingest timestamp;
- UTC epoch timestamp;
- UTC ISO timestamp;
- sampling/candle interval identity;
- source timeframe where applicable.

Derived calendar fields may include:

- UTC hour;
- minute;
- weekday;
- day of month;
- ISO week;
- month;
- quarter;
- year.

Local or market-session projections are derived views, not replacements for UTC.

If `Europe/London` or another IANA timezone is projected, the timezone identifier and derivation/version context must be retained so daylight-saving transitions cannot silently corrupt historical grouping.

Fixed manual UTC offsets are not a valid long-term substitute for timezone-aware derivation.

---

## 7. Raw market evidence contract

The system should preserve the most primary usable evidence made available by the governed provider and permitted by provider/storage policy.

Depending on provider capability this may include:

- price updates/ticks;
- bid/ask where genuinely available;
- midpoint or provider-reported last price where genuinely available;
- M1 candles;
- M5 candles;
- higher-timeframe candles if separately governed;
- provider sequence/time metadata.

Raw observation records must distinguish the actual available price type. A last price must not be relabeled bid, ask or midpoint.

Minimum candle evidence:

- symbol;
- timeframe;
- open timestamp;
- open;
- high;
- low;
- close;
- provider/source identity;
- observation provenance;
- cadence/gap quality state where applicable.

Volume may be stored only if the provider supplies a defined meaningful volume field. Missing or synthetic volume must not be invented.

---

## 8. Sampling and cadence

Observation cadence must be explicit.

The system may preserve:

- provider-native updates;
- governed sampled price observations;
- canonical candle series;
- derived resampled views.

A derived sampling interval must never pretend to be provider-native.

For every derived metric, the required temporal cadence must be declared.

If the source data cannot support a requested horizon, the metric is unavailable rather than interpolated.

The existing candle cadence/gap integrity authority remains binding.

---

## 9. Gap and missing-data discipline

No missing price may be fabricated merely to make a smooth time series.

Forbidden unless separately governed by an explicitly non-truth analytical transformation:

- synthetic ticks inserted into raw evidence;
- linear price interpolation presented as market truth;
- silent forward-fill presented as observed price;
- treating multi-minute gaps as one-minute movement;
- collapsing weekend/provider gaps into normal continuous motion.

Every analysis window must be able to determine whether its required source evidence was complete enough for the metric being computed.

---

## 10. Core derived behavior metrics

The continuous observation layer must support deterministic, versioned derivation of market-behavior features without claiming predictive power by definition.

Candidate domains include:

### 10.1 Price displacement

For supported horizons:

- absolute price delta;
- pip-equivalent delta where symbol conventions are explicitly defined;
- percentage return;
- optionally log return for research use;
- directional sign.

Relevant horizons may include, when source cadence permits:

- 2 seconds;
- 10 seconds;
- 30 seconds;
- 1 minute;
- 2 minutes;
- 5 minutes;
- 10 minutes;
- 15 minutes;
- 30 minutes;
- 60 minutes.

These are observation horizons, not promises that every provider/feed can materialize every horizon.

### 10.2 Range and volatility

Support derivation of:

- high-low range;
- close-to-close movement;
- realized movement/volatility measures;
- ATR-derived context where governed;
- range expansion/compression ratios;
- volatility acceleration/deceleration;
- distribution percentiles within declared comparison windows.

### 10.3 Directional persistence

Support measurement of:

- consecutive same-direction moves;
- duration of directional runs;
- distance traveled before reversal;
- continuation frequency after defined sequences;
- transition frequencies between UP / DOWN / FLAT states under a versioned state definition.

### 10.4 Reversal behavior

Support measurement of:

- reversal frequency;
- time to first reversal;
- reversal magnitude;
- failed continuation;
- early continuation followed by reversal;
- reversal after extension/compression states.

### 10.5 Impulse and pullback

A versioned detector may measure:

- impulse duration;
- impulse magnitude;
- pullback duration;
- pullback magnitude;
- impulse-to-pullback ratio;
- retracement proportion;
- continuation after pullback.

No subjective chart label becomes canonical unless its deterministic definition is versioned.

### 10.6 Compression and expansion

A versioned detector may measure:

- contraction of range/volatility;
- duration of compression;
- subsequent expansion magnitude;
- expansion direction;
- persistence after expansion;
- failure/re-entry into prior range.

### 10.7 Breakout and false-break behavior

Where a breakout boundary is objectively and versionedly defined, research evidence may include:

- breakout occurrence;
- continuation distance;
- time above/below boundary;
- retest behavior;
- return inside prior structure;
- false-break classification.

The detector must state the boundary authority. It must not infer arbitrary chart lines after seeing the future outcome.

### 10.8 Structural reaction behavior

Where canonical SR/corridor evidence is available, the system may study:

- approach speed;
- reaction distance;
- bounce/penetration behavior;
- time spent near a barrier;
- continuation after barrier interaction;
- repeated-test behavior.

The market observation remains objective; SR interpretation remains attributable to the structural model/version used.

---

## 11. Sequence evidence

The observation system must support later analysis of defined price-behavior sequences.

Examples of sequence classes may include:

- directional runs;
- impulse -> pullback -> continuation;
- compression -> expansion;
- breakout -> retest -> continuation;
- extension -> mean reversion;
- alternating/choppy transitions.

These examples are research categories, not assumed profitable patterns.

Every sequence detector must have:

- detector/version identity;
- input window;
- required cadence;
- feature cutoff timestamp;
- deterministic classification rules;
- no use of future evidence in the pre-cutoff classification.

---

## 12. Future-path observation for research labels

For an observation anchor or a formally detected pre-cutoff state, the system may record later market movement at declared future horizons.

Examples:

- +30 seconds;
- +1 minute;
- +2 minutes;
- +5 minutes;
- +10 minutes;
- +15 minutes;
- +30 minutes;
- +60 minutes.

Future-path evidence is **label/downstream evidence** relative to the anchor.

It must never be included in features intended to describe what was knowable at the anchor time.

Useful future-path measures may include:

- signed return;
- maximum favorable excursion relative to a declared direction/reference;
- maximum adverse excursion;
- maximum up/down excursion without presuming trade direction;
- time to local/research target;
- time to reversal;
- path efficiency;
- end-state direction.

---

## 13. Market-regime context

Behavior analysis may segment by governed regime evidence such as:

- activity state;
- volatility regime;
- trend regime;
- noise/chop state;
- corridor/structure regime;
- directional flow state;
- provider readiness/data-quality state.

A regime label is not raw price truth; it is a versioned derived interpretation and must retain its model/spec version.

---

## 14. Strategy independence and anti-selection-bias rule

The continuous market dataset must not be constructed only from times when the current strategy evaluated favorably.

Mandatory research capability:

`ALL VALID MARKET OBSERVATIONS`

must be comparable against:

`OBSERVATIONS SELECTED BY STRATEGY X VERSION Y`.

This enables the project to test whether a strategy discovers real conditional advantage or merely reproduces ordinary market behavior.

---

## 15. Raw-versus-derived preservation

Raw source evidence and derived behavior features must remain separate.

Rules:

1. Raw evidence is immutable after canonical ingestion, except clearly versioned correction/migration procedures.
2. Derived features are reproducible from raw evidence plus derivation version.
3. A derivation change creates a new feature version; it does not rewrite historical raw price.
4. Aggregated statistics never replace required raw evidence.
5. Compression/rotation policies must preserve reproducibility requirements.

---

## 16. Storage and retention

Storage should be durable, append-oriented or otherwise audit-safe, replayable and compatible with long-horizon research.

Before implementation, the system must explicitly define:

- raw observation storage path(s);
- provider/source partitioning;
- symbol partitioning;
- timeframe/cadence partitioning;
- retention policy;
- compression policy;
- deduplication identity;
- restart/recovery behavior;
- integrity checks.

A destructive aggregation policy that prevents later recomputation of newly defined behavior metrics is forbidden unless separately approved by Owner governance.

The canonical preference is to preserve the most valuable primary evidence first and derive aggregates later.

---

## 17. Data quality

At minimum track:

- gaps;
- duplicate observations;
- out-of-order observations;
- stale prices;
- invalid timestamps;
- provider changes;
- inconsistent symbol/timeframe identity;
- unsupported sampling windows;
- incomplete future-label windows;
- DST/local-time projection errors;
- derivation/version mismatch.

Poor data quality must never be interpreted as a market pattern.

---

## 18. Relationship to Trade Temporal Telemetry

`TRADE_TEMPORAL_TELEMETRY_SPEC_v3.0.0` answers what the market did **after an effective executable OPEN_NOW signal**.

This document answers what the market did **continuously, whether or not a signal existed**.

Trade Temporal Telemetry remains the authoritative signal-conditioned objective market outcome chain.

Market Behavior Observation is the broader unconditional evidence layer.

The same raw governed price evidence may support both systems when provenance and temporal eligibility permit, but the semantic records remain distinct.

---

## 19. Relationship to Performance Analytics

Performance Analytics evaluates strategy/system performance.

Market Behavior Observation does not declare strategy performance.

It supplies unconditional market behavior evidence that later analytics may use as a baseline or contextual dataset.

---

## 20. Relationship to Research and Strategy Intelligence

Research may use this evidence to ask:

- does behavior differ by hour/weekday/month?
- are some continuation/reversal structures recurrent?
- are apparent patterns stable across windows/regimes?
- does strategy-selected behavior differ materially from unconditional behavior?

Strategy Intelligence may summarize validated findings, but neither Research nor Intelligence may back-edit raw observation truth.

---

## 21. Prediction boundary

This document does not define a prediction model.

Historical conditional frequencies may later support probabilistic estimates, but:

- historical frequency is not certainty;
- pattern recurrence is not guaranteed;
- probabilities require explicit target, calibration, validation and readiness;
- future price must never be presented as known fact.

Prediction/model authority remains governed by Research/Intelligence and any future explicit model specification.

---

## 22. Initial authority mode

Upon future activation, the initial mode is:

`DATA_COLLECTION_AND_RESEARCH_ONLY`

In this mode, market-behavior evidence:

- is collected;
- is analyzed;
- may generate research findings;
- may appear in admin/research surfaces;
- does not change strategy thresholds;
- does not block or authorize signals;
- does not alter provider selection;
- does not enable broker execution.

---

## 23. Forbidden patterns

Forbidden:

- collecting only winning or signal-selected market periods;
- fabricating missing prices;
- silently mixing providers;
- storing only local time without UTC authority;
- using future observations as pre-anchor features;
- presenting a derived regime label as raw price truth;
- deleting raw evidence because a current aggregate exists;
- calling a repeated sequence profitable without strategy/outcome validation;
- turning an observed temporal correlation directly into a live gate;
- claiming certainty about future price.

---

## 24. Implementation sequence after activation

1. Define durable raw observation identity/storage and retention.
2. Persist UTC/provider/symbol/timeframe provenance.
3. Reuse existing candle integrity and freshness contracts.
4. Materialize a minimal reproducible continuous observation dataset.
5. Add versioned deterministic behavior features.
6. Add calendar/time projections from UTC.
7. Add data-quality and replay validation.
8. Feed Temporal Market Behavior Analytics.
9. Only later feed strategy-specific trading-window research.
10. Keep all live influence disabled until separately governed.

---

## 25. Validation requirements

At minimum prove:

1. market observations can be collected without a strategy signal;
2. provider provenance cannot be lost or silently mixed;
3. UTC authority survives local-time/DST projection;
4. gaps and stale evidence remain explicit;
5. raw evidence is not overwritten by derived analytics;
6. behavior features are reproducible from raw evidence and version;
7. future-label evidence cannot leak into pre-anchor features;
8. strategy-selected and unconditional datasets remain distinguishable;
9. no market-behavior feature changes live strategy by default;
10. broker execution remains untouched.

---

## 26. Final principle

The project cannot learn when it is best to trade if it records only the moments it already decided to trade.

The canonical evidence foundation must therefore preserve **what the market does continuously**, then allow strategy and research layers to determine whether any repeatable temporal advantage actually exists.

Canonical chain:

`OBSERVE THE MARKET -> PRESERVE RAW TRUTH -> DERIVE VERSIONED BEHAVIOR -> ANALYZE TIME -> VALIDATE PATTERNS -> COMPARE STRATEGIES -> GOVERN ANY FUTURE USE`.
