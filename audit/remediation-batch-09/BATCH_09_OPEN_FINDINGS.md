# BATCH_09_OPEN_FINDINGS

## Closed in BATCH-09
- **GAP-016**: Legacy bot cleanup — CLOSED. `send/legacy/bot_control.py` deleted.
- **GAP-020**: Health/metrics path inert — CLOSED. `send/monitoring/health_check.py`, `send/metrics/metrics_collector.py`, `send/metrics/aggregates_writer.py` deleted.
- **OF-08-002**: Hardcoded outcomes paths in outcome_service.py — CLOSED. Converged to `storage.root_path()`.
- **OF-08-003**: Hardcoded config/obs constants in admin_commands.py — CLOSED. Converged to `_storage.root_path()`.
- **OF-08-004**: `datetime.utcnow()` deprecation — CLOSED. Replaced with `datetime.now(datetime.UTC)`.

## Remaining / New Findings

### OF-09-001: TEST_PLAN_v2.0.0.md Truncation (carried forward from OF-08-001)
- **Status**: OPEN — requires owner action
- **File**: `send/docs/canonical/active/TEST_PLAN_v2.0.0.md`
- **Finding**: File truncated at `## 17. Analytics and Research Va` (heading incomplete mid-word). Sections 17+ body content and sections 18+ entirely missing.
- **Impact**: Documentation traceability gap only. No runtime or test impact.
- **Action required**: Owner must supply or approve content for sections 17+ before the canonical TEST_PLAN can be restored to completeness.
- **Owner decision item**: OWNER-DECISION-BATCH09-001

### OF-09-002: Residual /opt/binarybot env-var defaults in other modules
- **Severity**: LOW
- **Files**: `core/observability_logger.py`, `core/params_loader.py`, `core/analytics_engine.py`, `intelligence/research_engine.py`, `intelligence/report_loader.py`, `core/admin_permissions.py`, `core/bot_service.py`, `core/distribution_router.py`
- **Finding**: These files contain `/opt/binarybot/...` as the hardcoded fallback in `os.getenv("VAR", "/opt/binarybot/...")` patterns. They are all env-var overridable and do NOT require BATCH-09 scope authorization since they are not hardcoded unconditional writes.
- **Impact**: If no env var is set and no BINARYBOT_BASE_DIR is configured, these modules default to `/opt/binarybot/...` paths. In production (Railway), the env vars are set correctly.
- **Action**: Document for a future targeted cleanup batch. No change required for BATCH-09.

### OF-09-003: send/_archive/pycache directory committed
- **Severity**: LOW
- **Finding**: `send/_archive/pycache/` directory is tracked in version control. Likely a development artifact.
- **Impact**: Minor repository hygiene concern. No runtime impact.
- **Action**: Could be addressed in a future minor cleanup. Not in BATCH-09 scope since `_archive/` is preserved as governance/historical.

### OF-09-004: admin_permissions.json TEST_ONLY reclassification
- **Severity**: INFO
- **Finding**: `send/config/admin_permissions.json` was classified as DEAD in the deep audit but is actually a TEST_ONLY fixture dependency.
- **Impact**: None — file preserved in BATCH-09.
- **Action**: The deep code audit's DEAD classification should be updated in a future audit refresh.

## Remaining CRITICAL/HIGH Findings
- None introduced by BATCH-09.
- Pre-existing findings from prior batches (parameter schema split, channel config authority) remain deferred per prior batch records.

## Items Deferred from BATCH-09 Scope
Per BATCH-09 authorization, the following are explicitly not addressed:
- Final System Readiness Audit
- Railway deployment
- Telegram live credentials
- Broker/Pocket Option integration
- Paper/live trading
- Broad canonical redesign
