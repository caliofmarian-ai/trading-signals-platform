# PERFORMANCE_ANALYTICS_SPEC_v2.0.0

Version: 2.0.0  
Path: /opt/binarybot/docs/canonical/active/PERFORMANCE_ANALYTICS_SPEC_v2.0.0.md  

Linked Documents:
- /opt/binarybot/docs/canonical/active/CANONICAL_STRATEGY_STACK_v1.0.0.md
- /opt/binarybot/docs/canonical/active/OUTCOME_TRACKING_SPEC_v2.0.0.md
- /opt/binarybot/docs/canonical/active/TRADE_TEMPORAL_TELEMETRY_SPEC_v2.0.0.md
- /opt/binarybot/docs/canonical/active/DECISION_AUDIT_SPEC_v2.0.0.md
- /opt/binarybot/docs/canonical/active/RESEARCH_AND_LEARNING_FRAMEWORK_SPEC_v2.0.0.md
- /opt/binarybot/docs/canonical/active/STRATEGY_INTELLIGENCE_SYSTEM_v2.0.0.md


Status: Active Canonical  
Path target: `/opt/binarybot/docs/canonical/active/PERFORMANCE_ANALYTICS_SPEC_v2.0.0.md`  
Supersedes: `/opt/binarybot/docs/PERFORMANCE_ANALYTICS_SPEC.md`  
Related canonical documents:
- `/opt/binarybot/docs/canonical/active/CANONICAL_STRATEGY_STACK_v1.0.0.md`
- `/opt/binarybot/docs/canonical/active/ALGO_SPEC_v2.0.0.md`
- `/opt/binarybot/docs/canonical/active/DECISION_OBJECT_CANONICAL_SPEC_v1.0.0.md`
- `/opt/binarybot/docs/canonical/active/FSM_DECISION_ENGINE_SPEC_v1.0.0.md`
- `/opt/binarybot/docs/canonical/active/SIGNAL_ENGINE_EXECUTION_SPEC_v2.0.0.md`
- `/opt/binarybot/docs/canonical/active/SR_CORRIDOR_ENGINE_SPEC_v2.0.0.md`
- `/opt/binarybot/docs/canonical/active/TIME_MODEL_UNIFIED_CANON_v2.0.0.md`
- `/opt/binarybot/docs/canonical/active/DECISION_AUDIT_SPEC_v2.0.0.md`
- `/opt/binarybot/docs/canonical/active/TRADE_TEMPORAL_TELEMETRY_SPEC_v2.0.0.md`
- `/opt/binarybot/docs/canonical/active/OUTCOME_TRACKING_SPEC_v2.0.0.md`
- `/opt/binarybot/docs/canonical/active/OBSERVABILITY_SPEC_v2.0.0.md`

---

## 1. PURPOSE

This document defines the canonical **Performance Analytics Layer** for BinaryBot / DROPi Signals.

Its job is to measure, compare, explain, and monitor the system's performance across the full signal lifecycle without collapsing multiple truth layers into one misleading metric.

The older v1.0.0 document correctly established several important foundations:

- edge must be measurable
- drift must be detectable
- parameter tuning must be data-driven
- emotion must not drive evaluation
- lifecycle conversion matters
- segmentation matters by symbol / session / buffer / context fileciteturn28file0

Those foundations remain valid.

However, the older document also mixes multiple concepts that now need stricter canonical separation:

- engine lifecycle analytics
- community/user voting analytics
- admin operational outcome analytics
- market-truth telemetry analytics
- strategy fitness analytics

In v2.0.0, performance analytics becomes a **multi-truth analytics system**, not a single scoreboard.

---

## 2. WHY V1.0.0 IS NO LONGER SUFFICIENT

The older spec treated performance primarily as a measurement layer over wins, losses, frequency, rejections, and lifecycle conversions. It also added later sections about ELITE community outcome reporting, vote aggregation, user statistics, and signal reliability from community feedback. fileciteturn28file0

That is no longer sufficient for the current architecture because the project now requires explicit separation between:

1. **Decision truth**  
   Why the engine produced, advanced, rejected, or killed a signal.

2. **Market truth**  
   What the market objectively did after executable emission.

3. **Operational/admin truth**  
   What operators/admins actually executed, missed, corrected, or reconciled.

