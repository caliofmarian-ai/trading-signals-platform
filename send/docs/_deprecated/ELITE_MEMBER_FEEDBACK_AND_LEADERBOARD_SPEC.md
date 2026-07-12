# ELITE_MEMBER_FEEDBACK_AND_LEADERBOARD_SPEC.md
BinaryBot — Elite Feedback + Leaderboard (Self-Reported)
Version: 1.0.0
Status: Canonical (Elite Layer)

Linked Documents:
MEMBER_FEEDBACK_SPEC.md
SIGNAL_DISTRIBUTION_SPEC.md
CHANNEL_CONFIG_SPEC.md
OBSERVABILITY_LOGGING_SPEC.md
PERFORMANCE_ANALYTICS_SPEC.md
OUTCOME_TRACKING_SPEC.md

---

## 1. PURPOSE

Enable Elite members to report outcomes for OPEN_NOW signals.
Build:
- per-member performance profile (self-reported)
- aggregated loss reasons (execution issues)
- optional leaderboard (gamified, but controlled)

IMPORTANT:
These stats are SELF-REPORTED and do not override Admin Outcome (canonical truth).

---

## 2. WHERE IT RUNS

ONLY in:
- ELITE Telegram Channel

Buttons appear ONLY under OPEN_NOW messages sent to ELITE.

---

## 3. IDENTITY MODEL

Key fields:
- telegram_user_id (from callback)
- signal_id (embedded in OPEN_NOW)
- tier = ELITE

Unique vote key:
(user_id, signal_id)

One active outcome per user per signal.
User can update within voting window.

---

## 4. TWO-STEP VOTING UX

### Step 1: Outcome buttons
Buttons:
- ✅ WIN
- ❌ LOSE
- ⏳ MISSED

### Step 2: Reason buttons (conditional)
If outcome = LOSE → show REASON_LOSE buttons
If outcome = MISSED → show REASON_MISSED buttons
If outcome = WIN → no reason required (optional: “WIN_FAST / WIN_LATE” if you want)

No free-text reasons.

---

## 5. REASON CATEGORIES (CONTROLLED)

### 5.1 LOSE reasons
- LATE_ENTRY (entered too late)
- WRONG_EXPIRY (selected wrong expiry)
- WRONG_DIRECTION (clicked opposite)
- SIGNAL_DELAY (saw signal late / notification issue)
- PLATFORM_LAG (app lag / execution lag)
- OTHER (last resort)

### 5.2 MISSED reasons
- NO_TIME (was busy)
- SAW_TOO_LATE (saw after expiry)
- DOUBTED_SIGNAL (did not trust it)
- TECH_ISSUE (phone/net/app)
- OTHER

NOTE:
“OTHER” should be allowed but tracked separately and reviewed (it’s where people lie most).

---

## 6. VOTING WINDOW

Allowed until:
OPEN_NOW timestamp + expiry + grace

Grace default:
10 minutes

After window:
- callbacks ignored
- optionally edit buttons to “Voting closed”

---

## 7. DATA STORAGE (PERSISTENT)

File:
`/opt/binarybot/data/elite_feedback.json`

Schema (example):
{
  "meta": {"version":"1.0.0"},
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
  },
  "members": {
    "123456789": {
      "wins": 10,
      "losses": 6,
      "missed": 3,
      "lose_reasons": {"LATE_ENTRY":4,"WRONG_EXPIRY":2},
      "missed_reasons": {"NO_TIME":2,"SAW_TOO_LATE":1}
    }
  }
}

Counters must be rebuildable from raw votes.

---

## 8. LEADERBOARD (OPTIONAL BUT REQUESTED)

Leaderboard types:

### 8.1 Accuracy leaderboard
Metric:
WR_self = wins / (wins + losses)

Eligibility rules:
- minimum trades threshold, e.g. (wins+losses) >= 30
- MISSED excluded from WR

### 8.2 Activity leaderboard
Metric:
active_count = wins + losses + missed

### 8.3 Reliability score (anti-cheat simple)
Metric:
reliability = active_count * WR_self
(only for display, does not claim truth)

Leaderboard is SELF-REPORTED and must be labeled:
“Self-reported by members. Not verified.”

---

## 9. ANTI-LIE / ANTI-GAMING CONTROLS (LIGHT)

We cannot fully verify outcomes (no broker integration).
But we can reduce abuse:

- One vote per user per signal (updates allowed within window)
- Minimum sample for leaderboard eligibility
- Show “confidence label” next to member:
  HIGH if active_count>=100
  MED if 30..99
  LOW if <30
- Track “inconsistency flags”:
  If member reports WIN too often relative to admin outcomes over N signals → flag for review (no punishment, only admin visibility)

---

## 10. ADMIN VISIBILITY (PRIVATE)

Admin can request:
- /elite_stats USER_ID (or reply to a message)
- /elite_leaderboard
- /elite_reasons_summary (top reasons)

Admin sees:
- top winners (self reported)
- top losers
- top “missed”
- reasons distribution

Members should NOT see other members’ detailed reasons unless you explicitly allow a public leaderboard summary.

---

## 11. OBSERVABILITY EVENTS

Log:
- ELITE_VOTE_OUTCOME_SET
- ELITE_VOTE_REASON_SET
- ELITE_VOTE_UPDATED
- ELITE_VOTING_CLOSED
- ELITE_LEADERBOARD_GENERATED

---

## 12. GUARANTEES

- Elite members can report outcomes quickly
- Loss reasons are structured and analyzable
- You can identify execution problems (late entry, wrong expiry, delays)
- Leaderboard exists but is clearly labeled as self-reported

---

End of ELITE_MEMBER_FEEDBACK_AND_LEADERBOARD_SPEC.md
