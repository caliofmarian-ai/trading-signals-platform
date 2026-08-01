# Approved Recovery Contract

1. Session key remains `(chat_id, user_id, thread_id)`.
2. Active UI state is persisted as minimal metadata only.
3. Startup load failures (corrupt JSON / unsupported schema / invalid shape) do not block runtime; active UI cache starts empty.
4. On interactive response:
   - try preferred message edit,
   - then tracked active message edit,
   - on stale error clear state and send one replacement message,
   - track replacement as new active message.
5. Writes are atomic via existing storage framework.
6. State is versioned and validated.
7. Retention and max-session bounds prune abandoned sessions.
8. Authorization boundaries and role behavior remain unchanged.
