# INTELLIGENCE_FILES_AND_MODULE_MAP.md
BinaryBot / DROPi Signals

---

## 1. PURPOSE

This document defines the canonical **Intelligence Files and Module Map**.

Its purpose is to specify:

- which Intelligence Layer modules must exist
- which existing runtime modules feed intelligence data
- which snapshot files must exist
- which admin views consume intelligence snapshots
- which modules must remain untouched during early implementation steps

This document translates the Intelligence Layer architecture and the Intelligence Data Pipeline into a concrete module map for implementation.

This document does not itself define strategy logic, FSM rules, routing rules, or outcome rules.

It defines where intelligence responsibilities live in code.

---

## 2. CANONICAL DESIGN PRINCIPLE

The Intelligence Layer must remain separated from the runtime critical path.

Therefore:

- runtime modules may emit events
- intelligence modules may collect and aggregate them
- admin panel may render intelligence snapshots
- intelligence modules must not block runtime signal generation

The Intelligence Layer is:

```text
observe
→ aggregate
→ snapshot
→ render
→ recommend

It is not:

generate signal
→ alter runtime
→ auto-modify strategy```


---

## 3. NEW CANONICAL INTELLIGENCE MODULES

The following modules are canonical implementation targets for the Intelligence Layer.

### 3.1 core/intelligence_pipeline.py

Purpose:

central intake point for intelligence data flow

receives normalized runtime intelligence events

routes them to appropriate aggregators

coordinates snapshot refresh scheduling

acts as the orchestration layer of intelligence processing


Responsibilities:

ingest_event(...)

ingest_batch(...)

normalize_event(...)

dispatch_to_aggregators(...)

refresh_snapshots_if_needed(...)


This module must remain lightweight and orchestration-focused.

It must not contain heavy analytical logic.


---

### 3.2 core/intelligence_aggregators.py

Purpose:

transforms raw events into analytical aggregates


Responsibilities:

aggregate_symbol_health(...)

aggregate_reject_stats(...)

aggregate_focus_efficiency(...)

aggregate_strategy_performance(...)

aggregate_runtime_overview(...)

aggregate_optimizer_candidates(...)


Inputs:

raw runtime event logs

current state snapshots

optional supporting state files


Outputs:

intelligence snapshot dictionaries ready for persistence


This module is the main analytical computation layer.


---

### 3.3 core/intelligence_snapshots.py

Purpose:

safe persistence and retrieval of intelligence snapshots


Responsibilities:

load_snapshot(name)

save_snapshot(name, data)

snapshot_path(name)

validate_snapshot_shape(name, data)

atomic writes

fallback-safe reads


Canonical target snapshot names:

intelligence_symbol_health

intelligence_reject_stats

intelligence_focus_efficiency

intelligence_strategy_performance

intelligence_runtime_overview

intelligence_optimizer_candidates


This module must be storage-oriented only.

It must not compute business intelligence itself.


---

### 3.4 core/intelligence_admin_views.py

Purpose:

transforms intelligence snapshots into admin-panel-readable text blocks and Telegram-friendly views


Responsibilities:

render diagnostics

render reject reasons

render symbol health

render focus efficiency

render strategy insights

render optimizer recommendations


Expected functions:

render_intelligence_dashboard(...)

render_runtime_overview(...)

render_reject_stats(...)

render_symbol_health(...)

render_focus_efficiency(...)

render_strategy_performance(...)

render_optimizer_candidates(...)


This module must not perform heavy aggregation.

It must read precomputed snapshots only.


---

## 4. OPTIONAL FUTURE SPLIT MODULES

If the intelligence layer grows, the following module split is canonical-compatible:

core/intelligence_symbol_health.py

core/intelligence_reject_stats.py

core/intelligence_focus_efficiency.py

core/intelligence_strategy_performance.py

core/intelligence_optimizer.py


These are optional refinement modules.

They are not mandatory in the first implementation pass.

The first safe implementation may keep aggregation inside:

core/intelligence_aggregators.py



---

## 5. EXISTING RUNTIME MODULES THAT FEED INTELLIGENCE

The following existing modules remain the runtime sources of truth.

They must not be replaced by intelligence modules.

They may only emit or expose intelligence-relevant events.


---

### 5.1 core/signal_engine.py

Role in intelligence:

source of decision events

source of PRE / CONFIRM / OPEN_NOW / REJECT / NO_SIGNAL data

source of score and gate details


Feeds:

symbol health

reject stats

strategy performance

optimizer candidate detection


Expected emitted intelligence-relevant fields:

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

### 5.2 core/fsm_runtime.py

Role in intelligence:

source of lifecycle transitions

source of focus/watchlist state transitions

source of cooldown and lifecycle progression data


Feeds:

focus efficiency

strategy performance

runtime overview

stalled signal analysis


Expected emitted intelligence-relevant fields:

symbol

previous_state

new_state

signal_id

focus_enter_ts

cooldown_until_ts

watchlist operations



---

### 5.3 core/distribution_router.py

Role in intelligence:

source of routing outcomes

source of publication success/failure

source of dedup and suppression evidence


Feeds:

runtime overview

delivery diagnostics

optimizer confidence validation

signal lifecycle completion analysis


Expected emitted intelligence-relevant fields:

signal_id

symbol

stage

tier

publish_decision

dedup_key

telegram_ok



---

### 5.4 core/outcome_service.py

Role in intelligence:

source of outcome truth / outcome attachment layer

source of post-signal result data


Feeds:

strategy performance

symbol health

optimizer recommendations

research reports


Expected emitted intelligence-relevant fields:

signal_id

symbol

outcome

expiry_ts

feedback_ts



---

### 5.5 runtime/engine_loop.py

Role in intelligence:

runtime tick driver only

does not perform intelligence analytics

