# MEMBER_FEEDBACK_SPEC.md
BinaryBot — Member Feedback Layer (Optional / Non-Canonical)
Version: 1.0.0
Status: Canonical (Distribution Layer Only)

Linked Documents:
SIGNAL_DISTRIBUTION_SPEC.md
CHANNEL_CONFIG_SPEC.md
TELEGRAM_UX.md
OBSERVABILITY_LOGGING_SPEC.md
PERFORMANCE_ANALYTICS_SPEC.md
OUTCOME_TRACKING_SPEC.md

---

## 1. PURPOSE

This document defines an optional member feedback mechanism for OPEN_NOW signals.

Goal:
- measure member-perceived results (crowd feedback)
- detect issues like late entries, broker differences, or misunderstandings
- protect operator reputation via evidence-based reporting

IMPORTANT:
Member feedback is NOT ground truth.
Admin outcome remains canonical for strategy analytics.

---

## 2. FEEDBACK TYPES

Members can submit one of:

- 👍 WIN (member claims win)
- 👎 LOSE (member claims loss)
- ⏳ MISSED (member did not enter / entered too late)

Optional extra:
- 🕒 LATE ENTRY (entered late)
- ⚠️ DIFFERENT PAYOUT (broker payout issue)
(These are metadata tags, not outcomes.)

---

## 3. SCOPE & WHERE BUTTONS APPEAR

Buttons appear ONLY under OPEN_NOW messages posted to member channels:
FREE / BASIC / PRO / ELITE (optional for ELITE).

They must NOT appear in admin messages (admin uses its own outcome buttons).

---

## 4. IDENTITY & LINKING

Each OPEN_NOW contains SIGNAL_ID.

All feedback is linked to SIGNAL_ID.

If SIGNAL_ID missing → feedback disabled.

---

## 5. ANTI-SPAM / ANTI-FRAUD RULES

### 5.1 One vote per user per SIGNAL_ID
Key: (signal_id + user_id)

If user tries to vote again:
- allow update (overwrite previous vote) OR
- reject with "Already voted"
(Overwrite preferred, but log changes.)

### 5.2 Voting window
Feedback is allowed only for a limited time window:
- default: OPEN_NOW time + expiry + 10 minutes grace
After that:
- buttons can remain but bot ignores callbacks.

### 5.3 Optional eligibility filter (future)
Only users who are channel members can vote.
(Requires admin rights / API checks. Optional.)

---

## 6. PRIVACY MODEL

Member votes must NOT be posted publicly as individual reports.

Only aggregated results are published:
- in Admin Analytics topic (recommended)
- optionally once per day in Elite

No user names exposed.

---

## 7. DATA STORAGE (PERSISTENT)

Store feedback in:
`/opt/binarybot/data/member_feedback.json`

Example:

{
  "meta": {"version":"1.0.0"},
  "items": {
    "EURUSD_M1_20260304_001": {
      "signal_id": "EURUSD_M1_20260304_001",
      "tier": "BASIC",
      "votes": {
        "12345": {"vote":"WIN","at_utc":"2026-03-04T08:25:20Z"},
        "67890": {"vote":"LOSE","at_utc":"2026-03-04T08:25:40Z"}
      }
    }
  }
}

Additionally maintain aggregated counters per signal:
- wins_count
- losses_count
- missed_count
- late_entry_count (optional)
- payout_issue_count (optional)

Aggregation must be recomputable from raw votes.

---

## 8. AGGREGATION & REPORTING

### 8.1 Per-signal aggregation (admin view)
For each SIGNAL_ID:
- AdminOutcome (WIN/LOSE/MISSED)
- MemberFeedback summary by tier:
  FREE:  W/L/M (n=)
  BASIC: W/L/M (n=)
  PRO:   W/L/M (n=)
  ELITE: W/L/M (n=)

### 8.2 Daily summary (admin)
Once per day (after reset):
- total OPEN_NOW sent per tier
- % silent time (tiers hit limits)
- aggregated member W/L/M per tier
- mismatch rate:
  (member consensus != admin outcome)

This helps detect if members execute late or misunderstand.

---

## 9. MISMATCH DETECTION (REPUTATION PROTECTION)

Define:
MemberConsensus = argmax(W/L/M) if votes >= min_votes_threshold

If consensus differs from admin outcome:
- log mismatch event
- flag the signal for review

This does NOT change the admin outcome.

---

## 10. OBSERVABILITY EVENTS

Log:
- MEMBER_VOTE_RECEIVED
- MEMBER_VOTE_UPDATED
- VOTING_WINDOW_EXPIRED
- FEEDBACK_AGGREGATED
- FEEDBACK_MISMATCH_FLAGGED

Include:
signal_id, tier, counts, timestamp_utc.

---

## 11. GUARANTEES

If implemented correctly:
- members can provide feedback without exposing identities
- admin retains canonical truth
- you can measure perceived quality and execution issues
- reputation risk is reduced via transparent evidence

---

End of MEMBER_FEEDBACK_SPEC.md
