TRADING_RESEARCH_SPEC

BinaryBot — Strategy Research & Optimization Framework
Version: 1.0.0
Status: Canonical

Linked Documents:
ALGO_SPEC.md
PERFORMANCE_ANALYTICS_SPEC.md
FOCUS_LEARNING_SPEC.md
RISK_MODEL.md
PARAMS_REFERENCE.md

---

1. PURPOSE

This document defines the research methodology used to evaluate and improve the trading strategy.

The research layer converts raw performance data into strategic decisions.

It ensures that:

• symbol selection is data-driven
• parameter tuning is evidence-based
• strategy evolution is controlled
• long-term profitability remains stable

Without structured research the strategy risks drifting or overfitting.

---

2. RESEARCH OBJECTIVES

The research system must answer the following questions:

Which symbols generate the most valid trades?

Which symbols waste scanning resources?

Which buffer mode produces the most reliable signals?

Which market sessions offer the best opportunities?

Which market regimes reduce strategy performance?

These answers guide system optimization.

---

3. SYMBOL SELECTION PROCESS

Symbols in the WIDE SCAN list must be selected based on statistical evidence.

Evaluation metrics:

PRE signals generated
OPEN_NOW signals generated
PRE → OPEN conversion rate
rejection frequency

Symbols are classified as:

Strong symbols
Neutral symbols
Weak symbols

Strong symbols remain in the WIDE LIST.

Weak symbols may be removed from the scan universe.

---

4. SYMBOL PERFORMANCE SCORE

Each symbol receives a research score.

Example structure:

Symbol Score =

OPEN_NOW_WEIGHT × OPEN_NOW_COUNT

+ CONVERSION_WEIGHT × PRE_TO_OPEN_RATE
  − REJECTION_WEIGHT × REJECTION_RATE

Symbols with higher scores are prioritized in scanning.

Symbols with consistently low scores should be reviewed.

---

5. WIDE SCAN UNIVERSE MANAGEMENT

The WIDE SCAN universe defines which symbols the engine scans continuously.

Rules:

Only symbols with acceptable research scores should remain in the list.

Symbols may be temporarily disabled if performance drops.

The WIDE LIST should prioritize:

• high payout pairs
• stable market behavior
• reliable signal generation

---

6. BUFFER OPTIMIZATION RESEARCH

Buffer modes must be evaluated through historical data.

Compare:

SMALL
MEDIUM
LARGE

Metrics used:

PRE signal count
OPEN_NOW signal count
conversion ratio
rejection rate

Research must determine which buffer produces the best balance between:

signal quality
signal frequency

---

7. SESSION PERFORMANCE RESEARCH

Market behavior varies by session.

Sessions analyzed:

ASIA
LONDON
NEW YORK

Metrics tracked:

signal frequency
conversion rate
rejection rate

Sessions producing consistently poor results may be avoided.

---

8. MARKET REGIME ANALYSIS

The system must evaluate strategy performance across different volatility regimes.

Regimes:

Low volatility
Normal volatility
High volatility

Metrics:

signal frequency
conversion rate
rejection rate

This helps determine if the strategy behaves differently under volatile conditions.

---

9. STRATEGY DRIFT INVESTIGATION

When performance degrades the research system must determine the cause.

Possible causes:

market structure changes
volatility regime shifts
overly restrictive parameters
symbol instability

Research must isolate the root cause before adjusting parameters.

---

10. PARAMETER EXPERIMENTATION

Parameter changes must follow controlled experimentation.

Example parameters:

buffer multipliers
expiry ranges
score thresholds

Process:

1. Define hypothesis
2. Apply parameter change
3. Collect data sample (minimum 200 trades)
4. Compare metrics before and after change

Only statistically validated improvements are accepted.

---

11. LONG-TERM STRATEGY VALIDATION

Strategy reliability must be evaluated over large datasets.

Minimum dataset requirements:

200 trades per symbol
500 total trades minimum

Short-term performance should not drive strategic decisions.

---

12. SYMBOL ROTATION POLICY

Symbols may be rotated based on performance.

Possible actions:

add new symbol to WIDE LIST
remove consistently weak symbol
pause symbol temporarily

Rotation must be based on statistical evidence.

---

13. RESEARCH REPORT STRUCTURE

A research report should include:

symbol ranking
conversion rates
rejection breakdown
session performance
buffer mode comparison

Reports must be generated periodically.

---

14. HUMAN OPERATOR ROLE

The system provides analytics.

Final research decisions remain with the operator.

The operator may:

update symbol list
change buffer mode
adjust parameters

However these decisions must be supported by data.

---

15. CONTINUOUS STRATEGY EVOLUTION

The research system creates a continuous improvement cycle:

collect data
analyze results
identify weaknesses
test improvements
deploy adjustments

This cycle ensures the strategy evolves with market conditions.

---

16. RESEARCH GUARANTEE

If this research framework is followed:

• strategy evolution becomes systematic
• emotional decisions are minimized
• profitable symbols are identified early
• weak symbols are eliminated
• long-term stability improves

Research transforms the trading bot into a continuously improving system.

---

End of TRADING_RESEARCH_SPEC.md