# BATCH_08_VALIDATION_REPORT

## Commands executed
1. Baseline pre-change full suite:
   - `PYTHONPATH=send python -m pytest -q tests`
2. Canonical group validations:
   - `PYTHONPATH=send python -m pytest -q tests/canonical/unit`
   - `PYTHONPATH=send python -m pytest -q tests/canonical/contract`
   - `PYTHONPATH=send python -m pytest -q tests/canonical/integration`
   - `PYTHONPATH=send python -m pytest -q tests/canonical/security`
   - `PYTHONPATH=send python -m pytest -q tests/canonical/failure_recovery`
   - `PYTHONPATH=send python -m pytest -q tests/canonical/persistence`
   - `PYTHONPATH=send python -m pytest -q tests/canonical/end_to_end`
   - `PYTHONPATH=send python -m pytest -q tests/canonical`
3. Prior regression suites:
   - `PYTHONPATH=send python -m pytest -q tests/batch_01 tests/batch_02 tests/batch_03 tests/batch_04 tests/batch_05 tests/batch_06 tests/batch_07`
4. Full suite determinism runs:
   - `PYTHONPATH=send python -m pytest -q tests` (run #1)
   - `PYTHONPATH=send python -m pytest -q tests` (run #2)
   - `PYTHONPATH=send python -m pytest -q $(find tests -type f -name 'test_*.py' | sort -r)` (reverse order)

## Results summary
- Baseline before B08: **205 passed, 6 warnings**.
- Canonical tree: **25 passed, 0 failed**.
- Prior BATCH regression: **205 passed, 6 warnings**.
- Full suite run #1: **230 passed, 6 warnings, 1.44s**.
- Full suite run #2: **230 passed, 6 warnings, 1.46s**.
- Reverse-order run: **230 passed, 6 warnings, 1.52s**.

## Determinism result
- PASS: consistent pass/fail and counts across repeated and reversed-order executions.

## Skips / xfails
- Skipped: **0**
- XFail: **0**

## Warning inventory
- 6 warnings from pre-existing `datetime.utcnow()` deprecation in `send/tools/strategy_auditor_lib.py`.

## Network isolation result
- Canonical tests enforce blocked network by default via autouse fixture patching `requests.get`, `requests.post`, and socket connection.
- No canonical tests require live Telegram, broker, or internet access.

## Production-state mutation check
- Canonical tests use per-test isolated temporary runtime roots.
- No writes are performed into repository production runtime directories.

## Canonical document integrity
- No authoritative canonical docs modified.
