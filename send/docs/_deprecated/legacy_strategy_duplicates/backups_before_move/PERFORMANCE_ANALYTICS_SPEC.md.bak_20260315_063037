PERFORMANCE_ANALYTICS_SPEC.md

Performance Measurement & Statistical Edge Validation — BinaryBot
Version: 1.0.0
Status: Canonical
Linked Documents: ALGO_SPEC.md, FSM_SPEC.md, RISK_MODEL.md, OBSERVABILITY_LOGGING_SPEC.md, TEST_PLAN.md

---

1. PURPOSE

This document defines how system performance is measured, analyzed, validated, and improved.

It ensures:

- Strategy edge is measurable
- Risk-to-reward is statistically justified
- Drift is detected early
- Parameter tuning is data-driven
- Emotional bias is removed

Without performance analytics, the system is blind.

---

2. CORE METRICS

The system must track the following metrics:

2.1 Win Rate (WR)

Formula:

WR = Wins / Total Trades

Tracked by:

- Symbol
- Buffer mode
- Trend classification
- Time session (ASIA / LONDON / NY)

---

2.2 Expectancy (E)

Formula:

E = (WR × Avg Win) − (Loss Rate × Avg Loss)

For binary:

Avg Win = payout ratio
Avg Loss = 1 unit

Expectancy must remain positive.

---

2.3 Signal Frequency

Metrics:

- Signals per hour
- Signals per session
- Signals per symbol
- PRE to OPEN conversion rate

Detects overtrading or starvation.

---

2.4 Rejection Rate

Track:

- Spike rejection %
- SR rejection %
- Feasibility rejection %
- Score rejection %

High rejection may indicate:

- Market instability
- Overly strict parameters
- Incorrect tuning

---

2.5 Conversion Funnel

Track full lifecycle:

IDLE
→ PRE
→ CONFIRM
→ OPEN_NOW
→ EXECUTED
→ WIN / LOSS

Measure drop-off at each stage.

---

3. SEGMENTED PERFORMANCE ANALYSIS

Performance must be segmented by:

3.1 Symbol

Identify:

- Strong pairs
- Weak pairs
- Correlation clusters

---

3.2 Buffer Mode

Compare:

SMALL vs MEDIUM vs LARGE

Measure:

- Win rate
- Drawdown
- Frequency

---

3.3 Trend Context

Compare:

With trend
Flat
Counter-trend

Detect if counter-trend underperforms significantly.

---

3.4 Volatility Regime

Classify:

Low volatility
Normal volatility
High volatility

Analyze win rate per regime.

---

4. DRAWdown ANALYSIS

Track:

- Consecutive losses
- Max drawdown
- Average losing streak
- Worst day performance

Define risk ceiling:

If drawdown exceeds predefined threshold → system review required.

---

5. EDGE STABILITY TEST

Rolling window analysis:

- Last 50 trades
- Last 100 trades
- Last 200 trades

If WR drops below statistical confidence band → flag drift.

---

6. DRIFT DETECTION

Drift conditions:

- Win rate deviation > 10% from baseline
- Rejection rate spike > 30%
- Signal frequency anomaly
- Sudden session underperformance

When detected:

→ Trigger REVIEW protocol
→ Freeze parameter changes
→ Compare against ALGO_SPEC

---

7. SESSION ANALYSIS

Measure:

ASIA performance
LONDON performance
NY performance

Disable sessions if statistically negative over large sample.

---

8. PARAMETER IMPACT ANALYSIS

When modifying any parameter:

Must compare:

- Before vs after WR
- Before vs after expectancy
- Before vs after frequency
- Before vs after drawdown

No parameter change allowed without measurable improvement.

---

9. LONG-TERM VALIDATION

Minimum dataset for reliable validation:

- 200 trades per symbol
- 500 total trades minimum

Short-term results are noise.

Statistical confidence increases with sample size.

---

10. PERFORMANCE REPORT STRUCTURE

A performance report must include:

1. Total trades
2. Win rate
3. Expectancy
4. Max drawdown
5. Rejection breakdown
6. Session breakdown
7. Symbol breakdown
8. Buffer mode breakdown
9. Trend classification breakdown
10. Drift analysis

Reports must be generated periodically.

---

11. AUTOMATED ALERT THRESHOLDS

Engine should log warnings if:

- WR < 55% over last 100 trades
- Consecutive losses ≥ 6
- Rejection rate > 70%
- Signal frequency doubles unexpectedly

These are early instability indicators.

---

12. CAPITAL EFFICIENCY METRIC

Measure:

Capital Turnover Rate = Trades per day
Capital Utilization Efficiency = Winning trades / Active trades

Overtrading reduces efficiency even if WR acceptable.

---

13. ANTI-ILLUSION RULE

Never judge system by:

- Single day performance
- Single session performance
- Emotional reaction to streak
- 10-trade sample

Minimum statistically relevant sample required.

---

14. CONTINUOUS IMPROVEMENT LOOP

Cycle:

1. Deploy
2. Collect 200+ trades
3. Analyze metrics
4. Identify weakness
5. Adjust parameters
6. Re-test
7. Re-deploy

