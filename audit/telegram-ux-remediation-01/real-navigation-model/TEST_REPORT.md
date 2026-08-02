# Test Report

## Required command log

| Scope | Exact command | Actual result |
|---|---|---|
| Focused Issue #38 tests | `PYTHONPATH=send python -m pytest -q tests/telegram_app/test_real_navigation.py` | `86 passed in 2.61s` |
| Telegram application tests | `PYTHONPATH=send python -m pytest -q tests/telegram_app` | `187 passed in 3.79s` |
| Telegram admin UI tests | `PYTHONPATH=send python -m pytest -q tests/telegram_admin_ui_restoration/test_admin_ui_restoration.py` | `72 passed in 1.65s` |
| Telegram transport / recovery tests | `PYTHONPATH=send python -m pytest -q tests/telegram_transport/test_telegram_transport_and_recovery.py` | `22 passed in 0.34s` |
| Issue #31 start / restart / redeploy regressions | `PYTHONPATH=send python -m pytest -q tests/canonical/unit/test_start_hard_reset_visibility.py tests/canonical/unit/test_restart_redeploy_recovery.py tests/batch_06/test_fsm_restart_recovery.py` | `82 passed in 2.01s` |
| Railway tests | `PYTHONPATH=send python -m pytest -q tests/batch_10/test_railway_deployment_preparation.py` | `31 passed in 2.39s` |
| Complete repository suite | `PYTHONPATH=send python -m pytest -q tests` | `722 passed in 18.88s` |
| Clean-tree check | `git status --short` | `Pending final commit/push verification.` |
| Secret scan | `runtime-tools-secret_scanning` on the full PR file list | `No secrets detected in the scanned files.` |
| CodeQL / static analysis | `codeql_checker` | `Pending final CodeQL rerun after the last documentation commit.` |

## Supporting regression command

| Scope | Exact command | Actual result |
|---|---|---|
| Admin control plane regression | `PYTHONPATH=send python -m pytest -q tests/batch_05/test_admin_control_plane.py` | `55 passed in 1.12s` |
