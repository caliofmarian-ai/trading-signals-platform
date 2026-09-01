# SIGNAL_ENGINE_EXECUTION_SPEC_v3.0.0

Version: 3.0.0  
Status: ACTIVE CANONICAL  
Owner: BinaryBot / DROPi Signals  
Scope: post-FSM signal execution, SignalEvent candidate construction, execution outcomes, distribution handoff, execution observability, Trade Physics downstream boundary  
Supersedes: `SIGNAL_ENGINE_EXECUTION_SPEC_v2.0.0.md`  

Linked authorities:
- `CANONICAL_STRATEGY_STACK_v2.0.0.md`
- `ALGO_SPEC_v3.0.0.md`
- `TRADE_PHYSICS_MODEL_SPEC_v1.0.0.md`
- `TRADE_PHYSICS_INTELLIGENCE_SPEC_v1.0.0.md`
- `TIME_MODEL_UNIFIED_CANON_v3.0.0.md`
- `SR_CORRIDOR_ENGINE_SPEC_v3.0.0.md`
- `DECISION_OBJECT_CANONICAL_SPEC_v2.0.0.md`
- `FSM_DECISION_ENGINE_SPEC_v2.0.0.md`
- `MODULE_INTERFACE_SPEC_v3.0.0.md`
- `OBSERVABILITY_SPEC_v3.0.0.md`
- `EVENT_SCHEMA_SPEC_v3.0.0.md`
- `SIGNAL_DISTRIBUTION_ARCHITECTURE_v2.0.1.md`
- `SIGNAL_DISTRIBUTION_SPEC_v2.0.1.md`
- `CHANNEL_CONFIG_SPEC_v2.0.1.md`

---

## 0. Authority and promotion status

This document is the active canonical consolidated successor for the signal-execution domain.

It incorporates:
- staged execution / post-FSM observability remediation;
- the Trade Physics ownership boundary required by current-scope integration.

Promotion status: ACTIVE CANONICAL under `CANONICAL_ACTIVATION_RECORD_20260901.md` and `CANONICAL_MASTER_INDEX_v2.0.0.md`.

This active specification does not by itself authorize runtime changes, distribution activation, Telegram publication, outcome creation, or broker execution.

---

## 1. Purpose

Signal Engine is the execution layer between FSM and Distribution.

It must:
- consume explicit post-FSM operational handoff truth;
- apply exact-stage execution gating;
- materialize `SignalEvent` candidates only for accepted lifecycle stages;
- preserve stable identity and duplicate protection;
- hand candidates to Distribution without stealing route authority;
- classify execution outcomes distinctly;
- emit execution observability;
- carry upstream strategic evidence, including Trade Physics, without recomputing it.

Signal Engine does not own:
- strategy mathematics;
- Trade Physics mathematics;
- DecisionObject production;
- FSM lifecycle authority;
- distribution entitlement/routing;
- Telegram formatting;
- market telemetry truth;
- operational outcome truth;
- broker execution.

---

## 2. Canonical flow

The required order is:

`Market -> SR/Corridor -> Time -> Scoring + Trade Physics -> DecisionObject -> FSM -> Signal Engine -> SignalEvent candidate / execution result -> Distribution Router -> Publisher / External Surface`

No direct shortcut is canonical.

Forbidden shortcuts include:
- strategy -> signal/publication;
- score/TPS -> signal/publication;
- expiry -> signal/publication;
- DecisionObject -> SignalEvent without exact-stage FSM handoff;
- SignalEvent -> Telegram without Distribution Router.

---

## 3. Signal Engine responsibilities

1. execution gating;
2. exact-stage handoff validation;
3. SignalEvent candidate construction;
4. engine-level duplicate protection;
5. downstream handoff orchestration;
6. execution-outcome classification;
7. execution evidence/correlation.

---

## 4. Primary input contract

The primary authority is explicit post-FSM handoff semantics.

Minimum required semantic fields:
- `requested_stage`;
- `accepted_stage`;
- `stage_handoff_ready`;
- `trade_execution_ready`;
- FSM state/outcome;
- reason / reason family;
- `signal_id` where applicable;
- transition/handoff metadata.

DecisionObject is auxiliary strategic context for payload/evidence. It cannot bypass FSM.

---

## 5. Stage handoff vs trade-execution readiness

These two truths are distinct.

### `stage_handoff_ready`
Means the accepted lifecycle stage may be released from FSM to Signal Engine.

It can be true for:
- PRE;
- CONFIRM;
- OPEN_NOW.

### `trade_execution_ready`
Means final trade-action semantics are operationally mature.

It must be false for PRE/CONFIRM.
It may be true only for accepted OPEN_NOW.

PRE/CONFIRM are not excluded from SignalEvent lifecycle merely because they are not trade-execution ready.

---

## 6. SignalEvent candidate construction

SignalEvent may be constructed only when all required conditions hold:
- actionable DecisionObject stage is PRE/CONFIRM/OPEN_NOW;
- stable `signal_id` exists according to lifecycle rules;
- FSM accepted exactly that requested stage;
- `stage_handoff_ready=true`;
- `accepted_stage == DecisionObject.stage`;
- payload can be built coherently from real evidence;
- no execution blocker prevents construction;
- identity/version/schema requirements are satisfied.

