# TELEGRAM_UX_v2.0.0.md

BinaryBot — Telegram Experience, Routing & Interaction Specification  
Version: 2.0.0  
Status: CANONICAL  
Path: /opt/binarybot/docs/canonical/active/TELEGRAM_UX_v2.0.0.md

Linked Documents:
- ADMIN_CONTROL_SPEC_v2.0.0.md
- ADMIN_OPERATIONS_SPEC_v2.0.0.md
- ADMIN_TREE_MAP_v2.0.0.md
- CONTROL_PANEL_HIERARCHY_AND_INTELLIGENCE_SPEC_v2.0.0.md
- ROLE_AND_PERMISSION_MATRIX_SPEC_v2.0.0.md
- DECISION_AUDIT_SPEC_v2.0.0.md
- TRADE_TEMPORAL_TELEMETRY_SPEC_v2.0.0.md
- OUTCOME_TRACKING_SPEC_v2.0.0.md
- PERFORMANCE_ANALYTICS_SPEC_v2.0.0.md
- SIGNAL_DISTRIBUTION_SPEC_v2.0.0.md
- CHANNEL_CONFIG_SPEC_v2.0.0.md
- OBSERVABILITY_LOGGING_SPEC_v2.0.0.md
- GOVERNANCE_AND_CHANGE_CONTROL.md

---

## 1. PURPOSE

This document defines the canonical Telegram interaction model of BinaryBot.

Telegram is the primary operational interface for:
- signal delivery
- outcome capture
- admin interaction
- alert routing
- documentation access
- high-signal operational summaries

This document governs:
- Telegram message families
- topic and routing semantics
- operator/admin interaction flows
- outcome-panel behavior
- anti-spam and dedup rules
- formatting and message lifecycle expectations
- role-scoped admin UX behavior

This specification replaces the older flatter Telegram UX framing with a model aligned to:
- governed admin hierarchy
- role-scoped control surfaces
- newer decision-audit visibility
- production-safe operational flows
- clearer separation between live signal UX, admin UX and audit/alert UX

---

## 2. TELEGRAM AS INTERFACE, NOT ARCHITECTURE

Telegram is an interface layer, not the core architecture.

Therefore:
- Telegram commands must map to canonical governed actions
- Telegram messages must reflect canonical signal truth
- Telegram UI structure must respect role, scope and audit rules
- Telegram affordances must not bypass control policy
- interface convenience must not override system invariants

If Telegram presentation ever changes, the canonical behavioral meaning defined here remains authoritative.

---

## 3. CANONICAL TELEGRAM UX DOMAINS

Telegram UX is divided into the following domains:

### 3.1 Live Signal UX
Signal delivery to trading-facing channels or topics.

### 3.2 Outcome UX
Outcome reporting interfaces attached to eligible signals.

### 3.3 System Alert UX
Operational alerts, failures and critical state messages.

### 3.4 Admin UX
Private role-scoped operator control and visibility flows.

### 3.5 Research / Summary UX
Report, summary and insight delivery where policy allows.

### 3.6 Documentation UX
Governed delivery of documents and references inside Telegram.

---

## 4. CANONICAL TELEGRAM ROUTING MODEL

Telegram routing must separate message purposes cleanly.

At conceptual level, BinaryBot uses distinct routing classes:

```text
TELEGRAM ROUTING
├── Live Signal Destinations
├── Outcome Interaction Destinations
├── System Alert Destinations
├── Admin / Control Destinations
├── Research / Summary Destinations
└── Documentation Delivery Destinations
```

Important:
- these may map to channels, groups, supergroups or topics
- exact IDs are implementation/configuration details
- semantic separation is canonical and mandatory

---

## 5. LIVE SIGNAL UX

### 5.1 Purpose
Live Signal UX delivers trading-stage messages to the intended signal audiences.

### 5.2 Canonical live signal stages
The canonical signal-stage family is:

- PRE
- CONFIRM
- OPEN_NOW

These are message stages of one governed signal lifecycle.

### 5.3 Lifecycle continuity
When multiple stages exist for the same signal, they must be semantically linked by the governed signal identity.

Linked lifecycle expectation:

```text
PRE → CONFIRM → OPEN_NOW → OUTCOME_PANEL
```

Not every signal must pass through every visible stage, depending on strategy and routing policy, but any visible stage must remain truthful to actual governed state.

### 5.4 Live channel cleanliness
Live signal destinations must remain readable.

