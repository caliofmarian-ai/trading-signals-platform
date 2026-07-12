################################################################################
TRADE_PHYSICS_SCORE_SPEC.md
BinaryBot — Trade Physics Score (TPS)
Version: 1.0.0
Status: Canonical Strategy Intelligence Specification
################################################################################

Linked Documents

AI_TRADE_PHYSICS_SPACE_MODEL_SPEC.md
AI_TRADING_INTELLIGENCE_ARCHITECTURE.md
ALGO_SPEC.md
DECISION_AUDIT_SPEC.md
PERFORMANCE_ANALYTICS_SPEC.md
EVENT_SCHEMA_SPEC.md


################################################################################
1. PURPOSE
################################################################################

This document defines the canonical Trade Physics Score (TPS) model.

TPS is a mathematical scoring framework designed to estimate the real
probability that a trade setup can successfully develop under current
market conditions.

Unlike classical indicator-based scoring, TPS focuses on the physical
viability of the trade.

It combines four core dimensions:

• structural space
• time feasibility
• price speed
• volatility normalization

The output of the model is a single score that represents the physical
probability of trade completion.


################################################################################
2. CONCEPTUAL FOUNDATION
################################################################################

A valid trade is not determined only by direction.

A valid trade must satisfy four physical conditions:

1. There must be enough market space.
2. There must be enough time before expiry.
3. Price must move fast enough in the intended direction.
4. The move must be realistic relative to volatility.

TPS measures these four constraints and combines them into one unified score.

This transforms strategy evaluation from:

indicator confirmation

into:

trade feasibility probability


################################################################################
3. CORE DIMENSIONS
################################################################################

TPS is built from four normalized components:

S = Space Component
T = Time Feasibility Component
P = Price Speed Component
V = Volatility Efficiency Component

These dimensions are defined below.


################################################################################
4. SPACE COMPONENT
################################################################################

The space component evaluates whether the market structure provides enough
room for the trade.

Base variable:

space_to_buffer_ratio =
    available_space / required_space

Normalized space component:

S = min(space_to_buffer_ratio, S_cap) / S_cap

Recommended initial cap:

S_cap = 3.0

Interpretation:

S ≈ 0
    No structural space

S ≈ 0.33
    Marginal space

S ≈ 0.66
    Good space

S ≈ 1.0
    Excellent structural space


################################################################################
5. TIME FEASIBILITY COMPONENT
################################################################################

The time component evaluates whether the move can complete before expiry.

Base variable:

time_to_buffer_ratio =
    expiry_minutes / t_needed_adj_min

Normalized time component:

T = min(time_to_buffer_ratio, T_cap) / T_cap

Recommended initial cap:

T_cap = 2.0

Interpretation:

T < 0.5
    Low time feasibility

T ≈ 1.0
    Trade is likely feasible in time

T > 1.0
    Trade has comfortable timing


################################################################################
6. PRICE SPEED COMPONENT
################################################################################

The speed component evaluates whether price is moving efficiently enough
in the expected direction.

Base variable:

directional_speed_ratio =
    speed_price_per_min / atr_speed_reference

Where:

atr_speed_reference =
    atr_m5 / reference_minutes

Recommended initial reference:

reference_minutes = 5

Normalized price speed component:

P = min(directional_speed_ratio, P_cap) / P_cap

Recommended initial cap:

P_cap = 2.0

Interpretation:

P low
    Price too slow relative to volatility

P medium
    Price movement is usable

P high
    Price movement is efficient and strong


################################################################################
7. VOLATILITY EFFICIENCY COMPONENT
################################################################################

The volatility component evaluates whether the required move is realistic
relative to the volatility environment.

Base variable:

buffer_to_atr_ratio =
    buffer_price / atr_m5

If buffer_price is properly derived from ATR, this value reflects the
aggressiveness of the required movement.

For buffer-based strategies, a more useful normalized form is:

V = 1 / (1 + movement_stress)

Where:

movement_stress =
    required_space / atr_m5

Interpretation:

High movement_stress
    Trade requires too much movement relative to ATR

Low movement_stress
    Trade requirement is realistic

V therefore decreases when the trade becomes too demanding.


################################################################################
8. TRADE PHYSICS SCORE FORMULA
################################################################################

The canonical initial form of TPS is:

TPS_raw =
    wS * S +
    wT * T +
    wP * P +
    wV * V

Where recommended initial weights are:

wS = 0.35
wT = 0.25
wP = 0.20
wV = 0.20

Constraint:

wS + wT + wP + wV = 1.0

Final normalized score:

TPS = 100 * TPS_raw

