# BATCH_08_REQUIREMENT_TO_TEST_TRACEABILITY

## Machine-readable map (JSON)
```json
[
  {"requirement":"TP-8.1","test_id":"C08-UNIT-BOOT-001","test_path":"tests/canonical/unit/test_boot_and_market_data.py::test_system_boot_blocks_on_invalid_state","level":"UNIT","subsystem":"boot/config","source":"TEST_PLAN_v2.0.0.md#8.1","status":"COVERED"},
  {"requirement":"TP-8.2","test_id":"C08-INT-DIST-001","test_path":"tests/canonical/integration/test_fsm_distribution_outcome_integration.py::test_fsm_and_distribution_open_now_flow","level":"INTEGRATION","subsystem":"distribution","source":"TEST_PLAN_v2.0.0.md#8.2","status":"COVERED"},
  {"requirement":"TP-8.3","test_id":"C08-FR-ATOMIC-001","test_path":"tests/canonical/failure_recovery/test_failure_injection_behaviors.py::test_atomic_json_write_preserves_last_valid_state","level":"FAILURE_RECOVERY","subsystem":"storage","source":"TEST_PLAN_v2.0.0.md#8.3","status":"COVERED"},
  {"requirement":"TP-9.5","test_id":"C08-PERSIST-ROLLBACK-001","test_path":"tests/canonical/persistence/test_state_snapshot_recovery.py::test_snapshot_restore_rolls_back_on_failed_write","level":"PERSISTENCE","subsystem":"snapshot/recovery","source":"TEST_PLAN_v2.0.0.md#9.5","status":"COVERED"},
  {"requirement":"TP-10.5","test_id":"C08-UNIT-STRAT-002","test_path":"tests/canonical/unit/test_strategy_and_corridor.py::test_threshold_hierarchy_controls_stage_selection","level":"UNIT","subsystem":"strategy","source":"TEST_PLAN_v2.0.0.md#10.5","status":"COVERED"},
  {"requirement":"TP-10.6","test_id":"C08-UNIT-STRAT-001","test_path":"tests/canonical/unit/test_strategy_and_corridor.py::test_strategy_is_deterministic_and_preserves_inputs","level":"UNIT","subsystem":"strategy","source":"TEST_PLAN_v2.0.0.md#10.6","status":"COVERED"},
  {"requirement":"TP-12.1-12.8","test_id":"C08-E2E-RESTART-001","test_path":"tests/canonical/end_to_end/test_offline_end_to_end_flows.py::test_restart_lifecycle_preserves_dedup_and_no_duplicate_irreversible_action","level":"E2E","subsystem":"fsm/lifecycle","source":"TEST_PLAN_v2.0.0.md#12","status":"COVERED"},
  {"requirement":"TP-13.1","test_id":"C08-CONTRACT-TG-001","test_path":"tests/canonical/contract/test_telegram_adapter_boundary.py::test_callback_vote_parsing_delegates_without_network","level":"CONTRACT","subsystem":"telegram boundary","source":"TEST_PLAN_v2.0.0.md#13.1","status":"COVERED"},
  {"requirement":"TP-14.4","test_id":"C08-FR-DIST-001","test_path":"tests/canonical/failure_recovery/test_failure_injection_behaviors.py::test_distribution_publisher_failure_has_no_false_success","level":"FAILURE_RECOVERY","subsystem":"distribution","source":"TEST_PLAN_v2.0.0.md#14.4","status":"COVERED"},
  {"requirement":"TP-15.2","test_id":"C08-INT-OUTCOME-001","test_path":"tests/canonical/integration/test_fsm_distribution_outcome_integration.py::test_outcome_flow_records_vote_and_deduplicates","level":"INTEGRATION","subsystem":"outcome window/dedup","source":"TEST_PLAN_v2.0.0.md#15.2","status":"COVERED"},
  {"requirement":"TP-15.3","test_id":"C08-INT-OUTCOME-001","test_path":"tests/canonical/integration/test_fsm_distribution_outcome_integration.py::test_outcome_flow_records_vote_and_deduplicates","level":"INTEGRATION","subsystem":"outcome dedup","source":"TEST_PLAN_v2.0.0.md#15.3","status":"COVERED"},
  {"requirement":"TP-16.2","test_id":"C08-E2E-REJECT-001","test_path":"tests/canonical/end_to_end/test_offline_end_to_end_flows.py::test_rejected_signal_lifecycle_emits_observability_without_side_effects","level":"E2E","subsystem":"observability","source":"TEST_PLAN_v2.0.0.md#16.2","status":"COVERED"},
  {"requirement":"TP-17","test_id":"C08-E2E-SUCCESS-001","test_path":"tests/canonical/end_to_end/test_offline_end_to_end_flows.py::test_successful_signal_lifecycle_offline","level":"E2E","subsystem":"analytics/research","source":"TEST_PLAN_v2.0.0.md#17","status":"PARTIALLY_COVERED"}
]
```

## Human-readable coverage table
| Canonical requirement band | Representative B08 tests | Status | Evidence |
|---|---|---|---|
| Boot/import safety | `C08-UNIT-BOOT-001`, `C08-UNIT-BOOT-002` | COVERED | no thread/network side effects, unsafe boot blocked |
| Config/parameter contract | `C08-CONTRACT-CFG-001`, `C08-E2E-PARAM-001` | COVERED | schema rejection + authorized mutation consumed |
| Market normalization | `C08-UNIT-MARKET-001` | COVERED | normalize + validate ordering/malformed handling |
| Strategy/corridor | `C08-UNIT-STRAT-001`, `C08-UNIT-STRAT-002` | COVERED | deterministic output + threshold hierarchy |
| FSM/time/restart | `C08-INT-FSM-001`, `C08-E2E-RESTART-001`, `C08-PERSIST-MIG-001` | COVERED | transitions + restart dedup + migration |
| Signal identity/telemetry | `C08-CONTRACT-TELEM-001` | COVERED | idempotent register + conflict rejection |
| Distribution/channel routing | `C08-INT-DIST-001`, `C08-FR-DIST-001` | COVERED | publish success/failure semantics |
| Telegram boundary | `C08-CONTRACT-TG-001` | COVERED | callback parse + delegation, offline |
| Outcome/community/security | `C08-INT-OUTCOME-001`, `C08-SEC-OUTCOME-001`, `C08-SEC-CONTEXT-001` | COVERED | fail-closed + dedup + context checks |
| Admin control plane | `C08-SEC-ADMIN-001`, `C08-E2E-ADMIN-UNAUTH-001`, `C08-E2E-PARAM-001` | COVERED | unauthorized blocked; controlled mutation path |
| Observability/event schema | existing batch_03 + `C08-E2E-REJECT-001` | COVERED | explicit warning/error evidence |
| State/snapshot/recovery | `C08-PERSIST-ROLLBACK-001`, `C08-PERSIST-CONFLICT-001` | COVERED | rollback + conflict detection |
| Analytics/research | existing batch_07 + `C08-E2E-SUCCESS-001` | PARTIALLY COVERED | deterministic advisory flow, TP-17 text truncated |
| Security/risk/failure injection | `C08-SEC-*`, `C08-FR-*` | COVERED | fail-closed and no false-success behavior |

## Unmapped/blocked categories
- None silently omitted.
- TP-17 subclauses are partially blocked by truncation in canonical source file in-repo.
