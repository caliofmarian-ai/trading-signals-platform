# Repository-Wide Remediation Master Plan — 2026-09-01

Status: ACTIVE EXECUTION PLAN
Owner rule: work must follow this order unless a newly discovered blocker is demonstrably upstream of the current item.
Base audited commit: `7b26d33e34cf30790c52583a75d1ed36a2b9cf52`

## Execution discipline

1. Work one remediation item at a time.
2. Every item gets a dedicated branch/PR or a clearly isolated commit sequence if already inside the active remediation branch.
3. Before implementation: re-check the relevant active canon and current runtime path.
4. During implementation: preserve fail-closed behavior; do not invent thresholds, calibration values, market data, outcomes, or probabilities.
5. Every fix must add regression coverage for the exact defect.
6. Run the focused tests plus the full offline suite before Ready for Review.
7. Do not enable broker execution.
8. Do not lower canonical score thresholds as part of unrelated remediation.
9. Do not mix Finnhub and Twelve Data in one evidence stream.
10. Do not advance to the next item until the current item is merged and post-merge state is re-checked.
11. Update this file after every merged remediation: status, PR, commit, tests, and any newly discovered dependency.

## Priority 0 — Truth-chain blockers

### R-001 — Execution Time authority end-to-end
Severity: CRITICAL
Status: CLOSED
PR: #100
Merged main commit: `480303bc1e52c3610c0e9ffab3e539fcad358c16`
Validation: 971 full-suite tests passed; provider selector 5 passed; Telegram admin regression 72 passed.

Problem:
- External `expiry_minutes` is currently derived from `ceil(model_expiry)` in SignalEvent compatibility behavior.
- The canonical Execution Time model correctly refuses to invent calibrated trader-facing expiry when calibration is absent, but the live signal candidate path bypasses that authority.

Required outcome:
- Trader-facing/external expiry must come only from the governed Execution Time authority.
- OPEN_NOW must fail closed for external expiry/distribution when required execution calibration is unavailable.
- Model Time remains internal strategic evidence and is never silently promoted into external execution time.
- PRE/CONFIRM semantics must remain canonical and explicit.

Acceptance:
- no external `expiry_minutes` derived directly from `ceil(model_expiry)`;
- explicit execution-time evidence carried into SignalEvent when available;
- missing calibration blocks external executable expiry rather than inventing one;
- regression tests prove bypass is impossible;
- focused + full test suite pass.

### R-002 — Objective Trade Temporal Telemetry completion
Severity: CRITICAL
Status: IN PROGRESS
PR: #101 (Draft until final audit/CI completion)
Depends on: R-001 — SATISFIED

Problem:
- OPEN trade telemetry is registered, but objective expiry and post-expiry prices/results remain placeholders.

Required outcome:
- immutable OPEN_NOW registration with canonical execution expiry;
- objective market price captured at expiry and governed post-expiry checkpoints;
- objective result classification produced from market truth;
- no fabricated interpolation when required market evidence is absent;
- restart-safe pending-trade reconciliation.

Acceptance:
- expiry result is reproducible from persisted market evidence;
- missing evidence remains explicit UNKNOWN/PENDING, never silently WIN/LOSS;
- duplicate reconciliation is idempotent;
- tests cover restart, stale/missing market data, BUY/SELL, draw/equality, and duplicate processing.

### R-003 — Truth-source separation in outcomes and analytics
Severity: CRITICAL
Status: PENDING
Depends on: R-002

Problem:
- community self-reports are currently aggregated into a generic `win_rate` that can be mistaken for strategy performance.

Required outcome:
- MARKET_TRUTH, OPERATIONAL_TRUTH, and COMMUNITY_TRUTH remain distinct from storage through analytics/UI;
- strategy win-rate/effectiveness metrics use objective market truth only;
- community feedback remains a separate UX/community metric;
- MISSED remains operational, not market LOSS.

Acceptance:
- no generic strategy `win_rate` can be produced from community votes;
- reports state source/sample explicitly;
- migration/backward-compatibility behavior is explicit;
- regression tests cover mixed-source files.

### R-004 — Research/intelligence input sanitation before autonomy
Severity: CRITICAL FOR FUTURE AUTONOMY
Status: PENDING
Depends on: R-003

Problem:
- offline research/intelligence modules consume analytics derived from community outcomes; adaptive parameter and optimizer code also contains legacy-schema assumptions.

