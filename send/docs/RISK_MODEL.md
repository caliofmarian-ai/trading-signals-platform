# RISK_MODEL

Status: Satellite / Non-Canonical Reference
Canonical Position: Supporting document only; does not define active canonical truth.
Primary Active Canon: Refer to active canonical documents under /opt/binarybot/docs/canonical/active/

---

RISK_MODEL.md

Risk Control & Capital Protection Model — BinaryBot
Version: 1.0.0
Status: Canonical
Linked Documents: ALGO_SPEC_v2.0.0.md, FSM_DECISION_ENGINE_SPEC_v1.0.0.md, TELEGRAM_UX_v2.0.0.md, PARAMS_REFERENCE.md, CHECKLIST.md

---

1. PURPOSE

This document defines the complete risk logic behind the strategy.

It governs:

- Signal filtering discipline
- Capital protection logic
- Trade quality control
- Volatility defense
- Execution timing discipline
- Loss containment structure

This is the defensive backbone of the system.

The objective is not frequency.
The objective is capital preservation and statistical edge protection.

---

2. CORE RISK PHILOSOPHY

The engine must obey these principles:

1. Capital > Frequency
2. Quality > Quantity
3. Structure > Momentum
4. Stability > Aggression
5. Determinism > Emotion

The system is designed to reject more trades than it accepts.

Rejection is protection.

---

3. RISK LAYERS

The strategy operates through multiple defensive layers.

A trade must pass ALL layers to be allowed.

Layer hierarchy:

1. Structural integrity
2. Volatility stability
3. Feasibility logic
4. Directional bias validation
5. Score threshold
6. FSM state validation

Failure in any layer = REJECT.

---

4. STRUCTURAL RISK CONTROL (SR GATE)

Purpose:
Prevent trades too close to support/resistance.

Rule:

Available space ≥ sr_required_multiplier × buffer_price

If violated:
→ REJECT

Reason:
Binary expiry trades cannot tolerate structural compression.

Risk if removed:

- Frequent reversals
- Low win rate
- Increased drawdown

---

5. VOLATILITY RISK CONTROL (SPIKE FILTER)

Purpose:
Avoid unstable or manipulated conditions.

The spike filter blocks signals if ANY condition is met:

- Range z-score exceeds threshold
- Wick/body ratio exceeds threshold
- ATR acceleration exceeds threshold
- Jump vs ATR exceeds threshold

If spike active:
→ REJECT
→ Possible cooldown applied

Reason:
Volatility spikes distort statistical predictability.

---

6. FEASIBILITY CONTROL

Purpose:
Ensure the move can realistically complete before expiry.

Formula:

t_needed = buffer / (ATR × momentum_factor) × trend_time_adjust

Constraint:

t_needed ≤ expiry_time

If violated:
→ REJECT

Reason:
Prevents unrealistic expectations of price travel.

---

7. TREND RISK MANAGEMENT

Trend classification:

- With trend
- Flat
- Counter-trend

Risk adjustments:

With trend:

- Smaller buffer
- Shorter expiry

Flat:

- Moderate buffer
- Slightly longer expiry

Counter-trend:

- Larger buffer
- Longer expiry

Purpose:
Compensate statistically for directional disadvantage.

---

8. MOMENTUM RISK MODULATION

Momentum factor increases or decreases expected velocity.

Components:

- RSI displacement from neutral
- Body expansion ratio

Effect:
High momentum → shorter expiry
Low momentum → longer expiry

Clamped to prevent instability.

---

9. SCORE-BASED RISK FILTERING

Score range: 0–100

Modules:

Trend Score
Momentum Score
Entry Timing Score
Structure Score
Volatility Score

Threshold gates:

PRE ≥ 70
CONFIRM ≥ 75
OPEN ≥ 80

Lower score → informational only
Higher score → execution eligible

No OPEN without sufficient composite strength.

---

10. COOLDOWN MODEL

After OPEN and /open confirmation:

Symbol enters COOLDOWN state.

Purpose:

- Prevent revenge trading
- Prevent repeated entry on same structure
- Avoid overexposure

Cooldown duration:
Configured via spike filters or static value.

During cooldown:
No PRE
No CONFIRM
No OPEN

Cooldown must survive restart.

---

11. MAX CONCURRENT EXPOSURE CONTROL

System-level constraint:

Maximum 2 symbols in WATCHLIST.

Purpose:

- Limit cognitive overload
- Limit correlated exposure
- Prevent signal clustering risk

Additional PRE ignored if full.

---

12. DEDUPLICATION PROTECTION

Each signal must be uniquely keyed by:

symbol + candle_timestamp + signal_type

Prevents:

- Duplicate LIVE
- Duplicate CONFIRM
- Signal spam
- Restart signal replay

---

13. BUFFER RISK LOGIC

Buffer absorbs noise.

Higher buffer:

- Higher required movement
- Lower false entry probability
- Lower trade frequency

Lower buffer:

- Faster entries
- Higher noise exposure
- Higher risk

Buffer selection is strategic, not cosmetic.

---

14. EXPIRY RISK LOGIC

Expiry too short:
→ Incomplete move
→ Artificial loss

Expiry too long:
→ Structural reversal risk
→ Capital lock

Dynamic expiry aligns move expectation with volatility.

---

15. FAILURE SCENARIOS PROTECTED AGAINST

The risk model explicitly prevents:

- Overtrading in volatility spike
- Trading inside compression zone
- Re-entry during cooldown
- Execution without sufficient structure
- Duplicate signal storms
- Counter-trend underpowered trades

---

16. WHAT THIS MODEL DOES NOT CONTROL

This engine does NOT control:

- Position sizing
- Account leverage
- External broker risk
- Slippage execution

Capital management per trade is outside this document.

---

17. RISK ESCALATION EVENTS

If any of the following detected:

- Repeated spike rejections
- Frequent feasibility failures
- Sudden win-rate drop
- Unexpected signal frequency change

Required action:

- Freeze trading
- Audit parameters
- Review recent changes
- Compare behavior to ALGO_SPEC

---

18. RISK GUARANTEE

If implemented exactly as specified:

- Trade quality remains stable
- Volatility traps are filtered
- Structural traps are avoided
- Emotional overtrading prevented
- Signal spam impossible
- Deterministic capital protection ensured

This is a defensive-first system.

---

End of RISK_MODEL.md

## Non-Canonical Usage Note

This document is retained as a supporting/satellite reference only. It must not be treated as active canonical truth. Where conflict exists, active canonical documents in /opt/binarybot/docs/canonical/active/ take precedence.
