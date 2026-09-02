# R-015 — Environment / Config Example Reconciliation

Status: VALIDATED IMPLEMENTATION — FINAL PR HEAD VALIDATION RECORDED IN PR #127
Issue: #126
Parent: #97
PR: #127
Base main commit: `a50842c22fb4f534da980cbb017172f6f6493427`

## Defect

The root `.env.example` had drifted behind live governed behavior:

- it still presented `TWELVE_DATA` as the deployment default and described Finnhub as a preview;
- it still declared `EVENT_SCHEMA_VERSION=2.0.0` while the live SignalEvent, Signal Engine, and observability contracts use v3 (`3.0.0`);
- it did not explain the post-R-013 provider authority model, where persisted Owner selection wins over deployment bootstrap and existing invalid persisted provider state blocks rather than falling back;
- these stale example values could cause a fresh deployment to be configured with semantics older than the live runtime contract.

## R-015 decision

- `.env.example` is a deployment/bootstrap example, not persisted Owner provider authority;
- current governed shadow bootstrap is `FINNHUB` with the effective EUR/USD-only scope already enforced by runtime provider control;
- a persisted valid Owner provider selection remains authoritative;
- existing invalid persisted provider state fails closed and never falls back to the environment example;
- Twelve Data remains an alternative exclusive provider and must not be mixed with Finnhub in one evidence stream;
- event schema example is `3.0.0`;
- FREE/BASIC/PRO/ELITE remain `6/20/50/UNLIMITED`;
- `/data` persistence paths remain explicit;
- `SHADOW_MODE=true`, `ENABLE_BROKER_EXECUTION=false`, and `ENABLE_TELEGRAM=false` remain the safe example defaults;
- provider/API credentials remain placeholders only.

## Regression proof

`tests/canonical/unit/test_env_example_contract.py` parses the example and proves:

- no malformed or duplicate active key is accepted by the test parser;
- safety defaults and core `/data` paths remain exact;
- event schema cannot regress below v3 in the example;
- entitlement limits remain exact;
- current provider bootstrap is Finnhub, with EUR/USD storage/readiness settings intact;
- both provider secrets and Telegram token remain placeholders;
- comments preserve bootstrap-only authority, persisted Owner precedence, fail-closed behavior, exclusive-provider semantics, and the prohibition on provider mixing.

## Safety boundary

R-015 does not modify market-data provider switching code, persisted provider state, signal mathematics, score thresholds, SR/Corridor, Trade Physics, Time Model, FSM, distribution policy, broker execution, production Railway secrets, or future Forex implementation.

## Validation evidence

Implementation-head validation through GitHub Actions run `33667728450` succeeded on merge candidate `d96024d9fbdbf9a7a4fa2ea7111ee1668bf00e12`:

- provider selector regression: **5 passed**;
- Telegram admin regression: **72 passed**;
- full repository suite: **1065 passed**;
- changed-module compilation: PASS.

The one-shot Master Plan synchronization then advanced the branch and removed itself from the permanent PR diff. Because that synchronization commit was authored by `github-actions[bot]`, GitHub intentionally did not recursively execute the PR workflow for that bot-authored head. This evidence commit is a normal repository commit and triggers the permanent workflow again; the exact final-head run and merge candidate are recorded in PR #127 before Ready for Review.
