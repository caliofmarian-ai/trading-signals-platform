# RAILWAY VARIABLES

## Required (existing — no change)

| Variable | Description |
|---|---|
| `TELEGRAM_BOT_TOKEN` | Telegram Bot API token |
| `ADMIN_CONTROL_CHAT_ID` | Numeric chat ID of the admin Telegram group |
| `OWNER_TELEGRAM_ID` | Numeric Telegram user ID of the bot owner |
| `BINARYBOT_BASE_DIR` | Absolute base directory for all runtime data |

---

## Optional — topic routing (new)

These variables are optional. When absent, the system falls back to the existing
`ADMIN_CONTROL_CHAT_ID`-based targets. No behavior change when unset.

| Variable | Type | Default | Description |
|---|---|---|---|
| `ADMIN_ALERTS_THREAD_ID` | Integer | (uses ADMIN_CONTROL_CHAT_ID) | Thread ID for alert messages within the admin group |
| `ADMIN_ERRORS_THREAD_ID` | Integer | (uses ADMIN_CONTROL_CHAT_ID) | Thread ID for error messages within the admin group |
| `ADMIN_REPORTS_THREAD_ID` | Integer | (uses ADMIN_CONTROL_CHAT_ID) | Thread ID for report messages within the admin group |

---

## Optional — file delivery (new)

| Variable | Type | Default | Description |
|---|---|---|---|
| `MAX_DELIVERY_FILE_SIZE` | Integer (bytes) | `5242880` (5 MB) | Maximum file size that can be delivered via Telegram |

---

## How to set in Railway

1. Go to your Railway project.
2. Select the service.
3. Go to **Variables** tab.
4. Add or update the variable name and value.
5. Redeploy is triggered automatically.

---

## Setting thread IDs

To find a topic thread ID in Telegram:
1. Open the admin group.
2. Navigate to the desired topic.
3. Send any message in the topic.
4. Right-click the message → Copy Link.
5. The URL contains `.../c/{chat_id}/{thread_id}`.
6. Use the `thread_id` portion as the value.

---

## Example Railway variable export

```
TELEGRAM_BOT_TOKEN=<your-bot-token>
ADMIN_CONTROL_CHAT_ID=-100123456789
OWNER_TELEGRAM_ID=123456789
BINARYBOT_BASE_DIR=/app/data
ADMIN_ALERTS_THREAD_ID=42
ADMIN_ERRORS_THREAD_ID=43
ADMIN_REPORTS_THREAD_ID=44
MAX_DELIVERY_FILE_SIZE=5242880
```

---

## Notes

- All optional variables have safe defaults and are fully backward compatible.
- No previously required variable has been removed or renamed.
- The `MAX_DELIVERY_FILE_SIZE` default is 5 MB, which is well within Telegram's
  50 MB bot API file upload limit and appropriate for log/report files.
