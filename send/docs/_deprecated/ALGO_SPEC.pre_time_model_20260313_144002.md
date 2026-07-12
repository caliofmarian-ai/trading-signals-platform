# ALGO_SPEC — Binary Signals Engine
## Version: 1.0.0
## Canonical Behavioral Specification

---

# 0. META

ALGO_VERSION: 1.0.0  
Scope: Binary trading signals (manual execution)  
Primary timeframe: M1  
Expiry: Dynamic (2–15 minutes)  
Markets: Forex + Crypto  
Reporting: Telegram topics (SIGNALS_LIVE + BUFFER_LOGS)  
Source of truth (parameters): config/algo_params.json  
Secrets location: .env (tokens, IDs, API keys only)

This document defines the full behavioral contract of the signal engine.
Any logic modification requires version bump + changelog update.

---

# 1. CORE PHILOSOPHY

The engine does NOT attempt to predict direction blindly.

It performs:

1. Volatility measurement
2. Structural validation
3. Momentum qualification
4. Feasibility calculation
5. Safety distance computation (Buffer)
6. Time-to-target estimation (Expiry)
7. Multi-module scoring
8. Hard gating (rejection rules)
9. Controlled signal release via state machine

No signal is allowed unless:

- Buffer is statistically reachable
- Structural space exists
- No spike instability is active
- Confidence exceeds threshold

---

# 2. SIGNAL TYPES

## 2.1 PRE (Focus Candidate)

Conditions:

- Score ≥ PRE threshold
- No critical instability
- Structural feasibility is still plausible
- Candidate appears strong enough to justify focus/watchlist priority

Purpose:

- mark a setup as promising
- request elevated live attention
- promote the symbol toward focus context
- prepare the system for deeper timing analysis

PRE does NOT mean final entry readiness.
It means the setup is promising enough to deserve focused monitoring.

Includes:

- Symbol
- Direction
- Score
- Buffer estimate
- Expiry estimate
- Initial rationale

---

## 2.2 CONFIRM (Arm State)

Conditions:

- Score ≥ CONFIRM threshold
- Core gates remain valid
- Setup remains structurally consistent under live monitoring
- Buffer reachability remains plausible inside the expiry window

Purpose:

- signal that the setup is now armed
- indicate that live execution may become valid soon
- confirm that focus monitoring continues to be justified

CONFIRM does NOT mean immediate execution.
It means the setup is sufficiently aligned for possible execution if final timing remains favorable.

Includes:

- Symbol
- Direction
- Score
- Buffer
- Expiry
- Updated rationale
- Time-to-open estimate (if available)

---

## 2.3 OPEN_NOW

Conditions:

- Score ≥ OPEN threshold
- All hard gates passed
- want_open_now = TRUE
- Symbol is inside valid focus/watchlist context
- Buffer remains reachable with sufficient probability before expiry
- Final entry timing is considered favorable by live decision logic

Purpose:

- issue the final execution-stage signal
- indicate that the setup is not only directional, but actionable now
- express the bot's judgment that direction + distance + time feasibility are aligned

OPEN_NOW is not merely a directional call.
It is a final feasibility call based on:

- direction quality
- buffer distance
- remaining expiry window
- structural market validity
- live timing quality inside focus context

Includes:

- Symbol
- Direction
- Score
- Exact buffer
- Exact expiry
- Final action rationale

---

## 2.4 THRESHOLD HIERARCHY

Canonical rule:

- PRE threshold ≤ CONFIRM threshold ≤ OPEN threshold

Meaning:

- PRE = promising enough to enter focused attention
- CONFIRM = strong enough to arm
- OPEN = strong enough to execute

Threshold inversion is forbidden.

---

## 2.5 BUFFER SEMANTICS

Buffer is a core strategic variable.

Buffer is NOT:

- cosmetic
- UI-only
- a decorative offset

Buffer IS:

- the mathematical safety margin the strategy expects price to traverse
- the distance required so the signal has real edge by expiry
- a protection layer against weak entries and marginal closes

Canonical meaning:

