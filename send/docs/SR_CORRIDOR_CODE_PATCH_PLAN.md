# SR_CORRIDOR_CODE_PATCH_PLAN

Status: Satellite / Non-Canonical Reference
Canonical Position: Supporting document only; does not define active canonical truth.
Primary Active Canon: Refer to active canonical documents under /opt/binarybot/docs/canonical/active/

---

# SR_CORRIDOR_CODE_PATCH_PLAN.md

## Status
Canonical Patch Plan

## Purpose

This document defines the exact implementation plan for upgrading the current
binary SR gate into the new SR Corridor Detection Engine.

This step does NOT apply code changes.
It defines:

- what already exists
- what must be added
- what must be replaced
- what telemetry must be exposed
- how PRE / CONFIRM / OPEN_NOW must evolve

This document is based on the runtime/code audit performed in STEP 103.2.

---

## 1. Confirmed Existing SR Logic

Current implementation already exists in:

/opt/binarybot/core/strategy_v2.py

Confirmed existing functions / variables:

_swing_points_from_m5(...)
_nearest_support_resistance(...)
_available_space(...)
supports
resistances
nearest_support
nearest_resistance
available_space
required_space
sr_ok
SR_SPACE_INSUFFICIENT

Confirmed current rule:

required_space = buffer_price * sr_required_multiplier
sr_ok = available_space >= required_space

Confirmed current runtime telemetry fields:

nearest_support
nearest_resistance
available_space
required_space
buffer_price
atr_m5

---

## 2. Problem With Current Model

The current SR model is only a binary gate:

PASS / FAIL

This is insufficient because it does not model:

corridor quality
corridor class
market friction
SR density
expiry reachability inside corridor
structural tradability score

It blocks the strategy too early and prevents staged intelligence.

---

## 3. Strategic Upgrade Target

The target model is:

Binary SR Gate
→ SR Corridor Evaluation Layer

This new layer must classify the path ahead of price rather than only rejecting it.

---

## 4. New Canonical Variables To Introduce

The following variables must be added to runtime logic:

### 4.1 corridor_distance

BUY  -> nearest_resistance - entry_price
SELL -> entry_price - nearest_support

This is effectively the structural free space in trade direction.

---

### 4.2 free_path_ratio

free_path_ratio = corridor_distance / buffer_price

Purpose:

normalize corridor space against required trade movement

---

### 4.3 expiry_reach_ratio

expiry_reach_ratio = (price_speed * expiry_minutes) / buffer_price

Purpose:

measure if the market can realistically travel the needed distance in time

---

### 4.4 volatility_support_ratio

volatility_support_ratio = atr_reference / buffer_price

Purpose:

measure if volatility can support the planned move

---

### 4.5 corridor_quality_score

corridor_quality_score =
    free_path_ratio
    * expiry_reach_ratio
    * volatility_support_ratio

Purpose:

structural tradability score

---

### 4.6 sr_density

Initial implementation may approximate:

sr_density = number of relevant SR levels inside projected trade path

Projected trade path may be:

entry ± max(buffer_price, atr_reference, price_speed * expiry_minutes)

Purpose:

estimate how crowded the path ahead is

---

### 4.7 market_friction

Canonical approximation:

market_friction = sr_density / max(free_path_ratio, 0.01)

Purpose:

penalize corridors with clustered obstacles

---

### 4.8 corridor_quality_adjusted

corridor_quality_adjusted =
    corridor_quality_score / (1 + market_friction)

Purpose:

final corridor tradability score

---

### 4.9 corridor_class

The engine must classify the corridor as:

BLOCKED
TIGHT
TRADABLE
OPEN_FIELD

Canonical thresholds:

free_path_ratio < 1.0         -> BLOCKED
1.0 <= free_path_ratio < 1.3  -> TIGHT
1.3 <= free_path_ratio < 2.0  -> TRADABLE
free_path_ratio >= 2.0        -> OPEN_FIELD

---

## 5. Existing Variables To Preserve

The following existing variables must remain preserved for compatibility:

nearest_support
nearest_resistance
available_space
required_space
buffer_price
atr_m5
price
expiry_minutes
speed_price_per_min
score_struct
sr_gate

Reason:

backward compatibility
admin/debug views
stable observability
migration safety

---

## 6. Existing Rule To Replace

Current rule:

sr_ok = available_space >= required_space

Current rejection reason:

SR_SPACE_INSUFFICIENT

This must evolve into corridor evaluation.

Replacement logic must preserve a hard reject only for:

free_path_ratio < 1.0

Meaning:

obstacle sits inside required move

---

## 7. New Staged Decision Behavior

### 7.1 PRE

PRE must no longer be hard-blocked merely because corridor is weak.

PRE may be allowed if:

corridor_class in {TIGHT, TRADABLE, OPEN_FIELD}

and other score logic remains acceptable.

Meaning:

PRE becomes observational / opportunity staging
PRE is allowed even when structure is not perfect

---

### 7.2 CONFIRM

CONFIRM must require stronger corridor validation.

Suggested condition:

corridor_class in {TRADABLE, OPEN_FIELD}
OR
(corridor_class == TIGHT and corridor_quality_adjusted >= tighter_confirm_threshold)

