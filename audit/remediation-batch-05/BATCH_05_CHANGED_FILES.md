# BATCH_05_CHANGED_FILES

**Owner Decision Applied:** OWNER-002 = A
**Original Findings:** GAP-011, GAP-012, GAP-013

---

## Modified Files

| File | Type | Change Summary |
|------|------|----------------|
| `send/core/admin_commands.py` | Core module | Added `storage.with_lock()` to 5 mutation helpers (GAP-011) |
| `send/core/admin_permissions.py` | Core module | Added `load_permissions_config()`, `reload_permissions_config()`, `PERMISSIONS_CONFIG_PATH`, `_ROLE_NAME_MAP`; updated `list_permissions_for_user()` (GAP-012) |
| `send/core/bot_service.py` | Core module | Complete retirement of legacy Admin panel path; fail-closed `in_admin_context()`; VOTE/OUTCOME delegation preserved (GAP-013) |

## Created Files

| File | Type | Purpose |
|------|------|---------|
| `tests/batch_05/__init__.py` | Test package | Package marker |
| `tests/batch_05/test_admin_control_plane.py` | Tests | 55 BATCH-05 tests |
| `audit/remediation-batch-05/BATCH_05_ADMIN_CAPABILITY_INVENTORY.md` | Audit | Admin capability inventory before/after |
| `audit/remediation-batch-05/BATCH_05_CONTROL_PLANE_FLOW_BEFORE.md` | Audit | Before-state execution map |
| `audit/remediation-batch-05/BATCH_05_CANONICAL_CONTROL_PLANE_CONTRACT.md` | Audit | Canonical control plane contract |
| `audit/remediation-batch-05/BATCH_05_BOT_SERVICE_RETIREMENT_MAP.md` | Audit | bot_service retirement decisions |
| `audit/remediation-batch-05/BATCH_05_IMPLEMENTATION_REPORT.md` | Audit | Implementation summary |
| `audit/remediation-batch-05/BATCH_05_VALIDATION_REPORT.md` | Audit | Validation results |
| `audit/remediation-batch-05/BATCH_05_CHANGED_FILES.md` | Audit | This file |
| `audit/remediation-batch-05/BATCH_05_OPEN_FINDINGS.md` | Audit | Unresolved risks and deferred work |

---

## Not Modified

The following files were inspected but NOT modified (not required for BATCH-05):

- `send/config/admin_roles.json` — No changes needed
- `send/config/admin_permissions.json` — Already correct; now read by code
- `send/core/admin_views.py` — No changes needed
- `send/core/outcome_service.py` — BATCH-04 authority preserved unchanged
- `send/core/params_loader.py` — Unchanged
- `send/core/storage.py` — Unchanged
- `send/core/observability_logger.py` — Unchanged
- `send/runtime/telegram_updates.py` — Unchanged
- All other modules — Unchanged
- All canonical documents — Unchanged
