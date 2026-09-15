# Issue #174 — Telegram startup observability correction

## Live symptom

Railway production deployment `9c59d1d4-4e85-4520-b50a-0a120325baef` was terminal `SUCCESS`, but its healthy startup diagnostics were surfaced as `severity=error`:

- `TELEGRAM_UI_STATE_INITIALIZED` with persisted-state payload `status=ok`;
- `poller_started` with `active_ui_initialized=true`.

The same poller event reported `runtime_instance_id=replace-me` while the real Railway deployment ID was available separately.

## Root cause

1. `core.telegram_app_nav` emits its diagnostic JSON through stderr, including the healthy initialization event.
2. `runtime.telegram_updates._emit_poller_startup()` emitted every startup state through stderr and recorded every event through the warning sink, including healthy `poller_started`.
3. `runtime.telegram_updates._runtime_instance_id()` preferred generic `RUN_ID` before Railway's immutable deployment ID.

## Correction

- `runtime.telegram_updates._runtime_instance_id()` now prefers `RAILWAY_DEPLOYMENT_ID`, then `RAILWAY_SERVICE_ID`, then generic `RUN_ID`.
- healthy `poller_started` is emitted on stdout and is not written through the warning sink;
- non-healthy poller startup states such as `duplicate_poller_blocked` remain on stderr and continue to use `log_warning`;
- Railway startup installs a narrow stream adapter around the existing Telegram UI diagnostic emitter. Only `TELEGRAM_UI_STATE_INITIALIZED` with `status` in `ok`, `deferred`, or `skipped` is redirected from stderr to stdout. All warning/error diagnostics keep the original stderr behavior.

The stream adapter intentionally avoids rewriting the 56 KB navigation module solely for a Railway stream-boundary correction; the existing diagnostic payload construction remains the source of truth.

## Regression coverage

`tests/canonical/unit/test_issue174_startup_observability.py` verifies:

- Railway deployment ID precedence over placeholder `RUN_ID`;
- healthy poller startup uses stdout and creates no warning record;
- duplicate-poller evidence remains stderr + warning-log visible;
- the Railway UI stream adapter is idempotent;
- only healthy UI initialization is redirected to stdout while failed UI diagnostics remain stderr.

## Safety boundary

This change does not alter Telegram routing, callback behavior, role permissions, Admin context, strategy math, provider behavior, signal distribution, market-data policy, persistence semantics, or broker execution.

## Acceptance

Before merge:

1. exact-head `Required Repository CI` must pass;
2. full repository suite must pass;
3. diff must remain observability-only.

After merge/deploy:

1. Railway deployment must reach terminal `SUCCESS` on the exact merged commit;
2. `TELEGRAM_UI_STATE_INITIALIZED` healthy payload should no longer appear as a Railway error-severity stderr line;
3. `poller_started` should no longer appear as error severity;
4. `runtime_instance_id` should equal the real Railway deployment ID when that variable is available;
5. genuine warning/failure diagnostics must remain observable.
