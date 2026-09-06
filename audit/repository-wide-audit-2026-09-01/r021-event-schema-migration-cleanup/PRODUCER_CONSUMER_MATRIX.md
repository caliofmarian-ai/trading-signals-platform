# R-021 — Producer / Consumer Migration Matrix

Base main: `ecc09c4c25ec687c3d2ea1863cf4388c67360c88`
Issue: #148
Draft PR: #149

## Purpose

This matrix separates current event producers from historical/read-side consumers so R-021 can remove fresh legacy writes without deleting or silently reinterpreting existing evidence.

| Event family | Canonical role in v3 | Confirmed current producer / write surface | Confirmed consumer / read surface | R-021 treatment |
|---|---|---|---|---|
| `decision_evaluated` | Primary strategy decision truth | `send/core/signal_engine.py` | Strategy Auditor / analytics paths | KEEP primary v3 |
| `decision_promoted` / `decision_rejected` / `decision_no_signal` | Primary decision lifecycle truth | `send/core/signal_engine.py` and governed decision logging | Strategy Auditor / diagnostics | KEEP primary v3 |
| `signal_execution_result` | Primary Signal Engine execution truth | `send/core/signal_engine.py` | observability / execution analytics | KEEP primary v3 |
| `route_publish_attempt` | Primary route attempt truth | `send/core/distribution_router_v3.py` | v3 distribution tests / future analytics | KEEP primary v3 |
| `route_publish_result` | Primary route publication truth | `send/core/distribution_router_v3.py` | v3 distribution tests, objective telemetry publication evidence | KEEP primary v3 and migrate analytics to prefer it |
| `route_reset` | Primary route reset truth | `send/core/distribution_router_v3.py` | route-state observability | KEEP primary v3 |
| `signal_stage_visible` | Primary external visibility truth | `send/core/distribution_router_v3.py` | objective telemetry / execution proof | KEEP primary v3 |
| `tier_publish` | Legacy migration adapter only | Fresh writes currently produced by `distribution_router_v3._legacy_publish_adapter()` through legacy `_log_tier_publish()`; legacy router can also produce it | `send/core/analytics_engine.py` and older audit/test readers | STOP new v3-router writes; retain bounded historical read fallback until consumers migrate |
| `tier_reset` | Legacy migration adapter only | Fresh writes currently produced by v3 reset adapter; legacy reset owner can produce it; scheduler previously produced an additional duplicate shorthand record | older tests/docs; legacy reset evidence | STOP new v3 adapter writes; scheduler duplicate already removed in first R-021 patch; preserve historical read meaning |
| `decision` | Legacy migration adapter only | No current primary producer confirmed in active `signal_engine.py`; remains constructible through generic runtime schema/builder | historical audit/analytics compatibility | Keep read compatibility; later block ordinary new primary construction |
| `signal_event` | Legacy migration adapter only | No current primary producer confirmed in active Signal Engine; runtime schema still exposes it | `send/intelligence/research_engine.py` signal-funnel compatibility and older reports | Migrate consumer to v3 primary evidence with historical fallback; later block ordinary new primary construction |
| `signal_emitted` | History/compatibility only in v3 canon | No current live producer confirmed by repository search | historical docs / superseded evidence | Never recreate as primary v3; preserve historical meaning only |

## Current write-side priorities

1. `distribution_router_v3` dual-write behavior is the highest-confidence fresh legacy re-entry path.
2. `runtime.distribution_scheduler` duplicate `tier_reset` write was a separate live duplicate; R-021 first patch removes that scheduler-owned duplicate while leaving reset ownership unchanged.
3. Generic `observability_logger.build_event()` / shorthand normalization still lacks a primary-v3 vs legacy-compat guard; migration layer introduced by R-021 now provides the explicit classification and guard contract before wiring it into producers.

## Current read-side priorities

1. `analytics_engine` must learn to prefer `route_publish_result` and use `tier_publish` only as historical fallback.
2. `research_engine` must move signal-funnel logic away from fresh `signal_event` dependence while retaining historical fallback.
3. Strategy Auditor compatibility already has explicit v3/legacy normalization from R-018 and must not regress.

## Double-counting rule

During migration, if one logical publication is represented by both a primary v3 `route_publish_result` and a legacy `tier_publish` adapter in the same historical period, analytics must not count both as independent publications. Primary v3 evidence wins when an unambiguous correlation exists; otherwise evidence remains separately classified rather than guessed.

## Historical integrity rule

R-021 does not edit stored JSONL history, change original `schema_version`, relabel legacy `event_type`, or infer missing correlation. Compatibility is read-only interpretation under the event's original identity.
