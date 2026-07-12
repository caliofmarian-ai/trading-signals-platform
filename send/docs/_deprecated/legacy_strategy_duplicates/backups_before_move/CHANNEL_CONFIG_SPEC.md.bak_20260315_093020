CHANNEL CONFIG SPEC

BinaryBot — Channel Configuration Specification
Version: 1.1.0
Status: Canonical

Linked Documents:
SIGNAL_DISTRIBUTION_SPEC.md
TELEGRAM_UX.md
OBSERVABILITY_LOGGING_SPEC.md
PARAMS_REFERENCE.md

---

1. PURPOSE

This document defines the configuration layer used by the signal distribution system.

It contains operational parameters required for publishing signals to Telegram channels.

The configuration layer must remain independent from:

• trading algorithm logic  
• signal scoring models  
• risk calculations  

Its purpose is to control how signals are routed to external communication channels.

---

2. CHANNEL TIERS

The system distributes signals across four Telegram channel tiers.

FREE  
BASIC  
PRO  
ELITE  

Each tier corresponds to a Telegram broadcast channel where signals are published.

These channels represent different service levels for subscribers.

Tier behaviour is defined in SIGNAL_DISTRIBUTION_SPEC.md.

---

3. TELEGRAM CHANNEL IDENTIFIERS

Each channel tier must be mapped to a Telegram channel ID.

Example configuration:

FREE_CHANNEL_ID = -1003510282695  
BASIC_CHANNEL_ID = -1003769019175  
PRO_CHANNEL_ID = -1003823255426  
ELITE_CHANNEL_ID = -1003776464915  

These identifiers are used by the Telegram Bot API when publishing messages.

Rules:

• Channel IDs must never be hardcoded inside trading logic.  
• Channel IDs must be loaded from configuration during system startup.  
• Missing channel IDs must trigger a critical admin log.

If a tier does not have a valid channel ID:

The tier must be treated as DISABLED.

Disabled tiers receive no signals.

---

4. SIGNAL DELIVERY TARGETS

Each signal stage may be delivered to one or multiple tiers depending on tier state.

Typical broadcast:

PRE → all ACTIVE tiers  
CONFIRM → all ACTIVE tiers  
OPEN_NOW → all ACTIVE tiers  

If a tier becomes SILENT (daily limit reached) it must not receive any signal stage.

Blocked stages include:

PRE  
CONFIRM  
OPEN_NOW  

This ensures subscribers never receive partial signals.

---

5. DAILY LIMIT CONFIGURATION

Daily signal limits are configured per tier.

Limits apply only to OPEN_NOW signals.

FREE_LIMIT = 6  
BASIC_LIMIT = 20  
PRO_LIMIT = 50  
ELITE_LIMIT = UNLIMITED  

Rules:

PRE signals do not increase counters.  
CONFIRM signals do not increase counters.  

Only OPEN_NOW signals increment the tier counter.

Counters increase only when a signal is successfully published to Telegram.

Failed publishes must not increase counters.

---

6. TIER STATE

Each tier maintains a runtime state.

Possible states:

ACTIVE  
SILENT  

ACTIVE  
Tier receives signals normally.

SILENT  
Tier does not receive any signals.

State transition rule:

If OPEN_NOW counter reaches the configured limit  
→ tier transitions to SILENT immediately.

ELITE tier never transitions to SILENT.

---

7. DAILY RESET CONFIGURATION

Signal limits reset once per trading day.

Reset moment:

08:10 Europe/London

This corresponds to ten minutes after the London market opens.

Timezone used:

Europe/London

This ensures correct daylight saving adjustments.

Reset must be calculated using the Europe/London timezone.

---

8. RESET EFFECT

At reset time the following operations occur:

FREE counter reset to zero  
BASIC counter reset to zero  
PRO counter reset to zero  
ELITE counter reset to zero  

Tier states are updated:

FREE → ACTIVE  
BASIC → ACTIVE  
PRO → ACTIVE  
ELITE → ACTIVE  

Reset must occur only once per trading day.

Reset state must be persisted to prevent duplicate resets after restart.

---

9. CONFIGURATION STORAGE

Channel configuration must be stored in a persistent configuration source.

Recommended storage:

configuration JSON file

Example:

config/channel_config.json

Structure example:

{
  "FREE_CHANNEL_ID": -1003510282695,
  "BASIC_CHANNEL_ID": -1003769019175,
  "PRO_CHANNEL_ID": -1003823255426,
  "ELITE_CHANNEL_ID": -1003776464915
}

Alternative sources:

environment variables  
secure configuration service

The configuration must survive bot restarts.

---

10. ADMIN VISIBILITY

Administrators must be able to view current configuration parameters through the admin interface.

Visible values include:

channel IDs  
daily limits  
current counters  
tier state  
reset time  

Example admin panel output:

FREE → ACTIVE (2/6 today)  
BASIC → ACTIVE (7/20 today)  
PRO → ACTIVE (13/50 today)  
ELITE → ACTIVE (unlimited)

This allows operational verification of system status.

---

11. AUDIT REQUIREMENTS

The system must log configuration related events.

Required log events:

daily reset executed  
tier became silent  
tier returned to active  
signal delivered to tier  
signal blocked due to limit  
telegram publish failure  

These events must be recorded in the system observability logs.

---

12. CONFIGURATION GUARANTEES

Correct configuration ensures:

predictable signal distribution  
fair subscriber segmentation  
stable service tiers  
transparent operational behavior  
safe bot restarts  

This layer guarantees that channel routing remains fully deterministic and independent from trading logic.
---

13. ELITE MEMBERSHIP VERIFICATION

The ELITE tier includes additional features not available to other tiers:

• outcome feedback (WIN / LOSE / MISSED)  
• private personal statistics (/mystats)  
• contribution to performance analytics  

Access to these features is restricted to active members of the ELITE channel.

Membership verification rule:

Before accepting feedback or returning personal statistics, the system MUST verify that the requesting user is a member of the ELITE channel.

Verification method:

Telegram API call

getChatMember(ELITE_CHANNEL_ID, user_id)

Allowed membership statuses:

member  
administrator  
creator  

Rejected statuses:

left  
kicked  
restricted  

If the membership check fails:

• feedback submissions must be rejected  
• personal statistics must not be returned  
• the user must receive a private Telegram message explaining that ELITE membership is required.

---

ELITE BOT REQUIREMENT

The bot must be an ADMINISTRATOR in the ELITE channel.

Required permissions:

• read channel messages  
• access channel member information  

Without administrator permissions the system cannot verify ELITE membership.

If ELITE membership verification fails due to permission issues:

• a critical admin log must be generated  
• feedback system must be temporarily disabled until permissions are restored.

---

PRIVACY GUARANTEES

Membership verification must not expose user IDs publicly.

Rules:

• Telegram user IDs must never be posted in any public channel  
• User statistics must be delivered only in private chat with the bot  
• No user may access statistics of another user  

Admin users may access aggregated analytics across all ELITE members for system monitoring and performance evaluation.

End of CHANNEL_CONFIG_SPEC.md