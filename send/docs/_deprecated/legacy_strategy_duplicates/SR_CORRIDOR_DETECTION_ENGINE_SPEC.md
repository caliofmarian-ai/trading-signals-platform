# SR CORRIDOR DETECTION ENGINE SPEC
## Canonical Support/Resistance Corridor Feasibility Specification

Version: 1.0.0  
Status: Canonical  
Scope: Strategy Engine / Corridor Feasibility / Timing Compatibility  
Depends On: TIME_MODEL_CANON_v1.0.0.md

---

# 1. PURPOSE

This document defines the canonical logic of the support/resistance corridor detection engine used by BinaryBot.

Its purpose is to determine whether a signal candidate has a structurally valid movement corridor that supports:

- directional continuation
- realistic buffer traversal
- timing-feasible progression
- compatibility with strategy state progression

The corridor engine is an internal feasibility subsystem.

It is not, by itself, a trader-facing expiry selector.

---

# 2. FUNDAMENTAL PRINCIPLE

A corridor is not just a visual price path.

A corridor is a structured feasibility channel.

It must answer the question:

"Does the setup still have enough structured movement space to remain valid under the internal strategy time model?"

This means corridor logic must be evaluated against:

- support/resistance structure
- expected path continuity
- reachability of required price distance
- time feasibility under `model_expiry_minutes`

---

# 3. CANONICAL TIME MODEL RELATION

This document must obey TIME_MODEL_CANON_v1.0.0.md.

The corridor engine must explicitly separate:

- `model_expiry_minutes`
- `trade_expiry_minutes`
- `telemetry_checkpoints`

Only `model_expiry_minutes` is native to corridor feasibility logic.

The corridor engine may influence downstream trade expiry derivation, but it must not define trader-facing execution expiry directly as its primary output.

---

# 4. CORRIDOR DEFINITION

A corridor is the structured price space through which price is expected to move while preserving the validity of the signal hypothesis.

A corridor may be bounded by:

- support
- resistance
- local range limits
- dynamic path constraints
- structure-aware movement channels

The corridor must remain:

- directionally coherent
- sufficiently open
- structurally believable
- temporally compatible

---

# 5. CORRIDOR VALIDITY

A valid corridor is one in which:

- the direction hypothesis remains plausible
- the path to the required buffer remains open enough
- no blocking structure invalidates the move too early
- the required movement remains achievable inside `model_expiry_minutes`

Corridor validity must never be defined by distance alone.

It is a joint function of:

- structure
- path openness
- expected movement
- available internal model time

---

# 6. BUFFER REACHABILITY INSIDE CORRIDOR

The corridor engine must evaluate whether the required buffer traversal remains plausible inside the corridor.

This means the engine must ask:

- how much movement is still required
- whether the corridor still supports that movement
- whether the movement can occur inside the internal time horizon

The relevant question is not:

"Can price move eventually?"

The relevant question is:

"Can price move sufficiently, inside the current valid corridor, before the model time window collapses?"

---

# 7. MODEL EXPIRY IN CORRIDOR LOGIC

## 7.1 Definition

`model_expiry_minutes` is the canonical internal time horizon used for corridor feasibility.

## 7.2 Rule

Any corridor reachability calculation must be evaluated against `model_expiry_minutes`.

This includes:

- path length realism
- resistance traversal
- support break probability
- buffer arrival plausibility
- timing pressure

## 7.3 Consequence

If the corridor cannot support the required traversal within `model_expiry_minutes`, the corridor must be marked insufficient for promotion.

---

# 8. EXPIRY REACH RATIO REDEFINED

Older wording such as `expiry_reach_ratio` must be interpreted canonically as a model-time feasibility concept.

Canonical meaning:

`model_time_reach_ratio`

This represents the relationship between:

- required traversal
- achievable traversal
- available internal model time

It must not be used as a synonym for trader-facing execution expiry.

---

# 9. CORRIDOR PRESSURE

The corridor engine must evaluate timing pressure inside the corridor.

Timing pressure means how rapidly the valid movement window is shrinking relative to the required traversal.

Relevant effects:

- rising urgency
- degraded tolerance for delay
- reduced confidence in continuation
- state escalation or rejection

This pressure belongs to the internal model layer and aligns with:

- `time_model.corridor_time_pressure`

---

# 10. RELATION TO PRE / CONFIRM / OPEN_NOW

The corridor engine does not define signal states by itself, but it contributes to them.

---

## 10.1 PRE

At PRE level, the corridor may still be preliminary.

Requirements typically include:

- directionally plausible path
- no immediate structural invalidation
- realistic possibility of future buffer reachability
- valid internal timing horizon

No mandatory external trade expiry is required at this stage.

---

## 10.2 CONFIRM

At CONFIRM level, the corridor must support stronger feasibility.

Requirements typically include:

- a still-open movement path
- better confidence in buffer traversal
- internal timing compatibility robust enough to justify an execution interval

Any trader-facing expiry interval remains downstream of corridor feasibility.

The corridor engine supports the derivation but does not collapse into the final execution expiry field.

---

## 10.3 OPEN_NOW

At OPEN_NOW level, the corridor must support critical execution timing.

Requirements typically include:

- sufficiently strong immediate path validity
- low tolerance for further delay
- feasible final movement under current timing pressure

The corridor engine may support downstream exact execution expiry derivation, but the canonical trader-facing field remains:

- `open_now_expiry_minutes`

This is downstream of corridor feasibility, not identical to it.

---

# 11. RECOMMENDED EXECUTION TIME WORDING

Older wording such as:

- recommended expiry
- corridor recommended expiry

must be interpreted carefully.

Canonical rule:

The corridor engine may emit guidance that contributes to execution-time derivation, but this guidance must be described as downstream influence, not as a direct replacement for:

- `model_expiry_minutes`
- `confirm_expiry_min_minutes`
- `confirm_expiry_max_minutes`
- `open_now_expiry_minutes`

---

# 12. REJECTION CONDITIONS

The corridor must be considered insufficient if any of the following are true:

- the path is structurally blocked
- the remaining movement space is too narrow
- the required buffer cannot be reached plausibly
- timing pressure is too high for remaining traversal
- feasibility collapses before the setup reaches a valid state

This insufficiency may contribute to:

- REJECT
- PRE retention without promotion
- CONFIRM degradation
- OPEN_NOW invalidation

---

# 13. OUTPUT RELATION

The corridor engine should conceptually feed the strategy with corridor feasibility information, not final trader formatting.

Its output should remain compatible with canonical nested structures such as:

- `time_model.model_expiry_minutes`
- `time_model.corridor_time_pressure`
- `time_model.time_state`

It may also influence execution derivation indirectly, but must not flatten everything into an ambiguous `expiry_minutes` field.

---

# 14. CONFIG RELATION

If corridor-related parameters refer to expiry or timing, they must be scoped clearly.

Examples of correct interpretation:

- internal model feasibility bounds
- timing pressure thresholds
- corridor traversal tolerance

Incorrect interpretation:

- using a generic `expiry_minutes` label for mixed model and execution semantics

---

# 15. NON-GOALS

This document does not define:

- final Telegram wording
- full DecisionObject schema
- telemetry checkpoint schedule
- runtime outcome observation

These are handled in other canonical documents.

---

# 16. FINAL PRINCIPLE

The SR corridor engine is a model-feasibility subsystem.

Its primary responsibility is to determine whether structured movement remains possible inside the available internal time horizon.

Therefore:

- corridor feasibility uses `model_expiry_minutes`
- trader execution expiry remains downstream
- telemetry remains separate

No future canonical documentation may collapse these three layers into one ambiguous corridor expiry concept.
