# Trading Signals Platform

Governed Telegram trading-signal platform with canonical strategy, evidence, distribution, observability, research, and admin/control-plane layers.

This repository is the source of truth for implementation and canonical documentation. Runtime observations from Railway and Telegram are evidence of deployment/runtime state; they do not override canonical authority or source history.

## Verified project state — 2026-09-15

- Production source: `caliofmarian-ai/trading-signals-platform`, branch `main`.
- Latest verified Railway deployment during this documentation refresh: commit `ad76434a66dce6bdf1ae274c289d81d91bd02161`, terminal status `SUCCESS`.
- Railway production has one persistent volume mounted at `/data` (5 GB, `europe-west4-drams3a`).
- Telegram UI persisted state is loaded from `/data/state/telegram_ui_state.json` and the poller starts after successful runtime initialization.
- R-022 permanent CI/protected-main work, R-023 dependency compatibility, R-024 active-canonical status reconciliation, and R-025 repository hygiene are integrated in `main`.
- R-017 source/config reconciliation for the live PRIMARY_ADMIN and real `ADMIN_COMMANDS` topic is deployed, but the final post-fix real Telegram PRIMARY_ADMIN journey is still **PENDING**. Do not treat source tests or a successful Railway deployment as that live acceptance proof.
- Issue #137 temporal-market-intelligence documents are still **TRANSITIONAL / NON-ACTIVE**. The active functional canonical inventory remains 43, not 47.
- Broker execution is outside the currently accepted operating surface. Do not enable it from documentation, tests, or inferred state.

The connected Railway OAuth surface exposes variable names but redacts values. Therefore this README does not use connector inspection alone to claim current secret values, selected provider value, `SHADOW_MODE`, or `ENABLE_BROKER_EXECUTION`. Verify those through the governed runtime/operator surfaces before making an operational claim.

## Canonical authority

The authoritative root is:

- [`send/docs/canonical/active/CANONICAL_MASTER_INDEX_v2.0.0.md`](./send/docs/canonical/active/CANONICAL_MASTER_INDEX_v2.0.0.md)

It declares **43 unique active functional specifications**. The principal root manifests are:

- [`CANONICAL_STRATEGY_STACK_v2.0.0.md`](./send/docs/canonical/active/CANONICAL_STRATEGY_STACK_v2.0.0.md)
- [`ADMIN_SURFACE_AND_CONTROL_PLANE_CANON_v2.0.1.md`](./send/docs/canonical/active/ADMIN_SURFACE_AND_CONTROL_PLANE_CANON_v2.0.1.md)

Supporting governance records, superseded documents, deprecated material, intake documents, and transitional candidates cannot override active canon.

### Temporal-market-intelligence gap

Issue #137 introduced four governed candidates under `send/docs/canonical/transitional/`:

- `MARKET_BEHAVIOR_OBSERVATION_SPEC_v1.0.0.md`
- `TEMPORAL_MARKET_BEHAVIOR_ANALYTICS_SPEC_v1.0.0.md`
- `TEMPORAL_PATTERN_VALIDATION_SPEC_v1.0.0.md`
- `STRATEGY_TRADING_WINDOW_INTELLIGENCE_SPEC_v1.0.0.md`

They are observational/research candidates only. They do **not** currently authorize a temporal production gate, automatic strategy changes, or trade blocking/permitting. A future promotion requires a coherent successor update to the Master Index and affected architecture/interface/invariant/test authorities.

## Runtime model

### Engine cadence

`send/runtime/engine_loop.py` defines `ENGINE_TICK_SECONDS = 2`.

That means the runtime evaluates the signal engine every two seconds. It does **not** mean:

- a new market candle is fetched every two seconds;
- a signal is guaranteed every two seconds;
- history/freshness gates may be bypassed;
- a broker order is created every two seconds.

Each tick calls the governed signal-engine path. If required market/history evidence is unavailable or stale, the platform must remain fail-closed rather than inventing a decision.

### Market-data providers and symbol scope

Repository provider control currently supports:

- `FINNHUB`
- `TWELVE_DATA`

The Finnhub implementation has an explicit effective-symbol lock to `EUR/USD`. Repository files such as `send/config/active_symbols.json` contain a broader configured universe and must **not** be interpreted as proof that every symbol is currently provider-effective or production-ready.

The currently selected production provider is governed by runtime configuration (`MARKET_DATA_PROVIDER`). Because connected Railway OAuth redacts the value, use the Admin/runtime status evidence to verify the live provider instead of inferring it from this README.

### Real-data / fail-closed rule

The runtime must use provider-derived market evidence. Missing, stale, structurally invalid, or insufficient history is a blocking condition for decision readiness. Tests, mocks, synthetic fixtures, or historical audit examples are not production market truth.

