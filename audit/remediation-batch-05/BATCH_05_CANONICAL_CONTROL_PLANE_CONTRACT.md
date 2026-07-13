# BATCH_05_CANONICAL_CONTROL_PLANE_CONTRACT

**Owner Decision Applied:** OWNER-002 = A
**Original Findings:** GAP-011, GAP-012, GAP-013

---

## Authoritative Control Plane (Post-BATCH-05)

### Entry Point

```
handle_admin_command(text: str, user_id: int) -> str
Location: send/core/admin_commands.py
```

### Execution Flow (After BATCH-05)

```
Admin input (slash command text, user_id)
  │
  ▼
_parse_command(text) → [cmd, arg1, arg2, ...]
  │
  ▼
has_permission(user_id, "admin.view")          [GATE: admin surface access]
  │ fail → render_unauthorized()
  │ pass
  ▼
cmd dispatch switch (parts[0].lower())
  │
  ├─ /admin      → render_admin_home(debug_identity(user_id))
  │
  ├─ /strategy   → require_permission(strategy.view)
  │                render_strategy_status(_load_algo_params())
  │
  ├─ /thresholds → [read] require_permission(strategy.view) for display
  │                [write] require_permission(strategy.thresholds.write)
  │                        validate field ∈ {PRE, CONFIRM, OPEN}
  │                        validate 0 ≤ value ≤ 100
  │                        with_lock("algo_params"):  ← GAP-011 FIX
  │                          _load_raw_algo_params()
  │                          mutate score_thresholds[field]
  │                          _save_algo_params_validated()  → validate_algo_params() → save_json_atomic()
  │                        _audit(user_id, "/thresholds", "OK", {...})
  │                        render_ok(message)
  │
  ├─ /sr         → similar pattern with with_lock("algo_params")  ← GAP-011 FIX
  │
  ├─ /spike      → similar pattern with with_lock("algo_params")  ← GAP-011 FIX
  │
  ├─ /symbols    → [list] require_permission(strategy.view)
  │                [add/remove] require_permission(strategy.symbols.write)
  │                             with_lock("active_symbols"):  ← GAP-011 FIX
  │                               _load/_save_active_symbols()
  │                             _audit(...)
  │                             render_ok(message)
  │
  ├─ /engine     → require_permission(engine.view) → render_engine_status()
  ├─ /debug      → require_permission(debug.view)  → render_debug_last()
  ├─ /report     → require_permission(reports.view) → render_report_summary()
  ├─ /roles      → require_permission(roles.view)   → render_roles()
  ├─ /roles_reload → require_permission(roles.write) → reload_roles_config() → _audit()
  ├─ /affiliate  → require_permission(affiliate.view) → render_affiliate_scope()
  └─ unknown     → render_error("Unknown admin command.")
```

---

## Authorization Contract

```
has_permission(user_id, permission) → bool
require_permission(user_id, permission) → (bool, reason_str)
Location: send/core/admin_permissions.py
```

### Permission Evaluation Order

1. `load_roles_config()` — load `admin_roles.json` (ROLES_CONFIG_PATH env or default)
2. `get_user_roles(user_id)` — map user_id to role constants
3. `is_owner(user_id)` — OWNER bypasses all checks
4. `list_permissions_for_user(user_id)`:
   - Merge `PERMISSION_MATRIX[role]` for each role (hardcoded, canonical baseline)
   - Merge `load_permissions_config()[role]` for each role (from admin_permissions.json) ← GAP-012 FIX
5. Check if `permission` in merged set

### Fail-Closed Rules

- Missing `admin_roles.json` → all users assigned `ROLE_USER` → no admin access
- Missing `admin_permissions.json` → only hardcoded `PERMISSION_MATRIX` applies (no regression)
- Malformed `admin_permissions.json` → `load_permissions_config()` returns `{}` (safe fallback)
- Unknown role → `ROLE_USER` (no permissions)
- Unknown permission → always `False` for non-OWNER

---

## Permission Contract (Canonical)

