# LOGIN_COMMAND_HISTORY

## Direct findings for login/auth commands

## Commands searched in history
`/login`, `/auth`, `/unlock`, `/logout`, plus password/passcode/PIN markers across commits and backup modules.

## Result
- `/login`: **not found** in current code, historical commits, or backup admin modules.
- `/auth` as command: **not found**.
- `/unlock` command: **not found**.
- `/logout` command: **not found**.
- Password text-response flow: **not found**.
- Callback-button authentication flow: **not found**.

## Historical Telegram command inventory (evidence-backed)

### Legacy `send/legacy/bot_control.py` (pre-BATCH-09 deletion)
- `/start`
- `/forex`
- `/crypto`
- `/buffer`
- `/open`

### Canonical control-plane commands (`send/core/telegram_runtime.py`)
- `/admin`, `/strategy`, `/thresholds`, `/sr`, `/spike`, `/symbols`, `/engine`, `/debug`, `/report`, `/roles`, `/affiliate`, `/roles_reload`
- Public: `/start`, `/help`, `/status`

## Callback auth/login command history
No callback values corresponding to login/auth/password stages found.
