################################################################################
AI_TRADE_PHYSICS_SPACE_MODEL_SPEC.md
BinaryBot — Trade Physics Space Model
Version: 1.0.0
Status: Canonical Strategy Intelligence Specification
################################################################################

Linked Documents

ALGO_SPEC.md
STRATEGY_LOGIC_SPEC.md
DECISION_AUDIT_SPEC.md
AI_TRADING_INTELLIGENCE_ARCHITECTURE.md
EVENT_SCHEMA_SPEC.md
PERFORMANCE_ANALYTICS_SPEC.md


################################################################################
1. PURPOSE
################################################################################

This document defines the canonical “Trade Physics Space Model” used by the
BinaryBot intelligence layer.

The purpose of this model is to measure whether a potential trade setup has
sufficient structural space in the market to complete its movement.

Traditional indicators such as RSI, moving averages, or momentum oscillators
primarily describe direction and local market conditions.

However, they do not measure whether a trade has enough physical space
relative to volatility and structural barriers to successfully develop.

The Trade Physics Space Model addresses this limitation by measuring the
relationship between:

• available structural space in the market
• required movement distance for the trade
• current volatility regime (ATR)
• time feasibility

This model represents a fundamental feature used by the AI strategy analysis
layer to predict signal success probability.


################################################################################
2. CONCEPTUAL FOUNDATION
################################################################################

The central hypothesis of the model is:

A trading setup succeeds primarily when the market structure provides enough
space relative to the movement required for the trade.

In other words:

The probability of trade success is strongly related to the ratio between
available market space and the required movement distance.

If structural barriers (support or resistance) are too close relative to the
required move, the trade is likely to fail regardless of indicator signals.

This concept is referred to as:

TRADE PHYSICS


################################################################################
3. CORE VARIABLES
################################################################################

The model relies on variables already produced by the signal engine.

Primary variables:

available_space
required_space
atr_m5
buffer_price
buffer_mult

These values are generated during the decision engine evaluation phase.

Example engine output fields:

available_space
required_space
atr_m5
buffer_price
buffer_mult
speed_price_per_min
t_needed_adj_min


################################################################################
4. SPACE TO BUFFER RATIO
################################################################################

The fundamental metric is defined as:

space_to_buffer_ratio

Formula:

space_to_buffer_ratio =
    available_space / required_space


Interpretation

space_to_buffer_ratio < 1
    Trade is structurally constrained
    Setup is very likely invalid.

space_to_buffer_ratio ≈ 1
    Trade is marginal
    Structural barrier is close.

space_to_buffer_ratio > 1
    Trade has sufficient structural space.

space_to_buffer_ratio >> 1
    Trade environment is structurally favorable.


################################################################################
5. NORMALIZED TRADE SPACE MARGIN
################################################################################

For cross-symbol comparison, the raw ratio must be normalized by volatility.

Normalized metric:

trade_space_margin_atr

Formula:

trade_space_margin_atr =
    (available_space - required_space) / atr_m5


Interpretation

trade_space_margin_atr < 0
    Trade does not fit structurally.

trade_space_margin_atr ≈ 0
    Trade is structurally tight.

trade_space_margin_atr > 0
    Trade has sufficient structural room.

Large positive values indicate highly favorable conditions.


################################################################################
6. RELATION TO BUFFER MODEL
################################################################################

The required_space variable is derived from the volatility buffer model.

buffer_price =
    atr_m5 × buffer_mult

Where buffer_mult depends on the configured buffer mode.

Typical configuration:

SMALL
    atr_mult = 0.3

MEDIUM
    atr_mult = 0.6

LARGE
    atr_mult = 1.0

required_space therefore represents the minimum distance required for the
trade to move relative to the volatility environment.


################################################################################
7. RELATION TO STRUCTURE (SR GATE)
################################################################################

The structural space measurement depends on support and resistance detection.

available_space is computed as:

distance from current price to the nearest structural barrier
in the direction of the trade.

Examples:

BUY trade
    nearest resistance defines the space limit.

SELL trade
    nearest support defines the space limit.

If:

available_space < required_space

then the SR gate rejects the signal with reason:

SR_SPACE_INSUFFICIENT


################################################################################
8. RELATION TO FEASIBILITY
################################################################################

Space alone does not guarantee trade feasibility.

The engine also evaluates temporal feasibility:

Variables involved:

speed_price_per_min
t_needed_adj_min
expiry_minutes

Feasibility determines whether the price can reach the buffer distance
within the allowed time window.

The Trade Physics Space Model therefore works together with:

Feasibility Gate


################################################################################
9. ROLE IN AI STRATEGY ANALYSIS
################################################################################

The Trade Physics Space Model provides one of the most important features
for machine learning analysis of signal outcomes.

In historical datasets the following pattern is expected:

Low space_to_buffer_ratio
    → high failure probability

Moderate ratios
    → mixed outcomes

High ratios
    → significantly higher success probability


Therefore these metrics must be included in the AI dataset.


################################################################################
10. AI DATASET FEATURES
################################################################################

The following columns must be included in AI training datasets:

available_space
required_space
atr_m5
space_to_buffer_ratio
trade_space_margin_atr
speed_price_per_min
t_needed_adj_min
expiry_minutes
trend_score
momentum_score
signal_outcome


These features allow the AI system to analyze how structural space
influences signal success.


################################################################################
11. EXPECTED PREDICTIVE IMPORTANCE
################################################################################

In many market conditions the following predictors are expected to rank
highest for trade outcome prediction:

1. trade_space_margin_atr
2. space_to_buffer_ratio
3. time_to_buffer_ratio
4. feasibility score
5. momentum indicators
6. RSI or oscillator signals

The Trade Physics variables measure structural feasibility rather than
indicator appearance.


################################################################################
12. ROLE IN STRATEGY OPTIMIZATION
################################################################################

The intelligence layer may use these variables to:

• detect symbols with poor structural trade space
• optimize buffer multipliers
• adapt expiry selection
• improve SR gate thresholds
• detect over-constrained markets


################################################################################
13. FUTURE EXTENSIONS
################################################################################

Possible future extensions of the Trade Physics model include:

Space Quality Index (SQI)

Space / Volatility Efficiency

Structural Density Score

Dynamic Buffer Adjustment


These features may further improve signal evaluation.


################################################################################
14. SUMMARY
################################################################################

The Trade Physics Space Model measures the relationship between:

market structure
required trade movement
volatility environment

This model allows the strategy to determine whether a trade setup
has sufficient physical room to develop.

Unlike traditional indicators, this model evaluates the structural
feasibility of the trade itself.

For this reason, it forms a core component of the BinaryBot
AI trading intelligence architecture.

################################################################################
END OF DOCUMENT
################################################################################