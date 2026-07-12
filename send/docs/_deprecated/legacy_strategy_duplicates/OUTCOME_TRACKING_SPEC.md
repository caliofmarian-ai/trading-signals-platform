# OUTCOME_TRACKING_SPEC.md
BinaryBot — Admin Outcome Tracking (WIN / LOSE / MISSED)
Version: 1.0.0
Status: Canonical

Linked Documents:
ALGO_SPEC.md
SIGNAL_DISTRIBUTION_SPEC.md
PERFORMANCE_ANALYTICS_SPEC.md
OBSERVABILITY_LOGGING_SPEC.md
CHANNEL_CONFIG_SPEC.md
FSM_SPEC.md

---

## 1. PURPOSE

This document defines how the system records the real-world outcome of each OPEN_NOW signal.

The objective:
- Enable statistical validation (win rate, expectancy, drift detection)
- Build long-term performance history
- Separate "signal quality" from "operator availability" using MISSED

Outcome tracking is ADMIN-only and must not be available to subscribers.

---

## 2. OUTCOME TYPES

Each OPEN_NOW can be labeled with exactly one outcome:

- WIN     → trade ended in profit
- LOSE    → trade ended in loss
- MISSED  → signal was not executed by operator (no entry placed)

MISSED is not a loss.
MISSED does not affect win rate unless explicitly configured later.

---

## 3. OUTCOME SCOPE & ACCESS CONTROL

Rule:
Only ADMIN can set outcomes.

Implementation rules:
- Outcome buttons are attached ONLY to the ADMIN version of OPEN_NOW message.
- Subscriber channels never receive outcome buttons.

Hard gate:
- If user_id is not in ADMIN_USER_IDS → ignore callback.

---

## 4. SIGNAL IDENTITY LINKING (MANDATORY)

Every OPEN_NOW signal MUST include a stable unique identifier:

SIGNAL_ID

The same SIGNAL_ID must appear consistently in:
- PRE
- CONFIRM
- OPEN_NOW

Outcome records are keyed by SIGNAL_ID.

If SIGNAL_ID missing → outcome feature must refuse to record.

---

## 5. UI / UX REQUIREMENTS (ADMIN)

### 5.1 Buttons attached to ADMIN OPEN_NOW
Immediately under the ADMIN OPEN_NOW message, show 3 buttons:

✅ WIN
❌ LOSE
⏳ MISSED

Buttons are inline keyboard buttons.

### 5.2 After selection behavior
When admin taps a button:
- outcome is saved persistently
- the original ADMIN OPEN_NOW message is edited to append outcome status:
  - "OUTCOME: WIN" or "OUTCOME: LOSE" or "OUTCOME: MISSED"
- the inline buttons are either:
  A) removed (to prevent double-click), OR
  B) replaced with: "Change Outcome" + the same 3 buttons
(Option B preferred for corrections)

### 5.3 Idempotency
If admin presses the same outcome twice:
- system must not duplicate logs or counters
- it should respond with "Already set: WIN" etc.

---

## 6. DATA STORAGE (PERSISTENT)

Outcome must survive restart.

Storage file:
`/opt/binarybot/data/outcomes.json`

Structure example:

{
  "meta": {
    "version": "1.0.0"
  },
  "items": {
    "EURUSD_M1_20260304_001": {
      "signal_id": "EURUSD_M1_20260304_001",
      "symbol": "EUR/USD",
      "side": "BUY",
      "expiry_seconds": 300,
      "buffer_mode": "MEDIUM",
      "created_at_utc": "2026-03-04T08:20:11Z",
      "outcome": "WIN",
      "outcome_set_at_utc": "2026-03-04T08:25:18Z",
      "set_by_user_id": 123456789,
      "admin_message_id": 1111,
      "admin_chat_id": -100XXXXXXXXXX
    }
  }
}

Mandatory fields:
- signal_id
- outcome
- outcome_set_at_utc
- set_by_user_id

Recommended fields:
- symbol, side, expiry, buffer_mode
- admin message identifiers (for edit/trace)
- score, sr_space, rejection flags snapshot (optional)

---

## 7. LOGGING & OBSERVABILITY

Every outcome action must produce an observability event:

EVENT: OUTCOME_SET
Fields:
- timestamp_utc
- signal_id
- outcome
- previous_outcome (if overwritten)
- user_id
- symbol
- tier (admin)

These events must appear in OBSERVABILITY_LOGGING_SPEC.md.

---

## 8. ANALYTICS INTEGRATION (PERFORMANCE)

Performance analytics uses outcomes as ground truth.

Counters:
- wins_count
- losses_count
- missed_count

Win Rate calculation:
WR = wins / (wins + losses)

MISSED excluded by default.

Optional future mode:
- include_missed_in_wr = false (default)
- if true → WR = wins / total_outcomes

Also track:
- WR by symbol
- WR by buffer_mode
- WR by session
- PRE→OPEN conversion
- OPEN→WIN conversion (true execution success)

---

## 9. SAFETY RULES

- Outcomes can only be set for signals that exist (known SIGNAL_ID).
- If SIGNAL_ID not found in signals registry → reject.
- Duplicate open_now must not create duplicate outcomes. Key is SIGNAL_ID.

---

## 10. GUARANTEES

If implemented correctly, the system guarantees:
- deterministic per-signal outcome tracking
- admin-only control
- persistent truth data for analytics
- separation of strategy performance from operator availability

---

End of OUTCOME_TRACKING_SPEC.md