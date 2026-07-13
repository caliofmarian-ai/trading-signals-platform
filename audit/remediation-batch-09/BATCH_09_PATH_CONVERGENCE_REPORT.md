# BATCH_09_PATH_CONVERGENCE_REPORT

## Summary
Two active modules had hardcoded `/opt/binarybot/...` paths that reduced portability and required manual test monkeypatching. Both were converged to use the canonical `storage.root_path()` / `_storage.root_path()` abstraction.

---

## 1. send/core/outcome_service.py

### Before (hardcoded)
```python
OUTCOMES_JSONL = "/opt/binarybot/outcomes/outcomes.jsonl"
OPEN_REGISTRY_JSON = "/opt/binarybot/outcomes/open_now_registry.json"
OUTCOMES_INDEX_JSON = "/opt/binarybot/outcomes/outcomes_index.json"
```

### After (storage-based)
```python
OUTCOMES_JSONL = storage.root_path("outcomes", "outcomes.jsonl")
OPEN_REGISTRY_JSON = storage.root_path("outcomes", "open_now_registry.json")
OUTCOMES_INDEX_JSON = storage.root_path("outcomes", "outcomes_index.json")
```

### Rationale
- `storage` is already imported at the top of the module
- `storage.root_path()` uses `BINARYBOT_BASE_DIR` env var when set; falls back to the `send/` package directory
- Module-level constant names are preserved — existing tests that monkeypatch these attributes continue to work without modification
- Default paths now resolve to `send/outcomes/...` (correct relative to package)

### Test Impact
Tests that monkeypatch via `outcome_service.OUTCOMES_JSONL = str(root / "outcomes" / "outcomes.jsonl")` continue to work — they override the module attribute after import, as before.

---

## 2. send/core/admin_commands.py

### Before (hardcoded)
```python
CONFIG_DIR = "/opt/binarybot/config"
OBS_DIR = "/opt/binarybot/observability"
REPORTS_DIR = "/opt/binarybot/analytics/reports"
ALGO_PARAMS_PATH = os.path.join(CONFIG_DIR, "algo_params.json")
ACTIVE_SYMBOLS_PATH = os.path.join(CONFIG_DIR, "active_symbols.json")
ADMIN_SETTINGS_PATH = os.path.join(CONFIG_DIR, "admin_settings.json")
ADMIN_EVENTS_PATH = os.path.join(OBS_DIR, "admin_events.jsonl")
ADMIN_PROOFS_PATH = os.path.join(OBS_DIR, "admin_proofs.jsonl")
ENGINE_EVENTS_PATH = os.path.join(OBS_DIR, "engine_events.jsonl")
```

### After (storage-based)
```python
CONFIG_DIR = _storage.root_path("config")
OBS_DIR = os.getenv("OBS_DIR", _storage.root_path("observability"))
REPORTS_DIR = os.path.join(os.getenv("ANALYTICS_DIR", _storage.root_path("analytics")), "reports")
ALGO_PARAMS_PATH = os.path.join(CONFIG_DIR, "algo_params.json")
ACTIVE_SYMBOLS_PATH = os.path.join(CONFIG_DIR, "active_symbols.json")
ADMIN_SETTINGS_PATH = os.path.join(CONFIG_DIR, "admin_settings.json")
ADMIN_EVENTS_PATH = os.path.join(os.getenv("OBS_DIR", _storage.root_path("observability")), "admin_events.jsonl")
ADMIN_PROOFS_PATH = os.path.join(os.getenv("OBS_DIR", _storage.root_path("observability")), "admin_proofs.jsonl")
ENGINE_EVENTS_PATH = os.path.join(os.getenv("OBS_DIR", _storage.root_path("observability")), "engine_events.jsonl")
```

### Rationale
- `_storage` (`core.storage`) is already imported at the top of the module
- `CONFIG_DIR` always resolves from storage base dir (no env override needed — test base dir covers it)
- `OBS_DIR`, `REPORTS_DIR` and derived constants respect the `OBS_DIR` / `ANALYTICS_DIR` env vars already used by other modules and tests
- Module-level constant names are preserved — batch_05 tests that `monkeypatch.setattr(ac, "ADMIN_EVENTS_PATH", ...)` continue to work
- `ALGO_PARAMS_PATH` fallback still valid: `_algo_params_path()` prefers `_storage.config_path()` and falls back to `ALGO_PARAMS_PATH` — both now resolve to the same `send/config/algo_params.json`

### Test Impact
All batch_05 admin control plane tests continue to use `monkeypatch.setattr(ac, "ADMIN_EVENTS_PATH", ...)` — no test modifications required.

---

## 3. Residual /opt/binarybot References (Non-Live-Write)

After convergence, remaining `/opt/binarybot` occurrences in `send/` are:
- File-header comments (e.g., `# /opt/binarybot/core/strategy_v2.py`) — documentation only
- `core/observability_logger.py`: env-var overridable defaults (`os.getenv("OBS_DIR", "/opt/binarybot/observability")`) — these pre-date BATCH-09 and are not in BATCH-09 scope
- `core/params_loader.py`: `DEFAULT_PARAMS_PATH = os.getenv("ALGO_PARAMS_PATH", "/opt/binarybot/config/algo_params.json")` — env-var overridable; not a live write
- `core/analytics_engine.py`, `intelligence/research_engine.py`, `intelligence/report_loader.py`: all use env-var overridable defaults
- `core/admin_permissions.py`: env-var fallback for roles config path
- `core/bot_service.py`, `core/distribution_router.py`: existing env-var or multi-path patterns

### Verdict
No remaining active live write paths in BATCH-09 scope target `/opt/binarybot` unconditionally. All remaining occurrences are either comments, env-var overridable defaults, or pre-existing patterns outside BATCH-09 scope that will require separate remediation planning.

## 4. Canonical Segmented-Path Authority Confirmation
- Outcome writes: `outcomes/` segment via `outcome_service.py` (converged)
- Admin audit writes: `observability/` segment via `admin_commands.py` (converged)
- FSM state writes: `state/` segment via `state_store/state_store.py` (already canonical)
- Distribution state writes: `state/` segment via `state_store/state_store.py` (already canonical)
- Observability writes: `observability/` segment via `core/observability_logger.py` (already env-var overridable)
