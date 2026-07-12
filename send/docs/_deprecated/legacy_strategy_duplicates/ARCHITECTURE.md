ARCHITECTURE.md

Canonical System Architecture — BinaryBot Engine
Version: 1.1.0
Status: Active
Linked Documents:
ALGO_SPEC.md
FSM_SPEC.md
CHECKLIST.md
PARAMS_REFERENCE.md
MODULE_INTERFACE_SPEC.md
EVENT_SCHEMA_SPEC.md
OBSERVABILITY_LOGGING_SPEC.md
SIGNAL_DISTRIBUTION_SPEC.md
CHANNEL_CONFIG_SPEC.md


---

1. SYSTEM PHILOSOPHY

The system is built under the principle of:

- Single Source of Truth
- Single Runtime Engine
- Pure Strategy Separation
- Deterministic State Machine
- Zero Legacy Parallel Logic

No file may implement parallel scoring or signal logic outside the canonical engine.

---

2. SINGLE ENTRYPOINT PRINCIPLE

There must be exactly ONE runtime entrypoint.

Current canonical entrypoint:

/opt/binarybot/signal_engine.py

Systemd service:

ExecStart=/opt/binarybot/venv/bin/python /opt/binarybot/signal_engine.py

No other file may be executed as a parallel engine.

Legacy files (e.g., bot_service.py) may exist but must not be active in systemd.

---

3. FILE ROLE SEPARATION

3.1 strategy_v2.py — Pure Logic Engine

Role:

- Implements canonical ALGO_SPEC logic
- Contains no Telegram logic
- Contains no state persistence logic
- Contains no polling loops

Input:

- M1 candles
- M5 candles
- algo_params.json
- buffer_mode
- want_open_now flag

Output:

- Decision object (PRE / CONFIRM / OPEN_NOW / REJECT / NO_SIGNAL)

This file is deterministic and stateless.

---

3.2 signal_engine.py — Runtime Orchestrator

Role:

- Fetches market data
- Loads configuration
- Maintains FSM
- Manages watchlist
- Applies cooldown
- Sends Telegram messages
- Controls polling frequency

This is the only runtime loop.

Responsibilities:

- Wide scan
- Focus scan
- Deduplication (one LIVE per candle)
- State persistence
- Cooldown enforcement

---

3.3 config/algo_params.json — Parameter Source of Truth

Contains:

- Thresholds
- Multipliers
- Spike filters
- Expiry limits
- Scoring weights
- Version tag (algo_version)

No strategy thresholds are allowed inside .env.

.env may contain:

- API keys
- Telegram IDs
- Poll intervals
- Environment secrets

---

3.4 State Files

active_symbols.json

Contains active symbol list.
Used by wide scan.

focus_state.json

Contains:

- watchlist (max 2)
- pending_open flags
- cooldown_until timestamps

settings.json

Contains:

- buffer_mode (SMALL / MEDIUM / LARGE)

These files are persistent and must survive restart.

3.5 Core Module Architecture

BinaryBot is composed of several runtime modules defined in MODULE_INTERFACE_SPEC.md.

Core modules:

signal_engine.py
Main orchestrator loop.

strategy_v2.py
Pure strategy decision engine.

fsm_runtime.py
Finite state machine controlling signal lifecycle.

distribution_router.py
Handles tier routing and signal publication rules.

telegram_publisher.py
Single abstraction layer for Telegram API operations.

bot_service.py
Handles command interface and admin panel.

outcome_service.py
Handles ELITE outcome feedback system.

analytics_engine.py
Generates research and performance analytics.

observability_logger.py
Handles structured logging and proof logs.

storage.py
Provides atomic persistence for all state files.

---

4. EXECUTION FLOW

High-level runtime loop:

1. Load settings
2. Load active symbols
3. Load focus state
4. Run WIDE_SCAN continuously across all active symbols
5. Run FOCUS_SCAN concurrently for watchlist symbols when watchlist is not empty

---

4.1 Wide Scan Phase

Purpose:

- scan all active symbols continuously
- discover PRE candidates
- prevent symbol starvation
- maintain market-wide opportunity coverage

Behavior:

- Iterate active symbols
- Evaluate via strategy_v2
- If score >= PRE threshold:
  - candidate may enter watchlist/focus (if capacity allows or priority policy permits)
  - Send PRE message
  - Promote symbol to focus priority context
