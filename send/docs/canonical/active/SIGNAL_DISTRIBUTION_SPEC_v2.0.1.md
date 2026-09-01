# SIGNAL_DISTRIBUTION_SPEC_v2.0.1.md

BinaryBot — Signal Distribution, Entitlement Routing & Delivery Governance Specification  
Version: 2.0.1  
Status: ACTIVE CANONICAL  
Path: `send/docs/canonical/active/SIGNAL_DISTRIBUTION_SPEC_v2.0.1.md`  
Supersedes: `SIGNAL_DISTRIBUTION_SPEC_v2.0.0.md`  

---

**SCOPE AND AUTHORITY DECLARATION (OWNER-003 — canonical-reconciliation-01, reference-aligned 2026-09-01)**

This document and `SIGNAL_DISTRIBUTION_ARCHITECTURE_v2.0.1.md` address complementary, non-overlapping domains within signal distribution. Their scopes are explicitly declared below.

**This document (`SIGNAL_DISTRIBUTION_SPEC_v2.0.1.md`) governs exclusively:**

- Signal entitlement: which signal stages (PRE / CONFIRM / OPEN_NOW) may be delivered to which tiers
- Delivery rules: what constitutes a valid delivery, what silences a route, what counts as entitlement consumption
- Tier eligibility: which destinations are authorized for which signal lifecycle states
- Route silencing and entitlement exhaustion behavior
- Successful-delivery counting and daily reset behavior
- Outcome-interface eligibility at the destination level
- Commercial and operational distribution policy: the separation of signal truth from audience routing

**This document does not govern** routing topology, channel architecture, module ownership boundaries, or distribution layer structure. Those belong to `SIGNAL_DISTRIBUTION_ARCHITECTURE_v2.0.1.md`.

Where any ambiguity arises about which document governs a specific distribution concern, apply the following rule: entitlement, commercial routing, and operational delivery policy belong to this document; architectural and structural concerns (topology, boundaries, module ownership) belong to `SIGNAL_DISTRIBUTION_ARCHITECTURE_v2.0.1.md`.

---

Linked Documents:
- TELEGRAM_UX_v2.0.1.md
- CHANNEL_CONFIG_SPEC_v2.0.1.md
- OUTCOME_TRACKING_SPEC_v3.0.0.md
- PERFORMANCE_ANALYTICS_SPEC_v3.0.0.md
- ADMIN_CONTROL_SPEC_v2.0.1.md
- ADMIN_OPERATIONS_SPEC_v2.0.1.md
- ROLE_AND_PERMISSION_MATRIX_SPEC_v2.0.1.md
- ADMIN_TREE_MAP_v2.0.1.md
- CONTROL_PANEL_HIERARCHY_AND_INTELLIGENCE_SPEC_v2.0.1.md
- DECISION_AUDIT_SPEC_v3.0.0.md
- TRADE_TEMPORAL_TELEMETRY_SPEC_v3.0.0.md
- OBSERVABILITY_LOGGING_SPEC_v3.0.0.md
- GOVERNANCE_AND_CHANGE_CONTROL_v2.0.1.md

---

## 0. SCOPE AND NON-GOALS

### Scope
This document defines the canonical policy and mechanics for distributing governed signal lifecycle stages into Telegram destinations, according to entitlement, routing, delivery safety and operational governance rules.

It governs:
- distribution of PRE / CONFIRM / OPEN_NOW stages
- destination and tier eligibility
- route silencing / entitlement exhaustion behavior
- successful-delivery counting rules
- daily reset behavior
- routing observability
- delivery deduplication
- outcome-interface eligibility at destination level
- interaction between signal lifecycle and commercial distribution policy

### Non-goals
This document does not define:
- strategy scoring
- signal generation logic
- decision-object creation logic
- FSM internals
- market detection logic
- raw Telegram message layout
- low-level channel ID storage details

Those belong elsewhere.

---

## 1. PURPOSE

This document defines how governed signals are distributed across Telegram destinations and entitlement tiers.

The trading and decision layers generate governed lifecycle events independently of the distribution layer.

The distribution layer does not decide whether a signal is valid.
It decides:
- where the signal may be published
- when a route must be silent
- what counts as consumption of delivery entitlement
- which destinations receive outcome interaction capability
- how routing behavior is logged and governed

