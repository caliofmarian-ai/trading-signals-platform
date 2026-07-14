# MARKET_DATA_DEPLOYMENT_PREPARATION.md

## Prepared behavior
- Credential source: `TWELVE_DATA_API_KEY` only.
- Missing key now fails clearly before any HTTP request.
- No market-data calls occur during init, tests, readiness checks, or build validation.

## Runtime behavior
- `runtime.market_client.fetch_klines()` raises `RuntimeError("TWELVE_DATA_API_KEY missing")` if the key is absent.
- Request timeout remains `20s` with up to `3` attempts in active runtime code.

## Operator task
- Add a real Twelve Data key in Railway secrets before expecting live signal generation.