- BUY quality depends on the probability that price can close above entry plus buffer by expiry
- SELL quality depends on the probability that price can close below entry minus the required safety distance by expiry

Therefore:

- a correct direction without enough distance is not sufficient
- a setup may look valid directionally but still fail feasibility
- OPEN_NOW must require believable buffer traversal, not just directional bias

---

## 2.6 EXPIRY FEASIBILITY

Expiry is part of the strategic truth of the signal.

The engine must evaluate whether the expected move can complete within the available expiry window.

This means OPEN_NOW must reflect:

- distance-to-target feasibility
- timing feasibility
- structural feasibility
- current market quality under focus monitoring

Canonical rule:

A setup should not reach OPEN_NOW unless the strategy considers the required buffer traversal realistically achievable before expiry.

---

## 2.7 FOCUS CONTEXT AND LIVE DECISION QUALITY

Focus exists to improve live decision quality.

Focus is used because the final execution decision requires tighter observation of:

- score persistence
- timing quality
- buffer reachability
- expiry decay
- gate stability
- structural market behavior

Focus does not exist to freeze market discovery.
Focus exists to refine the truthfulness of CONFIRM and OPEN_NOW.

Canonical relation:

focus context
+ buffer reachability
+ expiry window
= final live execution quality

# 3. TIMEFRAMES

## 3.1 M1 (Execution Layer)

Used for:
- ATR
- RSI
- Candle body expansion
- Spike filters
- Micro-structure
- Entry timing

## 3.2 M5 (Structure Layer)

Used for:
- EMA50 / EMA200
- Trend alignment
- Structural pivots
- SR clustering

## 3.3 M15 (Optional Context Filter)

Disabled in v1.0.0 by default.

---

# 4. INDICATORS

## 4.1 Volatility

ATR_M1 = ATR(14) on M1  
ATR_fast = ATR(5)  
ATR_slow = ATR(14)

---

## 4.2 Trend

EMA50 (M5)  
EMA200 (M5)

Trend states:
- With trend
- Flat
- Counter trend

---

## 4.3 Momentum

RSI(14) M1  
BodyExpansion = avgBody_last3 / avgBody_14  

---

## 4.4 Structure

Fractal pivots (left=2 right=2) on M5  
Clustered to form major SR zones  

Micro swings (M1) for entry protection  

---

# 5. BUFFER (Safety Distance)

## 5.1 Definition

Buffer = minimum safety distance between entry and projected expiry price.

BUY:
expiry_price ≥ entry + buffer

SELL:
expiry_price ≤ entry - buffer

Buffer is dynamic.

---

## 5.2 Common Formula

buffer_raw = ATR_M1 × multiplier_mode × trend_factor × structure_factor

Where:

multiplier_mode ∈ {SMALL, MEDIUM, LARGE}

---

## 5.3 Forex (Pips)

pip_size:
- Non-JPY = 0.0001
- JPY pairs = 0.01

atr_pips = ATR_M1 / pip_size

buffer_pips = atr_pips × multiplier_mode × trend_factor × structure_factor

Rounded to 1 decimal.

buffer_price = buffer_pips × pip_size

---

## 5.4 Crypto (Points + %)

buffer_points = ATR_M1 × multiplier_mode × trend_factor × structure_factor

Rounded to configured decimals.

buffer_percent = (buffer_points / last_price) × 100

Rounded to 2 decimals.

---

# 6. EXPIRY (Dynamic Time Estimation)

## 6.1 Momentum Factor

r = abs(RSI - 50) / 50  
b = avgBody_last3 / avgBody_14  

MomentumFactor = Clamp(
1 + 0.6r + 0.4(b - 1),
0.7,
1.6
)

---

## 6.2 Trend Time Adjust

With trend → 0.90  
Flat → 1.05  
Counter trend → 1.20  

---

## 6.3 Expiry Formula

Expiry_minutes =
(buffer_price / (ATR_M1 × MomentumFactor)) × TrendTimeAdjust

Clamped between:

min_expiry_minutes  
max_expiry_minutes

Converted to minutes + seconds.

