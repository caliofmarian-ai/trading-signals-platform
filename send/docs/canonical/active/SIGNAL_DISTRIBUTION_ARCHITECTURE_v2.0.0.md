# SIGNAL_DISTRIBUTION_ARCHITECTURE_v2.0.0

Version: 2.0.0  
Status: Active Canonical  
Path: `send/docs/canonical/active/SIGNAL_DISTRIBUTION_ARCHITECTURE_v2.0.0.md`

---

**SCOPE AND AUTHORITY DECLARATION (OWNER-003 — canonical-reconciliation-01)**

This document and `SIGNAL_DISTRIBUTION_SPEC_v2.0.0.md` address complementary, non-overlapping domains within signal distribution. Their scopes are explicitly declared below.

**This document (`SIGNAL_DISTRIBUTION_ARCHITECTURE_v2.0.0.md`) governs exclusively:**

- Routing topology and the architectural structure of the distribution layer
- Channel architecture: how delivery surfaces are organized, segmented, and mapped
- Distribution structure: how modules relate to each other within the distribution system
- Architectural boundaries: what belongs to the distribution layer vs. adjacent layers (strategy, presentation, admin, affiliate)
- Ownership rules for the distribution router and delivery pathways
- Failure, retry, and degraded-delivery architecture
- The canonical authorization model for distribution paths

**This document does not govern** entitlement rules, delivery tier eligibility, CONFIRM/OPEN_NOW routing policy, or daily reset behavior. Those belong to `SIGNAL_DISTRIBUTION_SPEC_v2.0.0.md`.

Where any ambiguity arises about which document governs a specific distribution concern, apply the following rule: architectural and structural concerns (topology, boundaries, module ownership) belong to this document; entitlement, commercial routing, and operational delivery policy belong to `SIGNAL_DISTRIBUTION_SPEC_v2.0.0.md`.

---

Linked Documents:
- SYSTEM_INVARIANTS_v2.0.0.md
- SYSTEM_ARCHITECTURE_MAP_v2.0.0.md
- MODULE_INTERFACE_SPEC_v2.0.0.md
- SIGNAL_DISTRIBUTION_SPEC_v2.0.0.md
- EVENT_SCHEMA_SPEC_v2.0.0.md
- TELEGRAM_UX_v2.0.0.md
- OBSERVABILITY_LOGGING_SPEC_v2.0.0.md
- DECISION_AUDIT_SPEC_v2.0.0.md
- OUTCOME_TRACKING_SPEC_v2.0.0.md
- PERFORMANCE_ANALYTICS_SPEC_v2.0.0.md
- GOVERNANCE_AND_CHANGE_CONTROL_v2.0.0.md
- STRATEGY_INTELLIGENCE_SYSTEM_v2.0.0.md
- AUTONOMOUS_STRATEGY_EVOLUTION_SYSTEM_v2.0.0.md

Depends on:
- SYSTEM_INVARIANTS_v2.0.0.md
- MODULE_INTERFACE_SPEC_v2.0.0.md
- SIGNAL_DISTRIBUTION_SPEC_v2.0.0.md
- EVENT_SCHEMA_SPEC_v2.0.0.md
- TELEGRAM_UX_v2.0.0.md
- OBSERVABILITY_LOGGING_SPEC_v2.0.0.md

Code Alignment:
- core/signal_engine.py
- core/distribution_router.py
- core/telegram_publisher.py
- core/fsm_runtime.py
- core/observability_logger.py
- core/outcome_service.py
- core/analytics_engine.py
- bot_service.py
- distribution configs
- channel/topic mapping configs
- admin routing surfaces

## 0. Purpose

This document defines the canonical signal distribution architecture for BinaryBot / DROPi Signals.

Its role is to define how signal-state outputs move from the internal strategic runtime into external delivery surfaces while preserving tier policy, routing discipline, restart safety, observability proof, and operational control.

This document does not define signal scoring, internal strategy decision logic, or the full UI wording of Telegram messages. It defines the architecture, ownership boundaries, delivery pathways, routing constraints, and safety rules of the distribution layer.

## 1. Canonical Position

This document sits between the signal production layer and the user-facing communication layer.

It exists to answer eight questions:

1. What outputs are eligible for distribution.
2. Which module owns distribution routing.
3. Which delivery surfaces are allowed to receive which signal states.
4. How tier, topic, and channel routing are determined.
5. How duplicate or invalid delivery is prevented.
6. What proof must exist for distribution events.
7. How failures, retries, and degraded delivery are handled.
8. How affiliate, admin, and public-facing access are separated from core strategy ownership.

