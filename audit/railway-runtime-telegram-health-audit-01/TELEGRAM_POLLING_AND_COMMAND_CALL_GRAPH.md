# TELEGRAM_POLLING_AND_COMMAND_CALL_GRAPH

## Active long-poll owner
`/home/runner/work/trading-signals-platform/trading-signals-platform/send/runtime/telegram_updates.py::poll_updates`

## Full chain
`railway_start.main` -> `system_boot.start_system` -> (thread) `telegram_updates.poll_updates` -> `telegram_updates.process_update` -> `core.bot_service.process_update` -> `core.admin_commands.handle_admin_command` -> `core.telegram_publisher.send_message`

## Polling mechanics
- Uses Telegram `getUpdates` with `timeout=30`
- Tracks `LAST_UPDATE_ID` and advances `offset`
- Consumes updates even when no reply path is taken

## Why updates are consumed but commands appear silent
1. Non-admin slash commands are dropped silently in `bot_service.process_update`:
   - only a fixed admin command set is handled
   - unknown slash commands return no response and no warning
2. `/start`, `/help`, `/status` are not in the handled command set.
3. For handled commands, reply send can still fail (exception path) and is only logged via malformed `error` shorthand.
4. Admin callback handling is fail-closed on wrong/undefined `ADMIN_CONTROL_CHAT_ID`.

## Queue/recovery behavior
- Long polling with offset can process backlog updates after downtime.
- Backlog processing does not guarantee replies if router rejects/ignores commands.
