# R-013 — Provider-State Corruption Fail-Closed Reconciliation

Status: IMPLEMENTED ON REMEDIATION BRANCH — VALIDATION PENDING
Issue: #122
Parent: #97
Base main commit: `0993852e7bf6f65e393c31c39a2dc6a36c29c95c`

## Defect

`market_data_provider_control._load_persisted_state()` previously returned `None` for both a genuinely absent state file and an existing but unreadable, malformed, non-object, unsupported-provider state. `get_active_provider()` interpreted `None` as permission to use the deployment `MARKET_DATA_PROVIDER` value. This could silently replace persisted Owner authority after startup.

Production startup preflight already rejected several corrupt provider-state cases, but the live runtime/provider-control path remained permissive if state became corrupt after boot or a non-preflight caller evaluated the provider directly.

## R-013 decision

- only an actually absent `market_data_provider.json` may use deployment bootstrap;
- an existing invalid provider-state artifact is a blocking control-plane error;
- no environment fallback is applied while invalid persisted state exists;
- `provider_summary()` reports `BLOCKED`, `ready=false`, and no invented active provider;
- symbol mutations remain unavailable while provider authority is blocked;
- Telegram keeps the explicit Finnhub/Twelve Data provider-selection actions available so an authorized Owner can recover;
- recovery is allowed only through `set_active_provider()` after the requested provider passes API-key readiness validation;
- the recovery write remains atomic and restores `EXCLUSIVE` one-provider semantics.

## Safety boundary

R-013 does not mix providers, broaden Finnhub symbol scope, change Twelve Data symbol selection, change strategy parameters, change scoring/SR/FSM/Execution Time behavior, fabricate market data, enable signal distribution, or enable broker execution.

## Validation targets

- missing-state deployment bootstrap;
- invalid JSON;
- non-object state;
- missing/unsupported provider;
- non-EXCLUSIVE mode;
- no `_apply_provider()` environment fallback on invalid persisted state;
- blocked diagnostic summary;
- failed recovery target leaves corrupt artifact unchanged;
- successful explicit Owner recovery atomically replaces corrupt state;
- Telegram provider selector remains recoverable while symbol mutations are hidden/blocked;
- existing startup-preflight corruption guard remains green;
- focused provider + Telegram tests and full repository suite pass before Ready for Review.
