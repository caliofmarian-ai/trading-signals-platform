# R-019 path authority

## Base authority

`core.storage.base_dir()` / `root_path(...)` remain the authority. A configured `BINARYBOT_BASE_DIR` must resolve to an existing absolute directory. Malformed, relative or unavailable configured bases fail explicitly; they do not fall back to a different deployment root. Without a configured base, the existing local package-root default remains available.

The production mount is supplied by configuration, not embedded in auditor code. All examples below use `BASE` for the resolved base, not a literal directory name.

## Settings file precedence

1. Explicit `load_settings(path=...)` argument.
2. Explicit `STRATEGY_AUDITOR_SETTINGS`.
3. Runtime-base `config/intelligence_settings.json`, when present.
4. Packaged seed settings only when no explicit file was requested and the runtime-base file is absent.

An invalid/unreadable selected settings file fails; it is not replaced or silently ignored.

## Effective data-path precedence

Retain the established environment-override contract:

| Path | Highest precedence | Then | Runtime default |
| --- | --- | --- | --- |
| Reports | `ANALYTICS_DIR` plus `reports` | `reports.output_dir` in selected settings | `BASE/analytics/reports` |
| Cache | `ANALYTICS_DIR` plus `cache` | `reports.cache_dir` | `BASE/analytics/cache` |
| Engine source | `ENGINE_EVENTS_LOG` | `OBS_DIR/engine_events.jsonl`, then `sources.engine_events` | `BASE/observability/engine_events.jsonl` |
| FSM source | `FSM_EVENTS_LOG` | `OBS_DIR/fsm_events.jsonl`, then `sources.fsm_events` | `BASE/observability/fsm_events.jsonl` |
| Distribution source | `DIST_EVENTS_LOG` | `OBS_DIR/distribution_events.jsonl`, then `sources.distribution_events` | `BASE/observability/distribution_events.jsonl` |
| Error source | `ERROR_EVENTS_LOG` | `OBS_DIR/error_events.jsonl`, then `sources.error_events` | `BASE/observability/error_events.jsonl` |
| Outcomes source | `OUTCOMES_LOG` | `sources.outcomes` | `BASE/outcomes/outcomes.jsonl` |

Individual source environment overrides work without `OBS_DIR`. Explicit environment paths must be absolute. Settings paths may be logical relative paths rooted at `BASE`, or intentional absolute overrides; malformed paths and traversal must not silently escape the intended authority.

Reports/cache directories are created when needed. Missing source files retain the auditor's existing empty-input semantics; permission/read failures are not treated as empty data.

## Reader and writer agreement

The default auditor writer, intelligence report loader, Admin report summary and report-browser path use the same effective reports authority. Selecting an alternative settings file through the environment applies to both writer and default reader. An explicit per-call settings/path override affects only that call; callers must pass the same override to consumers when not using shared configuration.

Existing report filenames and report keys remain compatible. No change grants new Telegram roles or permissions; file-delivery checks remain enforced.

## Persistent operational state

Scheduling/completion state and the stable cross-process lock remain below `BASE/state`, independent of analytics/cache:

- `BASE/state/strategy_auditor_state.json`: period/attempt/completion ledger.
- `BASE/state/strategy_auditor_status.json`: bounded diagnostic snapshot, not completion authority.
- `BASE/state/strategy_auditor.lock`: stable kernel-lock inode, never age/deployment reclaimed.
- `BASE/observability/strategy_auditor_events.jsonl`: dedicated canonical operational journal, not an auditor input.

These destinations follow the base directly; source `OBS_DIR` overrides do not relocate the operational journal.

Source and writable destinations must not alias: configured sources are validated against report, state, lock and journal destinations before auditor writes. Cache is only a directory contract and is not governance-critical completion storage.

## Railway and legacy configuration

The existing Railway path contract fills missing environment paths from the persistent base before importing runtime workers. That contract overrides old seed paths in an already-persisted settings file without rewriting Owner configuration. New packaged settings use runtime-relative paths.

For local/direct callers without those Railway environment defaults, only the known former default settings values under the legacy installation prefix are mapped to the active base. The match is field-specific, not a blanket rewrite of arbitrary absolute paths. Explicit absolute environment overrides are never legacy-remapped; auditor readers must follow the same literal override as the event producers.

Intentional absolute environment overrides remain operational choices: the Owner is responsible for mounting those locations if persistence is required. No path remapping can make an unmounted external location durable.

Unavailable report/cache/state paths produce observable auditor failure without weakening the separate trading preflight.

An intentionally external reports directory remains readable by the intelligence/report-summary consumer. Telegram file downloads remain confined to the runtime base; configuring an external reports directory does not widen file-delivery authorization.
