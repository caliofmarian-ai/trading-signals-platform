# Session Key Normalization Audit

## Canonical key
- Interactive Telegram UI sessions are now normalized through one function: `(chat_id, user_id, normalized_thread_id)`.
- `normalized_thread_id` uses Telegram topic rules:
  - private chats -> `None`
  - non-topic chats -> `None`
  - valid supergroup topic IDs -> integer topic ID

## Verified consistency
- `/start`, `/status`, `/admin`, `/engine`, APP callbacks, ADMIN_NAV callbacks, and persisted JSON recovery all use the same normalization logic.
- Private-chat variants now resolve identically for:
  - missing `message_thread_id`
  - callback message without `message_thread_id`
  - explicit `None`
  - persisted `thread_id: null`
  - accidental `thread_id=0`

## Consequence
- Slash-command and callback paths now target the same active message for one private session.
