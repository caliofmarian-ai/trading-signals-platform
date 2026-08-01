# Unified Navigation Contract

## Canonical rules
1. Resolve `(chat_id, user_id, thread_id)`
2. Prefer edit of callback-originating message when provided
3. Otherwise edit tracked active message
4. Treat `message is not modified` as success
5. If stale/uneditable: clear stale active state
6. Send exactly one replacement only when no editable target remains
7. Track every successful interactive page target (`set_active_message`)
8. Never create a second interactive message solely due to route family differences

## Implemented API
- `core.bot_service._send_interactive_page(message, user_id, text, reply_markup, preferred_message_id=None)`
