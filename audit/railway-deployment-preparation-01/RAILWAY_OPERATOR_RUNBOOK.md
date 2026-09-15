# Railway Operator Runbook

Operational runbook for the production deployment of `caliofmarian-ai/trading-signals-platform`.

This document describes the verified operating model. It does not turn source/configuration defaults into claims about live runtime state. When Railway OAuth redacts a variable value, verify the effective value through the governed runtime/Admin surfaces rather than guessing it.

## 1. Production identity

- Repository: `caliofmarian-ai/trading-signals-platform`
- Production branch: `main`
- Railway project/service: `trading-signals-platform`
- Runtime volume mount: `/data`
- Repository start command: `PYTHONPATH=send python -m scripts.railway_start`
- Repository CI required check: `Required Repository CI`

Before operating a deployment, record the exact Git commit SHA and the Railway deployment ID. Do not use a previous green CI run as evidence for a later commit.

## 2. Canonical and source authority

Before changing production, verify the current canonical root:

`send/docs/canonical/active/CANONICAL_MASTER_INDEX_v2.0.0.md`

The current active functional inventory is 43 specifications. Files in `send/docs/canonical/transitional/` are non-active candidates and must not be used to justify production behavior. In particular, Issue #137 temporal-market-intelligence candidates do not authorize a temporal strategy gate or automatic strategy changes.

## 3. Pre-deploy safety gate

A production deployment is eligible only when all of the following are true:

1. the intended change is on a branch based on current `main`;
2. the pull request diff has been reviewed for scope drift;
3. `Required Repository CI` is `SUCCESS` on the exact current PR head;
4. the full repository test suite passed inside that exact CI run;
5. no unreviewed strategy mathematics, provider policy, Telegram RBAC, production-variable, or broker-execution changes are hidden in the diff;
6. any persistent-data migration has an explicit bounded contract and rollback/recovery path.

Do not enable broker execution as part of routine deployment or documentation work.

## 4. Persistent `/data` contract

`BINARYBOT_BASE_DIR` must resolve to the persistent Railway volume, currently `/data`.

Startup creates/uses the following governed runtime areas beneath the base directory:

- `config/`
- `state/`
- `outcomes/`
- `observability/`
- `analytics/`
- `snapshots/`

Important: `scripts.railway_init` seeds repository configuration files only when the corresponding persistent file is missing. Existing Owner-controlled files under `/data/config/` are preserved. A repository edit to a seed file therefore does not automatically prove that the persistent production file changed.

Any migration of preserved configuration must be explicit, narrow, tested, and disabled after the migration when it is intended as one-shot behavior.

### R-017 one-shot PRIMARY_ADMIN reconciliation

`ADMIN_PRIMARY_ADMIN_SYNC_FROM_SOURCE` is a bounded migration switch introduced for the R-017 PRIMARY_ADMIN identity correction.

Normal state: `false` / disabled.

When deliberately set to `true`, startup copies only the repository `primary_admin` list into the persistent Admin roles file after validation. It must not be used as a general-purpose role overwrite mechanism. After a successful reconciliation deployment, return it to `false` without triggering an unnecessary redeploy.

## 5. Environment-variable classes

Do not place real secret values in the repository.

### Required/runtime-critical categories

Verify that the production environment contains the required variable names for the active configuration, including as applicable:

- `BINARYBOT_BASE_DIR`
- `BOT_ENV`
- `MARKET_DATA_PROVIDER`
- provider credential corresponding to the selected provider (`FINNHUB_API_KEY` or `TWELVE_DATA_API_KEY`)
- `ENABLE_TELEGRAM` and `TELEGRAM_BOT_TOKEN` when Telegram is enabled
- `ADMIN_CONTROL_CHAT_ID`
- `ADMIN_CONTROL_THREAD_ID`
- `ADMIN_ROLES_CONFIG`
- `ADMIN_PERMISSIONS_CONFIG`
- `SHADOW_MODE`
- `ENABLE_BROKER_EXECUTION`

Connected Railway OAuth may expose only variable names, not plaintext values. In that case the presence of a name is not proof of its effective value.

### Admin topic context

R-017 production reconciliation uses the verified real `ADMIN_COMMANDS` forum context:

- Bot API chat: `-1003726714813`
- thread: `1310`

The runtime authorization gate remains fail-closed. Do not bypass the chat/thread check to make an acceptance test pass.

### Broker-execution safety

This runbook does not authorize real-money execution. Before every operational sign-off, verify through the governed runtime/configuration surface that broker execution remains disabled. If the effective value cannot be observed, classify it as `UNKNOWN`; do not infer a safe value from `.env.example`, README, tests, or historical screenshots.

## 6. Market-data provider and symbol scope

The repository provider-control layer supports:

- `FINNHUB`
- `TWELVE_DATA`

The selected live provider is determined by `MARKET_DATA_PROVIDER` and must be verified from runtime evidence.

Finnhub currently has an explicit effective-symbol lock to `EUR/USD`. The broader list in `send/config/active_symbols.json` is a configured universe and is not proof that every symbol is supported by the selected live provider.

Never substitute mocked, interpolated, stale, or test data for production market truth. If required provider history/freshness is unavailable, the system must remain fail-closed.

## 7. Two-second engine semantics

`send/runtime/engine_loop.py` currently defines `ENGINE_TICK_SECONDS = 2`.

