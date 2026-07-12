BINARYBOT — SIGNAL DISTRIBUTION ARCHITECTURE

Version: 1.0  
Status: CANONICAL SPECIFICATION  
Location: /opt/binarybot/docs/SIGNAL_DISTRIBUTION_ARCHITECTURE.md


------------------------------------------------------------
1. PURPOSE
------------------------------------------------------------

This document defines how trading signals produced by
the BinaryBot engine are distributed to users.

The distribution system connects the trading engine
with the external communication channels used
to deliver signals to subscribers.

Primary distribution medium:

Telegram channels.


------------------------------------------------------------
2. POSITION IN SYSTEM ARCHITECTURE
------------------------------------------------------------

The distribution layer sits between the signal engine
and the final user channels.

System architecture:

MARKET DATA
↓
ENGINE
↓
FSM SIGNAL DECISION
↓
OBSERVABILITY
↓
SIGNAL DISTRIBUTION
↓
TELEGRAM CHANNELS
↓
USERS


------------------------------------------------------------
3. SIGNAL LIFECYCLE
------------------------------------------------------------

Signals move through several states.

Signal states:

PRE  
CONFIRM  
OPEN_NOW  
RESULT

Each state may be distributed to different channels.


------------------------------------------------------------
4. SIGNAL DISTRIBUTION TIERS
------------------------------------------------------------

BinaryBot uses a multi-tier distribution model.

Tier 1 — FREE

Purpose:

marketing and user acquisition.

Content:

PRE signals only.


------------------------------------------------------------

Tier 2 — STANDARD

Purpose:

basic subscription.

Content:

PRE  
CONFIRM


------------------------------------------------------------

Tier 3 — PRO

Purpose:

advanced signal access.

Content:

PRE  
CONFIRM  
OPEN_NOW


------------------------------------------------------------

Tier 4 — VIP

Purpose:

full signal access.

Content:

PRE  
CONFIRM  
OPEN_NOW  
RESULT


------------------------------------------------------------
5. TELEGRAM CHANNEL STRUCTURE
------------------------------------------------------------

Each tier corresponds to a Telegram channel.

Example structure:

BinaryBot FREE

BinaryBot STANDARD

BinaryBot PRO

BinaryBot VIP


Each channel has a unique Telegram Chat ID.


------------------------------------------------------------
6. SIGNAL DISTRIBUTION FLOW
------------------------------------------------------------

Distribution pipeline:

Signal Engine
↓
FSM Decision
↓
Signal Event Generated
↓
Distribution Router
↓
Tier Filter
↓
Telegram Publisher
↓
Channel Delivery


------------------------------------------------------------
7. DISTRIBUTION ROUTER
------------------------------------------------------------

The distribution router determines
which channels receive a signal.

Example logic:

if signal_state == PRE

send_to:

FREE
STANDARD
PRO
VIP


if signal_state == CONFIRM

send_to:

STANDARD
PRO
VIP


if signal_state == OPEN_NOW

send_to:

PRO
VIP


if signal_state == RESULT

send_to:

VIP


------------------------------------------------------------
8. TELEGRAM MESSAGE FORMAT
------------------------------------------------------------

Example PRE message:

PRE SIGNAL

PAIR: EURAUD
TIMEFRAME: 1m

TREND: WITH_TREND
SCORE: 72.4

Waiting confirmation.


Example CONFIRM message:

CONFIRM SIGNAL

PAIR: EURAUD

Direction: CALL
Entry: 1.07240


Example OPEN_NOW message:

OPEN NOW

PAIR: EURAUD
Direction: CALL
Expiry: 5 minutes


Example RESULT message:

RESULT

PAIR: EURAUD
Outcome: WIN


------------------------------------------------------------
9. TELEGRAM DELIVERY SYSTEM
------------------------------------------------------------

Signal delivery is handled by the
Telegram publishing module.

Responsibilities:

• send formatted messages
• ensure delivery reliability
• handle Telegram rate limits
• retry failed messages


------------------------------------------------------------
10. RATE LIMIT MANAGEMENT
------------------------------------------------------------

Telegram enforces message rate limits.

The distribution system must:

queue messages

avoid flooding

retry failed sends

Example protection:

max_messages_per_second = 20


------------------------------------------------------------
11. DELIVERY LOGGING
------------------------------------------------------------

All distribution events must be logged.

Log location:

/opt/binarybot/observability/distribution_events.jsonl


Example event:

event_type: tier_publish

data:

symbol: EURAUD
tier: PRO
signal_state: CONFIRM


------------------------------------------------------------
12. FAILURE HANDLING
------------------------------------------------------------

If Telegram delivery fails:

retry message

log error

alert admin


Possible failures:

network issues

telegram api errors

channel permission issues


------------------------------------------------------------
13. DISTRIBUTION SECURITY
------------------------------------------------------------

Distribution channels must be protected.

Measures include:

restricted admin access

controlled bot permissions

channel membership management


------------------------------------------------------------
14. SIGNAL LEAK PREVENTION
------------------------------------------------------------

Signals may leak from private channels.

Mitigation strategies:

limited forwarding

subscriber watermarking

tier separation


------------------------------------------------------------
15. AFFILIATE INTEGRATION
------------------------------------------------------------

Affiliate influencers promote signal channels.

Users join channels via affiliate invitations.

Affiliate data includes:

affiliate_id

subscriber_count

generated_revenue


------------------------------------------------------------
16. AFFILIATE ACCESS CONTROL
------------------------------------------------------------

Affiliates receive limited administrative access.

They may view:

their subscriber count

their referral statistics

their commission earnings

They cannot access:

signal engine

strategy parameters

internal diagnostics


------------------------------------------------------------
17. FUTURE DISTRIBUTION EXTENSIONS
------------------------------------------------------------

Possible future upgrades:

Discord signal distribution

Web dashboard

Mobile application

Signal API


------------------------------------------------------------
18. RELATION TO OTHER SPECIFICATIONS
------------------------------------------------------------

Related documents:

AFFILIATE_SIGNAL_DISTRIBUTION_MODEL.md  
ROLE_AND_PERMISSION_MATRIX_SPEC.md  
CONTROL_PANEL_HIERARCHY_AND_INTELLIGENCE_SPEC.md  
SIGNAL_ECONOMICS_AND_MONETIZATION_MODEL.md  


------------------------------------------------------------
19. FINAL STATEMENT
------------------------------------------------------------

The signal distribution architecture ensures that
BinaryBot signals are delivered reliably, securely,
and efficiently to the appropriate user tiers.

This architecture supports both subscription-based
access and affiliate-driven growth of the signal ecosystem.