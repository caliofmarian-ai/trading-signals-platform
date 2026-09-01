# CHANGE_PROPOSAL_20260901_TRADE_PHYSICS_CURRENT_CANONICAL_INTEGRATION

Status: OWNER APPROVED DIRECTION — CANONICAL RECONCILIATION REQUIRED BEFORE CODE
Date: 2026-09-01
Owner: BinaryBot / DROPi Signals Owner
Requested by: Owner
Change ID: 20260901-TRADE-PHYSICS-01
Type: MAJOR — structural strategy / scoring / intelligence / event-contract integration

## 1. OWNER DECISION

The Owner explicitly decided on 2026-09-01 that the Trade Physics family currently located in `send/docs/intake/` must not remain a future upgrade or passive research-only concept.

Trade Physics must be integrated into the current governed Binary Strategy V2 system.

This decision overrides the prior future-state classification for the Trade Physics family recorded in `CANON_BATCH_EVALUATION_v2.0.0`, subject to completion of the canonical reconciliation and promotion process required by `GOVERNANCE_AND_CHANGE_CONTROL_v2.0.0`.

This proposal does not itself activate new runtime behavior and does not authorize code changes until the relevant canonical successors are complete, internally consistent, approved, promoted, and re-audited.

## 2. SOURCE DOCUMENTS IN SCOPE

The full Trade Physics intake family is in scope:

1. `send/docs/intake/AI_TRADE_PHYSICS_SPACE_MODEL_SPEC.md`
2. `send/docs/intake/TRADE_PHYSICS_SCORE_SPEC.md`
3. `send/docs/intake/AI_TRADE_PHYSICS_INTELLIGENCE_SPEC.md`

These source documents are not treated as active canonical authority merely because their internal headers use canonical wording. Their content must be reconciled into the active authority graph.

## 3. CURRENT CANONICAL CONFLICT

`CANON_BATCH_EVALUATION_v2.0.0` currently classifies:

- `AI_TRADE_PHYSICS_SPACE_MODEL_SPEC.md` as `KEEP_OUTSIDE_ACTIVE`;
- `TRADE_PHYSICS_SCORE_SPEC.md` as `PROPOSED_FUTURE_STATE`;
- `AI_TRADE_PHYSICS_INTELLIGENCE_SPEC.md` as `PROPOSED_FUTURE_STATE`.

That classification is no longer aligned with Owner intent.

The classification must therefore be superseded or amended through governed canonical versioning before implementation work proceeds.

## 4. CURRENT ACTIVE CANON ALREADY REQUIRES PART OF THE MODEL

Trade Physics is not being introduced into an empty architecture.

Current active canon already requires:

- corridor-first structural interpretation;
- explicit structural space and boundary semantics;
- structural feasibility before full temporal interpretation;
- time feasibility inside the established corridor;
- scoring after corridor and time;
- volatility and buffer realism in strategic scoring;
- DecisionObject production after scoring;
- observability and decision audit sufficient to explain structure, time, score and rejection.

Therefore the Trade Physics integration is a formalization and completion of concepts that are already partially present in active strategy truth and partially present in runtime telemetry.

## 5. DISCOVERED RUNTIME DRIFT

Current runtime contains partial Trade Physics concepts, including `space_to_buffer_ratio`, while the runtime event schema contains optional fields including `TPS`, `space_to_buffer_ratio`, and `trade_space_margin_atr`.

This means the repository already contains partial implementation vocabulary without one complete active canonical Trade Physics contract.

The remediation objective is not to preserve accidental runtime behavior. The objective is to define the intended canonical truth first and then reconcile implementation against it.

## 6. MATERIAL SOURCE CONTRADICTION — TWO TPS DEFINITIONS

The intake family currently contains two materially different score definitions.

### 6.1 Deterministic TPS in `TRADE_PHYSICS_SCORE_SPEC.md`

The document defines four normalized components:

- S = structural space component;
- T = time feasibility component;
- P = price speed component;
- V = volatility efficiency component.

It defines the deterministic score:

`TPS_raw = wS*S + wT*T + wP*P + wV*V`

with initial proposed weights:

- `wS = 0.35`
- `wT = 0.25`
- `wP = 0.20`
- `wV = 0.20`

and:

`TPS = 100 * TPS_raw`

so that `TPS` is in `[0,100]`.

### 6.2 Probabilistic formula in `AI_TRADE_PHYSICS_INTELLIGENCE_SPEC.md`

The AI intelligence document defines a different four-dimensional representation:

- E = Buffer-ATR Efficiency;
- S = Reachability Ratio;
- T = Time-to-Buffer Ratio;
- F = Momentum Alignment Factor.

