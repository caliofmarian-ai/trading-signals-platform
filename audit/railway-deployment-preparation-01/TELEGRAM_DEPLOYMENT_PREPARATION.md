# TELEGRAM_DEPLOYMENT_PREPARATION.md

## Prepared behavior
- Token is read only from `TELEGRAM_BOT_TOKEN`.
- Telegram is disabled by default in `.env.example`.
- No Telegram calls occur during init, build, tests, or health checks.
- Runtime only starts the Telegram polling thread when `ENABLE_TELEGRAM=true` and a token is present.

## Operator tasks after base deployment is healthy
1. Add `TELEGRAM_BOT_TOKEN` as a Railway secret.
2. Set `ENABLE_TELEGRAM=true`.
3. Update channel IDs via env overrides or seeded config for a **private test channel only**.
4. Add the bot as admin to the target test channels.
5. Optionally set `COMMUNITY_FEEDBACK_SALT` and `ELITE_CHANNEL_ID` for outcome voting.

## Security note
- BATCH-05 fail-closed admin behavior is preserved.
