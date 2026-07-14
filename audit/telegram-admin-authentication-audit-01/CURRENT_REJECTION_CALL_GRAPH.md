# CURRENT_REJECTION_CALL_GRAPH

## Call graph for admin command denial

```text
Telegram update
  -> send/runtime/telegram_updates.py::process_update
  -> send/core/bot_service.py::process_update
     -> cmd in admin_command_names()
     -> in_admin_context(chat_id)?
        - False -> _send_reply("Access denied (wrong chat).")
        - True  -> handle_admin_command_v2(...)
```

## Exact rejection line
- `send/core/bot_service.py:241` (`"Access denied (wrong chat)."`).

## Context of live variables
- `ADMIN_CONTROL_CHAT_ID=-1003855058603` means only this chat id is accepted for admin commands.
- Private DM chat id differs, so rejection is deterministic.

## Thread-specific behavior
- `ADMIN_CONTROL_THREAD_ID` is not part of admin authorization check.
- General-topic vs topic thread only affects outgoing reply threading when message carries `message_thread_id`.

## Ordering implication
Chat context is evaluated before admin role/permission checks.
Therefore interactive login (if it existed) cannot run in private chat in current code path.
