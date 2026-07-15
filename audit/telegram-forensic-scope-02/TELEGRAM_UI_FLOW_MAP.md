# TELEGRAM_UI_FLOW_MAP

## Audit metadata
- HEAD at audit time: `9912c14`
- Evidence: `send/legacy/bot_control.py` (`0fb9112`), `send/_archive/backups/bot_service.py.bak_step16`, `send/core/bot_service.py` (current HEAD), `send/core/telegram_admin_ui.py` (current HEAD).

---

## Era A — Legacy Runner (`bot_control.py`) UI flows

### Flow A1: Symbol selector interaction

```
User: /start  (or /forex, /crypto)
  ↓
bot sends FOREX panel  +  CRYPTO panel  (both inline keyboards)
  ↓
User taps [✅/⬜ EURUSD]
  → callback: tg:forex:EURUSD
  ↓
Toggle in active_symbols.json
Reload active list
Edit message: update text + rebuild keyboard (same structure, updated checkmarks)

User taps [✅ All]
  → callback: tg:forex:__ALL__
  ↓
Set all symbols active
Edit message

User taps [⬜ None]
  → callback: tg:forex:__NONE__
  ↓
Clear all active symbols
Edit message

User taps [🔄 Refresh]
  → callback: tg:forex:__REFRESH__
  ↓
No state change; re-render keyboard from current state
Edit message
```

### Flow A2: Buffer selection

```
User: /buffer
  ↓
Bot sends:
  "Alege Buffer (Mic / Mediu / Mare):"
  [✅ MIC  ] [☐ MEDIU] [☐ MARE ]
  ↓
User taps [☐ MARE]
  → callback: buffer_set:large
  ↓
Save "large" to settings.json["buffer_mode"]
Edit message:
  "✅ Buffer setat: LARGE"
  [☐ MIC  ] [☐ MEDIU] [✅ MARE ]
```

### Flow A3: Open confirmation

```
User: /open BTC/USD
  ↓
Write pending_open["BTC/USD"] = True in focus_state.json
Bot replies: "✅ Confirmed OPEN for BTC/USD. Scanner revine..."
```

---

## Era B — Legacy Admin Panel (`bot_service.py.bak_step16`) UI flows

### Flow B1: Admin panel entry

```
User: /admin  (in admin chat, role recognised)
  ↓
Bot sends:
  "🔐 Admin Panel\nRole: {OWNER|ADMIN|ANALYST|MODERATOR}"
  [🧱 Set Buffer]    (OWNER/ADMIN only)
  [🧩 Set Symbols]   (OWNER/ADMIN only)
  [📡 Status]        (all roles)
  [📊 Research]      (OWNER/ADMIN/ANALYST)
  [📚 View Docs]     (all roles)
```

### Flow B2: Buffer change from admin panel

```
User taps [🧱 Set Buffer]
  → callback: ADMIN_SET_BUFFER  (OWNER/ADMIN only)
  ↓
Edit message:
  "Select Buffer Mode\nCurrent: MEDIUM"
  [SMALL] [MEDIUM] [LARGE]
  [⬅️ Back]
  ↓
User taps [LARGE]
  → callback: BUFFER_LARGE
  ↓
Save "LARGE" to settings.json
Edit message: "✅ Buffer set to LARGE"  + admin home panel buttons
```

### Flow B3: Symbol management

```
User taps [🧩 Set Symbols]
  → callback: ADMIN_SET_SYMBOLS  (OWNER/ADMIN only)
  ↓
Edit message:
  "Active Symbols (7)\nTap to toggle (will remove/add)."
  [✅ EURUSD]
  [✅ GBPUSD]
  ...
  [⬅️ Back]
  ↓
User taps [✅ EURUSD]
  → callback: SYM_TOGGLE:EURUSD
  ↓
Remove/add symbol in symbols.json
Edit message: refreshed symbol list
```

### Flow B4: Status view

```
User taps [📡 Status]
  → callback: ADMIN_STATUS  (all roles)
  ↓
Edit message:
  "📡 System Status
   Mode: WIDE_SCAN
   Buffer: MEDIUM
   Active symbols: 7
   Focus/watchlist: —
   Tiers:
   - FREE: OPEN (2 today)
   ..."
  + admin home panel buttons (persistent)
```

### Flow B5: Docs viewer

