# TELEGRAM_UI_FLOW_MAP

## Audit metadata

- **Audited HEAD:** `0e736ae251dcb81dee7d13a34bbcfafcafe36967`
- **No code modifications were made during this audit.**
- **Evidence:** `send/legacy/bot_control.py` (git history), `send/_archive/backups/bot_service.py.bak_step16`, `send/core/bot_service.py` (HEAD), `send/core/telegram_admin_ui.py` (HEAD)

---

## ERA A — Legacy Runner flows

### Flow A1: Symbol selector interaction

```
User: /start  (or /forex, /crypto)
  │
  ▼
Bot sends two messages simultaneously:
  Message 1: FOREX panel (Screen A1)
  Message 2: CRYPTO panel (Screen A2)
  │
  ▼ User taps individual symbol button
  callback: tg:forex:EURUSD  (or tg:crypto:...)
  │
  ├─ Toggle: EURUSD active? → remove : add in active_symbols.json["forex"]
  ├─ Reload active list
  └─ Edit message: rebuild keyboard with updated ✅/⬜ state

User taps [✅ All]
  callback: tg:forex:__ALL__
  │
  ├─ Set active_symbols.json["forex"] = full_symbols_list
  └─ Edit message: all checkmarks now ✅

User taps [⬜ None]
  callback: tg:forex:__NONE__
  │
  ├─ Set active_symbols.json["forex"] = []
  └─ Edit message: all checkmarks now ⬜

User taps [🔄 Refresh]
  callback: tg:forex:__REFRESH__
  │
  └─ No state change; re-render keyboard from current state; edit message
```

### Flow A2: Buffer selection

```
User: /buffer
  │
  ▼
Bot sends:
  "Alege Buffer (Mic / Mediu / Mare):"
  [✅ MIC  ] [☐ MEDIU] [☐ MARE ]
  (current mode shown with ✅)
  │
  ▼ User taps [☐ MARE]
  callback: buffer_set:large
  │
  ├─ Save "large" to settings.json["buffer_mode"]
  └─ Edit message:
      "✅ Buffer setat: LARGE"
      [☐ MIC  ] [☐ MEDIU] [✅ MARE ]
```

### Flow A3: Open trade confirmation

```
User: /open BTC/USD
  │
  ▼
Bot writes focus_state.json["pending_open"]["BTC/USD"] = True
Bot replies (no keyboard):
  "✅ Confirmed OPEN for BTC/USD. Scanner revine la scanare generală când focus se eliberează."
```

---

## ERA B — Legacy Admin Panel flows

### Flow B1: Admin panel entry and navigation

```
User: /admin  (in admin chat, role recognized)
  │
  ▼
in_admin_context(chat_id)? Yes
get_role(user_id) → OWNER / ADMIN / ANALYST / MODERATOR
  │
  ▼
Bot sends Screen B1:
  "🔐 Admin Panel\nRole: OWNER"
  [🧱 Set Buffer] [🧩 Set Symbols]   ← OWNER/ADMIN only
  [📡 Status]                         ← all roles
  [📊 Research]                        ← OWNER/ADMIN/ANALYST
  [📚 View Docs]                       ← all roles
```

### Flow B2: Buffer sub-flow (from admin panel)

```
User taps [🧱 Set Buffer]
  callback: ADMIN_SET_BUFFER
  │
  ▼
Bot edits message to Screen B2:
  "Select Buffer Mode\nCurrent: MEDIUM"
  [SMALL] [MEDIUM] [LARGE]
  [⬅️ Back]
  │
User taps [SMALL]
  callback: BUFFER_SMALL
  │
  ├─ Save "small" to settings.json["buffer_mode"]
  └─ Bot edits message: "Buffer set to SMALL"
     returns to Screen B1 (admin home)

User taps [⬅️ Back]
  callback: ADMIN_BACK
  └─ Bot edits message: Screen B1 (admin home)
```

### Flow B3: Symbols sub-flow (from admin panel)

```
User taps [🧩 Set Symbols]
  callback: ADMIN_SET_SYMBOLS
  │
  ▼
Bot edits message to Screen B3:
  "Active Symbols (7)\nTap to toggle (will remove/add)."
  [✅ EURUSD]
  [✅ GBPUSD]
  ... up to 12
  [⬅️ Back]
  │
User taps [✅ EURUSD]
  callback: SYM_TOGGLE:EURUSD
  │
  ├─ Remove EURUSD from symbols.json
  └─ Bot edits message: updated active symbols list
     (screen reloads with EURUSD removed)

User taps [⬅️ Back]
  callback: ADMIN_BACK
  └─ Bot edits message: Screen B1 (admin home)
```

### Flow B4: Status view

```
User taps [📡 Status]
  callback: ADMIN_STATUS
  │
  ▼
Bot edits message to Screen B4:
  "📡 System Status\nMode: WIDE_SCAN\nBuffer: MEDIUM\n..."
  Reply markup: admin home panel buttons
  (status text with admin home keyboard underneath)
```

