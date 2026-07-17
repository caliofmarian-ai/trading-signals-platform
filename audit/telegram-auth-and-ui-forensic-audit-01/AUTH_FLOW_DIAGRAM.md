# AUTH_FLOW_DIAGRAM

## Audit metadata

- **Audited HEAD:** `0e736ae251dcb81dee7d13a34bbcfafcafe36967`
- **No code modifications were made during this audit.**
- **Evidence files:** `send/core/bot_service.py`, `send/core/admin_permissions.py`, `send/core/telegram_targets.py`, `send/core/telegram_runtime.py`

---

## Diagram 1 — Current slash-command authorization flow (HEAD `0e736ae`)

```
┌─────────────────────────────────────────────────────────────────────────┐
│  Telegram message update (text starting with "/")                       │
└───────────────────────────────────┬─────────────────────────────────────┘
                                    │
                                    ▼
                    send/runtime/telegram_updates.py
                         process_update(update)
                                    │
                                    ▼
                    send/core/bot_service.py
                         process_update(update)
                         extract: msg, user_id, text, cmd
                                    │
               ┌────────────────────┼────────────────────────┐
               │                    │                        │
               ▼                    ▼                        ▼
          /start              /help                    /status
          /help               render_help_text()       render_status_text()
          render_start_text() No auth gate             No auth gate
          No auth gate
               └────────────────────┼────────────────────────┘
                                    │
                                    ▼
                    cmd in admin_command_names()? ──No──► _send_reply(UNKNOWN_COMMAND_TEXT)
                                    │ Yes
                                    ▼
            ┌───────────────────────────────────────────────┐
            │  _can_run_admin_command(msg, user_id, cmd)    │
            │                                               │
            │  Branch A: _is_owner_private_context         │
            │    ├─ chat.type == "private"?                 │
            │    ├─ chat.id == user_id?                     │
            │    └─ is_owner(user_id)?                      │
            │         │                                     │
            │         ├─ True: cmd in _OWNER_PRIVATE_COMMANDS?
            │         │    ├─ Yes → ALLOW (return True)    │
            │         │    └─ No  → DENY (return False)    │
            │         └─ False: fall to Branch B           │
            │                                               │
            │  Branch B: _is_admin_topic_context           │
            │    ├─ in_admin_context(chat.id)               │
            │    │    ├─ ADMIN_CONTROL_CHAT_ID == 0? → DENY │
            │    │    └─ chat.id == ADMIN_CONTROL_CHAT_ID?  │
            │    │         ├─ No  → DENY (return False)    │
            │    │         └─ Yes → check thread           │
            │    └─ ADMIN_CONTROL_THREAD_ID set?            │
            │         ├─ No  → ALLOW (return True)          │
            │         └─ Yes → msg.thread_id == ADMIN_CONTROL_THREAD_ID?
            │               ├─ Yes → ALLOW (return True)   │
            │               └─ No  → DENY (return False)   │
            └───────────────────────────────────────────────┘
                                    │
                    ┌───────────────┴──────────────┐
                    │ DENY                         │ ALLOW
                    ▼                              ▼
        _send_reply("Access denied     _render_panel_for_command(text, user_id)
                     (wrong chat).")              │
                                                  ▼
                              handle_admin_command(text, user_id)
                              [send/core/admin_commands.py]
                                                  │
                                                  ▼
                              has_permission(user_id, "admin.view")? ──No──► render_unauthorized()
                                                  │ Yes
                                                  ▼
                              per-command permission check
                              (require_permission / has_permission)
                                                  │
                                    ┌─────────────┴────────────┐
                                    │ FAIL                     │ PASS
                                    ▼                          ▼
                              render_error(reason)     execute command + render
```

---

## Diagram 2 — is_owner() resolution chain

