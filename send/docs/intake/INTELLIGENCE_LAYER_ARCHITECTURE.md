INTELLIGENCE_LAYER_ARCHITECTURE.md

BinaryBot / DROPi Signals

---

1. PURPOSE

The Intelligence Layer represents the analytical and research brain of the system.

Its purpose is to transform raw runtime events into actionable strategic insight.

This layer enables the system to answer questions such as:

- Why did a signal appear?
- Why did a signal fail to progress?
- Which symbols produce profitable signals?
- Which gates suppress signals unnecessarily?
- Which focus symbols waste scanning resources?
- Which parameters produce the best outcomes?

The Intelligence Layer does not generate trading signals and does not modify strategy automatically.

It operates strictly as a diagnostic, analytical, and research layer.

---

2. POSITION IN SYSTEM ARCHITECTURE

The Intelligence Layer operates outside the runtime critical path.

Runtime signal generation must remain lightweight and deterministic.

The Intelligence Layer consumes events asynchronously.

System architecture pipeline:

Market Data (TeleData)
        ↓
Scan Scheduler
        ↓
Signal Engine
        ↓
FSM Lifecycle
        ↓
Distribution Router
        ↓
Telegram Publishing
        ↓
Outcome Feedback
        ↓
Observability Logger
        ↓
INTELLIGENCE LAYER
        ↓
Admin Intelligence Panel
        ↓
Operator Strategy Decisions

The Intelligence Layer acts as a secondary analysis pipeline.

---

3. RELATED CANONICAL DOCUMENTS

The Intelligence Layer aggregates and interprets information defined in the following canonical specifications.

Strategy Decision Layer

- "DECISION_AUDIT_SPEC.md"

Runtime Event Logging

- "OBSERVABILITY_LOGGING_SPEC.md"

Outcome Tracking

- "OUTCOME_TRACKING_SPEC.md"

Strategy Analytics

- "PERFORMANCE_ANALYTICS_SPEC.md"

Module Interfaces

- "MODULE_INTERFACE_SPEC.md"

System Architecture

- "SYSTEM_ARCHITECTURE_MAP.md"

Admin Panel Structure

- "ADMIN_TREE_MAP.md"
- "ADMIN_OPERATIONS_SPEC.md"

This document does not redefine their content.
It defines how those components integrate into a unified Intelligence Layer.

---

4. DATA SOURCES

The Intelligence Layer consumes structured runtime events.

4.1 Strategy Decisions

Source modules:

signal_engine.py
strategy_v2.py

Captured data:

symbol
decision_kind
score_total
score_components
buffer_mode
expiry_minutes
gates
debug_info
candidate_rank

Purpose:

- understand signal eligibility
- analyze scoring behavior
- analyze gate impact

---

4.2 FSM Lifecycle Events

Source module:

fsm_runtime.py

Captured data:

symbol_state
watchlist_entry
pre_stage_timestamp
confirm_stage_timestamp
open_stage_timestamp
cooldown_start
cooldown_end
focus_entry
focus_exit

Purpose:

- analyze signal lifecycle
- identify stalled signals
- detect focus deadlocks

---

4.3 Scan Scheduler Events

Source module:

scan_scheduler.py

Captured data:

active_symbols
focus_symbols
scan_cycle_symbols
teledata_calls
scan_budget_usage
symbol_scan_frequency

Purpose:

- analyze scanning efficiency
- detect symbol starvation
- monitor focus resource consumption

---

4.4 Distribution Events

Source module:

distribution_router.py

Captured data:

tier
stage_published
dedup_status
suppressed_messages
tier_counters

Purpose:

- validate signal routing
- detect distribution anomalies

---

4.5 Outcome Feedback

Source module:

outcome_service.py

Captured data:

signal_id
symbol
expiry
outcome
member_feedback
timestamp

Purpose:

- evaluate real-world signal performance
- compute success metrics

---

5. INTELLIGENCE DATA MODEL

