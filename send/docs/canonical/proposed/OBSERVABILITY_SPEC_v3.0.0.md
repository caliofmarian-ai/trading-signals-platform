# OBSERVABILITY_SPEC_v3.0.0

Version: 3.0.0  
Status: PROPOSED COMPLETE CONSOLIDATED SUCCESSOR — NOT ACTIVE CANONICAL  
Owner: BinaryBot / DROPi Signals  
Scope: observability policy for strategy, Trade Physics, FSM, signal execution, distribution, telemetry, outcomes and governed intelligence evidence  
Supersession Intent: `OBSERVABILITY_SPEC_v2.0.0.md`

Linked proposed/current authorities:
- Root Strategy Stack successor
- `ALGO_SPEC_v3.0.0.md`
- `TRADE_PHYSICS_MODEL_SPEC_v1.0.0.md`
- `TRADE_PHYSICS_INTELLIGENCE_SPEC_v1.0.0.md`
- `TIME_MODEL_UNIFIED_CANON_v3.0.0.md`
- `SR_CORRIDOR_ENGINE_SPEC_v3.0.0.md`
- `DECISION_OBJECT_CANONICAL_SPEC_v2.0.0.md`
- `FSM_DECISION_ENGINE_SPEC_v2.0.0.md`
- `SIGNAL_ENGINE_EXECUTION_SPEC_v3.0.0.md`
- `EVENT_SCHEMA_SPEC_v3.0.0.md`
- `OBSERVABILITY_LOGGING_SPEC_v3.0.0.md`
- `TRADE_TEMPORAL_TELEMETRY_SPEC_v3.0.0.md`
- `OUTCOME_TRACKING_SPEC_v3.0.0.md`
- Performance Analytics / Research / Intelligence successors

---

## 0. Authority and promotion status

This is the complete proposed successor for observability policy.

Until explicit promotion, `OBSERVABILITY_SPEC_v2.0.0.md` remains active.

The major version consolidates:
- explicit post-FSM signal-execution observability;
- truth-domain separation through distribution/external visibility;
- current-scope Trade Physics strategy evidence;
- learned-model/readiness observability;
- telemetry/label lineage requirements.

No code behavior is authorized by this proposal alone.

---

## 1. Purpose

Observability must allow a qualified operator/auditor to reconstruct the complete governed lifecycle of a candidate/setup from birth to rejection, progression, execution handoff, distribution, market outcome and operational reconciliation.

The system must answer not merely **what happened**, but **where, why, under which evidence/version, and under which authority**.

---

## 2. Core principle

The canonical observable chain is:

`Market Evidence -> SR/Corridor -> Time -> Classical Scoring + Trade Physics -> DecisionObject -> FSM -> Signal Engine Execution -> Distribution -> External Visibility -> Telemetry -> Outcome Reconciliation -> Analytics/Research/Intelligence`

Each layer owns its own truth.

Observability correlates these truths; it does not collapse them.

---

## 3. Minimum correlation

Every material setup/decision flow must support enough identifiers to reconstruct:
- setup/candidate correlation;
- symbol;
- direction;
- timeframe/candle context;
- timestamp;
- cycle/run identity;
- decision/stage identity;
- signal identity once assigned;
- execution attempt identity where applicable;
- route/destination identity where applicable;
- telemetry/outcome references.

Missing correlation is observability degradation.

---

## 4. Truth domains

Observability must keep at least these domains distinct:

1. market/indicator evidence;
2. structural/corridor truth;
3. time-model truth;
4. classical score truth;
5. deterministic Trade Physics truth;
6. learned probability/model truth;
7. DecisionObject strategy truth;
8. FSM operational truth;
9. Signal Engine execution truth;
10. Distribution route truth;
11. external visibility truth;
12. market telemetry truth;
13. operational/admin reconciliation truth;
14. analytics/research/intelligence interpretation;
15. governance/admin mutation truth.

No later domain may overwrite an earlier historical truth record.

---

## 5. Market/structural observability

The system must be able to explain:
- what market context was observed;
- trend/volatility/activity/noise state;
- ATR and relevant raw/derived evidence;
- what directional structural barrier/corridor was selected;
- available structural space;
- required movement distance;
- structural feasibility/conflict/compression;
- why structure was valid, degraded or rejected.

