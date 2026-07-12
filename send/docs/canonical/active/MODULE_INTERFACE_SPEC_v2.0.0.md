# MODULE_INTERFACE_SPEC_v2.0.0

Version: 2.0.0  
Status: Active Canonical  
Path: /opt/binarybot/docs/canonical/active/MODULE_INTERFACE_SPEC_v2.0.0.md

Linked Documents:
- SYSTEM_INVARIANTS_v2.0.0.md
- EVENT_SCHEMA_SPEC_v2.0.0.md
- DECISION_AUDIT_SPEC_v2.0.0.md
- SIGNAL_DISTRIBUTION_SPEC_v2.0.0.md
- OBSERVABILITY_LOGGING_SPEC_v2.0.0.md
- FAILURE_RECOVERY_SPEC_v2.0.0.md
- PERFORMANCE_ANALYTICS_SPEC_v2.0.0.md
- TELEGRAM_UX_v2.0.0.md
- STRATEGY_INTELLIGENCE_SYSTEM_v2.0.0.md
- AUTONOMOUS_STRATEGY_EVOLUTION_SYSTEM_v2.0.0.md

Depends on:
- SYSTEM_INVARIANTS_v2.0.0.md
- EVENT_SCHEMA_SPEC_v2.0.0.md
- SIGNAL_DISTRIBUTION_SPEC_v2.0.0.md
- OBSERVABILITY_LOGGING_SPEC_v2.0.0.md

Code Alignment:
- storage.py
- candle_adapter.py
- params_loader.py
- strategy_v2.py
- fsm_runtime.py
- signal_engine.py
- distribution_router.py
- telegram_publisher.py
- bot_service.py
- outcome_service.py
- observability_logger.py
- analytics_engine.py

## 0. Purpose

This document defines the canonical module contracts and cross-module boundaries for BinaryBot / DROPi Signals. Its role is to make implementation deterministic, debugging traceable, ownership explicit, and architecture resistant to hidden coupling.

This document does not define signal logic internals, presentation copy, or monetization rules in detail. It defines what each module is allowed to receive, produce, persist, and call.

## 1. Canonical Position

This document is the contract layer between strategy, state machine, distribution, Telegram UX, observability, outcome tracking, and analytics.

It exists to answer five questions:

1. What data objects are canonical across modules.
2. Which module owns each responsibility.
3. Which calls are allowed across boundaries.
4. Which persisted states are canonical sources of truth.
5. Which cross-layer accesses are forbidden.

If code behavior conflicts with this document, code must be aligned or this document must be updated canonically before further implementation proceeds.

## 2. Final Principle

No module may bypass its contract boundary in order to read hidden state, inject side effects, or duplicate ownership already assigned to another module.

A behavior is considered non-canonical if it introduces:
- hidden coupling
- duplicate ownership
- direct file access outside the persistence layer
- strategy logic inside UX or distribution modules
- tier policy inside Telegram abstraction
- analytics logic that mutates live-trading behavior

## 3. Global Shared Contracts

All modules must use one canonical shared schema family. Implementation may use dataclasses, typed dicts, pydantic-like models, or equivalent validated structures, but field names and semantics must remain canonically aligned.

### 3.1 Candle

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
- Candles passed to strategy must be newest-first.
- `candles[0]` is the newest candle.
- Candle normalization is owned by the market-data normalization layer, not by strategy.

### 3.2 DecisionObject

`DecisionObject`
- `kind: str` — `NO_SIGNAL | PRE | CONFIRM | OPEN_NOW | REJECT`
- `signal_id: str | None`
- `symbol: str`
- `timeframe: str`
- `direction: str | None` — `BUY | SELL`
- `score_total: float | None`
- `buffer_mode: str | None`
- `buffer_price: float | None`
- `expiry_minutes: int | None`
- `want_open_now: bool`
- `gates: dict`
- `debug: dict`
- `candle_ts: int`

