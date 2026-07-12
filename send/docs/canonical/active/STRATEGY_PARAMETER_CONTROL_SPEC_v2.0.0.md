# STRATEGY_PARAMETER_CONTROL_SPEC_v2.0.0

Version: 2.0.0  
Status: Active Canonical  
Path: /opt/binarybot/docs/canonical/active/STRATEGY_PARAMETER_CONTROL_SPEC_v2.0.0.md

Linked Documents:
- SYSTEM_INVARIANTS_v2.0.0.md
- SYSTEM_ARCHITECTURE_MAP_v2.0.0.md
- MODULE_INTERFACE_SPEC_v2.0.0.md
- GOVERNANCE_AND_CHANGE_CONTROL_v2.0.0.md
- DECISION_AUDIT_SPEC_v2.0.0.md
- PERFORMANCE_ANALYTICS_SPEC_v2.0.0.md
- TELEGRAM_UX_v2.0.0.md
- OBSERVABILITY_LOGGING_SPEC_v2.0.0.md
- SIGNAL_DISTRIBUTION_SPEC_v2.0.0.md
- OUTCOME_TRACKING_SPEC_v2.0.0.md

Depends on:
- SYSTEM_INVARIANTS_v2.0.0.md
- MODULE_INTERFACE_SPEC_v2.0.0.md
- GOVERNANCE_AND_CHANGE_CONTROL_v2.0.0.md
- DECISION_AUDIT_SPEC_v2.0.0.md
- PERFORMANCE_ANALYTICS_SPEC_v2.0.0.md

Code Alignment:
- bot_service.py
- core/params_loader.py
- core/strategy_v2.py
- core/signal_engine.py
- core/fsm_runtime.py
- core/observability_logger.py
- admin command handlers
- config/strategy_params.json

## 0. Purpose

This document defines the canonical parameter-control model for BinaryBot / DROPi Signals.

Its role is to separate stable strategy logic from controlled runtime parameterization, so that bounded strategy tuning can occur without direct source-code edits for every operational adjustment.

This document defines:
- what categories of parameters are controllable
- which layer owns parameter mutation
- which layer consumes parameter values
- how validation, persistence, reload, and proof logging must work
- what safety boundaries constrain parameter updates
- how governance and analytics must discipline parameter changes

This document does not authorize uncontrolled live experimentation.  
It defines the controlled surface through which approved parameter changes may be applied.

Its purpose is to prevent:
- source-code edits for simple tuning
- undocumented threshold mutation
- unsafe runtime overrides
- invalid parameter ranges
- silent admin-side behavioral drift
- parameter mutation without audit trail
- tuning without analytics and governance discipline

## 1. Canonical Position

This document belongs primarily to the ADMIN layer and secondarily influences the ENGINE layer.

Its canonical role is to define the bounded control surface through which authorized operators may adjust runtime strategy parameters without redefining structural strategy logic.

The relationship is:

ADMIN CONTROL SURFACE  
→ PARAMETER VALIDATION AND PERSISTENCE  
→ ENGINE PARAMETER LOAD  
→ STRATEGY DECISION BEHAVIOR

This document does not move strategy ownership into ADMIN.  
ENGINE still owns strategy execution truth.  
ADMIN only owns the authorized mutation surface for eligible tunable values.

If a behavior requires changing strategy structure rather than parameter values, that behavior falls outside this document and must be governed as a structural change under canonical governance.

## 2. Final Principle

Strategy parameters may be controlled dynamically only within explicit canonical bounds, explicit authority rules, explicit validation ranges, and explicit auditability requirements.

A parameter-control behavior is non-canonical if it introduces any of the following:
- direct mutation of structural logic disguised as parameter tuning
- hidden runtime overrides
- invalid or unbounded values
- changes without proof logging
- role bypass
- changes without rollback path
- parameter mutation that outruns governance and analytics discipline

Parameter control exists to make tuning safer, not to make the system improvisational.

## 3. Scope of Parameter Control

Parameter control applies only to runtime-tunable values explicitly classified as controllable.

These include categories such as:
- signal thresholds
- timing or expiry values
- support/resistance distance buffers
- spike filter limits
- trend confirmation settings
- symbol inclusion/exclusion surfaces
- bounded routing-related strategy parameters where canonically assigned
- bounded risk-linked parameters if and only if separately authorized by active canonical docs

Parameter control does not automatically include:
- score formula redesign
- lifecycle rule redesign
- new gate creation
- event schema changes
- audit taxonomy changes
- role/permission redesign
- hidden alternate strategy modes unless canonically documented

If changing a value would effectively redefine system structure or ownership, it is not a parameter-only change.

## 4. Ownership Model

Parameter control requires explicit ownership boundaries.

### 4.1 ADMIN Ownership

