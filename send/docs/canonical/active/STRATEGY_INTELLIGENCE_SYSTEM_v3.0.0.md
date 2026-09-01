# STRATEGY_INTELLIGENCE_SYSTEM_v3.0.0

Path: /opt/binarybot/docs/canonical/active/STRATEGY_INTELLIGENCE_SYSTEM_v3.0.0.md  
Version: 3.0.0  
Status: ACTIVE CANONICAL  
Owner: BinaryBot / DROPi Signals  
Scope: Governed strategy intelligence, operator understanding, Trade Physics intelligence integration, readiness, recommendations, control-facing evidence

Supersedes: `STRATEGY_INTELLIGENCE_SYSTEM_v2.0.0.md`
Governance basis: Change ID `20260901-TRADE-PHYSICS-01`; merged PR #78

Linked documents:
- `canonical/active/ALGO_SPEC_v3.0.0.md`
- `canonical/active/TRADE_PHYSICS_MODEL_SPEC_v1.0.0.md`
- `canonical/active/TRADE_PHYSICS_INTELLIGENCE_SPEC_v1.0.0.md`
- `canonical/active/DECISION_OBJECT_CANONICAL_SPEC_v2.0.0.md`
- active Performance Analytics, Research/Learning and Autonomous Evolution successors

---

## 0. PROMOTION STATUS

Promotion status: ACTIVE CANONICAL under `CANONICAL_ACTIVATION_RECORD_20260901.md` and `CANONICAL_MASTER_INDEX_v2.0.0.md`.

---

## 1. PURPOSE

The Strategy Intelligence System converts validated strategy, market, execution, telemetry, outcome, analytics and research evidence into operator-usable understanding and governed recommendations.

It is not a signal generator and not a truth source that can overwrite upstream records.

v3 integrates Trade Physics as a current intelligence subsystem, including:

- deterministic TPS interpretation;
- physical-feasibility diagnostics;
- outcome correlation;
- learned `trade_success_probability` readiness/calibration;
- model drift visibility;
- recommendation generation;
- owner/admin review support.

---

## 2. CANONICAL POSITION

Canonical high-level chain:

`Strategy -> DecisionObject -> FSM -> Signal Execution -> Observability -> Decision Audit -> Telemetry -> Outcome Tracking -> Performance Analytics -> Research & Learning -> Strategy Intelligence -> Autonomous Evolution / Admin / Governance`

Trade Physics intelligence consumes evidence from this chain. It does not bypass it.

---

## 3. TRUTH SEPARATION

The system must preserve distinct domains:

1. Decision truth — what strategy believed.
2. Market truth — what price later did.
3. Signal/execution truth — what Signal Engine did or did not emit.
4. Distribution truth — what was published and where.
5. Operational/admin truth — what operators reconciled.
6. Community/business truth — user/service experience.
7. Research truth — findings/hypotheses.
8. Model/intelligence truth — derived predictions/recommendations with provenance.

Trade Physics must never collapse these into a single unlabeled success metric.

---

## 4. CORE MISSIONS

The system must answer:

- What is happening inside the strategy?
- Why do candidates pass or fail?
- Where do classical score and TPS disagree?
- Which physical-feasibility dimension is limiting setups?
- Are directional-speed/time assumptions working?
- Which symbols/sessions/regimes have strong or weak Trade Physics profiles?
- Is a learned model trained, validated, calibrated and stable?
- Is a recommendation safe to review?
- Is the system currently safe for experimentation or mutation?

---

## 5. CANONICAL SUBSYSTEMS

v3 retains and strengthens the v2 subsystem set:

1. Strategy Heatmap
2. Decision Bottleneck Analyzer
3. Signal Debug Dashboard
4. Admin Intelligence Control Layer
5. Research Intelligence Bridge
6. Telegram Intelligence UX Layer
7. AI Audit and Recommendation Layer
8. Evolution Readiness Layer
9. **Trade Physics Intelligence and Calibration Layer**

The ninth subsystem is current-scope under Owner decision.

---

## 6. STRATEGY HEATMAP

Heatmaps must support existing dimensions such as symbol/session/rejection/funnel and may now include:

- TPS band distribution;
- Trade Physics readiness distribution;
- space constraint heatmaps;
- directional-flow weakness;
- movement-stress clusters;
- classical-score/TPS disagreement;
- probability calibration bands when validated.

A heatmap suggests patterns; it does not prove causality.

---

## 7. DECISION BOTTLENECK ANALYZER

The analyzer must localize bottlenecks across:

- market activity/noise;
- corridor/available space;
- Time Model;
- classical scoring;
- Trade Physics readiness/components;
- focus/watchlist;
- FSM;
- execution/distribution.

Trade Physics must not cause all failures to be relabeled as TPS failures. Stage-of-death remains precise.

---

## 8. SIGNAL DEBUG DASHBOARD

Per-setup debug must distinguish:

- decision-time market evidence;
- structural barrier and available space;
- time evidence;
- classical score;
- S/T/P/V and TPS;
- TPS readiness/reason;
- DecisionObject result;
- FSM result;
- execution/distribution truth;
- later telemetry/outcome;
- learned probability/model readiness if present.

It must show which value influenced the decision and which was advisory only.

---

## 9. ADMIN INTELLIGENCE CONTROL LAYER

Admin/Owner surfaces may expose:

- current Trade Physics spec/version;
- TPS components/constants;
- readiness/missingness;
- dataset/model status;
- current model version;
- calibration/drift status;
- recommendation queue;
- experiment status;
- rollback/suspension status.

Viewing intelligence does not automatically grant mutation rights.

Any TPS weight/cap/threshold control requires explicit Parameter Control authorization.

---

## 10. RESEARCH INTELLIGENCE BRIDGE

The bridge must surface evidence-backed questions such as:

- Does TPS add predictive value beyond classical score?
- Is `space_to_buffer_ratio` too restrictive or appropriately protective?
- Does directional effective speed improve time feasibility?
- Which TPS component dominates failure by regime?
- Is the learned probability calibrated?
- Is a model degraded by drift?
- Is there enough evidence for a controlled parameter experiment?

Research findings must include confidence and provenance.

---

## 11. TELEGRAM / OPERATOR UX

Where Telegram/admin UI is used, Trade Physics views should be concise and drillable, for example:

- TPS / readiness summary;
- space/time/flow/stress explanation;
- model readiness badge/state;
- probability only if valid;
- recommendation with evidence/risk;
- explicit advisory vs live-influence marker.

Telegram remains a decision interface, not a raw log dump.

---

## 12. AI AUDIT AND RECOMMENDATION LAYER

AI may assist with:

- pattern clustering;
- model diagnostics;
- calibration analysis;
- feature importance interpretation;
- hypothesis generation;
- bottleneck ranking;
- experiment suggestions;
- contradiction detection;
- recommendation drafting.

AI may not:

- invent historical evidence;
- silently mutate strategy;
- promote its own model authority;
- rewrite deterministic TPS;
- bypass Owner/Admin/governance approval.

---

## 13. EVOLUTION READINESS LAYER

Readiness must consider:

- instrumentation completeness;
- Trade Physics feature completeness;
- outcome-label integrity;
- sample adequacy;
- model validation/calibration;
- current drift;
- discrepancy contamination;
- rollback readiness;
- recent change volume;
- approval readiness.

It may output states aligned with Research/Autonomous Evolution such as research-only, staged-experiment-ready or not-ready.

---

## 14. TRADE PHYSICS INTELLIGENCE AND CALIBRATION LAYER

Detailed learned-model authority is delegated to `TRADE_PHYSICS_INTELLIGENCE_SPEC_v1.0.0`.

This subsystem must expose at minimum:

- feature/dataset version;
- current deterministic TPS model version;
- model registry status;
- model readiness;
- `trade_success_probability` when valid;
- calibration quality;
- drift state;
- baseline comparison vs TPS/classical score;
- recommendation state;
- authority mode.

No valid model means an explicit not-ready state, not a missing product feature.

---

## 15. CURRENT TRADE PHYSICS MODEL STATES

Intelligence views must recognize states such as:

- UNTRAINED;
- INSUFFICIENT_DATA;
- TRAINED_UNVALIDATED;
- VALIDATION_FAILED;
- VALIDATED_RECOMMEND_ONLY;
- APPROVED_FOR_BOUNDED_USE;
- SUSPENDED_DRIFT;
- INVALID_MODEL.

Exact shared enum must remain synchronized with Trade Physics Intelligence canon.

---

## 16. RECOMMENDATION BOUNDARY

Recommendations must be:

- evidence-backed;
- attributable to model/research versions;
- confidence-rated;
- risk-labeled;
- reversible;
- reviewable.

A recommendation is not a strategy mutation.

The intelligence system may route a recommendation into Autonomous Evolution / Admin governance, but cannot apply it directly.

---

## 17. CONTRADICTION DETECTION

The intelligence system should surface contradictions such as:

- high classical score but low TPS;
- high TPS but poor realized outcomes;
- high model probability but low TPS;
- model probability materially miscalibrated;
- strategy rejects that market truth later suggests deserve research;
- strong market truth but poor operational/user experience;
- model recommendations conflicting with active canonical bounds.

Contradictions trigger review/research, not automatic override.

---

## 18. MODEL / FEATURE VERSION AWARENESS

Every Trade Physics intelligence summary must remain attributable to:

- deterministic Trade Physics spec/model version;
- DecisionObject/event schema version;
- dataset version;
- feature schema version;
- model id/version;
- validation/calibration version;
- time window.

Aggregating incompatible versions without labeling is forbidden.

---

## 19. PERFORMANCE AND CALIBRATION VIEWS

The system should expose:

- outcome rate by TPS band;
- probability calibration by band;
- missing/readiness rate;
- model-versus-baseline comparison;
- error by symbol/session/regime;
- drift over rolling windows;
- false-confidence pockets;
- disagreement matrices.

No single overall win rate is sufficient.

---

## 20. PARAMETER INTELLIGENCE

The system may diagnose whether Trade Physics constants or policy appear too strict/loose.

It may propose experiments involving:

- S/T/P caps;
- deterministic weights;
- speed lookback/weight profile;
- future TPS policy thresholds;
- model features/hyperparameters;
- calibration methods.

These are proposals only. Structural changes require versioned canon; tunable changes require Parameter Control authority.

---

## 21. SAFETY AND FAILURE BEHAVIOR

If model or intelligence infrastructure fails:

- deterministic strategy continues according to active strategy canon;
- no guessed probability is generated;
- model authority fails closed;
- failure/readiness is visible;
- recommendations dependent on invalid evidence are suspended.

Intelligence failure must not create a hidden strategy mode.

---

## 22. OBSERVABILITY

Material intelligence actions should be observable, including:

- dataset refresh;
- model train/validation;
- readiness transition;
- calibration/drift alert;
- recommendation generation;
- approval/rejection;
- bounded-use activation/suspension;
- rollback.

Event naming must align with consolidated Event Schema.

---

## 23. FORBIDDEN PATTERNS

Forbidden:

- intelligence overwriting raw truth;
- model score labeled TPS;
- probability displayed without readiness/model identity;
- AI recommendation directly changing production;
- model drift hidden from operators;
- aggregate metrics mixing incompatible model/strategy versions;
- user/community data treated as objective market label without explicit truth labeling;
- debug output that cannot explain Trade Physics components.

---

## 24. IMPLEMENTATION REQUIREMENTS UNDER ACTIVE CANON

The current-scope intelligence implementation must provide, in governed sequence:

1. Trade Physics evidence ingestion;
2. analytics/dataset status;
3. model registry/readiness;
4. calibration/drift status;
5. per-setup debug explanation;
6. recommendations/experiment linkage;
7. owner/admin review surfaces;
8. failure/suspension visibility.

No broker/distribution behavior is implied.

---

## 25. FINAL PRINCIPLE

Strategy Intelligence turns truth into understandable, governable action.

For Trade Physics, the chain is:

`TPS + components + real outcomes -> analytics/research -> validated model/calibration -> intelligence explanation -> recommendation -> governed human decision`.

The intelligence layer may become sophisticated, but it never earns authority by opacity or by calling itself AI.