Rules:
- DecisionObject is produced before FSM.
- If `kind` is `PRE`, `CONFIRM`, or `OPEN_NOW`, `signal_id` must exist and remain stable across lifecycle stages.
- `candle_ts` is mandatory for deduplication and traceability.
- `debug` must be structured and safe; no secrets, tokens, or privileged config leakage.

### 3.3 SignalEvent

`SignalEvent`
- `event_type: str`
- `stage: str`
- `signal_id: str`
- `symbol: str`
- `timeframe: str`
- `direction: str`
- `score_total: float`
- `buffer_mode: str`
- `buffer_price: float`
- `expiry_minutes: int`
- `candle_ts: int`
- `created_ts: int`
- `payload: dict`

Rules:
- SignalEvent is the canonical engine-to-distribution object.
- `stage` must match the originating decision stage.
- `payload` may be Telegram-ready semantically but must not contain Telegram markup responsibility.
- Publisher formatting belongs to the Telegram abstraction layer.

### 3.4 FSMState

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
- Watchlist size must remain within canonical invariant limits.
- Cooldown blocks all stage emission until expiry.
- FSM persistence must survive restart without semantic drift.

### 3.5 DistributionState

`DistributionState`
- `version: str`
- `last_reset_epoch: int`
- `tier_state: dict`
- `open_signals_today: dict`
- `dedup: dict`
- `last_updated_ts: int`

Rules:
- Only successful `OPEN_NOW` publish increments non-ELITE counters.
- Tier silence blocks PRE, CONFIRM, and OPEN_NOW publication.
- Reset schedule is owned by the distribution layer and must remain timezone-safe.

### 3.6 OutcomeVote

`OutcomeVote`
- `signal_id: str`
- `user_id: int`
- `outcome: str`
- `voted_ts: int`
- `expiry_minutes: int`
- `open_now_ts: int`

Rules:
- First valid vote wins per `(signal_id, user_id)`.
- Voting activates only after trade expiry.
- Aggregates may be public; identity linkage must remain private.

### 3.7 EventRecord

All observability events must match the event schema canon.

Minimum event families include:
- `engine_start`
- `engine_stop`
- `decision_evaluated`
- `fsm_transition`
- `signal_emitted`
- `tier_publish_result`
- `tier_reset`
- `user_outcome`
- `admin_change`
- `error`
- `warning`

## 4. Module Contracts

### 4.1 `storage.py`

Purpose: Atomic persistence layer for JSON and JSONL state.

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

### 4.2 `candle_adapter.py`

Purpose: Normalize raw market data into canonical candle objects.

Owns:
- feed normalization
- candle validation
- ordering guarantees

Required interface:
- `normalize(raw, symbol, timeframe)`
- `validate(candles)`

Forbidden:
- scoring logic
- tier routing
- state transitions

### 4.3 `params_loader.py`

Purpose: Load and validate strategy parameter configuration.

Owns:
- algo parameter loading
- required-key validation
- parameter checksum generation

Required interface:
- `load_algo_params(...)`
- `validate_algo_params(params)`
- `compute_checksum(params)`

Forbidden:
- trading execution
- Telegram actions
- dynamic hidden thresholds outside canonical config

### 4.4 `strategy_v2.py`

Purpose: Pure strategy decision engine.

Owns:
- gate evaluation
- scoring
- buffer decision
- expiry decision
- DecisionObject production

Required interface:
- `decide(candles_m1, candles_m5, params, buffer_mode, want_open_now, context) -> DecisionObject`

Canonical rules:
- no file I/O
- no Telegram access
- no direct persisted-state reads
- deterministic output for identical inputs

### 4.5 `fsm_runtime.py`

Purpose: Lifecycle state machine and invariant enforcement.

Owns:
- FSM state loading and saving
- transition application
- invariant enforcement
- lifecycle traceability

