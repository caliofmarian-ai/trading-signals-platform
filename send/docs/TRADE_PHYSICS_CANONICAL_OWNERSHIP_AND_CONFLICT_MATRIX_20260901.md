# TRADE_PHYSICS_CANONICAL_OWNERSHIP_AND_CONFLICT_MATRIX_20260901

Status: GOVERNANCE SUPPORTING AUDIT — OWNER DIRECTION APPROVED, NOT ACTIVE CANON
Date: 2026-09-01
Change ID: 20260901-TRADE-PHYSICS-01

## 1. PURPOSE

This matrix maps the complete Trade Physics intake family into the current canonical authority graph and records the conflicts that must be resolved before implementation.

Source documents:

- `send/docs/intake/AI_TRADE_PHYSICS_SPACE_MODEL_SPEC.md`
- `send/docs/intake/TRADE_PHYSICS_SCORE_SPEC.md`
- `send/docs/intake/AI_TRADE_PHYSICS_INTELLIGENCE_SPEC.md`

The Owner has directed that Trade Physics be integrated into the current governed strategy rather than retained as future-state material.

This matrix does not itself activate any formula or runtime behavior.

## 2. CORE ARCHITECTURAL DECISION

Trade Physics must not create a parallel strategy pipeline.

The active architecture remains:

`MARKET DATA -> MARKET MODEL -> SR / CORRIDOR ENGINE -> TIME MODEL -> SCORING MODEL -> DECISION OBJECT -> FSM -> SIGNAL ENGINE`

Trade Physics is integrated primarily as a governed scoring/physical-feasibility submodel that consumes already-owned structural, temporal, flow and volatility evidence.

No Trade Physics component may bypass `DecisionObject`, FSM, signal-engine governance or observability.

## 3. SOURCE-TO-AUTHORITY MATRIX

