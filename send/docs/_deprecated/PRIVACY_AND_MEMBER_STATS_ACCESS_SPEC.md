# PRIVACY_AND_MEMBER_STATS_ACCESS_SPEC.md
BinaryBot — Privacy Model for Member Stats (Elite Feedback)
Version: 1.0.0
Status: Canonical

Linked Documents:
ELITE_MEMBER_FEEDBACK_AND_LEADERBOARD_SPEC.md
CHANNEL_CONFIG_SPEC.md
OBSERVABILITY_LOGGING_SPEC.md
TELEGRAM_UX.md
GOVERNANCE_AND_CHANGE_CONTROL.md

---

## 1. PURPOSE

Define strict privacy rules for:
- member identity (telegram_user_id)
- member stats visibility
- delivery channels (public vs private)
- prevention of cross-user data leakage

Goal:
Each Elite member can access ONLY their own stats, privately.
Admin can access full global + per-user statistics.

---

## 2. ROLES

### 2.1 ADMIN
- full access
- can view global metrics and any member profile
- can export summaries
- can audit suspicious patterns

### 2.2 ELITE MEMBER
- can submit outcomes (WIN/LOSE/MISSED) and reasons for OPEN_NOW
- can view ONLY own stats
- receives stats ONLY in private DM with bot

### 2.3 PUBLIC CHANNELS (FREE/BASIC/PRO/ELITE)
- are considered public broadcast surfaces
- must never display any user IDs or per-user data

---

## 3. ID CONFIDENTIALITY RULES (HARD)

### 3.1 Never show telegram_user_id in public
Forbidden surfaces:
- any channel message
- any group topic
- any pinned message
- any leaderboard message
- any callback alert text visible to the channel

Allowed surfaces:
- internal storage (DB/JSON)
- admin-only logs (private admin topic)
- private DM to the same user (self-only)

### 3.2 Never allow user-to-user queries
Members cannot run commands like:
- /stats <other_user>
- /leaderboard
- /top
- /compare

Any attempt:
→ deny + log event

---

## 4. MEMBER ID DISCLOSURE (SELF-ONLY)

### 4.1 When user “logs in”
Definition of “logged in”:
- user starts DM with bot (/start) OR
- user presses a stat button that triggers DM prompt

Bot sends a PRIVATE message:
- “Your member reference is: <MEMBER_REF>”
- also provide instructions how to access stats

### 4.2 MEMBER_REF format (do not expose raw ID)
To avoid leaking raw telegram_user_id, we use a pseudonymous reference:

MEMBER_REF = short hash (stable, reversible only by admin system)
Example:
M-7F3A29C1

Rules:
- MEMBER_REF is derived from telegram_user_id with secret salt in .env
- stable across time for that user
- cannot be guessed by other members

Admin can map MEMBER_REF → telegram_user_id internally.

---

## 5. STATS ACCESS UX

### 5.1 In Elite channel
Under OPEN_NOW message:
- buttons for outcome + reason (as specified)

When user presses:
- vote is recorded silently
- channel does NOT receive personal confirmation text
- optional: ephemeral callback “Saved” (only visible to that user)

### 5.2 Private DM stats command (self-only)
Commands allowed in DM:
- /my_stats
- /my_history (last N votes)
- /my_reasons (top reasons)
- /my_ref (show MEMBER_REF again)

These commands must:
- verify DM chat context
- reply only in DM
- never forward into channels

### 5.3 “Stats button” convenience
Bot may send a DM keyboard with:
- 📊 My Stats
- 🧾 My History
- 🧠 My Mistakes (reasons)
- 🆔 My Member Ref

---

## 6. ADMIN ACCESS

Admin-only commands (in admin topic / private admin chat):
- /admin_stats_global
- /admin_stats_member <MEMBER_REF or user_id>
- /admin_reasons_global
- /admin_export_csv (optional)

Admin reports may include raw user_id ONLY in admin surfaces.

---

## 7. STORAGE REQUIREMENTS

Storage contains:
- telegram_user_id (internal)
- MEMBER_REF (pseudonym)
- votes per signal

Privacy invariant:
No public-facing renderer may read user_id fields.

Implementer note:
Keep a dedicated “public serializer” that strips identity always.

---

## 8. SECURITY CONTROLS

### 8.1 Hard gate: context check
If chat.type != "private" then:
- deny any “my stats” response
- respond with: “Open private chat with bot to view your stats.”
- do not include MEMBER_REF in the public reply

### 8.2 Rate limiting (basic)
Prevent spam/exfil attempts:
- limit /my_stats to e.g. 1 per 10 seconds per user
- limit admin exports

### 8.3 No echo of IDs
Never echo:
- telegram_user_id
- channel_id
- internal mapping data

---

## 9. OBSERVABILITY EVENTS

Must log (admin-only logs):
- MEMBER_REF_ISSUED (user started DM)
- MEMBER_STATS_VIEWED
- MEMBER_HISTORY_VIEWED
- PUBLIC_STATS_REQUEST_BLOCKED
- CROSS_USER_QUERY_BLOCKED
- ADMIN_VIEW_MEMBER_STATS

Logs must not reveal raw IDs outside admin surfaces.

---

## 10. GUARANTEES

If implemented correctly:
- members see only self stats in DM
- no ID leaks into channels
- admin retains full oversight
- privacy breaches are detectable via logs

---

End of PRIVACY_AND_MEMBER_STATS_ACCESS_SPEC.md