# TELEGRAM_COMMAND_CONTRACT

## Public commands
- `/start`
- `/help`
- `/status`

## Admin read-only commands
- `/admin`
- `/strategy`
- `/thresholds`
- `/sr`
- `/spike`
- `/symbols list`
- `/engine`
- `/debug`
- `/report`
- `/roles`
- `/affiliate`

## Admin mutation commands
- `/thresholds PRE|CONFIRM|OPEN <value>`
- `/sr <multiplier>`
- `/spike wick_body_ratio_max|range_z_max|jump_vs_atr_max <value>`
- `/symbols add SYMBOL`
- `/symbols remove SYMBOL`
- `/roles_reload`

## Behavioral contract
- `/start` confirms the bot is online, mentions `SHADOW_MODE` when enabled, and points to `/help`.
- `/help` is rendered from the shared active command registry and distinguishes read-only vs mutation commands.
- `/status` reports runtime phase, recovery state, market-data state, Telegram state, FSM state, shadow-mode state, and always avoids claiming broker execution capability.
- Unknown slash commands always receive `Unknown command. Use /help to view available commands.`
- Non-command text remains unchanged.
