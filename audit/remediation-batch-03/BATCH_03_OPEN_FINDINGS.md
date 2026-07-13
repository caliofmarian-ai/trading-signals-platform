# BATCH_03_OPEN_FINDINGS

## Resolved in BATCH-03
- GAP-005
- GAP-006
- GAP-008
- GAP-019

## Remaining risks / ambiguities

### 1. Canon taxonomy is still broader than current runtime naming
`event_schema.json` now matches live emitted objects, including compatibility families required by current runtime emitters (`OUTCOME_SET`, `system_health`, `strategy_optimizer`, `user_outcome`).  
Some of these names still differ from broader v2 canonical family wording in related documents. BATCH-03 keeps them explicit and testable instead of silently dropping them, but a later canon-normalization batch may still want to converge names across all producers.

### 2. Outcome event family remains partially legacy outside BATCH-03
`user_outcome` was left in place for current runtime compatibility.  
This batch normalized the OPEN_NOW outcome-registration event to `outcome_panel_enabled`, but did not redesign the full outcome taxonomy.

## Deferred findings still deferred
- OWNER-002 — legacy `core/bot_service.py` control-plane retirement
- OWNER-003 — segmented mutable runtime path convergence
- OWNER-004 — deferred trade temporal telemetry work remains untouched

## Remaining CRITICAL / HIGH findings after BATCH-03
- No remaining CRITICAL findings were identified inside BATCH-03 scope.
- No remaining HIGH findings were identified inside GAP-005/GAP-006/GAP-008/GAP-019 scope after validation.

## Rollback instructions
1. `git revert <batch-03-commit-sha>`
2. Or restore:
   - `send/core/distribution_router.py`
   - `send/core/observability_logger.py`
   - `send/schema/event_schema.json`
   - `send/core/outcome_service.py`
   - `send/intelligence/risk_monitor.py`
   - `tests/batch_03/`
   - `audit/remediation-batch-03/`