| Trade Physics concept | Source intake document(s) | Canonical owner | Secondary consumers | Required action |
|---|---|---|---|---|
| nearest directional structural barrier | Space Model | SR_CORRIDOR_ENGINE_SPEC | ALGO, DecisionObject | make directional barrier/available-space semantics explicit if not already precise enough |
| `available_space` | Space Model, TPS Score | SR_CORRIDOR_ENGINE_SPEC | ALGO, DecisionObject, Analytics | define exact directional structural-space contract and units |
| `required_space` | Space Model, TPS Score | ALGO_SPEC / scoring contract using canonical `buffer_distance` input | DecisionObject, Analytics | replace legacy ambiguity; do not establish a second buffer authority |
| `space_to_buffer_ratio` | Space Model, TPS Score, AI Intelligence reachability S | ALGO_SPEC Trade Physics scoring submodel | DecisionObject, Audit, Analytics | canonicalize formula and edge-case behavior |
| `trade_space_margin_atr` | Space Model, TPS Score | ALGO_SPEC Trade Physics scoring submodel | DecisionObject, Audit, Analytics | canonicalize formula, ATR validity and units |
| structural compression / boundary proximity | Space Model concept + active corridor canon | SR_CORRIDOR_ENGINE_SPEC | ALGO, DecisionObject | map to stable structural semantics |
| ATR / volatility state | Space Model, TPS Score, AI Intelligence | existing market/strategy volatility truth | ALGO Trade Physics submodel | reuse existing source; no duplicate ATR computation authority |
| `buffer_distance` | AI Intelligence E; Space/Score legacy `buffer_price` | TIME_MODEL_UNIFIED_CANON / ALGO vocabulary | Trade Physics scoring | use canonical `buffer_distance`; legacy `buffer_price` only compatibility where explicitly mapped |
| E: buffer-ATR efficiency | AI Intelligence | ALGO Trade Physics scoring submodel | DecisionObject, Analytics, AI | define canonical orientation and naming; avoid duplicated V/movement-stress semantics |
| `t_needed` | AI Intelligence | TIME_MODEL_UNIFIED_CANON | ALGO / TPS | reuse canonical time math |
| `t_needed_adjusted` | TPS Score legacy spelling and active time canon | TIME_MODEL_UNIFIED_CANON | ALGO / TPS | canonical active spelling and semantics win |
| `model_expiry` | active time canon, conceptually intake time availability | TIME_MODEL_UNIFIED_CANON | ALGO / TPS | use active model time; do not introduce generic `expiry_minutes` as primary truth |
| time feasibility ratio | TPS Score, AI Intelligence T | TIME_MODEL_UNIFIED_CANON owns time metric; ALGO maps it into TPS component | DecisionObject, Analytics | reconcile direction: active `model_time_reach_ratio = t_needed_adjusted / model_expiry`; intake uses available/needed. One canonical conversion must be explicit |
| `directional_effective_speed` | AI Intelligence | Market/strategy derivation defined through ALGO and time inputs | Time Model, TPS | define exact formula, recency weights, direction handling, minimum evidence and noise treatment |
| gross speed | AI Intelligence flow efficiency | ALGO/market context contract | TPS, Analytics | define source and zero/invalid behavior |
| `flow_efficiency` | AI Intelligence | ALGO Trade Physics submodel | DecisionObject, Analytics, AI | canonicalize formula and range |
| momentum alignment factor F | AI Intelligence | ALGO scoring semantics | TPS/learned probability | decide whether F is deterministic TPS input, learned feature, or both with one source value |
| S normalized space component | TPS Score | ALGO Trade Physics scoring submodel | DecisionObject | canonicalize cap and clipping behavior |
| T normalized time component | TPS Score | ALGO Trade Physics scoring submodel consuming Time Model | DecisionObject | derive from active time vocabulary, not a parallel expiry formula |
| P normalized speed component | TPS Score | ALGO Trade Physics scoring submodel | DecisionObject | canonicalize ATR speed reference and cap |
| V volatility efficiency | TPS Score | ALGO Trade Physics scoring submodel | DecisionObject | reconcile with E and movement stress; avoid two opposite metrics without explicit naming |
| deterministic `TPS` 0–100 | TPS Score | ALGO_SPEC | DecisionObject, FSM input context, Audit, Analytics | proposed canonical deterministic Trade Physics Score |
| deterministic TPS weights/caps | TPS Score | ALGO structural defaults; Strategy Parameter Control only after ranges are canonically authorized | Admin/Analytics | initial values must be canonical defaults; tunability requires bounded parameter contract |
| TPS interpretation bands | TPS Score | ALGO_SPEC | DecisionObject, Audit | must be approved as decision semantics, not copied blindly as probability claims |
| sigmoid formula currently also named TPS | AI Intelligence | MUST NOT retain same field name as deterministic TPS | Strategy Intelligence / Research | rename/redefine as learned probability/calibration output after evidence validation |
| `trade_success_probability` | AI Intelligence | STRATEGY_INTELLIGENCE_SYSTEM + Research/Learning model contract | ALGO only when separately authorized for influence | explicit learned-output identity, model version, feature version and readiness required |
| Trade Physics feature dataset | all three | PERFORMANCE_ANALYTICS + RESEARCH_AND_LEARNING | Strategy Intelligence / model training | define truth labels, lineage, nullability, version, outcome target and leakage controls |
| model training (LightGBM/XGBoost candidates) | AI Intelligence | RESEARCH_AND_LEARNING / STRATEGY_INTELLIGENCE | Autonomous Evolution | algorithm choice is implementation/research choice unless canon explicitly locks one; no fabricated trained model |
| calibration engine | AI Intelligence | STRATEGY_INTELLIGENCE_SYSTEM / AUTONOMOUS_STRATEGY_EVOLUTION_SYSTEM | Admin/Governance | implement current architecture but gate authority by readiness/evidence |
| parameter recommendations | AI Intelligence | AUTONOMOUS_STRATEGY_EVOLUTION_SYSTEM | Owner/Admin | recommendation-only by default; governed approval path mandatory |
| bounded auto-adjust | AI Intelligence | Autonomous Evolution + Governance + Parameter Control | Engine | not allowed until separately authorized bounds/readiness are active canon |
| DecisionObject Trade Physics evidence | all three | DECISION_OBJECT_CANONICAL_SPEC | FSM, Audit, Observability | add explicit physical-feasibility domain or recognized score subdomain |
| decision audit fields | TPS Score | DECISION_AUDIT_SPEC | Analytics/Research | record primitive values, components, TPS and reason semantics |
| observability/event fields | all three | OBSERVABILITY + EVENT_SCHEMA | Analytics/Research | schema-versioned fields/events; no opaque debug-only truth |
| post-outcome calibration linkage | AI Intelligence | OUTCOME_TRACKING + TELEMETRY + PERFORMANCE_ANALYTICS | Research/AI | stable signal/setup identity and truth-layer labels required |

