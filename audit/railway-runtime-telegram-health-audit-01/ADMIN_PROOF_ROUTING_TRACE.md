# ADMIN_PROOF_ROUTING_TRACE

## Current admin-proof write path
1. Admin mutation in `core.admin_commands.handle_admin_command`
2. `_audit(...)` called on successful mutations
3. `_append_jsonl` writes to:
   - `ADMIN_EVENTS_PATH` (`obs/admin_events.jsonl`)
   - `ADMIN_PROOFS_PATH` (`obs/admin_proofs.jsonl`)

## Telegram proof path in codebase
- `core.observability_logger.proof()`:
  - logs `admin_change` event to `ADMIN_PROOFS_LOG` sink
  - optional Telegram send to `ADMIN_PROOF_CHAT_ID` + `ADMIN_PROOF_THREAD_ID`

## Active-state finding
- No active runtime module calls `observability_logger.proof()`.
- Therefore `ADMIN_PROOF_CHAT_ID` / `ADMIN_PROOF_THREAD_ID` are currently read by dormant code path only.
