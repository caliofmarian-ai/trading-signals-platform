# RAILWAY_VARIABLE_CHECKLIST.md

## Required now
- [ ] `BINARYBOT_BASE_DIR=/data`
- [ ] `SHADOW_MODE=true`
- [ ] `ENABLE_BROKER_EXECUTION=false`
- [ ] `ENABLE_TELEGRAM=false` (safe first deploy)
- [ ] `TWELVE_DATA_API_KEY` set as a Railway secret

## Add before Telegram testing
- [ ] `TELEGRAM_BOT_TOKEN`
- [ ] private channel ID overrides or verified seeded config values
- [ ] `COMMUNITY_FEEDBACK_SALT` (32+ chars) if outcome voting is desired
- [ ] `ELITE_CHANNEL_ID` if outcome voting is desired

## Optional overrides
- [ ] metadata vars (`SERVICE_NAME`, `BOT_ENV`, `BOT_VERSION`, `GIT_SHA`, `RUN_ID`)
- [ ] admin routing vars (`OWNER_TELEGRAM_ID`, `ADMIN_CONTROL_CHAT_ID`, `ADMIN_CONTROL_THREAD_ID`)
- [ ] explicit path overrides if not using derived defaults
