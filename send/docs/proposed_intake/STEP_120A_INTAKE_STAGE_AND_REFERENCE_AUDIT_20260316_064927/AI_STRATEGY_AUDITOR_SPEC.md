# AI_STRATEGY_AUDITOR_SPEC.md

## 1. PURPOSE

This document defines the canonical **AI Strategy Auditor** layer for BinaryBot / DROPi Signals.

The purpose of this layer is to transform raw decision telemetry and signal lifecycle logs into a **daily optimization report** for the strategy.

This layer does not replace the strategy engine.
It does not replace the Decision Audit Layer.
It sits **above** them and answers the next-level question:

- what happened today
- why it happened
- what failed most often
- what improved
- what degraded
- what should be reviewed by admin before changing parameters

The AI Strategy Auditor must help the project evolve from:

- a signal generator
- to an observable strategy
- to a measured optimization system

---

## 2. SCOPE

The AI Strategy Auditor must analyze at least the following daily evidence sources:

- `/opt/binarybot/observability/engine_events.jsonl`
- `/opt/binarybot/observability/fsm_events.jsonl`
- `/opt/binarybot/observability/distribution_events.jsonl`
- `/opt/binarybot/observability/error_events.jsonl`
- `/opt/binarybot/outcomes/outcomes.jsonl` if present
- future `/opt/binarybot/observability/decision_audit.jsonl` if later separated

This layer must remain read-only with respect to strategy execution.

It may generate reports, summaries, rankings, warnings, and recommendations, but must not auto-change strategy parameters unless a separate future spec explicitly allows that.

---

## 3. CORE QUESTIONS THE AUDITOR MUST ANSWER

Every daily report must aim to answer:

- how many symbols were scanned
- how many decision events were produced
- how many signals reached PRE
- how many reached CONFIRM
- how many reached OPEN_NOW
- how many were rejected
- what were the dominant rejection causes
- whether rejections were mostly caused by score, spike, SR, feasibility, focus pressure, cooldown, dedup, or distribution constraints
- which symbols generated the most valid candidates
- which symbols repeatedly died for the same reason
- whether one timeframe or direction underperformed
- whether today’s conversion funnel improved or degraded vs prior period
- whether the current thresholds appear too strict or too loose
- whether current risk gates appear healthy or pathological

---

## 4. OUTPUT ARTIFACTS

The auditor must generate at least the following output artifacts.

### 4.1 Daily JSON report

Canonical path:

`/opt/binarybot/analytics/reports/daily_strategy_audit_YYYY-MM-DD.json`

This is the machine-readable canonical daily artifact.

### 4.2 Daily human-readable markdown report

Canonical path:

`/opt/binarybot/analytics/reports/daily_strategy_audit_YYYY-MM-DD.md`

This is the admin-facing readable report.

### 4.3 Optional Telegram admin summary

A shortened summary may be sent into admin topic.

This summary must not replace the full report.
It is only a quick operational digest.

---

## 5. MINIMUM DAILY REPORT STRUCTURE

Each daily report must include the following sections.

### 5.1 Report header

- date
- timezone reference
- generation timestamp
- report version
- source files used
- run status
- data completeness status

### 5.2 Executive summary

Short admin digest:

- total decisions
- total PRE
- total CONFIRM
- total OPEN_NOW
- total REJECT
- top 3 rejection reasons
- top 3 symbols by useful signal progression
- top 3 anomalies or warnings

### 5.3 Conversion funnel

Mandatory funnel:

- scanned
- decision logged
- PRE
- CONFIRM
- OPEN_NOW
- published
- outcome-resolved

The report must compute both counts and ratios.

### 5.4 Rejection analysis

Mandatory breakdown by:

- reason
- symbol
- timeframe
- direction
- gate
- stage

### 5.5 Score analysis

Mandatory score breakdown:

- average score_total
- median score_total
- score buckets
- score distribution for REJECT
- score distribution for PRE
- score distribution for CONFIRM
- score distribution for OPEN_NOW

### 5.6 Gate health

For each gate:

- pass count
- fail count
- fail rate
- top symbols failing that gate
- whether fail rate exceeds expected band

Mandatory gates:

- spike_filter
- sr_gate
- feasibility

### 5.7 Symbol analysis

For each symbol:

- decisions
- rejects
- PRE count
- CONFIRM count
- OPEN_NOW count
- top reject reason
- average score
- dominant direction
- whether symbol appears healthy, noisy, or blocked

### 5.8 Timeframe analysis

For each timeframe:

- decision count
- reject rate
- PRE rate
- CONFIRM rate
- OPEN_NOW rate
- avg score
- dominant reject reason

### 5.9 Operational anomalies

Must include:

