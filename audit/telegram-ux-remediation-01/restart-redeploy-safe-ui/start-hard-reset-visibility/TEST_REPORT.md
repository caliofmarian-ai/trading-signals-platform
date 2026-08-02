# TEST_REPORT.md

## Test Report — /start Hard Reset Visibility

### New Test Suite

**File:** `tests/canonical/unit/test_start_hard_reset_visibility.py`

**Result:** 39/39 passed

### Full Repository Suite

**Result:** 636/636 passed

### Regression Impact

The following existing tests required minimal updates due to the new `/start` contract:

1. **`test_restart_redeploy_recovery.py::FakePublisher`** — Added `delete_message()` method
   (new function called by `_handle_start_hard_reset`; FakePublisher must implement it).

2. **`test_telegram_transport_and_recovery.py::FakePublisher`** — Added `delete_message()` method.

3. **`test_telegram_transport_and_recovery.py::test_08_replacement_becomes_active`** — Updated:
   - Old: used `edit_fail_once=True` to simulate stale edit recovery during `/start`.
   - New: `/start` never calls editMessageText, so `edit_fail_once` was never consumed.
   - Fix: removed `edit_fail_once` parameter; test still verifies that after `/start`, 
     subsequent `/help` edits the new anchor (the core invariant is preserved).

No tests were deleted. No test assertions were weakened. The intent of all
existing tests is preserved.

### Key Behavioral Invariants Verified

| Invariant | Verified by |
|---|---|
| `/start` never calls editMessageText | test_01, test_02, test_07, test_08, test_11 |
| `/start` always sends exactly one message | test_04, test_08, test_09, test_12–16 |
| deleteMessage failure never blocks send | test_13–16 |
| Persistence failure never blocks visible send | test_17–20 |
| Send failure leaves session cleared | test_21, test_22 |
| Subsequent /status edits new anchor | test_06 |
| USER and ADMIN sessions are independent | test_25 |
| Group chat behavior unchanged | test_28 |
| Role resolution unchanged | test_29 |
