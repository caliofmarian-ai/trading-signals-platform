# TELEGRAM_COMMAND_INVENTORY

## Implemented slash commands in active dispatcher
From `core.bot_service.process_update` + `core.admin_commands.handle_admin_command`:

- `/admin`
- `/strategy`
- `/thresholds`
- `/sr`
- `/spike`
- `/symbols`
- `/engine`
- `/debug`
- `/report`
- `/roles`
- `/affiliate`
- `/roles_reload`

## Not implemented in active dispatcher
- `/start` -> not handled
- `/help` -> not handled
- `/status` -> not handled
- generic symbol/member commands outside admin set -> not handled

## Callback families
- `VOTE_|...|...` and `VOTE_...` -> outcome flow
- `OUTCOME:...` -> delegated to outcome flow
- legacy admin panel callbacks -> explicit retirement response