```
is_owner(user_id)
    │
    ▼
get_user_roles(user_id)
    │
    ▼
load_roles_config()   [lru_cache(maxsize=1)]
    │
    ├─ Read ADMIN_ROLES_CONFIG file (default: /opt/binarybot/config/admin_roles.json)
    │      If absent or invalid → empty dict {}
    │
    └─ Read OWNER_TELEGRAM_ID env var
           If valid integer → append to data["owner"] if not already present
    │
    ▼
_ids_from_key(data, "owner")
    │
    ▼
user_id in owner_ids?
    ├─ Yes → ROLE_OWNER in roles → is_owner returns True
    └─ No  → ROLE_OWNER not in roles → is_owner returns False
              (falls back to _is_admin_topic_context in auth gate)
```

**Cache invalidation:** `reload_roles_config()` calls `load_roles_config.cache_clear()`.
This is only accessible via `/roles_reload` command, which is itself auth-gated.

---

## Diagram 3 — Callback authorization flow

```
Telegram callback_query update
    │
    ▼
send/core/bot_service.py process_update
    extract: msg_obj, chat_id, user_id, data
    │
    ├─ data starts with "VOTE_|" or "VOTE_" or "OUTCOME:"
    │       → outcome_service path, NO admin context check
    │
    └─ telegram_admin_ui.parse_action(data) → admin_action?
            │
            ├─ admin_action is not None
            │     → _can_use_admin_callback(msg_obj, user_id)?
            │           ├─ _is_owner_private_context(msg_obj, user_id) → True  → ALLOW
            │           └─ _is_admin_topic_context(msg_obj) → True → ALLOW, else DENY
            │     (if denied) → _send_reply("Access denied (wrong chat).")
            │     (if allowed) → _handle_admin_navigation_action(admin_action, user_id, msg_obj)
            │
            └─ admin_action is None
                  → handle_callback(chat_id, user_id, data, ...)
                        → _is_admin_topic_context(context_message)?
                              ├─ No  → "Access denied (wrong chat)."
                              └─ Yes → retired callback check
                                            ├─ retired → _RETIRED_MSG
                                            └─ unknown → "Unknown action."
```

---

## Diagram 4 — RELOAD_ROLES_CONFIRM special case

```
Callback data: "ADMIN_NAV:RELOAD_ROLES_CONFIRM"
    │
    ▼
parse_action → "RELOAD_ROLES_CONFIRM"
    │
    ▼
_can_use_admin_callback(msg_obj, user_id)?
    ├─ ALLOW (owner private OR admin topic)
    │
    ▼
_handle_admin_navigation_action("RELOAD_ROLES_CONFIRM", user_id, msg_obj)
    │
    ├─ owner_private is True?
    │     → return "Access denied (wrong chat)."  [explicit block, regardless of role]
    │
    └─ owner_private is False (admin topic context)
          → return confirmation screen with [✅ Confirm Reload] [❌ Cancel]
```

Rationale documented in BATCH-05: reload-roles from private DM is blocked as a safety measure.

---

## Diagram 5 — Historical flow at commit d7e7213 (pre-gate)

```
Telegram message ("/report")
    │
    ▼
send/core/bot_service.py (d7e7213 version)
    cmd in admin_command_names()? Yes
    │
    ▼
handle_admin_command_v2(text, user_id)   ← NO chat gate at this point
    │
    ▼
admin_commands.py: require_permission(user_id, "reports.view")
    ├─ FAIL → render_unauthorized()
    └─ PASS → render_report_summary(...)
```

At `d7e7213`, the owner could send `/report` from any chat — including their private DM — and it worked, because there was no context gate before `handle_admin_command_v2`.

---

## Diagram 6 — Gate introduced at commit 49aaeb4

```
Telegram message ("/report", from private DM)
    │
    ▼
send/core/bot_service.py (49aaeb4)
    cmd in admin_command_names()? Yes
    │
    ▼
in_admin_context(chat_id)?                ← NEW gate added here
    chat_id = private DM id ≠ ADMIN_CONTROL_CHAT_ID
    → False
    │
    ▼
_send_reply("Access denied (wrong chat).")  ← breakage introduced
```

No owner-private exception existed at `49aaeb4`.
The `_is_owner_private_context` path was added in a subsequent remediation commit (not separately tagged in the 2-commit shallow history but present in current HEAD).