This layer exists to separate:
- signal truth
from
- commercial / audience routing policy

---

## 2. DISTRIBUTION AS A GOVERNED LAYER

Distribution is not a cosmetic Telegram concern.
It is a governed product and entitlement layer.

Therefore distribution must respect:
- canonical signal identity
- route entitlement state
- destination class policy
- role/admin governance
- auditability
- restart-safe persistence

No UI convenience or one-off manual behavior may violate the canonical routing rules defined here.

---

## 3. CORE CANONICAL ENTITIES

### 3.1 Signal lifecycle stage
Canonical visible stages:
- PRE
- CONFIRM
- OPEN_NOW

### 3.2 Signal identity
All visible stages for the same trade idea must share the same governed signal identity.

### 3.3 Destination
A destination is a Telegram routing target configured by policy.
A destination may be:
- a public tier channel
- a premium/private tier channel
- a topic or sub-route where policy allows
- another governed delivery route introduced later

### 3.4 Entitlement route
An entitlement route is a governed delivery path with its own:
- eligibility
- state
- counters
- silence policy
- outcome capability policy

### 3.5 Delivery success
A successful delivery means the transport layer reported publish success for that destination.

### 3.6 Route state
Canonical distribution route states:
- ACTIVE
- SILENT
- DISABLED

### 3.7 Daily entitlement consumption
Entitlement consumption is the governed counting of successful OPEN_NOW deliveries for eligible limited routes.

---

## 4. SIGNAL LIFECYCLE CONTINUITY

Every governed trade idea may produce up to three visible trading stages:

```text
PRE → CONFIRM → OPEN_NOW
```

All visible stages belonging to the same trade idea must share the same governed signal identity.

Distribution does not determine:
- whether PRE exists
- whether CONFIRM exists
- whether OPEN_NOW exists

Distribution determines only whether a governed stage is routed to a particular destination.

---

## 5. SIGNAL IDENTITY RULES (MUST)

Each lifecycle must have one stable governed signal identity.

Strict rules:
- PRE, CONFIRM and OPEN_NOW for the same trade idea must share the same signal identity
- distribution must not invent a new identity
- retry logic must preserve the same identity
- deduplication must treat stage plus destination plus signal identity as the canonical minimum uniqueness boundary

Recommended canonical dedup basis:
- destination
- signal_identity
- stage

Additional time bucket or transport metadata may exist internally, but must not weaken these core invariants.

Rationale:
This guarantees traceability, retry safety, audit continuity and correct outcome attachment behavior.

---

## 6. CANONICAL DISTRIBUTION MODEL

The system distributes signals to governed destinations that represent commercial or operational tiers.

The legacy four-tier intuition remains valid and is the current baseline:

- FREE
- BASIC
- PRO
- ELITE

However, v2.0.1 treats these as governed entitlement routes, not merely hardcoded channel names.

Each route must have:
- a configured destination mapping
- a route state
- a defined entitlement policy
- a delivery logging path
- a clear outcome capability rule

Channel identifiers and low-level Telegram config remain implementation/config details and are not the canonical truth by themselves.

---

## 7. ROUTE ELIGIBILITY AND BEHAVIOR

### 7.1 ACTIVE
An ACTIVE route may receive governed visible lifecycle stages according to policy.

### 7.2 SILENT
A SILENT route receives no visible lifecycle stages:
- no PRE
- no CONFIRM
- no OPEN_NOW

Silent means fully silent for signal lifecycle visibility unless a future explicit exception is canonically defined.

### 7.3 DISABLED
A DISABLED route is not publishable because configuration or policy prevents delivery.
A disabled route:
- receives nothing
- consumes nothing
- must generate observability/admin visibility when relevant

### 7.4 ELITE-style unlimited route
An unlimited route may remain effectively always ACTIVE with respect to entitlement exhaustion, unless explicitly disabled by configuration or policy.

---

## 8. CORE ENTITLEMENT RULE

Signals may be published to multiple routes simultaneously.

Core gating principle:
- if route is ACTIVE and eligible, it may receive the stage
- if route is SILENT, it receives nothing
- if route is DISABLED, it receives nothing
- entitlement exhaustion affects the whole visible signal lifecycle for that route once silence applies