Required interface:
- `load_state()`
- `save_state(state)`
- `apply_transition(state, decision, now_ts)`
- `enforce_invariants(state)`

Canonical rules:
- OPEN_NOW may only occur where the strategy-state architecture permits it.
- cooldown blocks all stage release
- watchlist and focus invariants are mandatory

### 4.6 `signal_engine.py`

Purpose: Runtime orchestrator.

Owns:
- scan cadence
- strategy invocation
- FSM invocation
- SignalEvent construction
- engine-level dedup

Required interface:
- `run_once(now_ts)`
- `build_signal_event(decision, now_ts)`
- `global_dedup_check(symbol, candle_ts, stage)`
- `persist_dedup(symbol, candle_ts, stage)`

Canonical rules:
- engine emits SignalEvent objects
- engine does not own tier policy
- engine does not format Telegram messages

### 4.7 `distribution_router.py`

Purpose: Tier routing and publication decision layer.

Owns:
- channel configuration reads
- distribution state loading and saving
- daily reset logic
- tier dedup
- per-tier publish-or-skip decisions

Required interface:
- `load_config()`
- `load_state()`
- `save_state(state)`
- `maybe_daily_reset(state, now_ts)`
- `route(event, now_ts)`
- `tier_dedup_check(state, tier, signal_id, stage)`
- `tier_dedup_mark(state, tier, signal_id, stage)`

Forbidden:
- raw strategy scoring
- direct Telegram formatting policy
- hidden counter mutation outside canonical state

### 4.8 `telegram_publisher.py`

Purpose: Single Telegram transport abstraction.

Owns:
- send/edit/document transport calls
- Telegram error capture and return handling

Required interface:
- `send_message(chat_id, text, reply_markup, thread_id)`
- `edit_message(chat_id, message_id, text, reply_markup)`
- `send_document(chat_id, file_path, caption, thread_id)`

Forbidden:
- strategy decisions
- tier routing ownership
- analytics ownership

### 4.9 `bot_service.py`

Purpose: Operator UI, admin controls, command surface, docs viewer.

Owns:
- command handlers
- admin panel actions
- admin identity validation
- proof-triggering admin changes

Required interface includes command routing for:
- `/start`
- `/buffer`
- `/open`
- `/admin`

Canonical actions include:
- set buffer mode
- set active symbols
- read status views
- send canonical docs as files

Forbidden:
- scoring logic
- direct strategy mutation bypassing config/state ownership

### 4.10 `outcome_service.py`

Purpose: ELITE outcome workflow.

Owns:
- OPEN_NOW registration
- post-expiry vote activation
- vote callback handling
- per-signal aggregate computation

Required interface:
- `register_open_now(...)`
- `schedule_activation(signal_id)`
- `handle_vote_callback(user_id, signal_id, outcome, now_ts)`
- `compute_signal_stats(signal_id)`

Canonical rules:
- first valid vote wins
- voting only after expiry
- vote storage is append-only
- public outcome display must not expose user identities

### 4.11 `observability_logger.py`

Purpose: Structured event logging and proof emission.

Owns:
- schema-aligned event logging
- error/warning logging
- proof log generation
- optional admin proof mirroring

Required interface:
- `log_event(event)`
- `log_error(error)`
- `log_warning(warn)`
- `proof(kind, payload, now_ts)`

Final rule:
If an operationally relevant action is not logged, it is non-canonical from an audit perspective.

### 4.12 `analytics_engine.py`

Purpose: Derived research and performance layer.

Owns:
- aggregate recomputation
- funnel construction
- ranking derivation
- private per-user stats where allowed

Required interface:
- `recompute(now_ts)`
- `get_symbol_ranking(range_days)`
- `get_focus_history(range_days)`
- `get_funnel(range_days)`
- `get_user_stats(user_id, range_days)`

Forbidden:
- live-trading mutation
- hidden counters detached from source logs
- disclosure of another user’s private stats

## 5. Cross-Module Rules

### 5.1 No Layer Bleed

