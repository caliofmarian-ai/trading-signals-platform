# DIAGNOSTICS IMPLEMENTATION REPORT

## Overview

Two diagnostic commands have been implemented in `send/core/admin_commands.py`:
`/diagnose` and `/audit_runtime`.

---

## `/diagnose`

### Handler: `handle_diagnose(user_id)`

**Permission required:** `diagnostics.view`

### Output sections

| Section | Source | Notes |
|---|---|---|
| Runtime phase | `RUNTIME_PHASE` env var | Defaults to "unknown" |
| Telegram polling | `TELEGRAM_POLLING_ACTIVE` env var | "active" / "inactive" |
| Market data | Checks if any symbol is active | Uses `_load_active_symbols()` |
| FSM status | `FSM_STATE` env var | Defaults to "unknown" |
| Shadow mode | `SHADOW_MODE` env var | "true" = shadow |
| Broker execution | `BROKER_EXECUTION_ACTIVE` env var | "active" / "inactive" |
| Recovery state | `RECOVERY_ACTIVE` env var | "active" / "inactive" |
| Recent incidents | Last 5 error events from `engine_error_events.jsonl` | Timestamps + type only |
| File availability | Checks existence of key observability files | observability, outcomes, analytics |

### Format

Plain text with emoji markers:
- 🟢 = operational / active
- 🔴 = inactive or error
- ⚪ = unknown or not configured
- 🟡 = degraded or shadow mode

---

## `/audit_runtime`

### Handler: `handle_audit_runtime(user_id)`

**Permission required:** `diagnostics.view`

### Artifact contents

The artifact is a formatted text document sent via `send_document`:

1. **Header:** timestamp, runtime phase, audit version.
2. **Environment matrix:** Presence/absence of each known env variable (no values).
3. **Directory inventory:** Size and file count for each allowed directory.
4. **Recent observability events:** Last `AUDIT_MAX_EVENTS` (50) engine events.
   - Timestamps and event types only.
   - No raw event data that could contain trade details.
5. **Recent error summary:** Last `AUDIT_MAX_ERRORS` (20) error events.
   - Timestamps, error types, and sanitized messages.
6. **Active configuration summary:** Key algo_params values with secrets redacted.
   - Explicitly redacted fields: any key matching the secret-pattern list.

### Redaction rules

The following fields are NEVER included in the runtime audit artifact:
- `TELEGRAM_BOT_TOKEN`
- `TWELVE_DATA_API_KEY` (or any API key / secret)
- `COMMUNITY_FEEDBACK_SALT`
- Any env variable whose name contains: `TOKEN`, `SECRET`, `PASSWORD`, `KEY`, `SALT`,
  `CREDENTIAL`, `PRIVATE`, `API`

---

## Sanitized output guarantee

Both commands redact the following patterns before producing any output:
- All API key values (replaced with `[REDACTED]`)
- All token values (replaced with `[REDACTED]`)
- All secret values (replaced with `[REDACTED]`)

The redaction is applied recursively to all string values in any dict/list
sourced from environment variables or observability files.

---

## Error handling

- If the observability directory does not exist or a file cannot be read, the
  respective section shows `(not available)` rather than raising an exception.
- If `send_document` fails, the user receives a text error message with the failure reason.
- If the audit artifact generation itself fails, the error is logged as an
  `admin_event` observability entry.
- Diagnostics commands do not mutate any state.

---

## Rate limits

| Command | Max calls | Window |
|---|---|---|
| `/diagnose` | 5 | 60s |
| `/audit_runtime` | 3 | 60s |

Exceeding the rate limit returns an error message; no partial output is generated.

---

## Callback access

The audit and diagnose commands are also accessible via admin-home buttons:
- `🩺 Diagnose` → `ADMIN_NAV:DIAGNOSE` → runs `handle_diagnose`
- `🔍 Runtime Audit` → `ADMIN_NAV:AUDIT_RUNTIME` → runs `handle_audit_runtime`

These callbacks require the same `diagnostics.view` permission and respect the
same rate limits as the slash commands.
