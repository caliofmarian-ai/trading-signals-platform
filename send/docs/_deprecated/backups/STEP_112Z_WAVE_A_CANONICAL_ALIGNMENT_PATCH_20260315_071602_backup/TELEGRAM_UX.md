TELEGRAM_UX.md

Telegram User Experience Specification — BinaryBot
Version: 1.0.0
Status: Active
Linked Documents: ALGO_SPEC.md, FSM_SPEC.md, ARCHITECTURE.md, CHECKLIST.md

---

1. PURPOSE

This document defines:

- Exact Telegram message structure
- Message routing rules (topics)
- Command behavior
- Anti-spam safeguards
- Formatting standards
- Execution interaction model

Telegram is the operational interface of the engine.
Clarity and precision are mandatory.

---

2. TELEGRAM TOPICS (THREAD STRUCTURE)

The bot must route messages to specific topics.

2.1 SIGNALS_LIVE

Purpose:

- PRE
- CONFIRM
- OPEN_NOW

This is the operational trading channel.

No debug data allowed here.

---

2.2 BUFFER_LOGS

Purpose:

- Detailed scoring breakdown
- Buffer calculations
- Expiry calculations
- Gate rejections
- Internal state transitions

This is a technical transparency channel.

---

2.3 SYSTEM_ALERTS

Purpose:

- Engine started
- Engine stopped
- Restart detection
- API errors
- Runtime exceptions
- State corruption alerts

No trading signals allowed here.

---

3. MESSAGE TYPES

There are exactly four message categories:

1. PRE
2. CONFIRM
3. OPEN_NOW
4. SYSTEM

No other signal types are allowed.

---

4. PRE MESSAGE FORMAT

Purpose:
Informational. Early detection.

Format:

PRE-SIGNAL
Symbol: {SYMBOL}
Direction: {BUY/SELL}
Buffer Mode: {SMALL/MEDIUM/LARGE}
Estimated Expiry: {X} min
Confidence: {score}
Status: Monitoring

Rules:

- Sent only once per candle per symbol
- Only in FOCUS_MODE
- Not sent if watchlist full

---

5. CONFIRM MESSAGE FORMAT

Purpose:
Higher probability condition.

Format:

CONFIRM
Symbol: {SYMBOL}
Direction: {BUY/SELL}
Buffer: {value}
Expiry: {X} min
Confidence: {score}
Status: Strengthening

Rules:

- Only after PRE
- Only in WATCHLIST state
- No duplicate per candle

---

6. OPEN_NOW MESSAGE FORMAT

Purpose:
Execution signal.

Format:

OPEN NOW
Symbol: {SYMBOL}
Direction: {BUY/SELL}
Buffer: {value}
Expiry: {X} min
Confidence: {score}
Action: Execute and send /open {SYMBOL}

Rules:

- Only one per candle
- Only in FOCUS_MODE
- Requires score ≥ OPEN threshold
- Requires want_open_now = True
- Deduplicated by candle timestamp

---

7. SYSTEM MESSAGE FORMAT

Examples:

ENGINE STARTED
Algo Version: {version}
Mode: {WIDE/FOCUS}

API ERROR
Symbol: {SYMBOL}
Details: {error_message}

RESTART DETECTED
Cooldown states preserved

Rules:

- Only in SYSTEM_ALERTS
- No trading data included

---

8. COMMAND INTERFACE

8.1 /start

Function:

- Initialize user session
- Show available commands

---

8.2 /buffer

Function:

- Change buffer mode

Options:
SMALL
MEDIUM
LARGE

Effect:

- Updates settings.json
- Affects future signals only

---

8.3 /open SYMBOL

Function:

- Confirms trade execution
- Triggers COOLDOWN

Rules:

- Only valid for symbol in LIVE_SENT state
- If invalid → no state change

---

8.4 Symbol Toggle

Function:

- Enable / disable active symbols
- Update active_symbols.json

Rules:

- Deselected symbols produce zero signals
- Removal clears WATCHLIST state

---

9. ANTI-SPAM RULES

The following must never occur:

- Duplicate PRE per candle
- Duplicate CONFIRM per candle
- Duplicate OPEN_NOW per candle
- OPEN_NOW outside FOCUS_MODE
- More than 2 active focus symbols
- Message storm during volatility spike

All messages must be deduplicated by:

symbol + candle_timestamp + message_type

---

10. MESSAGE PRIORITY ORDER

If multiple events occur in same cycle:

Priority:

1. SYSTEM errors
2. OPEN_NOW
3. CONFIRM
4. PRE

Never send PRE if OPEN_NOW condition already met.

---

11. BUFFER_LOGS CONTENT RULES

Buffer logs must include:

- Trend score
- Momentum score
- Entry timing score
- Total score
- Buffer calculation formula
- Expiry formula
- Gate results (SR / Spike / Feasibility)
- State transition event

This ensures traceability.

---

12. USER EXPERIENCE GUARANTEE

