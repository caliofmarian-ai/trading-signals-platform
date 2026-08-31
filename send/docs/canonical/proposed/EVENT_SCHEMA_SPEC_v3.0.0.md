# EVENT_SCHEMA_SPEC_v3.0.0.md

BinaryBot — Canonical Event Envelope, Correlation & Domain Schema Specification  
Version: 3.0.0  
Status: PROPOSED CANONICAL REPLACEMENT — OWNER REVIEW REQUIRED  
Proposed Path: `send/docs/canonical/proposed/EVENT_SCHEMA_SPEC_v3.0.0.md`  
Intended Active Path After Promotion: `send/docs/canonical/active/EVENT_SCHEMA_SPEC_v3.0.0.md`  
Owner: BinaryBot / DROPi Signals  
Governance Change: `CHANGE_ID 20260831-01`  
Supersedes upon promotion: `EVENT_SCHEMA_SPEC_v2.0.0.md`

---

## 0. PROPOSAL STATUS AND PRESERVATION RULE

This document is a proposed replacement and is not active canonical truth until promoted through governance.

The purpose of v3.0.0 is to close the post-FSM signal-execution observability gap discovered during the canonical audit of PR #73 after PR #72.

All valid v2.0.0 principles, event families, privacy rules, correlation rules, distribution rules, outcome rules, admin/control rules, integrity rules and storage compatibility rules remain preserved unless this document explicitly changes or clarifies them.

Promotion must preserve the substantive v2.0.0 contract while applying the v3.0.0 changes defined here.

No runtime code change is authorized by this proposed document.

---

## 1. AUTHORITY AND SCOPE

This specification is the canonical schema contract for structured BinaryBot events once promoted.

It governs:
- the common event envelope;
- cross-domain correlation;
- canonical event-family naming;
- required and optional semantic fields;
- execution-outcome representation;
- privacy and integrity constraints;
- minimum payload obligations by observability domain;
- migration from legacy/generic event names.

It does not define:
- strategy mathematics;
- FSM transition policy itself;
- distribution entitlement policy;
- Telegram presentation;
- storage backend selection;
- broker execution.

Linked authority includes:
- `OBSERVABILITY_SPEC_v2.0.0.md` — observability policy/architecture authority;
- proposed `OBSERVABILITY_LOGGING_SPEC_v3.0.0.md` — logging mechanics;
- proposed `MODULE_INTERFACE_SPEC_v3.0.0.md` — cross-module contracts;
- `SIGNAL_ENGINE_EXECUTION_SPEC_v2.0.0.md` — execution outcome and delivery-trace authority;
- `FSM_DECISION_ENGINE_SPEC_v1.0.0.md` — FSM semantic authority;
- `SIGNAL_DISTRIBUTION_ARCHITECTURE_v2.0.0.md` — distribution topology authority;
- `SIGNAL_DISTRIBUTION_SPEC_v2.0.0.md` — entitlement/delivery policy authority;
- `SYSTEM_INVARIANTS_v2.0.0.md` — non-negotiable invariants.

---

## 2. CORE PRINCIPLES

1. Every materially relevant event must be structurally representable.
2. Every event must be reconstructable in context.
3. No silent governed-state mutation is allowed.
4. No ambiguous signal identity is allowed across a lifecycle.
5. Strategy truth, FSM truth, signal-execution truth and distribution truth must remain semantically separate.
6. Schema must support forensic reconstruction, analytics and governance.
7. Schema must not leak secrets or unnecessary personal data.
8. Schema evolution requires explicit versioning and migration discipline.
9. Schema-invalid events are not trustworthy canonical evidence.
10. A generic debug blob must not replace a required canonical semantic event family.

---

## 3. CANONICAL TRUTH-LAYER SEPARATION

The canonical event chain is:

`Strategy evaluation -> DecisionObject evidence -> FSM evidence -> Signal execution evidence -> Distribution evidence -> External visibility evidence -> Outcome/reconciliation evidence`

The following boundaries are mandatory:

