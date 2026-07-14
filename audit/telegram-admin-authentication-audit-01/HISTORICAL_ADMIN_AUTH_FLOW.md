# HISTORICAL_ADMIN_AUTH_FLOW

## Historical flow by commit evidence

## A) `0fb9112` (initial import)

### Slash admin commands
`git show 0fb9112:send/core/bot_service.py` lines ~548-556:
- `/admin` family routed directly to `handle_admin_command_v2(text, user_id)`.
- No chat gate in slash path.

`send/core/admin_commands.py` and `send/core/admin_permissions.py` performed identity/permission checks by user ID + roles config.

### Legacy panel path also existed
Same file had legacy functions:
- `get_role`, `_load_rbac`, `require_role`, `handle_admin_command(chat_id, user_id)`, `render_admin_panel`, and callback UI handlers.
- Callback path enforced chat context for admin callbacks and returned `"Access denied (wrong chat)."` on mismatch.

### Important historical conclusion
Even in this older runtime, evidence shows **RBAC/chat-context gating**, not password-login prompts.

## B) `d7e7213` (BATCH-05)
- Legacy panel callbacks retired.
- Independent bot_service RBAC removed.
- Canonical control plane consolidated in `admin_commands`.
- `in_admin_context` changed fail-open -> fail-closed (for callback/admin-context checks).
- Still no password/session flow introduced.

## C) `49aaeb4` (current runtime remediation)
- Added `/start`, `/help`, `/status`.
- Added explicit admin slash chat-context denial (`send/core/bot_service.py:239-242`).
- This is the direct change causing current private-chat admin denial behavior.

## D) Deleted legacy Hetzner runner: `send/legacy/bot_control.py`
- Had Telegram polling via `python-telegram-bot` with commands `/start`, `/forex`, `/crypto`, `/buffer`, `/open`.
- Used inline keyboards and callback controls for symbol toggles and buffer mode.
- No password/login/session implementation present.
