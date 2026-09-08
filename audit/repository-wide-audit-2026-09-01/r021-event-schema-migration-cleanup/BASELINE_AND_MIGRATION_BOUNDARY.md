# R-021 — Event Schema Migration Cleanup

## Baseline and implemented migration boundary

Date: 2026-09-06
Issue: #148
PR: #149
Parent remediation: #97
Base main: `ecc09c4c25ec687c3d2ea1863cf4388c67360c88`
Status: IMPLEMENTATION MATERIALIZED — FINAL VALIDATION REQUIRED

## 1. Canonical authority

The active Master Index declares `EVENT_SCHEMA_SPEC_v3.0.0.md` Active Canonical. Runtime/event migration therefore treats v3 semantics as primary authority.

The active Event Schema v3 authority establishes that:
- `signal_execution_result`, `route_publish_result`, `route_reset`, and `signal_stage_visible` are primary v3 truth families for their respective domains;
- historical `signal_emitted` remains valid only under its original historical schema meaning;
- generic legacy names including `decision`, `signal_event`, `tier_publish`, and `tier_reset` are migration-adapter-only and are not primary v3 names;
- historical evidence must not be silently reinterpreted.

The stale lower-level header inside the active Event Schema specification remains an R-024 documentation-governance defect. R-021 does not silently fold that separate cleanup into this remediation.

## 2. Baseline drift confirmed on R-021 base main

### 2.1 Shared observability/schema surface

At the audited base:
- `send/core/observability_logger.py` defaulted `EVENT_SCHEMA_VERSION` to `3.0.0`;
- `send/schema/event_schema.json` accepted both `2.0.0` and `3.0.0` envelopes so historical evidence remained validatable;
- the same schema registered both primary v3 families and legacy compatibility families;
- the low-level logger/builder therefore served both current construction and historical compatibility plumbing.

Deleting v2/legacy definitions from that shared validator would have broken historical evidence. R-021 therefore separates **primary write authority** from **historical validation authority** instead of rewriting history.

### 2.2 Distribution dual-write

The base `distribution_router_v3` emitted primary v3 route events but also emitted migration-era `tier_publish` and `tier_reset` adapters. The live distribution scheduler additionally used the legacy reset path and wrote another shorthand `tier_reset`.

This was the highest-confidence live legacy re-entry path.

### 2.3 Historical consumers

Confirmed compatibility consumers included:
- `send/core/analytics_engine.py`, which read `tier_publish` distribution evidence;
- `send/intelligence/research_engine.py`, which read `signal_event` lifecycle evidence;
- older audit/test readers;
- the R-018 Strategy Auditor compatibility layer.

These historical readers did not justify continued legacy writes from the current live path.

## 3. Implemented governing distinction

### Primary v3 write authority

`send/core/event_schema_migration.py` now provides the explicit primary construction contract:
- `PRIMARY_SCHEMA_VERSION = "3.0.0"`;
- `build_primary_v3_event()` stamps v3 explicitly and does not inherit a v2 environment override;
- `require_primary_v3_event_type()` rejects legacy-only families and unknown families;
- a constructed event must classify as `PRIMARY_V3` or construction fails.

The ordinary low-level observability validator remains compatibility plumbing because historical v2 records still need validation. It is no longer treated as the authority that decides whether an event is a **new primary write**.

### Historical read compatibility

The same migration layer provides:
- `LEGACY_COMPAT` identity for the bounded legacy families;
- `HISTORICAL_SCHEMA` identity for non-v3 stored events;
- `validate_historical_event()` for read-side validation without changing original `event_type` or `schema_version`;
- no silent promotion from v2/legacy evidence to v3 truth.

This makes compatibility one-way: old evidence can be read, but it is not a source of new primary identity.

## 4. Implemented live runtime boundary

### 4.1 Distribution