Therefore:
- no raw debug dump in live channels
- no irrelevant admin text in live channels
- no uncontrolled spam bursts
- no contradictory duplicate stage messages

---

## 6. SIGNAL MESSAGE FAMILIES

### 6.1 PRE
Purpose:
Early awareness or watch-stage visibility.

PRE messages must communicate that a setup is being monitored and is not yet the final execution state.

### 6.2 CONFIRM
Purpose:
Strengthened readiness stage.

CONFIRM messages must communicate that the setup has materially improved versus PRE, without falsely claiming final execution readiness unless that state is actually reached.

### 6.3 OPEN_NOW
Purpose:
Execution-stage signal.

OPEN_NOW messages must communicate that the strategy has reached the governed execution state required for the relevant destination and policy path.

### 6.4 SYSTEM
Purpose:
Non-signal operational message family.

SYSTEM messages are not trading-stage messages and must never be mixed ambiguously into live trading signal flows.

---

## 7. MESSAGE CONTENT PRINCIPLES

Telegram messages must optimize for clarity, not raw internal verbosity.

### 7.1 Clarity first
A recipient must understand the stage and meaning of the message quickly.

### 7.2 No false certainty
Confidence-style fields must not imply guarantees.

### 7.3 Stable field order
Equivalent message types should preserve a stable reading order.

### 7.4 Human readability
Formatting must remain scannable on mobile Telegram clients.

### 7.5 Canonical truth only
Message content must reflect actual governed signal state, not guessed or cosmetically inflated state.

---

## 8. LIVE SIGNAL FORMAT EXPECTATIONS

Exact phrasing may evolve, but message structure should remain consistent.

### 8.1 PRE expected fields
Typical fields may include:
- stage label
- symbol
- direction
- timing or expiry indication
- confidence or readiness summary if allowed
- status wording indicating monitoring / watch-stage semantics

### 8.2 CONFIRM expected fields
Typical fields may include:
- stage label
- symbol
- direction
- buffer or timing context where relevant
- expiry indication
- readiness strengthening wording

### 8.3 OPEN_NOW expected fields
Typical fields may include:
- stage label
- symbol
- direction
- execution-relevant timing / expiry
- confidence or readiness wording if policy allows
- action wording suitable for the destination and audience

### 8.4 Field minimization
Do not overload live messages with technical diagnostics that belong in debug/audit/research surfaces.

---

## 9. DEDUPLICATION AND ANTI-SPAM RULES

The Telegram layer must enforce anti-spam safety.

### 9.1 Canonical dedup rule
Equivalent message emissions must be deduplicated according to governed identity, stage and timing context.

The legacy dedup intuition remains valid:
- symbol
- candle or signal time bucket
- message stage

But implementation may use stronger internal IDs when available.

### 9.2 No duplicate PRE bursts
The system must not repeatedly emit equivalent PRE messages for the same governed event.

### 9.3 No duplicate CONFIRM bursts
The system must not repeatedly emit equivalent CONFIRM messages for the same governed event.

### 9.4 No duplicate OPEN_NOW bursts
The system must not repeatedly emit equivalent OPEN_NOW messages for the same governed execution state.

### 9.5 No stage inversion confusion
The user must not receive a weaker-stage message after a stronger-stage message in a contradictory way for the same active lifecycle, unless clearly explained by controlled correction logic.

### 9.6 Volatility safety
Volatility spikes or noisy strategy conditions must not create uncontrolled Telegram message storms.

---

## 10. MESSAGE PRIORITY

If multiple message-worthy events compete at the same time, Telegram routing should preserve priority logic.

General priority order:

1. critical system / safety alerts
2. OPEN_NOW
3. CONFIRM
4. PRE
5. lower-priority summaries

A weaker-stage signal should not displace a stronger or safety-critical message in a way that degrades user clarity.

---

## 11. SYSTEM ALERT UX

System alerts belong in operational/system destinations, not in ordinary live trading destinations unless policy explicitly requires it.

### 11.1 Typical system alert classes
Examples:
- engine started
- engine stopped
- guarded restart detected
- API degradation
- runtime exception
- state corruption warning
- invariant breach
- freeze entered
- recovery completed

### 11.2 System alert content principles
System alerts should:
- identify the event clearly
- provide enough context to act
- avoid leaking unnecessary sensitive internals
- route to the correct operational audience
- remain separable from trading-stage signals

### 11.3 No trading ambiguity
System alerts must not visually imitate PRE / CONFIRM / OPEN_NOW messages.

---

## 12. DEBUG / TECHNICAL TRANSPARENCY UX