| Permission | Roles |
|-----------|-------|
| `admin.view` | OWNER, PRIMARY_ADMIN, STRATEGY_ADMIN, RESEARCH_ADMIN, ANALYST, MODERATOR, AFFILIATE_ADMIN |
| `strategy.view` | OWNER, PRIMARY_ADMIN, STRATEGY_ADMIN, RESEARCH_ADMIN, ANALYST |
| `strategy.thresholds.write` | OWNER, PRIMARY_ADMIN, STRATEGY_ADMIN |
| `strategy.sr.write` | OWNER, PRIMARY_ADMIN, STRATEGY_ADMIN |
| `strategy.spike.write` | OWNER, PRIMARY_ADMIN, STRATEGY_ADMIN |
| `strategy.symbols.write` | OWNER, PRIMARY_ADMIN, STRATEGY_ADMIN |
| `engine.view` | OWNER, PRIMARY_ADMIN, STRATEGY_ADMIN, RESEARCH_ADMIN, ANALYST |
| `engine.restart` | OWNER, PRIMARY_ADMIN |
| `debug.view` | OWNER, PRIMARY_ADMIN, STRATEGY_ADMIN, RESEARCH_ADMIN, ANALYST |
| `reports.view` | OWNER, PRIMARY_ADMIN, STRATEGY_ADMIN, RESEARCH_ADMIN, ANALYST |
| `channels.view` | OWNER, PRIMARY_ADMIN, MODERATOR |
| `channels.test` | OWNER, PRIMARY_ADMIN |
| `roles.view` | OWNER, PRIMARY_ADMIN |
| `roles.write` | OWNER |
| `affiliate.view.own` | OWNER, PRIMARY_ADMIN, AFFILIATE_ADMIN |
| `affiliate.view.any` | OWNER, PRIMARY_ADMIN |

---

## Mutation Safety Contract

1. **Read-modify-write** for `algo_params.json`: protected by `storage.with_lock("algo_params")`
2. **Read-modify-write** for `active_symbols.json`: protected by `storage.with_lock("active_symbols")`
3. **Validation before write**: `params_loader.validate_algo_params()` called before `save_json_atomic()`
4. **Atomic write**: `storage.save_json_atomic()` uses temp file + fsync + atomic replace
5. **No partial state**: lock ensures only one writer at a time; validation ensures file is always valid
6. **No false-success**: `_audit()` called only after successful mutation; errors bubble up as `render_error()`

---

## Observability Contract

Every material Admin mutation emits:
- `_append_jsonl(ADMIN_EVENTS_PATH, {...})` with `event_type="admin_change"`, `user_id`, `command`, `result`, `details`
- `_append_jsonl(ADMIN_PROOFS_PATH, {...})` (same payload)

Audit events MUST contain: `event_type`, `user_id`, `primary_role`, `command`, `result`
Audit events MUST NOT contain: passwords, tokens, secrets, credentials

---

## bot_service Residual Responsibility (Post-BATCH-05)

`bot_service.py` is NOT an Admin mutation authority. Its sole responsibilities are:

1. **Slash command dispatch**: `handle_admin_command_v2(text, user_id)` (delegates to admin_commands)
2. **VOTE forwarding**: `outcome_service.handle_vote_callback(...)` (BATCH-04 canonical)
3. **OUTCOME: delegation**: forward to `outcome_service` (not independent mutation)
4. **Retired callback rejection**: clear message for ADMIN_* / BUFFER_* / SYM_TOGGLE: / DOC: callbacks
5. **Admin context enforcement**: `in_admin_context()` is fail-CLOSED (ADMIN_CONTROL_CHAT_ID=0 denies)

`bot_service.OUTCOMES_PATH` is retained as a module attribute for BATCH-04 compatibility but is NOT written by bot_service after BATCH-04/BATCH-05.

---

## Cross-Batch Preservation

| Contract | Preserved |
|---------|-----------|
| BATCH-02 parameter validation contract | YES — `params_loader.validate_algo_params()` still called before every write |
| BATCH-03 distribution/observability contracts | YES — admin_commands uses `_append_jsonl` consistent with BATCH-03 |
| BATCH-04 outcome_service authority | YES — VOTE_ callbacks delegated to outcome_service; bot_service does not independently mutate outcomes |
| BATCH-04 telemetry (OPEN_NOW) | YES — trade_temporal_telemetry not modified |
