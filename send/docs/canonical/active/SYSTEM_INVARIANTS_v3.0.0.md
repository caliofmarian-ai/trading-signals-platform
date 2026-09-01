# SYSTEM_INVARIANTS_v3.0.0

BinaryBot — Non-Negotiable System Invariants  
Version: 3.0.0  
Status: ACTIVE CANONICAL  
Owner: BinaryBot / DROPi Signals  
Supersedes: `SYSTEM_INVARIANTS_v2.0.0.md`  

Linked authorities:
- `CANONICAL_STRATEGY_STACK_v2.0.0.md`
- `SYSTEM_ARCHITECTURE_MAP_v3.0.0.md`
- `ALGO_SPEC_v3.0.0.md`
- `TRADE_PHYSICS_MODEL_SPEC_v1.0.0.md`
- `TRADE_PHYSICS_INTELLIGENCE_SPEC_v1.0.0.md`
- `DECISION_OBJECT_CANONICAL_SPEC_v2.0.0.md`
- `FSM_DECISION_ENGINE_SPEC_v2.0.0.md`
- `SIGNAL_ENGINE_EXECUTION_SPEC_v3.0.0.md`
- `EVENT_SCHEMA_SPEC_v3.0.0.md`
- `OBSERVABILITY_SPEC_v3.0.0.md`
- `TRADE_TEMPORAL_TELEMETRY_SPEC_v3.0.0.md`
- `OUTCOME_TRACKING_SPEC_v3.0.0.md`
- `TEST_PLAN_v3.0.0.md`
- Distribution, Governance, Security, Deployment, Failure Recovery and Human Comprehension authorities

---

## 0. Purpose

This document defines the absolute, non-negotiable truths of BinaryBot / DROPi Signals.

An invariant cannot be waived by:
- runtime convenience;
- admin action;
- recovery path;
- AI/model recommendation;
- analytics interpretation;
- deployment shortcut;
- legacy implementation;
- Intake wording.

If implementation and active canonical invariants conflict, implementation must be corrected after governed canonical authorization.

The v3 successor preserves the v2 safety set and adds explicit invariants for:
- current-scope deterministic Trade Physics;
- learned probability separation;
- exact FSM stage handoff;
- SignalEvent candidate vs delivery truth;
- model/data anti-leakage and readiness.

---

## 1. Interpretation rule

If a lower-level document, code path, operational playbook, model output or admin action conflicts with this document, this document wins unless a later promoted invariant successor explicitly changes the rule.

---

## 2. Philosophical / governance invariants

### INV-001 — Capital Protection First
No feature, model, tuning change, distribution expansion or operational shortcut may increase trade frequency at the expense of structural safety.

### INV-002 — Determinism
Given materially identical market inputs, strategy/formula versions, parameters, governed state and timing context, deterministic decision logic must produce materially identical outputs.

A learned model may produce deterministic inference for identical model/features, but it must never be confused with the deterministic TPS formula or introduce ungoverned randomness into canonical decision truth.

### INV-003 — Documentation Supremacy
If code and active canonical documentation conflict, active canon is reference truth and code must be corrected through governed implementation work.

### INV-004 — No Undocumented Change
Any material logic, model, data, governance, route, recovery, analytics or control change without canonical documentation alignment is a governance breach.

### INV-005 — No Emotional Tuning
Parameters, TPS interpretation, model thresholds or policy must not be changed from frustration, fear, euphoria, revenge tuning or anecdotal streak reaction.

---

## 3. Architecture-order invariants

### INV-010 — DecisionObject Before FSM
DecisionObject must be produced before FSM/state-transition handling.

### INV-011 — Corridor Engine Before Time Model
Structural/corridor truth must precede time-model interpretation.

### INV-012 — Route Governance Terminology Is Canonical
Active route/distribution terminology governs over legacy tier-only wording where migration has occurred.

### INV-013 — Scoring and Trade Physics Before DecisionObject
Classical score and deterministic Trade Physics for an evaluation must be finalized upstream of DecisionObject.

DecisionObject may carry their truth; it must not trigger their first hidden calculation downstream.

### INV-014 — Signal Engine Is Not a Strategy Engine
Signal Engine must not own or recompute market, corridor, time, classical score or deterministic Trade Physics mathematics.

### INV-015 — Distribution Is Downstream of Signal Engine
Distribution may act only on a canonical SignalEvent candidate released by Signal Engine after valid FSM handoff.

