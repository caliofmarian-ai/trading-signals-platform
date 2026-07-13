# BATCH-01 Open Findings

## Resolved in BATCH-01
- GAP-003 — missing `storage.config_path()` helper causes core import failure
- CON-001 — governed module-boundary import path blocked before runtime start

## Remaining CRITICAL findings explicitly still open
- GAP-001 — missing `trade_temporal_telemetry` module
- GAP-004 — strategy parameter contract split across incompatible schemas
- GAP-006 — distribution router observability calls are API-incompatible
- GAP-007 — outcome vote path is duplicated and divergent
- CON-002 — OPEN_NOW registration does not pass through the canonical telemetry layer
- CON-004 — distribution observability contract mismatch
- CON-006 — duplicated elite vote handling
- CON-012 — fail-open admin context in legacy bot path

## Remaining HIGH findings explicitly still open
- GAP-002 — missing `scan_scheduler` dependency path
- GAP-005 — distribution router ignores file-governed limits/admin routing fields
- GAP-008 — observability taxonomy drift
- GAP-009 — restart guard double-records each boot
- GAP-011 — admin mutation path bypasses atomic write/locks and central validation
- GAP-013 — `bot_service` uses separate RBAC/state path family and fail-open chat guard
- GAP-014 — FSM lifecycle lacks release/cooldown completion path
- GAP-017 — automated test plan remains incomplete beyond this batch
- GAP-019 — invalid `log_warning()` call sites break rejection/risk branches
- CON-003 — channel config file truth diverges from runtime behavior
- CON-005 — non-canonical observability event families still emitted elsewhere
- CON-008 — permission/source-of-truth drift remains
- CON-009 — FSM lifecycle semantics remain incomplete
- CON-010 — crash-loop protection still inflates restart count
- CON-011 — outcome rejection path logging incompatibility remains
- CON-013 — duplicated admin/control-plane surface remains

## Owner decisions still unresolved and untouched
- OWNER-001 — parameter contract decision remains open
- OWNER-002 — layered authority follow-up remains open
- OWNER-003 — layered authority follow-up remains open

## Recommended next step
- Obtain/confirm the owner decision needed for the canonical parameter contract, then begin BATCH-02 only after this BATCH-01 change is accepted.
