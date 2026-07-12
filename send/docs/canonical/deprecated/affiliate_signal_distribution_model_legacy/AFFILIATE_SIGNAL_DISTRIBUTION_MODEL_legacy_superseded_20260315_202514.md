BINARYBOT — AFFILIATE SIGNAL DISTRIBUTION MODEL

Version: 1.0  
Status: CANONICAL SPECIFICATION  
Location: /opt/binarybot/docs/AFFILIATE_SIGNAL_DISTRIBUTION_MODEL.md  


------------------------------------------------------------
1. PURPOSE
------------------------------------------------------------

This document defines the affiliate distribution model used
to expand the BinaryBot signal ecosystem through influencers
and trading communities.

The affiliate system allows external partners to:

• invite users into the signal ecosystem  
• monetize their audience through referral programs  
• receive a share of subscription revenue  

The system must remain:

• transparent  
• auditable  
• secure  
• isolated from core strategy internals  

Affiliates must never have access to:

• strategy parameters  
• diagnostics  
• observability logs  
• internal system intelligence  


------------------------------------------------------------
2. AFFILIATE CONCEPT
------------------------------------------------------------

An affiliate is an external promoter who brings users into
the signal ecosystem.

Typical affiliates include:

• trading influencers  
• Telegram channel owners  
• trading community leaders  
• YouTube trading educators  

Affiliates do not generate signals.
They only promote signal channels.

Their incentive is based on referral commissions.


------------------------------------------------------------
3. AFFILIATE ROLE
------------------------------------------------------------

Affiliates operate through the role:

AFFILIATE_ADMIN

Defined in:

ROLE_AND_PERMISSION_MATRIX_SPEC.md

Capabilities:

• view referral statistics  
• view subscriber counts  
• view earned commissions  

Restrictions:

• cannot access system strategy  
• cannot view diagnostics  
• cannot modify configuration  
• cannot see other affiliates' data  


------------------------------------------------------------
4. AFFILIATE USER FLOW
------------------------------------------------------------

Affiliate onboarding flow:

1. Influencer requests affiliate access
2. Admin approves affiliate account
3. System generates unique referral code
4. Affiliate receives promotional link

Example:

https://signals.dropi.ai/join?ref=TRADER_X


------------------------------------------------------------
5. REFERRAL TRACKING
------------------------------------------------------------

Each affiliate receives a unique referral identifier.

Example:

ref_code = TRADER_X

When a user joins a signal ecosystem:

1. referral link detected
2. user account created
3. affiliate reference stored

Example database record:

user_id: 987654
affiliate_code: TRADER_X
join_date: 2026-03-06


------------------------------------------------------------
6. SUBSCRIPTION CONVERSION
------------------------------------------------------------

Users may subscribe to different signal tiers:

FREE
BASIC
PRO
ELITE

When a referred user subscribes:

commission is attributed to the affiliate.

Example:

User subscription = PRO

Monthly price = $49

Affiliate share = 30%

Commission = $14.70


------------------------------------------------------------
7. COMMISSION STRUCTURE
------------------------------------------------------------

Commission models may vary.

Example baseline model:

FREE tier
Commission: 0%

BASIC tier
Commission: 20%

PRO tier
Commission: 30%

ELITE tier
Commission: 35%

Alternative models may include:

• flat referral bonus
• lifetime revenue share
• first month commission


------------------------------------------------------------
8. AFFILIATE DASHBOARD DATA
------------------------------------------------------------

Affiliate admins can access a limited dashboard.

Visible data:

• number of referred users
• active subscribers
• subscription tier distribution
• monthly commissions
• lifetime earnings

Example dashboard output:

Affiliate: TRADER_X

Referred Users: 148  
Active Subscribers: 92  

Tier Distribution:

FREE: 56  
BASIC: 21  
PRO: 13  
ELITE: 2  

Monthly Earnings: $1,274  


------------------------------------------------------------
9. DATA ISOLATION RULES
------------------------------------------------------------

Affiliates must only see their own data.

They must never see:

• users referred by other affiliates
• total system revenue
• system-wide subscriber counts
• strategy diagnostics

Isolation rule:

affiliate_data_scope = own_referrals_only


------------------------------------------------------------
10. AFFILIATE ADMIN EVENTS
------------------------------------------------------------

Affiliate operations must generate observability events.

Example event:

event_type: affiliate_event

Fields:

timestamp  
affiliate_id  
action  
result  

Example:

affiliate_event  
affiliate_id: TRADER_X  
action: referral_registered  
user_id: 987654  


------------------------------------------------------------
11. FRAUD PROTECTION
------------------------------------------------------------

The system must protect against affiliate abuse.

Possible fraud patterns:

• self-referral loops  
• fake accounts  
• subscription manipulation  

Detection rules:

• multiple accounts from same IP
• abnormal subscription bursts
• repeated cancellations


------------------------------------------------------------
12. PAYOUT SYSTEM
------------------------------------------------------------

Affiliate earnings accumulate in a commission ledger.

Payout options:

• monthly payout  
• minimum threshold payout  

Example:

Minimum payout: $100

Payment methods:

• crypto  
• bank transfer  
• PayPal  


------------------------------------------------------------
13. ADMIN CONTROL
------------------------------------------------------------

Admins can manage affiliate system.

Capabilities:

• approve affiliates  
• suspend affiliates  
• modify commission rates  
• review affiliate performance  


------------------------------------------------------------
14. FUTURE EXTENSIONS
------------------------------------------------------------

Possible future upgrades:

• multi-level affiliate systems  
• performance-based bonuses  
• affiliate leaderboards  
• automated payout integrations  


------------------------------------------------------------
15. RELATION TO SYSTEM ARCHITECTURE
------------------------------------------------------------

Affiliate system belongs to:

ADMIN layer  
DISTRIBUTION layer  

Affiliate analytics may interact with:

INTELLIGENCE layer


------------------------------------------------------------
16. FINAL STATEMENT
------------------------------------------------------------

The affiliate distribution model allows BinaryBot to scale
signal distribution through external trading communities
while preserving strict separation between:

• marketing layer  
• operational control layer  
• strategy intelligence layer  

This separation protects both system security
and the integrity of the trading strategy.