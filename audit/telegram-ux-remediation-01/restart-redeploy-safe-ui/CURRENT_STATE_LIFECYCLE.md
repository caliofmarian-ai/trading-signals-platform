# Current State Lifecycle

## Startup
- `runtime/system_boot.py` starts polling via `runtime/telegram_updates.py` when Telegram is enabled.
- `core/telegram_app_nav.py` now loads persisted active UI metadata at module load (safe fallback to empty on load failure).

## Runtime mutation
- `core/bot_service.py` drives app/admin interactive pages through `_send_interactive_page()`.
- Active message mutations:
  - `set_active_message()` on successful edit and successful replacement send.
  - `clear_active_message()` on stale edit classification.
  - `get_active_message()` before deciding reuse vs replacement send.
- `core/telegram_app_nav.py` prunes stale sessions and bounded-capacity entries; persists atomic state after set/clear/expiry cleanup.

## Shutdown / restart / redeploy
- Graceful shutdown markers are persisted by runtime restart guard (`runtime/system_boot.py` + `monitoring/restart_guard.py`).
- Active UI metadata is already on disk; next process load restores reuse candidates.

## Inventory: set/get/clear callers

### Production callers
- `send/core/bot_service.py`
  - `set_active_message`: lines ~195, ~205, ~282
  - `get_active_message`: line ~255
  - `clear_active_message`: line ~213

### Tests and audits (non-production)
- `tests/telegram_app/test_telegram_app_nav.py`
- `tests/telegram_app/test_telegram_app_nav_persistence.py`
- `tests/telegram_transport/test_telegram_transport_and_recovery.py`
- `tests/canonical/unit/test_telegram_runtime_remediation.py`
- prior audit documentation references

## Telegram UI message production paths
- Interactive text UI (single-message model):
  - `bot_service._send_interactive_page()` -> `telegram_publisher.edit_message()` or `telegram_publisher.send_message()` fallback.
- Simple replies:
  - `bot_service._send_reply()` -> `telegram_publisher.send_message()`.
- Document/file responses:
  - `bot_service._send_document_reply()` -> `telegram_publisher.send_document()`.
- Callback acknowledgment:
  - `runtime/telegram_updates.py` -> `telegram_publisher.answer_callback_query()`.
