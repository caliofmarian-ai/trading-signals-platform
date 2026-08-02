# Cross-Account Isolation Contract

## Proof

Given:
- USER session key: `(U, U, None)` where U = USER telegram user_id
- ADMIN session key: `(A, A, None)` where A = ADMIN telegram user_id
- U ≠ A (different Telegram accounts)

Then:
- `(U, U, None) ≠ (A, A, None)` — keys are distinct ✓
- `delete_telegram_ui_session(A, A)` filters by canonical key equality, preserving `(U, U, None)` ✓
- `set_active_message(U, ...)` uses key `(U, U, None)`, does not touch `(A, A, None)` ✓
- `get_active_message(U, ...)` reads `_active_ui[(U, U, None)]`, cannot return ADMIN data ✓

## Verified Properties

| Property | Status |
|----------|--------|
| USER and ADMIN keys differ | ✓ Proven by key construction |
| Deleting A does not change U | ✓ Exact-session delete by canonical key |
| Recovering A does not change U | ✓ Set only updates target key |
| Failure while replacing A does not change U | ✓ Each account's send is independent |
| Switching accounts has no coupling | ✓ No shared mutable state between keys |
| Simultaneous saves preserve both | ✓ Lock serializes writes; updater preserves all sessions |

## Test Coverage

Tests 3–10, 22–24, 28, 30 in `test_multi_account_session_isolation.py` explicitly verify these properties.
