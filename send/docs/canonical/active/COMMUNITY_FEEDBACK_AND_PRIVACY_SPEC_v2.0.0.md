# COMMUNITY_FEEDBACK_AND_PRIVACY_SPEC_v2.0.0.md

**Canonical Name:** COMMUNITY_FEEDBACK_AND_PRIVACY_SPEC  
**Version:** 2.0.0  
**Status:** Active Canonical Specification  
**Owner:** BinaryBot / DROPi Signals  
**Canonical Path:** `send/docs/canonical/active/COMMUNITY_FEEDBACK_AND_PRIVACY_SPEC_v2.0.0.md`  
**Governance Record:** canonical-reconciliation-01 (OWNER-001 = A)  
**Promoted:** 2026-07-12  

**Authority:** This document is the authoritative canonical specification for the community feedback, elite outcome reporting, and member privacy domain of BinaryBot / DROPi Signals. All implementation, design, and governance decisions regarding community feedback and member privacy must conform to this document.

**Predecessor / Superseded Documents:**  
- `send/docs/intake/COMMUNITY_FEEDBACK_AND_PRIVACY_SPEC.md` — intake source; retained as historical record.  
- `send/docs/_deprecated/ELITE_FEEDBACK_SPEC.md` — deprecated predecessor; superseded by this document.  
- `send/docs/_deprecated/ELITE_MEMBER_FEEDBACK_AND_LEADERBOARD_SPEC.md` — deprecated predecessor; superseded by this document.  
- `send/docs/_deprecated/MEMBER_FEEDBACK_SPEC.md` — deprecated predecessor; superseded by this document.  
- `send/docs/_deprecated/PRIVACY_AND_MEMBER_STATS_ACCESS_SPEC.md` — deprecated predecessor; superseded by this document.  

**Linked Documents:**  
- `send/docs/canonical/active/SIGNAL_DISTRIBUTION_SPEC_v2.0.0.md`  
- `send/docs/canonical/active/CHANNEL_CONFIG_SPEC_v2.0.0.md`  
- `send/docs/canonical/active/TELEGRAM_UX_v2.0.0.md`  
- `send/docs/canonical/active/OBSERVABILITY_LOGGING_SPEC_v2.0.0.md`  
- `send/docs/canonical/active/PERFORMANCE_ANALYTICS_SPEC_v2.0.0.md`  
- `send/docs/canonical/active/SYSTEM_INVARIANTS_v2.0.0.md`  
- `send/docs/canonical/active/OUTCOME_TRACKING_SPEC_v2.0.0.md`  
- `send/docs/canonical/active/GOVERNANCE_AND_CHANGE_CONTROL_v2.0.0.md`  
- `send/docs/canonical/active/SECURITY_MODEL_v2.0.0.md`  

---

## 1. PURPOSE

This document defines the complete community feedback layer of BinaryBot.

It combines:

- Member feedback for signals
- Elite outcome reporting dataset
- Loss / missed reason tracking
- Self-reported performance profiles
- Optional leaderboard system
- Strict privacy model for member identity and statistics

Goals:

- Collect real execution feedback from users
- Identify execution issues (late entry, wrong expiry, delay)
- Allow members to learn from their own statistics
- Provide admin with aggregated analytics
- Protect member privacy at all times

**IMPORTANT:**

Self-reported feedback **does not override Admin Outcome**.

Admin outcome remains the canonical truth used for strategy evaluation.

---

## 2. SYSTEM SCOPE

Two feedback layers exist.

### 2.1 Community Feedback (Optional)

Applies to:

- FREE
- BASIC
- PRO
- ELITE

Purpose:

- Collect crowd perception of results
- Detect misunderstandings or execution issues

Votes allowed:

- WIN
- LOSE
- MISSED

Community feedback is aggregated only.

Individual identities are never shown.

---

### 2.2 Elite Outcome Dataset

Applies only to: **ELITE** channel

Purpose:

- Build a high-quality dataset of trade outcomes
- Allow members to track their own performance
- Allow admin analytics on real execution

Elite members can:

- Report outcomes
- Specify reasons for losses or missed trades
- Access private statistics

---

## 3. OUTCOME TYPES

Three canonical outcomes exist.

| Outcome | Definition |
|---|---|
| WIN | User executed and won. |
| LOSE | User executed and lost. |
| MISSED | User did not execute or entered too late. |

---

## 4. SIGNAL IDENTITY

Each OPEN_NOW signal must contain a stable `SIGNAL_ID`.

Example: `EURUSD_M1_20260304_001`

All feedback entries must reference `SIGNAL_ID`.

If `SIGNAL_ID` is missing: feedback must be disabled.

---

## 5. FEEDBACK USER INTERFACE

Feedback buttons appear only under OPEN_NOW messages.

Buttons:

- ✅ WIN
- ❌ LOSE
- ⏳ MISSED

For Elite users: second-stage buttons appear after LOSE or MISSED.

---

## 6. TWO-STEP VOTING (ELITE)

**Step 1 — Outcome**

WIN / LOSE / MISSED

**Step 2 — Reason (conditional)**

- If outcome = LOSE → show LOSE reasons
- If outcome = MISSED → show MISSED reasons
- WIN does not require a reason.

Optional: WIN_FAST / WIN_LATE

---

## 7. REASON CATEGORIES

Reasons are strictly controlled. Free-text explanations are not allowed.

### 7.1 LOSE Reasons

- LATE_ENTRY
- WRONG_EXPIRY
- WRONG_DIRECTION
- SIGNAL_DELAY
- PLATFORM_LAG
- OTHER

