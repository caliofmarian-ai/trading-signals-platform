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
Status: CLOSED
PR: #101
Merged main commit: `ceba3c983936d68d9429a0c28d59b7e179bd0b0a`
Depends on: R-001 — SATISFIED
Validation: 983 full-suite tests passed; provider selector 5 passed; Telegram admin regression 72 passed.

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
Status: CLOSED
Issue: #102 — CLOSED
PR: #103
Merged main commit: `60b1e885ee01126d4b99e8aaa5cc34d995c6ce8e`
Depends on: R-002 — SATISFIED
Validation: 991 full-suite tests passed; provider selector 5 passed; Telegram admin regression 72 passed.

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
Status: CLOSED
Issue: #104 — CLOSED
PR: #105
Merged main commit: `a05710aafb1dba0d88ee11c926766bb6506a1bb2`
Depends on: R-003 — SATISFIED
Validation: 998 full-suite tests passed; provider selector 5 passed; Telegram admin regression 72 passed; final GitHub Actions run 33562146134 SUCCESS.

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
Status: CLOSED
Issue: #106 — CLOSED
PR: #107
Merged main commit: `1f5a06ffc0de7f83df4a7bb58a2162bf43b217d8`
Depends on: R-004 — SATISFIED
Validation: 1002 full-suite tests passed; provider selector 5 passed; Telegram admin regression 72 passed; final GitHub Actions run 33564055667 SUCCESS.

Required outcome:
- duplicate same-opportunity/same-stage/same-candle OPEN_NOW is observed but not re-released;
- `stage_handoff_ready=false` and `trade_execution_ready=false` for duplicates;
- distribution dedup remains second defense, not primary defense.

Acceptance:
- exact OPEN_NOW duplicate regression test;
- restart/persisted-state duplicate test where applicable.

### R-006 — Canonical parameter validation in live engine
Severity: HIGH
Status: CLOSED
Issue: #108 — CLOSED
PR: #109
Merged main commit: `8911e790ef6d466c39a45a325ae6aeaa864af95a`
Depends on: R-005 — SATISFIED
Validation: 1010 full-suite tests passed; provider selector 5 passed; Telegram admin regression 72 passed; final GitHub Actions run 33565403255 SUCCESS.

Required outcome:
- live Signal Engine loads algo params through the canonical loader/validator;
- syntactically valid but semantically invalid parameter files fail closed before strategy evaluation.

Acceptance:
- corrupted/missing/out-of-range configuration cannot reach strategy layers;
- observable failure state with no signal candidate.

### R-007 — Fail-closed production startup validation
Severity: HIGH
Status: CLOSED
Issue: #110 — CLOSED
PR: #111
Merged main commit: `5ba1e7773db439df488108f875b59cae58d70524`
Depends on: R-006 — SATISFIED
Validation: 1025 full-suite tests passed; provider selector 5 passed; Telegram admin regression 72 passed; final GitHub Actions run 33567808537 SUCCESS.

Required outcome:
- production boot validates required params, symbols, provider selection/readiness, permissions/config, and persistent state before starting decision/distribution threads;
- validation code is part of the actual Railway startup path rather than an optional script.

Acceptance:
- invalid critical config blocks engine start;
- Telegram/admin may expose safe diagnostics if allowed, but no strategy/distribution starts in unsafe state.

### R-008 — Candle cadence/gap integrity
Severity: HIGH
Status: CLOSED
Issue: #112 — CLOSED
PR: #113
Merged main commit: `92e4faa332f088a7b9af08dfc3b63ac1badcb4b5`
Depends on: R-007 — SATISFIED
Validation: 1033 full-suite tests passed; provider selector 5 passed; Telegram admin regression 72 passed; final GitHub Actions run 33597024074 SUCCESS.

Required outcome:
- M1/M5 candle history validates expected cadence or explicitly models gaps;
- directional speed/time calculations cannot treat multi-minute gaps as one-minute motion;
- provider-specific legitimate gaps are handled by governed rules rather than silent arithmetic.

Implementation boundary:
- the existing 21-M1 directional-speed window must be exact 60-second cadence;
- the existing 14-period M5 ATR requires 15 exact-cadence M5 candles before ATR-derived Trade Physics speed reference is usable;
- older discontinuities remain explicit evidence and may still support non-time-normalized EMA/structural analysis;
- no missing candle is interpolated or fabricated;
- weekend classification records only the objective UTC-calendar discontinuity and does not invent provider/session trading hours.

