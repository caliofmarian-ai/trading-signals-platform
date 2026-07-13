# BATCH_04_OPEN_FINDINGS

## Residual risks after BATCH-04

### MEDIUM
- Community vote persistence still spans a raw JSONL file and a JSON dedup index.
  - Result: accepted-path durability is strong, but full two-file atomicity is not guaranteed if a crash occurs between those writes.
  - Impact: a rare partial state could require manual repair or replay cleanup.

### MEDIUM
- The legacy admin dispatcher still exists for BATCH-05.
  - Result: VOTE callbacks are now forwarding-only, but the broader admin/control-plane duplication is intentionally deferred.
  - Remaining work: complete control-plane consolidation in BATCH-05.

### LOW
- The implemented community vote policy remains first-write-wins.
  - This matches the pre-existing live runtime and current batch scope.
  - If canon later requires within-window vote updates, that should be handled as a governed follow-up, not inside BATCH-04.

## Deferred findings
- BATCH-05
  - broader `bot_service.py` retirement / admin consolidation
  - control-plane mutation cleanup outside VOTE callback forwarding
- BATCH-06
  - segmented state/config migration
  - `scan_scheduler` / direct FSM state work
  - restart and FSM lifecycle reconciliation

## Remaining CRITICAL/HIGH findings in this batch scope
- None identified as unresolved within `GAP-001`, `GAP-007`, `CON-002`, `CON-006`, `CON-011`

## Recommended next step
- Proceed to BATCH-05 only after reviewing the remaining MEDIUM legacy-control-plane boundary and accepting the known two-file vote-persistence tradeoff.