4. **Community/user truth**  
   What subscribers or ELITE members reported about their own experience.

5. **Business truth**  
   What matters for monetization, trust, retention, UX, and channel quality.

A modern performance layer must preserve these as separate analytics dimensions.

---

## 3. CANONICAL POSITION IN THE ARCHITECTURE

Performance Analytics is downstream of:

- strategy decision production
- corridor / time / score / feasibility evaluation
- DecisionObject generation
- FSM transitions
- signal emission
- observability
- telemetry capture
- outcome reconciliation

High-level chain:

`Strategy Logic -> DecisionObject -> FSM -> Signal Execution Layer -> Observability -> Telemetry -> Outcome Reconciliation -> Performance Analytics -> Research -> Intelligence -> Governance`

Performance Analytics does not produce the signal.
Performance Analytics evaluates what the system did and what happened after.

It is therefore an interpretation and evidence layer.

---

## 4. CANONICAL ANALYTICS PHILOSOPHY

### 4.1 No single metric is allowed to define reality

The project must not reduce system quality to one unlabeled win rate.

At minimum, analytics must preserve distinct performance views:

- **Decision quality**
- **Market outcome quality**
- **Operational execution quality**
- **Community experience quality**
- **Business efficiency quality**

### 4.2 Explanation is as important as counting

Performance analytics must answer not only:

- how many wins?
- what is the win rate?

but also:

- why did the signal exist?
- why did it fail to open?
- why did it die?
- why was it missed?
- why is one session weaker?
- why did perceived performance differ from market-truth performance?
- why did user trust fall even if market-truth remained acceptable?

### 4.3 Analytics must support action

The output of performance analytics must be usable by:

- strategy review
- parameter governance
- admin workflow improvement
- control panel decisions
- Telegram UX improvement
- research and AI intelligence layers

---

## 5. TRUTH LAYERS (MANDATORY SEPARATION)

### 5.1 Decision Truth Analytics
Measures upstream strategy quality before downstream execution reality.

Examples:
- candidate counts
- rejection counts by reason
- PRE promotion rate
- CONFIRM promotion rate
- OPEN_NOW issuance rate
- death / kill distribution by reason
- DecisionObject score distributions

Primary source:
- `DECISION_AUDIT_SPEC_v2.0.0.md`

### 5.2 Market Truth Analytics
Measures what the market objectively did after executable emission.

Examples:
- expiry hit / fail
- favorable excursion
- adverse excursion
- time-to-target
- time-to-failure
- path shape after signal

Primary source:
- `TRADE_TEMPORAL_TELEMETRY_SPEC_v2.0.0.md`

### 5.3 Operational Truth Analytics
Measures what operators/admins actually executed or reconciled.

Examples:
- WIN / LOSE / MISSED
- missed-rate
- correction-rate
- discrepancy-rate vs telemetry
- manual override rate

Primary source:
- `OUTCOME_TRACKING_SPEC_v2.0.0.md`

### 5.4 Community Truth Analytics
Measures subscriber or ELITE-reported experience.

Examples:
- participation rate
- self-reported execution rate
- perceived result distribution
- complaint / dispute patterns
- trust signals

This layer is useful, but it is never allowed to overwrite decision truth or market truth.

### 5.5 Business Truth Analytics
Measures monetization and service performance.

Examples:
- retention
- plan conversion
- channel engagement
- admin response latency
- support case rate
- affiliate conversion quality
- symbol/session usefulness from a customer perspective

---

## 6. CORE PERFORMANCE DOMAINS

The analytics layer must cover at least the following domains:

1. **Signal production analytics**
2. **Lifecycle conversion analytics**
3. **Rejection analytics**
4. **Decision quality analytics**
5. **Market outcome analytics**
6. **Operational outcome analytics**
7. **Segmented performance analytics**
8. **Stability and drift analytics**
9. **Parameter impact analytics**
10. **Business and UX analytics**

The old document already covered many of these partially through win rate, expectancy, signal frequency, rejection rate, funnel tracking, segmentation, drawdown, drift, sessions, parameter impact, and reports. fileciteturn28file0  
v2.0.0 keeps them, but reorganizes them under a more mature architecture.

---

## 7. SIGNAL PRODUCTION ANALYTICS

These metrics describe how the engine produces opportunities before final outcome.