---

## 4. Decision / opportunity invariants

### INV-020 — Threshold Hierarchy
PRE ≤ CONFIRM ≤ OPEN_NOW for governed stage-threshold families.

### INV-021 — No OPEN_NOW Without PRE Path
OPEN_NOW must occur only through the canonical lifecycle path and not directly from discovery/IDLE-like context.

### INV-022 — OPEN_NOW Requires Valid Focus Qualification
A symbol may reach actionable OPEN_NOW only with valid focus/watchlist qualification where the lifecycle canon requires it.

### INV-023 — Buffer Reachability Required
OPEN_NOW is forbidden unless the required movement/buffer traversal remains realistically reachable.

### INV-024 — Expiry Feasibility Required
OPEN_NOW is forbidden unless expected movement remains feasible within canonical time constraints.

### INV-025 — Focus Context Governs Actionability
Wide scan may discover PRE; CONFIRM and OPEN_NOW require valid actionable focus/watchlist context under the current FSM rules.

### INV-026 — Same Opportunity Must Not Be Fully Recomputed On Every Tick
The same opportunity must not be treated as a new full candidate every scheduler tick unless material context changed.

### INV-027 — Decision Identity Must Be Stable
Opportunity identity must remain stable from canonical identity fields such as symbol, candle, direction and lifecycle context.

### INV-028 — Decision Freeze Window Required
A bounded freeze/dedup window must suppress redundant full evaluation where canonically configured.

### INV-029 — Material Context Change Reopens Evaluation
Reevaluation is allowed on material context change such as new candle, direction flip, focus state, significant strategic evidence change or stage-upgrade path.

### INV-030 — Rejection Evidence Must Exist
Material rejection must produce explicit reconstructable reason evidence.

### INV-031 — Deterministic TPS Has One Identity
`TPS` means exactly the deterministic Trade Physics score governed by `TRADE_PHYSICS_MODEL_SPEC` and is bounded `[0,100]`.

No second metric may use the TPS name with a different formula/range.

### INV-032 — Learned Probability Is Not TPS
`trade_success_probability` is a separate learned/calibrated probability `[0,1]` and must never be substituted for deterministic TPS.

### INV-033 — No Fabricated Learned Probability
If no validated model/readiness state authorizes a real prediction, learned probability must be absent/unknown, never filled with 0, 0.5, TPS-normalized or another invented proxy.

### INV-034 — Classical Score and TPS Remain Distinct
Classical score and deterministic TPS are separate strategic metrics unless a future promoted canonical formula explicitly combines them.

### INV-035 — TPS Band Is Not an Undocumented Stage Gate
Interpretation bands do not automatically alter PRE/CONFIRM/OPEN_NOW thresholds or FSM progression.

---

## 5. FSM / focus / watchlist invariants

### INV-040 — Max Watchlist Size
Watchlist size must remain ≤ 2 unless a later promoted invariant changes this hard limit.

### INV-041 — Focus Capacity Hard Limit
No more than 2 active focus/watchlist symbols; replacement must preserve capacity and auditability.

### INV-042 — No OPEN_NOW Outside Valid Focus Context
OPEN_NOW must not arise outside required valid focus/watchlist context.

### INV-043 — Cooldown Absolute Block
Cooldown blocks PRE/CONFIRM/OPEN_NOW release under the canonical lifecycle.

### INV-044 — Deterministic Focus Slot Release
Focus must release on canonical exit conditions; stuck focus is a breach.

### INV-045 — Focus Lease Mandatory
Focus/watchlist entry requires bounded lease/TTL/expiry semantics where governed.

### INV-046 — Forced Focus Eviction Outside Active Universe
A symbol outside the active universe must be evicted.

### INV-047 — Forced Focus Eviction On Lease Expiry
Expired focus must not remain resident by inertia.

### INV-048 — Watchlist Residency Must Match Operational Eligibility
Focus/watchlist residency requires continuing eligibility.

### INV-049 — Focus Must Not Fully Starve Wide Scan
Focus priority must not eliminate wide-scan coverage.

### INV-050 — Exact-Stage FSM Acceptance Required
PRE/CONFIRM/OPEN_NOW may be released to Signal Engine only when `accepted_stage` explicitly matches `requested_stage` and `stage_handoff_ready=true`.

A generic transition event or generic accepted boolean is insufficient.

