# MODULE_INTERFACE_SPEC.md
BinaryBot — Module Interface Specification
Version: 1.0.0
Status: Canonical

Linked Docs:
- ARCHITECTURE_CODE_MAPPING.md
- EVENT_SCHEMA_SPEC.md
- ALGO_SPEC.md
- FSM_SPEC.md
- TELEGRAM_UX.md
- SIGNAL_DISTRIBUTION_SPEC.md
- CHANNEL_CONFIG_SPEC.md
- OBSERVABILITY_LOGGING_SPEC.md
- SYSTEM_INVARIANTS.md
- PERFORMANCE_ANALYTICS_SPEC.md
- FAILURE_RECOVERY_SPEC.md
- PARAMS_REFERENCE.md
- CHECKLIST.md
- CHANGELOG.md

---

## 0) PURPOSE

This document defines the **strict module contracts** (interfaces) for BinaryBot.

Goal:
- Each module can be implemented independently.
- Debugging is deterministic.
- No hidden coupling between trading logic, distribution, UX, and analytics.

Rules:
- Modules communicate ONLY via:
  1) function calls with explicit typed payloads
  2) normalized internal events (SignalEvent, FSMTransition, etc.)
  3) persisted state files controlled by `storage.py`

Non-goals:
- This document does NOT define trading logic details (see ALGO_SPEC.md).
- This document does NOT define Telegram formatting details (see TELEGRAM_UX.md).
- This document does NOT define tier rules (see SIGNAL_DISTRIBUTION_SPEC.md).

---

## 1) GLOBAL DATA CONTRACTS (SHARED TYPES)

All modules must use a single shared schema set.
Implementation can be:
- dataclasses, pydantic-like models, or plain dicts validated by schema.
But the FIELD NAMES and SEMANTICS MUST MATCH.

### 1.1 Candle

Candle {
  symbol: str
  timeframe: str              # "M1" | "M5" | ...
  ts: int                     # epoch seconds (UTC)
  open: float
  high: float
  low: float
  close: float
  volume: float | None
}

Invariant:
- Candles are newest-first when passed to strategy (`candles[0]` is newest).

---

### 1.2 Decision (Strategy Output)

Decision {
  kind: str                   # "NO_SIGNAL" | "PRE" | "CONFIRM" | "OPEN_NOW" | "REJECT"
  signal_id: str | None       # required for PRE/CONFIRM/OPEN_NOW, null for NO_SIGNAL
  symbol: str
  timeframe: str              # canonical decision timeframe e.g. "M15"
  direction: str | None       # "BUY" | "SELL" (required for PRE/CONFIRM/OPEN_NOW)
  score_total: float | None   # 0..100 (required for PRE/CONFIRM/OPEN_NOW)
  buffer_mode: str | None     # "SMALL" | "MEDIUM" | "LARGE"
  buffer_price: float | None  # numeric buffer for entry
  expiry_minutes: int | None  # expiry duration for binary trade
  want_open_now: bool         # operator/engine gate
  gates: dict                 # gate_name -> GateResult
  debug: dict                 # safe structured debug fields (no secrets)
  candle_ts: int              # timestamp for dedup key
}

GateResult {
  ok: bool
  reason: str | None
  details: dict | None
}

Hard rules:
- If kind in {PRE, CONFIRM, OPEN_NOW} => signal_id MUST exist and be stable across stages.
- If kind == REJECT => signal_id may exist (preferred) OR be None (allowed). If exists, must be stable for lifecycle trace.
- `candle_ts` MUST be populated for dedup.

---

### 1.3 SignalEvent (Engine -> Distribution)

SignalEvent {
  event_type: str             # "SIGNAL_EVENT"
  stage: str                  # "PRE" | "CONFIRM" | "OPEN_NOW"
  signal_id: str
  symbol: str
  timeframe: str
  direction: str
  score_total: float
  buffer_mode: str
  buffer_price: float
  expiry_minutes: int
  candle_ts: int
  created_ts: int             # epoch seconds UTC
  payload: dict               # telegram-ready fields; no formatting here
}

Rules:
- SignalEvent stage must match Decision kind.
- SignalEvent must not contain Telegram-specific markup. Publisher formats it.

---

### 1.4 FSM State (Persisted)

FSMState {
  version: str
  mode: str                   # "WIDE_SCAN" | "FOCUS_MODE"
  watchlist: list[str]         # symbols in focus (max 2)
  per_symbol: dict             # symbol -> SymbolState
  last_updated_ts: int
}

