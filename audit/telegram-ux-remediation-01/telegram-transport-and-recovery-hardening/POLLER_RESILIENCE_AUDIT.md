# POLLER RESILIENCE AUDIT

## Architecture

`send/runtime/telegram_updates.py` — `poll_updates()` runs an infinite loop:

```
while True:
    try:
        getUpdates (long poll, timeout=30, requests timeout=35)
        for each update:
            LAST_UPDATE_ID = update_id + 1
            process_update(update)
    except Exception as e:
        log_error(sanitize(str(e)))
        sleep(3)
```

## Resilience properties

| Scenario | Before fix | After fix |
|---|---|---|
| `getUpdates` network error | Caught, logged (token may leak), sleep 3, retry | Caught, logged (token redacted), sleep 3, retry |
| `getUpdates` returns `ok: false` | `continue` (sleep POLL_INTERVAL=1.5) | same |
| Single `process_update` crash | Aborts current batch; remaining updates in batch skipped; next poll cycle delivers them via offset | same |
| Both edit and send_message fail | Silently dropped | Now logged via `telegram_app_nav_send_failure` event |
| APP:/ADMIN_NAV: callback not acked | 10-second Telegram spinner, "error occurred" message | Immediately acked with empty response |

## Token leakage risk

`requests` exceptions embed the full URL in `str(e)`.  For `getUpdates`:
```
HTTPSConnectionPool(host='api.telegram.org', port=443): Max retries exceeded
with url: /bot123456789:AABBccdd/getUpdates?timeout=30&offset=N
```

The `_sanitize()` helper in `telegram_publisher` uses the regex
`(?<=/bot)\d+:[A-Za-z0-9_-]+` to redact the token segment.

## LAST_UPDATE_ID advance semantics

`LAST_UPDATE_ID` is advanced to `update_id + 1` *before* `process_update` is called.
This means:
- If `process_update` crashes, the update is marked consumed and will not be redelivered.
- This is intentional: redelivery of a crashing update would loop indefinitely.
- The trade-off is that a crashing update is lost rather than retried.
- A future improvement would be to advance `LAST_UPDATE_ID` *after* successful processing
  and implement a dead-letter budget for persistently crashing updates.

## Offset persistence

`LAST_UPDATE_ID` is an in-memory module global.  After a process restart it resets to
`None`, which causes Telegram to redeliver unacknowledged updates from the server's queue
(up to 24 hours).  This is the correct behaviour for recovery after a Railway restart.

## Post-fix residual risks

- A crash inside `process_update` in the middle of a batch skips remaining batch items
  until the next poll cycle (see above).
- Long-poll timeout (30s) plus requests timeout (35s) means a hung TCP connection could
  block the poller for up to 35 seconds before the exception is raised and sleep begins.
  No change to this timing; it is an acceptable production configuration.