- Wide scan remains active even when focus symbols exist

---

4.2 Focus Scan Phase

Purpose:

- monitor focus/watchlist symbols more intensively
- refine live decision quality
- produce CONFIRM and OPEN_NOW only inside valid focus context
- allocate majority runtime/API attention to the strongest live opportunities

Behavior:

- Scan only watchlist/focus symbols inside the focus loop
- Watchlist capacity remains max 2 symbols
- If score >= CONFIRM threshold:
  - Send CONFIRM
- If score >= OPEN threshold:
  - Send OPEN_NOW
  - Set pending_open = False
- Upon lifecycle completion / invalidation / score drop below PRE:
  - Remove symbol from watchlist
  - Apply cooldown when required
  - Release focus slot for replacement by another candidate

Focus does NOT replace wide scan entirely.
Focus is a priority layer, not a total runtime takeover.

Canonical resource model:

- Majority of API/runtime budget is directed to focus symbols
- Remaining budget stays reserved for wide scan coverage
- If two focus symbols are active, focus priority is shared between them

Buffer meaning inside live decision logic:

- Buffer is not just a display value or cosmetic offset
- Buffer is the mathematical safety margin the strategy must expect price to traverse before expiry
- CONFIRM means the setup is strong enough to arm for possible execution
- OPEN_NOW means the bot considers it sufficiently probable that price can travel the required buffer distance within the expiry window
- Therefore OPEN_NOW is not only a direction call; it is a direction + distance + time feasibility decision

Operational consequence:

- BUY setup quality depends on the probability that price can close above entry plus buffer by expiry
- SELL setup quality depends on the probability that price can close below entry minus the required safety distance by expiry
- Focus exists to improve this live timing judgment, not to freeze discovery of new opportunities

---

4.3 Event Pipeline

BinaryBot operates through a structured event pipeline.

Pipeline stages:

1 Strategy Decision
strategy_v2.py evaluates candle data and produces a Decision object.

2 FSM Transition
fsm_runtime.py evaluates the decision and determines lifecycle transitions.

3 Signal Event Creation
signal_engine.py converts valid decisions into SignalEvent objects.

4 Distribution Routing
distribution_router.py routes events to Telegram tiers according to SIGNAL_DISTRIBUTION_SPEC.md.

5 Telegram Publishing
telegram_publisher.py sends messages to Telegram channels.

6 Outcome Feedback
outcome_service.py attaches voting mechanisms to OPEN_NOW signals in ELITE channels.

7 Observability Logging
observability_logger.py records all events following EVENT_SCHEMA_SPEC.md.


---

5. STATE MACHINE ENFORCEMENT

FSM invariants:

- Maximum 2 symbols in watchlist
- Only 1 LIVE message per candle per symbol
- Cooldown blocks re-entry
- Deselected symbols produce zero signals
- No state transition without explicit rule

All state transitions must be deterministic.

---

6. TELEGRAM ROUTING

Topics:

SIGNALS_LIVE

- PRE
- CONFIRM
- OPEN_NOW

BUFFER_LOGS

- Detailed scoring breakdown
- Buffer changes

SYSTEM_ALERTS

- Errors
- Restart
- API failure

Message formatting defined in TELEGRAM_UX.md.

---

7. FAILURE PROTECTION

The engine must protect against:

- Duplicate LIVE per candle
- Restart loops
- API flood
- Focus deadlock
- Memory growth
- Legacy logic execution

Restart policy:
Restart=on-failure (controlled)
Never restart in infinite loop.

---

8. VERSIONING CONTROL

Every structural change requires:

- CHANGELOG update
- algo_version bump
- CHECKLIST execution
- Pre-start validation
- Post-start monitoring

---

9. FORBIDDEN ARCHITECTURE PATTERNS

The following are strictly forbidden:

- Two runtime engines
- Two scoring models
- Strategy thresholds in multiple files
- Hardcoded thresholds outside config
- Telegram logic inside strategy_v2
- State persistence inside strategy_v2
- Parallel legacy bot_service execution

---

10. ARCHITECTURAL GUARANTEE

If this document is respected:

- Strategy behavior matches ALGO_SPEC
- No hidden logic drift occurs
- Runtime remains stable
- Signal quality remains deterministic
- Debugging remains traceable

---

End of ARCHITECTURE.md