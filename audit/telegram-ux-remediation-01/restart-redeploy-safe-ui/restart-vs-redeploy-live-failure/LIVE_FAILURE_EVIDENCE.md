# LIVE_FAILURE_EVIDENCE.md
# Issue #31 — Restart vs Redeploy Live Failure Evidence

## Failure Sequence (Confirmed for Both Accounts)

| Step | Action | Observed Outcome |
|------|--------|-----------------|
| 1 | Bot running normally | Both USER and ADMIN sessions respond |
| 2 | Telegram conversation history deleted | — |
| 3 | User sends `/start` | **No visible response** |
| 4 | Additional commands | **No visible response** |
| 5 | Railway Restart | — |
| 6 | `/start` after Restart | **Still no visible response** |
| 7 | Railway Redeploy | — |
| 8 | `/start` after Redeploy | **Bot responds normally** |

## Affected Accounts

- Normal USER account
- ADMIN/OWNER account

## Key Observations

1. Failure is not ADMIN-only (both accounts affected)
2. Failure is not a session-key isolation issue
3. Failure **survives Railway Restart**
4. Failure **is cleared by Railway Redeploy**
5. A deployment-local or persisted runtime artifact is involved

## PR Context

- PR #35 merged to main (commit `2dce9501ef1f8069e828bca3335a478077760e25`)
- Multi-account session isolation improved
- Initial interaction appeared functional
- Final live testing FAILED

## Status

Issue #31 remains **OPEN**. This PR is a corrective Draft PR only.
