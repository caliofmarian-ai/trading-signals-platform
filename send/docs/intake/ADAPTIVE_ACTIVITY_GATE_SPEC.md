# ADAPTIVE_ACTIVITY_GATE_SPEC.md

## Purpose

The Adaptive Activity Gate replaces the previous static `MIN_AVG_RANGE` filter
with a volatility-normalized activity detection mechanism.

The objective is to ensure that the trading engine evaluates opportunities
based on relative market activity, not fixed thresholds.

This prevents:

- inactivity false positives
- symbol-specific volatility bias
- blocking the decision pipeline before scoring

---

## Problem With Static Threshold

Previous logic:

```text
avg_range >= MIN_AVG_RANGE

Examples observed in runtime:

EUR/USD-class symbols can show avg_range around 0.00010 while fixed threshold is 0.00025

JPY pairs can show avg_range around 0.022 while fixed threshold is 0.025


These values may represent normal live market conditions, but the fixed gate rejects them as inactive.

Result:

Activity Gate FAIL
→ Score not computed
→ PRE not computed
→ CONFIRM not computed
→ OPEN_NOW not possible


---

Adaptive Activity Gate Model

Instead of constant thresholds, the activity gate is normalized using recent market volatility.

Core principle:

activity_ratio = avg_range / atr_reference

Where:

avg_range     = average candle range over the recent decision window
atr_reference = ATR from the same symbol / timeframe family used by the strategy

The gate must decide activity using relative movement, not absolute price units.


---

Canonical Rule

activity_ratio >= ACTIVITY_VOL_THRESHOLD

Recommended default:

ACTIVITY_VOL_THRESHOLD = 0.20

Meaning:

The market must move at least 20% of ATR scale to be considered active enough for strategy scoring.


---

Volatility Normalization

Volatility normalization allows the same rule to work consistently for:

low-volatility forex pairs

high-volatility forex pairs

JPY pairs

crypto symbols

future multi-asset universes


without manual per-symbol hardcoded thresholds.


---

Decision Engine Position

The canonical pipeline becomes:

Activity Gate
    ↓
Score Calculation
    ↓
PRE
    ↓
CONFIRM
    ↓
OPEN_NOW

The activity gate should only block the pipeline when market movement is statistically insignificant relative to volatility.

It must not block symbols merely because they have smaller absolute decimal ranges.


---

Interaction With Focus Scheduler

The Adaptive Activity Gate applies inside the signal evaluation layer.

Its outputs affect:

wide scan candidate viability
focus candidate viability
symbol eligibility for scoring

Symbols failing the activity gate remain observable in runtime, but do not advance into score-based decision states.


---

Strategic Impact

Adaptive gating is required because the previous static threshold model caused:

zero-signal runtime periods

under-sampling of real market opportunities

loss of telemetry for calibration

inability to generate outcome datasets


Adaptive gating improves:

signal availability

symbol fairness

runtime realism

dataset generation quality

future calibration quality



---

AI / Learning Relevance

The Adaptive Activity Gate directly improves dataset quality for:

Trade Physics Score analytics

outcome modeling

strategy calibration

symbol-specific intelligence

future ML ranking layers


The activity gate must therefore be documented as part of the canonical intelligence architecture, not only as a low-level filter.


---

Canonical Parameters

The following canonical parameters are introduced:

ACTIVITY_VOL_THRESHOLD
ACTIVITY_LOOKBACK_CANDLES
ACTIVITY_ATR_SOURCE

Recommended initial semantics:

ACTIVITY_VOL_THRESHOLD = minimum normalized movement required
ACTIVITY_LOOKBACK_CANDLES = candle window used for avg_range
ACTIVITY_ATR_SOURCE = ATR source timeframe used for normalization


---

Canonical Observability Requirement

Decision logs must record enough information to audit activity behavior.

Minimum required observability fields:

avg_range
atr_reference
activity_ratio
activity_threshold
activity_gate_ok
activity_gate_reason

This requirement is mandatory for future calibration.


---

Decision Audit Requirement

When a symbol is rejected by activity gate, the audit layer must be able to explain:

symbol
avg_range
atr_reference
activity_ratio
threshold_used
reason_for_rejection

This is necessary to distinguish:

true inactivity

threshold miscalibration

symbol mismatch

volatility regime changes



---

Migration Rule

From this point forward, static MIN_AVG_RANGE logic is considered legacy.

Canonical strategy direction is:

legacy absolute threshold
→ replaced by adaptive volatility-normalized threshold

Backward compatibility may temporarily exist in code during migration, but canonical strategy authority belongs to the adaptive model.


---

Related Canonical Documents

This specification is linked to:

ALGO_SPEC.md

STRATEGY_LOGIC_SPEC.md

DECISION_AUDIT_SPEC.md

TRADE_TEMPORAL_TELEMETRY_SPEC.md

AI_TRADE_PHYSICS_SPACE_MODEL_SPEC.md

TRADE_PHYSICS_SCORE_SPEC.md



---

Summary

The Adaptive Activity Gate replaces static activity thresholds with volatility-normalized activity evaluation.

Canonical formula:

activity_ratio = avg_range / atr_reference

Canonical rule:

activity_ratio >= ACTIVITY_VOL_THRESHOLD

This change is necessary to:

unblock live signal generation

improve runtime realism

enable telemetry collection

support later AI calibration

ensure cross-symbol fairness


