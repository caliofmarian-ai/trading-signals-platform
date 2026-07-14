# SHADOW_MODE_CONTRACT.md

## Explicit mode
- `SHADOW_MODE=true` is required.
- `ENABLE_BROKER_EXECUTION=false` is required.
- Telegram is optional via `ENABLE_TELEGRAM`.

## Guaranteed shadow behavior
- strategy evaluation remains enabled
- FSM, observability, analytics, and research remain enabled
- no broker execution path is added
- no Pocket Option integration is added
- no paper-trading executor is added
- no live-trading execution path is added

## Telegram handling
- `ENABLE_TELEGRAM=false`: system boots without Telegram polling.
- `ENABLE_TELEGRAM=true`: `TELEGRAM_BOT_TOKEN` is required.
