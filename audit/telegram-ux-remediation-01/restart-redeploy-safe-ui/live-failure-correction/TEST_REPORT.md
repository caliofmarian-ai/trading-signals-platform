# Test Report

## Initial independent verification failure (Termux)
- PR #33 independent verification failed in Termux before Railway/full-suite execution.
- Failing test: `tests/telegram_app/test_telegram_app_nav_persistence.py::test_stale_cross_instance_updates_preserve_independent_sessions`.
- Root cause: hard-coded Copilot/GitHub runner checkout path to `send/core/telegram_app_nav.py` inside the test.
- Independent run status at failure point: **69 passed, 1 failed**.

## Targeted corrective tests
- `PYTHONPATH=send python -m pytest -q tests/telegram_app/test_telegram_app_nav_persistence.py tests/telegram_transport/test_telegram_transport_and_recovery.py tests/canonical/unit/test_telegram_runtime_remediation.py`
  - Result: **71 passed**
- `PYTHONPATH=send python -m pytest -q tests/batch_10/test_railway_deployment_preparation.py`
  - Result: **31 passed**
- `PYTHONPATH=send python -m pytest -q tests`
  - Result: **531 passed**

## Repository-wide checkout-path scan
- Command:
  - `grep -RIn -e '/home/runner/work/' -e '/github/workspace/' -e '/workspace/' --exclude-dir=.git .`
- Result:
  - Matches found only in historical documentation/audit markdown files.
  - No executable source or test file matches remained.

## Status note
- PR #33 required corrective follow-up after Termux failure.
- The stale cross-instance persistence test is now checkout-location independent.