This preserves the old business rule:
once a limited route is exhausted, that route goes fully silent rather than receiving PRE/CONFIRM without OPEN_NOW.

---

## 9. DAILY OPEN_NOW LIMITS

Daily delivery limits apply only to successful OPEN_NOW publications on limited entitlement routes.

Current baseline limits inherited from the legacy canonical version are:

- FREE: 6 successful OPEN_NOW deliveries per day
- BASIC: 20 successful OPEN_NOW deliveries per day
- PRO: 50 successful OPEN_NOW deliveries per day
- ELITE: unlimited

Important:
- PRE does not consume entitlement
- CONFIRM does not consume entitlement
- OPEN_NOW only consumes entitlement if publish success occurs on that route
- unlimited routes do not become SILENT because of ordinary entitlement exhaustion

These numeric limits may later be governed by a configuration/control layer, but the counting semantics defined here remain canonical.

---

## 10. SILENT MODE RULE (HARD BEHAVIOR)

When a limited route reaches its daily successful OPEN_NOW entitlement limit, it becomes SILENT.

Once SILENT:
- no PRE
- no CONFIRM
- no OPEN_NOW

The route remains SILENT until the next governed reset.

Example:
if FREE reaches its daily successful OPEN_NOW entitlement maximum, FREE becomes fully silent for remaining signal lifecycle delivery that day, while other eligible routes may continue normally.

This rule is central and must not be weakened by ad hoc “partial visibility” shortcuts.

---

## 11. DELIVERY COUNTING RULES

### 11.1 Count only successful OPEN_NOW delivery
Counters increase only when OPEN_NOW publish to that route succeeds.

### 11.2 Do not count failed delivery
If transport publish fails, counters must not increase.

### 11.3 Do not count PRE / CONFIRM
PRE and CONFIRM never consume entitlement.

### 11.4 No synthetic count inflation
Retries, duplicate sends or replay logic must not inflate counters.

### 11.5 Route-local accounting
Entitlement is consumed per route, not globally per signal.

A signal may consume entitlement on one route and not another depending on actual delivery outcome.

---

## 12. PERSISTENCE AND RESTART SAFETY

Each governed route must persist enough state to survive restart without entitlement corruption.

Minimum persisted state per route:
- successful_open_now_today
- route_state
- last_reset_reference

Global or service-level persisted state may also include:
- last_reset_execution marker
- dedup materialization state
- transport retry continuity data where relevant

Hard requirements:
- restart must not reset route counters
- restart must not silently reactivate a SILENT route before reset
- restart must not duplicate prior successful entitlement consumption
- persisted state must support idempotent reset logic

---

## 13. DAILY RESET RULE

The legacy canonical version defined a daily reset at:
- 08:10 Europe/London

This remains the current baseline reset reference unless superseded canonically elsewhere.

Meaning:
- reset occurs according to Europe/London timezone
- DST handling must be correct
- reset logic must be idempotent
- on reset, limited route counters return to zero and SILENT limited routes become ACTIVE again
- DISABLED routes remain governed by configuration/policy and are not force-activated merely by reset

This baseline should align operationally with the intended London-session trading day boundary.

---

## 14. DESTINATION CONFIG CONTRACT

Each governed route must map to a valid Telegram destination through the channel/config layer.

At minimum, the legacy mapping family remains recognized:

- FREE_CHANNEL_ID
- BASIC_CHANNEL_ID
- PRO_CHANNEL_ID
- ELITE_CHANNEL_ID

If a required mapping is absent or invalid:
- that route is effectively DISABLED
- no publish attempt should be treated as successful
- counters must not increment
- an operational/admin visibility event must exist

The mapping mechanism belongs to configuration, but the behavior of missing mappings is canonical here.

---

## 15. ORDER OF OPERATIONS

For each governed SignalEvent candidate released to distribution:

### 15.1 Normalize the stage payload
Must ensure:
- stage is valid
- governed signal identity exists
- destination-relevant metadata is available as required

Missing signal identity is a hard failure for publish eligibility.

This wording deliberately distinguishes an internal candidate released by Signal Engine from the post-publication Signal Engine outcome `EMITTED`. Candidate release does not itself mean successful publication.

### 15.2 Resolve governed route set
Determine the currently eligible destination routes.

