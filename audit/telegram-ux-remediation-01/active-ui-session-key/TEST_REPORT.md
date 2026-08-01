# Test Report

## Targeted tests
- Command:
  - `PYTHONPATH=send python -m pytest -q tests/telegram_app/test_telegram_app_nav.py tests/telegram_app/test_e2e_application.py`
- Result:
  - `75 passed`

## Complete suite
- Command:
  - `PYTHONPATH=send python -m pytest -q tests`
- Result:
  - `483 passed`
