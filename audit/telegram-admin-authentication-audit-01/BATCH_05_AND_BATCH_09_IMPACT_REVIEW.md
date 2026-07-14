# BATCH_05_AND_BATCH_09_IMPACT_REVIEW

## BATCH-05 impact (commit `d7e7213`)

### What changed
- Retired legacy inline admin panel callback control plane.
- Removed independent RBAC functions from `bot_service`.
- Consolidated control plane into canonical slash-command handler (`admin_commands`).
- Kept fail-closed context logic for admin callback family.

### Authentication implication
- Did **not** remove password login flow (none found).
- Did remove legacy panel UX and callback actions that user could remember as old admin experience.

## BATCH-09 impact (commit `63834b3`)

### What changed
- Deleted `send/legacy/bot_control.py` (legacy Telegram runner with visual keyboards).

### Authentication implication
- Deleted module had no password/session auth flow.
- Removed a visually distinct Telegram interface (`/start` panel, `/buffer`, symbol selector keyboards), increasing UX gap vs remembered Hetzner behavior.

## Later remediation impact (post-BATCH-09)
Commit `49aaeb4` introduced admin slash command chat-context denial (`wrong chat`) before permission checks. This is the proximate cause of live private-chat admin denial.
