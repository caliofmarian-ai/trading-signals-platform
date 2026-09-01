# SYSTEM_ARCHITECTURE_MAP_v2.0.0

Version: 2.0.0  
Status: Active Canonical  
Path: /opt/binarybot/docs/canonical/active/SYSTEM_ARCHITECTURE_MAP_v2.0.0.md

Linked Documents:
- SYSTEM_INVARIANTS_v2.0.0.md
- MODULE_INTERFACE_SPEC_v2.0.0.md
- EVENT_SCHEMA_SPEC_v2.0.0.md
- DECISION_AUDIT_SPEC_v2.0.0.md
- SIGNAL_DISTRIBUTION_SPEC_v2.0.0.md
- OBSERVABILITY_LOGGING_SPEC_v2.0.0.md
- PERFORMANCE_ANALYTICS_SPEC_v2.0.0.md
- OUTCOME_TRACKING_SPEC_v2.0.0.md
- TELEGRAM_UX_v2.0.0.md
- FAILURE_RECOVERY_SPEC_v2.0.0.md
- STRATEGY_INTELLIGENCE_SYSTEM_v2.0.0.md
- AUTONOMOUS_STRATEGY_EVOLUTION_SYSTEM_v2.0.0.md

Depends on:
- SYSTEM_INVARIANTS_v2.0.0.md
- MODULE_INTERFACE_SPEC_v2.0.0.md
- EVENT_SCHEMA_SPEC_v2.0.0.md

Code Alignment:
- core/strategy_v2.py
- core/signal_engine.py
- core/fsm_runtime.py
- core/distribution_router.py
- core/telegram_publisher.py
- core/observability_logger.py
- core/outcome_service.py
- core/analytics_engine.py
- bot_service.py

## 0. Purpose

This document defines the canonical top-level architecture map for BinaryBot / DROPi Signals.

Its role is to organize the documentation library, subsystem responsibilities, and cross-layer relationships into one authoritative navigation document.

This document is not a replacement for subsystem specifications.  
It classifies them, anchors them, and defines where each concern belongs in the architecture.

Its purpose is to prevent:
- duplicate canonical documents for the same concern
- architectural drift across layers
- hidden ownership conflicts
- unclear responsibility boundaries
- incorrect placement of new specs
- confusion between execution, audit, intelligence, admin, and distribution responsibilities

This document is the master architecture index for the project.

## 1. Canonical Position

This document sits above individual subsystem specifications as the top-level architecture map.

It answers the following questions:

1. Which architectural layers exist in the system.
2. What each layer is allowed to own.
3. How layers depend on one another.
4. Which documents primarily belong to each layer.
5. Where a new concern must be classified before a new canonical document is created.

If any document classification, subsystem ownership, or cross-layer dependency conflicts with this map, the conflict must be resolved canonically before further implementation proceeds.

## 2. Final Principle

BinaryBot / DROPi Signals must be understood as a layered system with explicit ownership boundaries.

Every canonical concern must have:
- one primary architectural home
- one primary responsible layer
- explicit dependencies on lower layers where needed
- no silent duplication across multiple specs

No higher layer may silently redefine the truth of a lower layer.

That means:
- INTELLIGENCE may not invent events that OBSERVABILITY never recorded
- AUDIT may not invent decisions that ENGINE or FSM never produced
- DISTRIBUTION may not reinterpret strategy validity outside canonical routing rules
- ADMIN may not bypass canonical permission, governance, or proof requirements
- UX may not embed strategy logic
- analytics may not mutate live signal decisions unless explicitly authorized by canonical architecture

## 3. Architectural Backbone

The canonical architecture layers of BinaryBot / DROPi Signals are:

1. ENGINE
2. FSM
3. OBSERVABILITY
4. AUDIT
5. INTELLIGENCE
6. ADMIN
7. DISTRIBUTION
8. RISK

These layers form the primary architectural backbone of the system.

Every canonical document must belong primarily to one of these layers, even if it depends on multiple others.

A document may reference multiple layers, but it must still have one primary home for ownership and governance.

## 4. Top-Level System Flow

The high-level system flow is:

Market Data  
→ ENGINE  
→ FSM  
→ OBSERVABILITY  
→ AUDIT  
→ INTELLIGENCE  
→ ADMIN CONTROL / HUMAN REVIEW  
→ DISTRIBUTION  
→ OUTCOMES / RISK FEEDBACK

This flow is a top-level architectural orientation model.

It must not be misread as meaning every subsystem acts in one simple linear loop.  
Some layers consume outputs asynchronously, some operate continuously, and some serve governance or interpretation rather than direct execution.

