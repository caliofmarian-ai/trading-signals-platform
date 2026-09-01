# STRATEGY_INTELLIGENCE_SYSTEM_v2.0.0

Version: 2.0.0  
Path: /opt/binarybot/docs/canonical/active/STRATEGY_INTELLIGENCE_SYSTEM_v2.0.0.md  

Linked Documents:
- /opt/binarybot/docs/canonical/active/CANONICAL_STRATEGY_STACK_v1.0.0.md
- /opt/binarybot/docs/canonical/active/RESEARCH_AND_LEARNING_FRAMEWORK_SPEC_v2.0.0.md
- /opt/binarybot/docs/canonical/active/PERFORMANCE_ANALYTICS_SPEC_v2.0.0.md
- /opt/binarybot/docs/canonical/active/OUTCOME_TRACKING_SPEC_v2.0.0.md
- /opt/binarybot/docs/canonical/active/DECISION_AUDIT_SPEC_v2.0.0.md
- /opt/binarybot/docs/canonical/active/AUTONOMOUS_STRATEGY_EVOLUTION_SYSTEM_v2.0.0.md


Status: Active Canonical  
Path target: `/opt/binarybot/docs/canonical/active/STRATEGY_INTELLIGENCE_SYSTEM_v2.0.0.md`  
Supersedes: `/opt/binarybot/docs/STRATEGY_INTELLIGENCE_SYSTEM.md`

Related canonical documents:
- `/opt/binarybot/docs/canonical/active/CANONICAL_STRATEGY_STACK_v1.0.0.md`
- `/opt/binarybot/docs/canonical/active/ALGO_SPEC_v2.0.0.md`
- `/opt/binarybot/docs/canonical/active/DECISION_OBJECT_CANONICAL_SPEC_v1.0.0.md`
- `/opt/binarybot/docs/canonical/active/FSM_DECISION_ENGINE_SPEC_v1.0.0.md`
- `/opt/binarybot/docs/canonical/active/SIGNAL_ENGINE_EXECUTION_SPEC_v2.0.0.md`
- `/opt/binarybot/docs/canonical/active/SR_CORRIDOR_ENGINE_SPEC_v2.0.0.md`
- `/opt/binarybot/docs/canonical/active/TIME_MODEL_UNIFIED_CANON_v2.0.0.md`
- `/opt/binarybot/docs/canonical/active/DECISION_AUDIT_SPEC_v2.0.0.md`
- `/opt/binarybot/docs/canonical/active/TRADE_TEMPORAL_TELEMETRY_SPEC_v2.0.0.md`
- `/opt/binarybot/docs/canonical/active/OUTCOME_TRACKING_SPEC_v2.0.0.md`
- `/opt/binarybot/docs/canonical/active/PERFORMANCE_ANALYTICS_SPEC_v2.0.0.md`
- `/opt/binarybot/docs/canonical/active/RESEARCH_AND_LEARNING_FRAMEWORK_SPEC_v2.0.0.md`
- `/opt/binarybot/docs/AUTONOMOUS_STRATEGY_EVOLUTION_SYSTEM.md`
- `/opt/binarybot/docs/canonical/active/CONTROL_PANEL_HIERARCHY_AND_INTELLIGENCE_SPEC_v2.0.0.md`
- `/opt/binarybot/docs/canonical/active/ADMIN_CONTROL_SPEC_v2.0.0.md`
- `/opt/binarybot/docs/canonical/active/ADMIN_OPERATIONS_SPEC_v2.0.0.md`
- `/opt/binarybot/docs/canonical/active/ADMIN_TREE_MAP_v2.0.0.md`
- `/opt/binarybot/docs/canonical/active/ROLE_AND_PERMISSION_MATRIX_SPEC_v2.0.0.md`
- `/opt/binarybot/docs/canonical/active/TELEGRAM_UX_v2.0.0.md`

---

## 1. PURPOSE

This document defines the canonical **Strategy Intelligence System** for BinaryBot / DROPi Signals.

