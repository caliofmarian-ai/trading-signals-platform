# R-011 — FREE Entitlement Limit Reconciliation

Status: IMPLEMENTED ON REMEDIATION BRANCH — VALIDATION PENDING
Issue: #118
Parent: #97
Base main commit: `e42abad1ebec47f075eee8f7de78f8085bdc4732`

## Canonical decision

The governed FREE baseline is 6 successful `OPEN_NOW` publications per reset window. BASIC remains 20, PRO remains 50, and ELITE remains unlimited.

The existing runtime configuration precedence is preserved: an explicit environment value may override persisted configuration; persisted configuration may override the canonical runtime default. R-011 does not remove this governed configuration capability. Instead, it removes stale repository baselines and makes the effective source visible to authorized operators.

## Reconciliation

- `.env.example`: FREE baseline 5 -> 6.
- `send/config/channel_config.json`: FREE baseline 5 -> 6.
- live legacy and v3 runtime defaults remain 6.
- Telegram Distribution Control now reads the effective live distribution config/state rather than presenting a placeholder configuration summary.
- each route exposes effective state, current counter/limit, mapping readiness, and limit source (`ENV`, `PERSISTED_CONFIG`, or `CANONICAL_DEFAULT`).
- unavailable config/state fails visibly rather than claiming health.

## Scope boundary

No strategy threshold, TPS, S/R rule, provider selection, Finnhub licensing guard, FSM lifecycle, Execution Time behavior, publication counting semantic, or broker execution setting is changed by R-011.
