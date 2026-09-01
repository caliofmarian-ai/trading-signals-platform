# STRATEGY_PARAMETER_CONTROL_SPEC_v3.0.0

Path: /opt/binarybot/docs/canonical/active/STRATEGY_PARAMETER_CONTROL_SPEC_v3.0.0.md  
Version: 3.0.0  
Status: ACTIVE CANONICAL  
Owner: BinaryBot / DROPi Signals  
Scope: Governed runtime/experimental strategy parameter control, Trade Physics constants, model authority controls, validation, persistence, rollback

Supersedes: `STRATEGY_PARAMETER_CONTROL_SPEC_v2.0.0.md`
Governance basis: Change ID `20260901-TRADE-PHYSICS-01`; merged PR #78

---

## 0. PROMOTION STATUS

Promotion status: ACTIVE CANONICAL under `CANONICAL_ACTIVATION_RECORD_20260901.md` and `CANONICAL_MASTER_INDEX_v2.0.0.md`.

---

## 1. PURPOSE

This specification governs which strategy values may be viewed, proposed, tested, changed, persisted and rolled back without confusing configuration control with structural strategy redesign.

v3 integrates Trade Physics controls while preserving a critical rule:

**numeric does not automatically mean tunable.**

Trade Physics contains structural formulas, initial constants, future experimental candidates and learned-model authority controls. Each class requires distinct governance.

---

## 2. PARAMETER CONTROL IS NOT STRATEGY REDESIGN

The parameter-control layer may manage only values explicitly classified by active canon.

It does not automatically authorize:

- formula redesign;
- new Trade Physics dimensions;
- time-ratio redefinition;
- directional-speed algorithm redesign;
- DecisionObject schema change;
- new TPS lifecycle gates;
- learned-model authority escalation;
- event schema changes.

Those are structural changes requiring versioned canonical governance.

---

## 3. PARAMETER CLASSES

Every controlled value must belong to one class.

### 3.1 RUNTIME_TUNABLE

May be changed in production within explicit bounds by authorized roles with audit/rollback.

### 3.2 EXPERIMENT_TUNABLE

May be changed only in approved staging/experimental scope. Production requires separate approved promotion.

### 3.3 STRUCTURAL_CONSTANT

Part of the current canonical formula/architecture. Cannot be changed by ordinary runtime control.

### 3.4 READ_ONLY_DERIVED

Calculated from market/strategy evidence and never manually set.

### 3.5 MODEL_ARTIFACT_CONTROL

Selects/suspends a validated model artifact or authority mode according to model/governance rules; does not alter the model's learned weights in place.

---

## 4. TRADE PHYSICS V1 CLASSIFICATION

Initial proposed classifications:

| value | proposed class | reason |
|---|---|---|
| `available_space` | READ_ONLY_DERIVED | owned by Corridor structural truth |
| `required_space` | READ_ONLY_DERIVED | v1 derived from buffer distance |
| `space_to_buffer_ratio` | READ_ONLY_DERIVED | deterministic formula |
| `trade_space_margin_atr` | READ_ONLY_DERIVED | deterministic formula |
| `time_to_buffer_ratio` | READ_ONLY_DERIVED | derived from Time Model |
| `directional_effective_speed` | READ_ONLY_DERIVED | deterministic candle evidence |
| `flow_efficiency` | READ_ONLY_DERIVED | deterministic formula |
| `movement_stress` | READ_ONLY_DERIVED | deterministic formula |
| `S/T/P/V` | READ_ONLY_DERIVED | normalized components |
| `TPS` | READ_ONLY_DERIVED | deterministic final score |
| `S_cap = 3.0` | STRUCTURAL_CONSTANT initially | source default locked until evidence-based change |
| `T_cap = 2.0` | STRUCTURAL_CONSTANT initially | source default locked until evidence-based change |
| `P_cap = 2.0` | STRUCTURAL_CONSTANT initially | source default locked until evidence-based change |
| `reference_minutes = 5` | STRUCTURAL_CONSTANT initially | TPS speed normalization definition |
| `wS=.35,wT=.25,wP=.20,wV=.20` | STRUCTURAL_CONSTANT in production; EXPERIMENT_TUNABLE only under approved experiment | initial TPS formula |
| directional-speed lookback 20 | STRUCTURAL_CONSTANT in production; EXPERIMENT_TUNABLE in approved experiment | exact Time/TP contract |
| recency weights 1..20 | STRUCTURAL_CONSTANT in production; EXPERIMENT_TUNABLE in approved experiment | exact directional-speed formula |

This classification prevents undocumented live tuning while allowing governed research/staging.

---

## 5. WHY PRODUCTION RANGES ARE NOT INVENTED

The intake sources provide initial constants but do not provide validated safe production bounds for changing them.

Therefore v3 MUST NOT invent arbitrary ranges merely to make an admin slider possible.

Production tunability may be added later only after:

- research/sensitivity evidence;
- explicit allowed range;
- interaction constraints;
- rollback rule;
- role permission;
- monitoring/failure trigger;
- canonical version update.

---

## 6. WEIGHT CONSTRAINT

Any approved experimental change to TPS weights must satisfy:

- each weight finite and non-negative;
- `wS + wT + wP + wV = 1.0` within defined numerical tolerance;
- experiment/version identity recorded;
- no silent normalization that hides an invalid submitted bundle unless the canonical control contract explicitly says normalization is allowed.

Production uses the active canonical bundle exactly.

---

## 7. CAP / SPEED-CONTRACT CHANGES

Changes to:

- S/T/P caps;
- ATR reference minutes;
- directional-speed lookback;
- recency weight function;
- flow-efficiency definition