Track at minimum:

- candidates evaluated
- candidates rejected
- candidates entering PRE
- PRE to CONFIRM conversion
- CONFIRM to OPEN_NOW conversion
- PRE to OPEN_NOW conversion
- OPEN_NOW count by symbol
- OPEN_NOW count by session
- OPEN_NOW count by timeframe
- OPEN_NOW starvation intervals

Purpose:
- detect overtrading
- detect starvation
- detect imbalance between symbols or sessions
- detect over-filtering before executable emission

The older spec correctly tracked signal frequency and PRE to OPEN conversion. fileciteturn28file0  
This remains mandatory.

---

## 8. DECISION QUALITY ANALYTICS

This domain measures whether the strategy logic is selecting and filtering well.

Track at minimum:

- average DecisionObject score by symbol/session
- score distribution for promoted vs rejected candidates
- rejection counts by reason:
  - spike
  - SR corridor
  - feasibility
  - score
  - focus conflict
  - timing / temporal gate
  - other explicit kill reasons
- reversal / dead-on-arrival patterns
- proportion of high-score setups that later underperform
- proportion of medium-score setups that later outperform

Purpose:
- identify weak filters
- identify overconfident filters
- identify score calibration drift
- support parameter reviews

This generalizes the older rejection-rate and trend-context logic into a broader strategy-quality view. fileciteturn28file0

---

## 9. MARKET TRUTH ANALYTICS

This domain analyzes the objective market behavior after executable emission.

Examples of metrics:

- expiry win rate
- favorable excursion rate
- adverse excursion rate
- path efficiency
- time-to-favorable-threshold
- time-to-adverse-threshold
- stability after signal
- false-start frequency

Important rule:

These metrics must be computed from telemetry or equivalent objective post-signal data, not from admin buttons or community votes.

The performance layer must be able to answer:
- did the market actually validate this signal?
- even when operator/admin marked it differently?
- even when users missed it?

---

## 10. OPERATIONAL OUTCOME ANALYTICS

This domain measures execution and admin reconciliation reality.

Track at minimum:

- wins_count
- losses_count
- missed_count
- execution_rate
- missed_rate
- correction_rate
- override_rate
- disputed outcome rate
- telemetry vs admin discrepancy rate

The old document already treated outcomes as a core data source and used WIN / LOSE / MISSED for measurement. fileciteturn28file0  
That remains useful, but it is now explicitly labeled as **operational performance**, not universal truth.

Canonical rule:

A dashboard must label this view clearly, for example:

- `Operational WR`
- `Admin-Reconciled WR`
- `Execution WR`

and must never imply that it is the same as market-truth performance unless explicitly stated.

---

## 11. COMMUNITY / ELITE FEEDBACK ANALYTICS

The older document included:

- multiple member outcome reports per signal
- vote aggregation
- per-user statistics
- SRI (signal reliability index)
- one-vote-per-user safeguards fileciteturn28file0

This content is potentially valuable, but in the new architecture it must be downgraded from canonical truth to **community experience analytics** unless and until the business model officially confirms this subsystem as active.

### 11.1 Canonical rule
Community reports may inform:
- user behavior analysis
- trust analysis
- support analysis
- perceived signal quality

They must not overwrite:
- decision truth
- telemetry truth
- admin-reconciled truth

### 11.2 Status note
If the ELITE voting subsystem is not live in production, these sections should be treated as:
- optional future extension
- not required for minimal analytics implementation

### 11.3 If active later, track:
- participation rate
- per-user execution consistency
- perceived signal reliability
- disagreement rate among users
- disagreement rate vs telemetry
- disagreement rate vs admin reconciliation

---

## 12. SEGMENTED PERFORMANCE ANALYSIS

The old document correctly required segmentation by symbol, buffer mode, trend context, volatility regime, and session. fileciteturn28file0  
That remains mandatory and should be expanded.

Segment by:

- symbol
- direction
- timeframe
- session
- weekday
- expiry bucket
- buffer mode
- corridor regime
- score band
- volatility regime
- trend regime
- focus regime
- execution route / channel
- admin team / operational path where relevant

Purpose:
- identify where the system is actually strong
- identify weak local pockets hidden by aggregate stats
- support selective disabling instead of global panic

---

