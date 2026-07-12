# RESEARCH_AND_LEARNING_FRAMEWORK_SPEC.md
BinaryBot — Research, Learning & Trial Validation Framework
Version: 1.0.0
Status: Canonical

Linked Documents:
ALGO_SPEC.md
PERFORMANCE_ANALYTICS_SPEC.md
OBSERVABILITY_LOGGING_SPEC.md
SYSTEM_INVARIANTS.md
PARAMS_REFERENCE.md
TELEGRAM_UX.md

---

# 1. PURPOSE

This document defines the complete research and learning framework used by BinaryBot.

The framework converts runtime data into strategic insight and continuous strategy improvement.

It integrates three layers:

1. Focus learning dataset (engine events)
2. Trial outcome dataset (WIN/LOSS validation)
3. Strategy research analytics

Goals:

- identify profitable symbols
- evaluate signal conversion quality
- detect weak symbols and wasted setups
- validate the strategy edge using real outcomes
- support controlled parameter experimentation
- guide long-term strategy evolution

Without structured research and trial capture, strategy improvement becomes unreliable and subjective.

---

# 2. SYSTEM ARCHITECTURE

The research system follows a structured pipeline.

ENGINE SIGNAL EVENTS
↓
FOCUS_HISTORY DATASET
↓
TRIAL RESULTS DATASET
↓
RESEARCH ANALYTICS
↓
STRATEGY OPTIMIZATION

Each layer has clearly defined responsibilities.

---

# 3. FOCUS LEARNING DATASET

The engine records lifecycle events for every potential signal.

Primary storage:

/opt/binarybot/logs/focus_history.jsonl

Format:
Append-only JSONL.

Rules:

• every lifecycle event is recorded  
• history is never rewritten  
• data survives restart  
• duplicates must be prevented  

---

# 4. FOCUS EVENTS

The following event types must exist.

Focus lifecycle:

FOCUS_ENTER  
FOCUS_EXIT  

Signal lifecycle:

PRE_SENT  
CONFIRM_SENT  
OPEN_NOW_SENT  

Rejection / gate events:

REJECT_SPIKE  
REJECT_SR_SPACE  
REJECT_FEASIBILITY  
REJECT_SCORE  

Cooldown events:

COOLDOWN_START  
COOLDOWN_END  

Operator actions:

ADMIN_SET_SYMBOLS  
ADMIN_SET_BUFFER_MODE  
ADMIN_RELEASE_FOCUS  
DAILY_RESET

---

# 5. FOCUS EVENT SCHEMA

Each JSONL entry contains:

ts_utc  
event  
symbol  
signal_id  
buffer_mode  
score  
expiry_sec  
buffer_value  
buffer_extra  
focus_slot  
session  
reason  
meta

Example:

{
  "ts_utc": "2026-03-04T08:14:22Z",
  "event": "OPEN_NOW_SENT",
  "symbol": "EUR/USD",
  "signal_id": "EURUSD_M1_20260304_004",
  "buffer_mode": "MEDIUM",
  "score": 86,
  "expiry_sec": 300,
  "buffer_value": 5.8,
  "focus_slot": 1,
  "session": "LONDON",
  "meta": {"algo_version":"1.0.0"}
}

---

# 6. TRIAL DATASET (REAL OUTCOME VALIDATION)

Trial capture records the real outcome of OPEN_NOW signals.

Purpose:

Validate the statistical edge of the strategy.

A trial is defined as:

OPEN_NOW signal + confirmed result (WIN or LOSS).

---

# 7. TRIAL ID

Each trial has a deterministic identifier.

trial_id format:

{algo_version}|{params_hash}|{symbol}|{open_ts}|{expiry}|{side}

Example:

1.0.0|a1b2c3d4|EUR/USD|2026-03-03T12:34:00Z|180|BUY

This ensures reproducibility across datasets.

---

# 8. TRIAL STORAGE

Primary storage:

/opt/binarybot/data/trials.jsonl

Rules:

• append-only log  
• corrections recorded as new events  
• historical data never overwritten  

Supporting files:

/opt/binarybot/data/trials_index.json  
/opt/binarybot/data/pending_trials.json

---

# 9. TRIAL EVENT TYPES

OPEN_NOW  
RESULT  
REVISE  
VOID

