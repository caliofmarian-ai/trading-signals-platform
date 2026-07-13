# BATCH_08_TEST_ARCHITECTURE

## Canonical test tree
Created `tests/canonical/` with required logical grouping:
- `unit/`
- `contract/`
- `integration/`
- `end_to_end/`
- `security/`
- `failure_recovery/`
- `persistence/`
- `fixtures/`
- `fakes/`
- `helpers/`

## Determinism controls
- Isolated runtime root per test via `canonical_runtime_root` fixture.
- Fixed timestamps in canonical fixtures/builders.
- Network blocked by default via autouse fixture patching `requests.get/post` and socket connect.
- Runtime/import module cache purged per isolated test env to avoid cross-test state leakage.

## Utilities added
- `tests/canonical/helpers/builders.py` (canonical signal and candle fixtures)
- `tests/canonical/helpers/io.py` (JSONL readers)
- `tests/canonical/fakes/fake_publisher.py` (deterministic publish fake)
- `tests/canonical/conftest.py` (isolation + env + network blocking)

## Test levels by domain
- Unit: boot/import safety, market normalization, strategy determinism/hierarchy.
- Contract: params schema rejection, telemetry idempotency/conflict rules, Telegram callback delegation.
- Integration: FSM + distribution flow, outcome dedup/persistence path.
- Security: fail-closed config/auth/callback-context boundaries.
- Failure recovery: publisher/storage/outcome persistence fault injection.
- Persistence: legacy migration, conflict detection, snapshot rollback on failed restore.
- End-to-end: successful lifecycle, rejected lifecycle, failure lifecycle, restart lifecycle, unauthorized admin lifecycle, parameter-update lifecycle.

## CI/Test command decision
- Default offline command established: `PYTHONPATH=send python -m pytest -q tests`
- Added `pytest.ini` and pinned `requirements-test.txt` (`pytest==9.1.1`).
- No deployment workflow added.