If runtime behavior conflicts with this document, distribution logic must be corrected or this document must be updated canonically before further architecture changes proceed.

## 2. Final Principle

No signal may be delivered to an external destination unless its distribution path is canonically authorized, state-valid, tier-valid, observable, and bounded by ownership rules.

A distribution behavior is considered non-canonical if it introduces:
- message delivery without canonical signal-state eligibility
- channel or topic routing outside declared policy
- bypass of the distribution router
- publishing without observability proof
- duplicate or replay-style emission without canonical justification
- affiliate/admin access to restricted internal surfaces
- hidden coupling between strategy logic and delivery presentation
- direct publishing policy encoded inside the wrong module boundary

## 3. Distribution Scope

This architecture applies to:
- PRE distribution
- CONFIRM distribution
- OPEN_NOW distribution
- RESULT distribution
- tier-based routing
- channel and topic mapping
- publisher invocation
- retry and failure handling
- delivery observability
- restart-safe re-entry behavior
- admin-controlled routing surfaces
- affiliate-relevant distribution surfaces where applicable
- future compatible extension surfaces

This document applies whether delivery is broad or narrow. Message volume changes operational load, not the obligation to respect canonical routing.

## 4. Position in Runtime Pipeline

The high-level distribution architecture is:

Market Data  
→ Strategy Runtime  
→ Decision Object  
→ FSM Runtime  
→ Signal Event  
→ Distribution Router  
→ Tier / Topic Policy Filter  
→ Publisher Abstraction  
→ External Delivery Surface  
→ User Consumption  
→ Outcome / Analytics Feedback Surfaces

Distribution is downstream of strategic decisioning and lifecycle validation. It is not allowed to redefine strategy truth. It may only route, format, publish, record, and report according to canonical policy.

## 5. Canonical Distribution Objects

The distribution layer may only act on canonical objects already validated by upstream layers.

These include:
- Decision object or equivalent upstream strategic output
- FSM-valid state transitions
- SignalEvent or equivalent canonical distribution payload
- distribution state or message registry if persisted
- topic/channel mapping config
- delivery observability events
- outcome-linked references for later result publication

The distribution layer must not invent its own alternative truth about signal validity.

## 6. Distribution States

The canonical externally relevant signal lifecycle states are:

- PRE
- CONFIRM
- OPEN_NOW
- RESULT

Additional internal states may exist in runtime, but external distribution eligibility must remain explicit and canonical.

### 6.1 PRE

PRE is an early external visibility state intended for bounded awareness before stronger action readiness.

PRE distribution must remain aligned with the canonical rules governing:
- early-stage visibility
- confidence gating
- audience entitlement
- anti-flood discipline
- later transition continuity

### 6.2 CONFIRM

CONFIRM represents a stronger validated stage than PRE and must only be distributed when the FSM/runtime contract marks that signal as canonically eligible.

CONFIRM must not be emitted merely because a formatted message exists.

### 6.3 OPEN_NOW

OPEN_NOW is the most operationally sensitive live-action state in the main distribution chain.

Its routing must be tightly controlled, deduplicated, observable, and restart-safe.

OPEN_NOW must never be published to unauthorized tiers or destinations.

### 6.4 RESULT

RESULT closes the external lifecycle loop for eligible delivery surfaces.

RESULT routing must preserve continuity with the signal identity or reference chain that produced the prior externally visible state.

## 7. Distribution Tiers and Access Segmentation

Distribution must support tiered access segmentation.

At minimum, the architecture may include a combination of:
- public/free surfaces
- standard subscription surfaces
- premium/pro surfaces
- vip/full-access surfaces
- internal/admin observation surfaces
- affiliate-limited statistics surfaces

This document does not hardcode commercial naming as the source of truth. What is canonical is that entitlement-based routing exists and is enforced.

Tier assignment determines which signal states and message classes are externally visible to which audience category.

## 8. Tier Visibility Principles

The canonical routing policy must satisfy all of the following:

1. Lower-access tiers must not receive states reserved for higher-access tiers.
2. Higher-access tiers may receive the states granted to their tier policy.
3. Topic or channel routing must reflect entitlement, not convenience.
4. Presentation differences must not silently alter entitlement policy.
5. Distribution must remain explainable in policy terms and observable in proof logs.

This means delivery policy belongs to the routing layer and related canonical config, not to ad hoc message send code.

## 9. Channel and Topic Structure

External delivery surfaces may be implemented using:
- separate Telegram channels
- separate supergroup topics
- mixed channel/topic structures
- future compatible delivery abstractions

The canonical architecture requires that each externally reachable delivery surface has:
- an explicit identity
- an explicit entitlement role
- an explicit mapping from state/event class to destination
- an operational owner path
- observability traceability

