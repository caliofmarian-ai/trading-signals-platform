# AUTHORIZATION CHANGE REPORT

## Summary

This report documents the authorization changes introduced in this restoration,
per the requirements in the problem statement and the forensic audit findings.

---

## AUTH-001: Owner private DM — new commands added

**Finding (from FORENSIC_AUDIT_SUMMARY.md AUTH-001):**
The authorization code is correct when `OWNER_TELEGRAM_ID` is configured.
No code regression was present; the issue was a configuration omission.

**Change:**
`_OWNER_PRIVATE_COMMANDS` in `send/core/bot_service.py` was extended to include
the new commands:

```python
_OWNER_PRIVATE_COMMANDS: frozenset[str] = frozenset({
    "/admin", "/strategy", "/thresholds", "/sr", "/spike", "/symbols",
    "/engine", "/debug", "/report",
    "/files", "/docs", "/download", "/log", "/diagnose", "/audit_runtime",  # NEW
    "/roles", "/affiliate",
})
```

`/roles_reload` is intentionally excluded from owner private DM (AUTH-004).

---

## AUTH-002: `RELOAD_ROLES_CONFIRM` blocked in private DM

**Preserved behavior:** The `RELOAD_ROLES_CONFIRM` and `RELOAD_ROLES_EXEC` callbacks
continue to be blocked for owner-private context.

This is a security design choice documented in AUTH-004 of the forensic audit.
It prevents roles reload from private DM to reduce the risk of accidentally
invalidating admin access.

---

## AUTH-003: Callback authorization — same rules as slash commands

All new callbacks route through `_handle_admin_navigation_action`, which is
called only after `_can_use_admin_callback` passes.

`_can_use_admin_callback` enforces:
- Owner private DM: only if `is_owner(user_id)` returns True.
- Admin topic: only if `in_admin_context(chat_id)` and thread ID matches.

The new callbacks (`SYM_TOGGLE:*`, `PROFILE_EXEC:*`, `FILE_DL:*`, etc.) are
all routed through this same gate.

---

## AUTH-004: Fail-closed behavior preserved

All fail-closed rules from BATCH-05 are unchanged:

| Rule | Status |
|---|---|
| `ADMIN_CONTROL_CHAT_ID == 0` → deny | Preserved |
| Missing `admin_roles.json` → USER role → deny | Preserved |
| Missing `OWNER_TELEGRAM_ID` → `is_owner()` returns False → deny | Preserved |
| Unknown role → empty permissions → deny | Preserved |

---

## AUTH-005: New permissions added (non-breaking)

Two new permissions were added to the permission matrix:

| Permission | Roles |
|---|---|
| `files.view` | OWNER, PRIMARY_ADMIN, STRATEGY_ADMIN, RESEARCH_ADMIN |
| `diagnostics.view` | OWNER, PRIMARY_ADMIN |

These are additive-only changes. Existing permissions are unchanged.

---

## AUTH-006: Rate limiting

Per-user in-memory rate limiting was added to bot_service.py for the following operations:

| Operation | Max calls | Window |
|---|---|---|
| `files_list` | 20 | 60s |
| `file_download` | 10 | 60s |
| `diagnose` | 5 | 60s |
| `audit_runtime` | 3 | 60s |
| `mutation` (symbol toggle, profile apply) | 30 | 60s |

Rate-limited users receive a clear "Rate limit exceeded" message; no state is mutated.

---

## What did NOT change

- No password authentication was added (forensic audit confirmed no historical password).
- No session tokens or TTL state was added.
- No new env variables for auth were added (only optional topic routing and file-size limit).
- `ADMIN_CONTROL_CHAT_ID` remains the sole gate for admin-topic access.
- `OWNER_TELEGRAM_ID` remains the sole identity for owner private-DM access.
