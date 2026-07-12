# TIME MODEL CANON
## Canonical Time Model for Strategy, Execution and Telemetry

Version: 1.0.0  
Status: Canonical  
Scope: Strategy Engine / Signal Engine / Distribution / Telemetry

---

# 1. PURPOSE

This document defines the canonical time model of the BinaryBot signal system.

Its purpose is to separate clearly the following concepts:

- model time
- trader execution time
- telemetry observation time

This document exists because older documentation used ambiguous concepts such as:

- expiry
- expiry_minutes
- trade_expiry

without a strict separation of meaning.

This document is the canonical reference for all future updates to:

- ALGO_SPEC.md
- SR_CORRIDOR_DETECTION_ENGINE_SPEC.md
- SIGNAL_DECISION_FSM_SPEC.md
- PARAMS_REFERENCE.md
- MODULE_INTERFACE_SPEC.md

---

# 2. CANONICAL TIME LAYERS

The canonical time model has exactly three layers:

1. `model_expiry_minutes`
2. `trade_expiry_minutes`
3. `telemetry_checkpoints`

These layers must not be collapsed into a single ambiguous field.

---

# 3. MODEL EXPIRY

## 3.1 Definition

`model_expiry_minutes` is the internal time horizon used by the strategy engine.

It represents the time window in which the model considers the setup mathematically feasible.

## 3.2 Role

It is used for:

- feasibility
- corridor pressure
- scoring
- time-state transitions
- PRE / CONFIRM / OPEN_NOW decision logic

## 3.3 Nature

This value is internal.

It is not automatically the same as the trader execution duration.

---

# 4. TRADE EXPIRY

## 4.1 Definition

`trade_expiry_minutes` is the execution-layer expiry delivered to the trader or execution payload.

It belongs to the signal delivery layer, not directly to the internal model.

## 4.2 Derived Forms

Depending on signal state, it appears as:

- `confirm_expiry_min_minutes`
- `confirm_expiry_max_minutes`
- `open_now_expiry_minutes`

## 4.3 State Rules

### PRE
PRE does not require mandatory external trade expiry.

### CONFIRM
CONFIRM delivers an expiry interval:

- `confirm_expiry_min_minutes`
- `confirm_expiry_max_minutes`

### OPEN_NOW
OPEN_NOW delivers an exact expiry value:

- `open_now_expiry_minutes`

This value may be fractional and must not be rounded arbitrarily if the mathematical model requires precision.

---

# 5. TELEMETRY CHECKPOINTS

## 5.1 Definition

`telemetry_checkpoints` are observation timestamps used after trade opening.

They are not part of the internal strategy feasibility model and they are not the same as trader execution expiry.

## 5.2 Examples

Telemetry checkpoints may include:

- midpoint checkpoint
- at-expiry checkpoint
- post-expiry +1 minute
- post-expiry +3 minutes
- post-expiry +5 minutes

## 5.3 Role

They are used for:

- result observation
- post-expiry recovery analysis
- expiry calibration analysis
- distinction between bad trade and wrong expiry selection

---

# 6. RELATION BETWEEN THE THREE LAYERS

The canonical relation is:

`model_expiry_minutes`
→ used to derive
`trade_expiry_minutes`
→ used to schedule / interpret
`telemetry_checkpoints`

This does not mean the three values are equal.

They are related, but not identical.

---

# 7. STATE-SPECIFIC TIME MODEL

## 7.1 PRE

PRE may contain internal model time only.

Typical fields:

- `model_expiry_minutes`
- `time_state`
- `corridor_time_pressure`

External execution expiry is optional and normally omitted.

## 7.2 CONFIRM

CONFIRM contains:

- internal model time
- external execution expiry range

Typical external fields:

- `confirm_expiry_min_minutes`
- `confirm_expiry_max_minutes`

## 7.3 OPEN_NOW

OPEN_NOW contains:

- internal model time
- exact external execution expiry

Typical external field:

- `open_now_expiry_minutes`

---

# 8. DECISION OBJECT RELATION

The canonical DecisionObject must separate time blocks clearly.

Recommended structure:

- `time_model.model_expiry_minutes`
- `time_model.time_state`
- `time_model.corridor_time_pressure`

- `execution.confirm_expiry_min_minutes`
- `execution.confirm_expiry_max_minutes`
- `execution.open_now_expiry_minutes`

- `telemetry.telemetry_checkpoints`

Flat ambiguous fields such as:

- `expiry`
- `expiry_minutes`

must not be used without explicit context.

---

# 9. PARAMETER MODEL RELATION

Config-level expiry parameters must be reviewed in relation to the canonical time model.

Old names such as:

- `min_expiry_minutes`
- `max_expiry_minutes`
- `expiry_limits_minutes`

must be interpreted carefully:

- if they bound internal model time, they belong to model expiry config
- if they define trader delivery constraints, they belong to trade expiry config

These meanings must not remain mixed in future canonical documents.

---

# 10. FSM RELATION

The FSM must use the canonical time model as follows:

- PRE uses model feasibility and early timing confidence
- CONFIRM uses model feasibility plus tradable range
- OPEN_NOW uses model critical timing plus exact trader expiry

Deprecated or intermediary states such as `OPEN_READY` must be reviewed for compatibility with the canonical sequence:

`PRE → CONFIRM → OPEN_NOW`

---

# 11. TELEMETRY RELATION

Telemetry is downstream of execution.

It must not redefine strategy feasibility.

Telemetry must observe:

- open timestamp
- expected trade expiry timestamp
- checkpoint timestamps
- result at expiry
- post-expiry continuation

It must not reuse ambiguous wording where model time and observation time are confused.

---

# 12. CANONICAL TERMINOLOGY RULE

The following generic terms are not sufficient on their own:

- `expiry`
- `expiry_minutes`

They may appear only if the document explicitly states which of the following is meant:

- `model_expiry_minutes`
- `trade_expiry_minutes`
- `telemetry_checkpoints`
- `confirm_expiry_min_minutes`
- `confirm_expiry_max_minutes`
- `open_now_expiry_minutes`

---

# 13. PATCH IMPLICATIONS

Any canonical document that currently mixes the three layers must be patched.

Wave 1 targets:

- ALGO_SPEC.md
- SR_CORRIDOR_DETECTION_ENGINE_SPEC.md
- SIGNAL_DECISION_FSM_SPEC.md
- PARAMS_REFERENCE.md
- MODULE_INTERFACE_SPEC.md

Wave 2 and Wave 3 documents must be aligned afterwards.

---

# 14. FINAL PRINCIPLE

The BinaryBot canonical time model is:

- one internal model time
- one execution-layer trade time
- one telemetry-layer observation schedule

These are connected, but not identical.

This separation is mandatory for:

- strategy clarity
- signal correctness
- telemetry correctness
- documentation consistency
- future code alignment