Acceptance:
- tests for missing bars, duplicates, out-of-order bars, weekend/session gaps, and exact cadence.

### R-009 — Two-second Finnhub EUR/USD evaluation semantics
Severity: HIGH
Status: CLOSED
Issue: #114 — CLOSED
PR: #115
Merged main commit: `bc761fdbf30f80fcc1abb2ad8c0e054e20ac34ae`
Depends on: R-008 — SATISFIED
Validation: 1038 full-suite tests passed; provider selector 5 passed; Telegram admin regression 72 passed; final GitHub Actions run 33604168049 SUCCESS.

Problem:
- engine ticks every 2 seconds, but generic wide selection spreads symbols across a 60-second cycle;
- with FINNHUB's effective EUR/USD-only scope, the sole wide symbol was therefore evaluated only in slot zero instead of every engine tick.

Required outcome:
- when FINNHUB is exclusively active with EUR/USD-only scope, the current intended symbol is evaluated according to the governed 2-second runtime cadence where market evidence permits;
- no provider mixing and no fake candles.

Implementation boundary:
- reuse `runtime.market_client.configured_symbols()` as provider-scope authority;
- intersect provider scope with Owner-controlled active symbols before scheduling;
- preserve watchlist membership as the only source of focus semantics;
- preserve the existing 60-second sharded wide-scan behavior when provider scope is unconstrained.

Acceptance:
- scheduler tests prove effective Finnhub EUR/USD evaluation cadence;
- focus/wide lifecycle semantics remain canonical.

### R-010 — Model Time boundary/sawtooth review
Severity: HIGH
Status: CLOSED
Issue: #116 — CLOSED
PR: #117
Merged main commit: `e42abad1ebec47f075eee8f7de78f8085bdc4732`
Depends on: R-001 — SATISFIED; execution sequence through R-009 — SATISFIED
Validation: 1041 full-suite tests passed; provider selector 5 passed; Telegram admin regression 72 passed; PR final GitHub Actions validation SUCCESS.

Required outcome:
- determine canonically whether integer rounding belongs anywhere in Model Time;
- test boundary behavior around minute transitions;
- do not change formula merely for smoothness without canonical justification.

Implementation boundary:
- `CANONICAL_MASTER_INDEX_v2.0.0` is authoritative and confirms `TIME_MODEL_UNIFIED_CANON_v3.0.0.md` is Active Canonical despite stale lower-level header wording;
- active v3 does not define a fractional replacement derivation for `model_expiry`, so the existing bounded `ceil(clamp(...))` window is characterized rather than replaced;
- 4.999 / 5.000 / 5.001 minute boundary behavior is explicit and regression-tested;
- an R-010 regression exposed machine floating-point drift at an exact-fit maximum boundary; only conceptual equality is normalized with `isclose` at 1e-12 relative/absolute tolerance;
- exact fit yields reciprocal ratios of 1 and `READY`; any real overrun remains `LATE` and cannot extend the configured maximum;
- internal Model Time remains separate from calibrated trader-facing Execution Time.

Acceptance:
- explicit canonical decision documented;
- continuity/boundary tests added;
- exact-fit numerical representation cannot falsely degrade a setup;
- no trader-facing expiry derives from Model Time rounding.

## Priority 2 — Distribution, admin, provider, and control-plane reconciliation

