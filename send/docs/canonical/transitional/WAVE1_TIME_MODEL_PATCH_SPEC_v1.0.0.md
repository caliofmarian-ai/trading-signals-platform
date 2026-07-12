# WAVE1 TIME MODEL PATCH SPEC
## Canonical Patch Specification for Wave 1 Documentation Alignment

Version: 1.0.0  
Status: Canonical Patch Specification  
Scope: Wave 1 / P1 Documentation Alignment  
Depends On: TIME_MODEL_CANON_v1.0.0.md

---

# 1. PURPOSE

This document defines the official Wave 1 patch scope for canonical documentation alignment after introduction of the central time model canon.

Wave 1 exists to update the highest-priority canonical documents that still use ambiguous timing concepts such as:

- expiry
- expiry_minutes
- min_expiry_minutes
- max_expiry_minutes
- expiry_limits_minutes
- OPEN_READY
- flat signal_state
- flat decision payload structures

The purpose of this document is to prepare deterministic documentation patching before any code realignment begins.

---

# 2. WAVE 1 DOCUMENT SET

Wave 1 includes exactly these documents:

1. ALGO_SPEC.md
2. SR_CORRIDOR_DETECTION_ENGINE_SPEC.md
3. SIGNAL_DECISION_FSM_SPEC.md
4. PARAMS_REFERENCE.md
5. MODULE_INTERFACE_SPEC.md

These documents are considered core because they define:

- strategy time logic
- corridor feasibility logic
- signal state progression
- parameter naming
- strategy output / interface contract

---

# 3. PATCH PRINCIPLES

All Wave 1 patches must obey the following canonical principles:

## 3.1 Time Separation

The documentation must clearly separate:

- `model_expiry_minutes`
- `trade_expiry_minutes`
- `telemetry_checkpoints`

No Wave 1 document may continue to use `expiry_minutes` as a single ambiguous concept when multiple meanings are implied.

## 3.2 State Delivery Rules

State-specific delivery rules must be preserved:

- PRE → internal model time may exist, external trade expiry optional
- CONFIRM → external expiry delivered as interval
- OPEN_NOW → external expiry delivered as exact value

## 3.3 Decision Object Structure

Any old flat output model must be rewritten toward canonical DecisionObject structure, especially for:

- `time_model`
- `execution`
- `state`
- `telemetry`

## 3.4 No Silent Meaning Drift

Generic words like `expiry` may remain only if the document explicitly states which layer is meant.

---

# 4. DOCUMENT-BY-DOCUMENT PATCH SPEC

## 4.1 ALGO_SPEC.md

### Patch Type
TIME_MODEL_SPLIT

### Problem
ALGO_SPEC currently uses generic expiry terminology for:

- feasibility
- buffer reachability
- expiry window
- OPEN_NOW logic
- min/max expiry naming

This creates ambiguity between internal model feasibility time and trader execution time.

### Required Patch
ALGO_SPEC must be rewritten so that:

- strategy feasibility uses `model_expiry_minutes`
- PRE/CONFIRM/OPEN_NOW sections reference delivery rules explicitly
- CONFIRM is described using expiry interval semantics
- OPEN_NOW is described using exact execution expiry semantics
- old `min_expiry_minutes` / `max_expiry_minutes` wording is reviewed and relocated to proper config meaning

### Mandatory New References
- TIME_MODEL_CANON_v1.0.0.md
- DecisionObject time model block
- state-specific time delivery rules

### Expected Result
ALGO_SPEC becomes the canonical mathematical source for strategy timing and no longer mixes model time with trade delivery time.

---

## 4.2 SR_CORRIDOR_DETECTION_ENGINE_SPEC.md

### Patch Type
TIME_MODEL_SPLIT

### Problem
The corridor engine spec currently uses:

- `expiry_minutes`
- `expiry_reach_ratio`
- recommended expiry wording
- buffer reachability under expiry

without clearly distinguishing whether this refers to model feasibility time or trader execution time.

### Required Patch
SR corridor documentation must be rewritten so that:

- corridor feasibility calculations use `model_expiry_minutes`
- any recommended execution time is described as downstream derivation into trade expiry
- `expiry_reach_ratio` is redefined against model time
- no direct collapse remains between corridor feasibility and delivered trade expiry

### Mandatory New References
- model feasibility layer from TIME_MODEL_CANON_v1.0.0.md
- relation between corridor model and DecisionObject.time_model

### Expected Result
The corridor engine becomes strictly an input to model feasibility, not an ambiguous direct selector of trader-facing expiry.

---

## 4.3 SIGNAL_DECISION_FSM_SPEC.md

### Patch Type
FSM_STATE_ALIGNMENT

