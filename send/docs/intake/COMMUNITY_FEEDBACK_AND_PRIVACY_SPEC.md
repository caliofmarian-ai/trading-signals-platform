# COMMUNITY_FEEDBACK_AND_PRIVACY_SPEC.md
BinaryBot — Community Feedback, Elite Outcome Reporting & Privacy Model
Version: 1.0.0
Status: Canonical

Linked Documents:
SIGNAL_DISTRIBUTION_SPEC.md
CHANNEL_CONFIG_SPEC.md
TELEGRAM_UX.md
OBSERVABILITY_LOGGING_SPEC.md
PERFORMANCE_ANALYTICS_SPEC.md
SYSTEM_INVARIANTS.md
OUTCOME_TRACKING_SPEC.md
GOVERNANCE_AND_CHANGE_CONTROL.md

---

# 1. PURPOSE

This document defines the full community feedback layer of BinaryBot.

It combines:

• Member feedback for signals  
• Elite outcome reporting dataset  
• Loss / missed reason tracking  
• Self-reported performance profiles  
• Optional leaderboard system  
• Strict privacy model for member identity and statistics

Goals:

- collect real execution feedback from users
- identify execution issues (late entry, wrong expiry, delay)
- allow members to learn from their own statistics
- provide admin with aggregated analytics
- protect member privacy at all times

IMPORTANT:

Self-reported feedback **does not override Admin Outcome**.

Admin outcome remains the canonical truth used for strategy evaluation.

---

# 2. SYSTEM SCOPE

Two feedback layers exist.

## 2.1 Community Feedback (Optional)

Applies to:

FREE  
BASIC  
PRO  
ELITE

Purpose:

- collect crowd perception of results
- detect misunderstandings or execution issues

Votes allowed:

WIN  
LOSE  
MISSED

Community feedback is aggregated only.

Individual identities are never shown.

---

## 2.2 Elite Outcome Dataset

Applies only to:

ELITE channel

Purpose:

- build a high-quality dataset of trade outcomes
- allow members to track their own performance
- allow admin analytics on real execution

Elite members can:

• report outcomes  
• specify reasons for losses or missed trades  
• access private statistics

---

# 3. OUTCOME TYPES

Three canonical outcomes exist.

WIN  
LOSE  
MISSED

Definitions:

WIN  
User executed and won.

LOSE  
User executed and lost.

MISSED  
User did not execute or entered too late.

---

# 4. SIGNAL IDENTITY

Each OPEN_NOW signal must contain a stable:

SIGNAL_ID

Example:

EURUSD_M1_20260304_001

All feedback entries must reference SIGNAL_ID.

If SIGNAL_ID is missing:

Feedback must be disabled.

---

# 5. FEEDBACK USER INTERFACE

Feedback buttons appear only under:

OPEN_NOW messages.

Buttons:

✅ WIN  
❌ LOSE  
⏳ MISSED

For Elite users:

Second-stage buttons appear after LOSE or MISSED.

---

# 6. TWO-STEP VOTING (ELITE)

Step 1 — Outcome

WIN  
LOSE  
MISSED

Step 2 — Reason (conditional)

If outcome = LOSE → show LOSE reasons  
If outcome = MISSED → show MISSED reasons

WIN does not require a reason.

Optional:

WIN_FAST  
WIN_LATE

---

# 7. REASON CATEGORIES

Reasons are strictly controlled.

Free-text explanations are not allowed.

## 7.1 LOSE Reasons

LATE_ENTRY  
WRONG_EXPIRY  
WRONG_DIRECTION  
SIGNAL_DELAY  
PLATFORM_LAG  
OTHER

---

## 7.2 MISSED Reasons

NO_TIME  
SAW_TOO_LATE  
DOUBTED_SIGNAL  
TECH_ISSUE  
OTHER

OTHER must be monitored in admin analytics.

---

# 8. VOTING WINDOW

Votes are allowed until:

OPEN_NOW timestamp + expiry + grace_period

Default grace period:

10 minutes

After window closes:

- buttons may remain visible
- callbacks must be ignored

---

# 9. DEDUPLICATION RULES

Each user may have only one outcome per signal.

Key:

(signal_id, user_id)

Vote updates are allowed within the voting window.

After window closes:

Votes are locked.

---

# 10. ELITE MEMBERSHIP VERIFICATION