The Strategy Intelligence System is not merely a report generator.
It is the intelligence layer that converts strategic evidence, operational evidence, market evidence, and governance context into:

- diagnostic visibility
- strategic understanding
- operator assistance
- safe control interfaces
- anomaly detection
- research acceleration
- AI-assisted audit
- controlled evolution recommendations

The older version correctly described the initial mission:
transform operational logs from the signal engine into an analysis, diagnostic, and control system that helps the operator understand how the strategy behaves, why signals are rejected, where bottlenecks exist, and which parameters may need optimization. It also correctly introduced three core components:
1. Strategy Heatmap
2. Admin Control Panel
3. Signal Debug Dashboard fileciteturn32file0

Those foundations remain valid.

In v2.0.0, the system is expanded and redefined so it matches the newer architecture, newer governance model, and newer truth separation rules.

---

## 2. WHY V1.0 IS NOW INSUFFICIENT

The older document is useful as a first-generation intelligence layer, but it is no longer sufficient because:

1. It is centered mainly on `engine_events.jsonl` and observability events as the dominant truth source. fileciteturn32file0

2. It assumes a relatively direct chain:
`Signal Engine -> Observability Logger -> engine_events.jsonl -> Strategy Intelligence System -> Analytics Reports -> Telegram Admin Control` fileciteturn32file0

3. It does not explicitly model:
- DecisionObject as a first-class entity before FSM
- decision truth versus market truth
- operational/admin truth
- community/business truth
- research truth
- discrepancy-aware interpretation

4. It proposes admin controls that directly mutate strategy parameters through Telegram commands, but does not sufficiently define:
- role hierarchy
- approval boundaries
- mutation safety
- auditability
- staged versus immediate effect
- rollback rules

5. It treats heatmap, control, and debug mostly as separate utilities, while the newer architecture requires them to behave as coordinated subsystems of a governed intelligence layer.

Therefore, v2.0.0 preserves the older useful ideas but upgrades them into a broader canonical system.

---

## 3. CANONICAL POSITION IN THE ARCHITECTURE

The Strategy Intelligence System sits above raw event generation and below governance, admin action, and research-driven evolution.

Canonical chain:

`Strategy Logic -> DecisionObject -> FSM -> Signal Execution -> Observability -> Decision Audit -> Telemetry -> Outcome Tracking -> Performance Analytics -> Research & Learning -> Strategy Intelligence System -> Admin / Governance / AI Audit / Controlled Evolution`

Important rule:
The Strategy Intelligence System does **not** replace raw truth sources.
It consumes and interprets them.

Its role is not to invent truth.
Its role is to transform truth into operator-usable intelligence.

---

## 4. CANONICAL TRUTH MODEL

The Strategy Intelligence System must respect truth separation.

It may consume multiple truth domains, but it must never collapse them into one unlabeled metric layer.

### 4.1 Decision truth
What the strategy believed and why.

Examples:
- score breakdown
- gate pass/fail states
- reject reasons
- corridor result
- timing result
- feasibility result
- PRE / CONFIRM / OPEN_NOW progression

### 4.2 Market truth
What price actually did after emission.

Examples:
- favorable excursion
- adverse excursion
- expiry outcome
- time-to-target
- path stability
- reversal character

### 4.3 Operational truth
What admins/operators did or failed to do.

Examples:
- late marking
- misclassification
- corrections
- overrides
- unresolved outcome queues
- missing annotations

### 4.4 Community / business truth
What the channel ecosystem experienced.

Examples:
- trust complaints
- user confusion
- affiliate dissatisfaction
- reaction lag
- signal usability perception

### 4.5 Research truth
Structured findings, hypotheses, and evidence-weighted conclusions.

The intelligence layer may compare these truth domains, but must always preserve labels.

---

## 5. CORE MISSION OF THE SYSTEM

The canonical Strategy Intelligence System must answer:

