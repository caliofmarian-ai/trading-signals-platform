# BATCH_04_IMPLEMENTATION_REPORT

## Scope completed
- Implemented `GAP-001`
- Implemented `GAP-007`
- Resolved `CON-002`
- Resolved `CON-006`
- Resolved `CON-011`

## Exact implementation changes

### 1. New canonical telemetry module
- Added `send/core/trade_temporal_telemetry.py`
- Implemented:
  - deterministic OPEN_NOW validation
  - durable registry persistence
  - duplicate-idempotent registration
  - conflicting duplicate rejection
  - canonical `decision` event emission for `OPEN_NOW_REGISTERED`

### 2. OPEN_NOW integration
- Updated `send/core/signal_engine.py`
- Removed the fallback pseudo-registration event emission there
- Delegated registration authority to `trade_temporal_telemetry.py`

### 3. Canonical outcome callback service
- Reworked `send/core/outcome_service.py`
- Added:
  - strict payload parser
  - fail-closed security-config handling
  - registered callback-context validation
  - persistent callback dedup index
  - pseudonymous `member_ref` persistence
  - persistence-failure rejection path
  - safe warning/event emission wrappers

### 4. Single live callback path
- Updated `send/runtime/telegram_updates.py`
- VOTE callbacks now:
  - go only to `outcome_service`
  - are acknowledged via `answerCallbackQuery`
  - are not forwarded into `bot_service` afterward

### 5. Legacy boundary enforcement
- Updated `send/core/bot_service.py`
- Removed independent VOTE mutation behavior
- Legacy VOTE handling now forwards to `outcome_service`
- Fixed legacy callback dispatcher bugs encountered while preserving this forwarding path

### 6. Callback registration metadata
- Updated `send/core/distribution_router.py`
- `register_open_now(...)` now receives:
  - `symbol`
  - `direction`
  - `timeframe`
  - route name

### 7. Downstream compatibility adjustments
- Updated `send/core/analytics_engine.py`
- Updated `send/intelligence/research_engine.py`
- Replaced broken JSON parsing helper usage and preserved user-stat lookup through pseudonymous hashing

## Event-schema changes
- None required
- Existing canonical event families were sufficient:
  - `decision`
  - `user_outcome`
  - `warning`
  - `outcome_panel_enabled`

## Deferred work left intentionally out of scope
- BATCH-05:
  - broader admin/control-plane retirement and consolidation
  - reconciliation UX cleanup beyond VOTE forwarding
- BATCH-06:
  - segmented runtime-state migration
  - `scan_scheduler` → direct FSM state work
  - restart/FSM lifecycle refactors

## Rollback instructions
1. Revert the BATCH-04 commit(s).
2. Restore the prior runtime callback behavior and absence of telemetry registration.
3. Remove `audit/remediation-batch-04/`.
4. Re-run the repository pytest suite to confirm pre-BATCH-04 behavior.
