# HISTORICAL_TELEGRAM_UX_INVENTORY

## Historical UI surfaces found

## 1) `send/legacy/bot_control.py` (deleted in BATCH-09)

### Entry commands
- `/start` (sends both FOREX and CRYPTO selector panels)
- `/forex`
- `/crypto`
- `/buffer`
- `/open`

### Keyboard/UI features
- Inline keyboard symbol selectors (checkbox style ✅/⬜).
- All/None/Refresh controls.
- Buffer mode inline keyboard (MIC/MEDIU/MARE).
- Emoji-heavy labels and Romanian text prompts.

### Callback data values
- `tg:forex:<SYMBOL>` / `tg:crypto:<SYMBOL>`
- `tg:<category>:__ALL__`
- `tg:<category>:__NONE__`
- `tg:<category>:__REFRESH__`
- `buffer_set:small`
- `buffer_set:medium`
- `buffer_set:large`

### Login/auth UI elements
- No admin password screen found.
- No login prompt command found.

## 2) Legacy `bot_service` panel backups (`send/_archive/backups/bot_service.py.bak_step*`)

### Admin panel callbacks
- `ADMIN_STATUS`, `ADMIN_SET_BUFFER`, `ADMIN_SET_SYMBOLS`, `ADMIN_RESEARCH`, `ADMIN_DOCS`, `ADMIN_BACK`
- `BUFFER_SMALL`, `BUFFER_MEDIUM`, `BUFFER_LARGE`
- `SYM_TOGGLE:<symbol>`
- `DOC:<filename>`

### Role-gated UX
- Panel rendering depended on legacy roles (`OWNER/ADMIN/ANALYST/MODERATOR`).

### Login/auth UI elements
- No password-entry step found.