- `decision_evaluated`, `decision_promoted`, `decision_rejected`, `decision_no_signal` describe strategy/decision truth.
- `fsm_transition` describes FSM/state truth.
- `signal_execution_result` describes signal-engine execution truth after FSM.
- `route_publish_attempt` and `route_publish_result` describe distribution-route truth.
- `signal_stage_visible` describes proven externally visible signal-stage truth.
- outcome events describe downstream outcome/reconciliation truth.

No one event may silently collapse these distinct authorities into one opaque representation.

---

## 4. COMMON EVENT ENVELOPE

All canonical events must preserve the v2 common envelope.

### 4.1 Required fields

- `event_id: string`
- `event_type: string`
- `schema_version: string` — `3.0.0` for events governed by this schema
- `ts_utc: string` — ISO 8601 UTC with `Z`
- `ts_epoch_ms: integer`
- `service: string`
- `env: string`
- `run_id: string`
- `source: object`
- `host: object`

`source` minimum:
- `module: string`
- `function: string`
- `line: integer` optional

`host` minimum:
- `hostname: string`
- `pid: integer`
- `app_version: string`
- `git_sha: string` optional

### 4.2 Recommended fields

- `ts_local`
- `trace_id`
- `severity`
- `algo` metadata where relevant

### 4.3 Correlation-capable fields

As applicable:
- `setup_correlation_id`
- `signal_id`
- `candidate_id`
- `decision_audit_id`
- `execution_attempt_id`
- `symbol`
- `direction`
- `timeframe`
- `candle_ts_utc`
- `candle_ts_epoch`
- `stage`
- `route`
- `destination_id`
- `destination_class`
- `message_id`
- `thread_id`
- `user_id`
- `admin_actor_id`

An event must carry enough context to be interpreted without guessing.

---

## 5. CANONICAL EVENT FAMILIES

### 5.1 System lifecycle
- `engine_start`
- `engine_stop`
- `recovery_started`
- `recovery_completed`
- `dependency_degraded`
- `config_load_error`

### 5.2 Decision / strategy
- `decision_evaluated`
- `decision_promoted`
- `decision_rejected`
- `decision_no_signal`

### 5.3 FSM / state
- `fsm_transition`

### 5.4 Signal lifecycle / execution
- `signal_execution_result` — NEW in v3.0.0
- `signal_emitted`
- `signal_stage_visible`
- `signal_closed`
- `duplicate_suppressed`

### 5.5 Distribution / route governance
- `route_publish_attempt`
- `route_publish_result`
- `route_reset`
- `route_state_changed`
- `route_mapping_invalid`

### 5.6 Outcome / reconciliation
- `outcome_submission_attempt`
- `outcome_submission_result`
- `outcome_reconciled`
- `membership_verification_failed`

### 5.7 Admin / control
- `admin_change`
- `guarded_action_review`
- `feature_toggle_changed`

### 5.8 Warning / anomaly / error
- `warning`
- `anomaly`
- `error`
- `invariant_breach`

---

## 6. BASELINE ENUMS

### 6.1 Signal stage
- `PRE`
- `CONFIRM`
- `OPEN_NOW`

### 6.2 Decision result
- `PRE`
- `CONFIRM`
- `OPEN_NOW`
- `REJECT`
- `NO_SIGNAL`

### 6.3 Execution outcome — NEW explicit schema family
- `EMITTED`
- `NOT_EMITTED`
- `BLOCKED`
- `SKIPPED`
- `FAILED`
- `DEFERRED`

These describe signal-engine execution outcome, not strategy decision result, FSM state, or per-route publish result.

### 6.4 FSM-to-engine stage disposition
For correlation with the module-interface contract:
- `ACCEPTED`
- `DUPLICATE_SUPPRESSED`
- `BLOCKED`
- `REJECTED`
- `NOT_ACTIONABLE`

### 6.5 Route state
- `ACTIVE`
- `SILENT`
- `DISABLED`

### 6.6 Publish result
- `PUBLISHED`
- `SKIPPED_SILENT`
- `SKIPPED_LIMIT`
- `SKIPPED_DISABLED`
- `FAILED`
- `DUPLICATE_SUPPRESSED`