Required outcome:
- research/optimizer/risk/adaptive modules consume only governed analytics products with source/readiness metadata;
- legacy `thresholds` writes removed or migrated to canonical parameter schema;
- optimizer funnel key/schema mismatches repaired;
- autonomy remains disabled until sample/readiness gates are canonically satisfied.

Acceptance:
- no intelligence recommendation can be generated from COMMUNITY_TRUTH as model-label truth;
- no live parameter mutation occurs automatically;
- tests prove source and sample gates.

## Priority 1 — Live decision-path correctness

### R-005 — FSM OPEN_NOW idempotency
Severity: HIGH
Status: PENDING

Required outcome:
- duplicate same-opportunity/same-stage/same-candle OPEN_NOW is observed but not re-released;
- `stage_handoff_ready=false` and `trade_execution_ready=false` for duplicates;
- distribution dedup remains second defense, not primary defense.

Acceptance:
- exact OPEN_NOW duplicate regression test;
- restart/persisted-state duplicate test where applicable.

### R-006 — Canonical parameter validation in live engine
Severity: HIGH
Status: PENDING

Required outcome:
- live Signal Engine loads algo params through the canonical loader/validator;
- syntactically valid but semantically invalid parameter files fail closed before strategy evaluation.

Acceptance:
- corrupted/missing/out-of-range configuration cannot reach strategy layers;
- observable failure state with no signal candidate.

### R-007 — Fail-closed production startup validation
Severity: HIGH
Status: PENDING
Depends on: R-006

Required outcome:
- production boot validates required params, symbols, provider selection/readiness, permissions/config, and persistent state before starting decision/distribution threads;
- validation code is part of the actual Railway startup path rather than an optional script.

Acceptance:
- invalid critical config blocks engine start;
- Telegram/admin may expose safe diagnostics if allowed, but no strategy/distribution starts in unsafe state.

### R-008 — Candle cadence/gap integrity
Severity: HIGH
Status: PENDING

Required outcome:
- M1/M5 candle history validates expected cadence or explicitly models gaps;
- directional speed/time calculations cannot treat multi-minute gaps as one-minute motion;
- provider-specific legitimate gaps are handled by governed rules rather than silent arithmetic.

Acceptance:
- tests for missing bars, duplicates, out-of-order bars, weekend/session gaps, and exact cadence.

### R-009 — Two-second Finnhub EUR/USD evaluation semantics
Severity: HIGH
Status: PENDING

Problem:
- engine ticks every 2 seconds, but wide selection is spread across a 60-second cycle.

Required outcome:
- when FINNHUB is exclusively active with EUR/USD-only scope, the current intended symbol is evaluated according to the governed 2-second runtime cadence where market evidence permits;
- no provider mixing and no fake candles.

Acceptance:
- scheduler tests prove effective Finnhub EUR/USD evaluation cadence;
- focus/wide lifecycle semantics remain canonical.

### R-010 — Model Time boundary/sawtooth review
Severity: HIGH
Status: PENDING
Depends on: R-001

Required outcome:
- determine canonically whether integer rounding belongs anywhere in Model Time;
- test boundary behavior around minute transitions;
- do not change formula merely for smoothness without canonical justification.

Acceptance:
- explicit canonical decision documented;
- continuity/boundary tests added.

## Priority 2 — Distribution, admin, provider, and control-plane reconciliation

### R-011 — FREE entitlement limit reconciliation
Severity: HIGH
Status: PENDING

Required outcome:
- active canon, runtime defaults, channel config, `.env.example`, tests, and admin display agree on FREE limit = 6 unless a governed override is explicitly intended and auditable.

### R-012 — Strategy profile reconciliation
Severity: HIGH
Status: PENDING

Required outcome:
- Admin profiles cannot silently lower active canonical thresholds or mutate obsolete SR semantics;
- profiles either become canonical governed presets or are removed/disabled until canonically defined.

### R-013 — Provider-state corruption fail-closed behavior
Severity: HIGH
Status: PENDING

Required outcome:
- corrupt persisted provider state produces an explicit blocked/degraded state instead of silently selecting another provider;
- owner selection remains authoritative;
- one provider only.

### R-014 — Strategy catalog / Owner UI authority reconciliation
Severity: HIGH
Status: PENDING

Required outcome:
- strategy catalog and Owner surfaces point to the active canonical strategy authority (`ALGO_SPEC_v3.0.0` where applicable) and accurate implementation/version terminology.

### R-015 — Environment/config example reconciliation
Severity: MEDIUM-HIGH
Status: PENDING

