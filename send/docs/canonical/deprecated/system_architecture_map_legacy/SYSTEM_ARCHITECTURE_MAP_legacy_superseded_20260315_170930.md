BINARYBOT — SYSTEM ARCHITECTURE MAP

Version: 1.0
Status: CANONICAL SPECIFICATION
Location: /opt/binarybot/docs/SYSTEM_ARCHITECTURE_MAP.md


------------------------------------------------------------
1. PURPOSE
------------------------------------------------------------

This document defines the canonical high-level architecture map
for BinaryBot / DROPi Signals.

Its role is to organize the full documentation library into
clear architectural layers and to show how the major subsystems
connect to each other.

This document exists to solve the following problems:

- too many canonical documents without a single architecture index
- unclear dependency flow between subsystems
- risk of duplicate specifications
- difficulty onboarding new developers, admins, researchers, or investors
- difficulty understanding where a new feature belongs before implementation

This document is the top-level map of the project.

It does not replace subsystem specifications.
It classifies them.


------------------------------------------------------------
2. CORE ARCHITECTURAL PRINCIPLE
------------------------------------------------------------

BinaryBot must be understood as a layered system.

Each document belongs primarily to one architectural layer,
even if it has dependencies on multiple other layers.

The canonical architecture layers are:

1. ENGINE
2. FSM
3. OBSERVABILITY
4. AUDIT
5. INTELLIGENCE
6. ADMIN
7. DISTRIBUTION
8. RISK

These layers form the architectural backbone of the system.


------------------------------------------------------------
3. TOP-LEVEL SYSTEM FLOW
------------------------------------------------------------

The system-wide operational flow is:

Market Data
    ↓
ENGINE
    ↓
FSM
    ↓
OBSERVABILITY
    ↓
AUDIT
    ↓
INTELLIGENCE
    ↓
ADMIN CONTROL / HUMAN DECISION
    ↓
DISTRIBUTION
    ↓
OUTCOMES / RISK FEEDBACK

This flow describes how data moves from raw market input
to signal generation, strategy diagnosis, operational control,
distribution, and risk-informed refinement.


------------------------------------------------------------
4. LAYER 1 — ENGINE
------------------------------------------------------------

The ENGINE layer is responsible for:

- reading market data
- normalizing candle data
- computing indicators
- running the core signal strategy
- producing strategy decisions

The ENGINE layer answers:

- what is the market doing right now
- what score does the setup have
- should this setup be rejected, promoted, or held

Typical ENGINE responsibilities:

- candle fetching
- candle normalization
- score calculation
- gates
- thresholds
- strategy parameters
- execution timing for run_once / engine loop

Documents that belong primarily to ENGINE:

- ALGO_SPEC.md
- MODULE_INTERFACE_SPEC.md
- RUNTIME_EXECUTION_TIMELINE.md
- PARAMETER_SURFACE_SPEC.md
- CANDLE_ADAPTER_SPEC.md
- MARKET_DATA_INTERFACE_SPEC.md
- STRATEGY_V2_INTERFACE_SPEC.md

ENGINE code examples:

- core/strategy_v2.py
- core/signal_engine.py
- runtime/engine_loop.py
- runtime/market_client.py


------------------------------------------------------------
5. LAYER 2 — FSM
------------------------------------------------------------

The FSM layer is responsible for signal lifecycle control.

It defines how a signal moves between states.

The FSM layer answers:

- where in the lifecycle is the signal
- can PRE become CONFIRM
- can CONFIRM become OPEN_NOW
- did the signal die, expire, or get invalidated

Typical FSM responsibilities:

- state transitions
- lifecycle progression
- cancellation logic
- invalidation logic
- focus/watchlist interaction
- stage-specific timing

Documents that belong primarily to FSM:

- SIGNAL_DECISION_FSM_SPEC.md
- STATE_PERSISTENCE_SPEC.md
- WATCHLIST_AND_FOCUS_POLICY_SPEC.md
- SIGNAL_LIFECYCLE_SPEC.md

