# R-017 — Live Admin configuration reconciliation — 2026-09-15

## Status

`SOURCE FIX IN PROGRESS / LIVE ACCEPTANCE NOT YET PASS`

This record does not claim Telegram acceptance. It records only the configuration defects and the bounded remediation used to prepare a new production verification.

## Verified blockers carried from live evidence

1. The real `ADMIN_COMMANDS` forum topic was previously identified as Bot API chat `-1003726714813`, thread `1310`.
2. Live `/admin` in that topic returned `Access denied (wrong chat)`, so production Admin context did not match the real topic at the time of that test.
3. Owner-supplied Telegram evidence corrected the actual PRIMARY_ADMIN test account to `6766369444`.
4. Repository `send/config/admin_roles.json` still contained stale PRIMARY_ADMIN identity `6766367444` before this remediation.
5. These are independent blockers because Admin context is checked before role/permission evaluation.

## Current-source audit

Current `bot_service.py` remains fail-closed:

- `ADMIN_CONTROL_CHAT_ID == 0` denies access;
- Admin-topic commands require matching chat context;
- when `ADMIN_CONTROL_THREAD_ID` resolves to a valid thread, the incoming thread must match.

Previously reported delivery defects are already repaired in current `main`:

- file-return markers are preserved so `/audit_runtime` can dispatch the document rather than exposing a temporary path;
- interactive send failures emit observable diagnostics and a sanitized text fallback instead of disappearing silently.

## Repository correction

`send/config/admin_roles.json` now uses PRIMARY_ADMIN `6766369444`.

Because Railway intentionally preserves existing `/data/config/admin_roles.json`, source correction alone is insufficient. `scripts/admin_role_reconcile.py` therefore adds a migration hook that:

- is disabled by default;
- runs only when `ADMIN_PRIMARY_ADMIN_SYNC_FROM_SOURCE=true`;
- copies only the repository `primary_admin` list into persistent role configuration;
- validates identities as positive integers;
- preserves all other role lists, affiliate records, and permission configuration;
- refreshes the in-process role cache after a change.

The migration flag is intended to be enabled for the reconciliation deployment, verified, and then disabled without another migration.

## Production actions after merge

After exact-head CI passes and this change merges:

1. set `ADMIN_CONTROL_CHAT_ID=-1003726714813`;
2. set `ADMIN_CONTROL_THREAD_ID=1310`;
3. temporarily set `ADMIN_PRIMARY_ADMIN_SYNC_FROM_SOURCE=true`;
4. require Railway terminal deployment status `SUCCESS`;
5. verify startup/runtime logs contain no migration/startup failure;
6. disable `ADMIN_PRIMARY_ADMIN_SYNC_FROM_SOURCE` after the successful reconciliation;
7. perform/record a new live PRIMARY_ADMIN journey in `ADMIN_COMMANDS` before R-017 can be closed.

## Safety boundaries

No role permission ceiling is widened. No strategy math, provider policy, market-data policy, signal-distribution semantics, monetization behavior, or broker execution is changed. Broker execution remains outside this remediation.
