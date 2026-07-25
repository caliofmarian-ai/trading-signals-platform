# ROLLBACK PLAN

## Risk Assessment

This implementation is additive: all new handlers, callbacks, and commands
are added to existing functions. The only behavioral change is the authorization
fix (new commands added to `_OWNER_PRIVATE_COMMANDS`). No existing handlers,
data schemas, or configuration files were modified.

Risk level: **Low**

---

## Automated Rollback (Git)

To revert all changes from this implementation:

```bash
# 1. Identify the base commit SHA (before this implementation)
git log --oneline | head -5

# 2. Create a revert branch
git checkout -b revert/telegram-admin-ui-restoration

# 3. Revert to the base commit
git revert <IMPLEMENTATION_COMMIT_SHA>
# OR if multiple commits:
git revert <SHA1> <SHA2> ...

# 4. Push and create PR
git push origin revert/telegram-admin-ui-restoration
```

---

## Manual File Rollback

If a targeted rollback of specific files is needed:

### Source files to restore to their previous state

```bash
git checkout <BASE_COMMIT_SHA> -- send/core/admin_permissions.py
git checkout <BASE_COMMIT_SHA> -- send/core/telegram_admin_ui.py
git checkout <BASE_COMMIT_SHA> -- send/core/telegram_runtime.py
git checkout <BASE_COMMIT_SHA> -- send/core/telegram_targets.py
git checkout <BASE_COMMIT_SHA> -- send/core/admin_commands.py
git checkout <BASE_COMMIT_SHA> -- send/core/bot_service.py
git checkout <BASE_COMMIT_SHA> -- .env.example
```

### New files to remove

```bash
rm -rf tests/telegram_admin_ui_restoration/
# (Audit reports under audit/telegram-admin-ui-restoration-01/ are documentation only)
```

---

## Rollback Verification

After rollback, verify:

```bash
PYTHONPATH=send python -m pytest -q
# Expected: 325 passed (pre-implementation baseline)
```

---

## Railway Rollback

1. In Railway, redeploy from the base commit SHA.
2. The new optional environment variables (`ADMIN_ALERTS_THREAD_ID`, etc.) can remain
   without any effect — the reverted code ignores them.

---

## Zero-downtime consideration

The canonical Telegram polling loop is not modified. During rollback:
- The bot continues polling without interruption.
- No data migration is needed.
- No schema changes were made.
- All configuration files remain valid.

---

## What rollback does NOT restore

The forensic audit documents and implementation reports in
`audit/telegram-admin-ui-restoration-01/` are documentation artifacts;
they pose no runtime risk. They do not need to be removed in a rollback.

---

## Deferred items (not blocking rollback)

The following items were documented as deferred in IMPLEMENTATION_SUMMARY.md:
- Adaptive rate-limit tuning based on production usage patterns.
- File browser pagination UI improvements (currently text-only, buttons in future).
- Optional ADMIN_REPORTS_THREAD_ID wiring for automated report delivery.

None of these deferred items affect the rollback procedure.