### 15.3 Evaluate each route independently
For each route:
- if DISABLED → do not publish
- if SILENT → do not publish
- if ACTIVE → continue evaluation

### 15.4 Apply OPEN_NOW entitlement logic
If stage is OPEN_NOW on a limited route:
- if the route is already at or above daily entitlement, set/keep SILENT and do not publish
- otherwise continue to publish attempt

### 15.5 Attempt publish
Attempt transport publish to the resolved destination.

### 15.6 Commit route result
If publish succeeds:
- record successful stage delivery
- if stage is OPEN_NOW on a limited route, increment route entitlement consumption
- if the route now reaches its limit, transition it to SILENT for subsequent signals

If publish fails:
- do not increment entitlement
- do not fake success
- record failure observability

This sequence must be safe against retry duplication and restart ambiguity.

---

## 16. OBSERVABILITY AND ADMIN LOGGING

Every governed distribution decision must be observable.

Minimum event fields should include:
- timestamp in UTC
- local reference time where relevant
- stage
- governed signal identity
- symbol and timeframe where available
- route / tier
- decision result
- route state before and after where relevant
- counter before and after for OPEN_NOW on limited routes
- transport error if failure occurred
- reason code for skip / disable / silent / limit / duplicate where available

Canonical decision families may include:
- PUBLISHED
- SKIPPED_SILENT
- SKIPPED_DISABLED
- SKIPPED_LIMIT
- FAILED
- DUPLICATE_SUPPRESSED

This observability is mandatory for:
- monetization trust
- incident debugging
- entitlement verification
- audit review
- supportability

This domain should align with:
- `OBSERVABILITY_LOGGING_SPEC_v3.0.0.md`
- `ADMIN_OPERATIONS_SPEC_v2.0.1.md`
- `DECISION_AUDIT_SPEC_v3.0.0.md`

Exact route publication truth remains represented by the canonical Event Schema / Observability contracts. Distribution does not fabricate Signal Engine execution truth.

---

## 17. FAILURE PROTECTION AND GUARANTEES

The distribution system must prevent:
- duplicate broadcasts for the same route/stage/signal identity
- entitlement counter corruption on retry
- silent route leakage
- route reactivation without reset
- false success reporting
- broken outcome attachment linkage

Core guarantees:
- deduplication key must include at least route + signal identity + stage
- counters increment only on successful OPEN_NOW publish
- state changes must be persisted safely enough to survive restart
- signal lifecycle truth must remain independent from destination entitlement policy

---

## 18. OUTCOME-CAPABLE DISTRIBUTION ROUTES

The legacy model attached outcome collection only to ELITE OPEN_NOW messages.
That baseline remains valid in v2.0.1 unless broader entitlement policy is canonically introduced.

Outcome-capable route principles:
- outcome interaction applies only to eligible routes
- outcome interaction applies only to OPEN_NOW lifecycle stage
- PRE and CONFIRM are never outcome-rated
- outcome capability is a route policy, not an arbitrary message decoration
- outcome attachment must preserve the same governed signal identity linkage

This domain must align with:
- `TELEGRAM_UX_v2.0.1.md`
- `OUTCOME_TRACKING_SPEC_v3.0.0.md`

---

## 19. ELITE FEEDBACK / OUTCOME BASELINE

Current canonical baseline:
- ELITE is the outcome-capable entitlement route
- ELITE OPEN_NOW signals may carry outcome interaction capability
- eligible self-reported/operational outcome values remain:
  - WIN
  - LOSE
  - MISSED

Each accepted outcome/feedback record must be linkable to:
- signal identity
- Telegram/user identity under applicable privacy rules
- timestamp
- outcome value
- truth source under the promoted Outcome/Community Feedback contracts.

Purpose:
to collect governed execution feedback for later analytics and performance interpretation without collapsing objective market telemetry, operational reconciliation and self-reported community truth.

This feedback layer does not alter:
- strategy scoring
- signal generation
- FSM transitions
- distribution entitlement counters

---

## 20. ELITE MEMBERSHIP / ACCESS CHECK BASELINE

The legacy canonical version required Telegram membership verification before accepting feedback or returning personal outcome statistics.
That remains a valid baseline behavior.