SymbolState {
  state: str                  # "IDLE" | "WATCHLIST" | "LIVE_SENT" | "COOLDOWN"
  current_signal_id: str | None
  last_pre_candle_ts: int | None
  last_confirm_candle_ts: int | None
  last_open_candle_ts: int | None
  cooldown_until_ts: int | None
  focus_enter_ts: int | None
}

Invariant hooks:
- WATCHLIST size <= 2 at all times.
- COOLDOWN blocks all stages.

---

### 1.5 Distribution State (Persisted)

DistState {
  version: str
  last_reset_epoch: int
  tier_state: dict             # tier -> "ACTIVE"|"SILENT"
  open_signals_today: dict     # tier -> int
  dedup: dict                  # optional: tier -> {signal_id: {stage: bool}}
  last_updated_ts: int
}

Tiers:
- "FREE" | "BASIC" | "PRO" | "ELITE"

Rules:
- Only successful OPEN_NOW publish increments open_signals_today for non-ELITE tiers.
- SILENT blocks PRE/CONFIRM/OPEN_NOW for that tier.
- Reset at 08:10 Europe/London.

---

### 1.6 Outcome Vote (Elite Feedback)

OutcomeVote {
  signal_id: str
  user_id: int
  outcome: str                 # "WIN" | "LOSE" | "MISSED"
  voted_ts: int                # epoch seconds UTC
  expiry_minutes: int
  open_now_ts: int
}

Policy:
- LOCK: first write wins per (signal_id, user_id)
- Vote buttons only activate AFTER expiry.
- Vote window is finite (per TELEGRAM_UX.md; default expiry+5 minutes).
- After vote, buttons disappear for that user (via message edit / UI update).

---

### 1.7 Event Log Record (Observability)

All log events MUST match EVENT_SCHEMA_SPEC.md.
Minimum required event types:
- engine_start
- engine_stop
- decision_evaluated
- fsm_transition
- signal_emitted
- tier_publish_result
- tier_reset
- user_outcome
- admin_change
- error
- warning

---

## 2) MODULE INTERFACES (STRICT)

### 2.1 storage.py (Atomic Persistence)

Purpose:
- Single safe access layer for all JSON/JSONL persistence.
- Prevent corruption via atomic writes + file locks.

Required functions:

storage.load_json(path: str, default: dict|list|None) -> dict|list
storage.save_json_atomic(path: str, obj: dict|list) -> None

storage.append_jsonl(path: str, record: dict) -> None

storage.with_lock(lock_name: str) -> context_manager
  # lock_name examples: "focus_state", "dist_state", "settings", "active_symbols"

Hard rules:
- No module writes JSON files directly (must go via storage).
- JSON writes must be atomic (write temp + rename).
- JSONL is append-only.

---

### 2.2 candle_adapter.py (Market Data Normalization)

Purpose:
- Normalize external candle feed into Candle objects.

Required functions:

candle_adapter.normalize(raw: any, symbol: str, timeframe: str) -> list[Candle]
  - returns newest-first list

candle_adapter.validate(candles: list[Candle]) -> None
  - raises if ordering invalid or fields missing

Notes:
- Can be inside signal_engine.py if you prefer, but interface must exist logically.

---

### 2.3 params_loader.py (Config Loader + Validation)

Purpose:
- Load config/algo_params.json and validate against PARAMS_REFERENCE.md.

Required functions:

params_loader.load_algo_params(path="/opt/binarybot/config/algo_params.json") -> dict
params_loader.validate_algo_params(params: dict) -> None
params_loader.compute_checksum(params: dict) -> str

Rules:
- Missing keys => hard fail at startup (engine must stop).
- Hardcoded thresholds forbidden.

---

### 2.4 strategy_v2.py (Strategy Core - Pure Logic)

Purpose:
- Implements full decision logic (gates + scoring + buffer + expiry).

Required functions:

strategy_v2.decide(
  candles_m1: list[Candle],
  candles_m5: list[Candle],
  params: dict,
  buffer_mode: str,              # SMALL|MEDIUM|LARGE
  want_open_now: bool,
  context: dict                  # optional: trend context, session, etc.
) -> Decision

Hard rules:
- No Telegram calls.
- No file I/O.
- No reading global state files.
- Deterministic output for identical inputs.

---