### 6.7 Outcome
- `WIN`
- `LOSE`
- `MISSED`

### 6.8 Severity
- `INFO`
- `WARN`
- `ERROR`
- `CRITICAL`

---

## 7. SIGNAL IDENTITY AND CORRELATION RULES

1. Every event has a globally unique `event_id`.
2. Every materially relevant setup must preserve a `setup_correlation_id` or an explicitly equivalent canonical identifier across the layers needed for reconstruction.
3. The same trade idea must preserve one stable `signal_id` across PRE, CONFIRM, OPEN_NOW, signal-execution events, distribution events and outcome/reconciliation where applicable.
4. `trace_id` should connect events belonging to the same logical runtime flow.
5. `execution_attempt_id` must identify each materially relevant signal-engine execution attempt.
6. Direction/side must remain correlatable for a materially relevant setup and execution attempt.
7. A `signal_execution_result` must be linkable backward to the post-FSM handoff and forward to route events when distribution occurs.
8. Missing contextual sufficiency is a schema-quality failure even when JSON is syntactically valid.

---

## 8. DECISION EVENT CONTRACT

### 8.1 `decision_evaluated`

Purpose: preserve pre-FSM strategy truth after evaluation.

Minimum context:
- setup correlation id or canonical equivalent;
- symbol;
- direction/side where a directional candidate exists;
- timeframe;
- candle/evaluation timestamp.

Payload should include as applicable:
- `decision_result`;
- `score_total`;
- `buffer_mode`;
- model expiry/timing context;
- gates;
- structured strategy evidence;
- decision-object reference or structured representation;
- dedup/correlation context.

It must not be used as the canonical container for post-FSM execution outcome.

### 8.2 `decision_promoted`

Used when strategy truth is PRE, CONFIRM or OPEN_NOW before FSM operational acceptance is claimed.

A strategy promotion is not proof that FSM accepted the stage and not proof that a SignalEvent exists.

### 8.3 `decision_rejected`

Must preserve explicit rejection class/reason and relevant gate evidence.

### 8.4 `decision_no_signal`

Used when evaluation completes with no actionable signal and without a stronger rejection classification.

---

## 9. FSM EVENT CONTRACT

### 9.1 `fsm_transition`

Must preserve enough evidence to reconstruct:
- prior state;
- resulting state;
- trigger/reason;
- reason family where available;
- execution readiness where relevant;
- degradation/rejection status where relevant;
- explanation snippets where relevant;
- signal identity where applicable;
- setup correlation and direction where applicable;
- stage/request context where applicable;
- invariant/suppression context;
- persistence evidence where relevant.

A transition event existing by itself is not proof that a requested PRE/CONFIRM/OPEN_NOW stage was accepted for SignalEvent construction.

The FSM-to-engine acceptance contract is governed by `MODULE_INTERFACE_SPEC_v3.0.0.md` after promotion.

---

## 10. `signal_execution_result` — NEW CANONICAL EVENT FAMILY

### 10.1 Purpose

`signal_execution_result` records the signal engine's materially relevant execution verdict after the mandatory FSM boundary.

It exists specifically so that `NOT_EMITTED`, `BLOCKED`, `SKIPPED`, `FAILED` and `DEFERRED` do not have to be misrepresented as:
- strategy decisions;
- FSM states;
- emitted signals;
- distribution results.

### 10.2 Required correlation/context

Minimum required for every materially relevant execution attempt:
- `execution_attempt_id`;
- `setup_correlation_id` or explicitly equivalent canonical setup identifier;
- `symbol`;
- `direction` / side where the setup is directional;
- `timeframe` or equivalent temporal context;
- evaluation/candle context;
- `stage` for actionable-stage attempts;
- trace/run context from the common envelope.

Additionally:
- `signal_id` is required for governed PRE/CONFIRM/OPEN_NOW lifecycle attempts;
- for non-actionable decisions where no governed signal identity exists, `signal_id` may be absent, but setup correlation must remain sufficient.

### 10.3 Required payload