## 13. EXPECTANCY AND ECONOMIC METRICS

The older document correctly defined expectancy and highlighted binary options assumptions. fileciteturn28file0

Track at minimum:

- expectancy by market-truth outcome
- expectancy by operational outcome
- expectancy by symbol
- expectancy by session
- expectancy by score band
- expectancy by expiry bucket

Where relevant, distinguish:

- gross expectancy
- payout-adjusted expectancy
- execution-adjusted expectancy
- subscriber-realized expectancy
- business-value expectancy

Canonical rule:

Every expectancy value must declare which truth layer and which payout model it uses.

No unlabeled expectancy numbers are allowed.

---

## 14. LIFECYCLE CONVERSION ANALYTICS

The old document already required tracking the funnel from `IDLE -> PRE -> CONFIRM -> OPEN_NOW -> EXECUTED -> WIN / LOSS`. fileciteturn28file0

This remains important, but the canonical lifecycle must be updated.

Recommended lifecycle analytics model:

`CANDIDATE -> PRE -> CONFIRM -> OPEN_NOW -> TELEMETRY_CAPTURED -> OUTCOME_RECONCILED -> ANALYTICS_CLASSIFIED`

Track drop-off and rates between each step.

Examples:
- candidate to PRE rate
- PRE to CONFIRM rate
- CONFIRM to OPEN_NOW rate
- OPEN_NOW to telemetry-ready rate
- OPEN_NOW to reconciled-outcome rate
- OPEN_NOW to disputed-outcome rate

Purpose:
- distinguish strategy filtering problems from downstream instrumentation problems
- detect missing telemetry
- detect admin workflow gaps

---

## 15. REJECTION ANALYTICS

The older spec tracked spike rejection, SR rejection, feasibility rejection, and score rejection. fileciteturn28file0

This remains mandatory and should become a first-class analytics domain.

Track:

- total rejections by reason
- rejection rate by reason
- rejection rate by symbol
- rejection rate by session
- rejection rate by volatility regime
- rejection rate by score band
- rejection reason clusters
- rejection-to-later-opportunity analysis

Advanced question:
- how often does a rejected candidate later become a strong move?
- which rejection reasons are too harsh?
- which rejection reasons save the strategy from bad trades?

This domain is essential for improving strategy quality without blindly relaxing filters.

---

## 16. DRIFT, STABILITY, AND HEALTH ANALYTICS

The older document correctly required rolling windows, drift detection, session review, and alert thresholds. fileciteturn28file0

This remains mandatory.

Track across rolling windows such as:
- last 25
- last 50
- last 100
- last 200
- session-local windows
- symbol-local windows

Detect drift in:
- market-truth WR
- operational WR
- rejection rate
- signal frequency
- expectancy
- discrepancy rate
- miss rate
- focus efficiency
- score calibration

When drift is detected, analytics should support governance actions such as:
- review required
- freeze parameter changes
- temporary symbol disable proposal
- session downgrade proposal
- investigation request to research/intelligence layer

---

## 17. DRAWDOWN AND LOSS CLUSTER ANALYTICS

The old document already tracked consecutive losses, max drawdown, average losing streak, and worst day performance. fileciteturn28file0

This remains important, but it must be labeled carefully.

Possible tracked forms:
- market-truth drawdown
- operational drawdown
- subscriber-realized drawdown
- symbol-local drawdown
- session-local drawdown

Also track:
- loss clusters by rejection regime
- loss clusters by score band
- loss clusters after parameter change
- loss streak recovery speed

Canonical rule:

Drawdown numbers must specify which truth layer they represent.

---

## 18. PARAMETER IMPACT ANALYTICS

The older document correctly stated that parameter changes must be compared before vs after on WR, expectancy, frequency, and drawdown. fileciteturn28file0

This remains mandatory.

Every meaningful parameter change should be analyzable against:

- market-truth WR change
- operational WR change
- expectancy change
- frequency change
- rejection distribution change
- discrepancy change
- stability change
- symbol/session side effects

Canonical rule:

No parameter change should be called an improvement unless the measured improvement is explicitly labeled by truth layer and sample size.

---

## 19. MINIMUM SAMPLE AND ANTI-ILLUSION RULES

The older document correctly warned against judging the system by a single day, single session, emotional reaction, or tiny samples, and suggested minimum sample sizes such as 200 trades per symbol and 500 total trades. fileciteturn28file0