can materially alter the model.

They are not normal owner UI knobs in v3.

Research/Autonomous Evolution may propose experiments; production adoption requires governed version promotion.

---

## 8. TPS LIFECYCLE THRESHOLDS

The source TPS bands are descriptive.

No production parameter such as:

- `tps_pre_threshold`;
- `tps_confirm_threshold`;
- `tps_open_threshold`

exists canonically merely because score bands exist.

Such thresholds require:

- explicit ALGO/FSM policy;
- replay/outcome evidence;
- allowed range;
- interaction with classical score;
- rollback and monitoring.

Until then, controls for them are forbidden.

---

## 9. LEARNED MODEL CONTROLS

The control plane may expose model state without changing learned internals.

Potential governed controls include:

- active model artifact selection from approved candidates;
- suspend model influence;
- set authority mode to recommend-only;
- approve a validated candidate for bounded use when separately authorized;
- rollback to previous approved model.

Every model control requires model id/version and audit evidence.

---

## 10. MODEL AUTHORITY MODES

Recognized control semantics may include:

- `DISABLED`
- `RECOMMEND_ONLY`
- `VALIDATED_ADVISORY`
- `BOUNDED_USE` only when separately authorized
- `SUSPENDED`

The exact shared enum must align with Trade Physics Intelligence and Admin/Role canon.

A control cannot raise model authority above its readiness/approval state.

---

## 11. READINESS IS NOT A USER-EDITABLE PARAMETER

Model readiness such as UNTRAINED/VALIDATED/SUSPENDED is derived/governed state.

An admin cannot simply set `VALIDATED` by editing a field.

Readiness transitions require evidence/process events defined by model/research/governance canon.

---

## 12. PARAMETER RECORD

Every mutable governed parameter/control must declare:

- parameter/control id;
- owner domain;
- type;
- current value;
- default;
- allowed range/set if mutable;
- units;
- validation rule;
- role permission;
- persistence behavior;
- audit requirement;
- rollback behavior;
- version/provenance;
- experiment-only marker if applicable.

---

## 13. VALIDATION ORDER

A control update must validate:

1. role/permission;
2. parameter classification;
3. environment/experiment scope;
4. type/finite values;
5. allowed range/set;
6. cross-parameter constraints;
7. strategy/version compatibility;
8. persistence/write success;
9. readback;
10. audit evidence.

Failure at any step must not leave an ambiguous partial configuration.

---

## 14. EXPERIMENTAL BUNDLES

Trade Physics experimental values should be applied as versioned bundles linked to an experiment, not scattered ad hoc edits.

Bundle metadata includes:

- experiment id;
- parent canonical/default bundle;
- changed values;
- created/approved by;
- start/end window;
- success/failure criteria;
- rollback target.

Production and experimental bundles must be distinguishable.

---

## 15. PERSISTENCE

Mutable settings must use the canonical configuration/state mechanism defined by system architecture.

No hidden in-memory-only Trade Physics setting may appear active when it will disappear on restart.

Persistence must be atomic enough to prevent mixed weight bundles or partial model authority changes.

---

## 16. AUDIT

Every material change must record:

- who/what requested it;
- old value/state;
- new value/state;
- timestamp;
- environment;
- experiment/change id;
- validation result;
- resulting version/reference;
- rollback target.

AI recommendation and human approval must remain distinguishable events.

---

## 17. ROLLBACK

A change is not safely controllable without rollback.

Trade Physics rollback may restore:

- previous approved parameter bundle;
- previous model artifact;
- recommend-only authority;
- disabled model influence;
- canonical deterministic constants.

Rollback must not erase audit history.

---

## 18. FAILURE BEHAVIOR

On invalid/missing settings or failed model control:

- do not guess values;
- preserve last known valid governed state where safe;
- otherwise fail closed to canonical deterministic behavior;
- expose the failure;
- avoid partial mixed bundles.

---

## 19. OWNER / ROLE BOUNDARY

Owner remains final authority for material production strategy changes.

Admin roles may operate only controls granted by Role/Permission canon.

The existence of an Admin UI field must not imply permission.

---

## 20. AI / AUTONOMOUS EVOLUTION BOUNDARY

AI/Autonomous Evolution may propose parameter/model changes.

It may not bypass:

- classification;
- experimental scope;
- role approval;
- safe bounds;
- versioning;
- rollback;
- audit.

Where no production range exists, the AI may only propose a governed research/canonical change.

---

## 21. FORBIDDEN PATTERNS

Forbidden:

- arbitrary sliders for structural TPS constants;
- hidden environment variables changing TPS math outside canon;
- auto-normalizing invalid weights without audit;
- user-editable model readiness;
- model authority above readiness;
- production parameter change from AI recommendation without approval;
- partial bundle persistence;
- undeclared TPS lifecycle thresholds;
- changing formula semantics under same version.

---

## 22. VALIDATION REQUIREMENTS

At minimum:

1. derived fields cannot be edited;
2. structural constants cannot be changed through ordinary production control;
3. experimental bundle is isolated from production;
4. weight-sum constraint enforced;
5. model authority cannot exceed readiness;
6. invalid update leaves prior valid state intact;
7. persistence survives restart;
8. audit captures old/new/actor/reason;
9. rollback restores exact prior bundle/model state;
10. AI recommendation alone cannot write production.

---

## 23. FINAL PRINCIPLE

Trade Physics can evolve, but its mathematics must never become a collection of invisible knobs.

The control plane distinguishes:

**derived truth, structural constants, experimental parameters, production parameters and model authority.**

Only values explicitly governed as mutable may be changed, and every change remains attributable and reversible.