Technical transparency belongs in dedicated debug or diagnostic destinations, not live user channels.

Typical debug payload classes may include:
- score composition
- gate results
- buffer calculations
- expiry calculations
- state transition evidence
- rejection reasons
- diagnostic trace summaries

This domain must align with:
- `DECISION_AUDIT_SPEC_v2.0.0.md`
- `TRADE_TEMPORAL_TELEMETRY_SPEC_v2.0.0.md`
- `OBSERVABILITY_LOGGING_SPEC_v2.0.0.md`

---

## 13. OUTCOME UX

Outcome UX is the governed trade-result interaction surface for eligible destinations and tiers.

### 13.1 Purpose
Outcome reporting exists to collect real-world trade result feedback and support:
- outcome aggregation
- performance analysis
- strategy validation
- research and learning workflows

### 13.2 Lifecycle continuity
Outcome UX is part of the signal lifecycle for eligible paths:

```text
PRE → CONFIRM → OPEN_NOW → OUTCOME_PANEL
```

### 13.3 Attachment model
Preferred model:
- the outcome interface is attached to the OPEN_NOW message

Fallback model:
- a second Telegram message may be emitted immediately after OPEN_NOW when Telegram/UI constraints require it

If fallback is used:
- the second message must remain clearly linked to the same signal identity
- it should be sent effectively immediately
- it should reply to or otherwise clearly attach to the OPEN_NOW message where supported

### 13.4 Tier and route sensitivity
Outcome UX may exist only for configured destinations or tiers.

Public or lower-tier destinations do not automatically receive outcome interaction surfaces.

---

## 14. OUTCOME REPORTING RULES

### 14.1 Delayed activation
Outcome interaction must not open before the relevant trade or expiry window has logically closed.

### 14.2 Reporting window
Outcome reporting must remain bounded in time.

The old model of a short post-expiry reporting window remains directionally correct, but exact durations may be governed by the outcome-tracking system.

### 14.3 Single-vote rule
Each eligible Telegram user may submit only one governed outcome per signal identity.

### 14.4 Lock-first policy
Once a valid outcome is accepted, the stored result for that user/signal pair should not be silently overwritten by repeated presses unless a future governed override policy explicitly exists.

### 14.5 Canonical outcome options
The legacy family remains valid:
- WIN
- LOSE
- MISSED

Additional controlled states may exist only if formally governed elsewhere.

### 14.6 Aggregated statistics only
Public-facing Telegram outcome updates should display aggregate statistics only.

User identities and raw per-user voting data must not be exposed publicly.

### 14.7 Integrity model
Outcome data must be protected against:
- early voting
- late voting
- duplicate voting
- silent overwrites
- broken signal linkage

This domain must align with:
- `OUTCOME_TRACKING_SPEC_v2.0.0.md`
- `PERFORMANCE_ANALYTICS_SPEC_v2.0.0.md`

---

## 15. ADMIN UX

Admin UX is a private governed Telegram experience, not a public convenience menu.

### 15.1 Purpose
Admin UX exists to:
- inspect operational state
- execute allowed future-facing control actions
- inspect decision/rejection truth
- access research and intelligence summaries
- inspect audit and system health views
- access governed documentation

### 15.2 Role-scoped rendering
Admin surfaces must render according to role and scope.

A user must not see all admin buttons merely because they can open `/admin`.

### 15.3 Architecture alignment
Telegram admin UX must map to the canonical admin tree, not replace it.

This means the Telegram interface may expose:
- compact command groups
- inline keyboard menus
- paged navigation
- contextual detail screens

But the underlying meaning must remain aligned with:
- `ADMIN_TREE_MAP_v2.0.0.md`
- `CONTROL_PANEL_HIERARCHY_AND_INTELLIGENCE_SPEC_v2.0.0.md`
- `ADMIN_OPERATIONS_SPEC_v2.0.0.md`

---

## 16. ADMIN ENTRY AND NAVIGATION

### 16.1 Governed admin entry
Canonical entry remains:

`/admin`

### 16.2 Expected behavior
`/admin` should:
- identify the current role/scope context where appropriate
- show allowed top-level branches
- provide quick status summary
- avoid exposing unauthorized branches
- make visibility versus mutation differences clear

### 16.3 No flat unrestricted command dump
The legacy “show everything in one menu” pattern is not canonical.

---

## 17. ADMIN COMMAND FAMILIES

Exact commands may vary by implementation, but the UX families should map to the canonical tree.