---

## 6. Time observability

The system must expose enough time-model evidence to reconstruct:
- gross price speed where used;
- `directional_effective_speed`;
- `flow_efficiency`;
- `t_needed`;
- `t_needed_adjusted`;
- `model_expiry`;
- `model_time_reach_ratio`;
- `time_to_buffer_ratio` where Trade Physics consumes it;
- `corridor_time_pressure`;
- `time_state`;
- execution-expiry derivation where applicable.

Time metrics must preserve formula/version semantics and orientation.

---

## 7. Trade Physics observability

For every strategy evaluation where Trade Physics evidence is available, observability must answer:
- what `available_space` and `required_space` were used?
- what was `space_to_buffer_ratio`?
- what was `trade_space_margin_atr`?
- what was `directional_effective_speed`?
- what was `flow_efficiency`?
- what was `time_to_buffer_ratio`?
- what was `directional_speed_ratio`?
- what was `movement_stress`?
- what were S/T/P/V components?
- what deterministic TPS resulted?
- what Trade Physics formula/version and parameter/weight version produced it?

Deterministic TPS must remain distinguishable from classical score and from learned probability.

---

## 8. Learned probability/model observability

If a validated learned model produces `trade_success_probability`, observability must expose:
- probability value;
- model id/version;
- calibration version;
- feature schema version;
- readiness state;
- out-of-distribution/degraded flags where available;
- evidence timestamp/cutoff.

If no valid model exists, this absence must be representable without fabricated defaults.

Model predictions are interpretation/evidence, not market truth.

---

## 9. DecisionObject observability

Observability must preserve enough of the DecisionObject to explain:
- setup identity;
- market context;
- structure;
- time;
- classical score;
- Trade Physics;
- learned probability where valid;
- strategic blockers/degradation;
- requested lifecycle stage;
- schema/version.

DecisionObject truth is pre-FSM strategy truth.

---

## 10. FSM observability

For every material FSM action, the system must expose:
- prior/new state;
- requested stage;
- accepted stage;
- reason/reason family;
- state-change flag;
- `stage_handoff_ready`;
- `trade_execution_ready`;
- duplicate/cooldown/watchlist/focus context;
- persistent-state effect where applicable.

A transition record must not be interpreted automatically as accepted-stage handoff.

---

## 11. Signal Engine execution observability

The system must answer:
- what post-FSM handoff entered Signal Engine?
- was exact stage accepted?
- was a SignalEvent candidate built?
- what execution phase occurred?
- what outcome occurred: EMITTED / NOT_EMITTED / BLOCKED / SKIPPED / FAILED / DEFERRED?
- what was the reason?
- was routing invoked?
- what publication evidence supports EMITTED, if any?
- what upstream DecisionObject/Trade Physics snapshot was carried?

Execution truth must be represented by a dedicated `signal_execution_result` domain, not only generic debug data.

---

## 12. Signal candidate vs delivery observability

The following must remain visibly distinct:
- SignalEvent candidate constructed;
- candidate deferred before distribution;
- route publish attempted;
- route publish succeeded/failed/skipped;
- external stage became visible.

SignalEvent construction is not external visibility and not EMITTED.

---

## 13. Distribution observability

For every material route action, preserve:
- signal id;
- stage;
- route/destination;
- route state;
- entitlement/policy result;
- publish attempt/result;
- dedup/counter behavior;
- transport outcome;
- failure/skip reason.

Distribution owns exact route truth.

---

## 14. External visibility observability

The system must be able to prove whether a PRE/CONFIRM/OPEN_NOW stage became externally visible, through which governed route and which successful publication evidence.

No hidden externally material signal is allowed.

---

## 15. Telemetry observability

For every effective executable telemetry chain, preserve:
- stable signal/execution/decision linkage;
- immutable pre-trade strategy/Trade Physics snapshot;
- feature/version provenance;
- raw checkpoint timestamps/prices;
- official market outcome;
- derived recovery/path classifications;
- label derivation/version;
- feature cutoff timestamp.

