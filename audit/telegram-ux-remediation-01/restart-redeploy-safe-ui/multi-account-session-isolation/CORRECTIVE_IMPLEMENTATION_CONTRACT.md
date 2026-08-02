# Corrective Implementation Contract

## Changed Files

### `send/state_store/state_store.py`

Added:
- `_normalize_telegram_thread_id(chat_id, thread_id)` — canonical thread_id normalization
- `_normalize_telegram_session_key(chat_id, user_id, thread_id)` — canonical session key
- `TelegramSessionDeleteResult` dataclass — structured delete evidence
- `delete_telegram_ui_session(chat_id, user_id, thread_id, path=None)` — atomic exact-session delete
- `verify_telegram_session_absent(chat_id, user_id, thread_id, path=None)` — post-delete verification
- `read_telegram_session_message_id(chat_id, user_id, thread_id, path=None)` — independent persisted read

Fixed:
- `validate_telegram_ui_state` dedup key now uses `_normalize_telegram_session_key` (thread_id=0 and None collapse to same key)

### `send/core/telegram_app_nav.py`

Fixed:
- `clear_active_message` — removed early return on memory-miss; always invokes persisted delete; returns structured result
- `get_runtime_diagnostics` — independently reads `persisted_message_id` from disk (not copied from memory)
- `get_active_message` retention pruning — uses `delete_telegram_ui_session` instead of `update_telegram_ui_state`

### `tests/canonical/unit/test_multi_account_session_isolation.py`

New file: 28 tests covering all 30 required test cases (cases 11/12 and 13/14 merged).

## No Framework Changes

A second persistence framework was NOT introduced. The existing `state_store` framework was extended with new functions.

## No Breaking Changes

All existing 184 targeted tests and 540 prior full-suite tests continue to pass. Total: 568 tests green.