It then proposes:

`TPS = sigmoid(w1*(1/E) + w2*log(S) + w3*log(T) + w4*F)`

with a range `[0,1]` and different interpretation thresholds.

### 6.3 Required canonical resolution

The system MUST NOT ship two different calculations under the same canonical field name `TPS`.

The proposed reconciliation direction is:

1. `TPS` becomes the deterministic Trade Physics Score governed by the reconciled strategy/scoring canon and expressed on `[0,100]`.
2. The sigmoid/learned probability output from the AI intelligence model receives a distinct canonical name, provisionally `trade_success_probability` or another explicitly approved learned-probability field.
3. Learned probability MUST NOT silently overwrite deterministic TPS.
4. Thresholds and readiness rules for learned probability require evidence and governance independent of deterministic TPS.

The final field name and exact contract must be fixed in canonical documents before code implementation.

## 7. PROPOSED CURRENT TRADE PHYSICS MODEL

The current strategy must model physical trade feasibility through four governed dimensions.

### 7.1 Structural space

Canonical source ownership is primarily the SR / Corridor domain.

Required source metrics include:

- nearest relevant structural barrier in the trade direction;
- `available_space`;
- `required_space` / canonical buffer-distance equivalent;
- `space_to_buffer_ratio`;
- `trade_space_margin_atr`;
- structural compression / boundary proximity context.

The core relation from the intake source is:

`space_to_buffer_ratio = available_space / required_space`

and:

`trade_space_margin_atr = (available_space - required_space) / atr_m5`

Canonical integration must use active vocabulary, especially `buffer_distance` rather than legacy `buffer_price` where the active time/strategy canon requires it.

### 7.2 Time feasibility

Canonical source ownership is the unified Time Model.

The integration must map intake terminology such as `expiry_minutes / t_needed_adj_min` onto active canonical time vocabulary such as:

- `t_needed`;
- `t_needed_adjusted`;
- `model_expiry`;
- `model_time_reach_ratio`;
- `corridor_time_pressure`;
- `time_state`.

No Trade Physics document may create a parallel time-model authority.

### 7.3 Directional price speed / flow

The intake family requires directional, recency-weighted and noise-aware speed rather than an undifferentiated gross speed.

The canonical reconciliation must define ownership for:

- `directional_effective_speed`;
- gross speed reference;
- `flow_efficiency`;
- directional alignment semantics;
- ATR-normalized speed reference.

This must be integrated into the existing market/time/scoring ownership boundaries without duplicating authority.

### 7.4 Volatility / movement realism

The model must preserve explicit comparison between required movement and volatility scale.

Candidate source metrics include:

- ATR;
- buffer-to-ATR / movement stress;
- volatility efficiency component;
- normalized movement realism.

The active strategy vocabulary must be used consistently.

## 8. TPS CURRENT STRATEGY ROLE

Trade Physics is no longer classified only as future research.

The deterministic TPS must become part of the current strategic decision contract.

However, its exact influence must be canonical and explicit. It must not be introduced by a hidden multiplier or an undocumented threshold.

The canonical successor set must decide and state explicitly whether TPS acts as:

- a score component;
- a strategic gate;
- a degradation factor;
- a required physical-feasibility companion score;
- or a governed combination of these roles.

Whatever role is selected must preserve the existing architecture:

`Market Data -> Market Model -> SR/Corridor -> Time Model -> Scoring -> DecisionObject -> FSM -> Signal Engine`

Trade Physics is proposed as a governed submodel of the strategic/scoring layer, fed by already-owned structural, time, volatility and flow evidence. It is not proposed as a new top-level pipeline stage that bypasses current ownership.

## 9. AI / SELF-CALIBRATION CURRENT INTEGRATION

The AI intelligence content is also brought into current project scope, but current integration MUST distinguish architecture availability from statistical readiness.

The system may implement now:

- dataset collection;
- feature lineage;
- training pipeline interfaces;
- model registry / artifact identity;
- calibration engine interfaces;
- recommendation generation;
- admin review / approval surfaces;
- readiness and insufficient-data states;
- bounded adjustment governance where canonically allowed.

The system MUST NOT fabricate a trained model or pretend that an unvalidated model has predictive authority.

A learned model may influence live decisions only after canonical evidence criteria are satisfied.

The current integration must therefore support explicit states such as:

- `UNTRAINED`;
- `INSUFFICIENT_DATA`;
- `TRAINED_UNVALIDATED`;
- `VALIDATED_RECOMMEND_ONLY`;
- `APPROVED_FOR_BOUNDED_USE` where separately authorized.

