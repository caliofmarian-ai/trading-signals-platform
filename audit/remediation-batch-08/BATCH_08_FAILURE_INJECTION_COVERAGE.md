# BATCH_08_FAILURE_INJECTION_COVERAGE

## Injected failures and evidence

| Failure surface | Test | Injection method | Expected acceptance | Result |
|---|---|---|---|---|
| Publisher failure | `C08-FR-DIST-001` | fake publisher raises exception | explicit failure event, no false success/counting | PASS |
| Outcome persistence write | `C08-FR-OUTCOME-001` | monkeypatch `storage.append_jsonl` to raise | returns `persistence_failed`, no false accept | PASS |
| Atomic JSON state write | `C08-FR-ATOMIC-001` | monkeypatch `os.replace` failure | last valid file preserved | PASS |
| Snapshot restore partial failure | `C08-PERSIST-ROLLBACK-001` | monkeypatch first `save_fsm_state` failure | rollback to prior valid state | PASS |
| Legacy/canonical conflict | `C08-PERSIST-CONFLICT-001` | conflicting legacy+canonical files | explicit `StateConflictError` | PASS |

## Canonical expectations validated
- No partial trust after write failure.
- No false-success outcomes under failed persistence/publication.
- Restart/recovery paths preserve last valid state when restoration fails.
- Conflict detection blocks ambiguous state.

## Remaining un-injected surfaces (documented)
- explicit config read fault simulation,
- telemetry write fault at signal_engine level,
- analytics/research persist failures inside E2E path.

These remain covered partially by existing batch tests but are tracked for further depth if required.