## Truth-domain separation

The active canonical graph separates three important truth classes:

- **MARKET_TRUTH** — objective provider-derived market evidence and objective market telemetry.
- **OPERATIONAL_TRUTH** — runtime/FSM/distribution/outcome/admin evidence about what the system actually did.
- **COMMUNITY_TRUTH** — member/community self-report or feedback, governed separately and never promoted into market truth merely because users reported it.

Strategy/pre-FSM truth, FSM lifecycle truth, signal-execution truth, route/publication truth, and operational outcome truth also retain their canonical domain owners. Do not collapse these into one generic “result” field.

## Telegram and Admin control plane

Telegram is an application/control surface, not the canonical authority itself.

Current security properties include:

- role resolution through `send/config/admin_roles.json` and the governed permission matrix;
- fail-closed Admin context validation;
- configured Admin supergroup/topic validation through `ADMIN_CONTROL_CHAT_ID` and `ADMIN_CONTROL_THREAD_ID`;
- Owner private-DM recovery for explicitly allowed Owner commands;
- single-active-message navigation with persisted UI state on the Railway volume;
- sanitized fallback behavior for interactive transport failures;
- document transport for commands such as `/audit_runtime` instead of exposing temporary file paths.

R-017 final live multi-role acceptance remains evidence-driven. A role that is not configured with a real account must not be reported as live PASS merely because its automated E2E fixture passes.

## Railway production model

Repository deployment configuration is [`railway.json`](./railway.json).

Current start command:

```bash
PYTHONPATH=send python -m scripts.railway_start
```

The Railway startup path:

1. resolves and validates `BINARYBOT_BASE_DIR`;
2. applies the `/data` path contract;
3. initializes required runtime directories/log files and seeds missing config files;
4. preserves existing Owner-controlled persistent configuration unless a narrowly governed migration explicitly says otherwise;
5. runs readiness validation;
6. starts the runtime only after initialization/readiness succeed.

See the operator runbook:

- [`audit/railway-deployment-preparation-01/RAILWAY_OPERATOR_RUNBOOK.md`](./audit/railway-deployment-preparation-01/RAILWAY_OPERATOR_RUNBOOK.md)

## Repository CI

The permanent workflow is:

- [`.github/workflows/repository-ci.yml`](./.github/workflows/repository-ci.yml)

Required check name: **`Required Repository CI`**.

For pull requests into `main`, CI checks out and verifies the exact change-head SHA, then runs:

- critical module compilation;
- repository-governance regression;
- provider-selector regression;
- Telegram Admin regression;
- critical canonical contract/integration regressions;
- the complete repository test suite.

Local equivalent for the complete suite:

```bash
PYTHONPATH=send python -m pytest -q
```

A green historical run is not evidence for a later head. Merge decisions must use the check result for the exact current PR head.

## Repository hygiene

Active implementation must not contain live-adjacent editor/backup artifacts. Historical provenance is deliberately retained only in explicit history areas such as:

- `send/_archive/**`
- `send/docs/_deprecated/**`
- `send/docs/canonical/deprecated/**`
- `audit/**`

`tests/batch_10/test_repository_hygiene.py` enforces the active-vs-history boundary.

## Current open evidence / remediation

As of the verification snapshot above:

- **R-017 / #131** — source, CI, and production reconciliation are deployed; final real PRIMARY_ADMIN Telegram journey remains pending.
- **#137** — temporal market behavior/trading-window canonical candidates remain transitional and non-active.
- **#174** — healthy Telegram startup diagnostics are currently mislabeled as Railway `error` severity and `runtime_instance_id` may show a placeholder; this is an observability defect, not evidence that the successful deployment crashed.
- **R-026 / #154** — this README/operator-documentation refresh is the active documentation reconciliation lane.

Do not convert `PENDING`, `UNKNOWN`, transitional material, or source-only verification into `DEPLOYED`/live acceptance without direct evidence.

## Key repository areas

- `send/core/` — governed core decision, state, Telegram, observability, distribution, analytics, and strategy modules.
- `send/runtime/` — production runtime workers/boot/provider integration.
- `send/config/` — repository-side configuration seeds/defaults.
- `send/docs/canonical/active/` — active canonical functional authority.
- `send/docs/canonical/transitional/` — non-active candidate canon.
- `tests/` — repository-wide automated validation.
- `audit/` — historical audit, remediation, and verification evidence.

## Safety boundary

This platform provides governed trading-signal decision support. A signal, score, confidence value, historical win rate, or research finding is not a guarantee of profit. Automated broker execution must remain disabled unless separately designed, governed, tested, approved, and explicitly enabled through a future execution program.
