
# INTELLIGENCE_DATA_PIPELINE_DEFINITION.md

---

## 1. PURPOSE

This document defines the canonical **Intelligence Data Pipeline**.

Its role is to specify how runtime information is collected, transformed, aggregated, stored, and exposed to the Intelligence Layer inside the Admin Panel.

This document does not redefine:
- signal generation
- FSM rules
- distribution rules
- outcome rules

It defines how their outputs become structured intelligence.

---

## 2. PIPELINE OVERVIEW

The Intelligence Data Pipeline is:

```text
Runtime Event Sources
        ↓
Event Collection
        ↓
Normalization
        ↓
Aggregation
        ↓
Snapshot Storage
        ↓
Admin Intelligence Rendering
        ↓
Operator Review / Strategy Decisions

The pipeline must remain outside the runtime critical path.


---

## 3. EVENT SOURCES

### 3.1 Strategy Decision Events

Source:

signal_engine.py

strategy_v2.py


Examples:

PRE

CONFIRM

OPEN_NOW

REJECT

NO_SIGNAL


Core fields:

symbol

decision_kind

signal_id

score_total

gates

buffer_mode

expiry_minutes

candle_ts

debug



---

### 3.2 FSM Lifecycle Events

Source:

fsm_runtime.py


Examples:

entered watchlist

transitioned to confirm

transitioned to live

cooldown started

cooldown ended

removed from watchlist


Core fields:

symbol

previous_state

new_state

signal_id

timestamp

focus_enter_ts

cooldown_until_ts



---

### 3.3 Scan Scheduler Events

Source:

scan_scheduler.py (canonical target module)

temporary current source may be signal_engine.py / engine_loop.py


Examples:

wide scan cycle

focus scan cycle

symbols scanned

budget usage

skipped symbols

starved symbols


Core fields:

mode

symbols_scanned

focus_symbols

active_symbols

cycle_ts

teledata_calls_used

budget_remaining



---

### 3.4 Distribution Events

Source:

distribution_router.py


Examples:

published

duplicate_suppressed

tier_skipped

silent_tier

counter_increment


Core fields:

signal_id

symbol

stage

tier

publish_decision

dedup_key

telegram_ok



---

### 3.5 Outcome Events

Source:

outcome_service.py


Examples:

WIN

LOSS

EXPIRED

FEEDBACK_REGISTERED


Core fields:

signal_id

symbol

outcome

expiry_ts

feedback_ts



---

## 4. NORMALIZATION LAYER

All intelligence inputs must be normalized into a common analytical schema.

### 4.1 Canonical Intelligence Event

{
  "event_family": "decision|fsm|scan|distribution|outcome",
  "event_type": "string",
  "symbol": "string|null",
  "signal_id": "string|null",
  "stage": "PRE|CONFIRM|OPEN_NOW|null",
  "ts": 0,
  "payload": {}
}

This schema is analytical only.
It must not replace runtime event schemas.


---

## 5. STORAGE LAYER

The Intelligence Layer must use two storage forms:

### 5.1 Raw event logs

Purpose:

traceability

post-mortem analysis

audit


Examples:

engine_events.jsonl

fsm_events.jsonl

distribution_events.jsonl

outcome_events.jsonl


### 5.2 Aggregated intelligence snapshots

Purpose:

fast admin rendering

trend analysis

diagnostics


Canonical snapshot files:

state/intelligence_symbol_health.json
state/intelligence_reject_stats.json
state/intelligence_focus_efficiency.json
state/intelligence_strategy_performance.json
state/intelligence_runtime_overview.json
state/intelligence_optimizer_candidates.json

Snapshots must be derived from raw logs, never treated as source of truth.


---

## 6. AGGREGATION LAYER

The aggregation layer converts raw events into intelligence objects.

### 6.1 Symbol Health Aggregator

Output:

PRE count

CONFIRM count

OPEN count

WIN rate

reject rate

focus efficiency

scan cost


Target file:

state/intelligence_symbol_health.json



---

### 6.2 Reject Reason Aggregator

Output:

reject reasons by count

reject reasons by symbol

reject reasons by percentage


Target file:

state/intelligence_reject_stats.json



---

### 6.3 Focus Efficiency Aggregator

Output:

focus time

focus scans

focus API consumption

confirm/open conversion in focus


Target file:

state/intelligence_focus_efficiency.json



---

### 6.4 Strategy Performance Aggregator

Output:

PRE rate

PRE → CONFIRM conversion

CONFIRM → OPEN conversion

OPEN → outcome conversion

buffer performance

session performance


Target file:

state/intelligence_strategy_performance.json



---

### 6.5 Runtime Overview Aggregator

Output:

current mode

active symbols count

watchlist size

scan coverage

starved symbols

top bottlenecks


Target file:

state/intelligence_runtime_overview.json



---

### 6.6 Optimizer Candidate Aggregator

Output:

possible threshold tuning candidates

possible weak symbols

possible focus waste symbols

possible gate over-restriction patterns


Target file:

state/intelligence_optimizer_candidates.json


This file contains recommendations only, never auto-applied changes.


---

## 7. UPDATE STRATEGY

The Intelligence Pipeline must support two refresh modes.

### 7.1 Tick-safe lightweight updates

append runtime logs

optionally update counters

no heavy computation


### 7.2 Batch aggregation updates

periodic aggregation

full metric recomputation

dashboard snapshot regeneration


Recommended model:

runtime logs written continuously

intelligence snapshots recalculated on interval or admin-triggered refresh



---

## 8. ADMIN PANEL CONNECTION

The Admin Intelligence branch must read only the aggregated snapshot files.

/admin
  Intelligence
    Diagnostics
    Reject Reasons
    Symbol Health
    Focus Efficiency
    Strategy Insights
    Optimizer
    Research

Mapping:

Diagnostics → intelligence_runtime_overview.json

Reject Reasons → intelligence_reject_stats.json

Symbol Health → intelligence_symbol_health.json

Focus Efficiency → intelligence_focus_efficiency.json

Strategy Insights → intelligence_strategy_performance.json

Optimizer → intelligence_optimizer_candidates.json


The admin panel must not compute heavy analytics directly in Telegram request handlers.


---

## 9. PERFORMANCE RULES

The Intelligence Data Pipeline must obey:

1. No heavy analytics inside engine tick


2. No blocking of signal generation


3. No large file scans during every Telegram callback


4. Aggregates must be precomputed for fast rendering


5. Raw logs remain canonical evidence




---

## 10. SAFETY RULES

The pipeline must never:

change strategy automatically

modify active symbols automatically

alter watchlist state automatically

suppress runtime signals

introduce runtime instability


Intelligence is read/analyze/recommend only.


---

## 11. FUTURE IMPLEMENTATION TARGETS

Canonical implementation targets:

core/intelligence_pipeline.py
core/intelligence_aggregators.py
core/intelligence_snapshots.py
core/intelligence_admin_views.py

Optional future split:

core/intelligence_symbol_health.py
core/intelligence_reject_stats.py
core/intelligence_focus_efficiency.py
core/intelligence_optimizer.py


---

## 12. RELATION TO SCAN SCHEDULER

The Intelligence Data Pipeline must receive scheduler metrics from:

wide scan coverage

focus scan coverage

budget allocation

starved symbols


This is required because the canonical architecture expects:

WIDE_SCAN scheduler

FOCUS scheduler and analytical visibility over both.


The intelligence layer must be able to detect when focus incorrectly replaces wide scan entirely.


---

## 13. IMPLEMENTATION ORDER

Recommended safe order:

1. Define canonical pipeline


2. Create snapshot schemas


3. Create aggregators


4. Expose snapshots in admin panel


5. Refactor scan scheduler


6. Feed scheduler metrics into intelligence



This preserves runtime stability and avoids mixing analytics with critical execution code.


---

END OF DOCUMENT