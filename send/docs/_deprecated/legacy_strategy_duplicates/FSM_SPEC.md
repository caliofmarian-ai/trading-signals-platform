FSM_SPEC.md

Finite State Machine Specification — BinaryBot
Version: 1.0.0
Status: Active
Linked Documents: ALGO_SPEC.md, ARCHITECTURE.md, CHECKLIST.md

---

1. PURPOSE

This document defines the deterministic state machine controlling:

- Symbol lifecycle
- Signal lifecycle
- Focus management
- Cooldown enforcement
- LIVE execution control

The FSM guarantees:

- No duplicate LIVE signals
- Maximum 2 focus symbols
- Deterministic transitions
- No uncontrolled re-entry
- No signal spam

---

2. EXECUTION CONTEXT MODEL

The runtime architecture uses continuous wide scan coverage plus focused watchlist monitoring.
The FSM does NOT require a global binary engine mode switch in order to remain valid.

Canonical execution contexts:

2.1 WIDE SCAN COVERAGE

- scans all active symbols
- searches for PRE candidates
- must remain active to prevent symbol starvation
- does not by itself authorize OPEN_NOW

2.2 FOCUS CONTEXT

- applies to symbols currently inside WATCHLIST / focus tracking
- allows intensified monitoring for CONFIRM and OPEN_NOW readiness
- OPEN_NOW is only allowed for symbols in valid focus/watchlist context
- focus context may exist while wide scan coverage continues in parallel

Context rule:

- If a symbol is not in valid WATCHLIST / focus context, OPEN_NOW is forbidden
- Wide scan coverage may continue even when one or more focus symbols exist

3. SYMBOL STATES

Each symbol can be in exactly one of the following states:

---

3.1 IDLE

Meaning:

- Symbol active but not under watch
- Eligible for PRE detection

Allowed transitions:
IDLE → WATCHLIST (on PRE)

Forbidden:
IDLE → LIVE
IDLE → COOLDOWN

---

3.2 WATCHLIST

Meaning:

- PRE detected
- Symbol being monitored
- Awaiting CONFIRM or OPEN_NOW

Constraints:

- Max 2 symbols in WATCHLIST globally

Allowed transitions:
WATCHLIST → LIVE (on OPEN_NOW)
WATCHLIST → IDLE (if score drops below PRE)
WATCHLIST → COOLDOWN (manual open)

---

3.3 LIVE_SENT

Meaning:

- OPEN_NOW signal has been sent
- Awaiting user /open confirmation

Constraints:

- Only one LIVE per candle
- No repeated LIVE for same candle

Allowed transitions:
LIVE_SENT → COOLDOWN (on /open)
LIVE_SENT → WATCHLIST (if not opened and condition persists next candle)

---

3.4 COOLDOWN

Meaning:

- Trade executed
- Symbol locked temporarily

Cooldown duration:
Defined by configuration

Constraints:

- No PRE allowed
- No CONFIRM allowed
- No OPEN_NOW allowed

Allowed transitions:
COOLDOWN → IDLE (after cooldown expires)

---

4. SIGNAL LIFECYCLE

The canonical signal progression:

PRE → CONFIRM → OPEN_NOW → COOLDOWN

Rules:

- PRE requires score ≥ PRE threshold
- CONFIRM requires score ≥ CONFIRM threshold
- OPEN_NOW requires score ≥ OPEN threshold
- OPEN_NOW requires want_open_now flag TRUE
- OPEN_NOW only allowed in valid focus/watchlist context

---

5. INVARIANTS (NON-NEGOTIABLE RULES)

These rules must never be violated:

1. Max 2 symbols in WATCHLIST
2. Only one LIVE per symbol per candle
3. No LIVE outside valid focus context
4. Cooldown blocks all signals
5. Deselected symbols produce zero signals
6. No state transition without explicit trigger
7. No implicit re-entry during cooldown

Violation of any invariant = critical bug.

---

6. TRANSITION MATRIX

Current State| Event| Next State
IDLE| PRE detected| WATCHLIST
WATCHLIST| Score < PRE| IDLE
WATCHLIST| OPEN_NOW sent| LIVE_SENT
LIVE_SENT| /open received| COOLDOWN
LIVE_SENT| No open, next candle and setup persists| WATCHLIST
COOLDOWN| Cooldown expired| IDLE

---

7. FOCUS MANAGEMENT

Global constraints:

- WATCHLIST size ≤ 2
- If WATCHLIST size = 2:
  - no third symbol may become active focus simultaneously
  - additional PRE candidates may remain pending, be ignored, or be rejected by priority policy

Canonical focus lifecycle events:

7.1 focus_enter

A symbol enters focus when:

- PRE lifecycle conditions are satisfied
- score is strong enough for watchlist entry
- cooldown rules allow entry
- capacity permits entry or replacement policy allows takeover

7.2 focus_exit

A symbol exits focus when:

- score drops below PRE
- setup invalidates
- timeout / validity window expires
- OPEN_NOW lifecycle completes and transition continues
- cooldown requires release from active focus tracking

7.3 focus_replace

A symbol may be replaced in focus when:

- watchlist is full
- a stronger candidate outranks an existing focus symbol by canonical policy
- replacement is logged explicitly and does not violate watchlist capacity

Operational clarification:

- Focus context controls OPEN_NOW eligibility
- Focus context does not require global suspension of wide scan coverage
- When one symbol exits WATCHLIST, the released slot becomes available for replacement
- Wide scan continues discovering candidates while focus-tracked symbols are monitored more intensively

8. LIVE DEDUPLICATION

Each symbol must track:

last_live_candle_timestamp

Rule:

IF current_candle_timestamp == last_live_candle_timestamp
→ BLOCK OPEN_NOW

This prevents duplicate LIVE spam.

---

9. COOLDOWN LOGIC

Cooldown must track:

cooldown_until_timestamp

Rule:

IF now < cooldown_until
→ State remains COOLDOWN

After expiry:
→ Transition to IDLE automatically

Cooldown must persist across restart.

---

10. RESTART BEHAVIOR

On system restart:

- Reload focus_state.json
- Reload cooldown timestamps
- Do NOT resend LIVE for previous candle
- Do NOT reset cooldown timers

Restart must not cause duplicate signals.

---

11. FAILURE PROTECTION

FSM must prevent:

- Infinite PRE loop
- Infinite CONFIRM spam
- Infinite LIVE resend
- Focus deadlock
- Cooldown bypass

Any such behavior indicates state corruption.

---

12. GUARANTEE

If FSM_SPEC is implemented correctly:

- No duplicate LIVE
- No signal spam
- Stable focus behavior
- Deterministic trade lifecycle
- Fully controlled execution model

---

13. SIGNAL IDENTITY

Every signal instance must carry a unique identifier.

SignalID format:

signal_id = symbol + "_" + candle_timestamp + "_" + side

Example:
EURUSD_20260304_0835_BUY

Rules:

- PRE, CONFIRM and OPEN_NOW belonging to the same setup MUST share the same signal_id.
- signal_id must remain constant throughout the lifecycle.
- deduplication must use signal_id + signal_type.

This ensures traceability across all signal stages.

---

14. SIGNAL DISTRIBUTION HOOK

FSM does not directly publish signals to Telegram channels.

Instead, FSM emits signal events:

PRE
CONFIRM
OPEN_NOW

These events must be passed to the Signal Distribution Engine.

Distribution Engine responsibilities:

- route signals to channel tiers
- enforce daily limits
- enforce silent tiers
- log deliveries

FSM only generates signals.
Distribution system controls where signals are delivered.

---


15. TIER SILENCE RULE

Channel tiers operate with daily OPEN_NOW limits.

Limits:

FREE → 6 OPEN signals/day
BASIC → 20 OPEN signals/day
PRO → 50 OPEN signals/day
ELITE → unlimited

Important rule:

Only OPEN_NOW increments the counter.

However:

When a tier reaches its OPEN limit,
the tier becomes SILENT.

SILENT tier behavior:

- PRE signals blocked
- CONFIRM signals blocked
- OPEN_NOW signals blocked

ELITE tier never becomes silent.

---

16. DAILY RESET

Daily counters reset automatically.

Reset time:

10 minutes after London market open.

Timezone:

Europe/London

Reset behavior:

FREE counter reset
BASIC counter reset
PRO counter reset
ELITE counter reset

All tiers return to ACTIVE state.


End of FSM_SPEC.md


# Focus Lease and Forced Eviction Rules

## Focus Lease

Entering WATCHLIST / focus context is not permanent residency.

Every symbol that enters focus context must receive:

- focus_enter_ts
- focus_ttl_sec
- focus_expire_reason (nullable until exit)

The lease exists to guarantee that focus remains operational, bounded, and recyclable.

## Canonical Forced Focus Exit Conditions

A symbol must be forcibly removed from WATCHLIST / focus context when any of the following occurs:

1. symbol removed from active symbol universe
2. focus lease TTL expires
3. canonical lifecycle invalidates the setup
4. stronger replacement candidate takes the slot under canonical replacement policy
5. runtime cleanup requires release after terminal signal lifecycle

## Required Forced Exit Effects

Forced focus exit must:

- remove symbol from watchlist
- clear current focus residency
- preserve auditability through focus_expire_reason
- recalculate runtime mode based on remaining watchlist contents

## Focus Exit Reasons

Canonical reasons include at minimum:

- REMOVED_FROM_ACTIVE_SYMBOLS
- FOCUS_TTL_EXPIRED
- SETUP_INVALIDATED
- REPLACED_BY_STRONGER_CANDIDATE
- POST_LIFECYCLE_RELEASE

## Decision Freeze Semantics In FSM Context

FSM lifecycle must distinguish:

- same opportunity still being observed
- new opportunity requiring fresh state progression

Repeated observation of the same opportunity must not be interpreted as a new full lifecycle attempt unless material context has changed.

## Material Reopen Conditions

A previously evaluated opportunity may reopen for fresh evaluation only if one or more of the following occurs:

- new candle_ts
- direction changes
- focus context changes
- score changes materially
- expiry feasibility changes materially
- canonical stage progression becomes newly possible