### Problem
FSM documentation still references intermediary compatibility concepts such as `OPEN_READY`, which conflicts with the preferred canonical sequence:

PRE → CONFIRM → OPEN_NOW

### Required Patch
FSM documentation must be reviewed and rewritten so that:

- the canonical state chain is explicit
- PRE timing semantics are separated from CONFIRM and OPEN_NOW
- any retained `OPEN_READY` concept is either:
  - deprecated, or
  - explicitly defined as transitional / compatibility-only
- timing transitions must reference model time vs execution time correctly

### Mandatory New References
- TIME_MODEL_CANON_v1.0.0.md
- state-specific time rules
- DecisionObject.state.signal_state

### Expected Result
FSM documentation expresses the canonical signal state progression without ambiguity and without forcing an obsolete intermediary state into the main model.

---

## 4.4 PARAMS_REFERENCE.md

### Patch Type
PARAMETER_NAMING_ALIGNMENT

### Problem
PARAMS_REFERENCE still contains naming such as:

- `expiry_limits_minutes`
- `min_expiry_minutes`
- `max_expiry_minutes`

These names are ambiguous unless their role is explicitly scoped to internal model bounds or trader delivery bounds.

### Required Patch
PARAMS_REFERENCE must be rewritten so that:

- bounds on model time are clearly documented as model-time configuration
- execution delivery constraints, if any, are documented separately
- old names are either:
  - deprecated, or
  - explicitly scoped with canonical meaning

### Mandatory New References
- parameter relation section from TIME_MODEL_CANON_v1.0.0.md

### Expected Result
Parameter documentation becomes deterministic and no longer allows mixed interpretation of expiry bounds.

---

## 4.5 MODULE_INTERFACE_SPEC.md

### Patch Type
DECISION_OBJECT_ALIGNMENT

### Problem
MODULE_INTERFACE_SPEC still uses flat fields such as:

- `expiry_minutes`
- `signal_state`

This conflicts with the canonical DecisionObject structure.

### Required Patch
MODULE_INTERFACE_SPEC must be rewritten so that the strategy output contract becomes nested and explicit.

Minimum required structure alignment:

- `time_model.model_expiry_minutes`
- `time_model.time_state`
- `time_model.corridor_time_pressure`
- `execution.confirm_expiry_min_minutes`
- `execution.confirm_expiry_max_minutes`
- `execution.open_now_expiry_minutes`
- `state.signal_state`
- optional telemetry block where relevant

### Mandatory New References
- TIME_MODEL_CANON_v1.0.0.md
- canonical DecisionObject model
- state-specific execution semantics

### Expected Result
Interface documentation becomes directly usable for later code alignment without ambiguity on expiry or signal state placement.

---

# 5. PATCH ORDER INSIDE WAVE 1

Wave 1 must be executed in this order:

1. ALGO_SPEC.md
2. SR_CORRIDOR_DETECTION_ENGINE_SPEC.md
3. SIGNAL_DECISION_FSM_SPEC.md
4. PARAMS_REFERENCE.md
5. MODULE_INTERFACE_SPEC.md

Reason:

- first define strategy timing logic
- then define corridor timing logic
- then align FSM transitions
- then align parameters
- finally align interface contract

---

# 6. PATCH ACCEPTANCE CRITERIA

A Wave 1 document patch is accepted only if all of the following are true:

## 6.1 Terminology Criteria
The document no longer relies on ambiguous standalone use of:

- expiry_minutes
- expiry

unless the exact layer is explicitly stated.

## 6.2 Time Model Criteria
The document is compatible with:

- `model_expiry_minutes`
- `trade_expiry_minutes`
- `telemetry_checkpoints`

## 6.3 State Criteria
If the document references PRE / CONFIRM / OPEN_NOW, then:

- PRE timing semantics are distinct
- CONFIRM interval semantics are explicit
- OPEN_NOW exact expiry semantics are explicit

## 6.4 Interface Criteria
If the document defines payload or output structure, it must be compatible with canonical DecisionObject nesting.

---

# 7. NON-GOALS OF WAVE 1

Wave 1 does not yet patch:

- architecture-wide narrative cleanup
- UX-only refinements
- telemetry deep spec rewrite
- event schema full alignment
- code implementation

Those belong to later waves.

---

# 8. OUTPUT OF WAVE 1

The output of Wave 1 must be:

- updated P1 canonical documents
- no unresolved ambiguity on strategy time model
- no ambiguity between model time and execution time
- a stable basis for later code alignment audit

---

# 9. FINAL PRINCIPLE

Wave 1 is the core documentation stabilization layer.

No code alignment step should begin until these five documents are rewritten against:

TIME_MODEL_CANON_v1.0.0.md

This document is therefore the binding patch specification for the first documentation rewrite wave.