FSM code examples:

- core/fsm_runtime.py
- state persistence files
- focus/watchlist state files


------------------------------------------------------------
6. LAYER 3 — OBSERVABILITY
------------------------------------------------------------

The OBSERVABILITY layer is responsible for recording what happened.

It does not judge strategy quality.
It records the truth of system behavior.

The OBSERVABILITY layer answers:

- what event happened
- when it happened
- what payload was associated with it
- which subsystem emitted it

Typical OBSERVABILITY responsibilities:

- structured event schema
- engine logs
- FSM logs
- distribution logs
- admin proofs
- error events
- telemetry consistency

Documents that belong primarily to OBSERVABILITY:

- OBSERVABILITY_LOGGING_SPEC.md
- EVENT_SCHEMA_SPEC.md
- LOG_ROUTING_SPEC.md
- ERROR_REPORTING_SPEC.md

Observability files:

- /opt/binarybot/observability/engine_events.jsonl
- /opt/binarybot/observability/fsm_events.jsonl
- /opt/binarybot/observability/distribution_events.jsonl
- /opt/binarybot/observability/error_events.jsonl
- /opt/binarybot/observability/admin_proofs.jsonl

OBSERVABILITY code examples:

- core/observability_logger.py


------------------------------------------------------------
7. LAYER 4 — AUDIT
------------------------------------------------------------

The AUDIT layer explains why something happened.

This layer is distinct from observability:

- observability records events
- audit interprets strategy decisions and their causes

The AUDIT layer answers:

- why was the signal rejected
- which gate failed
- which score threshold failed
- why did PRE not become CONFIRM
- why did CONFIRM not become OPEN_NOW

Typical AUDIT responsibilities:

- decision cause tracking
- rejection taxonomy
- stage death explanation
- focus rejection cause analysis
- conversion bottleneck analysis

Documents that belong primarily to AUDIT:

- DECISION_AUDIT_SPEC.md
- STATISTICAL_PROOF_LAYER.md
- SIGNAL_REJECTION_ANALYTICS_SPEC.md if later introduced
- DECISION_PROOF_SPEC.md if later introduced

AUDIT depends on:

- OBSERVABILITY
- FSM
- ENGINE

AUDIT outputs support:

- AI Strategy Auditor
- Admin diagnostics
- Research reviews


------------------------------------------------------------
8. LAYER 5 — INTELLIGENCE
------------------------------------------------------------

The INTELLIGENCE layer transforms audit and observability data
into strategic insight.

This layer is where the system begins to explain itself
to humans in operational terms.

The INTELLIGENCE layer answers:

- what happened today
- what failed most often
- what improved
- what degraded
- what bottleneck dominates
- which symbols are starved
- which gates are pathological
- what should be reviewed before parameter changes

Typical INTELLIGENCE responsibilities:

- daily strategy audit
- strategy heatmap
- symbol starvation analysis
- bottleneck detection
- AI-generated diagnostics
- score distribution analysis
- conversion funnel reporting

Documents that belong primarily to INTELLIGENCE:

- AI_STRATEGY_AUDITOR_SPEC.md
- STRATEGY_INTELLIGENCE_SYSTEM.md
- PERFORMANCE_ANALYTICS_SPEC.md
- STRATEGY_HEATMAP_AND_SIGNAL_DIAGNOSTICS material if folded into auditor
- SIGNAL_DEBUG_DASHBOARD_SPEC.md if later introduced

INTELLIGENCE outputs:

- daily JSON reports
- daily markdown reports
- admin summary digests
- operator diagnostics
- research insights


------------------------------------------------------------
9. LAYER 6 — ADMIN
------------------------------------------------------------

The ADMIN layer is the human control surface of the system.

This layer defines:

- who is allowed to do what
- which commands exist
- which operator sees which controls
- which actions require proof logs

