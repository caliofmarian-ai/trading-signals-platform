# BATCH_04_FLOW_BEFORE

## Decisions and scope
- Prior OWNER-004 applied: implement `send/core/trade_temporal_telemetry.py`; do not start the separate `scan_scheduler`/FSM refactor.
- OWNER-002 boundary respected: remove duplicate live outcome mutation from the legacy path without retiring the broader `bot_service.py` control plane.
- Findings addressed in this batch: `GAP-001`, `GAP-007`, `CON-002`, `CON-006`, `CON-011`.

## Before-state OPEN_NOW registration flow
1. `send/core/signal_engine.py`
   - emits `signal_event`
   - tries to import `core.trade_temporal_telemetry`
   - import fails because the module is missing
2. `send/core/distribution_router.py`
   - publishes OPEN_NOW to ELITE and admin mirror
   - calls `outcome_service.register_open_now(...)` only for vote-window metadata
3. Result before BATCH-04
   - no canonical trade temporal telemetry persistence exists
   - no durable OPEN_NOW telemetry record exists
   - `signal_engine` logs deferred failure warnings instead of canonical registration

## Before-state outcome/community callback flow
1. `send/runtime/telegram_updates.py`
   - parses `callback_query.data`
   - if payload starts with `VOTE_`, calls `outcome_service.handle_vote_callback(...)`
   - then still forwards the same update into `bot_service.process_update(update)`
2. `send/core/outcome_service.py`
   - validates outcome value
   - verifies ELITE membership
   - checks vote window
   - persists vote into `/opt/binarybot/outcomes/outcomes.jsonl`
   - persists dedup index into `/opt/binarybot/outcomes/outcomes_index.json`
3. `send/core/bot_service.py`
   - independently parses `VOTE_|signal|outcome`
   - independently mutates `/opt/binarybot/state/outcomes.json`
   - emits separate `OUTCOME_SET`
4. Result before BATCH-04
   - same callback can traverse two mutation paths
   - stores diverge (`outcomes.jsonl` vs `state/outcomes.json`)
   - callback acknowledgment does not reflect committed vote result
   - context validation is incomplete
   - privacy is violated by persisted raw Telegram user IDs

## Duplicate handlers and stores identified before change
- Duplicate callback handlers:
  - `send/runtime/telegram_updates.py`
  - `send/core/bot_service.py`
- Duplicate stores:
  - `/opt/binarybot/outcomes/outcomes.jsonl`
  - `/opt/binarybot/state/outcomes.json`
- Duplicate mutation semantics:
  - `outcome_service.handle_vote_callback`
  - `bot_service._record_outcome`

## Selected canonical callback path for BATCH-04
- Primary live path kept: `runtime/telegram_updates.py` → `outcome_service.handle_vote_callback_data(...)` → `outcome_service.handle_vote_callback(...)`
- Legacy fallback path retained only as forwarding:
  - `bot_service.process_update(...)` → `bot_service.handle_callback(...)` → `outcome_service.handle_vote_callback(...)`
- No legacy `bot_service.py` outcome store mutation remains in the VOTE callback path.
