# CURRENT_VS_HISTORICAL_UI_COMPARISON

| Dimension | Historical (legacy modules) | Current Railway runtime |
|---|---|---|
| `/start` behavior | In `legacy/bot_control.py`, `/start` opened visual symbol panels | Plain text online/help guidance |
| Admin home | Legacy inline panel callbacks existed in old `bot_service` backups | `/admin` returns text summary of commands/roles |
| Inline keyboards | Extensively used in legacy runners/panel callbacks | Used for outcome voting; admin panel buttons retired |
| Callback navigation | Rich menu callbacks (`ADMIN_*`, `BUFFER_*`, `SYM_TOGGLE`, `DOC:`) | Legacy admin callbacks return retirement message |
| Visual density | Emoji/menu-driven, interactive | Mostly plain-text command-driven |
| Password/login screen | Not evidenced | Not present |

## Why bot currently looks different
1. BATCH-05 retired legacy admin callback panel path.
2. BATCH-09 deleted `send/legacy/bot_control.py`.
3. Active runtime now routes through canonical slash-command + text renderers.