- What is happening inside the strategy?
- Why are decisions being promoted or rejected?
- Which layers are blocking quality?
- Where is the strategy strong, weak, unstable, misleading, or under-observed?
- Is performance degradation strategic, operational, or perceptual?
- Which actions are safe to recommend?
- Which actions are unsafe without further research or approval?

This is broader than the old mission of merely showing reject reasons and threshold bottlenecks. fileciteturn32file0

---

## 6. CANONICAL SUBSYSTEMS

The older version introduced:
- Strategy Heatmap
- Admin Control Panel
- Signal Debug Dashboard fileciteturn32file0

These remain, but v2.0.0 expands the subsystem map.

Canonical Strategy Intelligence System subsystems:

1. Strategy Heatmap
2. Decision Bottleneck Analyzer
3. Signal Debug Dashboard
4. Admin Intelligence Control Layer
5. Research Intelligence Bridge
6. Telegram Intelligence UX Layer
7. AI Audit and Recommendation Layer
8. Evolution Readiness Layer

---

## 7. SUBSYSTEM 1 — STRATEGY HEATMAP

### 7.1 Purpose
The Strategy Heatmap remains the primary high-level visual/analytical summary layer.

Its role is to show concentration, distribution, pressure points, and asymmetry across strategy behavior.

The old spec correctly used it to reveal strategic bottlenecks such as:
- SR too tight
- RSI threshold too strict
- trend filter too aggressive
- spike filter blocking signals
- structure score insufficient
- feasibility gate too restrictive fileciteturn32file0

That remains useful.

### 7.2 v2.0.0 expansion
The heatmap must now operate across multiple domains:

- decision heatmaps
- symbol heatmaps
- session heatmaps
- corridor/time interaction heatmaps
- operational discrepancy heatmaps
- trust/friction heatmaps
- experimentation impact heatmaps

### 7.3 Typical outputs
Examples:
- dominant rejection surfaces
- promotion bottlenecks
- score compression zones
- session-symbol instability zones
- discrepancy clusters
- admin workload spikes
- user-friction concentrations

### 7.4 Canonical rule
A heatmap may suggest a bottleneck, but not prove causality by itself.
Causality requires deeper research or controlled validation.

---

## 8. SUBSYSTEM 2 — DECISION BOTTLENECK ANALYZER

This is a formalized evolution of the old reject-reason and bottleneck distribution logic. fileciteturn32file0

### 8.1 Purpose
Determine where the decision pipeline is losing candidates and whether that loss is:
- protective
- excessive
- unstable
- contradictory
- poorly calibrated

### 8.2 Analysis scope
The analyzer should inspect:
- gate hit frequency
- gate ordering effects
- dominant rejection reasons
- score-band compression
- late-stage failure clusters
- conflict between corridor and timing logic
- feasibility kill-zones
- PRE-to-CONFIRM leakage
- CONFIRM-to-OPEN_NOW blockage

### 8.3 Output categories
Possible findings:
- healthy strictness
- over-strict filtering
- unstable filtering
- redundant gating
- misleading score calibration
- corridor/time misalignment
- parameter harshness suspicion

This subsystem gives the operator a more precise picture than a simple reject histogram.

---

## 9. SUBSYSTEM 3 — SIGNAL DEBUG DASHBOARD

The older document correctly defined the need for per-signal transparency and showed useful debug fields such as:
- symbol
- timeframe
- trend_class
- RSI
- EMA gap
- ATR
- score
- thresholds
- reject_reason
- support/resistance distance fileciteturn32file0

This remains essential.

### 9.1 Canonical purpose
The Signal Debug Dashboard must explain, for a single candidate or signal:
- what the system saw
- what the system decided
- why it decided that
- what happened afterwards
- whether operational handling distorted interpretation

### 9.2 Required layers in debug view
Every serious debug view should distinguish:
- decision snapshot
- gate explanation
- score explanation
- context explanation
- post-emission market evidence
- operational annotations
- confidence or caveat flags

### 9.3 Debug modes
Suggested modes:
- candidate view
- rejected signal view
- emitted signal view
- discrepancy view
- experiment-affected signal view

