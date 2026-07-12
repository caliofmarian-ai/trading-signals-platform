ARCHITECTURE.md

Canonical System Architecture — BinaryBot Engine
Version: 1.0.0
Status: Active
Linked Documents: ALGO_SPEC.md, FSM_SPEC.md, CHECKLIST.md, PARAMS_REFERENCE.md

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

---

4. EXECUTION FLOW

High-level runtime loop:

1. Load settings
2. Load active symbols
3. Load focus state
4. If watchlist not empty → FOCUS MODE
5. Else → WIDE SCAN MODE

---

4.1 Wide Scan Mode

- Iterate active symbols
- Evaluate via strategy_v2
- If score >= PRE threshold:
  - Add to watchlist (if < 2)
  - Send PRE message
  - Switch to Focus Mode

---

4.2 Focus Mode

- Only scan symbols in watchlist
- If score >= CONFIRM:
  - Send CONFIRM
- If score >= OPEN threshold:
  - Send OPEN_NOW
  - Set pending_open = False
- Wait for /open confirmation
- Upon confirmation:
  - Remove from watchlist
  - Apply cooldown
  - Return to Wide Scan if no other focus symbol

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