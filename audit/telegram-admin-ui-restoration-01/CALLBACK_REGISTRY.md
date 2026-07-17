# CALLBACK REGISTRY

## Namespace

All admin UI callbacks use the `ADMIN_NAV:` prefix.

Maximum callback_data length: 64 bytes (Telegram limit).
All callbacks in this registry have been verified to stay within this limit.

---

## Navigation callbacks

| Callback | Action | Notes |
|---|---|---|
| `ADMIN_NAV:HOME` | Show admin home panel | All admin users |
| `ADMIN_NAV:STATUS` | Run /status | All admin users |
| `ADMIN_NAV:STRATEGY` | Run /strategy | strategy.view |
| `ADMIN_NAV:THRESHOLDS` | Run /thresholds | strategy.view |
| `ADMIN_NAV:SR` | Run /sr | strategy.view |
| `ADMIN_NAV:SPIKE` | Run /spike | strategy.view |
| `ADMIN_NAV:SYMBOLS` | Show symbol toggle panel | strategy.modify |
| `ADMIN_NAV:ENGINE` | Run /engine | diagnostics.view |
| `ADMIN_NAV:DEBUG` | Run /debug | diagnostics.view |
| `ADMIN_NAV:REPORT` | Run /report | All admin users |
| `ADMIN_NAV:FILES_HOME` | Show file browser home | files.view |
| `ADMIN_NAV:DOCS` | Show docs browser | files.view |
| `ADMIN_NAV:DIAGNOSE` | Run /diagnose | diagnostics.view |
| `ADMIN_NAV:AUDIT_RUNTIME` | Run /audit_runtime | diagnostics.view |
| `ADMIN_NAV:ROLES` | Run /roles | roles.view |
| `ADMIN_NAV:AFFILIATE` | Run /affiliate | All admin users |
| `ADMIN_NAV:RELOAD_ROLES` | Prompt roles reload confirmation | admin-topic only |

---

## Symbol management callbacks

| Callback | Action | Payload | Notes |
|---|---|---|---|
| `ADMIN_NAV:SYM_TOGGLE:{SYM}` | Toggle symbol on/off | SYM = uppercase symbol | strategy.modify |
| `ADMIN_NAV:SYMBOLS_ALL` | Enable all symbols | — | strategy.modify |
| `ADMIN_NAV:SYMBOLS_NONE` | Disable all symbols | — | strategy.modify |

Maximum SYM length: 8 characters. Longest known: `EURUSD` (6 chars).
Full callback: `ADMIN_NAV:SYM_TOGGLE:EURUSD` = 28 chars ✓

---

## Strategy profile callbacks

| Callback | Action | Payload | Notes |
|---|---|---|---|
| `ADMIN_NAV:PROFILE_HOME` | Show profile selector | — | strategy.modify |
| `ADMIN_NAV:PROFILE_CONFIRM:{P}` | Show confirmation for profile | P = profile name | strategy.modify |
| `ADMIN_NAV:PROFILE_EXEC:{P}` | Execute profile change | P = profile name | strategy.modify |

Profile name values: `CONSERVATIVE`, `BALANCED`, `AGGRESSIVE`.
Longest callback: `ADMIN_NAV:PROFILE_CONFIRM:CONSERVATIVE` = 39 chars ✓

---

## File browser callbacks

| Callback | Action | Payload | Notes |
|---|---|---|---|
| `ADMIN_NAV:FILES_DIR:{KEY}` | List files in directory | KEY = dir key | files.view |
| `ADMIN_NAV:FILES_PAGE:{KEY}:{PAGE}` | Paginate file list | KEY, PAGE = int | files.view |
| `ADMIN_NAV:FILE_DL:{KEY}:{FNAME}` | Download file | KEY, FNAME | files.view |

Dir key values: `obs`, `out`, `ana`, `rpt`, `doc`, `aud`, `snp`.
Max filename: validated at 50 chars to stay within 64-byte limit.
Longest realistic callback: `ADMIN_NAV:FILE_DL:obs:engine_events.jsonl` = 42 chars ✓

---

## Log and audit callbacks

| Callback | Action | Notes |
|---|---|---|
| `ADMIN_NAV:LOG` | Export bounded, sanitized log | diagnostics.view |
| `ADMIN_NAV:AUDIT` | Generate and send runtime audit | diagnostics.view |

---

## Report callbacks

| Callback | Action | Notes |
|---|---|---|
| `ADMIN_NAV:REPORT_DL` | Download latest report file if available | files.view |

---

## Confirmation callbacks (roles reload — preserved)

| Callback | Action | Notes |
|---|---|---|
| `ADMIN_NAV:RELOAD_ROLES_CONFIRM` | Prompt roles reload | admin-topic only |
| `ADMIN_NAV:RELOAD_ROLES_EXEC` | Execute roles reload | admin-topic only |

---

## Callback routing

All callbacks are parsed in `bot_service._handle_admin_navigation_action`:

```
action = parse_action(callback_data)  # strips "ADMIN_NAV:" prefix
if action.startswith("SYM_TOGGLE:"): ...
elif action.startswith("PROFILE_CONFIRM:"): ...
elif action.startswith("PROFILE_EXEC:"): ...
elif action.startswith("FILES_DIR:"): ...
elif action.startswith("FILES_PAGE:"): ...
elif action.startswith("FILE_DL:"): ...
elif action == "SYMBOLS_ALL": ...
elif action == "SYMBOLS_NONE": ...
elif action == "LOG": ...
elif action == "AUDIT_RUNTIME": ...
elif action == "DIAGNOSE": ...
...
```

Unknown callbacks return a safe error message; no state is mutated.

---

## Legacy callback compatibility

The following legacy callback prefixes from the old UI are NOT reactivated:
- `buffer_set:*` — replaced by `ADMIN_NAV:PROFILE_EXEC:*`
- `symbol_toggle:*` — replaced by `ADMIN_NAV:SYM_TOGGLE:*`
- `file_dl:*` — replaced by `ADMIN_NAV:FILE_DL:*`

These legacy callbacks will fall through to the "unknown callback" handler
and return a safe error message.
