# Root Cause Analysis

## Exact verified root cause
The production failure was caused by **non-deterministic Telegram active UI persistence initialization**.

### Primary defect
- PR #32 depended on a one-time import-side-effect load in `send/core/telegram_app_nav.py`.
- When that load happened before the final runtime path contract was available, `_active_ui` stayed empty for the process.
- Subsequent `/admin` requests could not find the `/start` message and fell back to `send_message()`, creating a second interactive surface.

### Secondary defect
- Persisted state writes used whole-file replacement from in-memory state, so independent instances or stale in-memory maps could destroy other session entries.

## Why this matched production evidence
- `/start` created message A.
- Restart/redeploy lost the preferred active-message target.
- `/admin` then created message B instead of editing A.
- Repeated commands could appear silent or stuck once state and visible message ownership diverged.

## Ruled-out items
- PR #32 absence on `main`: ruled out.
- Replica count > 1 in repository config: ruled out.
- Canonical `/admin` slash route bypass in current `bot_service.py`: not found after audit.