This remains canonical guidance.

### 19.1 Anti-illusion principles
Never judge the strategy by:
- one streak
- one bad day
- one good day
- one operator
- one symbol burst
- one Telegram complaint wave

### 19.2 Minimum confidence framing
Every dashboard or report should, where practical, expose:
- sample size
- window size
- confidence caveat
- truth layer used

### 19.3 Strong recommendation
Metrics below meaningful sample thresholds should be shown as:
- provisional
- low confidence
- watchlist only

not as grounds for hard strategic conclusions.

---

## 20. DATA SOURCES

The older document referenced sources such as:
- `focus_history.jsonl`
- `distribution_logs.jsonl`
- `execution_results.jsonl` (future extension) fileciteturn28file0

These remain useful examples, but the canonical v2.0.0 position is broader:

Performance analytics may ingest from:
- decision audit logs
- focus / lifecycle logs
- distribution logs
- signal execution logs
- telemetry datasets
- outcome reconciliation records
- observability event streams
- optional user/community feedback streams
- optional business/retention data

Canonical rule:

The data source must be truth-labeled.
Do not mix records from incompatible truth domains without explicit labeling.

---

## 21. PERFORMANCE REPORT STRUCTURE

The older document required periodic reports with totals, WR, expectancy, drawdown, rejection, session, symbol, buffer, trend, and drift. fileciteturn28file0

That remains good, but the report structure must be upgraded.

A canonical performance report should include:

1. Reporting window
2. Sample size
3. Truth layer labels
4. Signal production summary
5. Lifecycle conversion summary
6. Rejection summary
7. Market-truth performance summary
8. Operational outcome summary
9. Discrepancy summary
10. Segmentation summary
11. Drift / stability summary
12. Parameter-change impact summary
13. Research flags
14. Admin / UX / business flags
15. Recommended actions

This makes the report actionable instead of merely descriptive.

---

## 22. ALERTS AND THRESHOLDS

The older document suggested thresholds such as:
- WR < 55% over last 100 trades
- consecutive losses >= 6
- rejection rate > 70%
- signal frequency doubles unexpectedly fileciteturn28file0

These may remain as provisional operational heuristics, but they must not be treated as universal constants.

Canonical rule:

Every threshold must declare:
- metric definition
- truth layer
- sample window
- rationale
- severity

Recommended alert families:
- low market-truth WR
- low operational WR
- high miss rate
- high discrepancy rate
- rejection spike
- frequency anomaly
- symbol collapse
- session collapse
- telemetry missingness
- admin workflow lag

---

## 23. CAPITAL EFFICIENCY AND BUSINESS EFFICIENCY

The older document introduced capital turnover and capital utilization efficiency. fileciteturn28file0

These concepts remain useful, but the v2.0.0 analytics layer should expand them into both economic and business views.

Track where relevant:
- trades per day
- actionable trades per session
- payout-adjusted yield
- execution-adjusted value density
- value per subscriber cohort
- admin workload per executable signal
- support cost per active signal stream
- affiliate conversion quality by symbol/session/channel

This matters because a technically “good” strategy can still be operationally or commercially inefficient.

---

## 24. RESEARCH, INTELLIGENCE, AND AI CONSUMPTION

Performance analytics is an upstream provider to:
- research
- strategy intelligence
- AI audit layers
- governance
- future controlled evolution systems

### 24.1 Research usage
Research should use performance analytics to identify:
- weak symbols
- weak sessions
- unstable filters
- discrepancy patterns
- hidden strengths masked by bad operational handling

### 24.2 Intelligence usage
Intelligence layers may detect:
- structural underperformance
- false confidence zones
- admin workflow bottlenecks
- Telegram UX friction
- monetization distortions

### 24.3 AI guardrail
AI systems may consume analytics to propose hypotheses.
They must not autonomously mutate strategy parameters solely from noisy or unlabeled analytics.

---

## 25. ADMIN / CONTROL PANEL / TELEGRAM / UX UPGRADE PROPOSALS

Because you asked that patching should also surface upgrade proposals, this spec records several architecture-level improvements for future implementation.

