# OWNER_DECISIONS_APPLIED

- Restored `/start`, `/help`, and `/status` in the active canonical path `runtime.telegram_updates -> core.bot_service -> canonical command/permission modules -> core.telegram_publisher`.
- Added explicit fallback for unknown slash commands: `Unknown command. Use /help to view available commands.`
- Fixed reply routing so replies stay in the originating private chat, group chat, or topic thread.
- Kept admin context and canonical permission checks fail-closed.
- Wired Railway startup/recovery/blocked/degraded/shutdown notifications to `ADMIN_CONTROL_CHAT_ID` with topic use only when the configured chat can safely use a thread id.
- Wired operational escalation and recovery notifications to `ADMIN_PROOF_CHAT_ID` with bounded aggregation.
- Added Twelve Data HTTP 429 failure handling without changing WIDE SCAN, FOCUS MODE, scan gates, or normal cadence when market data is available.
- Canonicalized malformed error events before schema validation and bounded repeated observability log failures.
- Reconnected admin-proof Telegram delivery while preserving local JSONL proof persistence even when Telegram delivery fails.
- Treated placeholder `RUN_ID` / `GIT_SHA` values safely and generated a runtime run id when needed.
