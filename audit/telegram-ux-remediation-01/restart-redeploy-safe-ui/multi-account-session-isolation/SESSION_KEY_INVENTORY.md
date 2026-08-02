# Session Key Inventory

## Canonical Session Model

Active Telegram UI sessions are scoped by `(chat_id, user_id, thread_id)`.

For private chats, canonical normalization produces:

```
(chat_id=user_id, user_id=user_id, thread_id=None)
```

## Normalization Function

`_normalize_telegram_session_key(chat_id, user_id, thread_id)` in `state_store/state_store.py`.

`_normalize_telegram_thread_id(chat_id, thread_id)`:
- `thread_id is None → None`
- `thread_id <= 0 → None`
- `chat_id >= 0 (private chat) → None` (private chats cannot have supergroup topics)
- `chat_id < 0 and thread_id > 0 → thread_id` (supergroup topic)

## Equivalent Keys (all produce the same canonical key for private chat user_id=U)

| Input | Canonical |
|-------|-----------|
| `(chat_id=U, user_id=U, thread_id=None)` | `(U, U, None)` |
| `(chat_id=U, user_id=U, thread_id=0)` | `(U, U, None)` |
| `(chat_id=U, user_id=U, thread_id=-1)` | `(U, U, None)` |
| JSON `"thread_id": null` | `(U, U, None)` |
| JSON key absent | `(U, U, None)` |

## Cross-Account Isolation

| Account | chat_id | user_id | thread_id | Canonical Key |
|---------|---------|---------|-----------|---------------|
| USER | U | U | None | `(U, U, None)` |
| ADMIN | A | A | None | `(A, A, None)` |

Since `U ≠ A`, the keys are distinct. Operations on A cannot affect U.

## set_active_message callers
- `bot_service._edit_interactive_message` — on successful edit
- `bot_service._send_interactive_page` — on successful replacement send

## get_active_message callers
- `bot_service._send_interactive_page` — to find existing active message

## clear_active_message callers
- `bot_service._edit_interactive_message` — when edit classified as "stale"
- `core.telegram_app_nav.get_active_message` — on expired retention

## Persisted load/save/delete operations
- `state_store.load_telegram_ui_state` — startup recovery
- `state_store.update_telegram_ui_state` — session upsert (set_active_message)
- `state_store.delete_telegram_ui_session` — exact-session delete (clear_active_message)
- `state_store.verify_telegram_session_absent` — post-clear verification
- `state_store.read_telegram_session_message_id` — diagnostic independent read
