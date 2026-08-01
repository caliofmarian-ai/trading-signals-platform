# .gitignore Contract

## Required protections implemented
- Python bytecode and cache directories: `__pycache__/`, `*.pyc`, `*.pyo`, `*.pyd`
- Test and tool caches: `.pytest_cache/`, `.cache/`, `.mypy_cache/`, `.ruff_cache/`
- Local virtual environments: `venv/`, `.venv/`, `env/`, `ENV/`
- Runtime logs: `*.log`, `engine.log`
- Runtime observability/output paths:
  - `send/observability/*.jsonl`
  - `send/outcomes/*.jsonl`
  - `send/outcomes/open_now_registry.json`
  - `send/outcomes/outcomes_index.json`
  - `send/state/*.json`
  - `send/analytics/cache/`
  - `send/analytics/reports/daily_strategy_audit_*.json`
  - `send/analytics/reports/daily_strategy_audit_*.md`
- Temporary/local artifacts: `tmp_decision_*`, `*.tmp`, `*.temp`, `*~`, `send/config/*.bak.*`, `send/config/.env.example`
- Editor / OS artifacts: `.idea/`, `.vscode/`, `*.swp`, `*.swo`, `.DS_Store`, `Thumbs.db`

## Enforcement checks
- `tests/batch_10/test_repository_hygiene.py` asserts the ignore contract strings remain present.
- `pytest.ini` disables pytest's cache provider so the suite does not regenerate `.pytest_cache/`.
- `tests/conftest.py` sets `sys.dont_write_bytecode = True` so imports do not rewrite tracked `__pycache__` trees.