The purpose of this flow is to explain the dominant movement of information:
- from raw market input
- to strategy decision
- to lifecycle control
- to factual recording
- to decision explanation
- to strategic interpretation
- to human/admin visibility
- to publication
- to post-publication outcome and risk refinement

## 5. Layer 1 — ENGINE

The ENGINE layer is responsible for transforming normalized market input into strategy decisions.

It answers questions such as:
- what is the market doing now
- what setup exists
- what score does the setup have
- which gates passed or failed
- should the setup be rejected, held, shortlisted, or advanced

Typical ENGINE responsibilities include:
- market data intake
- candle normalization
- indicator computation
- signal scoring
- threshold application
- corridor evaluation
- feasibility evaluation
- strategy parameter interpretation
- production of the canonical decision object before lifecycle handling

ENGINE owns decision generation, not lifecycle progression and not publication.

ENGINE must not:
- publish Telegram messages
- mutate distribution state
- bypass persistence ownership
- replace FSM logic
- inject admin-side decisions directly into strategy output without canonical authorization

Typical canonical documents primarily belonging to ENGINE:
- MODULE_INTERFACE_SPEC_v2.0.0.md
- SYSTEM_INVARIANTS_v2.0.0.md
- strategy-related active strategy specifications
- parameter surface / runtime execution / market interface documents when canonically active

Typical code alignment:
- core/strategy_v2.py
- core/signal_engine.py
- candle adapter layer
- params loading logic

## 6. Layer 2 — FSM

The FSM layer is responsible for lifecycle progression of already-created decisions/signals.

It answers questions such as:
- where is the signal in its lifecycle
- can PRE become CONFIRM
- can CONFIRM become OPEN_NOW
- did the setup die
- was the signal invalidated
- did time, stage conditions, or contradictory market evolution terminate progression

FSM owns lifecycle truth after decision creation.

FSM must not:
- invent a strategy decision that ENGINE never produced
- recompute strategy score as a substitute for ENGINE
- publish tier/channel messages directly
- bypass persistence discipline

FSM responsibilities typically include:
- stage transitions
- invalidation
- expiry
- death reasons
- state persistence
- focus/watchlist interaction where canonically assigned
- stage timing governance

Typical canonical documents primarily belonging to FSM:
- lifecycle and state transition specifications
- state persistence specifications
- focus/watchlist policy documents where canonical ownership belongs to lifecycle control

Typical code alignment:
- core/fsm_runtime.py
- persistence state files and lifecycle state management code

## 7. Layer 3 — OBSERVABILITY

The OBSERVABILITY layer records what happened.

It is the factual event-trace layer of the system.

It answers:
- what happened
- when it happened
- which subsystem emitted it
- what structured payload accompanied it
- what proof exists that a system action occurred

OBSERVABILITY is not responsible for deciding whether the strategy was good or bad.  
It records canonical operational truth.

Typical OBSERVABILITY responsibilities include:
- structured event schemas
- engine event logs
- FSM event logs
- distribution event logs
- error logs
- admin proof logs
- telemetry and trace continuity

OBSERVABILITY must not:
- reinterpret strategy quality
- substitute for audit reasoning
- silently mutate execution behavior
- become a hidden control surface

Typical canonical documents primarily belonging to OBSERVABILITY:
- OBSERVABILITY_LOGGING_SPEC_v2.0.0.md
- EVENT_SCHEMA_SPEC_v2.0.0.md
- related logging / telemetry / proof specifications

Typical code alignment:
- core/observability_logger.py
- observability event writers
- generated jsonl event stores

## 8. Layer 4 — AUDIT

The AUDIT layer explains why something happened.

It transforms factual execution traces and decision records into interpretable causal explanations.

It answers:
- why was a signal rejected
- which gate failed
- why PRE did not become CONFIRM
- why CONFIRM did not become OPEN_NOW
- which condition or threshold blocked progression
- what decision pathology dominated

AUDIT depends on:
- ENGINE truth
- FSM truth
- OBSERVABILITY truth

AUDIT must not:
- invent facts absent from lower layers
- rewrite historical outcomes
- substitute descriptive narratives for missing evidence
- redefine strategy validity after the fact

Typical AUDIT responsibilities include:
- decision cause tracking
- rejection taxonomy
- stage death explanation
- conversion failure analysis
- bottleneck explanation
- proof-ready diagnostic narratives

Typical canonical documents primarily belonging to AUDIT:
- DECISION_AUDIT_SPEC_v2.0.0.md
- signal rejection analytics documents if canonically activated
- decision proof documents if canonically activated

## 9. Layer 5 — INTELLIGENCE

The INTELLIGENCE layer transforms audit and observability outputs into operational and strategic insight.

