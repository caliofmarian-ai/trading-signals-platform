# PERSISTENT_VOLUME_CONTRACT.md

## Recommendation
- Attach **one Railway volume**.
- Recommended mount path: `/data`.
- Set `BINARYBOT_BASE_DIR=/data`.

## Persisted directories
- `/data/config`
- `/data/state`
- `/data/outcomes`
- `/data/observability`
- `/data/analytics`
- `/data/snapshots`

## Persisted files of note
- config: `algo_params.json`, `channel_config.json`, `admin_roles.json`, `admin_permissions.json`, `admin_settings.json`, `active_symbols.json`, `intelligence_settings.json`, `symbols.json`
- state: `focus_state.json`, `dist_state.json`, `restart_guard.json`, `runtime_status.json`, `outcomes.json`, `trade_journal.json`
- append-only logs: `outcomes/outcomes.jsonl`, `observability/*.jsonl`
- analytics outputs: `analytics/aggregates.json`, `analytics/research_report.json`, `analytics/reports/*`, `analytics/cache/*`

## Mount assumptions
- The volume root must be writable.
- Redeployments must reuse the same mounted volume to preserve state, logs, analytics, and config.

## Without a volume
- Railway start is unsupported for production shadow mode.
- `scripts.railway_start` fails clearly when `BINARYBOT_BASE_DIR` is absent.

## Seeding / redeploy / rollback behavior
- First deploy: `scripts.railway_init` creates directories and seeds missing config files.
- Redeploy: existing config is preserved; state is preserved; init is idempotent.
- Rollback: keep the same volume; redeploy the previous code revision; do not delete the volume unless intentionally resetting all runtime state.
- Backup/export: copy the mounted volume contents before destructive changes.
