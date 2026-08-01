# Test Report

## Targeted tests
- Command:
  - `PYTHONPATH=send python -m pytest -q tests/telegram_app/test_telegram_app_nav.py tests/telegram_app/test_e2e_application.py tests/canonical/unit/test_telegram_runtime_remediation.py`
- Result:
  - `102 passed`

## Complete suite
- Command:
  - `PYTHONPATH=send python -m pytest -q tests`
- Result:
  - `487 passed`

## Live acceptance regression coverage
- Added automated coverage for:
  - repeated `/status` in the same session (`message is not modified` no-op),
  - repeated identical `APP:STATUS` callback in the same session,
  - duplicate rapid `/status` requests,
  - stale/deleted active message fallback sending one replacement,
  - active session tracking preservation after no-op edit.
