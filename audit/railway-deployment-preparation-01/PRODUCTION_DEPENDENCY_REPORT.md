# PRODUCTION_DEPENDENCY_REPORT.md

## Supported Python
- Python `3.12.3` (`runtime.txt`).

## Production dependency file
- `requirements.txt`
- Declared package: `requests==2.31.0`

## Inventory result
Active runtime code paths inspected:
- `send/runtime/`
- `send/core/`
- `send/state_store/`
- `send/monitoring/`
- `send/snapshots/`
- `send/intelligence/`
- `send/tools/strategy_auditor_daily.py`
- `send/tools/strategy_auditor_lib.py`

Third-party runtime dependency required by active code:
- `requests` — Telegram and Twelve Data HTTP client.

Excluded from production requirements:
- test-only dependency `pytest` remains in `requirements-test.txt`
- archived / historical `send/venv`
- deprecated / inactive code

## Validation
- Clean virtualenv install with only `requirements.txt`: passed.
- Active deployment modules imported with only production requirements: passed.