Exact state names are subject to canonical reconciliation.

## 10. SAFETY AND AUTHORITY BOUNDARY

The intake document already states that AI must not directly modify strategy without governance.

That boundary remains binding in the integration direction.

Trade Physics AI/calibration must not:

- silently change live strategy weights;
- silently change thresholds;
- bypass Owner/Admin approval where required;
- overwrite deterministic strategy truth with an opaque learned output;
- operate without model identity, dataset lineage and validation evidence;
- bypass rollback and monitoring requirements.

## 11. PROPOSED CANONICAL TARGET DOCUMENTS

The canonical audit must determine final versions and exact changes, but the expected impact surface includes at least:

### Strategy root and primary logic
- `CANONICAL_STRATEGY_STACK`
- `ALGO_SPEC`
- `SR_CORRIDOR_ENGINE_SPEC`
- `TIME_MODEL_UNIFIED_CANON`
- `DECISION_OBJECT_CANONICAL_SPEC`

### Scoring / parameters / controls
- `STRATEGY_PARAMETER_CONTROL_SPEC`
- relevant admin/owner control canon if TPS weights, caps or thresholds are exposed

### Intelligence / research / learning
- `STRATEGY_INTELLIGENCE_SYSTEM`
- `RESEARCH_AND_LEARNING_FRAMEWORK_SPEC`
- `AUTONOMOUS_STRATEGY_EVOLUTION_SYSTEM`
- `PERFORMANCE_ANALYTICS_SPEC`
- `OUTCOME_TRACKING_SPEC` where outcome linkage is required

### Contracts / telemetry / observability
- `MODULE_INTERFACE_SPEC`
- `DECISION_AUDIT_SPEC`
- `OBSERVABILITY_SPEC`
- `OBSERVABILITY_LOGGING_SPEC`
- `EVENT_SCHEMA_SPEC`
- `TRADE_TEMPORAL_TELEMETRY_SPEC` where post-trade temporal analysis participates in calibration

### Architecture / invariants / governance records
- `SYSTEM_ARCHITECTURE_MAP` if the intelligence/calibration topology materially changes
- `SYSTEM_INVARIANTS` if new hard truths are required
- `CANON_BATCH_EVALUATION` or its governed successor/amendment to reverse the former future-state classification
- `CANONICAL_MASTER_INDEX`

This list is not permission to patch every document. Each document must be changed only if the canonical impact audit proves a real ownership or reference requirement.

## 12. TARGET CODE — NOT AUTHORIZED YET

No runtime code is authorized by this proposal alone.

Expected future implementation impact may include, after canonical promotion:

- market model / directional speed derivation;
- SR/corridor structural-space outputs;
- time model input/output integration;
- strategy scoring and DecisionObject production;
- decision audit and observability;
- event schema runtime alignment;
- analytics / outcome datasets;
- intelligence/calibration modules;
- admin control/readiness surfaces;
- tests and replay validation.

Actual code targets must be derived from the promoted canon and re-audited before modification.

## 13. OUT OF SCOPE FOR THIS PROPOSAL

This proposal does not authorize:

- broker execution;
- automatic real-money trading;
- Telegram publication changes;
- distribution routing changes unrelated to Trade Physics telemetry;
- invented market data;
- invented model training results;
- silent replacement of Binary Strategy V2 with a machine-learning strategy;
- profit guarantees.

## 14. RATIONALE

The Owner requires Trade Physics to be part of the current strategy rather than deferred.

The integration is also technically necessary because:

- active strategy canon already contains structural-space/time/volatility concepts;
- runtime contains partial Trade Physics telemetry;
- the intake family contains valuable mathematical definitions not yet reconciled with active vocabulary;
- leaving the family outside active canon would preserve code/document drift;
- implementing directly from intake would create multiple competing truth sources.

## 15. EXPECTED IMPACT

Expected impact is high and structural.

The change may affect:

- score composition;
- strategic rejection/degradation reasons;
- DecisionObject evidence;
- event payloads;
- analytics feature sets;
- training datasets;
- parameter governance;
- future learned-probability recommendations;
- strategy explainability.

## 16. RISK

Primary risks include:

- selecting the wrong TPS formula or mixing two formulas;
- double-counting structural/time evidence already present in the classical score;
- unstable thresholds before sufficient outcome evidence exists;
- confusing deterministic physical feasibility with learned success probability;
- using legacy vocabulary (`buffer_price`, `expiry_minutes`) against active canonical vocabulary;
- training leakage or invalid outcome labels;
- premature AI authority;
- increased false rejects if TPS is introduced as a hard gate without calibration;
- increased false accepts if TPS is treated as probability without validation.

