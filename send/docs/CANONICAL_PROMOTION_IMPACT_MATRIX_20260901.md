# CANONICAL_PROMOTION_IMPACT_MATRIX_20260901

Status: SUPPORTING GOVERNANCE / PROMOTION PREFLIGHT — NOT CANONICAL AUTHORITY  
Date: 2026-09-01  
Programs:
- staged SignalEvent execution / post-FSM observability remediation;
- current-scope complete Trade Physics integration.

Owner-approved governance sources:
- merged proposal PR #77;
- merged Trade Physics governance PR #78.

## 1. Purpose

This matrix defines the minimum documentation blast radius that must be resolved before the combined proposed canonical successor set may be promoted into `canonical/active`.

It does not authorize runtime code changes, Distribution activation, Telegram publication, outcome creation, broker execution, or scan-cadence changes.

PR #73 remains blocked.

## 2. Structural successor set

The combined program requires the following structural successor versions:

| Current active authority | Proposed successor | Classification / reason |
|---|---|---|
| `CANONICAL_STRATEGY_STACK_v1.0.0.md` | `CANONICAL_STRATEGY_STACK_v2.0.0.md` | MAJOR — root flow, Trade Physics authority, exact FSM execution handoff |
| `CANONICAL_MASTER_INDEX_v1.0.0.md` | `CANONICAL_MASTER_INDEX_v2.0.0.md` | MAJOR — authority inventory grows 41 -> 43 and versions change |
| `ALGO_SPEC_v2.0.0.md` | `ALGO_SPEC_v3.0.0.md` | MAJOR — current-scope deterministic Trade Physics integrated into scoring/strategy |
| `SR_CORRIDOR_ENGINE_SPEC_v2.0.0.md` | `SR_CORRIDOR_ENGINE_SPEC_v3.0.0.md` | MAJOR — directional structural-space contract becomes explicit Trade Physics input |
| `TIME_MODEL_UNIFIED_CANON_v2.0.0.md` | `TIME_MODEL_UNIFIED_CANON_v3.0.0.md` | MAJOR — directional effective speed / Trade Physics time relation |
| new | `TRADE_PHYSICS_MODEL_SPEC_v1.0.0.md` | NEW ROOT DOMAIN — deterministic S/T/P/V and TPS authority |
| `DECISION_OBJECT_CANONICAL_SPEC_v1.0.0.md` | `DECISION_OBJECT_CANONICAL_SPEC_v2.0.0.md` | MAJOR — Trade Physics + optional learned prediction become first-class pre-FSM domains |
| `FSM_DECISION_ENGINE_SPEC_v1.0.0.md` | `FSM_DECISION_ENGINE_SPEC_v2.0.0.md` | MAJOR — exact-stage operational handoff/readiness |
| `SIGNAL_ENGINE_EXECUTION_SPEC_v2.0.0.md` | `SIGNAL_ENGINE_EXECUTION_SPEC_v3.0.0.md` | MAJOR — staged candidates/execution truth + explicit no-TPS-recompute boundary |
| `OBSERVABILITY_SPEC_v2.0.0.md` | `OBSERVABILITY_SPEC_v3.0.0.md` | MAJOR — first-class execution truth + Trade Physics/model observability |
| `OBSERVABILITY_LOGGING_SPEC_v2.0.0.md` | `OBSERVABILITY_LOGGING_SPEC_v3.0.0.md` | MAJOR — execution/Trade Physics/model lineage logging |
| `EVENT_SCHEMA_SPEC_v2.0.0.md` | `EVENT_SCHEMA_SPEC_v3.0.0.md` | MAJOR — signal_execution_result + Trade Physics/probability schema separation |
| `DECISION_AUDIT_SPEC_v2.0.0.md` | `DECISION_AUDIT_SPEC_v3.0.0.md` | MAJOR — Trade Physics decision audit + lifecycle order repair |
| `TRADE_TEMPORAL_TELEMETRY_SPEC_v2.0.0.md` | `TRADE_TEMPORAL_TELEMETRY_SPEC_v3.0.0.md` | MAJOR — immutable TP snapshot, feature/label provenance, ML anti-leakage |
| `OUTCOME_TRACKING_SPEC_v2.0.0.md` | `OUTCOME_TRACKING_SPEC_v3.0.0.md` | MAJOR — operational labels vs market-label lineage for Trade Physics/ML |
| `PERFORMANCE_ANALYTICS_SPEC_v2.0.0.md` | `PERFORMANCE_ANALYTICS_SPEC_v3.0.0.md` | MAJOR — TPS/model calibration analytics become current-scope |
| `RESEARCH_AND_LEARNING_FRAMEWORK_SPEC_v2.0.0.md` | `RESEARCH_AND_LEARNING_FRAMEWORK_SPEC_v3.0.0.md` | MAJOR — Trade Physics/model hypothesis/experiment governance |
| new | `TRADE_PHYSICS_INTELLIGENCE_SPEC_v1.0.0.md` | NEW DOMAIN — dataset/model/calibration/readiness authority |
| `STRATEGY_INTELLIGENCE_SYSTEM_v2.0.0.md` | `STRATEGY_INTELLIGENCE_SYSTEM_v3.0.0.md` | MAJOR — current-scope TP intelligence integration |
| `AUTONOMOUS_STRATEGY_EVOLUTION_SYSTEM_v2.0.0.md` | `AUTONOMOUS_STRATEGY_EVOLUTION_SYSTEM_v3.0.0.md` | MAJOR — TP/model evolution recommendations/readiness |
| `STRATEGY_PARAMETER_CONTROL_SPEC_v2.0.0.md` | `STRATEGY_PARAMETER_CONTROL_SPEC_v3.0.0.md` | MAJOR — TP structural-vs-tunable parameter boundary |
| `MODULE_INTERFACE_SPEC_v2.0.0.md` | `MODULE_INTERFACE_SPEC_v3.0.0.md` | MAJOR — explicit FSM handoff + Trade Physics shared contracts/ownership |
| `CANON_BATCH_EVALUATION_v2.0.0.md` | `CANON_BATCH_EVALUATION_v3.0.0.md` | MAJOR GOVERNANCE RECORD — Trade Physics future-state verdict reversed by Owner |

