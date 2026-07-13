# BATCH_05_IMPLEMENTATION_REPORT

**Owner Decision Applied:** OWNER-002 = A
**Original Findings Resolved:** GAP-011, GAP-012, GAP-013
**Implementation Date:** 2026-07-13
**Baseline Tests Passing (Before):** 84
**BATCH-05 Tests Added:** 55
**Total Tests Passing (After):** 139

---

## Summary

BATCH-05 consolidated the Admin/control plane to a single authoritative path:

1. **GAP-011**: Added `storage.with_lock()` around all read-modify-write mutation cycles in `admin_commands.py`. Five mutation helpers now hold the appropriate named lock during their full read-validate-write operation.

2. **GAP-012**: Added `load_permissions_config()` to `admin_permissions.py` that reads and parses `admin_permissions.json`. The function is cached with `lru_cache(maxsize=1)`. `list_permissions_for_user()` now merges permissions from both the hardcoded `PERMISSION_MATRIX` and the file-based config. If the file is absent or malformed, the hardcoded matrix applies (safe fallback, no regression).

3. **GAP-013**: Retired the legacy `bot_service.py` Admin/control-plane panel path:
   - `in_admin_context()` changed from fail-open to fail-closed
   - All independent RBAC functions removed (`get_role`, `require_role`, `_load_rbac`)
   - All legacy Admin mutations removed (`_do_set_buffer`, `_do_toggle_symbol`, `_record_outcome`, etc.)
   - All legacy Admin callback handlers retired (return clear rejection messages)
   - `OUTCOME:` callback format migrated to delegate to `outcome_service`
   - VOTE_ forwarding preserved intact (BATCH-04 compatibility)

---

## Files Modified

### `send/core/admin_commands.py`
- `_set_threshold()`: Wrapped body with `with _storage.with_lock("algo_params")`
- `_set_sr()`: Wrapped body with `with _storage.with_lock("algo_params")`
- `_set_spike()`: Wrapped body with `with _storage.with_lock("algo_params")`
- `_symbols_add()`: Wrapped body with `with _storage.with_lock("active_symbols")`
- `_symbols_remove()`: Wrapped body with `with _storage.with_lock("active_symbols")`

### `send/core/admin_permissions.py`
- Added `PERMISSIONS_CONFIG_PATH` constant (env `ADMIN_PERMISSIONS_CONFIG` or default path)
- Added `_ROLE_NAME_MAP` dict (lowercase role names → canonical ROLE_* constants)
- Added `load_permissions_config()` with `@lru_cache(maxsize=1)` — reads and parses `admin_permissions.json`
- Added `reload_permissions_config()` — clears `load_permissions_config` cache
- Modified `list_permissions_for_user()` — merges file-based matrix with hardcoded `PERMISSION_MATRIX`

### `send/core/bot_service.py`
- **Removed**: All legacy RBAC (`get_role`, `require_role`, `_load_rbac`, `ROLE_OWNER`, `ROLE_ADMIN`, `RBAC_PATH`, `ADMIN_USER_ID`)
- **Removed**: All legacy Admin panel UI builders and mutations (`render_admin_panel`, `handle_admin_command`, `_ui_*`, `_do_*`, `_record_outcome`, `_save_outcomes_store`, `_load_outcomes_store`, `_proof`, `kb`, `btn`)
- **Removed**: All legacy path/env constants for retired functions
- **Fixed**: `in_admin_context()` — fail-closed (returns `False` when `ADMIN_CONTROL_CHAT_ID == 0`)
- **Fixed**: `handle_callback()` — VOTE_ forwarding preserved; `OUTCOME:` now delegates to `outcome_service`; Admin panel callbacks return retirement message
- **Preserved**: `OUTCOMES_PATH` attribute, `process_update()`, VOTE forwarding, imports of `outcome_service` and `handle_admin_command_v2`

---

## Files Created

### `tests/batch_05/__init__.py`
Empty package marker.

### `tests/batch_05/test_admin_control_plane.py`
55 tests covering:
- Control-plane uniqueness (CP-1 through CP-6)
- Authorization / permissions (AU-7 through AU-17)
- Mutation safety (MS-18 through MS-25)
- Observability / security (OB-26 through OB-30)
- Cross-batch regression (XB-31 through XB-43)
- GAP-011 specific lock tests
- GAP-012 specific permissions file loading tests
- GAP-013 specific RBAC retirement tests

---

## Commands Executed

```bash
# Baseline test run
PYTHONPATH=send python -m pytest tests/ -q --tb=short
# Result: 84 passed

# Import validation after each change
PYTHONPATH=send python -c "import core.bot_service; import core.admin_commands; import core.admin_permissions; print('OK')"

# BATCH-05 test run
PYTHONPATH=send python -m pytest tests/batch_05/ -q --tb=short
# Result: 55 passed

# Full suite regression
PYTHONPATH=send python -m pytest tests/ -q --tb=short
# Result: 139 passed
```

---

## Role/Permission Configuration Changes

No changes to `send/config/admin_roles.json` or `send/config/admin_permissions.json`. The `admin_permissions.json` file previously on disk is now actually consumed by code (GAP-012 closed). Its content was already consistent with the hardcoded `PERMISSION_MATRIX`.

---

## Event Schema Changes

No event schema changes. Admin mutations continue to emit `event_type="admin_change"` events via `_audit()` in `admin_commands.py`. The schema is unchanged.

---

## OWNER-003 / BATCH-06 Scope

- OWNER-003 segmented-state migration: NOT started (as required)
- BATCH-06 FSM/restart work: NOT started (as required)
- No analytics/research remediation
- No deployment, Railway, Telegram credential, broker, or trading execution changes
