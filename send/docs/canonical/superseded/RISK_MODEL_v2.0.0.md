# RISK_MODEL_v2.0.0.md

**Canonical Name:** RISK_MODEL  
**Version:** 2.0.0  
**Status:** Active Canonical Specification  
**Owner:** BinaryBot / DROPi Signals  
**Canonical Path:** `send/docs/canonical/active/RISK_MODEL_v2.0.0.md`  
**Governance Record:** canonical-reconciliation-01 (OWNER-006 = A)  
**Promoted:** 2026-07-12  

**Authority:** This document is the authoritative canonical specification for the risk control and capital protection model of BinaryBot / DROPi Signals. All risk logic, trade filtering discipline, and capital protection decisions must conform to this document.

**Predecessor / Superseded Documents:**  
- `send/docs/RISK_MODEL.md` — root-level source document; retained as historical record, superseded by this canonical version.  

**Linked Documents:**  
- `send/docs/canonical/active/ALGO_SPEC_v2.0.0.md`  
- `send/docs/canonical/active/FSM_DECISION_ENGINE_SPEC_v1.0.0.md`  
- `send/docs/canonical/active/TELEGRAM_UX_v2.0.0.md`  
- `send/docs/canonical/active/SYSTEM_INVARIANTS_v2.0.0.md`  
- `send/docs/canonical/active/FAILURE_RECOVERY_SPEC_v2.0.0.md`  
- `send/docs/canonical/active/SECURITY_MODEL_v2.0.0.md`  
- `send/docs/canonical/active/SIGNAL_ENGINE_EXECUTION_SPEC_v2.0.0.md`  

---

## 1. PURPOSE

This document defines the complete risk logic behind the strategy.

It governs:

- Signal filtering discipline
- Capital protection logic
- Trade quality control
- Volatility defense
- Execution timing discipline
- Loss containment structure

This is the defensive backbone of the system.

The objective is not frequency. The objective is capital preservation and statistical edge protection.

---

## 2. CORE RISK PHILOSOPHY

The engine must obey these principles:

1. Capital > Frequency
2. Quality > Quantity
3. Structure > Momentum
4. Stability > Aggression
5. Determinism > Emotion

The system is designed to reject more trades than it accepts.

**Rejection is protection.**

---

## 3. RISK LAYERS

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

## 4. STRUCTURAL RISK CONTROL (SR GATE)

**Purpose:** Prevent trades too close to support/resistance.

**Rule:** Available space ≥ `sr_required_multiplier × buffer_price`

If violated: → REJECT

**Reason:** Binary expiry trades cannot tolerate structural compression.

Risk if removed:

- Frequent reversals
- Low win rate
- Increased drawdown

---

## 5. VOLATILITY RISK CONTROL (SPIKE FILTER)

**Purpose:** Avoid unstable or manipulated conditions.

The spike filter blocks signals if ANY condition is met:

- Range z-score exceeds threshold
- Wick/body ratio exceeds threshold
- ATR acceleration exceeds threshold
- Jump vs ATR exceeds threshold

If spike active: → REJECT → Possible cooldown applied

**Reason:** Volatility spikes distort statistical predictability.

---

## 6. FEASIBILITY CONTROL

**Purpose:** Ensure the move can realistically complete before expiry.

Formula:

```
t_needed = buffer / (ATR × momentum_factor) × trend_time_adjust
```

Constraint: `t_needed ≤ expiry_time`

If violated: → REJECT

**Reason:** Prevents unrealistic expectations of price travel.

---

## 7. TREND RISK MANAGEMENT

Trend classification:

- With trend
- Flat
- Counter-trend

Risk adjustments:

| Trend | Buffer | Expiry |
|---|---|---|
| With trend | Smaller | Shorter |
| Flat | Moderate | Slightly longer |
| Counter-trend | Larger | Longer |

**Purpose:** Compensate statistically for directional disadvantage.