- `execution_outcome`: one of `EMITTED | NOT_EMITTED | BLOCKED | SKIPPED | FAILED | DEFERRED`;
- `reason`: non-empty semantic reason;
- `fsm_outcome`: explicit post-FSM outcome/state semantics;
- `fsm_reason_family`: semantic reason family;
- `fsm_execution_readiness`: boolean;
- `fsm_degraded`: boolean;
- `fsm_rejected`: boolean;
- `fsm_handoff_disposition`: post-FSM disposition;
- `fsm_handoff_reason`: post-FSM reason;
- `destination_class`: explicit destination/channel class;
- `payload_status`: whether a canonical SignalEvent/payload exists;
- `distribution_authorized`: boolean;
- `distribution_attempted`: boolean.

Explanation snippets must be available directly or by a correlated FSM evidence reference when needed to explain the verdict.

### 10.4 Destination rule

The delivery-trace requirement applies even before concrete route selection.

If distribution has not been reached or is intentionally disabled, `destination_class` must use an explicit semantic value such as:
- `UNRESOLVED_PRE_DISTRIBUTION`
- `DISTRIBUTION_DISABLED`

It must not be silently omitted when the execution trace is intended to satisfy the canonical delivery-trace contract.

Concrete route and destination identifiers belong to route-level events once routing occurs.

### 10.5 Payload/reference rule

The event must include at least one of:
- validated `SignalEvent` reference/representation;
- payload reference;
- payload version plus reference;
- explicit `payload_status=UNAVAILABLE` with reason when no coherent payload can be produced.

No fabricated market value or synthetic payload may be created merely to satisfy logging.

### 10.6 Outcome semantics

- `EMITTED`: may only be recorded when the canonical execution contract has reached its governed emission-success boundary. During the current remediation phase, external distribution is disabled, so this outcome is not expected from accepted PRE/CONFIRM/OPEN_NOW candidates.
- `NOT_EMITTED`: no emission occurred without implying a technical failure.
- `BLOCKED`: an explicit operational/policy/invariant guard prevented execution.
- `SKIPPED`: flow logic intentionally skipped execution, including duplicate/suppression semantics where appropriate.
- `FAILED`: execution was intended but failed technically or because a required execution artifact could not be formed under the approved contract.
- `DEFERRED`: execution is intentionally held for a later governed condition, including accepted SignalEvent creation while distribution remains disabled.

### 10.7 Separation rule

`signal_execution_result` does not replace:
- decision events;
- FSM events;
- route publish events;
- `signal_stage_visible`;
- outcome events.

---

## 11. SIGNAL LIFECYCLE EVENTS

### 11.1 `signal_emitted`

This event must not be used merely because a `SignalEvent` candidate object was constructed.

It represents governed emission under the active signal-execution contract and must be correlated to the execution result that allowed it.

Minimum context:
- setup correlation id;
- signal_id;
- symbol;
- direction;
- timeframe;
- stage;
- candle/evaluation context.

Payload should include:
- score_total;
- buffer mode/value semantics;
- expiry/timing semantics;
- engine mode where relevant;
- dedup context;
- execution attempt reference.

### 11.2 `signal_stage_visible`

Used only when a lifecycle stage becomes externally visible through governed delivery.

Must include or correlate:
- signal_id;
- stage;
- route;
- destination_id;
- message_id where successful;
- visibility result.

### 11.3 `signal_closed`

Preserves operational lifecycle close evidence.

---

## 12. DISTRIBUTION EVENT CONTRACTS

The v2 route-event semantics remain preserved.

### 12.1 `route_publish_attempt`

Minimum context:
- route;
- signal_id;
- stage;
- destination_id.

Must include route state, counter/limit context, destination mapping status and dedup evidence.

### 12.2 `route_publish_result`

Must include:
- publish result;
- route state before/after;
- counters before/after;
- counted flag;
- transport result;
- dedup object;
- reason where relevant.

### 12.3 Route reset/state/mapping events

`route_reset`, `route_state_changed` and `route_mapping_invalid` remain canonical with v2 semantics preserved.

---

## 13. DEDUPLICATION RULES