### R-011 — FREE entitlement limit reconciliation
Severity: HIGH
Status: IN PROGRESS
Issue: #118
Branch: `remediation/audit-2026-09-01-r011-free-entitlement`
Depends on: R-010 — SATISFIED

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
- 2026-09-01: R-002 merged through PR #101; main advanced to `ceba3c983936d68d9429a0c28d59b7e179bd0b0a`; final validation was provider selector 5 passed, Telegram admin regression 72 passed, full repository suite 983 passed.
- 2026-09-01: R-003 started on branch `remediation/audit-2026-09-01-r003-truth-source-separation`; Issue #102 and Draft PR #103 created.
- 2026-09-01: R-003 merged through PR #103; main advanced to `60b1e885ee01126d4b99e8aaa5cc34d995c6ce8e`; Issue #102 closed; final validation was provider selector 5 passed, Telegram admin regression 72 passed, full repository suite 991 passed.
- 2026-09-01: R-004 started on branch `remediation/audit-2026-09-01-r004-intelligence-input-sanitation`; Issue #104 and Draft PR #105 created; current validation is provider selector 5 passed, Telegram admin regression 72 passed, full repository suite 998 passed, GitHub Actions run 33561964658 SUCCESS.
- 2026-09-01: R-004 merged through PR #105; main advanced to `a05710aafb1dba0d88ee11c926766bb6506a1bb2`; Issue #104 closed; final validation was provider selector 5 passed, Telegram admin regression 72 passed, full repository suite 998 passed.
- 2026-09-01: R-005 started on branch `remediation/audit-2026-09-01-r005-fsm-open-now-idempotency`; Issue #106 and Draft PR #107 created; current validation is provider selector 5 passed, Telegram admin regression 72 passed, full repository suite 1002 passed, GitHub Actions run 33563918504 SUCCESS.
- 2026-09-01: R-005 merged through PR #107; main advanced to `1f5a06ffc0de7f83df4a7bb58a2162bf43b217d8`; Issue #106 closed; final validation was provider selector 5 passed, Telegram admin regression 72 passed, full repository suite 1002 passed, GitHub Actions run 33564055667 SUCCESS.
- 2026-09-01: R-006 started on branch `remediation/audit-2026-09-01-r006-canonical-param-validation`; Issue #108 and Draft PR #109 created; current validation is provider selector 5 passed, Telegram admin regression 72 passed, full repository suite 1010 passed, GitHub Actions run 33565250011 SUCCESS.
- 2026-09-01: R-006 merged through PR #109; main advanced to `8911e790ef6d466c39a45a325ae6aeaa864af95a`; Issue #108 closed; final validation was provider selector 5 passed, Telegram admin regression 72 passed, full repository suite 1010 passed, GitHub Actions run 33565403255 SUCCESS.
- 2026-09-01: R-007 started on branch `remediation/audit-2026-09-01-r007-fail-closed-startup`; Issue #110 and Draft PR #111 created; current validation is provider selector 5 passed, Telegram admin regression 72 passed, full repository suite 1025 passed, GitHub Actions run 33567579775 SUCCESS.
- 2026-09-02: R-007 merged through PR #111; main advanced to `5ba1e7773db439df488108f875b59cae58d70524`; Issue #110 closed; final validation was provider selector 5 passed, Telegram admin regression 72 passed, full repository suite 1025 passed, GitHub Actions run 33567808537 SUCCESS.
- 2026-09-02: R-008 started on branch `remediation/audit-2026-09-01-r008-candle-cadence-gap-integrity`; Issue #112 and Draft PR #113 created; current validation is provider selector 5 passed, Telegram admin regression 72 passed, full repository suite 1033 passed, GitHub Actions run 33596838289 SUCCESS.
- 2026-09-02: R-008 merged through PR #113; main advanced to `92e4faa332f088a7b9af08dfc3b63ac1badcb4b5`; Issue #112 closed; final validation was provider selector 5 passed, Telegram admin regression 72 passed, full repository suite 1033 passed, GitHub Actions run 33597024074 SUCCESS.
- 2026-09-02: R-009 started on branch `remediation/audit-2026-09-01-r009-finnhub-two-second-evaluation`; Issue #114 and Draft PR #115 created; current validation is provider selector 5 passed, Telegram admin regression 72 passed, full repository suite 1038 passed, GitHub Actions run 33603960610 SUCCESS.
- 2026-09-02: R-009 merged through PR #115; main advanced to `bc761fdbf30f80fcc1abb2ad8c0e054e20ac34ae`; Issue #114 closed; final validation was provider selector 5 passed, Telegram admin regression 72 passed, full repository suite 1038 passed, GitHub Actions run 33604168049 SUCCESS.
- 2026-09-02: R-010 started on branch `remediation/audit-2026-09-01-r010-model-time-boundaries`; Issue #116 and Draft PR #117 created. Initial boundary characterization exposed an exact-fit floating-point defect; after the bounded numerical fix, validation is provider selector 5 passed, Telegram admin regression 72 passed, full repository suite 1041 passed, GitHub Actions run 33605761955 SUCCESS.
