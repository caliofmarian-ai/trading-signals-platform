# MODULE_INTERFACE_SPEC_v3.0.0

Version: 3.0.0  
Status: PROPOSED COMPLETE SUCCESSOR — NOT ACTIVE CANONICAL  
Path: /opt/binarybot/docs/canonical/proposed/MODULE_INTERFACE_SPEC_v3.0.0.md
Owner: BinaryBot / DROPi Signals
Scope: Canonical shared contracts, module ownership, cross-module boundaries, FSM-to-signal-engine handoff, SignalEvent construction boundary, distribution boundary, persistence and observability interfaces

Supersession Intent: MODULE_INTERFACE_SPEC_v2.0.0.md

Linked Documents:
- SYSTEM_INVARIANTS_v2.0.0.md
- CANONICAL_STRATEGY_STACK_v2.0.0.md
- FSM_DECISION_ENGINE_SPEC_v2.0.0.md
- SIGNAL_ENGINE_EXECUTION_SPEC_v3.0.0.md
- EVENT_SCHEMA_SPEC_v3.0.0.md
- DECISION_AUDIT_SPEC_v2.0.0.md
- SIGNAL_DISTRIBUTION_ARCHITECTURE_v2.0.0.md
- SIGNAL_DISTRIBUTION_SPEC_v2.0.0.md
- OBSERVABILITY_SPEC_v3.0.0.md
- OBSERVABILITY_LOGGING_SPEC_v3.0.0.md
- FAILURE_RECOVERY_SPEC_v2.0.0.md
- PERFORMANCE_ANALYTICS_SPEC_v2.0.0.md
- TELEGRAM_UX_v2.0.0.md
- STRATEGY_INTELLIGENCE_SYSTEM_v2.0.0.md
- AUTONOMOUS_STRATEGY_EVOLUTION_SYSTEM_v2.0.0.md

Depends on:
- SYSTEM_INVARIANTS_v2.0.0.md
- EVENT_SCHEMA_SPEC_v3.0.0.md
- SIGNAL_DISTRIBUTION_SPEC_v2.0.0.md
- OBSERVABILITY_LOGGING_SPEC_v3.0.0.md
- FSM_DECISION_ENGINE_SPEC_v2.0.0.md
- SIGNAL_ENGINE_EXECUTION_SPEC_v3.0.0.md

Code Alignment:
- storage.py
- candle_adapter.py
- params_loader.py
- strategy_v2.py
- fsm_runtime.py
- v2_fsm_orchestrator.py
- signal_engine.py
- signal_event.py
- signal_execution_gate.py
- distribution_router.py
- telegram_publisher.py
- bot_service.py
- outcome_service.py
- observability_logger.py
- analytics_engine.py

## 0. Authority and Promotion Status

This is a complete proposed successor. It is self-contained for the module-interface domain and does not require `MODULE_INTERFACE_SPEC_v2.0.0.md` to supply omitted normative rules.

Until explicit promotion, v2 remains active. Merge of this proposed file does not authorize runtime code changes, distribution activation, Telegram publication, outcome registration, broker execution, or scan-cadence changes.

## 1. Purpose

This document defines the canonical module contracts and cross-module boundaries for BinaryBot / DROPi Signals. Its role is to make implementation deterministic, debugging traceable, ownership explicit, and architecture resistant to hidden coupling.

It defines what each module is allowed to receive, produce, persist, and call. It does not redefine strategy mathematics, presentation copy, monetization, or route entitlement internals.

## 2. Canonical Position

This document is the contract layer between strategy, FSM, signal execution, distribution, Telegram UX, observability, outcome tracking, and analytics.

It answers:
1. Which data objects are canonical across modules.
2. Which module owns each responsibility.
3. Which calls are allowed across boundaries.
4. Which persisted states are canonical sources of truth.
5. Which cross-layer accesses are forbidden.
6. How exact-stage FSM handoff is represented before SignalEvent construction.

If code behavior conflicts with this document, code must be aligned only after the governing canonical change is active and re-audited.

## 3. Final Principle

No module may bypass its contract boundary to read hidden state, inject side effects, fabricate truth, or duplicate ownership assigned to another module.

