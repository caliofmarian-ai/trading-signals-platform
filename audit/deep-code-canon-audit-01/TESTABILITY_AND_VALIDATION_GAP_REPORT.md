# TESTABILITY_AND_VALIDATION_GAP_REPORT

## Current testability baseline
- No automated test suite exists in the repository.
- No `pytest`, `unittest` harness, `tests/` directory, or CI config was found.
- Some modules are pure or near-pure and therefore testable with minimal seams:
  - `core/strategy_v2.py`
  - `core/candle_adapter.py`
  - `core/fsm_runtime.py` (with temp state seam or refactor)
  - `core/admin_permissions.py`
  - `intelligence/*` analytics helpers
  - `alerts/alert_engine.py`

## What can currently be tested with moderate effort
- Strategy gating/scoring for deterministic input candles.
- Candle normalization and validation rules.
- FSM transition outputs for PRE/CONFIRM/OPEN/REJECT.
- Permission matrix decisions and affiliate scope checks.
- Offline analytics helpers if JSON parsing bugs are fixed.

## What cannot currently be verified cleanly
| Area | Why not testable today |
|---|---|
| Boot/startup | `core.signal_engine` import fails before runtime wiring is established |
| OPEN_NOW telemetry flow | canonical module missing |
| Distribution logging | `distribution_router` calls logger with invalid signature |
| Outcome flow correctness | duplicate callback path produces split behavior |
| Admin mutation safety | no dependency inversion around file writes; direct writes to live paths |
| Recovery flow | snapshot/health utilities not integrated and use direct file IO |

## Missing seams/interfaces
- No dependency injection for Telegram publisher or market client in runtime loop.
- No abstract clock interface; time is read directly in many modules.
- No in-memory/file-path seam for `core.signal_engine`, `core.distribution_router`, `core.outcome_service`.
- No schema validator abstraction shared between admin mutation path and strategy reader.

## Nondeterministic behavior barriers
- direct `time.time()` usage in strategy fallback path, boot, outcome, restart guard, metrics.
- direct network requests in `runtime.market_client`, `core.outcome_service`, `core.telegram_publisher`, `runtime.telegram_updates`.
- env vars read at import time by Telegram modules.

## Missing fixtures/mocks/test data
- deterministic candle fixtures for M1/M5 signal scenarios.
- canonical config fixtures for aligned parameter schema.
- state fixtures for focus/dist/outcomes lifecycle.
- Telegram callback/update fixtures for admin and vote flows.
- mock TwelveData responses and Telegram API responses.

## Required tests by canonical category
### Structural / boot validation
- import test for every runtime module
- boot test for `system_boot.start_system()` with mocked threads and env
- config-path/schema validation test at startup

### State persistence / restart validation
- atomic write/lock tests for admin mutations once refactored
- restart guard single-boot count test (prevents double-count)
- snapshot restore integrity tests

### Strategy and gate validation
- SR gate pass/fail cases
- spike filter boundary cases
- feasibility/time-to-target boundary cases
- threshold stage selection with canonical config

### Decision-object / pipeline-order validation
- decision payload field completeness against canon
- engine ordering: fetch → normalize → decide → FSM → route
- no OPEN_NOW path without telemetry registration

### FSM lifecycle validation
- PRE enters watchlist
- CONFIRM preserves/increments state appropriately
- OPEN_NOW release/cooldown behavior (currently missing)
- watchlist max overflow invariant

### Telegram UX / routing validation
- tier routing by stage and limit
- admin mirror behavior
- disabled/silent tier behavior
- callback edit vs send behavior

### Outcome / security validation
- elite membership rejection
- vote-window too-early / expired / duplicate cases
- ensure callback is processed exactly once
- ensure no second store is written outside canonical path

### Observability / audit-trail validation
- every emitter produces allowed event type
- logger build_event signatures compile/run
- proof logs created for admin mutations

## Canonical acceptance criteria currently unverifiable
- TEST_PLAN sections on restart safety, outcome integrity, observability completeness, deployment evidence.
- TRADE_TEMPORAL_TELEMETRY acceptance cannot be checked because module is absent.
- Security/privacy acceptance cannot be checked while duplicate vote path remains active.

## Conclusion
Repository is **not ready for formal canon-based validation**. Stabilization/remediation work must precede test implementation.