### Flow B5: Research panel

```
User taps [📊 Research]
  callback: ADMIN_RESEARCH
  │
  ▼
Bot edits message:
  "📊 Research panel: (coming next) — analytics_engine.py"
  Reply markup: admin home panel buttons (persistent)
```

### Flow B6: Docs viewer flow

```
User taps [📚 View Docs]
  callback: ADMIN_DOCS
  │
  ▼
Bot edits message to Screen B6:
  "📚 Docs Viewer\nSelect a document:"
  [README.md]
  [CANONICAL_SPEC.md]
  ...  (up to 20 .md files)
  [⬅️ Back]
  │
User taps [README.md]
  callback: DOC:README.md
  │
  └─ Bot calls sendDocument API: sends README.md as attachment
     No message edit (document is new message)

User taps [⬅️ Back]
  callback: ADMIN_BACK
  └─ Bot edits message: Screen B1 (admin home)
```

---

## ERA C — Current canonical admin flows (HEAD `0e736ae`)

### Flow C1: Admin home via slash

```
User: /admin  (in admin topic OR owner private DM with OWNER_TELEGRAM_ID set)
  │
  ▼
_can_run_admin_command passes
  │
  ▼
handle_admin_command("/admin", user_id)
  has_permission(user_id, "admin.view")? Yes
  return render_admin_home(identity)
  │
  ▼
Bot sends:
  "🛠️ Admin Panel\n{identity text}"
  [📡 Status  ] [📈 Strategy ]
  [🧩 Symbols ] [⚙️ Engine   ]
  [🧪 Debug   ] [📊 Report   ]
  [👥 Roles   ] [💼 Affiliate]
  [♻️ Reload Roles]   ← only shown in admin topic, NOT in owner private DM
```

### Flow C2: Navigation to sub-panels

```
User taps [📈 Strategy]
  callback: ADMIN_NAV:STRATEGY
  │
  ▼
_can_use_admin_callback passes
  │
  ▼
_handle_admin_navigation_action("STRATEGY", ...)
  command_for_action → "/strategy"
  _render_panel_for_command("/strategy", user_id)
  handle_admin_command("/strategy", user_id)
  │
  ▼
Bot edits message:
  "📈 Strategy Panel\n{strategy text}"
  [🎯 Thresholds] [📐 SR     ]
  [⚡ Spike     ] [🧩 Symbols]
  [⬅️ Admin    ]
```

### Flow C3: Symbols panel (current — view only)

```
User taps [🧩 Symbols] from admin home or strategy
  callback: ADMIN_NAV:SYMBOLS
  │
  ▼
handle_admin_command("/symbols list", user_id)
  has_permission(user_id, "strategy.view")? Yes
  return render_symbols(active_symbols)
  │
  ▼
Bot edits message:
  "🧩 Symbols Panel\n{text list of active symbols}"
  [🔄 Refresh Symbols] [📈 Strategy]
  [⬅️ Admin          ]
```

No toggle buttons; symbols view is text-only.
Add/remove requires slash: `/symbols add EURUSD` or `/symbols remove EURUSD`.

### Flow C4: Reload Roles confirmation (admin topic only)

```
User taps [♻️ Reload Roles]  (admin topic only; button absent in private DM)
  callback: ADMIN_NAV:RELOAD_ROLES_CONFIRM
  │
  ▼
_handle_admin_navigation_action("RELOAD_ROLES_CONFIRM", ...)
  owner_private = False (it's admin topic)
  │
  ▼
Bot edits message:
  "♻️ Confirmation\nConfirm reloading role + permission configuration?"
  [✅ Confirm Reload] [❌ Cancel]
  │
User taps [✅ Confirm Reload]
  callback: ADMIN_NAV:RELOAD_ROLES_EXEC
  │
  ▼
handle_admin_command("/roles_reload", user_id)
  require_permission(user_id, "roles.write")? Yes (OWNER only)
  reload_roles_config()
  return render_ok("Roles configuration reloaded.")
  │
  ▼
Bot edits message: "♻️ Roles Panel\nRoles configuration reloaded."
  [⬅️ Admin]
```

### Flow C5: VOTE interaction (signal channels, no admin gate)

```
Signal message in subscriber channel:
  "📊 SIGNAL: EURUSD LONG\n..."
  [✅ WIN] [❌ LOSS] [— NEUTRAL]

User taps [✅ WIN]
  callback: VOTE_|<signal_id>|WIN
  │
  ▼
outcome_service.handle_vote_callback(...)
  accepted? → "OUTCOME: WIN"   (message appended)
  already?  → "Outcome already recorded."
  rejected? → "Outcome rejected: {reason}"
  │
  ▼
Bot edits signal message: appends outcome line; removes inline keyboard
```
