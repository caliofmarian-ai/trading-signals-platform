# PARAMS_REFERENCE

Status: Legacy Superseded Reference
Superseded By: STRATEGY_PARAMETER_CONTROL_SPEC_v2.0.0.md
Canonical Position: Deprecated; do not use as active truth.

---

PARAMS_REFERENCE.md

Parameter Reference — BinaryBot Strategy Engine
Version: 1.0.0
Status: Canonical
Linked Documents: ALGO_SPEC.md, FSM_SPEC.md, TELEGRAM_UX.md, CHECKLIST.md

---

1. PURPOSE

This document defines:

- All configurable parameters used by the engine
- Their meaning
- Their valid ranges
- Their effect on behavior
- Their risk impact

This is the single source of truth for configuration behavior.

No parameter may exist outside this specification.

---

2. GLOBAL STRUCTURE (algo_params.json)

Canonical structure:

{
"algo_version": "1.0.0",

"buffer_multipliers": {},
"expiry_limits_minutes": {},
"trend_time_adjust": {},
"momentum_factor": {},
"sr_required_multiplier": 0.0,
"score_thresholds": {},
"crypto_points_rounding": 0,
"spike_filters": {}
}

---

3. VERSIONING

3.1 algo_version

Type: string
Example: "1.0.0"

Purpose:

- Displayed at startup
- Logged in SYSTEM_ALERTS
- Used for audit traceability

Rules:

- Must be bumped on structural logic change
- PATCH for minor tuning
- MINOR for threshold/weight changes
- MAJOR for structural changes

---

4. BUFFER PARAMETERS

4.1 buffer_multipliers

Structure:

"buffer_multipliers": {
"SMALL": 0.35,
"MEDIUM": 0.55,
"LARGE": 0.80
}

Meaning:
Base ATR multiplier used in buffer calculation.

Formula:

buffer_price = ATR_M1 × multiplier × trend_factor × structure_factor

Effect:
Higher multiplier →

- Larger buffer
- Longer expiry
- Fewer signals
- Higher quality entries

Valid Range:
0.2 – 1.5

Risk Impact:
Lower multiplier increases false entries.

---

5. EXPIRY LIMITS

5.1 expiry_limits_minutes

Structure:

"expiry_limits_minutes": {
"min": 2,
"max": 15
}

Meaning:
Clamps dynamic expiry computation.

Formula:

expiry_minutes = clamp(calculated_value, min, max)

Effect:
Prevents extreme short/long expiries.

Valid Range:
min ≥ 1
max ≤ 30

Risk:
Too low max → forced early expiration
Too high max → capital lock inefficiency

---

6. TREND TIME ADJUST

6.1 trend_time_adjust

Structure:

"trend_time_adjust": {
"with_trend": 0.90,
"flat": 1.05,
"counter_trend": 1.20
}

Meaning:
Multiplier applied to expiry calculation.

Effect:
With trend → shorter expiry
Counter trend → longer expiry

Valid Range:
0.7 – 1.5

Risk:
Too aggressive reduction may undercut move completion.

---

7. MOMENTUM FACTOR

7.1 momentum_factor

Structure:

"momentum_factor": {
"r_weight": 0.6,
"b_weight": 0.4,
"min": 0.7,
"max": 1.6
}

Meaning:
Adjusts expected price velocity.

Components:

r_weight → RSI influence
b_weight → Candle body expansion influence

Formula:

momentum_factor = clamp(
1 + (r_weight × RSI_component) + (b_weight × body_component),
min,
max
)

Effect:
Higher momentum_factor →
Shorter expiry

Risk:
Excessive max → unrealistic velocity expectation

---

8. SUPPORT / RESISTANCE CONTROL

8.1 sr_required_multiplier

Type: float
Example: 1.10

Meaning:
Required free space multiplier.

Rule:

SR distance ≥ sr_required_multiplier × buffer_price

Effect:
Ensures enough room before hitting resistance/support.

Valid Range:
1.0 – 2.0

Risk:
Too low → trades too close to structure
Too high → very few trades

---

9. SCORE THRESHOLDS

9.1 score_thresholds

Structure:

"score_thresholds": {
"PRE": 70,
"CONFIRM": 75,
"OPEN": 80
}

Meaning:
Score gates for state transitions.

Rules:

Score ≥ PRE → PRE allowed
Score ≥ CONFIRM → CONFIRM allowed
Score ≥ OPEN → OPEN_NOW allowed

Valid Range:
50 – 95

Risk:
Lower thresholds → spam
Higher thresholds → low frequency

---

10. CRYPTO ROUNDING

10.1 crypto_points_rounding

Type: integer
Example: 2

Meaning:
Decimal precision for crypto buffer display.

Effect:
Controls output formatting only.

No strategy impact.

---

11. SPIKE FILTERS

11.1 spike_filters

Structure:

"spike_filters": {
"range_zscore_threshold": 2.5,
"wick_body_ratio_threshold": 2.0,
"atr_fast_slow_ratio_threshold": 1.6,
"jump_vs_atr_threshold": 0.8,
"cooldown_seconds_mild": 60,
"cooldown_seconds_heavy": 180
}

---

11.1.1 range_zscore_threshold

Blocks extreme volatility expansion.

Lower value → stricter filter

---

11.1.2 wick_body_ratio_threshold

Blocks unstable candles with long wicks.

High wick/body = indecision or manipulation.

---

11.1.3 atr_fast_slow_ratio_threshold

Detects volatility acceleration.

atr_fast / atr_slow ≥ threshold → spike.

---

11.1.4 jump_vs_atr_threshold

Measures sudden gap relative to ATR.

Blocks sharp jumps.

---

11.1.5 cooldown_seconds_mild

Short volatility pause.

---

11.1.6 cooldown_seconds_heavy

Severe volatility lockout.

---

12. PARAMETER SAFETY RULES

1. No parameter may be unused.
2. All parameters must be loaded from algo_params.json.
3. No hardcoded constants allowed in engine.
4. Default fallback must match this document.
5. Parameter changes require CHANGELOG update.

---

13. RISK CONTROL PRINCIPLE

Parameters affect:

- Trade frequency
- Entry quality
- Expiry duration
- Volatility tolerance
- Structural safety margin

Improper tuning directly increases loss probability.

---

14. FINAL GUARANTEE

If all parameters follow this reference:

- Engine behavior is predictable
- Risk model is controlled
- No hidden logic exists
- No untracked constants exist
- Full transparency achieved

---

End of PARAMS_REFERENCE.md

## Deprecation Note

This document has been deprecated. Active parameter-control truth now lives in `STRATEGY_PARAMETER_CONTROL_SPEC_v2.0.0.md` under canonical active.