Elite outcome submission requires active ELITE membership.

Verification method:

Telegram API:

getChatMember(ELITE_CHANNEL_ID, user_id)

Allowed statuses:

member  
administrator  
creator

If user is not an Elite member:

Vote must be rejected.

---

# 11. DATA STORAGE

Persistent storage is required.

Recommended path:

/opt/binarybot/data/feedback_dataset.json

Structure example:

{
  "signals": {
    "EURUSD_M1_20260304_001": {
      "open_at_utc": "2026-03-04T08:10:05Z",
      "expiry_sec": 300,
      "votes": {
        "123456789": {
          "outcome": "LOSE",
          "reason": "LATE_ENTRY",
          "updated_at_utc": "2026-03-04T08:12:01Z"
        }
      }
    }
  }
}

Counters must be rebuildable from raw votes.

---

# 12. USER PRIVATE STATISTICS

Elite members can access personal statistics via DM with the bot.

Commands allowed:

/my_stats  
/my_history  
/my_reasons  
/my_ref

These commands must:

• work only in private chat  
• return only that user's data  

---

# 13. MEMBER REFERENCE ID

To protect privacy, raw telegram_user_id must not be exposed.

Each user receives a pseudonymous reference:

MEMBER_REF

Example:

M-7F3A29C1

Generation rule:

MEMBER_REF = hash(telegram_user_id + secret_salt)

Properties:

• stable  
• unique  
• not guessable  

Admin can reverse-map internally.

---

# 14. PRIVATE STATISTICS METRICS

Minimum metrics:

total_rated_signals  
win_count  
lose_count  
missed_count  
win_rate  
participation_rate  
missed_rate

Optional metrics:

symbol breakdown  
session breakdown  
buffer_mode breakdown

---

# 15. LEADERBOARD SYSTEM (OPTIONAL)

Leaderboard is self-reported and must be labeled as such.

Types:

Accuracy leaderboard

WR_self = wins / (wins + losses)

Eligibility:

minimum sample size (e.g. ≥30 trades)

---

Activity leaderboard

Metric:

wins + losses + missed

---

Reliability score

reliability = activity_count × WR_self

This score is informational only.

---

# 16. ANTI-GAMING CONTROLS

Because outcomes cannot be broker-verified:

The system must include soft protections.

Rules:

• one vote per signal per user  
• minimum trade count for leaderboard eligibility  
• confidence labels based on activity

Confidence levels:

HIGH ≥100 trades  
MEDIUM 30–99  
LOW <30

---

# 17. PRIVACY MODEL

Strict privacy rules apply.

Members must never see:

• other members' identities  
• other members' stats  
• telegram_user_id values  

Channel messages must never display user identifiers.

Allowed surfaces for identity:

• internal storage  
• admin logs  
• private DM with same user

---

# 18. STATS ACCESS RULES

Stats are accessible only through DM.

If stats requested from channel:

Bot must reply:

"Open private chat with bot to view your stats."

No stats returned publicly.

---

# 19. ADMIN ACCESS

Admin commands:

/admin_stats_global  
/admin_stats_member  
/admin_reasons_summary  
/admin_export_csv

Admin can access full dataset.

Admin reports must never expose identities publicly.

---

# 20. OBSERVABILITY EVENTS

System must log:

MEMBER_VOTE_RECEIVED  
MEMBER_VOTE_UPDATED  
ELITE_VOTE_REASON_SET  
VOTING_WINDOW_EXPIRED  
FEEDBACK_AGGREGATED  
FEEDBACK_MISMATCH_FLAGGED  
MEMBER_STATS_VIEWED  
PUBLIC_STATS_REQUEST_BLOCKED  
ADMIN_VIEW_MEMBER_STATS

Logs must include:

timestamp_utc  
signal_id  
tier  
algo_version

---

# 21. REPUTATION PROTECTION

Consensus analysis may be used.

MemberConsensus = majority(WIN / LOSE / MISSED)

If consensus differs from AdminOutcome:

Signal may be flagged for review.

Admin outcome remains canonical.

---

# 22. SYSTEM GUARANTEES

If implemented correctly:

• users can provide feedback safely  
• members learn from private stats  
• admin receives real execution analytics  
• leaderboards remain transparent but non-authoritative  
• member privacy is always preserved  

---

End of COMMUNITY_FEEDBACK_AND_PRIVACY_SPEC.md