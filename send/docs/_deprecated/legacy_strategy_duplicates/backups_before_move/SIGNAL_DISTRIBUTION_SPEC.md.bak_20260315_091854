SIGNAL_DISTRIBUTION_SPEC.md

BinaryBot — Signal Distribution Architecture
Version: 1.1.0
Status: Canonical

Linked Documents:
- ALGO_SPEC.md
- FSM_SPEC.md
- TELEGRAM_UX.md
- PARAMS_REFERENCE.md
- RISK_MODEL.md
- CHANNEL_CONFIG_SPEC.md

---

0. SCOPE & NON-GOALS

Scope:
This document defines the *policy + mechanics* for distributing trading signal stages to Telegram tier channels.

Non-goals:
- No changes to trading logic, signal detection, risk scoring, or FSM state transitions.
- Distribution layer must treat the trading engine as a black box that emits signal events.

---

1. PURPOSE

This document defines how trading signals are distributed across Telegram channel tiers.

The trading algorithm generates signals independently of the distribution layer.

This document governs:
- signal lifecycle broadcasting (PRE / CONFIRM / OPEN_NOW)
- channel tier logic (FREE / BASIC / PRO / ELITE)
- daily OPEN_NOW limits per tier
- tier silent mode rules
- daily reset behavior (Europe/London)
- signal identity consistency (same SIGNAL_ID across all stages)

This layer exists to separate trading logic from distribution policy.

---

2. DEFINITIONS

Signal Stage:
- PRE: Initial setup detection
- CONFIRM: Setup confirmation
- OPEN_NOW: Execution moment (entry signal)

Tier:
- One of: FREE, BASIC, PRO, ELITE

Tier State (distribution-layer state, NOT trading FSM):
- ACTIVE: tier receives signals
- SILENT: tier receives nothing until reset

Daily Limit:
- Maximum number of OPEN_NOW signals deliverable to a tier per trading day.

Delivery:
- A “successful publish” means Telegram API returned success for that tier/channel.

---

3. SIGNAL LIFECYCLE

Every trade idea may produce up to three stages:
PRE → CONFIRM → OPEN_NOW

All stages refer to the *same trade idea* and MUST share the same SIGNAL_ID.

Important:
- The distribution layer does not decide when a stage is generated.
- It only decides *where it gets posted*.

---

4. SIGNAL IDENTITY (MUST)

Each signal must contain a unique identifier: SIGNAL_ID

Example:
SIGNAL_ID: EURUSD_M15_20260304_001

Identity rule (strict):
- PRE, CONFIRM, OPEN_NOW belonging to the same trade idea MUST share the same SIGNAL_ID.
- No stage is allowed to invent a new SIGNAL_ID for the same trade idea.
- Deduplication keys must include: (tier, SIGNAL_ID, stage)

Rationale:
Guarantees traceability and prevents duplication across restarts or retries.

---

5. CHANNEL TIERS

The system distributes signals to four Telegram channel tiers:
- FREE
- BASIC
- PRO
- ELITE

Each tier maps to exactly one Telegram channel_id.

Channel IDs are configured in the bot configuration layer (see CHANNEL_CONFIG_SPEC.md).

---

6. TIER DISTRIBUTION MODEL (CORE RULE)

Signals may be broadcast to multiple tiers simultaneously.

Gating principle:
- If a tier is ACTIVE → it receives PRE, CONFIRM, OPEN_NOW as they come.
- If a tier is SILENT → it receives NOTHING (no PRE, no CONFIRM, no OPEN_NOW).

ELITE exception:
- ELITE never becomes SILENT (unlimited).

This enforces your rule:
“PRE/CONFIRM/OPEN_NOW se postează peste tot cât timp tier-ul e activ; după limită, tier-ul devine silent complet.”

---

7. DAILY OPEN_NOW LIMITS (COUNTS ONLY OPEN_NOW)

Daily limits apply ONLY to OPEN_NOW stage deliveries.

Limits per tier:
- FREE  : max 6 OPEN_NOW / day
- BASIC : max 20 OPEN_NOW / day
- PRO   : max 50 OPEN_NOW / day
- ELITE : unlimited

Counting rule (strict):
- The counter increases ONLY when an OPEN_NOW is successfully published to that tier.
- PRE and CONFIRM never increment counters.

---

8. SILENT MODE RULE (HARD BLOCK)

When a tier reaches its daily OPEN_NOW limit, it becomes SILENT immediately.

Silent tier must not receive:
- PRE
- CONFIRM
- OPEN_NOW

It remains SILENT until the next daily reset.

Example:
If FREE reaches 6 successful OPEN_NOW deliveries:
- FREE becomes SILENT
- FREE receives no further PRE/CONFIRM/OPEN_NOW that day
- BASIC/PRO/ELITE continue normally

---

9. COUNTER & STATE PERSISTENCE (MUST SURVIVE RESTART)

Each tier maintains:
- open_signals_today[tier] : integer
- tier_state[tier]         : ACTIVE|SILENT
- last_reset_epoch         : timestamp (or last_reset_date in Europe/London)

Persistence requirements:
- Counters and tier states MUST persist across bot restarts.
- Restart must not reset counters.
- Reset must be based on Europe/London day boundary defined in Section 10.

Suggested persistence keys (implementation hint):
- dist.open_signals_today.FREE
- dist.open_signals_today.BASIC
- dist.open_signals_today.PRO
- dist.open_signals_today.ELITE
- dist.tier_state.FREE
- dist.tier_state.BASIC
- dist.tier_state.PRO
- dist.tier_state.ELITE
- dist.last_reset_epoch

---

10. DAILY RESET RULE (LONDON + DST SAFE)