Non-canonical patterns include:
- hidden coupling
- duplicate ownership
- direct file access outside persistence ownership
- strategy logic inside UX/distribution
- tier policy inside Telegram transport
- analytics mutating live trading
- FSM transition evidence treated as implicit SignalEvent permission
- SignalEvent construction treated as external publication

## 4. Global Shared Contracts

Implementation may use dataclasses, typed dicts, pydantic-like models, or equivalent validated structures, but field names and semantics must align with this contract and deeper linked specs.

### 4.1 Candle

`Candle`
- `symbol: str`
- `timeframe: str`
- `ts: int` — epoch seconds UTC
- `open: float`
- `high: float`
- `low: float`
- `close: float`
- `volume: float | None`

Rules:
- Candles passed to strategy are newest-first.
- `candles[0]` is newest.
- normalization is owned by market-data normalization, not strategy.

### 4.2 DecisionObject

`DecisionObject` must expose the canonical strategic semantics defined by its own active specification. Interface-level fields include at least:
- `kind: str` — `NO_SIGNAL | PRE | CONFIRM | OPEN_NOW | REJECT`
- `signal_id: str | None`
- `symbol: str`
- `timeframe: str`
- `direction: str | None` — `BUY | SELL`
- `score_total: float | None`
- `buffer_mode: str | None`
- `buffer_distance: float | None`
- `expiry_minutes: int | None` or governed model-expiry equivalent
- `want_open_now: bool`
- `gates: dict`
- `debug: dict`
- `candle_ts: int`

Compatibility:
- `buffer_price` may exist only as an explicitly documented legacy compatibility alias where runtime migration requires it.
- New canonical logic must use `buffer_distance` semantics rather than treating `buffer_price` as the primary structural field.

Rules:
- DecisionObject is produced before FSM.
- PRE/CONFIRM/OPEN_NOW require stable `signal_id`.
- `candle_ts` is mandatory where used for dedup/traceability.
- debug must be structured and secret-safe.
- execution truth must not exist only inside DecisionObject debug.

### 4.3 FSMExecutionHandoff

`FSMExecutionHandoff` is the canonical interface-level representation of exact-stage FSM release semantics.

Minimum fields:
- `requested_stage: str | None`
- `accepted_stage: str | None`
- `signal_id: str | None`
- `state_changed: bool`
- `reason: str`
- `reason_family: str | None`
- `transition_event: dict | None`
- `stage_handoff_ready: bool`
- `trade_execution_ready: bool`

Rules:
- `requested_stage` represents the actionable DecisionObject stage being evaluated.
- `accepted_stage` is populated only when that exact stage is operationally released.
- `stage_handoff_ready=true` only when `accepted_stage == requested_stage`, lifecycle/identity rules pass, and no blocker/suppression prevents release.
- `stage_handoff_ready` may be true for PRE, CONFIRM, or OPEN_NOW.
- `trade_execution_ready=false` for PRE and CONFIRM.
- `trade_execution_ready` may be true only for an accepted actionable OPEN_NOW.
- transition-event existence, state change, normal return, or generic accepted status are not substitutes for this contract.

### 4.4 SignalEvent

`SignalEvent` is the canonical signal-engine-to-distribution candidate object.

Interface-level fields include:
- `event_type: str`
- `stage: str` — PRE | CONFIRM | OPEN_NOW
- `signal_id: str`
- `symbol: str`
- `timeframe: str`
- `direction: str`
- `score_total: float`
- `buffer_mode: str`
- `buffer_distance: float`
- `expiry_minutes: int` or governed model-expiry representation
- `candle_ts: int`
- `created_ts: int`
- `payload: dict`

Compatibility:
- `buffer_price` may be exposed only as a legacy alias during controlled migration.

Rules:
- stage must equal `accepted_stage` from FSMExecutionHandoff.
- construction requires `stage_handoff_ready=true` for that same stage.
- payload may contain semantic delivery data but Telegram markup responsibility belongs to the publisher/UX boundary.
- SignalEvent creation does not confer route entitlement, destination selection, publication success, external visibility, outcome registration, or broker permission.
- SignalEvent creation is not `EMITTED` evidence.