A transition event by itself is not proof of acceptance.

---

## 7. SignalEvent is not delivery

SignalEvent construction proves only that an internal engine-to-distribution candidate exists.

It does not prove or authorize:
- route selection;
- entitlement;
- destination resolution;
- publication;
- Telegram visibility;
- outcome registration;
- broker execution.

**SignalEvent construction alone must never be classified as `EMITTED`.**

---

## 8. Trade Physics ownership boundary

Trade Physics is upstream strategy truth.

Canonical ownership:
- Market Model supplies market/ATR/speed evidence;
- SR/Corridor supplies directional structural space;
- Time Model supplies directional time feasibility;
- Scoring/Trade Physics computes deterministic TPS;
- DecisionObject carries the immutable strategic snapshot;
- Signal Engine consumes/carries that snapshot downstream.

Signal Engine must not calculate or recalculate:
- `available_space`;
- `space_to_buffer_ratio`;
- `trade_space_margin_atr`;
- `directional_effective_speed`;
- `time_to_buffer_ratio`;
- `movement_stress`;
- TPS components S/T/P/V;
- deterministic `TPS`;
- `trade_success_probability`.

If runtime computes primary strategic TPS inside Signal Engine, that behavior is implementation drift requiring governed remediation against the active canon.

---

## 9. Trade Physics payload/evidence rule

When DecisionObject provides Trade Physics evidence, SignalEvent/execution evidence may carry a snapshot or stable reference including:
- deterministic `TPS`;
- TPS components;
- Trade Physics formula/version;
- feature schema version;
- corridor/time context;
- `trade_success_probability` only if a validated model produced it upstream;
- model/version/readiness metadata when probability exists.

Signal Engine must not fabricate missing Trade Physics fields.

Absence of a learned probability is valid when no validated model is ready.

---

## 10. Execution outcome families

Signal Engine execution truth must support:
- `EMITTED`;
- `NOT_EMITTED`;
- `BLOCKED`;
- `SKIPPED`;
- `FAILED`;
- `DEFERRED`.

These are not strategic outcomes, FSM outcomes, route outcomes, telemetry outcomes, or admin outcomes.

---

## 11. EMITTED

`EMITTED` requires downstream evidence that at least one authorized publication succeeded.

Required support:
- linked governed publication evidence;
- execution attempt correlation;
- signal/stage identity;
- at least one successful route publish result or canonically equivalent proof.

Insufficient:
- FSM acceptance;
- SignalEvent construction;
- route selection without publish success;
- publisher intent without success.

Route-by-route truth remains Distribution-owned.

---

## 12. NOT_EMITTED

`NOT_EMITTED` describes non-emission without technical failure or explicit blocker.

Examples:
- no execution-relevant candidate;
- readiness insufficient;
- coherent SignalEvent unavailable without technical exception;
- stage handoff not ready for a non-blocker reason.

It must not be confused with strategic REJECT, BLOCKED, FAILED, or DEFERRED.

---

## 13. BLOCKED

`BLOCKED` describes explicit rule/invariant prevention.

Examples:
- cooldown;
- focus/watchlist gating;
- duplicate prevention;
- policy guardrail;
- invariant blocker;
- applicable execution gate.

Blocker reason must be explicit.

---

## 14. SKIPPED

`SKIPPED` describes intentional flow non-continuation without technical failure.

Examples:
- opportunity superseded;
- window expired;
- branch intentionally not executed;
- higher-priority canonical flow took precedence.

---

## 15. FAILED

`FAILED` means intended execution-layer continuation failed technically.

Examples:
- candidate/payload construction exception;
- serialization failure;
- execution-layer infrastructure error;
- mandatory execution-evidence persistence failure when policy classifies it as execution failure.

---

## 16. DEFERRED

`DEFERRED` means a valid path/candidate exists but downstream execution is deliberately not yet invoked/activated.

Current pre-distribution remediation baseline:
- SignalEvent valid;
- Distribution intentionally disabled/not invoked;
- execution phase = PRE_DISTRIBUTION;
- outcome = DEFERRED;
- reason explicitly states that distribution is not enabled/invoked;
- destination state = `PRE_DISTRIBUTION_UNRESOLVED`.

DEFERRED is neither failure nor visibility.

---

## 17. Stage-specific handling

### PRE
May become SignalEvent candidate after exact-stage FSM acceptance. `trade_execution_ready=false`.

### CONFIRM
May become SignalEvent candidate after exact-stage FSM acceptance and lifecycle continuity validation. `trade_execution_ready=false`.

### OPEN_NOW
May become candidate only after lifecycle/focus/actionability validity and exact-stage FSM acceptance. `trade_execution_ready` may be true.

External publication for all stages remains Distribution-controlled.

---

## 18. Candidate payload semantic families

SignalEvent should carry or reference at minimum where applicable:
- signal identity;
- symbol;
- timeframe/context;
- lifecycle stage;
- direction;
- classical score summary;
- Trade Physics snapshot/reference;
- canonical buffer semantics;
- model/execution timing evidence;
- candle/setup correlation;
- schema/version metadata.