It answers:
- what happened today
- what failed most often
- what improved
- what degraded
- which bottleneck dominates
- which symbols are starved
- which gates are pathological
- what should be reviewed before any parameter change

INTELLIGENCE serves humans, governance, and strategic learning.

It may summarize, rank, diagnose, compare, cluster, and recommend review targets.  
It must not silently replace the execution truth of lower layers.

INTELLIGENCE must not:
- fabricate missing events
- fabricate missing audit causes
- directly alter live strategy behavior unless canonically authorized by a separate active control architecture
- function as an undocumented shadow strategy engine

Typical INTELLIGENCE responsibilities include:
- strategy diagnostics
- daily summaries
- heatmaps
- bottleneck analysis
- score distribution analysis
- degradation/improvement reporting
- AI-assisted strategy interpretation
- research-oriented insights

Typical canonical documents primarily belonging to INTELLIGENCE:
- STRATEGY_INTELLIGENCE_SYSTEM_v2.0.0.md
- PERFORMANCE_ANALYTICS_SPEC_v2.0.0.md
- AUTONOMOUS_STRATEGY_EVOLUTION_SYSTEM_v2.0.0.md where applicable
- strategy auditor material if and when canonically stabilized

Typical code alignment:
- core/analytics_engine.py
- report generation components
- research and diagnostics tooling

## 10. Layer 6 — ADMIN

The ADMIN layer is the human control surface and governance layer of the system.

It answers:
- who is allowed to do what
- which commands exist
- which operator sees which controls
- which actions require proof
- which roles can view research, diagnostics, or affiliate data
- which actions require governance boundaries or owner-level authority

ADMIN is not the same thing as strategy.  
It controls, governs, and supervises, but does not own strategy truth.

Typical ADMIN responsibilities include:
- role hierarchy
- permission scope
- admin command surfaces
- control panels
- governance for config mutation
- admin proofs
- owner/admin/affiliate visibility boundaries
- operational review surfaces

ADMIN must not:
- silently overwrite canonical strategy logic
- bypass auditability
- bypass permission rules
- perform undocumented direct writes into strategy state
- collapse all roles into one unrestricted access model

Typical canonical documents primarily belonging to ADMIN:
- admin control surface documents
- role and permission specifications
- control hierarchy specifications
- affiliate-admin scope specifications where canonically activated

Typical code alignment:
- bot_service.py
- admin command routing
- admin proof creation logic

## 11. Layer 7 — DISTRIBUTION

The DISTRIBUTION layer is responsible for signal publication after validity and lifecycle status have already been decided.

It answers:
- where should this signal go
- which channel or tier should receive it
- is publication allowed
- is this duplicate content
- is a rate or channel limit reached
- should routing suppress or allow delivery under canonical rules

DISTRIBUTION owns publication routing, not signal validity.

DISTRIBUTION must not:
- reinterpret strategy score
- override lifecycle truth without canonical permission
- silently create signal validity where none exists
- embed business logic that belongs to ADMIN, RISK, or ENGINE

Typical DISTRIBUTION responsibilities include:
- routing
- channel/tier mapping
- duplicate suppression
- publication proof logs
- free/basic/pro/elite separation
- message dispatch orchestration

Typical canonical documents primarily belonging to DISTRIBUTION:
- SIGNAL_DISTRIBUTION_SPEC_v2.0.0.md
- TELEGRAM_UX_v2.0.0.md
- channel routing / channel config documents where canonically active

Typical code alignment:
- core/distribution_router.py
- core/telegram_publisher.py

## 12. Layer 8 — RISK

The RISK layer governs protective exposure logic and post-publication outcome-aware constraints.

It answers:
- how many opens are allowed
- when should new opens be throttled
- how do outcomes affect future limits
- how does the system prevent overexposure
- how do result patterns inform protective controls

RISK may overlap with outcomes, limits, and exposure control, but it must still preserve explicit ownership boundaries.

RISK depends on:
- distribution outputs
- outcome truth
- admin policy where applicable

RISK must not:
- invent outcomes
- silently override canonical execution without trace
- become an undocumented strategy filter
- hide protective suppression from auditability

Typical RISK responsibilities include:
- open-signal limits
- reset policies
- exposure throttles
- outcome-linked protection rules
- future risk-aware control constraints

Typical canonical documents primarily belonging to RISK:
- OUTCOME_TRACKING_SPEC_v2.0.0.md
- risk and limits specifications when canonically active
- reset policy specifications when canonically active

Typical code alignment:
- outcome service
- risk counters
- protective throttling logic where implemented canonically

## 13. Cross-Layer Dependency Rules

The dominant dependency directions are:

ENGINE  
→ FSM  
→ OBSERVABILITY  
→ AUDIT  
→ INTELLIGENCE