The ADMIN layer answers:

- who can control strategy
- who can control channels
- who can control symbols
- who can view diagnostics
- who can access research
- who can access affiliate data
- who has owner-level visibility

Typical ADMIN responsibilities:

- role hierarchy
- permissions
- Telegram admin commands
- control panel structure
- config mutation governance
- admin proof logs
- owner/admin/affiliate visibility scopes

Documents that belong primarily to ADMIN:

- ADMIN_CONTROL_SPEC.md
- ADMIN_OPERATIONS_SPEC.md
- CONTROL_PANEL_HIERARCHY_AND_INTELLIGENCE_SPEC.md
- ROLE_AND_PERMISSION_MATRIX_SPEC.md if later introduced
- AFFILIATE_ADMIN_LAYER_SPEC.md if later separated

ADMIN roles currently relevant:

- OWNER
- PRIMARY_ADMIN
- FUNCTIONAL_ADMIN
- ANALYST
- MODERATOR
- AFFILIATE_ADMIN


------------------------------------------------------------
10. LAYER 7 — DISTRIBUTION
------------------------------------------------------------

The DISTRIBUTION layer is responsible for signal publication
after strategy and lifecycle logic have already decided validity.

This layer answers:

- where does the signal go
- which channel gets it
- is the signal suppressed as duplicate
- is a channel limit reached
- is publication allowed for that tier/channel

Typical DISTRIBUTION responsibilities:

- channel routing
- tier/channel separation
- publication limits
- duplicate suppression
- publish proof logs
- free/basic/pro/elite routing
- elite fallback behavior if defined

Documents that belong primarily to DISTRIBUTION:

- CHANNEL_CONFIG_SPEC.md
- SIGNAL_DISTRIBUTION_SPEC.md
- TELEGRAM_UX.md
- CHANNEL_ROUTING_SPEC.md if later introduced

DISTRIBUTION code examples:

- core/distribution_router.py
- core/telegram_publisher.py


------------------------------------------------------------
11. LAYER 8 — RISK
------------------------------------------------------------

The RISK layer governs protection logic and post-signal outcomes.

It answers:

- how many OPEN signals are allowed
- what happens after outcomes are known
- how does user feedback affect system understanding
- when should channels stop receiving new opens
- how does the system prevent overexposure

Typical RISK responsibilities:

- daily channel limits
- open signal counters
- reset policies
- outcome integration
- signal result interpretation
- future risk throttling

Documents that belong primarily to RISK:

- OUTCOME_TRACKING_SPEC.md
- RISK_AND_LIMITS_SPEC.md
- CHANNEL_CONFIG_SPEC.md (shared with DISTRIBUTION)
- DAILY_RESET_POLICY_SPEC.md
- USER_FEEDBACK_AND_VOTING_SPEC.md if present later

RISK overlaps with:

- DISTRIBUTION
- FSM
- AUDIT


------------------------------------------------------------
12. CROSS-LAYER DEPENDENCY MAP
------------------------------------------------------------

The main dependency directions are:

ENGINE
→ FSM
→ OBSERVABILITY
→ AUDIT
→ INTELLIGENCE

ADMIN
→ controls ENGINE / DISTRIBUTION / RISK / INTELLIGENCE visibility

DISTRIBUTION
→ depends on ENGINE + FSM decisions

RISK
→ depends on DISTRIBUTION + OUTCOMES + ADMIN policy

Key principle:

Higher analytical layers must not silently redefine lower execution layers.

Meaning:

- INTELLIGENCE cannot invent decisions not present in AUDIT/OBSERVABILITY
- AUDIT cannot invent engine scores that ENGINE never produced
- DISTRIBUTION cannot reinterpret strategy validity
- ADMIN cannot bypass canonical permission rules


------------------------------------------------------------
13. DOCUMENT CLASSIFICATION TABLE
------------------------------------------------------------

The following table is the canonical classification model.