`send/core/distribution_router_primary_v3.py` wraps the existing validated v3 routing mechanics while replacing only the migration-era write hooks:
- route evaluation, entitlements, daily limits, destination mapping, deduplication, Telegram publication, feedback, outcome registration, and publication evidence remain unchanged;
- primary `route_publish_attempt`, `route_publish_result`, `route_reset`, route-state events, and `signal_stage_visible` remain written;
- fresh `tier_publish` and `tier_reset` writes are suppressed from the active primary runtime boundary.

### 4.2 Engine and scheduler entry points

The active runtime entry points bind to the primary-v3 distribution boundary:
- `runtime.engine_loop` binds Signal Engine distribution to `distribution_router_primary_v3` before the engine loop executes;
- `runtime.distribution_scheduler` imports `distribution_router_primary_v3` directly for daily reset.

An AST regression guard inspects these active write entry points and fails if a literal `decision`, `signal_event`, `tier_publish`, or `tier_reset` construction is reintroduced through `build_event`, `_log_event`, or shorthand `log_event` calls.

## 5. Implemented consumer migration

### Distribution analytics

`analytics_engine._load_distribution_metrics()` now:
- treats `route_publish_result` with v3 identity as primary evidence;
- retains older `tier_publish`/historical route-result rows as bounded fallback;
- suppresses a matching legacy representation when the same observable publication fingerprint already has primary v3 evidence;
- reports primary, fallback, duplicate-suppression, historical-named, and invalid counts separately.

### Research funnel

`research_engine.compute_signal_funnel()` now:
- uses PRE_DISTRIBUTION `signal_execution_result` with `signal_event_available=true` as primary v3 candidate evidence;
- deduplicates by `execution_attempt_id`;
- excludes POST_DISTRIBUTION rows from candidate counting;
- retains historical `signal_event` as bounded fallback;
- suppresses matching `(signal_id, stage)` legacy rows when primary v3 candidate evidence exists;
- leaves unmatched historical evidence explicitly countable as fallback.

## 6. Historical integrity rules

R-021 does not:
- edit stored JSONL history;
- change an existing record's `schema_version`;
- relabel a legacy `event_type` as v3;
- infer missing correlation merely to force deduplication;
- convert COMMUNITY_TRUTH or operational evidence into strategy-performance truth.

If evidence cannot be unambiguously correlated, it remains separately classified rather than guessed.

## 7. Regression requirements and current evidence

R-021 regression coverage proves:
- live distribution writes primary route events without fresh `tier_publish` / `tier_reset` duplication;
- live scheduler cannot manufacture a second legacy reset event;
- primary event construction rejects legacy-only event families;
- primary construction remains v3 even if the lower-level logger's configured version is altered to v2 in a test;
- historical v2 validation preserves original identity;
- analytics uses v3-first distribution evidence with bounded legacy fallback and deduplication;
- Research uses v3-first candidate evidence with bounded legacy fallback and transition deduplication;
- active runtime entry points cannot reintroduce literal legacy event writes without failing CI.

A previously exact PR head `7fb5e15fd33d17b68a57751928f2ff8a88b7a049` passed:
- provider selector: 5 tests;
- Telegram Admin regression: 72 tests;
- full repository suite: 1232 tests.

Later Research mixed-history deduplication, anti-reentry coverage, and documentation synchronization changed the branch head. The resulting exact final head must pass the same CI gates before PR #149 is marked Ready for Review.

## 8. Non-goals / safety boundary

R-021 does not change:
- strategy mathematics or thresholds;
- Trade Physics formulas;
- Finnhub-exclusive provider policy or EUR/USD scope;
- 2-second evaluation cadence;
- FSM trading policy;
- distribution entitlements or daily limits;
- Telegram authorization or roles;
- outcome truth definitions;
- broker execution state.

Broker execution remains disabled.

## 9. Completion rule

R-021 is complete only when the exact final PR head passes CI and final review finds no unresolved migration correctness defect. After Owner merge, `REMEDIATION_MASTER_PLAN.md` must be reconciled on `main` with the merged R-020/R-021 state and final main validation evidence.
