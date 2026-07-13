# HEALTH_AND_READINESS_CONTRACT.md

## Commands
- Readiness: `PYTHONPATH=send python -m scripts.railway_healthcheck --mode readiness`
- Liveness: `PYTHONPATH=send python -m scripts.railway_healthcheck --mode liveness`

## Readiness checks
- `SHADOW_MODE=true`
- `ENABLE_BROKER_EXECUTION=false`
- `TWELVE_DATA_API_KEY` present
- `TELEGRAM_BOT_TOKEN` present when `ENABLE_TELEGRAM=true`
- critical runtime modules import cleanly
- persistent root writable
- seeded config loads and validates
- existing critical state files validate when present
- restart guard is not frozen

## Liveness checks
- runtime status file exists
- recorded PID is alive
- runtime phase is `starting` or `running`

## Non-goals
- No live Telegram or market-data calls
- No HTTP server added
- Readiness is not declared merely because a Python process exists
