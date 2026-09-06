# R-021 — Event Schema Migration Cleanup

## Baseline and migration boundary

Date: 2026-09-06
Issue: #148
Parent remediation: #97
Base main: `ecc09c4c25ec687c3d2ea1863cf4388c67360c88`
Status: IN PROGRESS — AUDIT / IMPLEMENTATION BOUNDARY MATERIALIZED

## 1. Canonical authority

The active Master Index declares `EVENT_SCHEMA_SPEC_v3.0.0.md` Active Canonical and the runtime/event migration must therefore treat v3 semantics as primary authority.

The active Event Schema v3 specification states that:
- `signal_execution_result`, `route_publish_result`, and `signal_stage_visible` are primary v3 truth families for their respective domains;
- historical `signal_emitted` remains valid only under its original historical schema meaning;
- generic legacy event names including `decision`, `signal_event`, `tier_publish`, and `tier_reset` may exist only in explicit migration adapters and are not primary v3 names;
- historical evidence must not be silently reinterpreted.

The stale header inside the active `EVENT_SCHEMA_SPEC_v3.0.0.md` still says proposed/not active. That is a real documentation drift but belongs to R-024 canonical header/status cleanup. R-021 uses the Master Index and activation state as authority and does not silently rewrite that separate governance defect.

## 2. Confirmed runtime state on current main

### 2.1 Observability logger

`send/core/observability_logger.py` currently:
- defaults `EVENT_SCHEMA_VERSION` to `3.0.0`;
- loads `send/schema/event_schema.json` as runtime implementation schema;
- allows normal `build_event()` and shorthand normalization to construct any event family registered by the runtime schema;
- validates an envelope against the schema-declared allowed schema versions.

This means the write API currently has no explicit boundary between primary v3 construction and legacy compatibility construction.

### 2.2 Runtime schema

`send/schema/event_schema.json` currently:
- identifies itself as schema `3.0.0`;
- accepts envelope `schema_version` values `2.0.0` and `3.0.0`;
- registers primary v3 families such as `decision_evaluated`, `decision_promoted`, `decision_rejected`, `fsm_transition`, `signal_execution_result`, `route_publish_attempt`, `route_publish_result`, `route_reset`, `signal_stage_visible`, and outcome/admin families;
- also registers legacy compatibility families including `decision`, `signal_event`, `tier_publish`, and `tier_reset` as ordinary constructible event types.

The schema therefore mixes write authority and historical compatibility in one undifferentiated surface.

### 2.3 Live strategy/distribution path

`send/core/signal_engine.py` imports `core.distribution_router_v3 as distribution_router`, so the live Signal Engine is already routed through the v3 distribution implementation.

`send/core/distribution_router_v3.py` correctly emits primary v3 events including:
- `route_publish_attempt`;
- `route_publish_result`;
- `route_reset`;
- `route_state_changed`;
- `route_mapping_invalid`;
- `signal_stage_visible`.

However, the same live v3 router intentionally also writes legacy adapter events:
- every route result is additionally passed through `_legacy_publish_adapter()` -> legacy `_log_tier_publish()` -> `tier_publish`;
- daily reset writes primary `route_reset` events and then additionally constructs/writes a `tier_reset` adapter.

This is the main confirmed R-021 re-entry path: new live v3 activity creates fresh legacy event records instead of limiting legacy semantics to historical compatibility reads.

### 2.4 Live distribution scheduler

`send/runtime/system_boot.py` starts `runtime.distribution_scheduler.scheduler_loop` as a live worker.

`send/runtime/distribution_scheduler.py` currently:
- imports the legacy `core.distribution_router`;
- calls `distribution_router.reset_daily_counters()`;
- additionally emits a raw shorthand `tier_reset` event.

The legacy router reset path itself also writes `tier_reset`, so this worker is another current producer of fresh legacy distribution events.

### 2.5 Legacy consumers that must not be broken blindly

Repository consumers still exist for historical/legacy evidence. Confirmed examples include:
- `send/core/analytics_engine.py` distribution summary logic that reads `tier_publish`;
- `send/intelligence/research_engine.py` signal-funnel logic that reads `signal_event`;
- older audit/report surfaces and tests that intentionally validate migration-era evidence;
- R-018 Strategy Auditor compatibility handling, which already distinguishes v3 primary decision events from legacy-compatible inputs.

These are read-side compatibility concerns. They do not justify continued legacy writes from the new live v3 path.

## 3. R-021 governing distinction

R-021 will separate two concerns that are currently conflated:

### Primary write authority

New runtime evidence created by current code must use v3 primary event families and v3 semantics.

### Historical read compatibility

Existing v2/legacy records remain readable under their original meanings through explicit bounded compatibility paths. Historical records must never be relabeled or silently upgraded to v3 truth.

## 4. Implementation sequence

### Phase A — stop fresh legacy distribution writes

1. Remove live `tier_publish` adapter emission from `distribution_router_v3` after confirming all required v3 `route_publish_result` fields and consumers are preserved.
2. Remove live `tier_reset` adapter emission from `distribution_router_v3` while preserving primary `route_reset` evidence.
3. Move the active distribution scheduler away from the legacy reset/write path so it cannot create new `tier_reset` records.
4. Preserve distribution limits, route state, reset timing, dedup, publication evidence, Telegram behavior, and outcome registration exactly.

### Phase B — separate write validation from legacy read validation

1. Introduce an explicit primary-v3 construction boundary in `observability_logger`.
2. Prevent ordinary new-runtime `build_event()` / shorthand logging paths from constructing legacy-only families.
3. Keep a narrow explicit compatibility validator/adapter for historical evidence where still required.
4. Do not mutate original schema_version or event_type while reading historical records.

### Phase C — migrate consumers without erasing history

1. Update analytics/research consumers to prefer v3 primary families.
2. Keep bounded fallback parsing for historical `tier_publish`, `signal_event`, `decision`, and other explicitly supported legacy records.
3. Ensure a single physical event is never double-counted merely because both primary and legacy representations existed historically.
4. Document authoritative precedence when both formats are present.

### Phase D — runtime schema boundary

1. Keep runtime schema definitions sufficient to validate historical evidence through the explicit compatibility path.
2. Make v3 the only ordinary live write schema.
3. Prevent new code from using v2 schema_version or legacy-only event families through the primary builder.

## 5. Regression requirements

R-021 tests must prove at minimum:
- live distribution writes v3 primary route events without fresh `tier_publish`/`tier_reset` duplication;
- live scheduler cannot reintroduce legacy reset writes;
- ordinary primary event construction rejects legacy-only event families;
- historical legacy validation/reading remains available through an explicit compatibility path;
- v2 history is not silently rewritten to v3;
- analytics/research can consume v3 primary evidence and historical legacy evidence without double counting;
- R-018 Strategy Auditor behavior remains correct;
- provider selector regression passes;
- Telegram Admin regression passes;
- full repository suite passes.

## 6. Non-goals / safety boundary

R-021 does not change:
- strategy mathematics or thresholds;
- Trade Physics formulas;
- Finnhub-exclusive provider policy or EUR/USD scope;
- 2-second evaluation cadence;
- FSM trading policy;
- distribution entitlements or daily limits;
- Telegram authorization/roles;
- outcome truth definitions;
- broker execution state.

Broker execution remains disabled.

## 7. Current conclusion

R-021 is required. The repository already has a v3 primary event model, but its runtime compatibility layer is still bidirectional: historical compatibility is allowed to generate new legacy writes. The remediation target is one-way compatibility — v3-only primary writes, bounded legacy reads, preserved historical meaning, and no silent schema reinterpretation.