---

## 8. MOMENTUM RISK MODULATION

Momentum factor increases or decreases expected velocity.

Components:

- RSI displacement from neutral
- Body expansion ratio

Effect:

- High momentum → shorter expiry
- Low momentum → longer expiry

Clamped to prevent instability.

---

## 9. SCORE-BASED RISK FILTERING

Score range: 0–100

Modules:

- Trend Score
- Momentum Score
- Entry Timing Score
- Structure Score
- Volatility Score

Threshold gates:

| Stage | Minimum Score |
|---|---|
| PRE | ≥ 70 |
| CONFIRM | ≥ 75 |
| OPEN | ≥ 80 |

Lower score → informational only  
Higher score → execution eligible

No OPEN without sufficient composite strength.

---

## 10. COOLDOWN MODEL

After OPEN and `/open` confirmation: symbol enters COOLDOWN state.

**Purpose:**

- Prevent revenge trading
- Prevent repeated entry on same structure
- Avoid overexposure

Cooldown duration: configured via spike filters or static value.

During cooldown: No PRE, No CONFIRM, No OPEN

**Cooldown must survive restart.**

---

## 11. MAX CONCURRENT EXPOSURE CONTROL

System-level constraint: **Maximum 2 symbols in WATCHLIST.**

**Purpose:**

- Limit cognitive overload
- Limit correlated exposure
- Prevent signal clustering risk

Additional PRE ignored if full.

---

## 12. DEDUPLICATION PROTECTION

Each signal must be uniquely keyed by: `symbol + candle_timestamp + signal_type`

Prevents:

- Duplicate LIVE
- Duplicate CONFIRM
- Signal spam
- Restart signal replay

---

## 13. BUFFER RISK LOGIC

Buffer absorbs noise.

| Buffer Level | Effect |
|---|---|
| Higher buffer | Higher required movement; lower false entry probability; lower trade frequency |
| Lower buffer | Faster entries; higher noise exposure; higher risk |

Buffer selection is strategic, not cosmetic.

---

## 14. EXPIRY RISK LOGIC

| Expiry Setting | Risk |
|---|---|
| Too short | Incomplete move → artificial loss |
| Too long | Structural reversal risk → capital lock |

Dynamic expiry aligns move expectation with volatility.

---

## 15. FAILURE SCENARIOS PROTECTED AGAINST

The risk model explicitly prevents:

- Overtrading in volatility spike
- Trading inside compression zone
- Re-entry during cooldown
- Execution without sufficient structure
- Duplicate signal storms
- Counter-trend underpowered trades

---

## 16. WHAT THIS MODEL DOES NOT CONTROL

This engine does NOT control:

- Position sizing
- Account leverage
- External broker risk
- Slippage execution

Capital management per trade is outside this document.

---

## 17. RISK ESCALATION EVENTS

If any of the following detected:

- Repeated spike rejections
- Frequent feasibility failures
- Sudden win-rate drop
- Unexpected signal frequency change

Required action:

1. Freeze trading
2. Audit parameters
3. Review recent changes
4. Compare behavior to `ALGO_SPEC_v2.0.0.md`

---

## 18. RISK GUARANTEE

If implemented exactly as specified:

- Trade quality remains stable
- Volatility traps are filtered
- Structural traps are avoided
- Emotional overtrading prevented
- Signal spam impossible
- Deterministic capital protection ensured

This is a defensive-first system.

---

## 19. CANONICAL VERSION HISTORY

| Version | Date | Description |
|---|---|---|
| 2.0.0 | 2026-07-12 | Promoted to active canonical status (OWNER-006 = A, canonical-reconciliation-01). Removed non-canonical header/footer annotations. Cross-references updated to canonical v2.0.0 paths. |
| 1.0.0 | — | Root-level source document: `send/docs/RISK_MODEL.md` |

---

*End of RISK_MODEL_v2.0.0.md*