No destination should exist merely as an unnamed hardcoded sink.

## 10. Distribution Router Ownership

The distribution router is the canonical owner of delivery selection.

Its responsibilities include:
- receiving canonical distribution-eligible signal events
- determining destination set
- applying tier/state/topic policy
- preventing unauthorized routing
- preparing publish tasks for the publisher abstraction
- triggering distribution observability events
- supporting retry-aware and restart-safe control flow

The router must not:
- redefine trading logic
- invent signal states
- mutate strategy truth
- own Telegram API transport details
- own analytics interpretation beyond distribution metadata
- bypass canonical eligibility checks

## 11. Publisher Ownership

The publisher abstraction is the canonical owner of external send execution.

Its responsibilities include:
- formatting handoff handling where applicable
- message send execution
- delivery attempt tracking
- Telegram or external API interaction
- rate-limit aware sending
- retry mechanics at the transport layer
- transport failure reporting

The publisher must not:
- decide tier entitlement
- decide whether a signal is strategy-valid
- change signal state
- silently reroute unauthorized messages
- replace the router as policy owner

## 12. Routing Policy Layers

Distribution routing must be determined by the combination of:
- signal state eligibility
- destination entitlement class
- topic/channel mapping
- admin-approved configuration
- anti-duplication rules
- restart/recovery safety rules
- transport health awareness where applicable

All of the above must remain architecturally separable and testable.

## 13. Signal Lifecycle to Delivery Lifecycle Mapping

A canonical signal lifecycle and a canonical delivery lifecycle are related but not identical.

For example:
- a signal may be valid internally but not entitled for a given external surface
- a signal may be entitled but temporarily delayed by transport constraints
- a signal may require a result follow-up on a different timing edge than the initial delivery
- a signal may fail transport while remaining valid internally

The distribution system must preserve this distinction.

## 14. Duplicate Prevention and Replay Safety

Distribution must be protected against:
- duplicate PRE emission for the same intended delivery event
- duplicate CONFIRM emission
- duplicate OPEN_NOW emission
- duplicate RESULT emission
- replay after restart when already published
- accidental repeated publish due to retry confusion
- cross-topic duplicate leakage

Canonical protection may include:
- message identity keys
- distribution state registry
- idempotency checks
- per-state publish markers
- restart recovery checks
- retry-aware transport bookkeeping

No externally sensitive state should rely on memory-only assumptions if duplicate risk exists.

## 15. Restart Safety

Distribution behavior must remain safe across restart events.

After restart, the system must not:
- re-emit already published sensitive states without canonical reason
- lose routing ownership boundaries
- forget delivery markers required for duplicate prevention
- publish stale items as if they were new
- confuse partial transport failure with publish eligibility

Where persistent distribution state exists, it must be treated as a protected state surface.

## 16. Observability Proof

All material distribution actions must be observable.

Observable events should include, as applicable:
- distribution eligibility accepted or rejected
- routing decision made
- destination set computed
- publish attempt started
- publish success
- publish failure
- retry scheduled
- retry exhausted
- duplicate prevented
- unauthorized routing blocked
- result linkage published

The purpose of observability is proof, debugging, and policy verification, not vanity logging.

## 17. Delivery Logging Requirements

Distribution observability must be sufficient to answer:
- what signal or event was routed
- which state was involved
- which destination class was selected
- which concrete channel/topic was targeted
- whether publish succeeded or failed
- whether retry occurred
- whether duplicate suppression occurred
- whether the final distribution result matched policy

A delivery system that sends messages without reconstructable evidence is non-canonical.

## 18. Failure Handling

Distribution failures must be handled in a bounded and explicit way.

Failure classes may include:
- network failure
- publisher API failure
- channel/topic permission failure
- invalid destination mapping
- malformed payload failure
- transport throttling
- duplicate-state conflict
- unavailable external surface

Failure handling must never silently widen access or silently drop architectural guarantees.

## 19. Retry Rules

Retries may exist, but retries are not permission to violate idempotency or routing correctness.

Retry design must ensure:
- same message is not wrongly transformed into a new entitlement event
- retry does not cause duplicate operational alerts without traceability
- retry exhaustion is visible
- retry behavior is transport-aware, not policy-guessing

Retry belongs to the delivery reliability layer, not the entitlement policy layer.

## 20. Rate Limit Management

Telegram and similar delivery surfaces may impose rate limits and throughput constraints.

The architecture must support:
- send pacing
- queue discipline
- backoff where needed
- retry coordination
- failure visibility
- no hidden silent dropping of critical delivery classes without evidence

