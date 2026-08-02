# TEST_MATRIX.md
# Issue #31 — Test Matrix

File: `tests/canonical/unit/test_restart_redeploy_recovery.py`

| # | Test Name | Class | Status |
|---|-----------|-------|--------|
| 1 | USER conversation deleted → /start recovers | TestTransportFirstRecovery::test_01 | ✅ PASS |
| 2 | ADMIN conversation deleted → /start recovers | TestTransportFirstRecovery::test_02 | ✅ PASS |
| 3 | Both sessions deleted independently | TestTransportFirstRecovery::test_03 | ✅ PASS |
| 4 | Stale-message API error classified correctly | TestTelegramAPIErrorClassification::test_04 | ✅ PASS |
| 4b | Not-modified classified as no_op | TestTelegramAPIErrorClassification::test_04b | ✅ PASS |
| 5 | Unknown error falls back without corrupting state | TestTelegramAPIErrorClassification::test_05 | ✅ PASS |
| 5b | Legacy RuntimeError string matching | TestTelegramAPIErrorClassification::test_05b | ✅ PASS |
| 7 | Clear fails (stale lock) → replacement still sent | TestTransportFirstRecovery::test_07 | ✅ PASS |
| 8 | Replacement sent when recoverable clear fails | TestTransportFirstRecovery::test_08 | ✅ PASS |
| 9 | Send success + persistence failure = transport success | TestTransportFirstRecovery::test_09 | ✅ PASS |
| 10 | Stale lock owned by dead PID reclaimed | TestStaleLockRecovery::test_10 | ✅ PASS |
| 11 | Active lock owned by live PID not stolen | TestStaleLockRecovery::test_11 | ✅ PASS |
| 12 | Lock from previous deployment handled | TestStaleLockRecovery::test_12 | ✅ PASS |
| 13 | Malformed lock reclaimed by age | TestStaleLockRecovery::test_13 | ✅ PASS |
| 14 | Lock timeout produces diagnostics | TestStaleLockRecovery::test_14 | ✅ PASS |
| — | Lock metadata written correctly | TestStaleLockRecovery::test_lock_metadata | ✅ PASS |
| 15 | Restart with stale lock recovers | TestRestartRedeployForensics::test_15 | ✅ PASS |
| 16 | Redeploy with different deployment ID recovers | TestRestartRedeployForensics::test_16 | ✅ PASS |
| 17 | Runtime path comparison | TestRestartRedeployForensics::test_17 | ✅ PASS |
| 18 | Exactly one poller starts | TestPollerBehavior::test_18 | ✅ PASS |
| 19 | Heartbeat update function works | TestPollerBehavior::test_19 | ✅ PASS |
| 19b | Stale heartbeat detected | TestPollerBehavior::test_19b | ✅ PASS |
| 20 | Failed update does not stop polling | TestPollerBehavior::test_20 | ✅ PASS |
| 21 | /start, /help, /status never silent | TestTransportFirstRecovery::test_21 | ✅ PASS |
| 22 | USER and ADMIN remain isolated | TestSessionIsolation::test_22 | ✅ PASS |
| 25 | Repository clean (no stale .lock files) | test_25_repository_clean | ✅ PASS |

## Full Suite Results

- New targeted tests: **29 passed**
- Full suite: **597 passed**
- Railway tests: included in full suite
- No regressions

## retry_after extraction | token_redaction | system_boot hardening

All structural tests pass — see test file for detail.
