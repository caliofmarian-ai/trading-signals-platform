FORMAL_SPEC.md

Formal Mathematical Specification — BinaryBot
Version: 1.0.0
Status: Canonical Formal Layer
Linked Documents:
ALGO_SPEC_v2.0.0.md, FSM_DECISION_ENGINE_SPEC_v1.0.0.md, SYSTEM_INVARIANTS_v2.0.0.md, RISK_MODEL.md, PARAMS_REFERENCE.md

---

1. PURPOSE

This document formalizes the BinaryBot system using mathematical definitions.

It removes ambiguity by defining:

- Inputs
- State space
- Transition functions
- Decision functions
- Risk gates
- Deterministic guarantees

This is the highest abstraction layer.

---

2. DEFINITIONS

Let:

S = set of symbols
T = discrete time indexed by candle timestamp
C_s(t) = candle for symbol s at time t

Each candle:

C = (open, high, low, close)

State of system at time t:

X(t) = (FSM_state, Watchlist, Cooldowns, Params)

---

3. INPUT SPACE

For each symbol s ∈ S:

Input vector at time t:

I_s(t) = {
M1 candles up to t,
M5 candles up to t,
Parameters P,
FSM state,
Buffer mode B
}

All decisions are functions of I_s(t).

---

4. INDICATOR FUNCTIONS

Define:

ATR_s(t) = Average True Range over last n candles
RSI_s(t) = Relative Strength Index
EMA50_s(t)
EMA200_s(t)

Momentum factor:

MF_s(t) = clamp(
1 + (w_r × |RSI_s(t) − 50|/50) + (w_b × body_ratio),
min,
max
)

Trend classification:

Trend_s(t) ∈ {WITH, FLAT, COUNTER}

---

5. BUFFER FUNCTION

Buffer for symbol s at time t:

Buffer_s(t) = ATR_s(t) × M(B) × TF_s(t) × SF_s(t)

Where:

M(B) = buffer multiplier from buffer mode
TF_s(t) = trend factor
SF_s(t) = structure factor

---

6. EXPIRY FUNCTION

Expiry_s(t) = clamp(
Buffer_s(t) / (ATR_s(t) × MF_s(t)) × TTA_s(t),
min_expiry,
max_expiry
)

All expiry calculations deterministic.

---

7. STRUCTURE CONSTRAINT

Let:

SR_space_s(t) = distance to nearest resistance/support

Trade valid only if:

SR_space_s(t) ≥ sr_required_multiplier × Buffer_s(t)

---

8. SPIKE FILTER FUNCTION

Define spike indicator:

Spike_s(t) = TRUE if any:

Z_range ≥ threshold
wick_ratio ≥ threshold
ATR_fast/ATR_slow ≥ threshold
jump/ATR ≥ threshold

Trade valid only if:

Spike_s(t) = FALSE

---

9. FEASIBILITY CONSTRAINT

Required movement time:

T_needed_s(t) = Buffer_s(t) / (ATR_s(t) × MF_s(t)) × TTA_s(t)

Trade valid only if:

T_needed_s(t) ≤ Expiry_s(t)

---

10. SCORE FUNCTION

Score_s(t) =

TrendScore_s(t)

+ MomentumScore_s(t)
+ EntryTimingScore_s(t)
+ StructureScore_s(t)
+ VolatilityScore_s(t)

Where:

Score_s(t) ∈ [0,100]

---

11. SIGNAL DECISION FUNCTION

Let thresholds:

θ_PRE
θ_CONFIRM
θ_OPEN

Define decision D_s(t):

If Spike = TRUE → REJECT

Else if SR constraint fails → REJECT

Else if Feasibility fails → REJECT

Else if Score ≥ θ_OPEN → OPEN_NOW

Else if Score ≥ θ_CONFIRM → CONFIRM

Else if Score ≥ θ_PRE → PRE

Else → NO_SIGNAL

---

12. FSM STATE FUNCTION

FSM_state_s(t+1) = F(FSM_state_s(t), Event_s(t))

Where events include:

PRE_detected
OPEN_sent
User_open
Cooldown_expired

FSM is deterministic finite automaton.

---

13. GLOBAL CONSTRAINTS

∀t:

|Watchlist(t)| ≤ 2

∀s,t:

At most one OPEN_NOW per (s,t)

∀s:

If in COOLDOWN_s(t) = TRUE → D_s(t) ≠ PRE/CONFIRM/OPEN

---

14. DETERMINISM PROPERTY

For any symbol s and time t:

If I_s(t) = I_s’(t)

Then:

D_s(t) = D_s’(t)

System has no stochastic components.

---

15. INVARIANT PRESERVATION

If invariants hold at time t,
and transition functions obey FSM_SPEC,

Then invariants hold at time t+1.

System is closed under valid transitions.

---

16. STABILITY CONDITION

Let WR(t,n) = win rate over last n trades.

System stable if:

|WR(t,n) − WR_baseline| ≤ ε

If exceeded:

Drift detected.

---

17. COMPLETENESS

A trade is allowed if and only if:

All gates pass
Score threshold met
FSM state permits
Invariants preserved

No hidden condition exists.

---

18. SYSTEM MODEL SUMMARY

BinaryBot is defined as:

A deterministic state machine
Operating on structured candle data
Applying layered risk constraints
Producing discrete signal outputs
Under strict invariants

Mathematically:

D_s(t) = f(I_s(t))
Subject to constraints C

Where f is deterministic and C enforces invariants.

---

19. FORMAL GUARANTEE

If:

- All constraints enforced
- All invariants preserved
- Determinism holds
- Parameters bounded

Then:

System behavior is provable,
Auditable,
And stable under controlled evolution.

---

End of FORMAL_SPEC.md