---

# 7. STRUCTURAL GATING

## 7.1 SR Space Requirement

Required space:

req = sr_required_multiplier × buffer

BUY:
nearest_resistance − entry ≥ req

SELL:
entry − nearest_support ≥ req

If not satisfied → hard reject.

---

## 7.2 Micro Swing Protection

BUY:
price must not break micro_swing_low before OPEN

SELL:
price must not break micro_swing_high before OPEN

---

# 8. SPIKE FILTERS

Hard rejection if:

- Range z-score > threshold
- Wick/body ratio too high
- ATR_fast / ATR_slow > threshold
- Jump vs ATR > threshold

Cooldown applied per symbol:
60–180 seconds depending on severity.

---

# 9. CONFIDENCE SCORING (0–100)

Modules:

TrendScore (0–18)  
MomentumScore (0–22)  
EntryTimingScore (0–18)  
BufferFeasibilityScore (0–16)  
SRSpaceScore (0–16)  
StabilityScore (0–10)  

Total = Sum

Thresholds:
PRE ≥ 70  
CONFIRM ≥ 75  
OPEN ≥ 80  

Hard reject if:
- Spike active
- SR fail
- Feasibility ratio > 1

---

# 10. STATE MACHINE

States per symbol:

WIDE_SCAN
FOCUS_PRE
CONFIRM_READY
OPEN_SENT
COOLDOWN

Rules:

- Max 2 symbols in focus
- Focus symbols get priority scanning while wide scan remains active
- PRE promotes a candidate into focus priority context; it does not globally shut down wide scan
- Release focus if score drops below PRE
- Release focus if setup invalidates or expiry feasibility collapses
- Cooldown blocks re-entry temporarily

Execution meaning:

- PRE = candidate worthy of focused attention
- CONFIRM_READY = setup armed under live monitoring
- OPEN_SENT = final execution-stage signal emitted
- COOLDOWN = post-trade lockout state

The state machine must remain consistent with:

- buffer semantics
- expiry feasibility
- focus context requirements
- final execution timing quality

# 11. TELEGRAM UX RULES

## PRE
Show:
- Symbol
- Direction
- Confidence
- Buffer
- Expiry estimate
- SR status

## CONFIRM
Show:
- Prepare symbol
- Expiry exact
- Buffer exact
- TargetMin
- OPEN timing estimation

## OPEN_NOW
Show:
- OPEN NOW
- Direction
- Expiry exact
- Buffer exact
- TargetMin

## BUFFER_LOGS
Include:
- Timestamp (UTC)
- Algo version
- Parameter hash
- Rejection reason codes
- Full calculation snapshot when needed

---

# 12. PARAMETERIZATION

All tunables in:

config/algo_params.json

.env contains ONLY:
- Tokens
- IDs
- API keys

---

# 13. VERSION CONTROL RULE

If logic changes:

1. Bump version
2. Update CHANGELOG
3. Validate algo_params.json
4. Restart services
5. Telegram test
6. Validate focus + cooldown behavior

---

END OF SPECIFICATION  
Version 1.0.0


# Operational Stability Extensions

## Focus Lease as Algorithmic Resource Guard

Focus context is not only a scheduler concept.
It is also an algorithmic resource guard.

Deep analysis resources must only remain attached to a symbol while that symbol still qualifies operationally and temporally.

Therefore the algorithm requires bounded focus lease semantics.

## Decision Freeze as Opportunity Identity Discipline

The algorithm must distinguish between:

- a new trade opportunity
- the same opportunity being observed again

Without this distinction, repeated ticks can create redundant analysis loops and noisy interpretation of the same signal candidate.

## Freeze Purpose

Decision freeze exists to preserve:

- signal identity integrity
- cleaner PRE / CONFIRM / OPEN progression
- reduced duplicate analytics noise
- reduced API waste

## Allowed Reopen Conditions

A frozen decision opportunity may reopen only when material information changes, including:

- new candle
- direction change
- meaningful score change
- focus qualification change
- expiry feasibility change
- stage progression becoming newly reachable


