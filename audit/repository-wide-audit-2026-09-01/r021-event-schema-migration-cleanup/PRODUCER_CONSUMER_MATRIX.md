# R-021 — Producer / Consumer Migration Matrix

Base main: `ecc09c4c25ec687c3d2ea1863cf4388c67360c88`
Issue: #148
PR: #149

## Purpose

This matrix separates current primary writers from historical/read-side compatibility so R-021 can keep v3 as live authority without deleting or silently reinterpreting existing evidence.

| Event family | Canonical role in v3 | Current write surface after R-021 | Current read surface after R-021 | R-021 treatment |
|---|---|---|---|---|
| `decision_evaluated` | Primary strategy decision truth | `send/core/signal_engine.py` | Strategy Auditor / diagnostics | KEEP primary v3 |
| `decision_promoted` / `decision_rejected` / `decision_no_signal` | Primary decision lifecycle truth | governed decision logging | Strategy Auditor / diagnostics | KEEP primary v3 |
| `signal_execution_result` | Primary Signal Engine execution truth | `send/core/signal_engine.py` | Research candidate funnel / execution observability | KEEP primary v3; PRE_DISTRIBUTION candidate evidence is Research primary |
| `route_publish_attempt` | Primary route attempt truth | live primary distribution boundary | distribution observability | KEEP primary v3 |
| `route_publish_result` | Primary route publication truth | live primary distribution boundary | analytics / objective publication evidence | KEEP primary v3; analytics prefers it |
| `route_reset` | Primary route reset truth | live primary distribution boundary and scheduler reset path | route-state observability | KEEP primary v3 |
| `signal_stage_visible` | Primary external visibility truth | live primary distribution boundary | objective telemetry / execution proof | KEEP primary v3 |
| `tier_publish` | Legacy migration adapter only | Not written by the active primary-v3 distribution boundary; legacy modules remain compatibility-only | bounded analytics fallback and historical tests | NO new primary write; read fallback only |
| `tier_reset` | Legacy migration adapter only | Not written by the active primary-v3 distribution boundary or live scheduler | bounded historical validation/tests | NO new primary write; read compatibility only |
| `decision` | Legacy migration adapter only | No current primary producer confirmed | historical audit compatibility | Never treat as primary v3; primary builder rejects it |
| `signal_event` | Legacy migration adapter only | No current primary producer confirmed | bounded Research fallback / older reports | Never treat as primary v3; matching v3 candidate suppresses fallback duplicate |
| `signal_emitted` | History/compatibility only | No current live producer confirmed | historical docs / superseded evidence | Never recreate as primary v3 |

## Write-side authority after R-021

1. `event_schema_migration.build_primary_v3_event()` is the explicit new primary construction surface and always materializes `schema_version=3.0.0`.
2. `require_primary_v3_event_type()` rejects `decision`, `signal_event`, `tier_publish`, and `tier_reset` as primary event families.
3. `distribution_router_primary_v3` retains the established v3 routing mechanics but suppresses the two migration-era distribution adapter writes.
4. `runtime.engine_loop` binds Signal Engine distribution to the primary-v3 boundary before live execution.
5. `runtime.distribution_scheduler` uses the same primary-v3 boundary for daily reset.
6. An AST regression guard fails CI if active runtime entry points reintroduce literal legacy event construction through `build_event`, `_log_event`, or shorthand `log_event`.

The lower-level `observability_logger` and runtime schema remain able to validate historical canonical evidence. That read/validation capability is not primary write authority.

## Read-side authority after R-021

1. `analytics_engine` prefers `route_publish_result`; matching `tier_publish` is suppressed as a migration duplicate, while unmatched history remains explicit fallback.
2. `research_engine` prefers PRE_DISTRIBUTION `signal_execution_result` candidate evidence; matching `(signal_id, stage)` `signal_event` rows are suppressed, while unmatched history remains explicit fallback.
3. R-018 Strategy Auditor compatibility remains intact and must not reinterpret legacy records as primary v3 truth.

## Double-counting rules

For distribution, primary `route_publish_result` wins when the observable publication fingerprint unambiguously matches a legacy representation.

For Research candidate lifecycle evidence, primary PRE_DISTRIBUTION `signal_execution_result` wins when `(signal_id, stage)` matches a legacy `signal_event` record.

If correlation is not unambiguous, evidence remains separately classified rather than guessed.

## Historical integrity rule

R-021 does not edit stored JSONL history, change an original `schema_version`, relabel legacy `event_type`, fabricate missing correlation, or promote legacy evidence into primary v3 truth. Compatibility is one-way: historical evidence remains readable, but current primary runtime writes remain v3-only.