## 4. MATERIAL CONFLICTS THAT BLOCK CODE

### C-01 — Two incompatible TPS definitions

`TRADE_PHYSICS_SCORE_SPEC.md` defines deterministic TPS on `[0,100]` through weighted normalized S/T/P/V components.

`AI_TRADE_PHYSICS_INTELLIGENCE_SPEC.md` defines a sigmoid TPS on `[0,1]` through E/S/T/F.

Resolution direction:

- reserve `TPS` for the deterministic `[0,100]` Trade Physics Score;
- rename the learned/sigmoid output to a distinct probability field;
- no runtime code may implement two meanings under `TPS`.

### C-02 — Opposite time-ratio orientation

The intake TPS document uses conceptually:

`time_to_buffer_ratio = expiry / t_needed`

while the active unified time canon defines:

`model_time_reach_ratio = t_needed_adjusted / model_expiry`

These ratios move in opposite directions.

Resolution direction:

- Time Model remains authoritative;
- Trade Physics may derive a normalized time component from the active canonical ratio, but the conversion must be explicit and tested;
- no duplicate time authority is allowed.

### C-03 — Legacy `buffer_price` vs active `buffer_distance`

The intake Space/TPS documents use `buffer_price` in places.

Active ALGO/Time canon explicitly treats `buffer_distance` as primary vocabulary.

Resolution direction:

- `buffer_distance` is canonical;
- `buffer_price` is only an explicitly mapped compatibility alias where unavoidable.

### C-04 — E vs V/movement-stress duplication

AI Intelligence defines E as buffer distance divided by ATR.

TPS Score defines movement stress as required space divided by ATR and V as `1/(1+movement_stress)`.

These are strongly related and may become mathematical duplicates if `required_space == buffer_distance`.

Resolution direction:

- define one primitive movement-stress/energy ratio;
- define any transformed efficiency component explicitly from that primitive;
- do not double-count mathematically equivalent evidence in TPS.

### C-05 — Directional speed lacks exact canonical algorithm

AI Intelligence says directional speed is recency-weighted, directional and noise-filtered but does not lock exact weights, sample horizon, missing-data behavior or noise filter.

Resolution direction:

- exact deterministic algorithm must be specified before code;
- no guessed weights or hardcoded arbitrary smoothing are allowed.

### C-06 — TPS probability wording is stronger than current evidence

The intake documents describe TPS as probability or physical probability of completion, but no calibration evidence is contained in the source documents proving that deterministic TPS numerically equals empirical probability.

Resolution direction:

- deterministic TPS is a physical-feasibility score unless and until calibration evidence supports probability semantics;
- learned/calibrated probability must remain separately named and evidence-governed.

### C-07 — Decision influence conflict

The TPS Score intake document says TPS is complementary and does not immediately replace the current strategy score.

The AI Intelligence intake document maps its sigmoid TPS directly to reject/watchlist/focus/open-candidate bands.

Resolution direction:

- the successor ALGO spec must explicitly define current TPS influence;
- no hidden or implicit combination with the existing score is allowed;
- replay/validation must quantify double-counting and signal-volume effects before production activation.

### C-08 — AI implementation timing overridden by Owner

