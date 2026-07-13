# BATCH_08_BASELINE_TEST_INVENTORY

## Owner approval
- Owner approval for BATCH-08: **applied** (per task statement).
- Target finding: **GAP-017**.

## Preconditions verification
1. BATCH-01..BATCH-07 tests present: **verified** (`tests/batch_01` .. `tests/batch_07`).
2. Stable test runner/deps before changes: repository lacked pinned test dependency file; added `requirements-test.txt` with `pytest==9.1.1`.
3. Baseline regression check for BATCH-01..BATCH-07: **no material regression detected**.

## Baseline full-suite run (before BATCH-08 changes)
- Command: `PYTHONPATH=send python -m pytest -q tests`
- Result: **205 passed, 0 failed, 0 skipped, 0 xfailed, 6 warnings**
- Duration: **1.46s**
- Environment:
  - Python `3.12.3`
  - Linux `6.17.0-1018-azure` (Ubuntu)

## Existing test tree inventory before BATCH-08
| File | Tests | Batch origin | Primary subsystem |
|---|---:|---|---|
| `tests/batch_01/test_boot_and_import_stabilization.py` | 7 | BATCH-01 | boot/import/storage |
| `tests/batch_02/test_canonical_parameter_contract.py` | 51 | BATCH-02 | params/schema/strategy contract |
| `tests/batch_03/test_distribution_observability_interface_repair.py` | 13 | BATCH-03 | distribution/observability |
| `tests/batch_04/test_canonical_outcome_and_telemetry_flow.py` | 13 | BATCH-04 | outcome + telemetry |
| `tests/batch_05/test_admin_control_plane.py` | 55 | BATCH-05 | admin/control-plane/rbac |
| `tests/batch_06/test_fsm_restart_recovery.py` | 14 | BATCH-06 | fsm/restart/state/snapshots |
| `tests/batch_07/test_analytics_research_toolchain.py` | 52 | BATCH-07 | analytics/research/auditor |

Total pre-existing tests: **205**.

## Baseline coverage observations (pre-BATCH-08)
- Strong coverage already existed for prior remediated domains.
- GAP-017 persisted because canonical acceptance evidence was fragmented by batch and lacked a unified canonical test architecture + explicit requirement/invariant traceability package.
- Key remaining gaps identified pre-BATCH-08:
  - explicit canonical `tests/canonical/` structure,
  - consolidated offline end-to-end lifecycle proof set,
  - explicit requirement-to-test and invariant-to-test mapping artifacts,
  - formalized failure-injection evidence package.

## Existing test quality and risk notes
- Duplicate/near-duplicate intent: minimal; mostly complementary batch scenarios.
- Weak assertion-only/import-only tests: present in small number (sanity guards), retained as regression guards.
- Nondeterministic/environment-dependent behavior: mostly mitigated in existing batches using temp paths and monkeypatching; no flaky behavior observed in repeated baseline run.
- Hidden network assumptions: mitigated in prior batches but not centrally enforced for a canonical test tree before BATCH-08.
