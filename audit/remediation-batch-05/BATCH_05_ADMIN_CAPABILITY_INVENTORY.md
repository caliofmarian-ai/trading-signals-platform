# BATCH_05_ADMIN_CAPABILITY_INVENTORY

**Owner Decision Applied:** OWNER-002 = A (legacy bot_service Admin path retired in favor of authoritative Admin/control plane)
**Original Findings:** GAP-011, GAP-012, GAP-013
**Date:** 2026-07-13

---

## Admin Capability Inventory (Before BATCH-05)

### Entry Point 1: `core/admin_commands.py :: handle_admin_command(text, user_id)`
Canonical authoritative entry point for slash-command Admin mutations.

| Command | Handler | Auth Mechanism | Permission | Validation | Mutation Target | Persistence | Observability | Canonical | Duplicated | Required | Action |
|---------|---------|----------------|------------|------------|-----------------|-------------|---------------|-----------|------------|----------|--------|
| `/admin` | `admin_commands` | `has_permission(admin.view)` | `admin.view` | N/A (view) | None | None | None | YES | NO | YES | KEEP |
| `/strategy` | `admin_commands` | `require_permission(strategy.view)` | `strategy.view` | N/A (view) | None | None | None | YES | NO | YES | KEEP |
| `/thresholds PRE\|CONFIRM\|OPEN <val>` | `admin_commands` | `require_permission(strategy.thresholds.write)` | `strategy.thresholds.write` | `validate_algo_params` | `algo_params.json::score_thresholds` | `save_json_atomic` (GAP-011: no lock) | `_audit()` → JSONL | YES | Partial | YES | FIX (GAP-011: add lock) |
| `/sr <val>` | `admin_commands` | `require_permission(strategy.sr.write)` | `strategy.sr.write` | `validate_algo_params` | `algo_params.json::sr_required_multiplier` | `save_json_atomic` (GAP-011: no lock) | `_audit()` → JSONL | YES | Partial | YES | FIX (GAP-011: add lock) |
| `/spike <field> <val>` | `admin_commands` | `require_permission(strategy.spike.write)` | `strategy.spike.write` | `validate_algo_params` | `algo_params.json::spike_filters` | `save_json_atomic` (GAP-011: no lock) | `_audit()` → JSONL | YES | Partial | YES | FIX (GAP-011: add lock) |
| `/symbols list` | `admin_commands` | `require_permission(strategy.view)` | `strategy.view` | N/A (view) | None | None | None | YES | Partial | YES | KEEP |
| `/symbols add <sym>` | `admin_commands` | `require_permission(strategy.symbols.write)` | `strategy.symbols.write` | N/A | `active_symbols.json` | `save_json_atomic` (GAP-011: no lock) | `_audit()` → JSONL | YES | Partial | YES | FIX (GAP-011: add lock) |
| `/symbols remove <sym>` | `admin_commands` | `require_permission(strategy.symbols.write)` | `strategy.symbols.write` | N/A | `active_symbols.json` | `save_json_atomic` (GAP-011: no lock) | `_audit()` → JSONL | YES | Partial | YES | FIX (GAP-011: add lock) |
| `/engine` | `admin_commands` | `require_permission(engine.view)` | `engine.view` | N/A (view) | None | None | None | YES | NO | YES | KEEP |
| `/debug` | `admin_commands` | `require_permission(debug.view)` | `debug.view` | N/A (view) | None | None | None | YES | NO | YES | KEEP |
| `/report` | `admin_commands` | `require_permission(reports.view)` | `reports.view` | N/A (view) | None | None | None | YES | NO | YES | KEEP |
| `/roles` | `admin_commands` | `require_permission(roles.view)` | `roles.view` | N/A (view) | None | None | None | YES | NO | YES | KEEP |
| `/roles_reload` | `admin_commands` | `require_permission(roles.write)` | `roles.write` | N/A | roles cache | `lru_cache.clear()` | `_audit()` → JSONL | YES | NO | YES | KEEP |
| `/affiliate` | `admin_commands` | `require_permission(affiliate.view)` | `affiliate.view[.own/.any]` | N/A (view) | None | None | None | YES | NO | YES | KEEP |

---

### Entry Point 2 (LEGACY): `core/bot_service.py :: handle_admin_command(chat_id, user_id)`
Legacy panel entry point. Uses local RBAC (`get_role()`), not canonical `admin_permissions`.

| Capability | Auth | Permission | Mutation | Persistence | Action |
|-----------|------|------------|----------|-------------|--------|
| Display Admin panel | `get_role()` / `in_admin_context()` | ROLE_OWNER/ADMIN | None | None | RETIRE (GAP-013) |