may later trigger lightweight intelligence refresh hooks if explicitly designed


This module must remain minimal.


---

## 6. SCAN SCHEDULER RELATION

The Intelligence Layer requires scheduler metrics, but the canonical scan scheduler may not yet exist as a separate module.

### 6.1 Future canonical scheduler module

Target:

core/scan_scheduler.py


Purpose:

separate WIDE_SCAN and FOCUS scheduling

expose scan coverage and budget metrics

feed scheduler intelligence into the intelligence pipeline


### 6.2 Temporary current source

Until core/scan_scheduler.py exists, scheduler-related intelligence signals may originate from:

core/signal_engine.py

runtime/engine_loop.py


### 6.3 Required future scheduler metrics

The intelligence layer must eventually receive:

wide scan coverage

focus scan coverage

symbols scanned this cycle

starved symbols

TeleData/API budget usage

focus-vs-wide allocation ratios


The intelligence layer must be able to detect:

focus replacing wide scan entirely

symbol starvation

resource monopolization by focus symbols



---

## 7. CANONICAL INTELLIGENCE SNAPSHOT FILES

The following snapshot files must exist under state/.

### 7.1 state/intelligence_symbol_health.json

Contains per-symbol intelligence metrics:

PRE count

CONFIRM count

OPEN count

win/loss profile

reject rate

focus efficiency

resource usage estimate



---

### 7.2 state/intelligence_reject_stats.json

Contains reject analytics:

reject reasons by count

reject reasons by percentage

reject reasons by symbol

dominant rejection patterns



---

### 7.3 state/intelligence_focus_efficiency.json

Contains focus diagnostics:

focus duration

focus scan count

focus-to-confirm conversion

focus-to-open conversion

focus API cost

symbols wasting focus resources



---

### 7.4 state/intelligence_strategy_performance.json

Contains strategy-wide metrics:

PRE rate

PRE → CONFIRM conversion

CONFIRM → OPEN conversion

OPEN → OUTCOME conversion

buffer mode performance

time/session segmentation if available later



---

### 7.5 state/intelligence_runtime_overview.json

Contains fast admin summary:

current mode

watchlist size

active symbols count

current focus symbols

scan coverage

top bottlenecks

current runtime health view



---

### 7.6 state/intelligence_optimizer_candidates.json

Contains recommendation candidates only:

threshold tuning candidates

weak symbols

symbols wasting focus

gate over-restriction patterns

candidate configuration review suggestions


This file must never auto-apply changes.


---

## 8. ADMIN PANEL CONSUMERS

The Intelligence branch of the admin panel must consume the snapshot files through dedicated view logic.

Canonical admin tree branch

/admin
  Intelligence
    Diagnostics
    Reject Reasons
    Symbol Health
    Focus Efficiency
    Strategy Insights
    Optimizer
    Research

Canonical snapshot → admin mapping

Diagnostics → intelligence_runtime_overview.json

Reject Reasons → intelligence_reject_stats.json

Symbol Health → intelligence_symbol_health.json

Focus Efficiency → intelligence_focus_efficiency.json

Strategy Insights → intelligence_strategy_performance.json

Optimizer → intelligence_optimizer_candidates.json


Admin handlers must never perform heavy recomputation directly from full raw logs during Telegram callback handling.

They must read precomputed snapshots.


---

## 9. MODULE RESPONSIBILITY BOUNDARIES

Intelligence modules must do:

normalize analytical inputs

aggregate evidence

persist snapshots

render operator-facing intelligence

produce recommendations


Intelligence modules must not do:

emit PRE / CONFIRM / OPEN_NOW

modify watchlist automatically

modify thresholds automatically

alter distribution behavior directly

block runtime execution



---

## 10. MODULES THAT MUST REMAIN UNTOUCHED IN EARLY IMPLEMENTATION

During the first safe implementation stages, the following modules must not be structurally refactored:

core/signal_engine.py

core/fsm_runtime.py

core/distribution_router.py

runtime/engine_loop.py


Reason:

the first intelligence implementation pass should be additive, not invasive.

Only lightweight event emission hooks or integrations may be added later, after snapshot/view scaffolding exists.


---

## 11. SAFE IMPLEMENTATION ORDER

Canonical safe order:

Phase 1

Create:

core/intelligence_pipeline.py

core/intelligence_aggregators.py

core/intelligence_snapshots.py

core/intelligence_admin_views.py


Phase 2

Create empty/default snapshot files:

state/intelligence_symbol_health.json

state/intelligence_reject_stats.json

state/intelligence_focus_efficiency.json

state/intelligence_strategy_performance.json

state/intelligence_runtime_overview.json

state/intelligence_optimizer_candidates.json


Phase 3

Connect admin Intelligence branch to read these snapshots.

Phase 4

Add event ingestion from runtime modules.

Phase 5

Add scheduler metrics once scan scheduler is separated canonically.

This preserves runtime stability.


---

## 12. IMPLEMENTATION OUTCOME

Once this module map is implemented, the Intelligence Layer will have a canonical code structure:

runtime modules
    ↓
intelligence_pipeline.py
    ↓
intelligence_aggregators.py
    ↓
intelligence_snapshots.py
    ↓
intelligence_admin_views.py
    ↓
Admin Intelligence Panel

This is the canonical structure for the first stable intelligence implementation pass.


---

END OF DOCUMENT EOF

---

## MERGE STATUS

merge_status: BOUNDED_CONTENT_MERGED_INTO_ACTIVE_CANON
merge_target_docs:
- MODULE_INTERFACE_SPEC_v2.0.0.md
- STRATEGY_INTELLIGENCE_SYSTEM_v2.0.0.md

merge_note:
This intake document was merged in bounded form into active canon. Intelligence module-map guidance now lives in active interface/intelligence canon.