- `strategy_v2.py` must not call Telegram or persistence directly.
- `distribution_router.py` must not make strategy decisions.
- `bot_service.py` must not implement scoring logic.
- `analytics_engine.py` must not affect live trading decisions in real time.

### 5.2 One Source of Truth

Canonical ownership must remain singular:
- algo params -> config layer
- active symbols -> symbols state/config owner
- FSM -> FSM state owner
- distribution counters and silence -> distribution state owner
- outcomes -> outcome persistence owner
- observability -> event log owner

### 5.3 Dedup Ownership

- engine dedup belongs to `signal_engine.py`
- tier dedup belongs to `distribution_router.py`
- vote dedup belongs to `outcome_service.py`

No module may silently create competing dedup systems for the same semantic layer.

### 5.4 Restart Safety

All persisted states must survive restart without semantic drift.

This includes at minimum:
- cooldown continuity
- tier counter continuity
- dedup continuity or safe reconstruction
- linkage continuity between emitted signals and later outcome actions

## 6. Canonical Dependency Rules

1. Strategy produces DecisionObject.
2. FSM consumes DecisionObject and current FSM state.
3. Engine emits SignalEvent only after valid orchestration and dedup checks.
4. Distribution consumes SignalEvent and tier state.
5. Telegram publisher performs transport only.
6. Outcome service consumes published OPEN_NOW linkage and expiry context.
7. Observability records every material action.
8. Analytics derives from logs and persisted outcomes, not from hidden side channels.

## 7. Forbidden Patterns

The following are forbidden unless canonically redefined:
- strategy reading Telegram state
- Telegram layer deciding tier policy
- analytics mutating live engine decisions
- direct JSON writes outside `storage.py`
- duplicated state files for the same ownership domain
- bypassing event schema for operational events
- UI modules changing strategy thresholds without canonical config path

## 8. Code Alignment Expectations

The codebase should be auditable against this document along four dimensions:
- module ownership
- interface signature alignment
- persistence ownership
- forbidden cross-layer access absence

Any implementation patch that changes module responsibility must update this document or an explicitly linked canonical dependency first.

## 9. Implementation Guidance

Recommended implementation order:
1. `storage.py`
2. event schema enforcement
3. parameter loading and validation
4. FSM runtime
5. strategy core
6. engine orchestration
7. Telegram transport abstraction
8. distribution routing
9. bot/admin surface
10. outcome workflow
11. observability proof completeness
12. analytics derivation

This order is guidance, not permission to violate ownership rules.

## 10. Final Enforcement Rule

This document is authoritative for module boundaries, ownership, and interface-level architectural discipline.

When another document defines deeper behavior for one module family, that deeper document refines this one but may not violate the invariants and ownership rules defined here.

End of document.

## 5. Intelligence Pipeline Interface Boundary

This section absorbs bounded content from INTELLIGENCE_DATA_PIPELINE_DEFINITION.md.

### 5.1 Interface principle
Intelligence pipeline modules may read normalized evidence and emit bounded snapshots/aggregates for research and analytics surfaces.

### 5.2 Ownership rule
The pipeline consumes canonical evidence but does not become the source of truth for FSM lifecycle, routing, execution, or admin authority.

### 5.3 Expected outputs
Expected outputs may include derived aggregates, snapshot records, and bounded admin/research views.

## 6. Intelligence Module Map Compatibility

This section absorbs bounded content from INTELLIGENCE_FILES_AND_MODULE_MAP.md.

### 6.1 Module map role
The intelligence layer may be implemented through bounded modules for pipeline flow, aggregations, snapshots, and admin/research-facing views.

### 6.2 Compatibility rule
Implementation modules must remain compatible with active interface boundaries and may not create hidden ownership drift against runtime execution or FSM truth.

### 6.3 Growth rule
If the intelligence layer grows, module split is allowed only where canonical boundaries remain explicit and traceable.
