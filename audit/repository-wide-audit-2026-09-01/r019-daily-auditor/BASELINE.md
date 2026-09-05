# R-019 baseline

## Verified starting point

- Repository: `caliofmarian-ai/trading-signals-platform`; existing issue: #140; parent: #97.
- Fetched main and initial task HEAD: `8037a3dac42a0e1b0c44cb8ab83e3f6f9f5b5f83`.
- Work stays on the supplied dedicated branch `copilot/caliofmarian-ai-r-019-daily-strategy-auditor`, already based on that exact main, rather than creating a second branch/PR.
- GitHub confirms PR #136 merged and Issue #139 closed/completed. R-018 implementation head: `e834e9e66497e635b81a1c3ec279b1939b634bbc`; merge: `1dae636555fcc6fdba6304d65f39b359da013629`.
- GitHub Actions run [33983482998](https://github.com/caliofmarian-ai/trading-signals-platform/actions/runs/33983482998) succeeded on that R-018 implementation head: provider 5, Telegram admin 72, full repository 1142 passed. These are baseline evidence, not R-019 test results.
- R-018 master-plan/validation/open-findings metadata was reconciled first, separately from runtime changes; historical baseline entries remain historical.
- Complete R-019 requirements include [Owner comment 5555082775](https://github.com/caliofmarian-ai/trading-signals-platform/issues/140#issuecomment-5555082775).

## Baseline dependency map

All source locations below are relative to the absolute worktree `/home/runner/work/trading-signals-platform/trading-signals-platform`.

| Boundary | Verified baseline |
| --- | --- |
| Runtime startup | `scripts/railway_start.py:12-25` applies the volume path contract, initializes persisted config, performs readiness, then calls `runtime.system_boot.start_system()`. |
| Live workers | `send/runtime/system_boot.py:351-376` starts engine, distribution scheduler, telemetry and optional Telegram workers. No auditor worker. |
| Existing clock | `send/runtime/distribution_scheduler.py:14-38` resets distribution at 08:10 Europe/London; this is not auditor authority. |
| Auditor invocation | `send/tools/strategy_auditor_daily.py:12-32` is on demand, catches exceptions and prints tracebacks without a machine-readable result or failing exit status. |
| Inputs/config | `send/tools/strategy_auditor_lib.py:31-77` loads settings and applies partial environment overrides; individual observability source overrides depend on `OBS_DIR`. The seed settings hardcode an old deployment root. |
| Path authority | `send/core/storage.py:32-58` owns base/config/state resolution. `scripts/railway_common.py:73-97` derives Railway environment defaults from its base. |
| Reports/cache | `send/config/intelligence_settings.json` names both directories; cache has no auditor computation role. |
| Report meaning | `send/tools/strategy_auditor_lib.py:1027-1106` aggregates all supplied records, labels the report with current UTC date, and does not filter input to one day. |
| Atomic artifacts | `send/tools/strategy_auditor_lib.py:1109-1215` already uses temporary files, fsync and replace per JSON/Markdown file, with cleanup. |
| Consumers | `send/intelligence/report_loader.py` independently defaults to the old root. Admin latest-report and report-browser helpers in `send/core/admin_commands.py` also resolve paths; `send/core/bot_service.py` imports the admin report helper. Research and analytics consume these existing products. |
| Operational evidence | `send/core/observability_logger.py` validates canonical envelopes, but normal error/warning routing writes an auditor input file. R-019 must not use those default sinks for its own execution evidence. |
| Runtime status | `send/runtime/runtime_status.py` stores main runtime state; its read-modify-write update is not an appropriate shared completion ledger. |
| Locking | `send/core/storage.py:197-247` can reclaim a live lock by age or differing deployment identity. That behavior cannot safely guard a long auditor run during overlapping redeploys. |

## Schedule authority audit

No active auditor daily clock was found in current configuration or the active canonical directory. The existing admin feature flag expresses feature availability, not a UTC daily time. Historical readiness reports recommend/example 09:00 London; the production-process model describes a separate auditor job as optional. Neither is a configured runtime schedule. R-019 must require an explicit clock instead of promoting either 09:00 London or the distribution reset to authority.

## Boundaries retained

R-018 normalization, event identity/deduplication, explicit legacy compatibility, NO_SIGNAL, primary reject distribution, blocker occurrences and compatibility metadata remain regression requirements. All five evidence sources stay read-only. No strategy, thresholds, provider selection, permissions, entitlements or broker execution changes are authorized. R-017 (#131/#23) and temporal intelligence (#137) remain separate; R-020 onward is not started.