Membership verification principles:
- only entitled ELITE members may submit ELITE member feedback where that workflow is enabled
- only entitled ELITE members may access their private personal stats in the relevant product path
- access should follow current membership state rather than manual one-off whitelists whenever possible

Telegram API membership verification remains the baseline mechanism, subject to implementation details and transport limits.

Allowed/denied status mapping may be refined operationally, but the canonical rule is:
access follows governed membership state.

---

## 21. PRIVATE USER STATISTICS BASELINE

Entitled ELITE users may receive private personal statistics through private bot interaction paths.

Privacy rules:
- a user may access only their own statistics
- no public exposure of per-user personal performance
- aggregate analytics may be visible to properly authorized admin roles
- user identities must not be publicly exposed in channels

Minimum baseline metrics inherited from the old version remain conceptually valid:
- total_signals_rated
- wins
- losses
- missed

Derived metrics may include:
- win_rate
- accuracy
- miss_rate

The precise truth classification and analytics model belongs primarily to:
- `OUTCOME_TRACKING_SPEC_v3.0.0.md`
- `COMMUNITY_FEEDBACK_AND_PRIVACY_SPEC_v3.0.0.md`
- `PERFORMANCE_ANALYTICS_SPEC_v3.0.0.md`

---

## 22. ADMIN AND CONTROL IMPLICATIONS

Distribution is an admin-visible governed subsystem.

Admin/control surfaces may inspect or manage:
- route state
- route counters
- route config validity
- destination mapping health
- delivery failures
- entitlement exhaustion state
- outcome-capable route status

Any mutating admin action affecting distribution must respect the admin governance stack and must not bypass:
- role rules
- guarded actions
- audit requirements
- observability requirements

This aligns with:
- `ADMIN_CONTROL_SPEC_v2.0.1.md`
- `ROLE_AND_PERMISSION_MATRIX_SPEC_v2.0.1.md`
- `CONTROL_PANEL_HIERARCHY_AND_INTELLIGENCE_SPEC_v2.0.1.md`

---

## 23. GUARANTEES

If implemented according to this specification, the distribution layer guarantees:

- predictable entitlement consumption
- route-local counting correctness
- full silence after limited-route exhaustion
- clean separation between signal truth and commercial routing policy
- restart-safe route state persistence
- DST-safe reset behavior aligned to Europe/London baseline
- outcome capability restricted to governed eligible routes
- operational visibility for every delivery decision

---

## 24. MIGRATION NOTES FROM LEGACY VERSION

The legacy signal distribution specification established the right commercial intuition:
- PRE / CONFIRM / OPEN_NOW lifecycle continuity
- route-level entitlement limits
- full silence after limit exhaustion
- successful OPEN_NOW-only counting
- London-time reset baseline
- ELITE outcome feedback baseline

The v2.0.0 canonical version preserved those rules while introducing governed entitlement routes and stronger admin/observability framing.

### v2.0.1 reference/terminology repair

This PATCH successor makes no route-policy or entitlement change.

It:
- updates normative references to the staged-execution / Trade Physics successor graph;
- updates cross-references to the final PATCH filenames in the distribution/admin/UX cluster;
- replaces the ambiguous order-of-operations phrase `For each emitted governed signal stage` with `For each governed SignalEvent candidate released to distribution`;
- clarifies that internal candidate release is not the post-publication execution outcome `EMITTED`;
- aligns feedback wording with the promoted multi-truth Outcome/Community Feedback model.

Unchanged behavior includes:
- FREE = 6 successful OPEN_NOW/day;
- BASIC = 20;
- PRO = 50;
- ELITE = unlimited;
- PRE/CONFIRM never consume entitlement;
- SILENT blocks all stages;
- reset baseline remains 08:10 Europe/London;
- counters increment only after successful OPEN_NOW publication;
- distribution remains downstream and does not decide strategy validity.

---

## 25. VERSION HISTORY

| Version | Date | Description |
|---|---|---|
| 2.0.1 | 2026-09-01 | Proposed PATCH successor: canonical reference repair and SignalEvent-candidate vs EMITTED terminology clarification; no entitlement/routing behavior change. |
| 2.0.0 | 2026-07-12 | Active canonical governed distribution policy. |

---

End of SIGNAL_DISTRIBUTION_SPEC_v2.0.1.md