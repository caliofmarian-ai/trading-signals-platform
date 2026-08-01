# Test Report

## Targeted tests
1. `PYTHONPATH=send python -m pytest -q tests/telegram_app/test_telegram_app_nav.py tests/telegram_app/test_telegram_app_nav_persistence.py tests/telegram_transport/test_telegram_transport_and_recovery.py`
   - Result: **66 passed**
2. `PYTHONPATH=send python -m pytest -q tests/batch_10/test_railway_deployment_preparation.py`
   - Result: **31 passed**

## Full repository suite
- `PYTHONPATH=send python -m pytest -q tests`
- Result: **524 passed**

## Security validation
- Secret scan:
  - Tool: `runtime-tools-secret_scanning`
  - Result: **No secrets detected**
- CodeQL:
  - Tool: `codeql_checker`
  - Result: **0 alerts**
