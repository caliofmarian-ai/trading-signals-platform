# BATCH_06_VALIDATION_REPORT

- Owner decision applied: OWNER-003 = A
- Prior decision applied: OWNER-004

## Commands executed

```bash
python -m pip install pytest
PYTHONPATH=send python -m pytest -q tests/batch_01 tests/batch_02 tests/batch_03 tests/batch_04 tests/batch_05
python -m py_compile send/state_store/state_store.py send/core/fsm_runtime.py send/core/signal_engine.py send/core/distribution_router.py send/monitoring/restart_guard.py send/runtime/system_boot.py send/snapshots/snapshot_manager.py
PYTHONPATH=send python -m pytest -q tests/batch_06/test_fsm_restart_recovery.py
PYTHONPATH=send python -m pytest -q tests/batch_01 tests/batch_02 tests/batch_03 tests/batch_04 tests/batch_05 tests/batch_06
PYTHONPATH=send python -m pytest -q tests
PYTHONPATH=send python - <<'PY'
import importlib
for name in [
    'state_store.state_store',
    'core.fsm_runtime',
    'core.signal_engine',
    'core.distribution_router',
    'monitoring.restart_guard',
    'runtime.system_boot',
    'snapshots.snapshot_manager',
]:
    importlib.import_module(name)
print('OK')
PY
```

## Results

- BATCH-01 through BATCH-05 pre-edit baseline: **139 passed**
- BATCH-06 test file: **14 passed**
- BATCH-01 through BATCH-06 regression: **153 passed**
- Full offline repository suite: **153 passed**
- Modified-module import check: **OK**
- Modified-module syntax check: **OK**
- Live `scan_scheduler` dependency search in active BATCH-06 modules: **no matches**
- Live `_focus_state_path` dependency search in active BATCH-06 modules: **no matches**

## Contract validation summary

- Exactly one live segmented write path now exists for BATCH-06 state artifacts.
- Root-level compatibility paths are migration-only reads and receive no live writes.
- Conflicting dual-state files fail clearly.
- Identical dual-state files normalize safely.
- FSM state survives restart through canonical persisted state.
- Restart guard counts once per startup and no longer double-records one boot.
- Invalid snapshots are rejected before overwrite.
- Recovery boot emits schema-valid recovery observability events.
- BATCH-02 through BATCH-05 contracts remained green under regression.

## Scope control validation

- No BATCH-07 analytics/research remediation started.
- No README update performed.
- No deployment/Railway/Telegram credential/broker/live trading work performed.
- No unrelated canonical documents modified.