### 2.5 fsm_runtime.py (Lifecycle State Machine)

Purpose:
- Applies lifecycle transitions and enforces invariants.

Required functions:

fsm_runtime.load_state() -> FSMState
fsm_runtime.save_state(state: FSMState) -> None

fsm_runtime.apply_transition(
  state: FSMState,
  decision: Decision,
  now_ts: int
) -> tuple[FSMState, dict]
  returns: (new_state, transition_info)

fsm_runtime.enforce_invariants(state: FSMState) -> None
  - raises or returns violation details

Required transition_info fields:
- symbol
- prev_state
- new_state
- trigger
- signal_id
- candle_ts

Rules:
- OPEN_NOW allowed only in FOCUS_MODE.
- COOLDOWN blocks all signals.
- Watchlist size <= 2.

---

### 2.6 signal_engine.py (Orchestrator Loop)

Purpose:
- Owns runtime scanning:
  - WIDE_SCAN: scan all selected symbols
  - FOCUS_MODE: allocate majority scanning to focus symbols, remainder to wide
- Calls strategy, calls FSM, emits SignalEvents.

Required functions:

signal_engine.run_once(now_ts: int) -> None
  - executes one engine tick

signal_engine.build_signal_event(decision: Decision, now_ts: int) -> SignalEvent

signal_engine.global_dedup_check(symbol: str, candle_ts: int, stage: str) -> bool
  - returns True if duplicate (block), False if new

signal_engine.persist_dedup(symbol: str, candle_ts: int, stage: str) -> None

Rules:
- The engine does NOT publish to Telegram tiers.
- The engine emits SignalEvents to distribution_router only.

Events emitted:
- decision_evaluated (always)
- fsm_transition (when state changes)
- signal_emitted (when PRE/CONFIRM/OPEN_NOW produced)

---

### 2.7 distribution_router.py (Tier Distribution)

Purpose:
- Route SignalEvents to tiers using CHANNEL_CONFIG + SIGNAL_DISTRIBUTION rules.
- Enforce silent mode, limits, reset schedule, tier dedup.

Required functions:

distribution_router.load_config() -> dict
  - reads config/channel_config.json (or env)

distribution_router.load_state() -> DistState
distribution_router.save_state(state: DistState) -> None

distribution_router.maybe_daily_reset(state: DistState, now_ts: int) -> tuple[DistState, bool]
  - returns (new_state, did_reset)

distribution_router.route(event: SignalEvent, now_ts: int) -> None
  - for each tier decides publish/skip

distribution_router.tier_dedup_check(state: DistState, tier: str, signal_id: str, stage: str) -> bool
distribution_router.tier_dedup_mark(state: DistState, tier: str, signal_id: str, stage: str) -> None

Rules:
- Tier missing channel_id => DISABLED tier (no publish, log critical).
- Only successful OPEN_NOW publish increments counters (non-ELITE).
- If tier is SILENT => publish nothing at all (PRE/CONFIRM/OPEN_NOW).
- Reset at 08:10 Europe/London (DST safe).
- Tier dedup key: (tier, signal_id, stage).

---

### 2.8 telegram_publisher.py (Telegram API Abstraction)

Purpose:
- Single module responsible for send/edit operations.

Required functions:

telegram_publisher.send_message(
  chat_id: int,
  text: str,
  reply_markup: dict | None,
  thread_id: int | None
) -> dict
  - returns Telegram API response (includes message_id)

telegram_publisher.edit_message(
  chat_id: int,
  message_id: int,
  text: str | None,
  reply_markup: dict | None
) -> dict

telegram_publisher.send_document(
  chat_id: int,
  file_path: str,
  caption: str | None,
  thread_id: int | None
) -> dict

Rules:
- All Telegram errors must be caught and returned/logged.
- Publisher must never decide tier policy or strategy.

---

### 2.9 bot_service.py (Commands + Admin Panel + Docs Viewer)

Purpose:
- UI and operator controls.

Required command handlers:

/start
/buffer
/open
/admin (panel)