## 3. New Trade Physics semantic locks

All promoted successors must agree on:

### Deterministic identity
- `TPS` is deterministic and bounded `[0,100]`.
- formula: `100 * (0.35*S + 0.25*T + 0.20*P + 0.20*V)`.
- formula/feature version must be traceable.

### Structural evidence
- `available_space` is directional space to the relevant SR barrier.
- `required_space` uses canonical `buffer_distance` semantics.
- `space_to_buffer_ratio = available_space / required_space`.
- `trade_space_margin_atr = (available_space-required_space)/atr_m5`.

### Time evidence
- `model_time_reach_ratio = t_needed_adjusted / model_expiry`.
- `time_to_buffer_ratio = model_expiry / t_needed_adjusted` when valid.
- orientation must never be ambiguous.
- `directional_effective_speed` is distinct from gross/absolute price activity.

### TPS components
- `S = min(space_to_buffer_ratio,3)/3`.
- `T = min(time_to_buffer_ratio,2)/2`.
- `atr_speed_reference = atr_m5 / 5` baseline.
- `directional_speed_ratio = directional_effective_speed / atr_speed_reference`.
- `P = min(directional_speed_ratio,2)/2`.
- `movement_stress = required_space / atr_m5`.
- `V = 1/(1+movement_stress)`.

### Learned probability
- `trade_success_probability` is learned/calibrated `[0,1]`.
- it is not TPS.
- it requires model/version/calibration/readiness metadata.
- no validated model -> no fabricated probability.

### Ownership
- SR owns structural-space derivation.
- Time owns time/speed semantics.
- Scoring/Trade Physics owns deterministic TPS.
- DecisionObject carries strategic snapshot.
- FSM does not recompute TPS.
- Signal Engine does not recompute TPS.
- Telemetry preserves feature/label lineage.
- Trade Physics Intelligence owns learned model lifecycle.

## 4. Staged-execution semantic locks

All promoted successors must also agree on:
- `requested_stage`;
- `accepted_stage`;
- `stage_handoff_ready`;
- `trade_execution_ready`;
- `execution_attempt_id`;
- `execution_phase`;
- `execution_outcome`;
- `execution_reason`;
- `signal_event_available`;
- `destination_state`;
- `PRE_DISTRIBUTION_UNRESOLVED`;
- `signal_execution_result`.

Readiness:
- PRE handoff-ready may be true; trade-ready false.
- CONFIRM handoff-ready may be true; trade-ready false.
- OPEN_NOW may have both true only after valid lifecycle acceptance.

Execution:
- SignalEvent construction is not Distribution authorization.
- SignalEvent construction is not EMITTED.
- valid SignalEvent + Distribution intentionally not invoked = DEFERRED/PRE_DISTRIBUTION.
- EMITTED requires downstream successful publication evidence.

## 5. Trade Physics source absorption

The three original Intake sources are fully covered by:

`TRADE_PHYSICS_INTAKE_SOURCE_ABSORPTION_LEDGER_v1.0.0.md`

Sources:
- `AI_TRADE_PHYSICS_SPACE_MODEL_SPEC.md`
- `TRADE_PHYSICS_SCORE_SPEC.md`
- `AI_TRADE_PHYSICS_INTELLIGENCE_SPEC.md`

After promotion they remain historical Intake/provenance, not active authority.

## 6. Reference-only active consumers inherited from staged-execution preflight