### 4.5 FSMState

`FSMState`
- `version: str`
- `mode: str`
- `watchlist: list[str]`
- `per_symbol: dict`
- `last_updated_ts: int`

`SymbolState`
- `state: str`
- `current_signal_id: str | None`
- `last_pre_candle_ts: int | None`
- `last_confirm_candle_ts: int | None`
- `last_open_candle_ts: int | None`
- `cooldown_until_ts: int | None`
- `focus_enter_ts: int | None`

Rules:
- watchlist size respects invariants;
- cooldown blocks stage release until expiry;
- persistence survives restart without semantic drift;
- FSM state itself is not proof of external publication.

### 4.6 DistributionState

`DistributionState`
- `version: str`
- `last_reset_epoch: int`
- `tier_state: dict`
- `open_signals_today: dict`
- `dedup: dict`
- `last_updated_ts: int`

Rules:
- only successful OPEN_NOW publication may increment entitlement counters where the distribution canon says so;
- route silence blocks governed stages according to distribution policy;
- reset ownership remains distribution-layer and timezone-safe.

### 4.7 OutcomeVote

`OutcomeVote`
- `signal_id: str`
- `user_id: int`
- `outcome: str`
- `voted_ts: int`
- `expiry_minutes: int`
- `open_now_ts: int`

Rules:
- first valid vote wins per `(signal_id, user_id)`;
- voting activates only after expiry;
- public aggregates must not expose private identity linkage.

### 4.8 EventRecord

All observability events must match EVENT_SCHEMA canon.

Minimum families relevant across the system include:
- engine lifecycle events
- `decision_evaluated`
- `decision_promoted`
- `decision_rejected`
- `decision_no_signal`
- `fsm_transition`
- `signal_execution_result`
- `signal_stage_visible`
- `route_publish_attempt`
- `route_publish_result`
- outcome events
- admin change/proof events
- error/warning events

Legacy names such as `signal_emitted` or `tier_publish_result` may exist only under explicit compatibility/migration status; they are not substitutes for the v3 canonical truth domains.

## 5. Module Contracts

### 5.1 `storage.py`

Purpose: atomic persistence layer for JSON/JSONL state.

Owns:
- loading JSON state
- atomic JSON writes
- append-only JSONL writes
- lock-based critical sections

Required interface:
- `load_json(path, default)`
- `save_json_atomic(path, obj)`
- `append_jsonl(path, record)`
- `with_lock(lock_name)`

Forbidden:
- business logic
- strategy decisions
- Telegram publishing

### 5.2 `candle_adapter.py`

Purpose: normalize raw market data into canonical candles.

Owns feed normalization, validation, ordering guarantees.

Required interface:
- `normalize(raw, symbol, timeframe)`
- `validate(candles)`

Forbidden: scoring, routing, FSM transition ownership.

### 5.3 `params_loader.py`

Purpose: load and validate strategy parameter configuration.

Owns:
- parameter loading
- required-key validation
- checksum generation

Required interface:
- `load_algo_params(...)`
- `validate_algo_params(params)`
- `compute_checksum(params)`

Forbidden:
- trading execution
- Telegram actions
- hidden thresholds outside canonical config

### 5.4 `strategy_v2.py`

Purpose: pure strategy decision engine.

Owns:
- gate evaluation
- scoring
- buffer decision
- expiry decision
- DecisionObject production

Required interface concept:
- `decide(...) -> DecisionObject`

Rules:
- no Telegram
- no direct persisted-state reads
- no distribution ownership
- deterministic result for identical canonical inputs

### 5.5 `fsm_runtime.py` / FSM orchestration boundary

Purpose: lifecycle state machine, invariant enforcement, exact-stage operational handoff.

Owns:
- FSM state load/save
- transition application
- invariant enforcement
- lifecycle traceability
- stage acceptance/block/suppression semantics
- production of FSMExecutionHandoff semantics

Required interface concepts:
- `load_state()`
- `save_state(state)`
- `apply_transition(state, decision, now_ts)`
- `enforce_invariants(state)`
- a governed adapter/orchestrator that returns `FSMExecutionHandoff`

