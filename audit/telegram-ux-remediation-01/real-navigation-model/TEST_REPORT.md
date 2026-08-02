# Test Report

## Required command log

| Scope | Exact command | Actual result |
|---|---|---|
| Focused Issue #38 tests | `PYTHONPATH=send python -m pytest -q tests/telegram_app/test_real_navigation.py` | `70 passed in 0.56s` |
| Telegram application tests | `PYTHONPATH=send python -m pytest -q tests/telegram_app` | `171 passed in 1.81s` |
| Telegram admin UI tests | `PYTHONPATH=send python -m pytest -q tests/telegram_admin_ui_restoration/test_admin_ui_restoration.py` | `72 passed in 0.42s` |
| Telegram transport / recovery tests | `PYTHONPATH=send python -m pytest -q tests/telegram_transport/test_telegram_transport_and_recovery.py` | `22 passed in 0.49s` |
| Issue #31 start / restart / redeploy regressions | `PYTHONPATH=send python -m pytest -q tests/canonical/unit/test_start_hard_reset_visibility.py tests/canonical/unit/test_restart_redeploy_recovery.py tests/batch_06/test_fsm_restart_recovery.py` | `82 passed in 0.90s` |
| Railway tests | `PYTHONPATH=send python -m pytest -q tests/batch_10/test_railway_deployment_preparation.py` | `31 passed in 0.79s` |
| Complete repository suite | `PYTHONPATH=send python -m pytest -q tests` | `706 passed in 9.59s` |
| Clean-tree check | `git status --short` | `0 lines expected after final commit/push verification` |
| Secret scan | `runtime-tools-secret_scanning` on the full PR file list | `No secrets detected in the scanned files.` |
| CodeQL / static analysis | `codeql_checker` | `Analysis Result for 'python': Found 0 alerts.` |

## Supporting regression command

| Scope | Exact command | Actual result |
|---|---|---|
| Admin control plane regression | `PYTHONPATH=send python -m pytest -q tests/batch_05/test_admin_control_plane.py` | `55 passed in 0.28s` |
