# BATCH_05_CONTROL_PLANE_FLOW_BEFORE

**Owner Decision Applied:** OWNER-002 = A
**Original Findings:** GAP-011, GAP-012, GAP-013

---

## Before-State Admin Execution Map (Pre-BATCH-05)

### Path A — Slash Commands (via `bot_service.process_update`)

```
Telegram message → process_update()
  → check text.startswith("/")
  → if cmd in admin_commands set:
      → handle_admin_command_v2(text, user_id)   [admin_commands.py]
          → _parse_command(text)
          → has_permission(user_id, "admin.view")  [admin_permissions.py]
              → load_roles_config()   [reads admin_roles.json or env fallback]
              → get_user_roles(user_id)
              → PERMISSION_MATRIX lookup
              ⚠ admin_permissions.json IGNORED (GAP-012)
          → cmd dispatch (switch on parts[0].lower())
          → require_permission(user_id, <specific_perm>)
          → validation (params_loader.validate_algo_params)
          → mutation helpers (_set_threshold, _set_sr, _set_spike, _symbols_add/remove)
              ⚠ NO LOCK: read then write without lock (GAP-011)
              → _save_algo_params_validated() → save_json_atomic()
          → _audit() → _append_jsonl(ADMIN_EVENTS_PATH)
          → render_* → return str
      → telegram_publisher.send_message()
```

### Path B — Admin Panel Command (via `bot_service.handle_admin_command`)
Legacy path. Uses independent RBAC.

```
Telegram message → process_update()
  → [THIS PATH NOT REACHED: handle_admin_command_v2 is called for slash cmds]
  [handle_admin_command() was reachable via direct call but not from process_update]
  → handle_admin_command(chat_id, user_id)
      → in_admin_context(chat_id)
          ⚠ FAIL-OPEN: returns True when ADMIN_CONTROL_CHAT_ID == 0 (GAP-013)
      → get_role(user_id)  [reads config/rbac.json or ADMIN_USER_ID env]
          ⚠ SEPARATE RBAC from admin_permissions.py (GAP-013)
      → render_admin_panel(user_id) [uses legacy ROLE_OWNER/ROLE_ADMIN constants]
      → return {"text": ..., "reply_markup": keyboard}
```

### Path C — Callback Queries (via `bot_service.handle_callback`)
Dual-path: VOTE forwarding (canonical) + Admin panel (legacy RBAC, fail-open)

```
Telegram callback → process_update()
  → handle_callback(chat_id, user_id, data)
      → in_admin_context(chat_id)
          ⚠ FAIL-OPEN: returns True when ADMIN_CONTROL_CHAT_ID == 0 (GAP-013)
      → get_role(user_id)
          ⚠ SEPARATE RBAC (GAP-013)
      
      if data.startswith("VOTE_|"):
          → outcome_service.handle_vote_callback(...)  ✓ CANONICAL
      
      if data.startswith("OUTCOME:"):
          → _record_outcome(...)  ⚠ INDEPENDENT mutation bypassing outcome_service
              → _load_outcomes_store() → outcomes.json (separate path)
              → _save_outcomes_store() → atomic write but no lock
              → observability_logger.log_event(OUTCOME_SET) ⚠ DUPLICATE audit
      
      if data.startswith("VOTE_"):
          → outcome_service.handle_vote_callback_data(...)  ✓ CANONICAL
      
      if data == "ADMIN_STATUS":
          → _ui_status()  ⚠ uses bot_service._load_settings(), _load_focus_state()
      
      if data == "ADMIN_SET_BUFFER":
          → requires role in (ROLE_OWNER, ROLE_ADMIN)  ⚠ legacy RBAC check
          → _ui_set_buffer()
      
      if data.startswith("BUFFER_"):
          → requires role in (ROLE_OWNER, ROLE_ADMIN)  ⚠ legacy RBAC check
          → _do_set_buffer(user_id, mode)  ⚠ INDEPENDENT Admin mutation
              → _load_settings() / _save_settings()  → settings.json
              → observability_logger.log_event(admin_change)
              → _proof(...)
      
      if data == "ADMIN_SET_SYMBOLS":
          → requires role in (ROLE_OWNER, ROLE_ADMIN)  ⚠ legacy RBAC check
          → _ui_symbols_menu()
      
      if data.startswith("SYM_TOGGLE:"):
          → requires role in (ROLE_OWNER, ROLE_ADMIN)  ⚠ legacy RBAC check
          → _do_toggle_symbol(user_id, symbol)  ⚠ INDEPENDENT Admin mutation
              → _load_active_symbols() / _save_active_symbols() → symbols.json
              → observability_logger.log_event(admin_change)
              → _proof(...)
      
      [ADMIN_RESEARCH, ADMIN_DOCS, DOC:, ADMIN_BACK → UI only, no canonical mutations]
```

---

## Pre-BATCH-05 Security Defects

| Defect | Location | GAP |
|--------|---------|-----|
| Fail-open `in_admin_context()` when `ADMIN_CONTROL_CHAT_ID==0` | `bot_service.py:79-83` | GAP-013 |
| Independent RBAC (`get_role`, `require_role`) separate from canonical `admin_permissions` | `bot_service.py:51-76` | GAP-013 |
| Admin mutations without lock (read-then-write race) | `admin_commands.py` `_set_threshold`, `_set_sr`, `_set_spike`, `_symbols_add`, `_symbols_remove` | GAP-011 |
| `admin_permissions.json` on disk but completely ignored by code | `admin_permissions.py` | GAP-012 |
| `_record_outcome()` independent of `outcome_service` | `bot_service.py:148-220` | GAP-013 |
| Duplicate Admin control planes (admin_commands vs bot_service panel) | Both modules | GAP-013 |