### 9.4 Rule
Debug output must explain decisions without pretending certainty where evidence is incomplete.

---

## 10. SUBSYSTEM 4 — ADMIN INTELLIGENCE CONTROL LAYER

The older document proposed Telegram commands such as:
- `/strategy`
- `/symbols`
- `/thresholds`
- `/sr`
- `/spike` fileciteturn32file0

The core idea is good: operators need direct strategic control.
But in v2.0.0, this must become governance-safe.

### 10.1 Purpose
Provide controlled interfaces for viewing, reviewing, proposing, approving, and applying strategic actions.

### 10.2 Not all controls are equal
The system must separate:
- read-only intelligence views
- proposal actions
- staged mutation actions
- production mutation actions
- rollback actions

### 10.3 Role awareness
Control access must reflect hierarchy:
- Owner
- principal admin
- function admins
- research/intelligence roles
- affiliate or limited-visibility roles

### 10.4 Canonical rule
No important production strategy mutation should be invisible, unaudited, or role-agnostic.

### 10.5 Intelligence-driven actions
Examples of safe admin actions:
- inspect parameter state
- inspect drift state
- inspect symbol health
- inspect discrepancy queues
- create experiment proposal
- approve a staged change
- rollback last controlled mutation

This is more mature than direct blind threshold editing.

---

## 11. SUBSYSTEM 5 — RESEARCH INTELLIGENCE BRIDGE

This is a major new requirement absent from the old v1.0 system.

### 11.1 Purpose
Bridge the gap between analytics/research and operator decisions.

The intelligence layer should surface:
- findings that deserve review
- hypotheses worth testing
- confidence-rated evidence
- unresolved contradictions
- recommended experiment candidates

### 11.2 Why this matters
Without this bridge:
- research becomes passive
- admin control becomes intuition-driven
- strategy changes become reactive

### 11.3 Canonical outputs
Examples:
- “SR harshness likely excessive in London on EURAUD”
- “USDJPY appears operationally noisy, not strategically weak”
- “Late-session CONFIRM signals show trust drop despite acceptable market truth”
- “Experiment candidate: tighten rejection explanation messaging before changing filters”

This subsystem makes intelligence operationally useful.

---

## 12. SUBSYSTEM 6 — TELEGRAM INTELLIGENCE UX LAYER

The older document already understood Telegram as the admin control surface. fileciteturn32file0  
v2.0.0 expands this to a full intelligence UX concept.

### 12.1 Purpose
Turn complex strategic information into Telegram-native, operator-usable interfaces.

### 12.2 Required capabilities
The Telegram intelligence UX layer should support:
- compact status views
- drill-down views
- discrepancy review cards
- experiment review cards
- bottleneck summaries
- symbol watchlists
- session alerts
- risk/guardrail warnings

### 12.3 UX principle
Telegram is not a terminal dump.
It is a decision interface.

### 12.4 Canonical rule
Outputs should be role-aware, concise, and action-oriented.

---

## 13. SUBSYSTEM 7 — AI AUDIT AND RECOMMENDATION LAYER

The old document proposed future AI extensions such as:
- threshold suggestions
- SR distance optimization
- RSI tuning
- strategy evolution engine
- A/B testing
- simulation
- replay fileciteturn32file0

Those ideas remain valuable, but must be governed.

### 13.1 AI may assist with
- anomaly clustering
- hypothesis generation
- bottleneck ranking
- suspicious parameter-region detection
- research summary drafting
- contradiction detection across truth layers

### 13.2 AI may not independently do
- silent production mutation
- truth rewriting
- unauthorized threshold rollout
- hidden rule activation
- governance bypass

### 13.3 Canonical output style
AI recommendations must be:
- explainable
- confidence-rated
- bounded
- reviewable
- attributable to evidence

---

## 14. SUBSYSTEM 8 — EVOLUTION READINESS LAYER

This is another major maturity upgrade.