Preserved canonical baselines:
- engine-side: `symbol + candle context + stage` or stricter canonical equivalent;
- distribution-side: `route + signal_id + stage`.

Every dedup-relevant path must record:
- dedup key/class;
- duplicate detection result;
- action taken.

A duplicate/suppressed actionable stage must not create a second distribution candidate.

---

## 14. COUNTER / ENTITLEMENT INTEGRITY

Only successful OPEN_NOW publication to a limited governed route may consume entitlement.

SignalEvent construction or `signal_execution_result=DEFERRED` must never consume route entitlement.

---

## 15. PRIVACY AND DATA MINIMIZATION

Preserved hard rules:
- no secrets;
- no tokens;
- no API keys;
- no raw credentials;
- no unnecessary personal data;
- no public exposure of user-identifiable data.

Operational numeric IDs may exist only in governed observability paths where required.

---

## 16. STORAGE / PERSISTENCE COMPATIBILITY

Append-oriented structured storage remains acceptable.

The schema does not require specific filenames or one storage backend, but storage must preserve:
- reconstruction;
- domain meaning;
- event identity;
- correlation;
- append/history integrity.

---

## 17. SCHEMA EVOLUTION AND LEGACY EVENT MIGRATION

### 17.1 Version rule

Events governed by v3.0.0 use `schema_version=3.0.0` unless a documented compatibility adapter explicitly preserves an older envelope during migration.

### 17.2 Legacy/generic runtime names

The following current runtime families are not the target canonical v3 source of truth:
- `decision`;
- `signal_event`;
- `tier_publish`;
- `tier_reset`.

They may exist only as explicitly documented transitional compatibility aliases while consumers migrate.

They must not redefine canonical semantics.

Canonical targets include:
- `decision_evaluated` / `decision_promoted` / `decision_rejected` / `decision_no_signal`;
- `signal_execution_result`;
- `signal_emitted` where emission really occurred;
- `route_publish_attempt` / `route_publish_result` / `route_reset`.

### 17.3 Runtime validator rule

`send/schema/event_schema.json` must be aligned to this contract only after this document is promoted into the active canonical set.

Code must not pre-empt canonical promotion.

---

## 18. INTEGRITY RULES

1. Setup correlation is sufficient to reconstruct every materially relevant setup across applicable layers.
2. Signal identity remains stable across one trade idea.
3. Direction/side remains correlatable across the applicable decision/FSM/execution chain.
4. Strategy, FSM, execution and distribution truth remain separate.
5. Dedup is observable.
6. Governed state mutation is reconstructable.
7. Entitlement mutation is provable.
8. Persisted evidence is not silently rewritten.
9. Schema-invalid events are not trusted as canonical evidence.
10. A stage that was blocked or suppressed cannot be represented as an accepted SignalEvent candidate.
11. OPEN_NOW candidacy is not successful delivery.
12. No externally visible stage may lack corresponding structured upstream and distribution evidence.

---

## 19. V3 MIGRATION SUMMARY

v3.0.0 preserves the v2 event-envelope, correlation, privacy, distribution, outcome, admin, anomaly and integrity foundations while adding the missing canonical execution layer.

The principal changes are:
- new `signal_execution_result` family;
- explicit execution-outcome enum;
- explicit FSM semantic output and handoff-disposition correlation;
- explicit setup-correlation and direction requirements;
- explicit destination/payload trace semantics before route selection;
- strict separation of strategy/FSM/execution/distribution truths;
- migration rule away from generic runtime `decision`/`signal_event`/`tier_*` families as hidden authority.

---

## 20. PROMOTION GATE

This proposed document may move to `canonical/active` only when:
- Owner review confirms the v3 semantic contract;
- `OBSERVABILITY_LOGGING_SPEC_v3.0.0.md` is consistent with it;
- `MODULE_INTERFACE_SPEC_v3.0.0.md` is consistent with it;
- the authoritative master index is prepared for the promoted filenames;
- supersession/reference-repair handling is defined;
- no runtime code change is bundled into the canonical promotion.

Until then, `EVENT_SCHEMA_SPEC_v2.0.0.md` remains the active event-schema authority.