- repeated identical rejects
- sudden drop to zero decisions
- sudden spike in one gate failure
- empty output despite active symbols
- distribution success but no outcomes
- unusually high error log volume
- symbol starvation
- focus starvation if focus/watchlist mode is active

### 5.10 Recommendations

Recommendations must be split into:

- observe only
- investigate manually
- parameter review candidate
- do not change yet

The report must never present speculative tuning as a certainty.

---

## 6. REQUIRED METRICS

The auditor must compute at least these metrics.

### 6.1 Volume metrics

- `decision_count`
- `reject_count`
- `pre_count`
- `confirm_count`
- `open_now_count`
- `published_count`
- `error_count`

### 6.2 Ratio metrics

- `reject_rate`
- `pre_rate`
- `confirm_rate`
- `open_now_rate`
- `publish_rate`
- `outcome_resolution_rate`

### 6.3 Gate metrics

- `spike_fail_rate`
- `sr_fail_rate`
- `feasibility_fail_rate`

### 6.4 Score metrics

- `avg_score_total`
- `median_score_total`
- `score_p10`
- `score_p25`
- `score_p75`
- `score_p90`

### 6.5 Stability metrics

- `symbol_repeat_reject_rate`
- `same_reason_repeat_rate`
- `empty_cycle_rate`
- `decision_to_pre_conversion`
- `pre_to_confirm_conversion`
- `confirm_to_open_conversion`

---

## 7. CANONICAL REJECTION GROUPING

The auditor must normalize raw reasons into canonical groups.

### 7.1 Score group

- score_pre_fail
- score_confirm_fail
- score_open_fail
- below_threshold

### 7.2 Spike group

- SPIKE_DETECTED
- WICK_BODY_RATIO
- RANGE_Z
- JUMP_VS_ATR

### 7.3 Structure / SR group

- SR_SPACE_INSUFFICIENT
- support_too_close
- resistance_too_close

### 7.4 Feasibility group

- FEASIBILITY_FAIL
- expiry_not_viable
- speed_too_low

### 7.5 Focus / capacity group

- watchlist_full
- focus_priority_lost
- cooldown_active
- duplicate_focus

### 7.6 Distribution group

- duplicate_suppressed
- tier_limit_reached
- channel_inactive

### 7.7 Unknown group

Anything unmatched must be grouped into `unknown_reject_reason`.

The report must explicitly show unknown reason count.

---

## 8. RECOMMENDATION ENGINE RULES

The AI Strategy Auditor may generate recommendations, but must follow strict rules.

### 8.1 Recommendations must be evidence-based

A recommendation must cite:

- metric
- count
- ratio
- comparison period
- affected symbols or timeframes if relevant

### 8.2 Recommendations must be conservative

Examples of valid recommendation tones:

- observe for 3 more days
- investigate symbol-specific SR sensitivity
- review spike filter on BTC/USD
- compare M5 vs M15 feasibility behavior

Examples of invalid recommendation tones:

- definitely reduce threshold now
- disable gate immediately
- spike filter is wrong
- strategy is broken

### 8.3 Confidence labeling

Every recommendation must carry one of:

- LOW confidence
- MEDIUM confidence
- HIGH confidence

Confidence must depend on sample size and consistency.

### 8.4 No auto-tuning in v1

Version 1 of the AI Strategy Auditor is reporting-only.
No direct parameter mutation is allowed.

---

## 9. DAILY COMPARISON LOGIC

The daily report must compare the current day against at least one prior window.

Minimum comparison windows:

- previous day
- rolling 7-day average

Comparison should detect:

- reject rate up/down
- OPEN_NOW conversion up/down
- score distribution shift
- gate fail spikes
- symbol-specific degradation

---

## 10. ADMIN SUMMARY FORMAT

The short Telegram summary should include only high-value information.

Example structure:

- date
- decisions / PRE / CONFIRM / OPEN
- top reject reason
- top healthy symbol
- top warning
- recommendation headline

It must not dump raw JSON into Telegram.

---

## 11. FILES TO CREATE

Recommended initial files:

- `/opt/binarybot/tools/strategy_auditor_daily.py`
- `/opt/binarybot/tools/strategy_auditor_lib.py`
- `/opt/binarybot/analytics/reports/`
- `/opt/binarybot/analytics/cache/`

Optional later:

- `/opt/binarybot/tools/strategy_auditor_send_summary.py`
- `/opt/binarybot/tools/strategy_auditor_compare.py`

---

## 12. INITIAL IMPLEMENTATION PLAN

### Phase 1 — read logs

Read `engine_events.jsonl` and collect `decision` events.

### Phase 2 — compute daily aggregates

Compute counts, ratios, rejection reasons, score stats, symbol stats.

### Phase 3 — generate markdown report

Produce admin-readable `.md` report.

### Phase 4 — generate JSON report