### INV-051 — Stage Handoff and Trade Readiness Are Distinct
PRE/CONFIRM may be `stage_handoff_ready=true` while `trade_execution_ready=false`.
Only valid OPEN_NOW may be trade-execution ready.

### INV-052 — Blocker/No-Op Transition Is Not Stage Release
Cooldown, watchlist-full, duplicate, invalid-lifecycle or informational no-op transitions must not be interpreted as accepted-stage handoff.

---

## 6. Signal lifecycle / execution invariants

### INV-060 — One OPEN_NOW Per Symbol-Candle Opportunity
Only one OPEN_NOW may become externally visible for the same canonical symbol-candle opportunity.

### INV-061 — Signal Identity Stable Across Lifecycle
Same trade idea preserves stable `signal_id` across PRE/CONFIRM/OPEN_NOW, execution, distribution, telemetry and outcome linkage.

### INV-062 — No Hidden External Signal
No signal stage may become externally visible without corresponding structured observability/publication evidence.

### INV-063 — Telegram and Evidence Must Match
If Telegram/external surface shows a governed stage, corresponding decision/FSM/execution/distribution evidence must exist. Logs must not claim external visibility that did not occur.

### INV-064 — Signal Lifecycle Must Be Traceable
Every signal must have a reconstructable chain across decision, FSM, execution, distribution and downstream evidence where applicable.

### INV-065 — SignalEvent Candidate Is Not Delivery
Internal SignalEvent construction does not prove Distribution authorization, publication or external visibility.

### INV-066 — EMITTED Requires Successful Publication Evidence
Signal Engine outcome `EMITTED` requires linked downstream evidence that at least one authorized publication succeeded.

### INV-067 — Pre-Distribution Valid Candidate Is DEFERRED When Distribution Is Intentionally Not Invoked
A valid SignalEvent candidate while Distribution is intentionally disabled/not invoked must be classified `DEFERRED`/PRE_DISTRIBUTION, not EMITTED or FAILED.

### INV-068 — Signal Engine Must Not Recompute TPS
The deterministic Trade Physics snapshot consumed downstream must originate upstream of DecisionObject. Signal Engine may carry/reference it only.

---

## 7. Risk / actionability / Trade Physics invariants

### INV-070 — SR Space Must Exceed Required Buffer
If directional structural space is smaller than required canonical movement distance, actionability must be rejected/blocked as defined by strategy canon.

### INV-071 — Feasibility Must Hold
If required movement time exceeds available model time under canonical ratio semantics, actionability must fail.

### INV-072 — Spike / Instability Active Blocks Trade
Canonical instability/spike gate blocks actionability unless a later canonical exception is explicitly defined.

### INV-073 — Timing Decay Cannot Be Ignored
Stale prior feasibility cannot preserve actionability after timing becomes infeasible.

### INV-074 — Trade Physics Uses Directional Structural Space
`available_space` must represent direction-relevant structural room; opposite-side or arbitrary corridor width must not silently substitute.

### INV-075 — Time-Ratio Orientation Must Be Explicit
`model_time_reach_ratio = t_needed_adjusted/model_expiry`; `time_to_buffer_ratio = model_expiry/t_needed_adjusted` when valid. They must not be silently interchanged.

### INV-076 — Directional Effective Speed Must Not Be Replaced Silently By Gross Speed
When Trade Physics/Time canon requires `directional_effective_speed`, gross absolute movement speed cannot silently substitute without explicit degraded/compatibility semantics.

### INV-077 — Trade Physics Formula Must Be Versioned
S/T/P/V formulas, weights/caps and deterministic TPS meaning must have reproducible formula/version identity.

---

## 8. Parameter / version invariants

### INV-080 — No Hardcoded Adjustable Constants
Operationally adjustable thresholds/parameters must be governed configuration, not hidden constants.

Structural formula constants may be code literals only if they exactly implement an active versioned canonical formula and are not misrepresented as runtime-tunable.

### INV-081 — Version Must Match Behavior
Displayed/emitted algorithm, formula, schema and model versions must reflect materially deployed behavior.

### INV-082 — Material Parameter Change Requires Version Discipline
Material thresholds, multipliers, timing, route-affecting or gate-policy changes require governed version/change evidence.

### INV-083 — Structural Formula Is Not Ordinary Live Parameter
TPS formula shape, deterministic-vs-learned identity and feature semantics cannot be changed through ordinary admin tuning unless active canon explicitly makes them tunable.

