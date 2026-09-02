# R-011 — FREE Entitlement Limit Reconciliation

Status: VALIDATED — AWAITING MERGE
Issue: #118
PR: #119
Parent: #97
Base main commit: `e42abad1ebec47f075eee8f7de78f8085bdc4732`
Validated implementation head: `55e0750efa74b3dacaaad66f0da6985a9591d799`

## Canonical decision

The governed FREE baseline is 6 successful `OPEN_NOW` publications per reset window. BASIC remains 20, PRO remains 50, and ELITE remains unlimited.

The existing runtime configuration precedence is preserved: an explicit valid environment value may override persisted configuration; persisted configuration may override the canonical runtime default. R-011 does not remove this governed configuration capability. Instead, it removes stale repository baselines and makes the effective source visible to authorized operators.

## Reconciliation

- `.env.example`: FREE baseline 5 -> 6.
- `send/config/channel_config.json`: FREE baseline 5 -> 6.
- live legacy and v3 runtime defaults remain 6.
- Telegram Distribution Control now reads the effective live distribution config/state rather than presenting a placeholder configuration summary.
- each route exposes effective state, current successful `OPEN_NOW` counter/limit, mapping readiness, and limit source (`ENV`, `PERSISTED_CONFIG`, or `CANONICAL_DEFAULT`).
- invalid environment limit text is not falsely reported as the effective ENV source when runtime falls back to persisted/default truth.
- unlimited tiers retain and display the objective current counter (for example `0/UNLIMITED`).
- unavailable config/state fails visibly rather than claiming health.

## Validation

GitHub Actions run `33650971311` on PR #119 merge candidate `1e2fe811c3298a261c1835509d4c0a271d26247a` completed successfully:

- market-data provider selector: 5 passed;
- Telegram admin regression: 72 passed;
- full repository regression suite: 1046 passed.

The full-suite tests are reload-safe against legacy restart-recovery tests that intentionally purge and re-import the `core` package.

## Scope boundary

No strategy threshold, TPS, S/R rule, provider selection, Finnhub licensing guard, FSM lifecycle, Execution Time behavior, publication counting semantic, or broker execution setting is changed by R-011.