DISTRIBUTION  
→ depends on ENGINE and FSM truth

RISK  
→ depends on DISTRIBUTION outputs, OUTCOME truth, and ADMIN policy where canonically defined

ADMIN  
→ governs visibility, controls, and authorized mutation surfaces across ENGINE, DISTRIBUTION, RISK, and INTELLIGENCE, but does not erase their ownership boundaries

The following rules are mandatory:

1. Higher analytical layers may interpret lower layers but may not silently redefine them.
2. Execution layers may emit facts upward, but must not depend on speculative interpretation from higher layers unless canonically authorized.
3. Each subsystem must preserve auditability for any action that crosses a layer boundary.
4. No layer may create hidden side channels that bypass canonical contracts.

## 14. Document Classification Model

The following model governs primary document placement.

### 14.1 ENGINE
Primary home for documents about:
- strategy execution
- decision production
- market input normalization
- parameter interpretation
- execution-time computation contracts

### 14.2 FSM
Primary home for documents about:
- lifecycle state transitions
- invalidation
- expiry
- state persistence tied to lifecycle progression
- watch/focus progression if canonically assigned here

### 14.3 OBSERVABILITY
Primary home for documents about:
- logging
- event schemas
- telemetry
- proof records
- emitted trace structure

### 14.4 AUDIT
Primary home for documents about:
- decision explanations
- rejection causes
- progression failure causality
- proof interpretation
- bottleneck explanation

### 14.5 INTELLIGENCE
Primary home for documents about:
- diagnostics
- comparative reporting
- strategic insights
- analytics summaries
- AI-assisted interpretation
- learning and research outputs

### 14.6 ADMIN
Primary home for documents about:
- role hierarchy
- command permissions
- control panels
- operator scope
- admin governance
- affiliate or specialized access layers

### 14.7 DISTRIBUTION
Primary home for documents about:
- routing
- channels
- tier delivery
- publication controls
- duplication suppression
- Telegram message publication behavior

### 14.8 RISK
Primary home for documents about:
- open limits
- protective constraints
- exposure controls
- outcome-aware throttling
- resets and post-result protection logic

If a document spans multiple layers, it must still declare one primary layer of ownership.

## 15. Rule for New Canonical Documents

Before creating any new canonical document, the following questions must be answered:

1. Which architectural layer owns this concern.
2. Does an active canonical document already exist in that layer.
3. Is the concern a genuinely new specification or only an extension to an existing one.
4. Which lower layers does it depend on.
5. Which higher layers consume or interpret it.
6. Would creating a new document duplicate ownership already assigned elsewhere.

No new canonical document may be created before this classification is performed.

If an existing active document can absorb the concern without loss of clarity, extension of the active document is preferred over spawning a duplicate canonical file.

## 16. Operational Use of This Map

This architecture map must be used whenever:
- a new feature is proposed
- a new spec is requested
- a bug spans multiple subsystems
- code ownership is unclear
- a control surface is being extended
- an audit/intelligence feature is proposed
- a new admin role is introduced
- a distribution behavior is modified
- a document promotion decision is being made

This document is the master navigation layer of the documentation library.

It must be consulted before:
- promoting a non-active doc into active canonical
- splitting an existing canonical spec
- merging multiple legacy docs
- introducing a new subsystem map

## 17. Relation to Codebase

The codebase should reflect the same layered thinking used by the documentation system.

Conceptually, code grouping should mirror architectural ownership:

runtime/  
→ engine loop, boot, market connectivity, execution entrypoints

core/  
→ strategy, FSM, routing, publishing, logging, storage, outcomes, analytics

observability/  
→ generated logs and proof artifacts

analytics/  
→ reports, summaries, research artifacts

tools/  
→ auditors, summarizers, migration helpers, diagnostics, admin support tooling

docs/  
→ canonical architecture and subsystem definitions

This architecture map does not require a rigid folder ideology, but code should remain understandable through the same ownership model defined here.

## 18. Architecture Enforcement Rules

The architecture is considered non-canonical if any of the following occurs:
- one concern is owned by multiple active docs without explicit hierarchy
- one layer bypasses another layer’s canonical boundary
- strategy logic is hidden inside distribution or UX
- admin logic mutates execution truth without auditability
- audit or intelligence fabricate facts absent from recorded truth
- new documents are created without classification against this map
- documentation and code drift so far apart that ownership becomes ambiguous

When such a conflict is detected, the conflict must be resolved by:
1. identifying the correct primary layer
2. identifying the canonical owner document
3. deprecating or merging duplicate material where necessary
4. aligning code and documentation before further expansion

## 19. Future Extensions

This map may later be extended with:
- code-to-doc alignment tables
- document maturity tracking
- implementation statu