### INV-084 — Model Version and Readiness Must Travel With Prediction
A learned probability without model/version/calibration/readiness metadata has no canonical standing.

---

## 9. Observability / schema / lineage invariants

### INV-090 — Every Externally Material Signal Stage Must Be Logged
Material PRE/CONFIRM/OPEN_NOW external visibility must have required structured evidence.

### INV-091 — Errors Must Never Be Silent
Material exceptions/faults require observable evidence.

### INV-092 — Log Format Must Follow Canonical Event Schema
Structured events must follow active Event Schema semantics.

### INV-093 — Governed State Mutation Must Be Observable
Route, counter, permission, parameter, model-readiness, recovery or other governed mutation must not occur silently.

### INV-094 — If It Is Not Logged, It Did Not Happen
For governance-grade interpretation, unlogged material action lacks canonical evidentiary standing.

### INV-095 — Trade Physics Snapshot Must Be Reproducible
Decision/telemetry evidence used for TP analytics/modeling must preserve formula/feature version sufficient to reproduce meaning.

### INV-096 — Learned Prediction Must Be Identifiable Separately
Event/log schema must not store deterministic TPS and learned probability under an ambiguous shared field.

### INV-097 — No Future-Label Leakage Into Pre-Trade Features
Post-decision/expiry/outcome evidence must not enter pre-trade feature vectors used to train/infer a pre-trade probability model.

---

## 10. Distribution / route governance invariants

### INV-100 — Route Limits Must Be Enforced
Governed distribution enforces route limits/state rules.

### INV-101 — SILENT Route Blocks All Stages
SILENT blocks PRE/CONFIRM/OPEN_NOW publication on that route.

### INV-102 — Unlimited Route Must Not Be Improperly Limited
Unrestricted routes must not consume/apply limited-route counters contrary to policy.

### INV-103 — Reset Exactly Once Per Canonical Boundary
Route reset occurs exactly once per defined boundary.

### INV-104 — Counter Consumption Requires Successful Governed Publication
Entitlement/counter consumption occurs only on successful publication under distribution policy.

### INV-105 — Duplicate Suppression Must Be Visible
Route duplicate suppression must be observable.

### INV-106 — Distribution Must Not Recompute Strategic Validity
Distribution consumes a governed SignalEvent candidate and may not reconstruct classical score/TPS from raw market data to decide validity.

---

## 11. Outcome / reconciliation invariants

### INV-110 — One Outcome Submission Per User Per Signal
Where user outcome submission is governed, one submission per eligible user/signal remains baseline unless later canon defines supersession.

### INV-111 — Outcome Window Limited
Outcome interaction is bounded by canonical eligibility window.

### INV-112 — Outcome UI Expires
Outcome UI becomes non-actionable after eligibility window.

### INV-113 — Outcome History Preserved
Canonical outcome evidence must preserve append/history semantics; corrections cannot erase prior evidence.

### INV-114 — Multi-Truth Reconciliation Must Not Collapse Evidence Sources
Market telemetry, operational/admin outcomes and user-reported truth remain distinct.

### INV-115 — MISSED Is Not Market LOSS
Operational MISSED must not be silently used as objective market LOSS.

---

## 12. Performance / analytics / model invariants

### INV-120 — No Drift Without Detection
Material performance/model drift beyond governed tolerance requires anomaly/review evidence.

### INV-121 — No Frequency Explosion Without Causal Explanation
Major signal-frequency change requires documented causal/version basis.

### INV-122 — Analytics Must Not Invent Missing Truth
Unknown/missing evidence cannot be fabricated or silently coerced into normal values.

### INV-123 — TPS Calibration Must Be Measured, Not Assumed
TPS bands or predictive interpretation must be validated against objective labeled evidence before being treated as empirically proven.

### INV-124 — Model Readiness Governs Learned Influence
A learned model may influence governed behavior only at an explicitly approved readiness state and within the allowed scope.

### INV-125 — Model Training Must Preserve Dataset Provenance
Training/evaluation must preserve feature schema, data window, label definition, code/config/model version and evaluation evidence.

---

## 13. Recovery / failure invariants

### INV-130 — Recovery Cannot Waive Core Invariants
Recovery may not bypass identity, dedup, route, Trade Physics truth, model-readiness or observability safety.