Admin panel required actions:
- Set Buffer Mode (writes settings.json; emits admin_change + proof log)
- Set Symbols (writes active_symbols.json; emits admin_change + proof log)
- Status (reads focus_state + dist_state + settings)
- Docs Viewer (sends selected docs/*.md as .md file)

Docs viewer contract:
bot_service.send_doc(doc_name: str) -> None
- sends /opt/binarybot/docs/{doc_name}.md as file

Rules:
- Admin-only actions must validate ADMIN_USER_ID.
- Each admin change must emit:
  - observability admin_change event (JSONL)
  - proof message in admin proofs topic

---

### 2.10 outcome_service.py (ELITE Outcome Voting)

Purpose:
- Attach outcome workflow to each OPEN_NOW in ELITE.
- Collect votes, enforce LOCK policy, update aggregated stats.

Required functions:

outcome_service.register_open_now(
  signal_id: str,
  elite_chat_id: int,
  open_message_id: int,
  open_now_ts: int,
  expiry_minutes: int
) -> None
  - stores mapping so votes can be linked to the correct signal

outcome_service.schedule_activation(signal_id: str) -> None
  - activates buttons AFTER expiry

outcome_service.handle_vote_callback(
  user_id: int,
  signal_id: str,
  outcome: str,
  now_ts: int
) -> dict
  - returns result for UI feedback

outcome_service.compute_signal_stats(signal_id: str) -> dict
  - {win_count, lose_count, missed_count, total, percentages}

Hard rules:
- Voting only after trade expiry.
- Voting window finite (expiry + 5 minutes default).
- LOCK: first vote wins; ignore repeats silently or with short notice.
- After vote: buttons removed for that user (via message edit / UI update).
- Aggregated stats visible in channel; no user identities shown.
- Store votes append-only in outcomes/outcomes.jsonl.

---

### 2.11 observability_logger.py (Structured Events + Proof Logs)

Purpose:
- Central event emission for JSONL + optional admin topic mirrors.

Required functions:

observability_logger.log_event(event: dict) -> None
  - validates against EVENT_SCHEMA_SPEC.md

observability_logger.log_error(error: dict) -> None
observability_logger.log_warning(warn: dict) -> None

observability_logger.proof(
  kind: str,                      # "ADMIN_CHANGE"|"TIER_RESET"|"TIER_SILENT"|"PUBLISH"
  payload: dict,
  now_ts: int
) -> None
  - writes to admin_proofs.jsonl and posts summary to admin proof topic

Rules:
- If not logged, it does not exist.
- All module actions must have trace events.

---

### 2.12 analytics_engine.py (Performance + Research)

Purpose:
- Build research and performance metrics from logs and outcomes.

Required functions:

analytics_engine.recompute(now_ts: int) -> dict
  - reads observability/*.jsonl and outcomes/outcomes.jsonl
  - writes analytics/aggregates.json

analytics_engine.get_symbol_ranking(range_days: int) -> list[dict]
analytics_engine.get_focus_history(range_days: int) -> dict
analytics_engine.get_funnel(range_days: int) -> dict
analytics_engine.get_user_stats(user_id: int, range_days: int) -> dict
  - only for ELITE users, and must be private (DM)

Rules:
- Analytics must be derived from source logs (no hidden counters).
- Public results show aggregate only; private user stats only for that user.

---

## 3) CROSS-MODULE RULES (NO VIOLATION)

### 3.1 No Layer Bleed
- strategy_v2.py: no Telegram, no persistence
- distribution_router.py: no trading decisions
- bot_service.py: no scoring logic
- analytics_engine.py: no live trading impact

### 3.2 One Source of Truth
- algo params: config/algo_params.json
- symbols: active_symbols.json
- FSM: focus_state.json
- distribution: dist_state.json
- outcomes: outcomes/outcomes.jsonl
- logs: observability/*.jsonl

### 3.3 Deduplication Ownership
- engine dedup: signal_engine.py using (symbol + candle_ts + stage)
- tier dedup: distribution_router.py using (tier + signal_id + stage)
- vote dedup: outcome_service.py using (signal_id + user_id)

### 3.4 Restart Safety
All persisted states must survive restart without drift:
- cooldown must persist
- tier counters must persist
- dedup must persist or be safely reconstructable (preferred: persist last keys)

---

## 4) IMPLEMENTATION ORDER (RECOMMENDED)

1) storage.py
2) EVENT_SCHEMA_SPEC enforcement in observability_logger.py
3) params_loader.py + algo_params validation
4) fsm_runtime.py
5) strategy_v2.py
6) signal_engine.py
7) telegram_publisher.py
8) distribution_router.py
9) bot_service.py
10) outcome_service.py
11) analytics_engine.py

---

End of MODULE_INTERFACE_SPEC.md