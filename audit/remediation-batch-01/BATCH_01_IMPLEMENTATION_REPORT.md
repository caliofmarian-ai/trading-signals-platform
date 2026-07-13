# BATCH-01 Implementation Report

## Batch
- Batch ID: BATCH-01
- Objective: boot and import stabilization
- Findings addressed: GAP-003, CON-001

## Root cause
- `send/core/signal_engine.py` imported `config_path()` from `send/core/storage.py`, but that helper did not exist.
- Importing the core runtime also depended on import-time Telegram token checks and a top-level import of the deferred `trade_temporal_telemetry` module.
- Those import-time failures prevented `core.signal_engine`, `runtime.engine_loop`, and `runtime.system_boot` from loading deterministically.

## Selected solution
- Added a deterministic storage path contract in `send/core/storage.py`:
  - repository-relative default base directory;
  - explicit `BINARYBOT_BASE_DIR` override with clear validation errors;
  - shared `config_path()` helper.
- Deferred Telegram token resolution in the Telegram runtime helpers so imports stay side-effect free.
- Deferred `trade_temporal_telemetry` loading to OPEN_NOW execution time and converted the missing-module case into a clear actionable runtime error message, without implementing the deferred module itself.
- Updated boot env-file discovery to support deterministic repository-relative startup (`send/.env` then `send/config/.env`) plus explicit `BINARYBOT_ENV_FILE`.

## Canonical basis
- `send/docs/canonical/active/MODULE_INTERFACE_SPEC_v2.0.0.md`
  - `storage.py` owns persistence/path interface concerns.
  - `signal_engine.py` must remain within its module boundary.
- `send/docs/canonical/active/SYSTEM_ARCHITECTURE_MAP_v2.0.0.md`
  - runtime entrypoints must remain layered and bootable through canonical boundaries.
- `send/docs/canonical/active/SIGNAL_ENGINE_EXECUTION_SPEC_v2.0.0.md`
  - signal execution must remain a governed execution layer, not fail before the execution path is reached.
- `audit/deep-code-canon-audit-01/REMEDIATION_BATCH_PLAN.md`
- `audit/deep-code-canon-audit-01/REMEDIATION_DEPENDENCY_GRAPH.md`
- `audit/deep-code-canon-audit-01/IMPLEMENTATION_GAP_REGISTER.md`
- `audit/deep-code-canon-audit-01/CANON_CONTRADICTION_REGISTER.md`
- `audit/deep-code-canon-audit-01/END_TO_END_FLOW_TRACE_REPORT.md`

## Files modified
- `send/core/storage.py`
- `send/core/signal_engine.py`
- `send/core/telegram_publisher.py`
- `send/runtime/system_boot.py`
- `send/runtime/telegram_updates.py`

## Files created
- `tests/batch_01/test_boot_and_import_stabilization.py`
- `audit/remediation-batch-01/BATCH_01_IMPLEMENTATION_REPORT.md`
- `audit/remediation-batch-01/BATCH_01_VALIDATION_REPORT.md`
- `audit/remediation-batch-01/BATCH_01_CHANGED_FILES.md`
- `audit/remediation-batch-01/BATCH_01_OPEN_FINDINGS.md`

## Tests created
- `tests/batch_01/test_boot_and_import_stabilization.py`
  - storage import smoke
  - deterministic config-path resolution
  - environment override contract
  - invalid override failure clarity
  - side-effect-free imports for `core.signal_engine`, `runtime.engine_loop`, `runtime.system_boot`
  - clean-environment config resolution
  - params-loader behavior regression coverage

## Findings intentionally deferred
- GAP-001 / CON-002: missing `trade_temporal_telemetry` implementation remains open by prior governance.
- GAP-002: missing `scan_scheduler` remains open and untouched.
- GAP-004 and all later batches remain out of scope for BATCH-01.

## Remaining risks
- OPEN_NOW telemetry registration still cannot complete until the deferred `trade_temporal_telemetry` module is implemented in its approved future batch.
- Restart-guard double-record behavior (GAP-009 / CON-010) remains open and untouched.
- Parameter-contract contradictions (GAP-004 / CON-007) remain open and untouched.

## Rollback instructions
1. Revert the BATCH-01 commits affecting:
   - `send/core/storage.py`
   - `send/core/signal_engine.py`
   - `send/core/telegram_publisher.py`
   - `send/runtime/system_boot.py`
   - `send/runtime/telegram_updates.py`
   - `tests/batch_01/test_boot_and_import_stabilization.py`
   - `audit/remediation-batch-01/`
2. Re-run the BATCH-01 import and pytest validation commands from the validation report.
3. Confirm the repository returns to the pre-remediation import-failure baseline before any alternate repair is attempted.