Exact-filename scans performed in the staged-execution preflight identified active consumers requiring contextual re-evaluation during final promotion, including:

- `RISK_MODEL_v2.0.0.md`
- `DEPLOYMENT_PROTOCOL_v2.0.0.md`
- `SYSTEM_ARCHITECTURE_MAP_v2.0.0.md`
- `SIGNAL_ECONOMICS_AND_MONETIZATION_MODEL_v2.0.0.md`
- `GOVERNANCE_AND_CHANGE_CONTROL_v2.0.0.md`
- `SIGNAL_DISTRIBUTION_ARCHITECTURE_v2.0.0.md`
- `SIGNAL_DISTRIBUTION_SPEC_v2.0.0.md`
- `AFFILIATE_SIGNAL_DISTRIBUTION_MODEL_v2.0.0.md`
- `ADMIN_TREE_MAP_v2.0.0.md`
- `TELEGRAM_UX_v2.0.0.md`
- `SECURITY_MODEL_v2.0.0.md`
- `SYSTEM_INVARIANTS_v2.0.0.md`
- `HUMAN_COMPREHENSION_AND_SELF_EXPLAINING_CONTROL_SURFACE_CANON_v1.0.0.md`

Some previous “reference-only” consumers are no longer reference-only because Trade Physics now gives them full structural successors (ALGO, SR, Time, DecisionObject, Outcome, Strategy Parameter Control, etc.).

## 7. Distribution wording compatibility

`SIGNAL_DISTRIBUTION_SPEC_v2.0.0.md` remains conceptually compatible with successful-publication semantics, but wording such as:

`For each emitted governed signal stage`

becomes ambiguous because EMITTED now means post-publication Signal Engine outcome.

Promotion-time PATCH clarification should use wording equivalent to:

`For each governed SignalEvent candidate released to distribution`

without altering route eligibility, silence state, entitlement counting, lifecycle stage policy or route ownership.

Its Observability Logging reference must also be updated.

## 8. Reference-only patch classification rule

For every active exact-filename match to a superseded authority:

- normative current cross-reference -> versioned reference-repair successor required;
- historical/version-history mention -> preserve/annotate, do not blindly replace;
- compatibility/migration mention -> preserve according to semantics;
- unrelated match -> no change.

A fresh exact-filename scan must be rerun immediately before promotion.

## 9. Intended post-promotion inventory

After promotion:
- 43 unique functional canonical specifications;
- 2 new Trade Physics functional authorities;
- one active version per domain;
- Master Index and Root Stack agree exactly;
- supporting governance records are not counted as functional authorities.

## 10. Runtime drift explicitly deferred until after promotion

Known runtime issues to re-audit after canonical activation include:
- TPS currently computed in/around `signal_engine.py` instead of strategy/scoring ownership;
- runtime TPS speed component uses a different reference than proposed Intake-aligned formula;
- current gross speed is not full directional effective speed;
- runtime event schema uses legacy/generic event names;
- PRE/CONFIRM exact-stage candidate handoff requires implementation alignment;
- post-FSM execution-result event implementation is incomplete/drifted.

No code correction is authorized by this matrix.

## 11. Promotion atomicity requirements

The eventual active-promotion PR must:
1. start from fresh current `main`;
2. rerun exact-filename scans for every superseded authority;
3. inspect every active match in context;
4. create reference-only PATCH successors only when actually required;
5. install every complete structural successor;
6. install the two new Trade Physics authorities;
7. move/preserve old versions under canonical superseded storage;
8. activate Root Stack v2 and Master Index v2 only after exact final filenames are known;
9. ensure 43 unique functional active specifications;
10. ensure no active normative reference points to superseded authority;
11. reclassify Trade Physics Intake material as historical source/provenance;
12. perform post-promotion canonical re-audit;
13. keep runtime code and `send/schema/event_schema.json` unchanged in the promotion PR.

## 12. Hard blockers

Promotion stops if:
- any active normative reference still points to a superseded authority;
- old/new versions both claim active authority;
- Root Stack and Master Index disagree;
- Event Schema/Logging/Observability disagree on field names or truth semantics;
- FSM and Signal Engine disagree on stage/readiness semantics;
- TPS formula or probability identity differs across active successors;
- Time ratio orientation differs across successors;
- Signal Engine is canonically allowed to recompute TPS;
- market and operational labels are conflated;
- model prediction can exist without validated model/readiness metadata;
- Distribution is implicitly activated;
- runtime code is mixed into docs-only promotion.

## 13. No-code / #73 rule

PR #73 remains on canonical hold until:
1. the complete proposed combined successor package is reviewed/merged;
2. active canonical promotion is completed atomically;
3. active canon is re-audited;
4. runtime code is audited against newly active truth;
5. only then are code remediations implemented/tested.

End of supporting impact matrix.
