# Role and Context Analysis

## Session isolation
All APP navigation state is isolated by `(chat_id, user_id, thread_id)`.

This prevents cross-talk between:
- the same user in multiple chats;
- the same user in multiple forum topics;
- different users in the same chat.

## Authorization checkpoints
- APP destinations are rendered only through the canonical renderer set.
- Admin pages still enforce owner-private and admin-topic restrictions at callback/slash handling time.
- Roles reload requires both admin-topic context and `roles.write` permission at execution time.
- Symbol mutations, file browsing, document delivery, log export, and audit export still pass through their existing permission/path checks.