Meaning:

OPEN_NOW → signal generated  
RESULT → result recorded (WIN/LOSS)  
REVISE → correction event  
VOID → trade invalidated

Latest event timestamp defines final state.

---

# 10. TELEGRAM RESULT COMMANDS

Admin records outcomes through Telegram commands.

Primary command:

/result SYMBOL WIN  
/result SYMBOL LOSS

Alternative command:

/result_id TRIAL_ID WIN  
/result_id TRIAL_ID LOSS

Support commands:

/pending  
/void  
/revise  

These commands update the trial dataset.

---

# 11. TRIAL VALIDATION RULES

1. Trials enter pending list only after OPEN_NOW is sent.
2. Each trial may have only one final outcome.
3. Result corrections must use REVISE events.
4. Engine restart must reload pending trials safely.
5. Duplicate trial IDs are forbidden.

---

# 12. RESEARCH OBJECTIVES

The research layer answers strategic questions:

Which symbols generate the most valid trades?

Which symbols waste scanning resources?

Which buffer modes produce the best conversions?

Which market sessions perform best?

Which market regimes degrade performance?

---

# 13. SYMBOL PERFORMANCE ANALYSIS

For each symbol compute:

PRE_count  
CONFIRM_count  
OPEN_count  

Derived metrics:

PRE_to_OPEN_rate  
CONFIRM_to_OPEN_rate  
rejection_rate  
cooldown_rate

Symbols are classified as:

Strong symbols  
Neutral symbols  
Weak symbols

---

# 14. SYMBOL PERFORMANCE SCORE

Example scoring model:

SymbolScore =

OPEN_WEIGHT × OPEN_count
+ CONVERSION_WEIGHT × PRE_to_OPEN_rate
− REJECTION_WEIGHT × rejection_rate

Symbols with higher scores receive higher priority.

---

# 15. BUFFER MODE RESEARCH

Evaluate buffer modes:

SMALL  
MEDIUM  
LARGE

Metrics:

PRE frequency  
OPEN frequency  
conversion ratio  
reject distribution

Goal:

Find the optimal balance between signal quality and frequency.

---

# 16. SESSION PERFORMANCE ANALYSIS

Sessions analyzed:

ASIA  
LONDON  
NEW YORK  
LATE

Metrics:

OPEN frequency  
conversion rate  
average expiry  
rejection distribution

---

# 17. MARKET REGIME ANALYSIS

Performance must be evaluated across volatility regimes.

Regimes:

Low volatility  
Normal volatility  
High volatility

Metrics:

signal frequency  
conversion rate  
reject distribution

---

# 18. STRATEGY DRIFT DETECTION

Performance degradation may indicate:

market structure changes  
volatility regime shifts  
parameter misconfiguration  
symbol instability

Research must isolate the cause before changes are applied.

---

# 19. PARAMETER EXPERIMENTATION

Parameter changes must follow controlled experiments.

Example parameters:

buffer multipliers  
expiry ranges  
score thresholds  

Process:

1. Define hypothesis
2. Apply parameter change
3. Collect sufficient dataset (minimum 200 trades)
4. Compare performance before and after

Only statistically validated improvements are accepted.

---

# 20. SYMBOL ROTATION POLICY

Symbols may be added or removed from the WIDE_SCAN universe based on research evidence.

Possible actions:

add new symbol  
pause unstable symbol  
remove consistently weak symbol

---

# 21. RESEARCH REPORTS

Periodic reports should include:

symbol ranking  
conversion rates  
rejection breakdown  
session statistics  
buffer mode comparison  

These reports guide operator decisions.

---

# 22. CONTINUOUS STRATEGY EVOLUTION

The research cycle follows:

collect runtime data  
capture trial outcomes  
analyze performance  
identify weaknesses  
test improvements  
deploy validated changes

This cycle ensures that BinaryBot adapts to evolving market conditions.

---

# 23. GUARANTEES

If this framework is implemented correctly:

• the strategy edge becomes measurable  
• experiments become reproducible  
• weak symbols are identified early  
• emotional parameter changes are minimized  
• long-term strategy stability improves  

Research and learning convert the bot from a static system into a continuously improving trading engine.

---

End of RESEARCH_AND_LEARNING_FRAMEWORK_SPEC.md