---

### Entry Point 3 (LEGACY): `core/bot_service.py :: handle_callback(chat_id, user_id, data)`
Legacy callback handler. Uses local RBAC. Contains both VOTE forwarding (BATCH-04) and Admin mutations.

| Callback | Auth | Permission | Mutation | Persistence | Canonical | Action |
|----------|------|------------|----------|-------------|-----------|--------|
| `VOTE_\|<sig>\|<outcome>` | None (public) | None | None (forwards to outcome_service) | Via outcome_service | YES | KEEP (DELEGATE to outcome_service) |
| `VOTE_<generic>` | None (public) | None | None (forwards to outcome_service) | Via outcome_service | YES | KEEP (DELEGATE to outcome_service) |
| `OUTCOME:<outcome>:<sig>` | `in_admin_context()` (fail-open!) | ROLE_OWNER/ADMIN | `_record_outcome()` (independent) | `outcomes.json` (bypasses outcome_service!) | NO | MIGRATE → outcome_service |
| `ADMIN_STATUS` | `get_role()` + `in_admin_context()` | ROLE_OWNER/ADMIN/ANALYST/MODERATOR | None (view) | None | NO | RETIRE |
| `ADMIN_SET_BUFFER` | `get_role()` + `in_admin_context()` | ROLE_OWNER/ADMIN | None (UI only) | None | NO | RETIRE |
| `BUFFER_SMALL/MEDIUM/LARGE` | `get_role()` | ROLE_OWNER/ADMIN | `_do_set_buffer()` → settings.json | `save_json_atomic` | NO | RETIRE (buffer mode not in canonical v2) |
| `ADMIN_SET_SYMBOLS` | `get_role()` + `in_admin_context()` | ROLE_OWNER/ADMIN | None (UI only) | None | NO | RETIRE |
| `SYM_TOGGLE:<sym>` | `get_role()` | ROLE_OWNER/ADMIN | `_do_toggle_symbol()` → symbols.json | `save_json_atomic` | NO | RETIRE (use `/symbols add/remove`) |
| `ADMIN_RESEARCH` | `get_role()` + `in_admin_context()` | ROLE_OWNER/ADMIN/ANALYST | None (placeholder) | None | NO | RETIRE |
| `ADMIN_DOCS` | `get_role()` + `in_admin_context()` | ROLE_OWNER/ADMIN/ANALYST/MODERATOR | None (UI only) | None | NO | RETIRE |
| `DOC:<filename>` | `get_role()` | All roles | None (file serving) | None | NO | RETIRE |
| `ADMIN_BACK` | `get_role()` | All roles | None (UI only) | None | NO | RETIRE |

---

### Legacy-Only Mutations (Not in Canonical Admin Plane)

| Capability | Location | Decision |
|-----------|---------|---------|
| Buffer mode control (`BUFFER_SMALL/MEDIUM/LARGE`) | `bot_service._do_set_buffer()` | RETIRE — buffer concept superseded by canonical v2 spec |
| Symbol toggle UI (`SYM_TOGGLE:`) | `bot_service._do_toggle_symbol()` | RETIRE — `/symbols add/remove` in canonical admin_commands covers this |
| Docs viewer (`ADMIN_DOCS`, `DOC:`) | `bot_service._ui_docs_menu()`, `_do_send_doc()` | RETIRE — documentation viewer not in canonical v2 |
| Research panel placeholder (`ADMIN_RESEARCH`) | `bot_service` | RETIRE — placeholder only |
| Legacy RBAC (`get_role`, `require_role`, `_load_rbac`) | `bot_service` | RETIRE (GAP-013) |
| Independent outcome store (`_record_outcome`) | `bot_service` | RETIRE (replaced by outcome_service delegation) |
| `in_admin_context()` fail-open | `bot_service` | FIX to fail-closed (GAP-013) |

---

## Post-BATCH-05 State

Single authoritative Admin control plane: **`admin_commands.handle_admin_command()`**

`bot_service.py` residual responsibilities after BATCH-05:
1. Dispatch slash commands to `handle_admin_command_v2` (canonical)
2. Forward VOTE_ callbacks to `outcome_service` (BATCH-04 canonical path)
3. Forward legacy OUTCOME: callbacks to `outcome_service` (not independent mutation)
4. Reject retired Admin panel callbacks with clear message
5. Deny all Admin callbacks when ADMIN_CONTROL_CHAT_ID not configured (fail-closed)