Never skip testing phase.

---

15. PERFORMANCE GUARANTEE

If analytics are followed:

- Edge is measurable
- Drift detectable
- Overfitting minimized
- Risk controlled
- Emotional interference reduced
- Long-term sustainability increased

Performance analytics converts strategy into a measurable system.

---

---

16. DATA SOURCES

Performance analytics relies on structured event data generated by the engine.

Primary data sources:

focus_history.jsonl  
distribution_logs.jsonl  
execution_results.jsonl (future extension)

focus_history.jsonl contains the complete lifecycle of every signal event.

Events include:

PRE_SENT  
CONFIRM_SENT  
OPEN_NOW_SENT  
FOCUS_ENTER  
FOCUS_EXIT  
REJECT_* events  

Each event includes:

timestamp  
symbol  
signal_id  
buffer_mode  
score  
expiry  
session  

Analytics must be computed from these raw events.

---

---

17. SIGNAL DATA PIPELINE

The analytics system processes the signal lifecycle pipeline.

Lifecycle model:

IDLE  
→ PRE  
→ CONFIRM  
→ OPEN_NOW  
→ EXECUTED  

Each stage is recorded in the event log.

The analytics engine reconstructs the full lifecycle using:

signal_id

This allows accurate conversion tracking:

PRE → CONFIRM  
CONFIRM → OPEN  
PRE → OPEN

---

---

18. SYMBOL EFFICIENCY INDEX

The system calculates an efficiency index for each symbol.

Formula components:

OPEN frequency  
PRE→OPEN conversion rate  
rejection rate  
focus stability

Example simplified score:

SEI = (OPEN_COUNT × CONVERSION_RATE) − REJECTION_FACTOR

High SEI symbols are considered optimal trading pairs.

Low SEI symbols may be removed from the symbol scan list.

This index supports long-term pair selection decisions.


---

---

19. FOCUS MECHANISM ANALYTICS

The performance system must evaluate the efficiency of the focus mechanism.

Metrics tracked:

focus_entries  
focus_exits  
focus_to_open_conversion

Focus efficiency = OPEN_NOW / FOCUS_ENTER

This metric measures the quality of setup detection.

A high ratio indicates that focus selection is accurate.

A low ratio may indicate overly sensitive PRE triggers.


---

20. OUTCOME DATA SOURCE

Trade outcomes are collected from the ELITE outcome reporting system.

Defined in:

TELEGRAM_UX.md

Outcome reporting occurs after the OPEN_NOW signal using the outcome panel.

Signal lifecycle becomes:

IDLE
→ PRE
→ CONFIRM
→ OPEN_NOW
→ OUTCOME_PANEL
→ RESULT

Possible results:

WIN
LOSE
MISSED

Outcome data is stored using:

SIGNAL_ID + USER_ID

Example record:

signal_id
symbol
direction
expiry
user_id
outcome
timestamp

These records form the real performance dataset of the system.

---

21. SIGNAL OUTCOME AGGREGATION

Each signal may produce multiple outcome reports from ELITE members.

Example:

Signal: EURUSD_M5_20260412_003

Votes:

WIN: 14  
LOSE: 5  
MISSED: 3

Aggregated result:

WIN_RATE_SIGNAL = WIN / (WIN + LOSE)

MISSED votes are excluded from performance metrics because the trade was not executed.

Example:

WIN_RATE_SIGNAL = 14 / (14 + 5) = 73.6%

This allows measuring signal performance independently from user participation.

---

22. USER PERFORMANCE TRACKING (ELITE)

Each ELITE user accumulates personal trading statistics.

Metrics tracked per user:

total_signals_seen  
wins  
losses  
missed  

Derived metrics:

personal_win_rate  
execution_rate  
participation_rate  

Example:

execution_rate = (wins + losses) / total_signals_seen

These metrics help evaluate:

- user discipline
- signal execution consistency
- community performance

Important:

User statistics are private.

Each user can only see their own statistics.

Only the system administrator may access full aggregated statistics.

---

23. SIGNAL RELIABILITY INDEX

Each signal generates a reliability score derived from community feedback.

Formula example:

SRI = WIN / (WIN + LOSE)

Signals with very low SRI may indicate:

- incorrect setup
- bad market condition
- algorithm weakness

Tracking SRI allows detection of:

weak symbols  
weak market sessions  
unstable setups  

This metric complements internal engine analytics.

---

24. DATA QUALITY SAFEGUARDS

To maintain statistical integrity the system must enforce:

• one vote per user per SIGNAL_ID  
• voting allowed only after trade expiry  
• voting window limited to 5 minutes  
• votes permanently locked once submitted  

Votes outside the allowed window must be rejected.

This prevents:

false early voting  
statistical manipulation  
duplicate reporting  

---

25. ANALYTICS GUARANTEE

If outcome reporting is combined with engine analytics:

The system obtains:

• real signal performance feedback  
• community execution statistics  
• symbol profitability insights  
• signal reliability measurement  

This transforms BinaryBot into a continuously learning trading system.



End of PERFORMANCE_ANALYTICS_SPEC.md