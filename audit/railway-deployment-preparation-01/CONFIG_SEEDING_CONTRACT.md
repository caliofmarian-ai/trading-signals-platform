# CONFIG_SEEDING_CONTRACT.md

## Script
- `scripts/railway_init.py`

## Behavior
- Resolves `BINARYBOT_BASE_DIR` from the environment.
- Derives all path overrides from that root.
- Creates required runtime directories.
- Seeds missing config files from `send/config/` only when absent.
- Never overwrites existing config files.
- Validates seeded or preserved config before success.
- Fails non-zero on invalid existing config or missing required seed sources.
- Performs no network calls.
- Emits only safe counts and paths; secrets are never logged.

## Seeded files
- `active_symbols.json`
- `admin_permissions.json`
- `admin_roles.json`
- `admin_settings.json`
- `algo_params.json`
- `channel_config.json`
- `intelligence_settings.json`
- `symbols.json`

## Validation path
- algo params: `core.params_loader.load_algo_params`
- runtime settings: `state_store.state_store.load_settings`
- active symbols: `state_store.state_store.load_active_symbols`
- admin role/permission files: strict JSON-object validation + `core.admin_permissions.reload_*`
- strategy auditor settings: `tools.strategy_auditor_lib.load_settings`
- distribution config: `core.distribution_router.load_config`
