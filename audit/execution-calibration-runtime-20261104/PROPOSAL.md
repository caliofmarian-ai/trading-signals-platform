# Runtime execution-calibration input

CHANGE_ID: 20261104-EXECUTION-CALIBRATION-INPUT-01  
TITLE: Connect an explicitly governed execution-calibration artifact to the existing strategy runtime  
TYPE: PATCH — implementation of the existing optional input; no formula or parameter change  
OWNER: Semnale Trading / BinaryBot  
REQUESTED_BY: Owner instructions to continue the strategy, signal and test work  
DATE: 2026-11-04

## Canon-to-code review

Authority is the active `CANONICAL_MASTER_INDEX_v2.0.0`, not superseded attachments or code comments. `ALGO_SPEC_v3.0.0` explicitly defines Binary Strategy V2. Root Stack v2 requires the complete strategy → DecisionObject → FSM → execution → distribution path. Time Model v3 §§20–23 distinguish Model Time from trader-facing Execution Time, require governed deterministic derivation, permit fractional durations, and require the OPEN_NOW duration to fit the CONFIRM interval. Parameter Control v3 §§12–17 require version/provenance, validation, persistence, audit and rollback.

The attached ALGO v2 and Signal Engine v2 agree on the binary strategy and pipeline; the active repository versions supply the current authority. No canonical numeric defaults for `confirm_delta_minutes` or `pressure_bias` were found. The existing `execution_model` already accepts explicit `ExecutionCalibration`; `signal_engine.run_once` never passes it. This is a runtime wiring gap, not evidence that a fixed expiry should be invented.

TARGET_DOCS: Active canon confirmed unchanged; this implementation record describes the bounded file format.  
TARGET_CODE: `core/runtime_execution_calibration.py`, `core/signal_engine.py`, focused regression tests  
RATIONALE: Make an approved, evidence-backed calibration usable without changing strategy mathematics or bypassing publication gates.  
EXPECTED_IMPACT: A matching valid artifact reaches `decide(execution_calibration=...)`. Missing, malformed, expired, suspended or mismatched artifacts supply `None`, retain the existing expiry block and preserve independent strategy/research evaluation.  
RISK: An incorrectly approved artifact can still be ineffective; parsing and metadata do not establish empirical calibration quality.  
BLAST_RADIUS: Existing optional execution-expiry input only; no provider, broker, routing, score or Time Model changes.

## Input contract

The sole input is `config/execution_calibration.json` under the existing canonical runtime base. It is a trusted, operator-deployed configuration artifact, not a new public/admin write endpoint. Nothing seeds, synthesizes, approves, promotes or modifies this file automatically.

Schema `1.0.0` requires exactly:

- `schema_version`, `calibration_id`, `status` (`APPROVED` for use);
- `strategy_version`, `time_model_schema_version`;
- `provider`, exact `symbol`, `buffer_mode`;
- `algo_params_sha256`: SHA-256 of UTF-8 JSON of the validated algo parameters with `sort_keys=True`, `separators=(",", ":")`, `ensure_ascii=True`, `allow_nan=False`;
- integer UTC `valid_from_ts`, `valid_until_ts` (exclusive);
- `governance`: `change_id`, `approval_ref`, `evidence_ref`, `rollback_ref`, integer `approved_at_ts`;
- `values`: the four existing numeric ExecutionCalibration fields (excluding source).

References must identify independently reviewed approval, chronological research/replay evidence and rollback material before an operator deploys a production artifact. The loader validates the attestation structure, not external reference contents or signatures. Possession of file-write/deployment authority remains the trust boundary. Approved-at ≤ valid-from ≤ current time < valid-until is required. Values use the existing ExecutionCalibration validation; provenance is the calibration id plus SHA-256 of the exact file bytes. Scope and parameter hash must match every evaluation. Duplicate JSON keys, non-finite numbers, unknown/missing fields, symlinks/nonregular files and files over 32 KiB fail closed. There is no cache: deletion, replacement, suspension, expiry and parameter changes take effect on the next evaluation.

The artifact must satisfy the existing CONFIRM/OPEN_NOW consistency inequalities over the entire governed Model Time expiry range. Checking both endpoints of these affine inequalities establishes range coverage; an artifact that would cause derivation errors at another permitted horizon remains unavailable. This is configuration validation, not a change to the expiry formula or its numeric values.

No production calibration artifact or sample numeric bundle is included. Test-only values never leave temporary test directories. Availability of configuration is not proof of profitable calibration, broker quote equivalence, signal publication or broker execution.

## Validation and operation

VALIDATION_METHOD: Offline schema/scope/time/type and fail-closed regression; file replacement/restart behavior; actual runtime argument capture; exact-stage expiry candidate and unchanged Finnhub publication block; full repository suite; required exact-head CI.  
ROLLBACK_PLAN: Remove/suspend the optional artifact to restore missing-calibration behavior; revert the implementation commit if the loader causes an operational regression.  
DEPLOYMENT_PLAN: CI-gated GitHub main deployment; do not deploy any calibration values.  
MONITORING_WINDOW: Verify the deployed commit, runtime health, real-feed recovery and a sanitized calibration-state startup record. Absence of an approved artifact must remain explicitly unavailable.  
SUCCESS_CRITERIA: Correct source/None reaches the existing strategy call; no strategy parameter, publication permission, broker state or research truth-domain change.  
FAILURE_TRIGGERS: Guessed defaults, source mismatch accepted, stale approval accepted, strategy evaluation suppressed solely by missing calibration, false publication/efficiency claim, feed or deployment failure.  
APPROVAL_STATUS: Bounded implementation/testing covered by the Owner's continuation instruction. No approval of numeric production values or distribution activation is inferred.
