# ALGO SPEC
## Canonical Strategy Logic Specification

Version: 1.0.0  
Status: Canonical  
Scope: Strategy Engine / Signal Decision Logic  
Depends On: TIME_MODEL_CANON_v1.0.0.md

---

# 1. PURPOSE

This document defines the canonical mathematical logic of the BinaryBot strategy engine.

It specifies how the engine evaluates:

- direction
- feasibility
- buffer reachability
- corridor validity
- timing confidence
- state progression from PRE to CONFIRM to OPEN_NOW

This document is the canonical algorithm reference for signal generation.

---

# 2. FUNDAMENTAL PRINCIPLE

The strategy engine does not directly produce a Telegram message.

The strategy engine produces a structured decision result based on:

- market state
- movement feasibility
- scoring
- timing model
- state transition logic

This output must be compatible with the canonical DecisionObject model.

---

# 3. CORE STRATEGY QUESTION

The core strategy question is not:

"Is there movement?"

The core strategy question is:

"Is there enough probabilistic, structured, and time-feasible movement to justify a signal at the current state?"

This means the strategy must evaluate:

- directional coherence
- buffer feasibility
- corridor validity
- timing quality
- confidence progression by state

---

# 4. BUFFER PRINCIPLE

Buffer is the mathematical safety margin required between entry and projected price result.

The strategy must not promote a setup unless price movement is realistically sufficient to cover the required buffer within the model time horizon.

For BUY/CALL logic, the setup quality depends on the probability that price can move above entry plus required buffer.

For SELL/PUT logic, the setup quality depends on the probability that price can move below entry minus required buffer.

---

# 5. CANONICAL TIME MODEL RELATION

This algorithm must obey TIME_MODEL_CANON_v1.0.0.md.

The strategy must explicitly separate:

- `model_expiry_minutes`
- `trade_expiry_minutes`
- `telemetry_checkpoints`

Only `model_expiry_minutes` belongs directly to the internal feasibility model.

The strategy must never treat trader-facing execution expiry as identical to internal model feasibility time.

---

# 6. MODEL EXPIRY IN STRATEGY

## 6.1 Definition

`model_expiry_minutes` is the internal time horizon used by the strategy to determine whether the movement remains feasible.

## 6.2 Role in Feasibility

The strategy must evaluate whether the expected move can complete within the available model time horizon.

This includes:

- expected movement distance
- price speed
- corridor structure
- timing pressure
- directional persistence

## 6.3 Rule

If required movement time is greater than the available model feasibility horizon, the signal must not be promoted to executable states.

---

# 7. FEASIBILITY MODEL

A setup is feasible only if all of the following hold together:

- price movement remains directionally coherent
- the required buffer traversal is realistically achievable
- the corridor remains structurally valid
- the internal timing horizon remains compatible with required movement
- the setup retains enough quality score

Feasibility is therefore not a binary yes/no from one input.

It is a joint function of:

- movement
- structure
- time
- risk gates

---

# 8. CORRIDOR PRINCIPLE

The corridor defines whether the setup has a valid movement channel.

A valid corridor supports:

- direction continuity
- expected path realism
- buffer reachability
- controlled timing pressure

A setup may not advance if the corridor becomes blocked, structurally weak, or time-incompatible with the required buffer traversal.

---

# 9. TIMING PRESSURE

The strategy must evaluate timing pressure explicitly.

Timing pressure reflects how close the setup is to losing feasibility under the internal model time horizon.

This pressure influences:

- score quality
- urgency
- state progression
- degradation behavior

The relevant internal field is:

- `time_model.corridor_time_pressure`

This is an internal model concept, not a trader-facing execution field.

---

# 10. STATE PROGRESSION

The canonical progression is:

`PRE → CONFIRM → OPEN_NOW`

The strategy may also keep or degrade a setup depending on score, feasibility, and timing pressure.

---

## 10.1 PRE

PRE means the setup is promising but not yet in final execution form.

PRE may include:

- valid direction
- valid preliminary corridor
- acceptable score
- valid `model_expiry_minutes`

PRE does not require mandatory external trade expiry delivery.

PRE is primarily a monitored opportunity state.

---

## 10.2 CONFIRM

CONFIRM means the setup is sufficiently strong to prepare trader execution.

At this state:

- internal model feasibility remains valid
- corridor remains valid
- score has strengthened
- the setup supports a trader-facing expiry interval

CONFIRM must be described with interval semantics:

- `confirm_expiry_min_minutes`
- `confirm_expiry_max_minutes`

This is not the same thing as internal `model_expiry_minutes`.

---

## 10.3 OPEN_NOW

OPEN_NOW means the setup has reached critical execution timing.

At this state:

- internal model feasibility remains valid
- timing pressure is high enough to justify immediate action
- the setup supports an exact execution expiry

OPEN_NOW must be described with exact trader-facing expiry semantics:

- `open_now_expiry_minutes`

This value may be fractional if the mathematical model requires precision.

---

# 11. EXECUTION EXPIRY VS MODEL EXPIRY

The algorithm must distinguish between:

## Internal
- `model_expiry_minutes`

## External
- `confirm_expiry_min_minutes`
- `confirm_expiry_max_minutes`
- `open_now_expiry_minutes`

Execution expiry is downstream of internal model feasibility.

The strategy must not describe these as one undifferentiated field.

---

# 12. SCORE RELATION

Score is not independent of timing.

Score must reflect:

- direction quality
- corridor quality
- movement realism
- buffer feasibility
- timing compatibility

A setup with strong directional structure but weak timing feasibility must not be promoted as if timing were already valid.

---

# 13. DEGRADATION RULES

A setup may degrade if:

- corridor weakens
- required movement becomes unrealistic
- timing feasibility collapses
- score deteriorates
- internal time pressure becomes incompatible with continuation

Degradation may include:

- CONFIRM → PRE
- CONFIRM → REJECT
- OPEN_NOW → CONFIRM
- OPEN_NOW → REJECT

The algorithm must remain consistent with SIGNAL_DECISION_FSM_SPEC.md.

---

# 14. CONFIG RELATION

Old naming such as:

- `min_expiry_minutes`
- `max_expiry_minutes`

must not be interpreted generically.

If used in config, they must be explicitly documented as:

- internal model-time bounds, or
- trader execution delivery constraints

No ambiguous config wording is allowed in the canonical algorithm document.

---

# 15. OUTPUT RELATION

The strategy output must be compatible with canonical nested DecisionObject structure.

At minimum, timing-related output must conceptually align with:

- `time_model.model_expiry_minutes`
- `time_model.time_state`
- `time_model.corridor_time_pressure`
- `execution.confirm_expiry_min_minutes`
- `execution.confirm_expiry_max_minutes`
- `execution.open_now_expiry_minutes`
- `state.signal_state`

Flat fields such as `expiry_minutes` are not sufficient as canonical output description.

---

# 16. NON-GOALS

This document does not define:

- Telegram UX formatting
- telemetry checkpoint implementation detail
- event schema transport format
- runtime scheduler internals

Those are defined in other canonical documents.

---

# 17. FINAL PRINCIPLE

The strategy is valid only if movement, structure, buffer, and time are coherent together.

Timing is not a cosmetic field.

Timing is part of the mathematical validity of the signal.

Therefore:

- internal model time determines feasibility
- execution time determines trader delivery
- telemetry time determines post-open observation

These three layers must remain separate in all future canonical documentation and later code alignment.