The Intelligence Layer derives analytical objects from raw events.

5.1 SymbolHealth

Represents long-term performance of each symbol.

Attributes:

symbol
pre_rate
confirm_rate
open_rate
win_rate
reject_rate
focus_usage
focus_efficiency
scan_cost

---

5.2 RejectStats

Aggregates signal rejection reasons.

Attributes:

reject_reason
count
percentage
affected_symbols
average_score

Typical reject reasons:

MIN_AVG_RANGE
SR_SPACE_INSUFFICIENT
SPIKE_FILTER
COOLDOWN_ACTIVE
WATCHLIST_FULL
DEDUP

---

5.3 FocusEfficiency

Measures effectiveness of Focus Mode.

Attributes:

symbol
focus_time_minutes
focus_scans
confirm_generated
open_generated
focus_to_open_ratio
api_calls_consumed

Purpose:

detect symbols that waste focus resources.

---

5.4 StrategyPerformance

Measures conversion across the signal lifecycle.

Metrics:

PRE rate
PRE → CONFIRM conversion
CONFIRM → OPEN conversion
OPEN → WIN rate

---

5.5 GateImpact

Evaluates strategy gates.

Attributes:

gate_name
reject_count
reject_percentage
symbol_distribution
average_score_rejected

Purpose:

identify overly restrictive gates.

---

6. SYMBOL HEALTH ANALYSIS

The Intelligence Layer continuously evaluates each symbol.

Analysis includes:

signal frequency
signal quality
reject patterns
focus efficiency
resource cost

Symbols may be classified as:

STRONG
NEUTRAL
WEAK

Weak symbols may be removed from the scan universe.

---

7. FOCUS MODE ANALYSIS

Focus Mode diagnostics are critical for resource management.

The Intelligence Layer monitors:

focus duration
focus signal yield
focus API consumption
focus deadlocks
focus waste

Key metric:

OPEN_NOW per focus minute

Symbols with poor focus efficiency should not be prioritized.

---

8. STRATEGY RESEARCH CAPABILITIES

The Intelligence Layer supports strategy research.

Research questions include:

Which symbols produce the most PRE signals?
Which gates kill the most signals?
Which buffer mode performs best?
Which sessions produce the best results?
Which signals stall at PRE?

Outputs:

- research reports
- statistical dashboards
- strategy recommendations

---

9. ADMIN INTELLIGENCE PANEL

The Intelligence Layer is exposed through the Admin Panel.

Admin navigation tree:

/admin
  Intelligence
      Diagnostics
      Reject Reasons
      Symbol Health
      Focus Efficiency
      Strategy Insights
      Optimizer
      Research Reports

Each section presents aggregated intelligence data.

---

10. STRATEGY OPTIMIZATION WORKFLOW

The Intelligence Layer supports controlled strategy refinement.

Workflow:

Runtime data collection
        ↓
Intelligence aggregation
        ↓
Operator analysis
        ↓
Parameter adjustment
        ↓
Monitoring and validation

All parameter changes must follow the governance process defined in:

GOVERNANCE_AND_CHANGE_CONTROL.md

---

11. SAFETY RULES

The Intelligence Layer must obey strict safety constraints.

It must never:

execute trades
publish signals
modify parameters automatically
block runtime execution
interfere with engine tick cycle

Its function is strictly:

observe
analyze
recommend

---

12. DESIGN PRINCIPLES

The Intelligence Layer follows these principles:

1. Separation from runtime execution
2. Deterministic signal generation remains untouched
3. Data-driven strategy refinement
4. Operator-controlled optimization
5. Full observability of the signal lifecycle
6. Evidence-based trading decisions

---

13. FUTURE EXTENSIONS

Potential extensions include:

automated anomaly detection
symbol clustering
adaptive scanning allocation
machine learning assisted research
long-term regime analysis

These features must remain non-intrusive to runtime execution.

---

END OF DOCUMENT