# R-019 scheduling decision

## Production process and alternatives

The current Railway entry point is one worker-style service: `PYTHONPATH=send python -m scripts.railway_start`, followed by `runtime.system_boot.start_system()`. Existing engine, distribution, telemetry and optional Telegram workers are independent threads.

| Option | Assessment |
| --- | --- |
| Separate Railway scheduled service invoking the auditor CLI | Possible, but adds service configuration, volume sharing/coordination and another lifecycle for the Owner to manage. Historical documentation calls this optional; no active authority requires it. |
| Run inside the existing distribution scheduler | Rejected: expensive report work would stall maintenance and invites accidental reuse of its London reset clock. |
| Run inside the engine loop | Rejected: analytics must not block the two-second signal evaluation boundary. |
| One dedicated, optional runtime worker | Selected: keeps the existing deployment, isolates report work from other loops, and permits deterministic checks and cooperative shutdown without uncontrolled thread creation. |

The CLI remains a supported one-shot entry point. It must use the same run transaction and duplicate protection as the worker, not a bypass.

Both JSON and Markdown are required to complete a governed runtime period, including manual CLI invocation. A single-artifact manual run must not suppress the scheduled two-artifact report. The lower-level report-writing library retains configurable formats for callers that do not claim runtime period completion.

## Schedule authority

The new worker requires explicit enablement and a strictly validated daily UTC `HH:MM`. There is no default clock. Missing schedule is `SCHEDULE_NOT_CONFIGURED`; malformed configuration disables/degrades only the optional auditor. Trading preflight remains independent and unchanged.

The existing 08:10 Europe/London distribution reset is not auditor authority. Historical audit suggestions/examples of 09:00 London are not active configuration either. Neither is adopted. The existing admin auditor-availability feature flag is not a daily schedule and does not silently enable the new worker.

Owner action is to choose and configure the actual UTC clock. DST and the host timezone must not affect eligibility. Aware injected times are converted to UTC; naive times are rejected instead of assuming local time.

| Setting | Meaning |
| --- | --- |
| `STRATEGY_AUDITOR_ENABLED` | Explicit opt-in. Unset/false does not start the worker. Invalid boolean configuration is not silently enabled. |
| `STRATEGY_AUDITOR_DAILY_TIME_UTC` | Owner-selected strict `HH:MM`; unset means no configured schedule. No example clock is presented as a production default. |
| `admin_settings.feature_flags.strategy_auditor_enabled` | Existing `false` value vetoes enablement; `true` alone does not start a scheduled worker. |
| `reports.enabled` | False disables auditor report execution; it is not treated as successful completion. |
| `STRATEGY_AUDITOR_SETTINGS` | Optional selected settings file shared with report consumers; path precedence is specified separately. |

## Report identity versus analytical window

An eligible period is the current UTC date at invocation, not the previous date. Starting after that date's configured time catches up today's missing report only. No historical backfill or force/rebuild command is introduced.

The original report filename and keys remain compatible. The report date is fixed at the start of the attempt even if the build crosses midnight. Schedule identity and attempt identity are additive metadata.

**Important limitation:** the original auditor aggregates all available input records. Daily scheduling does not turn those records into a single-day analytical window. Scheduling metadata/limitations state this explicitly; historical filtering, input rotation and temporal intelligence are outside R-019.

## Idempotency and locking

Completion truth is durable state under `storage.state_path(...)`, not disposable analytics cache. It records the report period, attempt, timestamps, result and artifacts. Successful periods remain skipped across restarts, schedule changes and overlapping callers.

The existing `storage.with_lock(...)` can reclaim a live lock when its deployment ID differs or its age exceeds 300 seconds. It is therefore inappropriate for a potentially long report spanning a Railway redeploy. R-019 instead uses a narrowly scoped, nonblocking in-process guard and a POSIX kernel file lock shared by all auditor callers under the same persistent state authority. The stable lockfile must not be unlinked or reclaimed by deployment/age. The OS releases the lock on process death.

The lock covers eligibility/state checking through source reads, report persistence and completion. Contending processes safely skip. Unsupported locking/storage fails visibly rather than executing unlocked. This assumes a shared persistent filesystem with working POSIX advisory locking; separate unrelated volumes are not coordinated.

## Failure and redeploy behavior

Persist the attempt before expensive work. Completion is recorded only after every required artifact succeeds. Failure preserves the attempt/error and leaves the period incomplete; corrupt state is not silently replaced with fresh success eligibility.

Retries are bounded engineering behavior, not a trading clock: persisted cooldown and per-period attempt limit prevent repeated scheduler checks or restarts from creating a retry storm. Interrupted attempts count toward this budget. Successful artifact publication followed by an interrupted state update must not trigger destructive rebuilding.

The worker checks every 30 seconds. There are at most three started attempts for a UTC period, with a persisted 300-second minimum separation. These constants control operational retry load only; they do not define trading windows or alter the chosen due time.

Shutdown requests cooperative stopping. Forced termination can leave an incomplete attempt, but atomic state/artifact replacement and OS-released locking permit safe restart inspection. No claim is made that a thread's memory survives redeploy.

## Observability without evidence mutation

The five source JSONL files must remain unchanged. Existing canonical warning/error envelopes are built and validated through `core.observability_logger`, then persisted to a separate auditor operational journal rather than using the logger's default error/engine sinks. No event family or schema is added.

Auditor diagnostics are additive and isolated from market/FSM health. Exceptions use bounded sanitized classes/static messages, not raw tracebacks, environment values or secrets. If storage itself fails, safe process diagnostics remain visible; a missing optional schedule never weakens the trading startup gates.

If malformed configuration makes source/write separation impossible to establish, diagnostic persistence must fail closed too: sanitized stderr is safer than modifying an unknown evidence source. This exceptional condition requires Owner configuration repair and is not reported as successful execution.

## Railway implications

No new Railway service, cron definition or broker setting is required. Keep the existing persistent base authority (`BINARYBOT_BASE_DIR`) and choose the explicit auditor enable/time settings. The implementation must not hardcode the production volume mount. Reports/cache are created beneath the resolved analytics authority; completion state remains beneath persistent state. Without persistence, cross-redeploy guarantees cannot be made.

Enablement requires a restart/redeploy so boot starts the optional worker. Do not deploy a separate scheduled auditor service in addition to this worker. The one-shot CLI is still available for operational invocation, with the same persistent duplicate/retry guard.

Real Railway restart/overlap and volume evidence remains an Owner post-merge acceptance step; local deterministic simulations are not represented as production evidence.