The AI Intelligence intake source states implementation should begin after prior strategy stabilization / STEP 100.

The Owner decision on 2026-09-01 explicitly brings the Trade Physics family into current project scope.

Resolution direction:

- architecture, datasets, telemetry, deterministic physics scoring, readiness states and calibration interfaces are current-scope;
- statistical authority still requires real evidence and cannot be fabricated;
- the prior future-timing statement must be superseded in canonical successors.

## 5. PROPOSED CANONICAL SHAPE

### 5.1 Strategy-critical deterministic path

Proposed conceptual path without creating a new top-level pipeline layer:

`Market Model evidence`

+ `SR/Corridor structural evidence`

+ `Time Model evidence`

-> `Trade Physics component derivation inside governed scoring`

-> `Deterministic TPS + component evidence`

-> `combined strategic scoring/gating semantics defined by ALGO`

-> `DecisionObject`

-> `FSM`

The exact relation between classical strategy score and TPS must be defined in the successor ALGO canon.

### 5.2 Intelligence / learning path

`DecisionObject + Trade Physics evidence`

-> `Telemetry + Outcome Truth`

-> `Performance Analytics dataset`

-> `Research/Learning`

-> `Trade Physics learned probability / calibration`

-> `Strategy Intelligence`

-> `Autonomous Evolution recommendation`

-> `Owner/Admin governed approval`

No learned output may bypass this authority chain.

## 6. EXPECTED CANONICAL SUCCESSORS

Final SemVer requires full audit. Based on current evidence:

### Structural successor candidates

Likely structural changes requiring MAJOR version review:

- `ALGO_SPEC`
- `DECISION_OBJECT_CANONICAL_SPEC`
- `SR_CORRIDOR_ENGINE_SPEC` if exact available-space contract materially expands current output contract
- `TIME_MODEL_UNIFIED_CANON` if directional speed/time normalization contracts materially change
- `STRATEGY_INTELLIGENCE_SYSTEM`
- `RESEARCH_AND_LEARNING_FRAMEWORK_SPEC`
- `PERFORMANCE_ANALYTICS_SPEC`
- `EVENT_SCHEMA_SPEC` if new required contract fields/events are added
- `MODULE_INTERFACE_SPEC`

### Potential bounded/reference successors

Depending on final audit:

- `DECISION_AUDIT_SPEC`
- `OBSERVABILITY_SPEC`
- `OBSERVABILITY_LOGGING_SPEC`
- `OUTCOME_TRACKING_SPEC`
- `TRADE_TEMPORAL_TELEMETRY_SPEC`
- `AUTONOMOUS_STRATEGY_EVOLUTION_SYSTEM`
- `STRATEGY_PARAMETER_CONTROL_SPEC`
- `SYSTEM_ARCHITECTURE_MAP`
- `SYSTEM_INVARIANTS`
- `CANONICAL_STRATEGY_STACK`
- `CANONICAL_MASTER_INDEX`
- `CANON_BATCH_EVALUATION` / governed replacement record

No version is assigned by this matrix alone.

## 7. CODE AUTHORIZATION STATUS

Code authorization: BLOCKED.

Reason:

- formula conflicts remain unresolved canonically;
- current active batch classification still calls Trade Physics future/outside-active;
- exact TPS influence on strategy is not yet authoritative;
- exact directional effective speed algorithm is not authoritative;
- event and DecisionObject contracts are not yet promoted.

The next valid work is complete canonical successor drafting and review.

## 8. FINAL AUDIT STATEMENT

The Owner decision is technically integrable without replacing the current architecture.

Trade Physics should become a current governed strategy submodel plus a current governed intelligence/calibration subsystem.

The intake documents are valuable source material, but they cannot be copied verbatim into runtime because they contain:

- duplicated formulas;
- conflicting score ranges;
- opposite ratio orientation;
- legacy vocabulary;
- future-timing assumptions now overridden by Owner;
- probabilistic claims that require calibration evidence.

The canonical integration must preserve all valuable concepts while resolving these conflicts into one self-consistent authority graph before code changes.