## 17. BLAST RADIUS

Blast radius is expected across the strategy, audit, analytics and intelligence clusters.

This change must therefore be implemented as a governed program with isolated documentation and code phases.

It must not be silently folded into the staged signal-execution/observability remediation currently associated with PR #73 and the post-#77 canonical successor work.

The two structural changes may be coordinated in the master index/root manifest, but their behavioral validation must remain separately attributable.

## 18. VALIDATION METHOD

Before code:

1. full intake-to-active canonical mapping;
2. formula conflict resolution;
3. vocabulary reconciliation;
4. ownership mapping;
5. version and supersession plan;
6. canonical reference scan;
7. final active-canon consistency audit.

After code authorization:

1. unit tests for every primitive metric;
2. deterministic formula tests with hand-calculated examples;
3. edge-case tests for zero/invalid ATR, zero required space, missing SR, missing time evidence, insufficient speed evidence;
4. DecisionObject contract tests;
5. event-schema tests;
6. replay comparison against prior strategy behavior;
7. shadow-mode distribution of TPS metrics before any aggressive decision influence if required by evidence policy;
8. outcome correlation analysis;
9. model/dataset leakage tests for AI training;
10. restart/persistence/reproducibility tests;
11. validation of admin approval and rollback controls.

## 19. ROLLBACK PLAN

Documentation rollback:

- keep current active canon authoritative until complete successor promotion;
- if reconciliation fails, do not promote successors;
- source intake documents remain retained for provenance.

Runtime rollback after future implementation:

- retain previous strategy release baseline;
- make deterministic TPS decision influence separately disable-able only through canonically governed control;
- preserve telemetry where safe so rollback does not destroy evidence;
- learned model influence must be independently disable-able and must fail closed to deterministic governed strategy behavior.

Exact rollback controls require canonical definition before code.

## 20. DEPLOYMENT PLAN

No deployment is authorized by this proposal.

Future deployment must be staged:

1. canonical promotion;
2. implementation on isolated branch;
3. unit/integration/replay tests;
4. shadow evidence collection if required;
5. controlled runtime validation;
6. monitored activation of governed TPS decision influence;
7. separate validation of learned-probability influence only after readiness criteria are met.

## 21. MONITORING WINDOW

Monitoring requirements must include, at minimum:

- TPS component distributions;
- reject/degrade counts attributable to Trade Physics;
- missing-evidence rates;
- per-symbol and per-regime behavior;
- strategy-score vs TPS disagreement;
- outcome correlation;
- calibration drift;
- learned-model readiness and validation state;
- before/after signal volume and lifecycle impact.

The exact window is to be set in the deployment protocol for the implementation release.

## 22. SUCCESS CRITERIA

Canonical success requires:

- one unambiguous deterministic TPS formula;
- one distinct learned-probability contract;
- no duplicated ownership;
- no active/future classification conflict;
- complete source-to-canon provenance;
- active vocabulary alignment;
- complete observability and DecisionObject evidence contract;
- explicit AI readiness and authority states.

Implementation success later requires:

- exact reproducible metric calculations;
- no invented market inputs;
- no schema drift;
- no hidden parameter changes;
- stable replay behavior explainable by the new rules;
- evidence that decision influence behaves as canonically intended.

## 23. FAILURE TRIGGERS

Stop and return to canonical reconciliation if any of the following occurs:

- two TPS definitions remain active;
- canonical docs disagree on metric direction or units;
- active time-model vocabulary is bypassed;
- SR and scoring layers both claim conflicting ownership of the same derived metric;
- DecisionObject lacks required provenance;
- AI learned output can affect live decisions without readiness evidence;
- any code patch is proposed before canonical promotion;
- Trade Physics integration silently changes broker/distribution behavior outside approved scope.

## 24. APPROVAL STATUS

Owner strategic direction: APPROVED on 2026-09-01.

Technical/canonical reconciliation: IN PROGRESS.

Runtime implementation: NOT YET AUTHORIZED.

PR #73: REMAINS ON CANONICAL HOLD.

## 25. NEXT GOVERNED STEP

The next step is documentation-only:

1. audit all three Trade Physics intake documents against the latest active canon;
2. produce a source-to-canonical ownership matrix;
3. resolve TPS formula/name conflicts;
4. decide exact successor versions under SemVer;
5. produce complete self-contained proposed canonical successors;
6. update the canonical classification so Trade Physics is current-scope;
7. run a complete canonical consistency audit;
8. only after promotion, re-audit and modify runtime code.