Operational meaning: the engine calls its governed evaluation path on a two-second cadence.

It does not mean:

- one new candle every two seconds;
- one trading signal every two seconds;
- bypass of minimum-history/freshness gates;
- automatic order execution every two seconds.

If the runtime has insufficient evidence, the correct outcome is a blocked/not-ready decision state.

## 8. Strategy Auditor scheduling

The Strategy Auditor has layered activation and must not be reported as running merely because a repository seed says it is allowed.

Repository `admin_settings.json` includes the Admin feature flag `strategy_auditor_enabled`. Runtime scheduling additionally evaluates:

- `STRATEGY_AUDITOR_ENABLED`
- `STRATEGY_AUDITOR_DAILY_TIME` in `HH:MM`
- `STRATEGY_AUDITOR_TIMEZONE` as an IANA timezone

A valid local schedule requires both local time and timezone. Invalid, incomplete, conflicting, or disabled configuration produces an explicit disabled/error status rather than guessing a schedule.

For operational verification, inspect the Strategy Auditor runtime/Admin status and diagnostics. Treat redacted/unobservable variable values as `UNKNOWN` until runtime evidence resolves them.

## 9. Deployment procedure

1. Confirm the exact intended `main` commit.
2. Confirm the associated PR passed exact-head `Required Repository CI` before merge.
3. Confirm the production Railway service is sourced from `main`.
4. Confirm the persistent volume remains mounted at `/data`.
5. Confirm no unrequested production variable mutation is included in the change.
6. Allow Railway to build/deploy the exact merged commit.
7. Wait for a terminal deployment state; do not call `BUILDING` or `DEPLOYING` a success.
8. Verify the deployment metadata commit hash equals the intended `main` commit.
9. Inspect startup logs for initialization/readiness failures.
10. Confirm the Telegram poller starts when Telegram is enabled.
11. Confirm persisted Telegram UI state resolves under `/data/state/telegram_ui_state.json` when persistence is active.
12. Inspect runtime/provider/history readiness; do not assume a green container implies trading-decision readiness.
13. Verify the broker-execution safety state from runtime/configuration evidence before operational sign-off.

## 10. Runtime diagnostics

Useful evidence surfaces include:

- Railway deployment status and deployment commit hash;
- Railway deploy/runtime logs;
- `/status` and role-appropriate Telegram/Admin status surfaces;
- `/diagnose` for authorized operators;
- `/audit_runtime` document delivery for authorized operators;
- persisted JSONL/runtime artifacts under `/data` where governed;
- Strategy Auditor diagnostics/reports where enabled and configured.

Separate source truth, CI truth, deployment truth, and live Telegram acceptance. One does not automatically prove another.

### Known observability finding — Issue #174

A successful deployment can currently show healthy Telegram startup events as Railway `severity=error` because those diagnostics are printed on stderr. `poller_started` may also report `runtime_instance_id=replace-me` because a placeholder `RUN_ID` can take precedence over the real Railway deployment ID.

Until Issue #174 is remediated, interpret these specific events by their payload (`status=ok`, `poller_started`) and the terminal deployment state. Do not ignore unrelated real errors.

## 11. Telegram acceptance

Automated Telegram tests verify source behavior but do not replace a real Telegram acceptance journey.

For R-017:

- source/config reconciliation: verified;
- exact-head CI: verified;
- corrected code/config deployed to Railway: verified;
- post-fix real PRIMARY_ADMIN `/admin` journey in the actual `ADMIN_COMMANDS` topic: **PENDING** until directly observed.

Unconfigured roles must remain `NOT CONFIGURED`, `NOT TESTABLE`, or equivalent; never fabricate a live identity to force a PASS.

## 12. Rollback and recovery

If a deployment fails:

1. keep the persistent `/data` volume attached;
2. identify whether failure is source, configuration, migration, provider, Telegram, or persistence related;
3. do not delete persistent state as the first troubleshooting action;
4. roll back/redeploy a previously verified source revision when appropriate;
5. re-run readiness and inspect startup/runtime diagnostics;
6. re-verify any migration-specific state before disabling or retrying the migration;
7. preserve audit evidence for the failed and recovered deployments.

Do not use rollback as a way to reactivate superseded canonical authority or stale security configuration.

## 13. CI and local validation

Canonical complete local test command:

```bash
PYTHONPATH=send python -m pytest -q
```

The permanent GitHub workflow is `.github/workflows/repository-ci.yml` and its stable required check is `Required Repository CI`.

Operational acceptance must use the CI result for the exact change head plus Railway evidence for the exact merged deployment commit.

## 14. Secrets and repository safety

Never commit:

- Telegram bot tokens;
- Finnhub/Twelve Data API keys;
- private salts or credentials;
- Railway secret values;
- generated production state/log files;
- ad-hoc backups beside active source files.

Historical provenance belongs in explicit archive/deprecated/audit areas, not next to live implementation.

## 15. Status vocabulary

Use status terms literally:

- `SOURCE VERIFIED` — code/config source has been inspected/tested.
- `CI VERIFIED` — exact-head required CI passed.
- `DEPLOYED` — a terminal successful deployment of the exact intended commit exists.
- `LIVE ACCEPTED` — required real interaction/evidence has been observed.
- `PENDING` / `UNKNOWN` — evidence is still missing or unavailable.

Never collapse these states into one generic `DONE` claim.