Therefore:

TPS ∈ [0, 100]


################################################################################
9. INTERPRETATION OF TPS
################################################################################

Recommended interpretation ranges:

TPS < 30
    Physically weak trade
    Very low probability of completion

TPS 30 – 50
    Weak trade
    Likely blocked by structure or timing

TPS 50 – 65
    Moderate trade
    Tradable only if other conditions are strong

TPS 65 – 80
    Strong trade
    Good physical conditions

TPS > 80
    Excellent trade
    High probability of completion


################################################################################
10. RELATION TO EXISTING STRATEGY SCORE
################################################################################

The current engine already computes a classical score:

trend
rsi
body
structure
feasibility
total

TPS is not intended to replace this score immediately.

Instead:

Current Strategy Score
    measures signal quality

TPS
    measures physical executability

The two scores should be treated as complementary.

A future combined model may be:

final_probability_score =
    alpha * strategy_score_normalized +
    beta  * TPS_normalized

Where:

alpha + beta = 1


################################################################################
11. EXAMPLE
################################################################################

Suppose a setup has:

available_space = 0.020
required_space  = 0.010
expiry_minutes  = 4
t_needed_adj_min = 2
speed_price_per_min = 0.004
atr_m5 = 0.008
buffer_price = 0.004

Then:

space_to_buffer_ratio = 0.020 / 0.010 = 2.0
S = min(2.0, 3.0) / 3.0 = 0.6667

time_to_buffer_ratio = 4 / 2 = 2.0
T = min(2.0, 2.0) / 2.0 = 1.0

atr_speed_reference = 0.008 / 5 = 0.0016
directional_speed_ratio = 0.004 / 0.0016 = 2.5
P = min(2.5, 2.0) / 2.0 = 1.0

movement_stress = 0.010 / 0.008 = 1.25
V = 1 / (1 + 1.25) = 0.4444

TPS_raw =
    0.35*0.6667 +
    0.25*1.0 +
    0.20*1.0 +
    0.20*0.4444

TPS_raw = 0.7723

TPS = 77.23

Interpretation:
Strong trade with good structural and temporal feasibility.


################################################################################
12. ROLE IN AI DATASET
################################################################################

The following dataset fields must be stored for AI training:

available_space
required_space
space_to_buffer_ratio
trade_space_margin_atr
expiry_minutes
t_needed_adj_min
time_to_buffer_ratio
speed_price_per_min
atr_speed_reference
directional_speed_ratio
atr_m5
buffer_price
movement_stress
TPS
signal_outcome

The target label remains:

trade_success
or
trade_outcome_class


################################################################################
13. ROLE IN DECISION AUDIT
################################################################################

Decision audit events should optionally include:

space_to_buffer_ratio
trade_space_margin_atr
time_to_buffer_ratio
directional_speed_ratio
movement_stress
TPS

This allows later analysis of:

• which TPS ranges convert best
• which symbols produce high TPS most often
• whether low TPS signals should be fully suppressed
• whether TPS predicts outcome better than RSI or trend score


################################################################################
14. ROLE IN FUTURE AI ARCHITECTURE
################################################################################

TPS is expected to become one of the core intelligence features for:

• outcome prediction
• strategy calibration
• symbol ranking
• adaptive scheduler prioritization
• candidate replacement logic
• rejection analytics

Possible future usage:

1. Prioritize focus candidates by TPS
2. Suppress low-TPS PRE signals
3. Increase confidence level for high-TPS OPEN_NOW
4. Use TPS as a feature in gradient boosting models
5. Build symbol-specific TPS calibration curves


################################################################################
15. STRATEGIC VALUE
################################################################################

TPS is important because it transforms the strategy from:

signal appearance model

into:

trade execution reality model

Indicators describe what the market looks like.

TPS describes whether the trade can actually happen.


################################################################################
16. FUTURE EXTENSIONS
################################################################################

Possible future TPS extensions:

TPS_v2 with flow efficiency
TPS_v3 with structural density score
TPS_v4 with session-specific calibration
TPS_v5 with symbol-specific adaptive weighting

These future versions must remain backward compatible with TPS_v1 logging.


################################################################################
17. SUMMARY
################################################################################

Trade Physics Score (TPS) is the canonical mathematical model that combines:

space
time feasibility
price speed
volatility normalization

into a single probabilistic trade quality score.

TPS does not replace the current strategy score.
It complements it by measuring physical executability.

This model forms the mathematical bridge between:

rule-based strategy
and
AI-assisted probabilistic trading intelligence

################################################################################
END OF DOCUMENT
################################################################################