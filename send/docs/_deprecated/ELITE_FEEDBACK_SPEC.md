# ELITE_FEEDBACK_SPEC — Member Outcome Reporting & Private Statistics
Version: 1.0.0
Status: Canonical

Linked Documents:
SIGNAL_DISTRIBUTION_SPEC.md
CHANNEL_CONFIG_SPEC.md
TELEGRAM_UX.md
OBSERVABILITY_LOGGING_SPEC.md
PERFORMANCE_ANALYTICS_SPEC.md
SYSTEM_INVARIANTS.md

---

## 1. PURPOSE

This document defines the feedback system used to collect real outcomes for OPEN_NOW signals from ELITE members.

Goals:
- Build a high-integrity dataset of outcomes
- Enable per-user private stats (self-learning)
- Enable admin aggregate analytics (edge validation)
- Prevent spam, fraud, and privacy leaks

This layer does not change the trading algorithm.
It only records outcomes after signals are published.

---

## 2. SCOPE

Applies only to:
- OPEN_NOW signals posted in ELITE channel

Does NOT apply to:
- PRE signals
- CONFIRM signals
- FREE/BASIC/PRO channels

---

## 3. DEFINITIONS

### 3.1 Outcome Types
- WIN: user executed and won
- LOSE: user executed and lost
- MISSED: user did not execute (late / absent)

### 3.2 Signal Reference
Each OPEN_NOW must have a stable:
- SIGNAL_ID

Feedback entries MUST reference SIGNAL_ID.

---

## 4. AUTHORIZATION (VARIANT 2)

Feedback submission and stats access are allowed only if:
- user is a current member of ELITE channel

Membership check:
- Telegram getChatMember(ELITE_CHANNEL_ID, user_id)
- allowed statuses: member / administrator / creator

If not a member:
- feedback rejected
- stats rejected
- user receives private message explaining requirement

No whitelist.
No manual enrollment.

---

## 5. FEEDBACK UI RULES

### 5.1 Button Placement
Buttons appear only on:
- ELITE OPEN_NOW messages

Buttons:
- ✅ WIN
- ❌ LOSE
- ⏳ MISSED

### 5.2 Button Behavior
When pressed:
1) Bot verifies ELITE membership (Variant 2)
2) Bot records outcome linked to SIGNAL_ID + user_id
3) Bot sends a private confirmation to that user
4) Bot logs the event (observability)

---

## 6. DEDUPLICATION / INTEGRITY RULES

### 6.1 Single Outcome per User per Signal
A user may have only ONE final outcome per SIGNAL_ID.

If user presses another outcome later:
- The system may either:
  A) overwrite (last write wins) OR
  B) lock (first write wins)

Canonical mode (recommended):
- OVERWRITE allowed within a short window (e.g. 30 minutes)
- After window closes: LOCK

(Exact values are parameters.)

### 6.2 Spam Protection
Rate limit:
- max N feedback submissions per minute per user (parameter)

---

## 7. DATA MODEL (CANONICAL)

### 7.1 Required Fields per Feedback Entry
- timestamp_utc
- signal_id
- user_id
- outcome (WIN/LOSE/MISSED)
- symbol
- side (BUY/SELL)
- expiry_seconds
- buffer_value (pips or points+%)
- algo_version
- tier = ELITE

### 7.2 Storage Requirements
- persistent storage (survive restarts)
- safe append or safe update
- no corruption

---

## 8. USER PRIVATE STATISTICS (/mystats)

### 8.1 Visibility
User may see ONLY their own stats via private chat with the bot.

### 8.2 Minimum Metrics
- total_rated_signals
- win_count
- lose_count
- missed_count
- win_rate = win / (win + lose)
- participation_rate = (win + lose) / total
- missed_rate = missed / total

Optional:
- breakdown by symbol
- breakdown by session (ASIA/LONDON/NY)
- breakdown by buffer_mode

---

## 9. ADMIN AGGREGATE STATISTICS

Admin can request:
- totals across all ELITE members
- win rate overall
- participation rate overall
- top symbols by win rate
- worst symbols by win rate
- member leaderboard (optional)

Privacy rule:
- Member identifiers must not be public.
- Admin view may show user_id internally, but never posted into ELITE channel.

---

## 10. AUDIT & OBSERVABILITY

The system must log:
- outcome recorded (signal_id, user_id, outcome)
- membership check pass/fail
- duplicate overwrite events
- suspicious activity (rate-limit hits)

Logs must include:
- algo_version
- parameter hash (if available)

---

## 11. FAILURE MODES & SAFETY

If membership check fails:
- do not record
- respond privately with reason

If storage fails:
- do not claim recorded
- log error
- notify admin

---

## 12. GUARANTEES

If implemented correctly:
- outcomes dataset is real and traceable
- users learn from their own stats privately
- admin gains objective performance analytics
- no privacy leaks
- no manual user management is required

---

End of ELITE_FEEDBACK_SPEC.md