### 25.1 Admin Control Panel Upgrades
Add dedicated analytics views for:
- market-truth vs operational-truth comparison
- rejection heatmaps
- drift radar
- symbol/session watchlists
- discrepancy queue
- parameter-change compare mode

### 25.2 Telegram UX Upgrades
Add clearer admin-facing summaries such as:
- `Operational result pending`
- `Telemetry captured`
- `Mismatch detected`
- `Review needed`

Do not expose complex truth collisions in subscriber channels unless product policy explicitly allows it.

### 25.3 Research UX Upgrades
Create an analytics workspace where research can inspect:
- score band performance
- rejection reason quality
- corridor / time interactions
- symbol-local drift
- missed-rate distortions

### 25.4 Intelligence Upgrades
Introduce future dashboards for:
- structural weakness ranking
- filter harshness ranking
- symbol efficiency ranking
- admin friction ranking
- user trust divergence ranking

These proposals are not mandatory for minimal implementation, but they are strongly recommended.

---

## 26. NON-GOALS

This document does not define:
- strategy logic itself
- corridor detection rules
- time model internals
- FSM state machine internals
- public subscriber UI policy
- broker integration contracts
- pricing / product package rules

It defines the measurement and interpretation layer for system performance.

---

## 27. SUMMARY

The older `PERFORMANCE_ANALYTICS_SPEC.md` correctly established that the system must measure edge, expectancy, signal frequency, rejections, funnel conversion, segmentation, drawdown, drift, sessions, parameter impact, and reporting. It also proposed later additions for event-log analytics and ELITE outcome voting. fileciteturn28file0

In v2.0.0, those useful foundations are preserved but reorganized under a more rigorous architecture.

Performance Analytics is now defined as a **multi-truth analytics layer** that keeps separate:

- decision quality
- market-truth quality
- operational/admin execution quality
- community experience quality
- business efficiency quality

This prevents false conclusions, supports better governance, and gives the project a far stronger base for admin tooling, Telegram UX, research, intelligence, and future AI-assisted optimization.

## 24. Community Statistics and Non-Authoritative Leaderboards

This section integrates bounded analytics rules from the merged Community Feedback and Privacy intake.

### 24.1 Private statistics metrics
Private member statistics may include win_rate, participation_rate, activity measures, and reliability-oriented scoring, provided these are clearly scoped as member/private statistics rather than canonical engine truth.

### 24.2 Leaderboard treatment
Leaderboard surfaces remain optional, transparent, and non-authoritative. Any leaderboard derived from self-reported outcomes must be labeled as self-reported and must not be presented as canonical performance truth.

### 24.3 Eligibility and reliability framing
Leaderboard eligibility may require minimum trade count / participation thresholds. Reliability-style ranking is allowed only as an analytical/community convenience metric and must not replace canonical outcome analytics.

## 25. Strategy Auditor Metrics and Diagnostic Ratios

This section absorbs bounded content from AI_STRATEGY_AUDITOR_SPEC.md.

### 25.1 Metric scope
Performance analytics may include diagnostic metrics tied to rejection rates, output sparsity, symbol starvation, and channel/distribution-side loss of useful delivery opportunities.

### 25.2 Interpretation boundary
These metrics are interpretive diagnostics and must not be confused with canonical outcome truth or raw execution ownership.

## 26. Aggregated Intelligence Metrics and Snapshot-Derived Views

This section absorbs bounded content from INTELLIGENCE_DATA_PIPELINE_DEFINITION.md.

### 26.1 Aggregate view purpose
Performance analytics may consume aggregated intelligence snapshots to present multi-event trends, active symbol patterns, and research-facing rollups.

### 26.2 Canonical limit
These aggregated views remain interpretive analytical surfaces and must not silently replace raw canonical evidence.

## 27. Statistical Proof Layer Clarifications

This section absorbs bounded clarifications extracted from STATISTICAL_PROOF_LAYER.md.

### 27.1 Proof-oriented analytics role
Analytics may expose proof-oriented summaries, evidence aggregates, and statistical confidence views, provided they remain interpretations over canonical evidence rather than replacement truth.

### 27.2 Canonical evidence precedence
Raw and canonical evidence sources remain authoritative. Statistical proof views are analytical overlays.

### 27.3 No shadow score authority
A statistical proof layer must not become a parallel scoring or decision authority outside active analytics and strategy canon.