Daily reset time:
08:10 Europe/London

Meaning:
10 minutes after London market open.

At reset:
- open_signals_today[*] = 0
- tier_state[*] = ACTIVE
- last_reset_epoch updated

Timezone rule:
- All reset decisions must use Europe/London timezone to handle DST correctly.

Safety rule:
- Reset must be idempotent (if called twice, state remains correct).

---

11. CHANNEL MAPPING (CONFIG CONTRACT)

Tier → channel_id mapping must exist:

- FREE_CHANNEL_ID
- BASIC_CHANNEL_ID
- PRO_CHANNEL_ID
- ELITE_CHANNEL_ID

The distribution engine uses these mappings to publish signals.

If a mapping is missing:
- That tier is treated as DISABLED (do not publish; do not increment counters).
- A critical admin log must be emitted.

---

12. SIGNAL FLOW (ORDER OF OPERATIONS)

On each emitted signal stage from trading engine:

1) Normalize payload
   - ensure stage ∈ {PRE, CONFIRM, OPEN_NOW}
   - ensure SIGNAL_ID exists (hard fail if missing)

2) Resolve tier list
   - tiers = {FREE,BASIC,PRO,ELITE}

3) For each tier:
   a) Check tier_state[tier]
      - if SILENT → skip publish
   b) If stage == OPEN_NOW:
      - if tier != ELITE and open_signals_today[tier] >= limit[tier]
        → set tier_state[tier]=SILENT, skip publish
   c) Attempt Telegram publish
      - if success:
          - if stage == OPEN_NOW and tier != ELITE:
              increment open_signals_today[tier]
              if now open_signals_today[tier] == limit[tier]:
                  set tier_state[tier]=SILENT (effective for next signals)
      - if failure:
          - do NOT increment counters
          - log failure (see Section 13)

Important:
- “consumă limita” = ONLY successful OPEN_NOW publish.
- Silent gating blocks everything, including PRE/CONFIRM.

---

13. OBSERVABILITY & ADMIN LOGGING (MUST)

Every distribution action must generate an admin log event:

Event fields:
- timestamp (UTC + Europe/London local)
- stage (PRE|CONFIRM|OPEN_NOW)
- SIGNAL_ID
- symbol, timeframe (if available)
- tier
- decision (PUBLISHED | SKIPPED_SILENT | SKIPPED_LIMIT | FAILED)
- counter_before / counter_after (for OPEN_NOW)
- error (if failed)

This is mandatory for debugging + monetization trust.

---

14. FAILURE PROTECTION (GUARANTEES)

The distribution system must prevent:
- duplicate broadcasts per tier/stage/SIGNAL_ID
- counter corruption on retry
- silent tier leaks
- restart counter resets

Rules:
- Deduplication key: (tier, SIGNAL_ID, stage)
- Counter increments only on successful OPEN_NOW publish.
- State persisted before acknowledging “success” to the trading engine (or use transactional pattern).

---

15. GUARANTEES

If implemented correctly this system guarantees:
- predictable tier limits
- consistent lifecycle delivery (no partial leaks after silent)
- fair segmentation & monetization stability
- clear separation between trading logic and distribution policy
- DST-safe resets aligned with London session

---

16. ELITE FEEDBACK LAYER (OUTCOME COLLECTION)

The ELITE tier includes a feedback system used to collect real-world outcomes for OPEN_NOW signals.

Feedback applies ONLY to the ELITE tier.

Eligible feedback types:
- WIN
- LOSE
- MISSED

Scope rules:
- Feedback is allowed only for OPEN_NOW signals.
- PRE and CONFIRM signals are never rated.

Feedback buttons appear only in ELITE channel messages that contain OPEN_NOW signals.

Each feedback entry must reference:
- SIGNAL_ID
- user_id (Telegram user id)
- timestamp_utc
- outcome (WIN / LOSE / MISSED)

The purpose of this layer is to collect real execution data from ELITE members for statistical analysis.

This layer does NOT affect:
- trading logic
- signal scoring
- signal generation
- FSM behavior

---

17. ELITE ACCESS CONTROL (MEMBERSHIP CHECK)

Outcome reporting and personal statistics access are restricted to ELITE members.

Authorization rule:

Before accepting feedback or returning personal statistics, the system MUST verify that the user is a member of the ELITE channel.

Membership verification uses Telegram API:

getChatMember(ELITE_CHANNEL_ID, user_id)

Allowed statuses:
- member
- administrator
- creator

Rejected statuses:
- left
- kicked
- restricted

If the membership check fails:
- feedback is rejected
- personal statistics are not returned
- user receives a private message explaining that ELITE membership is required.

No manual whitelist of user IDs is used.

This ensures that:
- only paying ELITE members contribute to statistical data
- no manual maintenance of user lists is required
- access automatically follows Telegram membership state.

---

18. USER PRIVATE STATISTICS (ELITE ONLY)

ELITE members may request their personal trading statistics via private chat with the bot.

Statistics visibility rules:

- Each user may access ONLY their own statistics.
- No user can view statistics of other users.
- No statistics are posted in public channels.

Statistics are delivered via private Telegram chat with the bot.

Minimum metrics provided:

- total_signals_rated
- wins
- losses
- missed

Derived metrics:

WinRate:
wins / (wins + losses)

Accuracy:
wins / (wins + losses + missed)

MissRate:
missed / total_signals_rated

Admin visibility:

The admin may access aggregate statistics across all ELITE members, including:

- overall win rate
- overall participation rate
- symbol performance
- session performance

Privacy guarantees:

- user IDs are never exposed publicly
- personal statistics remain private
- only the admin can access aggregate analytics.



End of SIGNAL_DISTRIBUTION_SPEC.md