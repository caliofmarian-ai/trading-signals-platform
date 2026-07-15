# CHANGED_FILES

## Audit metadata

- **Audited HEAD at audit start:** `0e736ae251dcb81dee7d13a34bbcfafcafe36967`
- **Branch:** `copilot/telegram-capability-recovery-audit`
- **Audit date:** 2026-07-15
- **No application code was modified. Only forensic audit report files were created.**

---

## Files created in this audit session

All files are in `audit/telegram-auth-and-ui-forensic-audit-01/`:

| File | Description | Size (approx) |
|---|---|---|
| `TELEGRAM_AUTH_FORENSIC_AUDIT.md` | Authentication forensic audit: 8 mandatory questions answered with exact code evidence | ~13,000 chars |
| `AUTH_FLOW_DIAGRAM.md` | ASCII flow diagrams: slash-command auth, is_owner chain, callback auth, historical comparisons | ~8,500 chars |
| `OWNER_ACCESS_COMPARISON.md` | Owner access matrix: what is allowed/blocked in private DM vs admin topic; Railway variables | ~5,500 chars |
| `TELEGRAM_LEGACY_UI_INVENTORY.md` | Complete inventory of all legacy UI screens: Era A (runner) and Era B (admin panel) | ~7,500 chars |
| `TELEGRAM_UI_FLOW_MAP.md` | Step-by-step user interaction flows for all legacy and current UI paths | ~7,300 chars |
| `TELEGRAM_BUTTON_AND_CALLBACK_REGISTER.md` | Complete callback register: all families, button labels, callback_data, actions, state files | ~10,800 chars |
| `OLD_VS_CURRENT_TELEGRAM_UI_COMPARISON.md` | Dimension-by-dimension comparison of legacy vs current UI; classification of each capability | ~8,800 chars |
| `CANONICAL_UI_RESTORATION_PLAN.md` | Single restoration architecture using only canonical control plane files; Railway variable register | ~11,500 chars |
| `FORENSIC_AUDIT_SUMMARY.md` | Executive summary of all findings; index to mandatory question answers; risk register | ~9,000 chars |
| `CHANGED_FILES.md` | This file | ~2,000 chars |

---

## No application code changes

The following files were **read but not modified**:

```
send/core/bot_service.py
send/core/admin_commands.py
send/core/admin_permissions.py
send/core/telegram_admin_ui.py
send/core/telegram_publisher.py
send/core/telegram_runtime.py
send/core/telegram_targets.py
send/core/distribution_router.py
send/legacy/bot_control.py  (git history only)
send/_archive/backups/bot_service.py.bak_step16  (git history only)
.env.example
tests/*
```

---

## Git evidence references

| Reference | Used for |
|---|---|
| `0e736ae` | Audited HEAD — current branch tip |
| `9912c14` | Prior auth audit commit |
| `49aaeb4` | Commit that introduced slash-command chat gate (per stored memory) |
| `d7e7213` | Commit where slash commands had no chat-context gate (per stored memory) |
| `0fb9112` | Initial import commit (bot_control.py, bak_step16 present) |
| `63834b3` | BATCH-09: commit that deleted send/legacy/bot_control.py |

---

## Audit commit hash

The audit commit hash (the commit that adds these 10 files) will appear in `git log` after the `engine-tools-report_progress` push completes.

Commit message: `Add telegram-auth-and-ui-forensic-audit-01: 10 required files`