Illustrative families:
- `/admin`
- `/status`
- `/ops`
- `/symbols`
- `/distribution`
- `/decision`
- `/research`
- `/intelligence`
- `/audit`
- `/docs`
- `/help`

Important:
- command availability must be role-scoped
- results must respect visibility policy
- commands must not bypass guarded-action requirements
- commands are interface affordances, not authority grants

---

## 18. ADMIN BUTTON AND MENU PRINCIPLES

### 18.1 Buttons must reflect allowed actions only
Unauthorized actions should normally be absent, not merely teased.

### 18.2 Destructive or guarded actions need stronger signaling
Sensitive actions should not look identical to harmless inspect actions.

### 18.3 Visibility actions must be clearly separated
A read-only status button should not be mixed confusingly with mutating controls.

### 18.4 Multi-step control flows are allowed
For sensitive actions, confirmation or staged flow is acceptable and often preferable.

### 18.5 Response determinism
An admin interaction should return a clear result message whenever possible.

---

## 19. DOCUMENTATION UX

Telegram may deliver Markdown or file-based documentation to authorized roles.

### 19.1 Purpose
Documentation UX allows governed in-bot access to:
- canonical specs
- migration notes
- implementation references
- selected playbooks

### 19.2 Role sensitivity
Not every role should see the same document set.

### 19.3 Document truth
Telegram-delivered docs must correspond to current active canonical truth, not stale deprecated files.

This is important for the later reference-hygiene pass across the document set.

---

## 20. RESEARCH / SUMMARY UX

Telegram may also act as a delivery channel for:
- daily summaries
- weekly summaries
- performance snapshots
- rejection analytics summaries
- drift alerts
- recommendation summaries
- affiliate summaries where appropriate

Research delivery must remain audience-scoped and must not leak sensitive data into the wrong destinations.

---

## 21. ACCESS RULES

### 21.1 No public admin control
Admin control interactions must not execute from public signal destinations.

### 21.2 No role leakage
A lower-scope actor must not infer hidden higher-scope controls through Telegram affordances.

### 21.3 No hidden mutation through read views
A read-style interaction must not perform mutating admin actions.

### 21.4 No ambiguous result state
A user should not be left unsure whether a mutating command succeeded, failed or was ignored.

---

## 22. UX GUARANTEES

If Telegram UX is implemented according to this specification, the system should provide:

- clear message meaning
- clean stage progression
- bounded outcome interaction
- role-scoped admin control visibility
- reduced duplicate signal spam
- cleaner separation between signal, alert, admin and research experiences
- canonical alignment with the broader BinaryBot architecture

---

## 23. MIGRATION NOTES FROM LEGACY VERSION

The legacy Telegram UX specification provided a useful first baseline, but had several limitations:

- flatter topic model
- overly command-centric framing
- weaker distinction between live UX, admin UX and governed control architecture
- limited integration with the new decision-audit and intelligence layers
- incomplete role-scoped admin rendering model
- references to older admin documents that are now being upgraded

This v2.0.0 specification replaces that with a Telegram model centered on:
- governed routing classes
- cleaner UX domain separation
- signal lifecycle continuity
- bounded outcome interaction
- role-scoped admin rendering
- compatibility with the newer admin/control canonical stack

---

End of TELEGRAM_UX_v2.0.0.md

## 29. DM-Only Member Statistics and Public Channel Privacy

This section integrates bounded UX/privacy rules from the merged Community Feedback and Privacy intake.

### 29.1 DM-only access
Member statistics are accessible only through DM/private chat with the bot. Public stats requests in channels/groups must be blocked or redirected to private chat.

### 29.2 Public channel identity protection
Channel messages must never display user identifiers or expose private member statistics. Public-facing prompts may instruct the user: "Open private chat with bot to view your stats."

### 29.3 Admin command boundary
Admin/operator commands for reviewing member statistics may exist, but operator access must remain role-bounded and must not leak private identity fields into public channel UX.

## 31. Private/Admin UX Routing Clarifications from Admin UX Review

This section absorbs bounded Telegram/admin UX clarifications extracted from ADMIN_UX_V2_SPEC.md.

### 31.1 Surface distinction
Private member UX, public channel UX, and admin/operator UX must remain explicitly separated.

### 31.2 Admin route boundary
Admin-specific Telegram actions are control-plane surfaces only and must not be confused with member-facing UX flows.

### 31.3 Canonical precedence
Where older admin UX material described interaction ideas, active Telegram UX canon remains the source of truth.
