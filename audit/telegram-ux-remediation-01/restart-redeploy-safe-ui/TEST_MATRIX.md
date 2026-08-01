# Test Matrix

| Area | Coverage |
|---|---|
| Module reload recovery | `tests/telegram_app/test_telegram_app_nav_persistence.py::test_active_ui_persists_across_module_reload` |
| Process restart reuse | `tests/telegram_transport/test_telegram_transport_and_recovery.py::test_19_restart_reuses_persisted_active_message` |
| Restart with deleted message | `tests/telegram_transport/test_telegram_transport_and_recovery.py::test_20_restart_with_deleted_message_generates_single_replacement` |
| Corrupt persistence safety | `tests/telegram_app/test_telegram_app_nav_persistence.py::test_corrupt_persistence_does_not_break_startup` |
| Unsupported schema safety | `tests/telegram_app/test_telegram_app_nav_persistence.py::test_unsupported_schema_recovers_safely` |
| Retention cleanup | `tests/telegram_app/test_telegram_app_nav_persistence.py::test_retention_and_abandoned_cleanup_on_load` |
| Atomic writes / temp cleanup | `tests/telegram_app/test_telegram_app_nav_persistence.py::test_concurrent_updates_are_safe_and_atomic` |
| Concurrent updates | `tests/telegram_app/test_telegram_app_nav_persistence.py::test_concurrent_updates_are_safe_and_atomic` |
| Message reuse / replacement generation | tests 19/20 above |
| Multi chat/user/thread isolation | existing + persisted tests in `test_telegram_app_nav.py`, `test_telegram_transport_and_recovery.py` |
| Permission boundaries and role isolation | `tests/canonical/unit/test_telegram_runtime_remediation.py` admin-context/role tests |
| Shutdown/startup cycle and Railway startup behavior | existing `tests/canonical/unit/test_telegram_runtime_remediation.py` startup notification tests + `tests/batch_10/test_railway_deployment_preparation.py` |
| Full Telegram navigation after restart | covered by test 19 and existing single-message end-to-end journey tests |
