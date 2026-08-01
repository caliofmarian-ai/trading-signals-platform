# Keep / Remove Decisions

## Keep decisions
1. **Keep `/.env.example`.** Evidence: `tests/batch_10/test_railway_deployment_preparation.py:204-227` reads only the root file, and Railway preparation docs reference `/.env.example`.
2. **Keep `railway.json`.** Evidence: `railway.json:1-14` is the deployment contract used by Railway.
3. **Keep the eight tracked seed config JSON files under `send/config/`.** Evidence: `scripts/railway_common.py:10-19` defines `CONFIG_SEED_FILES`; `scripts/railway_init.py:93-103` seeds exactly those files.
4. **Keep test fixtures and canonical runtime setup.** Evidence: `tests/canonical/conftest.py:29-72` copies canonical config into a temp runtime root and does not depend on tracked runtime output.

## Remove decisions
1. **Remove tracked bytecode and `__pycache__` trees.** Evidence: generated interpreter output; already covered by ignore policy and never named as canonical fixtures.
2. **Remove `send/venv/`.** Evidence: local virtual environment binaries and site-packages from `git ls-files send/venv`; not referenced by runtime or tests.
3. **Remove `send/observability/*.jsonl`.** Evidence: live event payloads were present in these files, and `send/core/observability_logger.py:38-145` writes them at runtime.
4. **Remove `send/outcomes/outcomes.jsonl` and `send/outcomes/open_now_registry.json`.** Evidence: `send/core/outcome_service.py:15-17,50-75` treats them as mutable runtime stores.
5. **Remove `send/state/*.json`.** Evidence: `send/state_store/state_store.py:58-63,106-116` treats them as mutable runtime state files; `scripts/railway_healthcheck.py:47-55` validates them only if present under the runtime volume.
6. **Remove `send/analytics/reports/daily_strategy_audit_2026-03-06.json|md`.** Evidence: `send/tools/strategy_auditor_lib.py:467-532` generates these reports into `analytics/reports`.
7. **Remove `send/config/.env.example`.** Evidence: empty duplicate artifact; canonical env template is root `/.env.example`.
8. **Remove `send/config/channel_config.json.bak.1772746111`.** Evidence: backup artifact not listed in `CONFIG_SEED_FILES` and not referenced by tests or runtime initialization.

## Do-not-remove decisions validated during audit
- Do **not** remove `send/config/admin_permissions.json`, `admin_roles.json`, `admin_settings.json`, `algo_params.json`, `channel_config.json`, `intelligence_settings.json`, `symbols.json`, or canonical `active_symbols.json`; Railway init and canonical fixtures depend on them.
- Do **not** remove Railway scripts or tests; they are the authoritative verification path for deployment preparation.