```
User taps [📚 View Docs]
  → callback: ADMIN_DOCS
  ↓
Edit message:
  "📚 Docs Viewer\nSelect a document:"
  [README.md]
  [CANONICAL_SPEC.md]
  ...
  [⬅️ Back]
  ↓
User taps [README.md]
  → callback: DOC:README.md
  ↓
Bot sends_document: file from /opt/binarybot/docs/README.md
(File attachment, not inline text)
```

### Flow B6: Back navigation

```
User taps [⬅️ Back]  (from any sub-panel)
  → callback: ADMIN_BACK
  ↓
Edit message:
  "🔐 Admin Panel" + role-filtered buttons
```

---

## Era C — Current canonical admin UI flows (HEAD `9912c14`)

### Flow C1: Slash admin entry (owner private context)

```
User: /admin  (in private DM with bot, user_id matches OWNER_TELEGRAM_ID)
  ↓
_is_owner_private_context → True
cmd "/admin" in _OWNER_PRIVATE_COMMANDS → True
_can_run_admin_command → True
  ↓
handle_admin_command_v2("/admin", user_id)  → permission: admin.view
  ↓
Bot sends:
  "🛠️ Admin Panel\n{response text}"
  [📡 Status] [📈 Strategy]
  [🧩 Symbols] [⚙️ Engine]
  [🧪 Debug] [📊 Report]
  [👥 Roles] [💼 Affiliate]
  (no [♻️ Reload Roles] — private context excludes it)
```

### Flow C2: Slash admin entry (admin topic context)

```
User: /admin  (in configured admin supergroup, correct topic thread)
  ↓
_is_admin_topic_context → True
_can_run_admin_command → True
  ↓
handle_admin_command_v2("/admin", user_id)
  ↓
Bot sends:
  "🛠️ Admin Panel\n{response text}"
  [📡 Status] [📈 Strategy]
  [🧩 Symbols] [⚙️ Engine]
  [🧪 Debug] [📊 Report]
  [👥 Roles] [💼 Affiliate]
  [♻️ Reload Roles]  ← present in admin topic context
```

### Flow C3: Panel navigation (callback, admin_nav prefix)

```
User taps [📈 Strategy]
  → callback: ADMIN_NAV:STRATEGY
  ↓
parse_action → "STRATEGY"
_can_use_admin_callback → True (owner private or admin topic)
_handle_admin_navigation_action("STRATEGY", user_id, msg)
  ↓
handle_admin_command_v2("/strategy", user_id)
Edit message:
  "📈 Strategy Panel\n{strategy config text}"
  [🎯 Thresholds] [📐 SR]
  [⚡ Spike] [🧩 Symbols]
  [⬅️ Admin]
```

### Flow C4: Roles reload (admin topic only)

```
User taps [♻️ Reload Roles]  (in admin topic context)
  → callback: ADMIN_NAV:RELOAD_ROLES_CONFIRM
  ↓
Not owner_private → show confirmation screen
Edit message:
  "♻️ Confirmation\nConfirm reloading role + permission configuration?"
  [✅ Confirm Reload] [❌ Cancel]
  ↓
User taps [✅ Confirm Reload]
  → callback: ADMIN_NAV:RELOAD_ROLES_EXEC
  ↓
handle_admin_command_v2("/roles_reload", user_id)
Edit message: "♻️ Roles Panel\n{result}"  + [⬅️ Admin]
```

### Flow C5: Roles reload in private (blocked)

```
User taps [♻️ Reload Roles] (in owner private DM — button absent for private context)
  ↓
admin_home_markup(include_roles_reload=False) → button not rendered
  → No interaction possible
```

### Flow C6: Wrong-context denial

```
User: /admin  (not owner private, not admin topic)
  ↓
_can_run_admin_command → False
  ↓
Bot sends: "Access denied (wrong chat)."
```

---

## Context-decision summary table

| Context | Owner private DM | Admin topic | Other |
|---|---|---|---|
| Slash commands allowed | _OWNER_PRIVATE_COMMANDS subset | All admin commands | None |
| /roles_reload slash | ❌ denied | ✅ allowed | ❌ denied |
| ADMIN_NAV callbacks | ✅ allowed | ✅ allowed | ❌ denied |
| RELOAD_ROLES_CONFIRM action | ❌ returns denial text | ✅ confirmation screen | ❌ denied |
| Reload Roles button shown | ❌ hidden | ✅ shown | n/a |
| VOTE_ callbacks | ✅ (no context gate) | ✅ | ✅ |
