# BATCH_08_OPEN_FINDINGS

## Status of GAP-017
- **Resolved for offline canonical acceptance baseline** via canonical test tree + traceability + invariant coverage artifacts.

## Newly observed / remaining findings

### OF-08-001: TEST_PLAN canonical file appears truncated
- File: `send/docs/canonical/active/TEST_PLAN_v2.0.0.md`
- Observation: ends at heading fragment `## 17. Analytics and Research Va`.
- Impact: exact TP-17+ subclause verbatim mapping cannot be completed from in-repo text.
- Severity: MEDIUM (documentation integrity / traceability completeness).
- Recommendation: restore full canonical TEST_PLAN document in active canon set.

### OF-08-002: Hardcoded absolute outcome paths in `core/outcome_service.py`
- Observation: paths default to `/opt/binarybot/outcomes/...` constants at import-time.
- Impact: reduces natural testability and environment portability; tests require explicit path rewiring.
- Severity: MEDIUM.
- Recommendation: align with storage/base-dir and env-driven path conventions used by other modules.

### OF-08-003: Hardcoded absolute config/obs constants in `core/admin_commands.py`
- Observation: default constants point to `/opt/binarybot/...`; mixed with storage-based path usage.
- Impact: constrained offline portability and fixture ergonomics.
- Severity: MEDIUM.
- Recommendation: fully unify admin path resolution through storage/state-store conventions.

### OF-08-004: Pre-existing deprecation warning
- File: `send/tools/strategy_auditor_lib.py`
- Observation: `datetime.utcnow()` deprecation warning (6 warnings in suite).
- Severity: LOW.
- Recommendation: replace with timezone-aware UTC datetime call in future cleanup batch.

## Remaining CRITICAL/HIGH findings for BATCH-08 scope
- None newly introduced by BATCH-08 test implementation.
