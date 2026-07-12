# REMEDIATION_DEPENDENCY_GRAPH

| REM-ID | Findings resolved | Prerequisites | Modules / specs | Risk | Independent? | Validation before next work |
|---|---|---|---|---|---|---|
| REM-01 | GAP-003, CON-001, SYSTEM_ARCHITECTURE import blockers | none | `core/storage.py`, `core/signal_engine.py`, `runtime/engine_loop.py`, `runtime/system_boot.py` | CRITICAL | yes | import-check of runtime/core modules must pass |
| REM-02 | GAP-004, FSM/ALGO/RISK parameter contradictions | REM-01 | `core/strategy_v2.py`, `core/params_loader.py`, `config/algo_params.json`, `schema/params_schema.json`, `admin_commands.py` | CRITICAL | no | strategy unit tests + config validation must pass |
| REM-03 | GAP-005, GAP-006, GAP-008, GAP-019, CON-003/004/005 | REM-01 | `core/distribution_router.py`, `core/observability_logger.py`, `schema/event_schema.json` | CRITICAL | mostly | route/logging smoke tests and emitted event-type audit |
| REM-04 | GAP-001, GAP-007, CON-002/006/011 | REM-01, REM-03 | `core/trade_temporal_telemetry.py` (new in future code task), `core/outcome_service.py`, `runtime/telegram_updates.py`, `core/bot_service.py` | CRITICAL | no | single-path vote integration test; OPEN_NOW registration trace |
| REM-05 | GAP-011, GAP-012, GAP-013, admin/control contradictions | REM-01, REM-02 | `core/admin_commands.py`, `core/admin_permissions.py`, `core/admin_views.py`, `core/bot_service.py`, config files | HIGH | partially | admin auth/mutation tests; proof logging test |
| REM-06 | GAP-002, GAP-009, GAP-014, GAP-018, FAILURE_RECOVERY drift | REM-01 | `core/fsm_runtime.py`, `core/signal_engine.py`, `monitoring/restart_guard.py`, `state_store/*`, `snapshots/*` | HIGH | partially | FSM lifecycle + restart safety tests |
| REM-07 | Telegram env/runtime integration hardening | REM-01 | `core/telegram_publisher.py`, `runtime/telegram_updates.py`, `runtime/market_client.py` | HIGH | yes | mocked network integration tests |
| REM-08 | GAP-010, GAP-015, analytics/research/intelligence gaps | REM-01, REM-02, REM-03 | `core/analytics_engine.py`, `intelligence/*`, `tools/*`, `experiments/*` | MEDIUM | partly | offline report generation smoke test |
| REM-09 | GAP-017 (test plan implementation) | REM-01 through REM-08 critical path stabilized | test tree to be created later | HIGH | no | test harness green baseline |
| REM-10 | GAP-016, GAP-020, undocumented/orphan cleanup | REM-01 through REM-08 | `legacy/*`, `metrics/*`, `journal/*`, `model_registry/*`, dead configs/state artifacts | LOW-MEDIUM | yes | no active callers remain; cleanup diff reviewed |

## Critical path to safe runnable system
1. **REM-01** boot/import unblock.
2. **REM-02** single canonical parameter/runtime contract.
3. **REM-03** distribution + observability correctness.
4. **REM-04** single secure outcome/telemetry flow.
5. **REM-05** admin/control-plane consolidation.
6. **REM-06** FSM/restart/state lifecycle correctness.
7. Only then begin **REM-09** full test-plan implementation.
