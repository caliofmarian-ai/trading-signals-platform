# Gap Analysis — Active UI Session Key

## Required behavior
Active Telegram UI state must be session-scoped by **chat_id + user_id + thread_id**, so one user cannot cross-collide active UI message tracking across different chats/topics.

## Repository state before change
- `send/core/telegram_app_nav.py` tracked active UI in `_active_ui` keyed only by `user_id`.
- `send/core/bot_service.py` looked up/cleared active state using only `user_id` and then compared chat id after lookup.
- No thread-level scoping existed for active UI state.
- Existing tests validated per-user behavior but did not enforce chat/thread isolation for the same user.

## Risk from the gap
- Same user interacting in multiple topics/chats could have active message references overwritten.
- Edits could target stale/wrong session context instead of session-local UI message.

## Resolution summary
- Re-keyed active UI store by `(chat_id, user_id, thread_id)`.
- Updated bot service lookup/set/clear paths to use session key consistently.
- Added unit and e2e coverage for chat/thread isolation.
