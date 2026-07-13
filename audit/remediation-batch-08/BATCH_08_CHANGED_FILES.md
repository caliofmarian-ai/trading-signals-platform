# BATCH_08_CHANGED_FILES

## Created
- `requirements-test.txt`
- `pytest.ini`
- `tests/canonical/conftest.py`
- `tests/canonical/helpers/builders.py`
- `tests/canonical/helpers/io.py`
- `tests/canonical/fakes/fake_publisher.py`
- `tests/canonical/unit/test_boot_and_market_data.py`
- `tests/canonical/unit/test_strategy_and_corridor.py`
- `tests/canonical/contract/test_config_and_signal_contracts.py`
- `tests/canonical/contract/test_telegram_adapter_boundary.py`
- `tests/canonical/integration/test_fsm_distribution_outcome_integration.py`
- `tests/canonical/security/test_security_boundaries.py`
- `tests/canonical/failure_recovery/test_failure_injection_behaviors.py`
- `tests/canonical/persistence/test_state_snapshot_recovery.py`
- `tests/canonical/end_to_end/test_offline_end_to_end_flows.py`
- `audit/remediation-batch-08/BATCH_08_BASELINE_TEST_INVENTORY.md`
- `audit/remediation-batch-08/BATCH_08_CANONICAL_ACCEPTANCE_CRITERIA.md`
- `audit/remediation-batch-08/BATCH_08_TEST_ARCHITECTURE.md`
- `audit/remediation-batch-08/BATCH_08_REQUIREMENT_TO_TEST_TRACEABILITY.md`
- `audit/remediation-batch-08/BATCH_08_INVARIANT_COVERAGE.md`
- `audit/remediation-batch-08/BATCH_08_END_TO_END_FLOW_COVERAGE.md`
- `audit/remediation-batch-08/BATCH_08_FAILURE_INJECTION_COVERAGE.md`
- `audit/remediation-batch-08/BATCH_08_IMPLEMENTATION_REPORT.md`
- `audit/remediation-batch-08/BATCH_08_VALIDATION_REPORT.md`
- `audit/remediation-batch-08/BATCH_08_CHANGED_FILES.md`
- `audit/remediation-batch-08/BATCH_08_OPEN_FINDINGS.md`

## Modified
- `README.md`
- `tests/canonical/conftest.py` (post-create refinements)
- `tests/canonical/integration/test_fsm_distribution_outcome_integration.py` (path-wiring + assertion refinement)
- `tests/canonical/security/test_security_boundaries.py` (outcome path wiring)
- `tests/canonical/failure_recovery/test_failure_injection_behaviors.py` (outcome path wiring)
- `tests/canonical/end_to_end/test_offline_end_to_end_flows.py` (stability and auth-fixture refinements)

## Not changed
- No deployment workflows
- No Railway config
- No broker/live credentials
- No canonical source docs under `send/docs/canonical/active/`