It must never invent unavailable values.

---

## 19. Execution gating

Before candidate construction/downstream handoff verify:
- exact-stage FSM acceptance;
- `stage_handoff_ready`;
- lifecycle and signal identity consistency;
- execution blockers;
- candidate schema coherence;
- duplicate protection;
- distribution authorization state before router invocation.

Failure of a condition must map to an explicit execution outcome/reason.

---

## 20. Duplicate/flood control

Engine-side protection may include:
- stage/candle duplicate suppression;
- signal uniqueness;
- repeated setup suppression;
- engine-owned cooldown/anti-flood controls.

Distribution dedup remains separate.

Duplicate suppression must be observable and preserve stable signal identity.

---

## 21. Relation to FSM

FSM owns exact operational stage acceptance/handoff.

Signal Engine must not reinterpret:
- no-op transition;
- cooldown transition;
- watchlist-full transition;
- duplicate transition;
- generic `accepted=true`

as stage release unless exact-stage handoff is explicit.

---

## 22. Relation to DecisionObject

DecisionObject is upstream strategic truth.

Signal Engine may consume it for:
- identity;
- stage/direction;
- timing;
- classical score;
- Trade Physics evidence;
- payload construction.

Signal Engine must not mutate DecisionObject or overwrite its strategic evidence.

---

## 23. Relation to Distribution

Distribution Router owns:
- route selection;
- entitlement;
- destination mapping;
- route state/publish/skip policy;
- route-level counters/dedup.

Signal Engine does not invent destination truth before routing.

---

## 24. Relation to Observability

The system must reconstruct:
- input FSM handoff;
- accepted/requested stage;
- SignalEvent availability;
- execution outcome and reason;
- whether routing began;
- publication evidence supporting EMITTED;
- upstream DecisionObject/Trade Physics snapshot reference.

Execution truth must not live only in a generic debug blob.

---

## 25. `signal_execution_result`

Event Schema must define dedicated `signal_execution_result` events.

They may represent:
- pre-distribution execution checkpoint;
- post-distribution execution result.

Same logical attempt is correlated by `execution_attempt_id` plus signal/stage identity.

It does not replace FSM or route events.

---

## 26. Minimum execution trace

For each material execution attempt preserve:
- `execution_attempt_id`;
- setup/signal correlation;
- signal id where applicable;
- symbol;
- timeframe/context;
- stage;
- execution phase;
- execution outcome;
- reason/blocker/failure detail;
- timestamp;
- destination state/context;
- candidate/payload reference where applicable;
- FSM handoff reference;
- DecisionObject/Trade Physics snapshot reference;
- publication evidence if outcome=EMITTED.

---

## 27. Truth-domain separation

Do not collapse:
- strategic PRE/CONFIRM/OPEN_NOW/REJECT/NO_SIGNAL;
- FSM operational outcome;
- Signal Engine execution outcome;
- Distribution route result;
- external visibility;
- telemetry market result;
- operational/admin outcome.

They are correlated, not merged.

---

## 28. Legacy event compatibility

Legacy `signal_emitted` is compatibility/history only for new v3 behavior.

New primary truths:
- `signal_execution_result` for Signal Engine;
- `route_publish_result` for route truth;
- `signal_stage_visible` for governed external visibility.

Historical records retain their original schema meaning.

---

## 29. Forbidden patterns

Forbidden:
- direct emission from score/TPS/expiry/DecisionObject;
- generic FSM transition used as implicit handoff;
- candidate construction treated as publication;
- EMITTED without downstream success evidence;
- PRE/CONFIRM excluded because trade-execution readiness is false;
- strategic mathematics recalculated in Signal Engine;
- Trade Physics calculated in Signal Engine;
- learned probability fabricated in Signal Engine;
- route truth invented before router;
- generic debug as sole execution evidence;
- broker execution activated implicitly.

---

## 30. Code alignment questions

Implementation must answer:
- what exact post-FSM handoff is consumed?
- where requested/accepted stage is validated?
- how handoff readiness differs from trade readiness?
- how PRE/CONFIRM/OPEN_NOW candidates are constructed?
- where duplicate protection occurs?
- how all execution outcomes are classified?
- how `signal_execution_result` is produced?
- how EMITTED is proven by publication evidence?
- where Trade Physics snapshot is consumed?
- how Signal Engine avoids recomputing TPS?

If these answers are unclear, alignment is incomplete.

---

## 31. Promotion and migration

Under the executed promotion:
- this v3 becomes the single signal-execution authority;
- v2 moves to superseded storage;
- active references are repaired atomically;
- FSM/Module Interface/Event Schema/Observability/Root/Master versions must be compatible;
- runtime remains unchanged until post-promotion re-audit.

---

## 32. Final principle

Signal Engine is a governed execution layer between FSM and Distribution.

It carries strategic evidence—including Trade Physics—but does not own or recalculate it. It constructs stage candidates only after exact FSM handoff, never confuses candidate construction with delivery, and preserves distinct execution truth until downstream publication evidence exists.