### 14.1 Purpose
Assess whether the system is actually safe for experimentation or mutation.

### 14.2 Inputs
It should consider:
- data integrity
- discrepancy rate
- instrumentation completeness
- current drift intensity
- recent change volume
- role approval readiness
- rollback readiness

### 14.3 Typical states
Examples:
- safe for research only
- safe for staged experiment
- safe for low-risk parameter tuning
- unsafe for mutation
- rollback-first recommended

This prevents chaotic optimization cycles.

---

## 15. CANONICAL INPUT SOURCES

The old v1.0 document focused on:
- `engine_events.jsonl`
- signal engine
- observability logger
- analytics tooling fileciteturn32file0

These remain important, but the intelligence layer now consumes more.

Typical inputs may include:
- decision audit records
- observability event streams
- telemetry records
- outcome reconciliation data
- performance analytics outputs
- research findings
- admin action logs
- discrepancy queues
- optional channel/business feedback signals

Important rule:
No single file is the intelligence truth by itself.

---

## 16. CANONICAL OUTPUTS

The Strategy Intelligence System should produce outputs such as:

- strategic state summaries
- bottleneck maps
- debug cards
- discrepancy alerts
- drift alerts
- experiment proposals
- risk advisories
- rollback advisories
- operator review queues
- AI-assisted summaries
- governance-ready recommendations

---

## 17. METRICS AND SIGNALS THE SYSTEM SHOULD SURFACE

The old document correctly surfaced:
- decision distribution
- reject reason distribution
- symbol activity
- average score
- strategy bottlenecks fileciteturn32file0

These remain foundational.

v2.0.0 expands the surface set to include:

### Decision layer
- candidate count
- promotion rate
- late-stage rejection rate
- gate pressure map
- score-band density

### Market layer
- post-emission favorable excursion
- time-to-fail
- expiry alignment
- path quality segmentation

### Operational layer
- unresolved outcome count
- correction rate
- override rate
- admin latency
- discrepancy density

### UX / business layer
- trust-friction markers
- unclear-signal clusters
- affiliate dissatisfaction hotspots

### Research layer
- active hypotheses
- pending experiments
- confidence-weighted findings
- evidence quality warnings

---

## 18. STRATEGIC BENEFITS

The older document listed benefits such as:
- transparent strategy behavior
- faster optimization
- tuning without direct code edits fileciteturn32file0

These remain real, but v2.0.0 adds stronger benefits.

If implemented correctly, the Strategy Intelligence System provides:

- transparent multi-layer diagnosis
- safer operator control
- earlier detection of false bottlenecks
- separation of strategy weakness from operational distortion
- evidence-driven admin action
- AI assistance without governance loss
- better Telegram-native control UX
- safer path toward autonomous evolution

---

## 19. FILE AND MODULE DIRECTION

The old document proposed tools such as:
- `/opt/binarybot/tools/strategy_auditor_daily.py`
- `/opt/binarybot/tools/strategy_auditor_lib.py`
and analytics folders such as:
- `/opt/binarybot/analytics/reports/`
- `/opt/binarybot/analytics/cache/` fileciteturn32file0

Those may still exist as implementation starting points.

Canonical v2.0.0 direction is broader and may include:
- strategy intelligence aggregators
- decision audit summarizers
- bottleneck analyzers
- Telegram card renderers
- admin review queues
- AI audit helpers
- experiment status reporters
- discrepancy inspectors

This document does not lock exact filenames, but it does lock the system role and boundaries.

---

## 20. ADMIN / CONTROL PANEL UPGRADE PROPOSALS

Because you asked that patching should include upgrade proposals, this section records them explicitly.

### 20.1 Proposed admin upgrades
- strategy state dashboard by truth layer
- staged mutation workflow instead of direct blind edits
- mutation approval queue
- rollback panel
- drift panel
- discrepancy review panel
- symbol health matrix
- session health matrix
- experiment tracker

