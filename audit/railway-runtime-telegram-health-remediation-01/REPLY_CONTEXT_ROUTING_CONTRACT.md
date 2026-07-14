# REPLY_CONTEXT_ROUTING_CONTRACT

## Accepted routing rules
- Private message -> private reply with no configured topic id.
- Group message without a topic -> same group with no topic id.
- Topic message -> same chat and same `message_thread_id`.

## Security rules
- Admin slash commands remain fail-closed outside `ADMIN_CONTROL_CHAT_ID`.
- Mutation commands still rely on canonical role/permission checks.
- Configured admin topic ids are not forced onto unrelated chats.
- Topic ids are only forwarded when the originating chat can safely use them.