If TELEGRAM_UX is respected:

- No confusion in message meaning
- No duplicate execution signals
- Clear progression PRE → CONFIRM → OPEN_NOW
- No hidden logic
- No silent state transitions

---

---

13. OPEN_NOW OUTCOME PANEL (ELITE)

In the ELITE channel, each OPEN_NOW signal includes an outcome reporting interface.

This interface allows ELITE members to report the real result of the trade.

The outcome interface is considered part of the same signal lifecycle.

Signal lifecycle:

PRE → CONFIRM → OPEN_NOW → OUTCOME_PANEL

All four stages must share the same SIGNAL_ID.

The outcome panel is directly attached to the OPEN_NOW signal.

Preferred implementation:

The outcome buttons are included in the same OPEN_NOW message.

Fallback implementation:

If Telegram limitations require separation, the bot may send a second message immediately after OPEN_NOW.

Rules:

- The second message must be sent within ≤ 1 second
- It must contain the same SIGNAL_ID
- It must reference the OPEN_NOW message using reply_to_message_id

This ensures both messages are logically linked.

Example format:

OPEN NOW
Symbol: {SYMBOL}
Direction: {BUY/SELL}
Buffer: {value}
Expiry: {X} min
Confidence: {score}

TRADE RESULT REPORT (ELITE)

Vote AFTER trade expiry.

[ WIN ]   [ LOSE ]   [ MISSED ]

Outcome statistics will appear below.

---

14. OUTCOME REPORTING SYSTEM

Purpose:

Collect real trade results from ELITE members in order to build accurate performance statistics.

These statistics are used for:

- symbol performance analysis
- strategy validation
- signal quality evaluation

---

14.1 Voting Activation

Outcome buttons must become active only after the trade expiry.

trade_close_time = OPEN_NOW_time + expiry_minutes

This prevents early voting which could generate false statistics.

---

14.2 Voting Window

Voting is allowed only within the outcome reporting window.

vote_start = trade_close_time
vote_end   = vote_start + 5 minutes

After vote_end:

- voting buttons are removed
- outcome submissions are rejected

Maximum reporting window must never exceed 15 minutes after OPEN_NOW.

---

14.3 Single Vote Rule

Each Telegram user may submit only one outcome per SIGNAL_ID.

Policy:

LOCK (first write wins)

Once an outcome is submitted:

- the result is permanently recorded
- the user cannot change the vote
- additional button presses are ignored

---

14.4 Outcome Options

WIN

Trade executed successfully.

LOSE

Trade executed but resulted in loss.

MISSED

User did not execute the trade or entered too late.

---

14.5 Public Outcome Statistics

The bot must update the OPEN_NOW message with aggregated outcome statistics.

Example:

OUTCOME (ELITE)

WIN: {count} ({percentage}%)
LOSE: {count} ({percentage}%)
MISSED: {count} ({percentage}%)

TOTAL VOTES: {total}

Only aggregated statistics are visible.

User identities must never be exposed.

---

14.6 Data Integrity Safeguards

The system must enforce the following protections:

- one vote per user per SIGNAL_ID
- no voting before trade expiry
- no voting after reporting window
- no outcome modification

All outcome records must be stored using:

SIGNAL_ID + USER_ID

This guarantees statistical accuracy.

---

15. ADMIN CONTROL PANEL

The bot provides a private Admin Control Panel accessible only to the system operator.

Purpose:

- Control bot behavior
- Adjust trading parameters
- Access research data
- View system configuration

---

15.1 Admin Panel Access

The panel is available only in the ADMIN Telegram topic.

Access restricted by ADMIN_USER_ID.

---

15.2 Admin Panel Buttons

Core Controls:

SET BUFFER
Change buffer mode:
SMALL / MEDIUM / LARGE

SET SYMBOLS
Open symbol selection interface.

Admin selects symbols with high payout to scan.

These symbols define the WIDE SCAN universe.

---

15.3 Research & Analytics

Buttons available:

SIGNAL PERFORMANCE
Shows statistics for signals per symbol.

FOCUS HISTORY
Displays symbols that entered focus mode.

Shows:

- number of PRE signals
- number of CONFIRM signals
- number of OPEN_NOW signals

Helps identify profitable pairs.

---

15.4 System Monitoring

Buttons:

SYSTEM STATUS
Displays:

- engine mode
- active symbols
- focus symbols
- API usage load

ENGINE LOGS
Shows recent system alerts.

---

15.5 Documentation Access

Admin panel allows direct access to architecture documents.

Buttons:

VIEW ALGO_SPEC
VIEW FSM_SPEC
VIEW TELEGRAM_UX
VIEW RISK_MODEL
VIEW CHANNEL_CONFIG
VIEW SIGNAL_DISTRIBUTION

Documents are sent as Markdown files directly in Telegram.
This allows the operator to review system rules inside the bot interface.



End of TELEGRAM_UX.md