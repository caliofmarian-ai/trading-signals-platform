# Send/Edit Call Graph

## Interactive canonical page delivery
- Entry: `core.bot_service._send_interactive_page(...)`
  1. resolve `(chat_id, user_id, thread_id)` from message
  2. optional preferred (originating callback) message edit via `_edit_interactive_message`
  3. fallback to tracked active message edit via `_edit_interactive_message`
  4. on stale edits: `telegram_app_nav.clear_active_message(...)`
  5. fallback send: `telegram_publisher.send_message(...)`
  6. track replacement: `telegram_app_nav.set_active_message(...)`

## Edit helper
- `core.bot_service._edit_interactive_message(...)`
  - uses `telegram_publisher.edit_message(...)`
  - success/no-op => `set_active_message(...)`
  - stale => `clear_active_message(...)`
  - unexpected => error telemetry

## Non-interactive exception paths
- File delivery: `core.bot_service._send_document_reply(...)` → `telegram_publisher.send_document(...)`
- Outcome callbacks: direct callback result edit path for outcome line/keyboard cleanup
- Distribution publications: `core.distribution_router` direct `send_message`
- Operational alerts/proofs: `core.observability_logger` direct `send_message`
