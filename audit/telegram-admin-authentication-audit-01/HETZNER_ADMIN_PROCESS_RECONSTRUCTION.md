# HETZNER_ADMIN_PROCESS_RECONSTRUCTION

## Evidence-backed reconstruction

## In-repo pieces consistent with historical Hetzner behavior
1. `send/legacy/bot_control.py` (deleted) used `python-telegram-bot` `run_polling()` and visual inline-keyboard controls.
2. Shell transport stack:
   - `send/tg_send.sh`
   - `send/alerts/send_system.sh`, `send_error.sh`, etc.
3. Deprecated architecture references to systemd-style standalone process startup.

## Most likely historical process shape (probable, not fully reproducible)
- Canonical runtime plus one or more auxiliary Telegram processes/scripts on Hetzner.
- This explains remembered different UX and startup/alert behavior.

## Login/password in reconstructed Hetzner path
- No password/login flow found in reconstructed in-repo Hetzner components.
- If such flow existed operationally, it was likely external/untracked and is not recoverable from repository evidence.
