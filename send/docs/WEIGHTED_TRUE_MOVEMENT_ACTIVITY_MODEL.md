# WEIGHTED TRUE MOVEMENT ACTIVITY MODEL
Canonical Specification
Version: 1.0

---

# 1. Purpose

The purpose of this model is to replace the simplistic `avg_range` activity detection
used by the strategy engine with a more realistic representation of market activity.

The previous method:

    avg_range = mean(high - low)

fails to capture:

• recent volatility expansion
• true price displacement
• candle-to-candle momentum
• gap movement

This document defines a new canonical activity metric:

    Weighted True Movement (WTM)

---

# 2. True Movement Definition

For each candle i:

TrueMovement_i = max(

    high_i - low_i,

    abs(high_i - close_(i-1)),

    abs(low_i - close_(i-1))

)

This captures:

• intrabar range
• gap movement
• directional expansion

---

# 3. Weighted Activity Model

Instead of simple averaging, the system uses a weighted average
that prioritizes recent candles.

For the last N candles (default N = 10):

Weights:

    [1,1,1,2,2,3,3,4,5,6]

Where the most recent candles receive the largest weight.

The Weighted True Movement:

WTM = sum(TrueMovement_i * weight_i) / sum(weights)

---

# 4. Volatility Normalization

Raw activity must be normalized against market volatility.

Define:

    ATR_ref = ATR(M5)

Normalized Activity:

    ActivityRatio = WTM / ATR_ref

This ensures activity detection is:

• cross-symbol compatible
• volatility aware
• timeframe consistent

---

# 5. Activity Gate Condition

The activity gate becomes:

IF

    ActivityRatio < ACTIVITY_RATIO_THRESHOLD

THEN

    reject signal

Else

    allow PRE evaluation

---

# 6. Default Threshold

Recommended canonical threshold:

    ACTIVITY_RATIO_THRESHOLD = 0.18

Typical interpretation:

ActivityRatio < 0.10  → market idle
ActivityRatio 0.10-0.18 → weak movement
ActivityRatio > 0.18 → acceptable trading activity

---

# 7. Interaction With Existing Strategy

The Activity Model operates before:

PRE Gate
CONFIRM Gate
OPEN_NOW Gate

Pipeline:

Market Data
    ↓
Weighted True Movement
    ↓
Activity Ratio
    ↓
Activity Gate
    ↓
Strategy PRE evaluation

---

# 8. Compatibility With Trade Physics Model

WTM integrates naturally with the following models:

Trade Physics Score
Time-to-Buffer feasibility
Price Speed
Volatility Scaling

This ensures compatibility with the AI calibration layer.

---

# 9. Implementation Notes

This model replaces:

    avg_range

but does NOT replace ATR.

ATR remains the volatility normalization reference.

---

# 10. Implementation Scope

Files affected in code phase:

core/strategy_v2.py
core/signal_engine.py
core/scan_scheduler.py

However, implementation must occur only after this canonical specification is approved.

---

END OF SPEC
