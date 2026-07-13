# BATCH_07_OPEN_FINDINGS

## Deferred / Out-of-Scope for BATCH-07

### GAP-011 — Admin mutation path bypasses atomic write/locks (HIGH)
Deferred to BATCH-05 (already recorded). `admin_commands.py` not modified in BATCH-07.

### GAP-012 — Hardcoded permission matrix ignores admin_permissions.json (MEDIUM)
Deferred to BATCH-05 (already recorded). Out of BATCH-07 scope.

### GAP-013 — bot_service fail-open RBAC (HIGH)
Deferred. Out of BATCH-07 scope.

### GAP-016 — Legacy bot with missing dependency (MEDIUM)
Deferred to BATCH-09. Out of BATCH-07 scope.

### GAP-017 — Automated test plan not implemented (HIGH)
Addressed partially by BATCH-07 (52 tests created). Full canonical test suite deferred to BATCH-08 per plan.

### GAP-018 — State/path abstraction conflicts (MEDIUM)
Addressed by BATCH-06. Residual cleanup deferred to BATCH-09.

### GAP-019 — Invalid log_warning() call sites (HIGH)
Deferred to BATCH-03 record. Out of BATCH-07 scope.

### GAP-020 — Daily metrics/health path inert (LOW)
Deferred to BATCH-09. Out of BATCH-07 scope.

## Known Remaining Risks

### analytics_engine.py — datetime.utcnow() deprecation
`strategy_auditor_lib.py` uses `datetime.datetime.utcnow()` which is deprecated in Python 3.12. This is a pre-existing issue in the `build_report()` function's date computation. It does not affect correctness in current Python versions. Recommend fixing in BATCH-09 cleanup.

### research_engine.py — confidence is always MEDIUM with non-empty data
The `confidence` field is simplified: LOW if no data, MEDIUM otherwise. A proper confidence model (factoring sample size, data age, etc.) is deferred to BATCH-08.

### signal funnel — no correlation to outcome
The signal funnel (PRE/CONFIRM/OPEN_NOW counts) is not correlated to outcome records by signal_id. Correlation analysis is deferred to BATCH-08 research capabilities.

### strategy_auditor_lib — FSM/distribution/error events loaded but not analyzed
`load_all_events` loads FSM events, distribution events, and error events, but `build_report` only analyzes engine decision events. Enriched reporting with FSM and distribution integration is deferred to BATCH-08.

### report_loader.py — REPORTS_DIR computed at import time
`REPORTS_DIR` is computed once at module import from `ANALYTICS_DIR` env var. If the env var is set after import, the path won't update. This is a minor limitation consistent with how other modules handle this pattern; mitigated by the test fixture always setting env vars before import.

## Rollback Instructions

To revert BATCH-07:

```bash
git revert <BATCH-07-commit-hash>
# or
git checkout <pre-BATCH-07-commit> -- \
  send/core/analytics_engine.py \
  send/intelligence/research_engine.py \
  send/tools/strategy_auditor_daily.py \
  send/tools/strategy_auditor_lib.py \
  send/intelligence/report_loader.py
git rm send/core/jsonl_parser.py
git rm send/tools/__init__.py
git rm tests/batch_07/test_analytics_research_toolchain.py
git rm tests/batch_07/__init__.py
git rm -r audit/remediation-batch-07/
```

After rollback: GAP-010 and GAP-015 will be re-opened. Analytics and research toolchain will be non-functional (ModuleNotFoundError, silent data loss, wrong stage field).

## Work Remaining for BATCH-08

Per `REMEDIATION_BATCH_PLAN.md`:

1. Implement the full canonical test suite (GAP-017) covering all acceptance criteria from TEST_PLAN canonical spec.
2. Add correlation analysis between signal funnel stages and outcome records by signal_id.
3. Add proper confidence model for research findings (sample size, data age).
4. Enrich strategy auditor reports with FSM and distribution event analysis.
5. Add temporal filtering (range_days) to analytics recompute and research functions.
6. Implement `get_symbol_ranking`, `get_focus_history`, `get_funnel` placeholders.

## BATCH-09 Deferred

Cleanup of legacy/orphan utilities (GAP-016, GAP-020, dead configs) is deferred to BATCH-09 per plan. Requires owner approval.
