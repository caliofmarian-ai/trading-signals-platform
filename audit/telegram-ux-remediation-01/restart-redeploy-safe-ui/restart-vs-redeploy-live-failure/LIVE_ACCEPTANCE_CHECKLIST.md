# LIVE_ACCEPTANCE_CHECKLIST.md
# Issue #31 — Live Acceptance Checklist

## USER Flow

- [ ] Start from a working USER session
- [ ] Delete the entire USER conversation
- [ ] Send `/start`
- [ ] Confirm exactly one visible replacement message
- [ ] Send `/status`
- [ ] Confirm the replacement is edited (not a new message)

## ADMIN Flow

- [ ] Start from a working ADMIN/OWNER session
- [ ] Delete the entire ADMIN conversation
- [ ] Send `/start`
- [ ] Confirm exactly one visible replacement message
- [ ] Open Admin → Engine → Home
- [ ] Confirm one message is continuously edited

## After Railway Restart

- [ ] Delete both conversations again
- [ ] Send `/start` from each account → confirm recovery for both
- [ ] Perform Railway Restart
- [ ] Wait for confirmed poller heartbeat in Railway logs (look for `"event": "poller_started"`)
- [ ] Send `/start` from USER → must respond WITHOUT Redeploy
- [ ] Send `/start` from ADMIN → must respond WITHOUT Redeploy

## After Railway Redeploy

- [ ] Perform Railway Redeploy
- [ ] Send `/start` from USER → confirm response
- [ ] Send `/start` from ADMIN → confirm response

## Lock Recovery

- [ ] Verify Railway logs show no `TimeoutError` for lock acquisition
- [ ] Verify no `"stale_lock_reclaimed"` events after Redeploy (clean start)
- [ ] Verify only one `"poller_started"` event per deployment

## Diagnostics to Check in Railway Logs

```
{"event": "poller_started", "component": "telegram_poller", ...}
{"event": "stale_lock_reclaimed", "component": "storage_lock", ...}  ← only on Restart if lock was stale
{"code": "TELEGRAM_UI_STATE_INITIALIZED", ...}
```

## Issue #31 Acceptance Criteria

This issue is NOT complete until all checklist items above are verified in production.
Do NOT close Issue #31 based on this PR alone.