### 20.2 Proposed Telegram UX upgrades
- compact summary cards
- expandable debug cards
- role-aware action buttons
- warning banners for low-confidence conclusions
- distinction between “finding”, “hypothesis”, and “approved action”

### 20.3 Proposed intelligence upgrades
- contradiction detector between decision truth and market truth
- pattern-ranking engine
- experiment recommendation engine
- evidence confidence engine
- false-bottleneck detector

### 20.4 Proposed AI upgrades
- AI-generated research digest
- anomaly clustering assistant
- explanation assistant for reject clusters
- guarded recommendation assistant

---

## 21. NON-GOALS

This document does not define:
- raw signal-generation formulas
- broker execution plumbing
- every Telegram callback name
- every exact database schema
- every future AI model choice
- unrestricted autonomous control

It defines the canonical architecture and purpose of the Strategy Intelligence System.

---

## 22. SUMMARY

The old `STRATEGY_INTELLIGENCE_SYSTEM.md` established an important first-generation vision:
use engine logs, strategy heatmaps, admin Telegram controls, and debug dashboards to understand strategy behavior, reveal bottlenecks, and allow faster optimization without direct code edits. It also correctly identified future directions such as AI optimization, performance tracking, and strategy evolution. fileciteturn32file0

In v2.0.0, that vision is preserved but matured.

The Strategy Intelligence System is now defined as a multi-layer intelligence framework that:
- consumes multiple labeled truth domains
- powers heatmaps, bottleneck analysis, debug views, and Telegram-native intelligence UX
- supports role-aware and governance-safe control
- bridges research to operations
- enables AI-assisted audit without silent mutation
- evaluates readiness for controlled evolution

This makes the intelligence layer compatible with the current architecture rather than leaving it anchored to the old observability-only model.

## 20. AI Strategy Auditor as Intelligence Subcomponent

This section absorbs bounded content from AI_STRATEGY_AUDITOR_SPEC.md.

### 20.1 Auditor role
The AI Strategy Auditor is an intelligence-layer subcomponent that transforms structured observability and outcome evidence into measured diagnostics, bottleneck views, and optimization hypotheses.

### 20.2 Non-execution boundary
Auditor outputs may guide research and review, but they do not directly override active execution truth or governance.

### 20.3 Example focus areas
Auditor analysis may include rejection clusters, symbol starvation, focus/watchlist inefficiency, cooldown-side effects, and channel inactivity patterns.

## 21. Intelligence Data Pipeline and Snapshot Flow

This section absorbs bounded content from INTELLIGENCE_DATA_PIPELINE_DEFINITION.md.

### 21.1 Pipeline role
The intelligence data pipeline may normalize event sources, produce snapshots, aggregate research-facing summaries, and expose bounded admin/intelligence views.

### 21.2 Data classes
Relevant pipeline inputs may include lifecycle events, outcome signals, audit logs, active symbol state, and operator-reviewed evidence.

### 21.3 Snapshot boundary
Snapshotting supports intelligence and analytics surfaces but must not replace active runtime truth ownership.

## 22. Intelligence Module Responsibilities

This section absorbs bounded content from INTELLIGENCE_FILES_AND_MODULE_MAP.md.

### 22.1 Responsibility families
Canonical-compatible intelligence responsibilities may include pipeline ingestion, aggregation, snapshot persistence, and admin/research rendering.

### 22.2 Boundary rule
These responsibilities support the intelligence layer and must remain downstream of canonical execution, distribution, and lifecycle truth.

## 23. Intelligence/Proof Relationship Clarifications

This section absorbs bounded intelligence clarifications extracted from STATISTICAL_PROOF_LAYER.md.

### 23.1 Intelligence role
The intelligence layer may consume proof-oriented statistical summaries as one input among many for evaluation, diagnostics, and hypothesis ranking.

### 23.2 No replacement rule
A proof layer does not replace active intelligence ownership, analytics ownership, or strategy governance.

### 23.3 Canonical fit
Any retained concepts from the older Statistical Proof Layer material are now canonically subordinate to the active intelligence/research/analytics cluster.