### 7.2 MISSED Reasons

- NO_TIME
- SAW_TOO_LATE
- DOUBTED_SIGNAL
- TECH_ISSUE
- OTHER

OTHER must be monitored in admin analytics.

---

## 8. VOTING WINDOW

Votes are allowed until: `OPEN_NOW timestamp + expiry + grace_period`

Default grace period: **10 minutes**

After window closes:

- Buttons may remain visible
- Callbacks must be ignored

---

## 9. DEDUPLICATION RULES

Each user may have only one outcome per signal.

Key: `(signal_id, user_id)`

Vote updates are allowed within the voting window.

After window closes: votes are locked.

---

## 10. ELITE MEMBERSHIP VERIFICATION

Elite outcome submission requires active ELITE membership.

Verification method: Telegram API `getChatMember(ELITE_CHANNEL_ID, user_id)`

Allowed statuses: `member`, `administrator`, `creator`

If user is not an Elite member: vote must be rejected.

---

## 11. DATA STORAGE

Persistent storage is required.

Recommended path: `data/feedback_dataset.json`

Structure example:

```json
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
```

Counters must be rebuildable from raw votes.

---

## 12. USER PRIVATE STATISTICS

Elite members can access personal statistics via DM with the bot.

Commands allowed:

- `/my_stats`
- `/my_history`
- `/my_reasons`
- `/my_ref`

These commands must:

- Work only in private chat
- Return only that user's data

---

## 13. MEMBER REFERENCE ID

To protect privacy, raw `telegram_user_id` must not be exposed.

Each user receives a pseudonymous reference: `MEMBER_REF`

Example: `M-7F3A29C1`

Generation rule: `MEMBER_REF = hash(telegram_user_id + secret_salt)`

Properties:

- Stable
- Unique
- Not guessable

Admin can reverse-map internally.

---

## 14. PRIVATE STATISTICS METRICS

Minimum metrics:

- `total_rated_signals`
- `win_count`
- `lose_count`
- `missed_count`
- `win_rate`
- `participation_rate`
- `missed_rate`

Optional metrics:

- Symbol breakdown
- Session breakdown
- `buffer_mode` breakdown

---

## 15. LEADERBOARD SYSTEM (OPTIONAL)

Leaderboard is self-reported and must be labeled as such.

**Accuracy leaderboard:**

`WR_self = wins / (wins + losses)`

Eligibility: minimum sample size (e.g. ≥30 trades)

**Activity leaderboard:**

Metric: `wins + losses + missed`

**Reliability score:**

`reliability = activity_count × WR_self`

This score is informational only.

---

## 16. ANTI-GAMING CONTROLS

Because outcomes cannot be broker-verified, the system must include soft protections.

Rules:

- One vote per signal per user
- Minimum trade count for leaderboard eligibility
- Confidence labels based on activity

Confidence levels:

| Level | Threshold |
|---|---|
| HIGH | ≥100 trades |
| MEDIUM | 30–99 trades |
| LOW | <30 trades |

---

## 17. PRIVACY MODEL

Strict privacy rules apply.

Members must never see:

- Other members' identities
- Other members' stats
- `telegram_user_id` values

Channel messages must never display user identifiers.

Allowed surfaces for identity:

- Internal storage
- Admin logs
- Private DM with same user

---

## 18. STATS ACCESS RULES

Stats are accessible only through DM.

If stats requested from channel: bot must reply:

> "Open private chat with bot to view your stats."

No stats returned publicly.

---

## 19. ADMIN ACCESS

Admin commands:

- `/admin_stats_global`
- `/admin_stats_member`
- `/admin_reasons_summary`
- `/admin_export_csv`

Admin can access full dataset.

Admin reports must never expose identities publicly.

---

## 20. OBSERVABILITY EVENTS

System must log:

- `MEMBER_VOTE_RECEIVED`
- `MEMBER_VOTE_UPDATED`
- `ELITE_VOTE_REASON_SET`
- `VOTING_WINDOW_EXPIRED`
- `FEEDBACK_AGGREGATED`
- `FEEDBACK_MISMATCH_FLAGGED`
- `MEMBER_STATS_VIEWED`
- `PUBLIC_STATS_REQUEST_BLOCKED`
- `ADMIN_VIEW_MEMBER_STATS`

Logs must include: `timestamp_utc`, `signal_id`, `tier`, `algo_version`

Observability implementation must conform to `OBSERVABILITY_LOGGING_SPEC_v2.0.0.md`.

---

## 21. REPUTATION PROTECTION

Consensus analysis may be used.

`MemberConsensus = majority(WIN / LOSE / MISSED)`

If consensus differs from AdminOutcome: signal may be flagged for review.

Admin outcome remains canonical.

---

## 22. SYSTEM GUARANTEES

If implemented correctly:

- Users can provide feedback safely
- Members learn from private stats
- Admin receives real execution analytics
- Leaderboards remain transparent but non-authoritative
- Member privacy is always preserved

---

## 23. CANONICAL VERSION HISTORY

| Version | Date | Description |
|---|---|---|
| 2.0.0 | 2026-07-12 | Promoted to active canonical status (OWNER-001 = A, canonical-reconciliation-01). Cross-references updated to canonical paths. |
| 1.0.0 | — | Intake document: `send/docs/intake/COMMUNITY_FEEDBACK_AND_PRIVACY_SPEC.md` |

---

*End of COMMUNITY_FEEDBACK_AND_PRIVACY_SPEC_v2.0.0.md*
