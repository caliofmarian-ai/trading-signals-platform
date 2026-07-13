# RAILWAY_PREPARATION_SCOPE.md

- Scope: prepare the current repository for Railway deployment in **signal-only / shadow mode**.
- In scope: production dependency declaration, Railway config, env contract, persistent-volume contract, init/start/health helpers, deployment-preparation tests, operator documentation.
- Out of scope: Railway project creation, owner account access, secret provisioning, live deployment, Telegram activation, market-data activation, broker execution, Pocket Option integration, paper trading, live trading, strategy changes.
- Safety posture: shadow mode only; broker execution remains impossible; Telegram remains opt-in and disabled by default.