Required outcome:
- `.env.example` reflects current provider bootstrap policy, event schema v3, FREE limit 6, runtime paths, and current safety defaults;
- example values cannot silently downgrade live semantics.

### R-016 — Role/permission fail-closed reconciliation
Severity: MEDIUM-HIGH
Status: PENDING

Required outcome:
- malformed critical permission configuration does not broaden authority through permissive fallback;
- precedence between canonical baseline and operator overrides is explicit and testable;
- non-Owner role journeys completed.

### R-017 — Telegram multi-role final acceptance
Severity: HIGH
Status: PENDING
Tracks: Issue #23

Required outcome:
- canonical non-Owner journeys;
- stale/retired/unauthorized handling live where practicable;
- final multi-role Railway/Telegram acceptance evidence.

## Priority 3 — Observability, analytics, audit tooling

### R-018 — Strategy Auditor v3 event compatibility
Severity: HIGH
Status: PENDING

Required outcome:
- auditor consumes `decision_evaluated` and other active v3 event families;
- legacy adapters are explicit, not mistaken for primary truth;
- reports no longer show zero decisions when v3 events exist.

### R-019 — Daily auditor scheduling and persistent reports
Severity: MEDIUM-HIGH
Status: PENDING
Depends on: R-018

Required outcome:
- governed Railway-compatible scheduling or runtime scheduler integration;
- reports/cache persist under runtime base paths;
- failures are observable.

### R-020 — Decision audit identity materialization
Severity: MEDIUM
Status: PENDING

Required outcome:
- stable decision audit/correlation identity links DecisionObject, FSM, SignalEvent, distribution, telemetry, and outcomes without recomputing truth.

### R-021 — Event schema migration cleanup
Severity: MEDIUM
Status: PENDING

Required outcome:
- v3 is the live primary event schema;
- v2 compatibility is bounded, documented, and prevented from re-entering new runtime paths.

## Priority 4 — Repository governance, security, and maintainability

### R-022 — Required CI / protected main
Severity: HIGH
Status: PENDING

Required outcome:
- permanent repository-wide CI for canonical tests/full offline suite;
- merge policy requires passing checks where repository permissions allow;
- Issue #23 independent CI requirement closed only with evidence.

### R-023 — Dependency security upgrade
Severity: MEDIUM
Status: PENDING

Required outcome:
- upgrade `requests` and `websocket-client` to currently supported secure versions after compatibility review;
- full regression suite and provider/Telegram network mocks pass;
- no blind dependency bump.

### R-024 — Active canonical header/status cleanup
Severity: MEDIUM
Status: PENDING

Required outcome:
- files under canonical active paths do not claim they are proposed/not active;
- Master Index, activation records, headers, links, and versions agree.

### R-025 — Backup/orphan code quarantine cleanup
Severity: MEDIUM
Status: PENDING

Required outcome:
- `.bak_*` and obsolete live-adjacent code removed or moved into explicit archive areas;
- searches/agents cannot confuse backups with active runtime implementation.

### R-026 — README/operator documentation refresh
Severity: MEDIUM
Status: PENDING
Depends on: preceding control-plane fixes

Required outcome:
- current runtime architecture, provider selection, safety state, test command, Railway startup, canonical authority, and remediation status documented accurately.

## Completion gate

The repository-wide remediation program is complete only when:

- R-001 through R-026 are CLOSED or explicitly DEFERRED by an owner decision recorded in this plan;
- all CRITICAL/HIGH items are closed;
- full offline suite passes on final main;
- current Railway runtime is re-validated;
- Telegram Owner and non-Owner acceptance required by canon is evidenced;
- objective market-truth telemetry exists and analytics distinguishes all truth sources;
- autonomous strategy evolution remains disabled until its own canonical readiness gates are satisfied;
- broker execution remains disabled unless separately and explicitly governed in a future program.

## Progress log

- 2026-09-01: repository-wide audit completed against main commit `7b26d33e34cf30790c52583a75d1ed36a2b9cf52`.
- 2026-09-01: remediation program created; R-001 started on branch `remediation/audit-2026-09-01-r001-execution-time`.
- 2026-09-01: R-001 merged through PR #100; main advanced to `480303bc1e52c3610c0e9ffab3e539fcad358c16`; Issue #98 closed automatically.
- 2026-09-01: R-002 started on branch `remediation/audit-2026-09-01-r002-objective-telemetry`; PR #101 opened Draft.
- 2026-09-01: R-002 current CI evidence on head prior to this plan update: provider selector 5 passed, Telegram admin regression 72 passed, full repository suite 980 passed.