Rate limiting is an operational transport concern and must not rewrite entitlement rules.

## 21. Security and Access Boundaries

Distribution channels and topics are externally exposed surfaces and must be governed accordingly.

Canonical security boundaries include:
- controlled bot permissions
- controlled admin permissions
- restricted routing config mutation
- no direct strategy access from affiliate surfaces
- no unauthorized read path into engine internals from delivery layers
- protected operational credentials and mappings

Distribution convenience must never weaken strategic or operational isolation.

## 22. Signal Leak Prevention

The architecture must assume that external signal leakage is a risk.

Mitigation may include:
- careful tier separation
- forwarding restrictions where supported
- watermarking or attribution strategies where applicable
- membership governance
- differentiated content entitlement
- auditability of which surface received which class of message

Leak prevention is not only a UI policy. It is part of delivery architecture and governance.

## 23. Affiliate Adjacency

Affiliate-driven growth may coexist with the distribution system, but affiliates are not distribution owners.

Affiliate-related surfaces may expose:
- referral counts
- attributed subscriber metrics
- commission-relevant metrics
- campaign performance summaries

Affiliate surfaces must not expose:
- strategy internals
- restricted signal states beyond entitlement
- raw engine diagnostics
- operational override capability
- internal routing control
- protected observability streams beyond authorized summaries

## 24. Admin and Control Surface Adjacency

Admin surfaces may interact with distribution architecture in bounded ways.

Examples:
- route enable/disable controls
- topic mapping controls
- publication freeze/unfreeze controls
- health and send-status visibility
- test surface for non-production validation
- evidence and proof review surfaces

However, admin tools must still remain subordinate to canonical governance and system invariants.

## 25. Distribution Freeze / Controlled Hold

The architecture may support controlled hold states for operational safety.

Examples include:
- temporary publish freeze
- maintenance hold
- channel/topic remapping freeze
- degraded delivery mode under controlled governance

A hold state must be explicit, observable, and reversible. It must not create hidden entitlement drift.

## 26. Relationship to Telegram UX

Distribution architecture and Telegram UX are adjacent but not identical.

Distribution architecture defines:
- who may receive what
- where it is routed
- under what state conditions
- with what safety and proof

Telegram UX defines:
- how externally delivered content is presented
- wording, layout, formatting, and user-facing readability patterns

The two must remain aligned, but one must not absorb the other’s ownership.

## 27. Relationship to Decision Audit and Analytics

Distribution is downstream from decision production, but it must remain analyzable.

This means the system should be able to study:
- which decisions reached which tiers
- where routing succeeded or failed
- where entitlement blocked distribution
- where duplicates were prevented
- whether publish latency or failure affected external lifecycle quality
- how results closed the loop across distributed states

Distribution analytics may inform governance and improvement, but analytics must not silently mutate live routing truth.

## 28. Relationship to Outcome Tracking

When RESULT or equivalent closure states are published, the distribution chain must preserve identity continuity with the prior published signal path.

This continuity is necessary for:
- user trust
- lifecycle traceability
- performance analytics
- result publication integrity
- dispute resolution
- audit reconstruction

## 29. Future Extension Rule

The architecture may later extend to additional destinations such as:
- Discord
- web dashboards
- mobile clients
- external APIs
- partner surfaces

Such extensions are allowed only if they preserve the same canonical principles:
- explicit entitlement
- explicit destination identity
- explicit routing ownership
- observability proof
- duplicate safety
- restart safety
- governance compatibility

New destinations do not justify bypassing the router/publisher discipline.

## 30. Forbidden Distribution Behaviors

The following are non-canonical:
- direct publish bypassing the distribution router
- tier logic embedded ad hoc in unrelated modules
- publisher deciding entitlement policy
- routing to undocumented destinations
- unobservable external publication
- duplicate OPEN_NOW without canonical justification
- result publication without identity continuity
- affiliate access to restricted operational surfaces
- hidden topic remaps without governance
- retry logic that causes unauthorized replay
- distribution code mutating strategy truth

## 31. Canonical Success Standard

The distribution architecture is functioning canonically only when:
- eligible states are routed to authorized destinations only
- unauthorized destinations receive nothing
- publisher transport is bounded by rate-limit and retry discipline
- duplicates are prevented or explicitly explainable
- restart does not break routing safety
- observability proves the external lifecycle
- admin/affiliate boundaries remain intact
- architecture remains consistent with active canonical documents

## 32. Final Enforcement Statement

No future distribution implementation may bypass the ownership, routing, proof, and safety rules defined in this document.

If a faster or simpler delivery path conflicts with this architecture, that path is non-canonical.

External delivery is allowed only through canonical control, never instead of it.