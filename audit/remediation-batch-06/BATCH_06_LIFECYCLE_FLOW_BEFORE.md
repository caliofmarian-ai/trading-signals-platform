# BATCH_06_LIFECYCLE_FLOW_BEFORE

- Owner decision applied: OWNER-003 = A
- Prior decision applied: OWNER-004
- Findings addressed: GAP-002, GAP-009, GAP-014, GAP-018

## A. FSM lifecycle before BATCH-06

1. `signal_engine.run_once()` loaded `focus_state.json` through `core.fsm_runtime.load_state()`.
2. `strategy_v2.decide()` returned `PRE`, `CONFIRM`, `OPEN_NOW`, `REJECT`, or `NO_SIGNAL`.
3. `fsm_runtime.apply_transition()` only handled PRE/CONFIRM/OPEN_NOW/REJECT shallowly:
   - PRE appended to `watchlist`
   - CONFIRM only updated a timestamp
   - OPEN_NOW marked `LIVE_SENT`
   - no release path removed symbols from watchlist
   - no cooldown path activated
4. `signal_engine.update_symbol_replacement_score()` tried to import missing `core.scan_scheduler._focus_state_path` and silently did nothing on failure.
5. Observability received a transition event only for the direct state mutation returned by `apply_transition()`.
6. Next evaluation reused persistent watchlist state indefinitely because no lifecycle exit contract existed.

## B. Startup / restart before BATCH-06

1. `runtime.system_boot.start_system()` called `record_start()` immediately.
2. It then called `should_freeze()`; that helper called `record_start()` again.
3. One boot therefore incremented restart state twice.
4. No graceful-shutdown marker distinguished clean stop from crash recovery.
5. No shared validation contract existed for FSM state, restart state, distribution state, and snapshots.
6. Boot did not emit explicit recovery-start / recovery-complete evidence.

## C. Shutdown / recovery before BATCH-06

1. No canonical shutdown hook persisted graceful-stop intent.
2. No automatic snapshot was created on graceful shutdown.
3. `snapshots.snapshot_manager` wrote raw JSON directly, without snapshot schema validation.
4. `restore_snapshot()` overwrote current state files directly, with no rollback path if the second write failed.
5. Recovery could therefore:
   - misclassify clean restarts as crash-like restarts
   - double-count restart loops
   - overwrite valid current state with invalid snapshot content
   - leave watchlist/focus state stuck across restarts