Meaning:

CONFIRM is structure-sensitive

---

### 7.3 OPEN_NOW

OPEN_NOW must require:

corridor_class != BLOCKED
expiry_reach_ratio >= 1.0
corridor_quality_adjusted >= corridor_open_threshold

Meaning:

execution only in structurally reachable corridors

---

## 8. Patch Scope In Code

Primary file

/opt/binarybot/core/strategy_v2.py

This file must receive the main patch.

Secondary file

/opt/binarybot/core/signal_engine.py

This file must be updated only if needed to surface the new telemetry
into runtime outputs / downstream logs / dashboards.

Optional admin/UI files

/opt/binarybot/core/admin_views.py

Only if we decide to expose corridor telemetry in admin panels.

---

## 9. Exact Patch Zones In strategy_v2.py

Based on audit, the critical zones are:

Zone A — helper layer

Near existing helpers:

_swing_points_from_m5
_nearest_support_resistance
_available_space

New helpers may be introduced here:

_count_sr_levels_in_path(...)
_classify_corridor(...)
_compute_corridor_metrics(...)

---

Zone B — decision runtime before gates

Current existing block:

supports, resistances = _swing_points_from_m5(...)
nearest_sup, nearest_res = _nearest_support_resistance(...)
avail_space = _available_space(...)
sr_ok = (avail_space >= required_space)

This is the main replacement zone.

Here we must compute:

corridor_distance
free_path_ratio
expiry_reach_ratio
volatility_support_ratio
sr_density
market_friction
corridor_quality_score
corridor_quality_adjusted
corridor_class

---

Zone C — gates dictionary

Current gate payload:

available_space
required_space
nearest_support
nearest_resistance

This must be extended to include:

corridor_distance
free_path_ratio
expiry_reach_ratio
volatility_support_ratio
corridor_quality_score
market_friction
corridor_quality_adjusted
corridor_class
sr_density

---

Zone D — critical gate logic

Current logic:

critical_ok = sr_ok and spike_ok and feas_ok

This must evolve so that PRE is not hard-killed by weak corridor.

We must separate:

execution corridor validity
vs
early opportunity visibility

---

## 10. Migration Strategy

The migration must happen in two safe phases.

Phase 1 — Additive telemetry migration

Add new corridor metrics while preserving old fields:

available_space
required_space
sr_ok

No destructive removal yet.

Goal:

observe behavior safely
validate runtime telemetry

---

Phase 2 — Decision behavior migration

Switch staged logic from binary SR gate to corridor-class-based logic.

Goal:

PRE / CONFIRM / OPEN_NOW become structure-aware

---

## 11. Backward Compatibility Rules

During migration:

keep available_space
keep required_space
keep sr_gate
keep SR_SPACE_INSUFFICIENT for hard BLOCKED cases if needed
add new reasons only as extension, not replacement, during first rollout

Suggested extended reasons:

SR_CORRIDOR_BLOCKED
SR_CORRIDOR_TIGHT
SR_CORRIDOR_WEAK_CONFIRM
SR_CORRIDOR_EXPIRY_UNREACHABLE

---

## 12. New Runtime Telemetry Requirements

The following must appear in runtime output:

corridor_distance
free_path_ratio
expiry_reach_ratio
volatility_support_ratio
corridor_quality_score
market_friction
corridor_quality_adjusted
corridor_class
sr_density

These fields must appear in:

decision debug payload
sr_gate details payload
downstream audit rows

---

## 13. New Dataset Requirements

Future AI dataset rows must include:

symbol
timestamp
direction
entry_price
buffer_price
corridor_distance
free_path_ratio
expiry_reach_ratio
volatility_support_ratio
corridor_quality_score
market_friction
corridor_quality_adjusted
corridor_class
sr_density
trade_result

---

## 14. Immediate Expected Benefit

After implementation, the strategy will stop treating SR as only a yes/no wall.

Instead it will understand:

blocked path
tight path
tradable path
open field

This is expected to:

reduce false rejects
allow PRE visibility for near-valid setups
improve CONFIRM quality
improve OPEN_NOW structural realism
feed better telemetry to AI calibration later

---

## 15. Step-by-Step Execution Plan

STEP 103.4

Implement additive corridor telemetry in strategy_v2.py

STEP 103.5

Run runtime audit on new corridor metrics

STEP 103.6

Switch PRE / CONFIRM / OPEN_NOW logic to corridor-class staged behavior

STEP 103.7

Run post-patch signal flow audit

---

## 16. Summary

The project already contains a primitive SR gate.

This patch plan upgrades it into an SR Corridor Detection Engine by:

preserving existing SR infrastructure
adding corridor metrics
adding corridor classification
adding friction logic
changing staged decision behavior
supporting future TPS / AI integration

This is the canonical bridge between the current signal engine and the future
market-structure-aware intelligence engine.

## Non-Canonical Usage Note

This document is retained as a supporting/satellite reference only. It must not be treated as active canonical truth. Where conflict exists, active canonical documents in /opt/binarybot/docs/canonical/active/ take precedence.