Rules:
- OPEN_NOW only through valid lifecycle path;
- cooldown blocks stage release;
- watchlist/focus invariants mandatory;
- no transition event automatically implies handoff;
- FSM does not construct SignalEvent or publish.

### 5.6 `signal_engine.py` / `signal_event.py` / execution gate boundary

Purpose: runtime orchestration and signal candidate execution boundary.

Owns:
- scan cadence
- strategy invocation
- FSM invocation
- consumption of FSMExecutionHandoff
- SignalEvent construction after exact-stage handoff
- engine-level dedup
- `signal_execution_result` production

Required interface concepts:
- `run_once(now_ts)`
- `build_signal_event(decision, handoff, now_ts)` or equivalent validated boundary
- engine dedup check/persist
- execution-result creation/logging

Rules:
- PRE/CONFIRM/OPEN_NOW candidate construction requires exact-stage `stage_handoff_ready=true`;
- `trade_execution_ready=false` on PRE/CONFIRM is not grounds to suppress their lifecycle candidate;
- SignalEvent is not publication evidence;
- engine does not own route policy or Telegram formatting;
- before routing, destination state is explicitly unresolved, not fabricated.

### 5.7 `distribution_router.py`

Purpose: route selection and publication decision layer.

Owns:
- channel configuration reads
- distribution state
- daily reset logic
- route/tier dedup
- entitlement
- publish-or-skip decisions
- destination resolution

Required interface:
- `load_config()`
- `load_state()`
- `save_state(state)`
- `maybe_daily_reset(state, now_ts)`
- `route(event, now_ts)`
- route/tier dedup operations

Forbidden:
- raw strategy scoring
- redefining FSM acceptance
- hidden counter mutation
- pretending route intent equals transport success

### 5.8 `telegram_publisher.py`

Purpose: single Telegram transport abstraction.

Owns send/edit/document transport calls and transport result/error capture.

Required interface:
- `send_message(...)`
- `edit_message(...)`
- `send_document(...)`

Forbidden:
- strategy decisions
- route policy ownership
- analytics ownership

Successful transport must be returned in a form that distribution observability can use as publication evidence.

### 5.9 `bot_service.py`

Purpose: operator UI, admin controls, commands, docs viewer.

Owns:
- command handlers
- admin panel actions
- admin identity validation
- proof-triggering admin changes

Forbidden:
- scoring logic
- direct strategy mutation bypassing config/state ownership
- bypassing distribution to publish trading stages

### 5.10 `outcome_service.py`

Purpose: outcome workflow.

Owns:
- eligible OPEN_NOW registration after governed publication boundary
- post-expiry activation
- vote handling
- aggregate computation

Required interface:
- `register_open_now(...)`
- `schedule_activation(signal_id)`
- `handle_vote_callback(...)`
- `compute_signal_stats(signal_id)`

Rules:
- do not register merely because an internal SignalEvent was constructed;
- outcome linkage requires the publication/lifecycle proof defined by outcome canon;
- first valid vote wins;
- public display protects identities.

### 5.11 `observability_logger.py`

Purpose: structured event logging and proof emission.

Owns:
- schema-aligned event logging
- error/warning logging
- proof generation
- execution-result persistence
- optional admin proof mirroring

Required interface:
- `log_event(event)`
- `log_error(error)`
- `log_warning(warn)`
- `proof(kind, payload, now_ts)`

Material strategy/FSM/execution/distribution actions require observable evidence according to their own specs.

### 5.12 `analytics_engine.py`

Purpose: derived research/performance layer.

Owns:
- aggregate recomputation
- funnel construction
- rankings
- permitted private stats

Required interface:
- `recompute(now_ts)`
- ranking/funnel/stats readers

Forbidden:
- live trading mutation
- hidden counters detached from source evidence
- private-data leakage

## 6. Cross-Module Rules

### 6.1 No Layer Bleed
- strategy must not call Telegram/persistence directly;
- FSM must not construct/publish SignalEvent;
- signal engine must not own route entitlement;
- distribution must not decide strategy validity;
- Telegram transport must not decide tier policy;
- analytics must not mutate live engine decisions.