ADMIN owns:
- input surface for authorized parameter change requests
- command/UI access control
- bounded submission of new values
- proof logging of who changed what
- safe exposure of readable current values
- rollback or reset entrypoints where permitted

### 4.2 ENGINE Ownership

ENGINE owns:
- interpretation of accepted parameter values during runtime decision generation
- use of loaded parameters in canonical decision flow
- refusal to treat missing/invalid values as implicit license for undefined behavior
- stable execution after reload

### 4.3 PERSISTENCE Ownership

The persistence/config layer owns:
- durable storage of canonical runtime parameters
- atomic update semantics
- last-known-good state preservation
- reload-safe data format
- protection against partial writes or corrupt mutation

### 4.4 GOVERNANCE Ownership

Governance owns:
- authority rules
- change approval discipline
- versioning implications
- monitoring window expectations
- freeze mode constraints
- change-class interpretation

### 4.5 ANALYTICS / AUDIT Relationship

Analytics and audit do not directly mutate parameters.  
They provide evidence used to justify or reject change proposals.

## 5. Parameter Groups

Canonical parameter groups may include the following categories.

### 5.1 Threshold Parameters

Threshold parameters govern progression gates or scoring cutoffs.

Examples:
- PRE threshold
- CONFIRM threshold
- OPEN_NOW threshold
- bounded shortlist or watch thresholds where canonically used

These values materially affect trade frequency and stage conversion behavior.

### 5.2 Support / Resistance Parameters

These parameters govern minimum safe distance from relevant support/resistance structures.

Examples:
- SR buffer
- profile-based SR buffer sets
- volatility-adjusted SR distance multipliers where canonically supported

### 5.3 Spike Detection Parameters

These parameters govern rejection or filtering of abnormal candle behavior.

Examples:
- wick ratio limit
- ATR jump limit
- candle anomaly thresholds
- volatility shock filters

### 5.4 Trend Filter Parameters

These parameters govern directional confirmation.

Examples:
- EMA gap minimum
- trend confirmation bars
- slope filters
- distance-to-trend thresholds

### 5.5 Symbol Control Parameters

These parameters govern which symbols are eligible for runtime monitoring/trading.

Examples:
- active symbol list
- symbol disable list
- symbol class filters
- bounded per-symbol enable/disable controls

### 5.6 Timing / Lifecycle-Adjacent Parameters

If canonically allowed, some bounded timing values may be runtime-controlled.

Examples:
- expiry windows
- timing buffers
- confirmation wait tolerances

These values must be treated carefully because they may border structural lifecycle behavior.

## 6. Control Surfaces

Parameters may be modified only through canonical control surfaces.

Allowed surfaces may include:
- Telegram admin commands
- admin control panel
- controlled config update workflows
- approved maintenance tooling
- governance-approved migration scripts

Primary control surface may be Telegram/admin interface, but every surface must obey the same rules:
- permission checks
- input validation
- proof logging
- persistence discipline
- reload confirmation
- failure visibility

No side-channel or ad hoc file editing is canonical parameter control.

## 7. Canonical Parameter Storage

Strategy parameters must persist in a canonical runtime configuration source.

Recommended canonical storage:
- `/opt/binarybot/config/strategy_params.json`

The exact implementation may evolve, but the storage model must satisfy:
- machine-readable structure
- atomic writes
- recoverability
- validation before commit
- compatibility with runtime reload
- traceability to proof logs

Illustrative structure:

```json
{
  "thresholds": {
    "pre": 70,
    "confirm": 75,
    "open": 80
  },
  "sr_buffer": 0.0006,
  "spike": {
    "wick_ratio": 5.0,
    "atr_jump": 2.2
  },
  "trend": {
    "ema_gap": 0.0004,
    "confirm_bars": 3
  },
  "symbols": {
    "enabled": ["EURUSD", "GBPUSD"]
  }
}
```

The example above is illustrative, not exhaustive. 

## 8. Load and Reload Discipline

The engine must load parameters from the canonical configuration source in a deterministic way.

Canonical load points may include:

engine startup

controlled refresh cycle

post-admin approved parameter update

restart recovery path


Reload behavior must satisfy:

validation before acceptance

no partial application

stable switch from old to new value set

refusal or rollback on invalid state

observability event for successful or failed reload


A parameter change is not fully complete until the system confirms whether reload succeeded.

## 9. Live Update Rules

When an authorized admin changes a parameter:

1. the request is authenticated


2. the role is verified


3. the requested value is validated


4. the persistence layer updates canonically


5. the system attempts controlled reload


6. the result is logged


7. the operator receives success/failure feedback


8. the previous value remains recoverable



“Immediate effect” is allowed only if the change completes the full safe path above.

No live update may bypass validation and persistence just because it is operationally convenient.

## 10. Validation Rules

Every controllable parameter must have an explicit validation rule.

Validation dimensions may include:

numeric range

allowed enum/profile values

allowed symbol syntax

bounded step size