ENGINE
- ALGO_SPEC.md
- MODULE_INTERFACE_SPEC.md
- PARAMETER_SURFACE_SPEC.md
- RUNTIME_EXECUTION_TIMELINE.md
- CANDLE_ADAPTER_SPEC.md
- MARKET_DATA_INTERFACE_SPEC.md

FSM
- SIGNAL_DECISION_FSM_SPEC.md
- STATE_PERSISTENCE_SPEC.md
- WATCHLIST_AND_FOCUS_POLICY_SPEC.md
- SIGNAL_LIFECYCLE_SPEC.md

OBSERVABILITY
- OBSERVABILITY_LOGGING_SPEC.md
- EVENT_SCHEMA_SPEC.md
- LOG_ROUTING_SPEC.md
- ERROR_REPORTING_SPEC.md

AUDIT
- DECISION_AUDIT_SPEC.md
- STATISTICAL_PROOF_LAYER.md

INTELLIGENCE
- AI_STRATEGY_AUDITOR_SPEC.md
- STRATEGY_INTELLIGENCE_SYSTEM.md
- PERFORMANCE_ANALYTICS_SPEC.md

ADMIN
- ADMIN_CONTROL_SPEC.md
- ADMIN_OPERATIONS_SPEC.md
- CONTROL_PANEL_HIERARCHY_AND_INTELLIGENCE_SPEC.md

DISTRIBUTION
- CHANNEL_CONFIG_SPEC.md
- SIGNAL_DISTRIBUTION_SPEC.md
- TELEGRAM_UX.md

RISK
- OUTCOME_TRACKING_SPEC.md
- RISK_AND_LIMITS_SPEC.md
- DAILY_RESET_POLICY_SPEC.md

If a document touches multiple layers, it should still have one primary home.


------------------------------------------------------------
14. CANONICAL RULE FOR NEW DOCUMENTS
------------------------------------------------------------

Before creating any new canonical document, the following questions must be answered:

1. Which architectural layer owns this concern?
2. Does a document already exist in that layer?
3. Is this a new spec or an extension to an existing spec?
4. Which lower layers does it depend on?
5. Which higher layers will consume it?

No new document should be created before this classification is performed.

This prevents duplicate canon and architectural drift.


------------------------------------------------------------
15. OPERATIONAL USE OF THIS MAP
------------------------------------------------------------

This architecture map must be used whenever:

- a new feature is proposed
- a new spec is requested
- a bug spans multiple subsystems
- a developer needs to find the correct place for code
- an admin wants to understand system control scope
- an investor or partner needs a top-level architecture overview

It is the master navigation layer of the documentation library.


------------------------------------------------------------
16. RELATION TO CODEBASE
------------------------------------------------------------

The codebase should follow the same layered thinking.

High-level code grouping should conceptually mirror the documentation:

runtime/
→ engine loop, boot, market client

core/
→ strategy, FSM, logging, routing, publishers, storage

observability/
→ generated logs

analytics/
→ generated reports

tools/
→ auditors, summarizers, admin support scripts

docs/
→ canonical architecture and subsystem definitions

This map helps keep documentation and code aligned.


------------------------------------------------------------
17. FUTURE EXTENSIONS
------------------------------------------------------------

Planned future extensions to this map may include:

- code-to-doc mapping table
- dependency graph diagram
- owner/admin visibility matrix
- affiliate/commercial architecture map
- research subsystem map
- AI subsystem map
- document maturity levels
- implementation status tracking per document

These are optional future upgrades.


------------------------------------------------------------
18. FINAL CANONICAL STATEMENT
------------------------------------------------------------

BinaryBot / DROPi Signals is not a single script or a single bot.

It is a layered system composed of:

ENGINE
FSM
OBSERVABILITY
AUDIT
INTELLIGENCE
ADMIN
DISTRIBUTION
RISK

Every canonical document must belong to one of these layers.

This architecture map is the authoritative top-level index
for understanding how the entire project is structured.