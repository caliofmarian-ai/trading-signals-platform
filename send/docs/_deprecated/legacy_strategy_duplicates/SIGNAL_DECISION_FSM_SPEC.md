# SIGNAL_DECISION_FSM_SPEC.md

Version: 1.0  
Status: CANONICAL SPECIFICATION  


## 1. PURPOSE

This document defines the canonical **Signal Decision Finite State Machine (FSM)** for BinaryBot / DROPi Signals.

The purpose of this FSM is to formalize the lifecycle of every candidate signal from initial detection to final execution or rejection.

This specification ensures that:

- signal progression is deterministic
- signal stages are auditable
- signal behavior is consistent across all symbols
- PRE / CONFIRM / OPEN_NOW transitions are clearly defined
- signal deaths are explainable
- focus/watchlist behavior is controlled
- strategy analytics can measure exact transition bottlenecks

This FSM is one of the core control models of the system and must be treated as canonical architecture.

---

## 2. SCOPE

This specification applies to the signal lifecycle beginning at market scan evaluation and ending at one of the following terminal outcomes:

- REJECT
- CANCELLED
- EXPIRED
- OPEN_NOW emitted
- signal invalidated before final publication

This specification covers:

- candidate detection
- PRE
- CONFIRM
- OPEN_NOW
- stage rejections
- stage invalidation
- focus/watchlist transitions
- terminal states
- observability events for all transitions

This specification does not define:

- score calculation formulas
- channel routing rules
- outcome voting behavior
- Telegram UI formatting

Those are defined elsewhere.

---

## 3. CORE DESIGN PRINCIPLES

### 3.1 Single strategy quality

All signals follow the same strategy quality rules.
FREE, BASIC, PRO, and ELITE do not have different signal quality standards.

### 3.2 Deterministic transitions

A candidate must move between stages according to explicit state transition rules.

### 3.3 No hidden deaths

If a signal dies, the reason must be visible through observability and decision audit.

### 3.4 Focus-controlled OPEN_NOW

`OPEN_NOW` is only allowed for candidates that are inside focus/watchlist context, unless a future explicit spec changes this rule.

### 3.5 Stage progression is not guaranteed

Not every candidate becomes PRE.  
Not every PRE becomes CONFIRM.  
Not every CONFIRM becomes OPEN_NOW.

This is normal and expected.

---

## 4. STATE MODEL OVERVIEW

The canonical signal lifecycle is:

```text
IDLE
  ↓
CANDIDATE
  ↓
PRE
  ↓
CONFIRM
  ↓
OPEN_READY
  ↓
OPEN_NOW
  ↓
TERMINAL

The FSM also supports rejection / death paths:

CANDIDATE → REJECT
PRE → CANCELLED
CONFIRM → CANCELLED
OPEN_READY → CANCELLED
ANY ACTIVE STATE → EXPIRED / INVALIDATED


---

## 5. CANONICAL STATES

### 5.1 IDLE

The symbol has no active candidate and no active signal lifecycle in progress.

Characteristics:

no PRE

no CONFIRM

no OPEN_NOW

no watchlist focus requirement

normal wide scan only


### 5.2 CANDIDATE

A potential setup exists and has enough evidence to be evaluated as a meaningful opportunity.

Characteristics:

decision data exists

score may still be below PRE threshold

gates may still fail

candidate is not yet public


### 5.3 PRE

Initial public signal stage.

Meaning:

a meaningful setup exists

score and conditions are strong enough for early visibility

candidate is promising

not yet confirmed for final entry

may enter focus/watchlist


### 5.4 CONFIRM

Intermediate confirmation stage.

Meaning:

setup remains alive after PRE

evidence has improved or remained strong

direction still valid

signal is closer to execution quality

still not final entry


### 5.5 OPEN_READY

Internal near-final state.

Meaning:

signal is structurally ready for OPEN_NOW

focus conditions are satisfied

final checks pass or are nearly passing

may be used internally even if not exposed publicly


This state is optional in implementation but canonical in FSM analysis.

### 5.6 OPEN_NOW

Final execution-stage signal.

Meaning:

strategy authorizes immediate actionable entry

signal is strong enough to be published as final trade signal

this is the operationally relevant stage for channel limits


### 5.7 REJECT

Terminal strategy rejection state.

Meaning:

candidate failed structural requirements

candidate does not enter public lifecycle

no signal should be emitted beyond diagnostic/audit traces


### 5.8 CANCELLED

Signal was valid at an earlier stage but later lost viability.

Examples:

PRE cancelled before CONFIRM

CONFIRM cancelled before OPEN_NOW

setup invalidated by new candle


### 5.9 EXPIRED

Signal reached a stage but became stale due to time conditions.

Examples:

too much time passed between PRE and confirmation

open window no longer relevant


### 5.10 INVALIDATED

Signal became logically invalid due to market structure change.

Examples:

trend flipped

spike appeared

SR space collapsed

feasibility failed after stage promotion



---

## 6. STATE TRANSITION MAP

Canonical transitions:

IDLE → CANDIDATE
CANDIDATE → PRE
CANDIDATE → REJECT

PRE → CONFIRM
PRE → CANCELLED
PRE → EXPIRED
PRE → INVALIDATED

CONFIRM → OPEN_READY
CONFIRM → OPEN_NOW
CONFIRM → CANCELLED
CONFIRM → EXPIRED
CONFIRM → INVALIDATED

OPEN_READY → OPEN_NOW
OPEN_READY → CANCELLED
OPEN_READY → EXPIRED
OPEN_READY → INVALIDATED

OPEN_NOW → TERMINAL

Forbidden transitions:

IDLE → OPEN_NOW
IDLE → CONFIRM
REJECT → PRE
CANCELLED → OPEN_NOW
EXPIRED → CONFIRM
INVALIDATED → OPEN_NOW


---

## 7. ENTRY CONDITIONS BY STATE

### 7.1 IDLE → CANDIDATE

A symbol enters CANDIDATE when:

market data is available

basic strategy evaluation is possible

current market context suggests a potential setup worth evaluating


### 7.2 CANDIDATE → PRE

A candidate becomes PRE when:

score reaches PRE threshold

required critical gates pass

setup is not disqualified by hard rejections

signal timing is still valid


Canonical requirements:

minimum PRE score

spike filter pass

SR gate pass

feasibility pass

direction resolved


### 7.3 CANDIDATE → REJECT

A candidate becomes REJECT when:

score is below PRE threshold

or a hard gate fails

or data integrity is invalid

or market structure invalidates opportunity


### 7.4 PRE → CONFIRM

A PRE becomes CONFIRM when:

score improves or remains sufficiently high

initial structure survives new candle updates

no hard gate fails

timing window remains valid


### 7.5 CONFIRM → OPEN_READY

CONFIRM becomes OPEN_READY when:

conditions indicate likely entry validity

focus/watchlist context is satisfied

no final hard gate blocks entry

the signal is near final actionability


### 7.6 OPEN_READY → OPEN_NOW

A signal becomes OPEN_NOW when:

final open threshold is met

focus mode permits open emission

critical gates still pass

timing is optimal for entry

signal has not become stale



---

## 8. REJECTION CONDITIONS

A candidate or signal may be rejected at any non-terminal stage.

Canonical rejection groups:

### 8.1 Score rejections

score_pre_fail

score_confirm_fail

score_open_fail


### 8.2 Gate rejections

spike_reject

sr_reject

feasibility_reject

trend_reject

structure_reject

buffer_reject


### 8.3 Focus-related rejections

focus_full

focus_priority_lost

focus_cooldown_active

focus_state_invalid


### 8.4 Timing rejections

open_window_expired

confirmation_window_expired

stale_candidate


### 8.5 Data rejections

missing_candles

invalid_candle_shape

market_api_error

normalization_failure



---

## 9. CANCELLATION CONDITIONS

A signal in PRE / CONFIRM / OPEN_READY may be cancelled if:

price structure deteriorates

direction changes

trend alignment weakens materially

support/resistance compresses available space

spike behavior invalidates signal quality

feasibility becomes poor

higher-priority focus symbol displaces it


Cancellation must not be treated the same as initial rejection.

Initial rejection means it never progressed. Cancellation means it progressed and then died.


---

## 10. FOCUS / WATCHLIST RELATION

The FSM is integrated with focus/watchlist behavior.

### 10.1 Wide Scan

In wide scan mode:

all active symbols are scanned

candidates may emerge

PRE may be produced according to strategy design

focus candidates are selected from strongest opportunities


### 10.2 Focus Mode

In focus mode:

a subset of symbols receives more intensive monitoring

watchlist size is limited

only focused symbols may escalate to OPEN_NOW under current architecture


### 10.3 Watchlist Capacity

The focus/watchlist system must enforce a capacity limit.

Canonical assumption:

maximum two active focus symbols


If watchlist is full:

lower-priority candidates may remain PRE only

or may be rejected from focus

or may die before OPEN_NOW


### 10.4 Focus Entry

A symbol enters focus when:

it produces a strong enough PRE

priority is sufficient relative to other symbols

watchlist capacity permits entry

cooldown rules allow focus entry


### 10.5 Focus Exit

A symbol exits focus when:

it reaches OPEN_NOW and lifecycle completes

it is invalidated

it expires

it is displaced by stronger candidate

it returns to IDLE



---

## 11. TIMER / LIFETIME RULES

Signals are not immortal.

Each stage may have time sensitivity.

### 11.1 Candidate lifetime

Candidates may die quickly if market conditions move away before PRE threshold is met.

### 11.2 PRE lifetime

A PRE must not remain active indefinitely without progress.

Possible outcomes:

PRE → CONFIRM

PRE → CANCELLED

PRE → EXPIRED


### 11.3 CONFIRM lifetime

A CONFIRM must progress within a valid timing window or die.

Possible outcomes:

CONFIRM → OPEN_NOW

CONFIRM → CANCELLED

CONFIRM → EXPIRED


### 11.4 OPEN_NOW lifetime

OPEN_NOW is final execution-stage publication. After publication, the FSM transitions to terminal tracking rather than higher stage progression.


---

## 12. SIGNAL IDENTITY RULES

Each progressing signal must retain a stable identity.

Canonical signal identity components:

symbol

timeframe

candle_ts

direction


A signal ID must remain stable across:

PRE

CONFIRM

OPEN_NOW


This is required for:

deduplication

lifecycle correlation

auditability

distribution consistency

outcome linkage



---

## 13. OBSERVABILITY REQUIREMENTS

Every major state change must be observable.

Minimum events required:

candidate_detected

decision_evaluated

stage_promoted

decision_rejected

focus_entered

focus_rejected

stage_killed

distribution_decision


The FSM must be reconstructable from logs.

A human or script must be able to answer:

where the signal entered the lifecycle

where it died

why it died

whether it reached focus

whether it reached OPEN_NOW

whether it was suppressed operationally



---

## 14. FSM EVENT CONTRACT

Each FSM event should include at least:

event_type

symbol

timeframe

signal_id

previous_state

next_state

ts_utc

candle_ts

decision_kind

score_total

rejected_reason if applicable


Optional but recommended:

gates

debug payload

watchlist state

focus rank

stage age



---

## 15. RELATION TO DECISION AUDIT

The FSM and Decision Audit Layer serve related but different purposes.

### 15.1 FSM role

The FSM explains stage progression.

It answers:

what state the signal was in

how it moved

when it died


### 15.2 Decision Audit role

Decision Audit explains why each strategy evaluation concluded as it did.

It answers:

why a candidate failed

which gates failed

which score threshold failed

why a stage promotion did or did not happen


## 15.3 Combined use

Together they answer:

what happened

why it happened

where in the lifecycle it happened



---

## 16. RELATION TO DISTRIBUTION

The FSM decides signal lifecycle progression. Distribution decides publication routing.

These must remain distinct.

Examples:

A signal may reach OPEN_NOW in FSM terms but still be blocked from a channel by distribution limits.

A signal may be valid in strategy terms but suppressed as a duplicate operationally.


Therefore:

FSM state progression must not be confused with channel publication

distribution logs must not overwrite FSM interpretation



---

## 17. CHANNEL LIMIT RELATION

OPEN_NOW is the stage that matters for operational channel limits.

Canonical rule:

PRE and CONFIRM are signal lifecycle stages

OPEN_NOW is the final actionable stage

daily channel limits must be evaluated at the OPEN_NOW level, not PRE


This keeps signal quality and lifecycle separate from channel capacity rules.


---

## 18. ADMIN / OPERATOR INTERPRETATION RULES

Operators must interpret FSM behavior as follows:

### 18.1 PRE without CONFIRM

This means the setup was promising but not strong enough to continue.

### 18.2 CONFIRM without OPEN_NOW

This means the setup matured but still failed final actionability or timing.

### 18.3 Frequent REJECT at candidate stage

This suggests strategy gates are too strict or market conditions are poor.

### 18.4 Frequent PRE deaths

This suggests PRE threshold may be too loose or confirmation requirements too strict.

### 18.5 Very rare OPEN_NOW

This suggests either:

open threshold too high

focus system too restrictive

SR/spike/feasibility gates too aggressive

time windows too narrow



---

## 19. MINIMUM ACCEPTANCE CRITERIA

The Signal Decision FSM is considered correctly implemented only if:

all major states are represented or inferable

all allowed transitions are deterministic

invalid transitions are prevented

signal IDs remain stable across stages

PRE / CONFIRM / OPEN_NOW transitions are logged

rejections and cancellations are distinguishable

focus entry/exit is observable

stage death causes are visible via audit



---

## 20. IMPLEMENTATION GUIDANCE

The implementation should be split conceptually as follows:

strategy decides candidate quality

signal engine applies stage progression

FSM runtime stores state

observability logger records transitions

distribution router publishes approved stages


No single module should own the entire lifecycle implicitly without logs.

The lifecycle must remain reconstructable.


---

## 21. EXAMPLE LIFECYCLES

### 21.1 Healthy lifecycle

IDLE
→ CANDIDATE
→ PRE
→ CONFIRM
→ OPEN_READY
→ OPEN_NOW
→ TERMINAL

### 21.2 Early rejection lifecycle

IDLE
→ CANDIDATE
→ REJECT

Reason example:

score_pre_fail

### 21.3 PRE death lifecycle

IDLE
→ CANDIDATE
→ PRE
→ CANCELLED

Reason example:

confirm_stalled

### 21.4 Confirm death lifecycle

IDLE
→ CANDIDATE
→ PRE
→ CONFIRM
→ INVALIDATED

Reason example:

SR_SPACE_INSUFFICIENT

### 21.5 Focus-blocked lifecycle

IDLE
→ CANDIDATE
→ PRE
→ FOCUS_REJECTED
→ CANCELLED

Reason example:

focus_full


---

## 22. FUTURE EXTENSIONS

Possible future upgrades:

explicit OPEN_READY state in code if not already present

per-stage timeout policies configurable by admin

symbol-specific FSM tuning

adaptive focus prioritization

replayable FSM backtesting

visual FSM timeline per signal


These are extensions, not requirements for v1.


---

## 23. FINAL CANONICAL STATEMENT

BinaryBot / DROPi Signals must treat every signal as a lifecycle object, not a one-shot alert.

Every candidate must move through a deterministic and auditable decision state machine.

The canonical signal lifecycle is governed by:

strategy evaluation

state transition rules

focus/watchlist policy

time validity

rejection and cancellation conditions


The Signal Decision FSM is the authoritative architecture for understanding how a signal is born, evolves, and dies.