cross-field consistency

governance freeze-state blocking

role-based scope restrictions


Illustrative examples from the legacy spec include:

thresholds constrained within an allowed band

SR buffer constrained within an allowed band

invalid values rejected instead of coerced silently

profile selection limited to predefined profile names 


Validation must reject:

malformed values

out-of-range values

structurally dangerous values

values forbidden in freeze mode

changes outside role authority


## 11. Proof Logging and Auditability

Every parameter mutation attempt must be observable.

At minimum, proof logging should capture:

event type

parameter or parameter group

old value

proposed new value

final accepted value if different from proposed

requesting role

requesting actor

timestamp

success/failure status

validation or rejection reason

reload result

rollback result if triggered


Recommended proof destination may include:

/opt/binarybot/observability/admin_proofs.jsonl 


Parameter changes without proof logs are non-canonical even if the runtime value changed successfully.

## 12. Role Permissions

Parameter mutation rights must be role-scoped.

Illustrative role pattern:

OWNER: full control within governance constraints

PRIMARY_ADMIN: bounded operational control

ANALYST: read-only

affiliate or specialist roles: no strategy mutation unless explicitly authorized


Role access must define not only who can change parameters, but also:

which parameter groups each role may touch

whether a role may only view values

whether a role may trigger resets or rollback

whether approval from a higher role is required for sensitive changes


No role system may silently grant full parameter mutation to all admins.

## 13. Safety Mechanisms

Parameter control must include explicit safety protections.

These may include:

max delta limits per change

profile-based safer presets

rollback to last-known-good values

emergency reset to canonical defaults

freeze-mode blocking

cooldown between sensitive mutations

rejection of repeated rapid changes

protection against conflicting simultaneous writes


Safety exists because runtime tunability increases drift risk if left uncontrolled.

## 14. Parameter Profiles

Where useful, predefined parameter profiles may be offered instead of raw numeric input.

Examples:

small / medium / large buffer profiles

conservative / balanced / aggressive but canonically bounded profiles

symbol packs or preset groups


Profiles are allowed only when:

mappings are explicitly documented

mappings remain bounded

profile application is logged

profiles do not act as hidden structural mode switches


A profile is a parameter bundle, not a secret alternate strategy.

## 15. Symbol Control Rules

Dynamic symbol control is permitted only if symbol mutation remains:

role-gated

validated

persistent

reload-safe

observable

reversible


Allowed operations may include:

list symbols

add symbol

remove symbol

enable/disable symbol

apply approved symbol groups


Symbol control must not:

create undocumented market-universe drift

silently disable major operational coverage

allow malformed or unsupported symbol identifiers

bypass governance if symbol scope materially changes risk posture


## 16. Governance Discipline for Parameter Changes

Not every parameter change has the same significance.

The governance class of a parameter change depends on:

behavioral impact

affected layer interaction

blast radius

coupling with other changes

whether the value is routine tuning or materially alters strategy behavior


Parameter changes must therefore reference:

relevant analytics

relevant audit findings

change proposal or admin proof trail

monitoring expectations

rollback conditions


Under freeze mode, non-essential parameter changes must be blocked.

## 17. Relationship to Analytics and Learning

Analytics may identify patterns such as:

thresholds too strict

thresholds too loose

excessive spike-filter deaths

symbol starvation

low PRE→CONFIRM conversion

over-filtering near SR

excessive open suppression


These findings may justify human-reviewed parameter proposals.

However:

analytics may recommend

analytics may summarize

analytics may diagnose


Analytics may not silently mutate live parameters unless a separate active canonical automation framework explicitly authorizes that behavior.

## 18. Relationship to Other Specifications

This document is closely related to:

governance and change control

module interface contracts

observability logging

admin UX/control surfaces

decision audit and performance analytics

any role/permission spec that later becomes active canonical

any deployment or rollback spec that governs runtime config mutation


If conflict exists between this document and governance, governance takes precedence for approval and operational discipline.

If conflict exists between this document and module contract ownership, module ownership boundaries take precedence.

## 19. Non-Canonical Patterns

The following patterns are forbidden or non-canonical:

editing source code just to change a tunable threshold

editing config files manually in production without controlled process

changing values without proof logs

changing values outside validation bounds

using parameter surfaces to simulate hidden strategy redesign

mass multi-parameter tuning without attribution discipline

allowing admin UI to bypass persistence and write directly into live memory

letting stale config and live runtime diverge silently


## 20. Final Canonical Statement

The strategy parameter control surface exists to make runtime tuning controlled, bounded, reversible, and auditable.

ADMIN may own the mutation surface.
ENGINE owns execution truth.
GOVERNANCE owns approval discipline.
OBSERVABILITY owns proof of change.
ANALYTICS may inform tuning, but may not silently seize control.

This document is the authoritative canonical specification for strategy parameter control in BinaryBot / DROPi Signals. 