Telemetry truth must be independent of admin/community reports.

---

## 16. Outcome reconciliation observability

Every outcome mutation/reconciliation must expose:
- signal id;
- actor/authorization;
- requested outcome;
- prior outcome;
- final outcome;
- reconciliation status;
- timestamp;
- reason/correction/dispute context;
- telemetry discrepancy linkage.

Operational truth must remain distinct from market telemetry truth.

---

## 17. Analytics/research/intelligence observability

Derived findings must preserve provenance:
- source truth domains;
- time window;
- sample size;
- feature/formula/model versions;
- derivation method;
- confidence/readiness;
- linked hypothesis/experiment where applicable.

A dashboard number without provenance must not be treated as canonical evidence for strategic mutation.

---

## 18. Model lifecycle/readiness observability

Current-scope Trade Physics Intelligence requires visibility into:
- dataset build/version;
- training run;
- evaluation metrics;
- calibration result;
- model registry/version;
- readiness state transition;
- drift alerts;
- recommendation/approval/rollback history.

No model may silently move from training to production influence.

---

## 19. Admin/parameter observability

Every material strategy/model/parameter mutation attempt must expose:
- actor and role;
- requested change;
- prior value/state;
- validation result;
- approval state;
- persisted value;
- reload/activation result;
- rollback result where applicable;
- proof/correlation identifiers.

Trade Physics weights/formulas are structural truth, not ordinary live-tunable parameters unless separately authorized.

---

## 20. Distinct outcome families

Observability must not merge:

### Strategic
- accept/degrade/reject/no-signal/stage request

### FSM
- wait/prepare/confirm/open-now/reject/blocked/degraded and stage handoff semantics

### Signal Engine
- EMITTED/NOT_EMITTED/BLOCKED/SKIPPED/FAILED/DEFERRED

### Distribution
- published/skipped/failed/duplicate etc.

### Market telemetry
- WIN/LOSS/DRAW and derived temporal classes

### Operational/admin
- WIN/LOSE/MISSED/reconciliation statuses

These labels may be correlated but never treated as the same taxonomy.

---

## 21. Stage-of-death / rejection observability

For candidates that fail to progress, observability should identify where death occurred:
- market/context;
- structural/space;
- time;
- classical score;
- Trade Physics;
- DecisionObject gate;
- FSM;
- execution;
- distribution.

This enables rejection analytics without guessing from missing signals.

---

## 22. Missingness/degradation policy

Missing observability is not equivalent to a successful/failed strategy result.

The system must distinguish:
- field legitimately not applicable;
- field unavailable because no validated model exists;
- upstream evidence missing;
- logging failure;
- schema validation failure;
- correlation loss.

Evidence quality must be visible to downstream research/AI.

---

## 23. Security/privacy

Observability must not expose:
- secrets;
- API credentials;
- unnecessary personal data;
- unrestricted member-level private statistics.

Role/permission/privacy canon governs visibility.

---

## 24. Storage/retention principle

Evidence must be durable enough for:
- forensic reconstruction;
- replay;
- analytics;
- research;
- model reproducibility;
- governance review.

Rotation/compression may not destroy required provenance without governed retention policy.

---

## 25. Runtime schema relationship

Observability policy is canonical authority.

Runtime JSON schema, log writers, dashboards and report code are implementations that must be audited against this policy after promotion.

---

## 26. Forbidden observability patterns

Forbidden:
- opaque single debug blob as sole evidence;
- TPS without formula/version in contexts where reproducibility matters;
- learned probability without model/readiness metadata;
- fabricated model probability when no model is ready;
- candidate construction logged as external emission;
- market result overwritten by admin result;
- downstream outcome used to rewrite historical pre-trade evidence;
- parameter/model mutation without proof trail.

---

## 27. Final principle

If a material event, decision, state transition, Trade Physics calculation, execution result, distribution action, market outcome, model readiness transition, or admin mutation cannot be reconstructed from governed evidence, observability is incomplete.

Trade Physics integration is considered observable only when the deterministic score, its components/formula/version, any learned probability/model version, and the eventual market/operational outcomes remain independently traceable end-to-end.
