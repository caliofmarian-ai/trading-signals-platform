# INLINE_KEYBOARD_AND_CALLBACK_INVENTORY

## Historical callback inventory

### Legacy runner (`send/legacy/bot_control.py`)
- `tg:<category>:<symbol|__ALL__|__NONE__|__REFRESH__>`
- `buffer_set:<small|medium|large>`

### Legacy panel (`send/_archive/backups/bot_service.py.bak_step*`)
- `ADMIN_STATUS`
- `ADMIN_SET_BUFFER`
- `ADMIN_SET_SYMBOLS`
- `ADMIN_RESEARCH`
- `ADMIN_DOCS`
- `ADMIN_BACK`
- `BUFFER_SMALL|BUFFER_MEDIUM|BUFFER_LARGE`
- `SYM_TOGGLE:<symbol>`
- `DOC:<filename>`
- `VOTE_|<signal_id>|<outcome>`
- `OUTCOME:<outcome>:<signal_id>`
- `VOTE_<...>` generic

## Current callback inventory
- Outcome-related callbacks (`VOTE_|...|...`, `VOTE_...`, `OUTCOME:...`) still handled.
- Legacy admin callbacks are explicitly retired (`send/core/bot_service.py:115-129`, `:206-207`).
