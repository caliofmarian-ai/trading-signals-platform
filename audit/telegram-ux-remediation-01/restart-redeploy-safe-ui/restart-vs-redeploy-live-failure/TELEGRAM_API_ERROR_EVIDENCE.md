# TELEGRAM_API_ERROR_EVIDENCE.md
# Issue #31 — Telegram API Error Evidence

## Observed Error When Message is Deleted

When a user deletes the entire Telegram conversation and then sends `/start`,
the bot attempts to edit the tracked message (which no longer exists).
Telegram returns:

```json
{
  "ok": false,
  "error_code": 400,
  "description": "Bad Request: message to edit not found"
}
```

HTTP status: 400

## Classification (Post-Fix)

`TelegramAPIError.is_stale_message()` returns `True` when:
- `http_status == 400` AND description contains any of:
  - `"message to edit not found"`
  - `"message can't be edited"`
  - `"message can not be edited"`
  - `"message to be replied not found"`
- `http_status == 403` AND description contains:
  - `"bot was blocked by the user"`
  - `"user is deactivated"`

## Pre-Fix Classification (Fragile)

Used string matching on the bare exception message:
```python
detail = str(exc).lower()
if "message to edit not found" in detail:
    return "stale"
```

Problems:
- If Telegram changes wording, classification breaks
- No structured HTTP status or error_code check
- Any exception (including lockfile TimeoutError) could leak through if not handled

## Sensitive Data Not Logged

The following are NEVER captured in `TelegramAPIError` or logs:
- Bot token
- Authorization headers
- Private message content
- Full Telegram payload

The `_sanitize()` function redacts bot tokens from any string via regex.