Produce machine-readable `.json` report.

### Phase 5 — optional Telegram digest

Send short summary into admin topic.

---

## 13. MINIMUM ACCEPTANCE CRITERIA

The AI Strategy Auditor v1 is considered implemented when:

- it reads current observability logs successfully
- it produces one daily JSON report
- it produces one daily markdown report
- it computes funnel metrics
- it computes reject reason metrics
- it computes gate health metrics
- it computes symbol metrics
- it produces recommendations with confidence labels

---

## 14. RELATION TO DECISION AUDIT LAYER

The Decision Audit Layer records what happened per candidate / decision.

The AI Strategy Auditor aggregates those records into operational intelligence.

Therefore:

- Decision Audit Layer = evidence collection
- AI Strategy Auditor = evidence interpretation

The auditor depends on decision telemetry quality.
It must never silently invent missing evidence.

---

## 15. FINAL CANONICAL STATEMENT

BinaryBot / DROPi Signals must not only log why signals are rejected.

It must also summarize that evidence daily and convert it into actionable strategy intelligence.

The AI Strategy Auditor is the canonical reporting layer that transforms raw observability into measured strategy optimization.

--- 
## 16. STRATEGY HEATMAP

The AI Strategy Auditor must generate a **Strategy Heatmap** summarizing
how the strategy behaves across score ranges, symbols, and timeframes.

The heatmap is not merely visual.
It must expose structural pressure points in the strategy.

The heatmap should include at minimum:

• score bucket distribution  
• reject distribution by score range  
• PRE / CONFIRM / OPEN success by score range  

Example score buckets:

- 50–55
- 55–60
- 60–65
- 65–70
- 70–75
- 75–80
- 80+

Example heatmap output:

Score Bucket | Decisions | PRE | CONFIRM | OPEN | Reject Rate
--------------------------------------------------------------
60–65        | 320       | 110 | 30      | 5    | 65%
65–70        | 280       | 140 | 70      | 20   | 50%
70–75        | 200       | 120 | 80      | 35   | 40%

This helps detect:

• thresholds too strict
• thresholds too loose
• score clustering
• score deserts
• ineffective score ranges

The heatmap must also detect abnormal cases such as:

- extremely high reject rates in high score ranges
- almost no candidates in mid score ranges
- sharp score cliffs after PRE threshold  


## 17. STRATEGY BOTTLENECK DETECTION

The auditor must automatically detect **strategy bottlenecks**.

A bottleneck occurs when a single rejection cause dominates
a large portion of the decision pipeline.

Example thresholds:

If a single rejection reason exceeds:

60% of all rejects

the auditor must flag:

strategy_bottleneck_detected = true

Example diagnostic:

Top Reject Reason:

SR_SPACE_INSUFFICIENT = 64%

Interpretation:

The support/resistance gate is blocking most candidate signals.

Example report entry:

Strategy Bottleneck Detected

Dominant Reject Cause:
SR_SPACE_INSUFFICIENT

Reject Share:
64%

Suggested Operator Action:

Review SR buffer logic before modifying thresholds.


The system must not automatically adjust parameters.
It must only surface evidence.


---

## 18. SYMBOL STARVATION DETECTION

The auditor must detect **symbol starvation**.

Symbol starvation occurs when a symbol is actively scanned
but rarely produces viable signal candidates.

Symptoms:

• symbol scanned many times
• decisions generated
• almost no PRE signals

Example metrics:

Symbol | Decisions | PRE | PRE Rate
-----------------------------------
EURUSD | 220       | 3   | 1.3%
GBPUSD | 190       | 2   | 1.0%
BTCUSD | 160       | 40  | 25%

Interpretation:

EURUSD and GBPUSD may be blocked by
structure gates or scoring thresholds.

The report should label symbols as:

HEALTHY  
NOISY  
STARVED  
BLOCKED  

Definitions:

HEALTHY
PRE conversion within expected band.

NOISY
High decisions but low confirmation.

STARVED
Very low PRE rate.

BLOCKED
Repeated rejection by same gate.

Symbol starvation detection helps identify:

• symbols incompatible with current strategy
• symbols suffering from structural filter pressure
• symbols needing timeframe adjustments.

---

## MERGE STATUS

merge_status: BOUNDED_CONTENT_MERGED_INTO_ACTIVE_CANON
merge_target_docs:
- STRATEGY_INTELLIGENCE_SYSTEM_v2.0.0.md
- RESEARCH_AND_LEARNING_FRAMEWORK_SPEC_v2.0.0.md
- PERFORMANCE_ANALYTICS_SPEC_v2.0.0.md

merge_note:
This intake document was merged in bounded form into active canon. Auditor truth now lives as bounded sections inside the active intelligence/research/analytics cluster.
