# SR_CORRIDOR_DETECTION_ENGINE_SPEC.md

## Status
Canonical Specification

## Purpose

This document defines the SR Corridor Detection Engine used by the strategy
runtime to detect whether price has a tradable free corridor between entry
and the nearest relevant support/resistance obstacle.

The engine upgrades the previous SR gate model from a binary blocker into a
market-structure navigation model.

Instead of only rejecting trades when SR space is insufficient, the engine
must classify the available path ahead of price and expose a corridor model
usable by:

- PRE detection
- CONFIRM validation
- OPEN_NOW execution
- Trade Physics Score
- AI training dataset generation

---

## Core Idea

A trade is not evaluated only by direction or score.

A trade must also have a navigable path.

This path is called:

SR Corridor

Definition:

SR Corridor = the price interval between candidate entry and the nearest
relevant obstacle in the direction of the trade

For BUY:

corridor_distance = nearest_resistance - entry_price

For SELL:

corridor_distance = entry_price - nearest_support


---

Engine Responsibilities

The SR Corridor Detection Engine must:

1. detect nearest relevant support/resistance

2. measure free path distance in trade direction

3. compute corridor quality metrics

4. classify corridor tradability

5. expose corridor telemetry to decision engine

6. support entry-point optimization

7. support expiry estimation

8. support TPS / AI dataset generation

---

Inputs

Minimum required inputs:

symbol
timeframe
entry_price
direction
nearest_support
nearest_resistance
buffer_price
atr_reference
price_speed
expiry_minutes

Optional advanced inputs:

sr_cluster_count
sr_levels_ahead
recent_true_movement
trend_class
volatility_regime

---

Primary Measurements

1. corridor_distance

Distance from entry to the nearest blocking SR in the trade direction.

For BUY:

corridor_distance = nearest_resistance - entry_price

For SELL:

corridor_distance = entry_price - nearest_support

If the relevant SR does not exist:

corridor_distance = +Infinity

---

2. free_path_ratio

free_path_ratio = corridor_distance / buffer_price

Interpretation:

< 1.0   → obstacle inside required move
1.0-1.3 → weak corridor / borderline
1.3-2.0 → valid corridor
> 2.0   → strong corridor

---

3. expiry_reach_ratio

expiry_reach_ratio = (price_speed * expiry_minutes) / buffer_price

Interpretation:

< 1.0   → insufficient movement capability
≈ 1.0   → borderline
> 1.0   → reachable

---

4. volatility_support_ratio

volatility_support_ratio = atr_reference / buffer_price

Interpretation:

low  → buffer too ambitious for volatility
high → volatility can support move

---

5. corridor_quality_score

Canonical corridor quality score:

corridor_quality_score =
    free_path_ratio
    * expiry_reach_ratio
    * volatility_support_ratio

This is a structural tradability score, not a direction score.

---

Corridor Classes

The engine must classify each setup into one of the following:

BLOCKED

free_path_ratio < 1.0

Meaning:

nearest SR sits inside the required buffer

trade should not advance to execution

TIGHT

1.0 <= free_path_ratio < 1.3

Meaning:

path exists but is weak

trade may be allowed only for PRE or under stronger confirmation

TRADABLE

1.3 <= free_path_ratio < 2.0

Meaning:

sufficient corridor exists

normal candidate

OPEN_FIELD

free_path_ratio >= 2.0

Meaning:

large free path ahead

excellent corridor geometry

---

SR Density Model

Not all corridors are equally clean.

The engine must estimate SR density ahead of price.

Definition:

sr_density = number of relevant SR levels inside projected trade path

Projected trade path may be approximated as:

entry_price ± max(buffer_price, atr_reference, price_speed * expiry_minutes)

Interpretation:

0 → clean corridor
1 → moderate friction
2+ → clustered corridor / high friction

---

Friction Model

The engine must expose a concept of market friction:

market_friction = function(sr_density, corridor_distance, volatility_regime)

Simple canonical approximation:

market_friction = sr_density / max(free_path_ratio, 0.01)

Higher friction reduces corridor quality.

Adjusted corridor quality:

corridor_quality_adjusted =
    corridor_quality_score / (1 + market_friction)

---

Entry Optimization Role

The corridor engine must support entry optimization.

Instead of assuming current market price is always the correct entry, the engine may evaluate candidate entries that improve corridor geometry.

Goal:

select entry zone that maximizes corridor_quality_adjusted

Examples:

retrace entry near support in BUY
retrace entry near resistance in SELL
breakout continuation entry after SR clearance

The engine does not need to execute optimization in first implementation, but the canonical model must support it.

---

Expiry Optimization Role

The corridor engine must help select realistic expiry.

Definition:

time_to_buffer = buffer_price / max(price_speed, epsilon)

Recommended expiry lower bound:

expiry_recommended = time_to_buffer * safety_factor

Where:

safety_factor = 1.15 to 1.50

The engine must flag setups where:

expiry_minutes < time_to_buffer

as structurally weak.

---

Decision Engine Integration

The canonical staged behavior is:

PRE

PRE may be allowed with:
corridor class TIGHT, TRADABLE, or OPEN_FIELD
provided score and trend logic are acceptable

PRE should not be hard-blocked by weak SR if corridor is not fully blocked.

CONFIRM

CONFIRM must require corridor validation:
corridor class ideally TRADABLE or OPEN_FIELD
or TIGHT only with stronger supporting conditions

OPEN_NOW

OPEN_NOW must require:
corridor not BLOCKED
reachability acceptable
corridor_quality_adjusted above threshold
time-to-buffer compatible with expiry

---

Canonical Decision Rules

Hard reject

if free_path_ratio < 1.0:
    corridor_state = BLOCKED
    reject execution

PRE eligibility

if free_path_ratio >= 1.0:
    PRE may still be allowed

CONFIRM eligibility

if free_path_ratio >= 1.2
and corridor_quality_adjusted >= corridor_confirm_threshold:
    CONFIRM eligible

OPEN_NOW eligibility

if free_path_ratio >= 1.3
and expiry_reach_ratio >= 1.0
and corridor_quality_adjusted >= corridor_open_threshold:
    OPEN_NOW eligible

Thresholds remain configurable in implementation.

---

Observability Requirements

Minimum telemetry fields to be logged:

corridor_distance
free_path_ratio
expiry_reach_ratio
volatility_support_ratio
corridor_quality_score
market_friction
corridor_quality_adjusted
corridor_class
sr_density
nearest_support
nearest_resistance
buffer_price
price_speed
expiry_minutes

These fields are required for audit and later AI learning.

---

AI / Dataset Relevance

The SR Corridor Detection Engine is a core feature generator for future AI.

Canonical dataset fields include:

symbol
timestamp
direction
entry_price
buffer_price
corridor_distance
free_path_ratio
expiry_reach_ratio
volatility_support_ratio
corridor_quality_score
market_friction
corridor_quality_adjusted
corridor_class
sr_density
trade_result

This allows the AI layer to learn:

which corridor structures succeed
which corridor geometries fail
how market friction impacts outcomes
which expiry choices are realistic

---

Relation To Trade Physics Score

The corridor engine extends Trade Physics Score.

Trade Physics Score models:

space + time + speed + volatility

SR Corridor Detection adds:

obstacles + free path + friction

So the strategic evolution becomes:

TPS
→ TPS + SR Corridor
→ TPS + SR Corridor + AI calibration

---

Phaseing / Implementation Roadmap

Phase 1
detect corridor_distance
compute free_path_ratio
classify corridor
log telemetry

Phase 2
compute sr_density
compute market_friction
compute corridor_quality_adjusted

Phase 3
integrate into PRE / CONFIRM / OPEN_NOW staged logic

Phase 4
entry-point optimization
expiry optimization
AI calibration dataset integration

---

Summary

The SR Corridor Detection Engine transforms SR from a simple binary blocker into a structural path-evaluation model.

It allows the bot to ask not only:

is direction good?

but also:

is there enough navigable path ahead?
is the path clean enough?
is the move reachable in time?

This is a required foundation for turning the bot from a simple signal scorer into a market-structure-aware trading engine.

