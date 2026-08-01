# TEST REPORT

## Targeted test run

File: `tests/telegram_transport/test_telegram_transport_and_recovery.py`

```
============================= test session starts ==============================
platform linux -- Python 3.12.3, pytest-9.1.1, pluggy-1.6.0
rootdir: trading-signals-platform
configfile: pytest.ini
collected 18 items

tests/telegram_transport/test_telegram_transport_and_recovery.py::test_01_send_message_no_parse_mode PASSED
tests/telegram_transport/test_telegram_transport_and_recovery.py::test_02_edit_message_no_parse_mode PASSED
tests/telegram_transport/test_telegram_transport_and_recovery.py::test_03_parse_mode_consistent PASSED
tests/telegram_transport/test_telegram_transport_and_recovery.py::test_04_engine_command_edits_start_message PASSED
tests/telegram_transport/test_telegram_transport_and_recovery.py::test_05_admin_button_edits_engine_message PASSED
tests/telegram_transport/test_telegram_transport_and_recovery.py::test_06_full_navigation_single_message PASSED
tests/telegram_transport/test_telegram_transport_and_recovery.py::test_07_deleted_active_message_replacement PASSED
tests/telegram_transport/test_telegram_transport_and_recovery.py::test_08_replacement_becomes_active PASSED
tests/telegram_transport/test_telegram_transport_and_recovery.py::test_09_deleted_conversation_start_responds PASSED
tests/telegram_transport/test_telegram_transport_and_recovery.py::test_10_stale_edit_then_successful_send PASSED
tests/telegram_transport/test_telegram_transport_and_recovery.py::test_11_failed_edit_and_send_not_silent PASSED
tests/telegram_transport/test_telegram_transport_and_recovery.py::test_12_unexpected_edit_does_not_corrupt_state PASSED
tests/telegram_transport/test_telegram_transport_and_recovery.py::test_13_poller_continues_after_failure PASSED
tests/telegram_transport/test_telegram_transport_and_recovery.py::test_14_railway_safe_log_line PASSED
tests/telegram_transport/test_telegram_transport_and_recovery.py::test_15_token_not_in_logs PASSED
tests/telegram_transport/test_telegram_transport_and_recovery.py::test_16_jsonl_logging_works PASSED
tests/telegram_transport/test_telegram_transport_and_recovery.py::test_17_session_isolation PASSED
tests/telegram_transport/test_telegram_transport_and_recovery.py::test_18_full_e2e_single_message PASSED

============================== 18 passed in 0.25s ==============================
```

## Full suite run

```
517 passed in 12.83s
```

Baseline (main, before this branch): 499 passed.
This branch adds 18 new tests; all 517 pass.  No regressions.