### 6.2 One Source of Truth
- strategy truth -> DecisionObject
- lifecycle/operational release -> FSM / FSMExecutionHandoff
- execution truth -> signal engine / signal_execution_result
- route/publication truth -> distribution + publisher evidence
- external visibility -> governed visibility event
- outcomes -> outcome persistence
- analytics -> derived evidence only

### 6.3 Dedup Ownership
- engine/stage dedup -> signal engine
- route/tier dedup -> distribution router
- vote dedup -> outcome service

No competing hidden dedup system may own the same semantic boundary.

### 6.4 Restart Safety
Persisted states must survive restart without semantic drift, including cooldown, lifecycle identity, distribution counters, dedup, and published-signal linkage.

### 6.5 Fail-Closed Handoff
The following alone are insufficient for SignalEvent construction:
- transition_event exists
- state_changed=true
- function returns normally
- DecisionObject is actionable
- generic accepted flag

Only exact-stage `stage_handoff_ready=true` with accepted_stage matching requested_stage permits candidate construction.

## 7. Canonical Dependency Rules

1. Strategy produces DecisionObject.
2. FSM consumes DecisionObject and state, then produces exact-stage handoff semantics.
3. Signal engine consumes FSMExecutionHandoff and may build SignalEvent only after valid release/dedup.
4. Signal engine emits `signal_execution_result` for execution truth.
5. Distribution consumes SignalEvent and route state.
6. Publisher performs transport only.
7. Outcome service consumes governed publication/lifecycle linkage.
8. Observability records material truth domains without conflation.
9. Analytics derives from recorded evidence and outcomes.

## 8. Forbidden Patterns

Forbidden unless canonically redefined:
- strategy reading Telegram state
- Telegram deciding route/tier policy
- analytics mutating live engine decisions
- direct JSON writes outside storage ownership
- duplicate state ownership
- bypassing event schema
- UI changing strategy thresholds outside canonical control path
- DecisionObject -> SignalEvent without FSM handoff
- transition_event -> SignalEvent implicitly
- SignalEvent -> Telegram bypassing distribution
- SignalEvent construction == EMITTED
- PRE/CONFIRM lifecycle suppression solely because trade_execution_ready=false

## 9. Code Alignment Expectations

The codebase must be auditable on:
- module ownership
- shared field semantics
- interface signatures/adapters
- persistence ownership
- explicit truth-domain boundaries
- absence of forbidden cross-layer calls
- stable signal identity across lifecycle
- event-schema compliance

## 10. Implementation Guidance

Recommended implementation order after active canonical promotion and re-audit:
1. shared schema/event validation
2. FSM handoff model/adapter
3. signal-engine handoff consumption
4. SignalEvent candidate construction for all accepted stages
5. execution-result observability
6. no-distribution regression validation
7. only in a later separately governed phase, distribution activation
8. publisher proof integration
9. outcomes/analytics validation

This guidance does not authorize code before promotion.

## 11. Intelligence Pipeline Interface Boundary

Intelligence pipeline modules may read normalized evidence and emit bounded snapshots/aggregates for research and analytics surfaces.

They consume canonical evidence but do not become the source of truth for FSM lifecycle, execution, routing, or admin authority.

Expected outputs may include derived aggregates, snapshot records, and bounded admin/research views.

## 12. Intelligence Module Map Compatibility

The intelligence layer may be implemented through bounded modules for pipeline flow, aggregations, snapshots, and research/admin views.

Implementation modules must remain compatible with active interface boundaries and may not create hidden ownership drift against runtime execution or FSM truth.

If the intelligence layer grows, module splitting is allowed only where canonical boundaries remain explicit and traceable.

## 13. Promotion and Migration Rule

At promotion:
- v3 becomes the sole active module-interface authority;
- v2 moves to `canonical/superseded` with explicit traceability;
- all active references to v2 must be repaired atomically;
- SignalEvent terminology must be reconciled with the active code contract only after promotion;
- runtime schema/code remain unchanged until post-promotion canonical re-audit authorizes implementation.

## 14. Final Enforcement Rule

This document is the complete proposed authority for module boundaries, ownership, and interface-level discipline.

Deeper subsystem specs may refine their own behavior but may not violate the ownership and separation rules here.

End of document.