### INV-131 — Severe Corruption Blocks Unsafe Continuation
If critical governed state cannot be restored, runtime refuses unsafe trusted continuation.

### INV-132 — Backup Fallback Does Not Silently Overwrite Trust
Fallback must be explicit and provenance-aware.

### INV-133 — Degraded Mode Explicit
Degraded state must be visible.

### INV-134 — Missing Model Is Not Runtime Failure By Itself
When learned prediction is optional/recommend-only, absence of a validated model yields no prediction rather than crashing or fabricating one.

### INV-135 — Missing Mandatory Deterministic Trade Physics Evidence Is Explicit
If current strategy canon requires deterministic TP evaluation and required real evidence is unavailable, the setup must be explicitly degraded/rejected/unavailable according to the strategy contract, never silently assigned a neutral TPS.

---

## 14. Deployment / change-control invariants

### INV-140 — No Deployment Without Backup/Rollback Readiness
Material deployment requires protected baseline/rollback evidence appropriate to its class.

### INV-141 — No Mixed Incompatible Version State
Persisted state, code, event schema, TP formula, DecisionObject and model versions must remain compatible enough for safe operation.

### INV-142 — Canonical Change Requires Auditability
Material change must be traceable through proposal, documentation, validation, deployment and review evidence.

### INV-143 — Docs Before Code
Structural runtime change may not be deployed before active canon describes the intended truth.

---

## 15. Admin / control invariants

### INV-150 — No Silent Governed Admin Mutation
Material admin actions affecting strategy/model/route/permissions/recovery must be auditable.

### INV-151 — Permission Boundaries Hold
No control path exceeds active role/permission authority.

### INV-152 — Unsafe Override Is Exceptional
Override mechanisms require explicit authorization, audit, bounded scope and rollback.

### INV-153 — Comprehension Does Not Become Mutation Authority
Showing TPS/model readiness/definitions does not grant permission to change them.

---

## 16. Freeze / safety switch

### INV-160 — Freeze Capability Must Exist
Critical invariant breach must support immediate freeze/safe-stop that blocks unsafe forward behavior while preserving evidence.

### INV-161 — Freeze Preserves Evidence
Safety stop cannot erase the evidence that triggered it.

### INV-162 — Model/Strategy Drift Can Trigger Review/Freeze
Severe unexplained drift in deterministic/learned behavior may require mutation freeze or signal-safety review under governance.

---

## 17. Human-comprehension invariants

### INV-HC-001 — No Naked Operational Concepts
Stable human-facing surfaces must explain material operational concepts, metrics, states and controls.

### INV-HC-002 — Interface as Operational Memory
Authorized returning users must be able to reconstruct meaning, purpose, consequences, limitations and canonical ownership without relying on chat memory/operator folklore.

### INV-HC-003 — Explanation Preserves Canonical Ownership
Human explanation cannot create alternate strategy/execution/distribution/analytics/model/governance truth.

### INV-HC-004 — Unknown Must Mean Unknown
A surface must not report UNKNOWN when sufficient canonical runtime evidence determines the state.

### INV-HC-005 — Comprehension Does Not Grant Authority
Definitions/help do not grant mutation/execution/permission authority.

### INV-HC-006 — TPS and Learned Probability Must Be Explained Separately
Human-facing intelligence must clearly distinguish deterministic TPS `[0,100]` from learned `trade_success_probability` `[0,1]` and show model/readiness provenance when probability exists.

---

## 18. Priority order

If obligations conflict, default priority is:
1. safety / capital / integrity invariants;
2. strategy/actionability invariants;
3. identity/FSM/execution invariants;
4. distribution/entitlement invariants;
5. evidence/schema/lineage invariants;
6. recovery/deployment invariants;
7. analytics/model optimization goals;
8. UX convenience.

AI/model performance never outranks safety, truth integrity or governance.

---

## 19. Breach consequence model

A material invariant breach must support as appropriate:
- explicit breach event;
- severity;
- affected domain/version;
- safe restriction/freeze;
- evidence preservation;
- remediation;
- rollback;
- post-incident review.

---

## 20. Final principle

BinaryBot remains trustworthy only if deterministic strategy truth, Trade Physics truth, learned-model truth, FSM/execution truth, publication truth and outcome truth stay explicitly separated, versioned, observable and governed.

No layer, model or operator may gain hidden authority by implementation accident.
