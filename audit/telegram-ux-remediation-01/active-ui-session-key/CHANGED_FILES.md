# Changed Files

## Code
- `send/core/telegram_app_nav.py`
  - Active UI state storage and API changed to session-scoped key `(chat_id, user_id, thread_id)`.
- `send/core/bot_service.py`
  - Active UI lookup/set/clear updated to pass chat/thread session context.

## Tests
- `tests/telegram_app/test_telegram_app_nav.py`
  - Updated active-state unit tests to new API and semantics.
  - Added independence coverage for same user across different chats and threads.
- `tests/telegram_app/test_e2e_application.py`
  - Added end-to-end test proving same user in different topics gets separate active message tracking.
