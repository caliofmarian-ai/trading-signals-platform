# OLD_VS_CURRENT_TELEGRAM_UI_COMPARISON

## Audit metadata
- HEAD at audit time: `9912c14`
- No code modifications made during this audit.
- Evidence: `send/legacy/bot_control.py` (git `0fb9112`), `send/_archive/backups/bot_service.py.bak_step16`, current `send/core/telegram_admin_ui.py`, `send/core/bot_service.py`.

---

## Section 1 — Admin panel home screen

| Dimension | Legacy (`bak_step16`) | Current HEAD (`9912c14`) |
|---|---|---|
| Title text | `🔐 Admin Panel\nRole: {role}` | `🛠️ Admin Panel\n{command response text}` |
| Home reached via | `/admin` slash | `/admin` slash OR `ADMIN_NAV:HOME` callback |
| Status button | `📡 Status` → `ADMIN_STATUS` | `📡 Status` → `ADMIN_NAV:STATUS` |
| Strategy button | None | `📈 Strategy` → `ADMIN_NAV:STRATEGY` |
| Symbols button | `🧩 Set Symbols` → `ADMIN_SET_SYMBOLS` (mutations only) | `🧩 Symbols` → `ADMIN_NAV:SYMBOLS` (view only from nav) |
| Buffer button | `🧱 Set Buffer` → `ADMIN_SET_BUFFER` | **Not present** (no direct buffer shortcut) |
| Engine button | None | `⚙️ Engine` → `ADMIN_NAV:ENGINE` |
| Debug button | None | `🧪 Debug` → `ADMIN_NAV:DEBUG` |
| Report button | None | `📊 Report` → `ADMIN_NAV:REPORT` |
| Roles button | None | `👥 Roles` → `ADMIN_NAV:ROLES` |
| Affiliate button | None | `💼 Affiliate` → `ADMIN_NAV:AFFILIATE` |
| Research button | `📊 Research` → `ADMIN_RESEARCH` (placeholder text) | **Not present** (analytics exposed via `/report` and `/debug`) |
| Docs button | `📚 View Docs` → `ADMIN_DOCS` | **Not present** (no docs viewer) |
| Reload Roles button | None | `♻️ Reload Roles` → `ADMIN_NAV:RELOAD_ROLES_CONFIRM` (admin topic only) |
| Role-filtered buttons | Yes — different buttons per OWNER/ADMIN/ANALYST/MODERATOR | No per-button filtering; permission gate is inside `admin_commands.py` |
| Back button | Not applicable (home panel) | Not applicable |

---

## Section 2 — Buffer management

| Dimension | Legacy | Current |
|---|---|---|
| Access path | Admin panel → `[🧱 Set Buffer]` OR `/buffer` in runner | No direct buffer control in admin panel |
| Sub-panel title | `Select Buffer Mode\nCurrent: {mode}` | **Not present** |
| SMALL button | `BUFFER_SMALL` | **Retired** (error message if received) |
| MEDIUM button | `BUFFER_MEDIUM` | **Retired** |
| LARGE button | `BUFFER_LARGE` | **Retired** |
| Persistence target | `settings.json` (key `buffer_mode`) | Strategy config via `/thresholds`, `/sr`, `/spike` slash commands |
| Mutation gate | OWNER or ADMIN role | `strategy.thresholds.write` permission via canonical permission matrix |
| Back button | `[⬅️ Back]` → `ADMIN_BACK` | n/a |
| Current canonical replacement | n/a | `/thresholds`, `/sr`, `/spike` for strategy params; no direct buffer toggle button |

---

## Section 3 — Symbol management

| Dimension | Legacy runner (`bot_control.py`) | Legacy panel (`bak_step16`) | Current (`9912c14`) |
|---|---|---|---|
| Entry path | `/start`, `/forex`, `/crypto` slash | Admin panel → `[🧩 Set Symbols]` | `/symbols list` slash or `ADMIN_NAV:SYMBOLS` |
| Screen title | Category-specific Romanian text | `Active Symbols (<count>)\nTap to toggle` | Text from `admin_commands.handle_symbols` |
| Per-symbol toggle button | `✅/⬜ {SYM}` → `tg:<cat>:<sym>` | `✅ {SYM}` → `SYM_TOGGLE:{sym}` | **Not present** — view-only from nav |
| Add symbol | None | Toggle-based add | `/symbols add {SYMBOL}` slash |
| Remove symbol | Toggle-based remove | Toggle-based remove | `/symbols remove {SYMBOL}` slash |
| All/None control | `__ALL__`, `__NONE__` callbacks | None | None |
| Refresh control | `__REFRESH__` callback | Reload via Back then re-entry | `[🔄 Refresh Symbols]` → `ADMIN_NAV:SYMBOLS` |
| Max displayed | 3 per row (all symbols) | 12 | View text (no inline toggle grid) |
| Language | Romanian | English | English |
| State file | `active_symbols.json` | `symbols.json` (canonical) | Canonical `symbols.json` via `admin_commands` |
| Mutation gate | None (any user, any chat) | OWNER/ADMIN role | `strategy.symbols.write` permission |
| Back navigation | n/a (standalone panel) | `[⬅️ Back]` → `ADMIN_BACK` | `[⬅️ Admin]` → `ADMIN_NAV:HOME` |

---

## Section 4 — Status view

| Dimension | Legacy panel | Current |
|---|---|---|
| Entry path | Admin panel → `[📡 Status]` or `/status` | `/status` slash or `ADMIN_NAV:STATUS` |
| Title | `📡 System Status` | `BinaryBot Status` (from `render_status_text`) |
| Mode field | `Mode: FOCUS_MODE / WIDE_SCAN` | `Runtime phase: {RUNNING/BLOCKED/...}` |
| Buffer field | `Buffer: {mode}` | Not shown in status; accessible via `/strategy` |
| Active symbols | `Active symbols: {count}` | Not shown (accessible via `/symbols`) |
| Watchlist field | `Focus/watchlist: {list}` | `FSM: {mode} watchlist={count}` |
| Tier state | Per-tier lines (FREE/BASIC/PRO/ELITE) | Not in /status (in `/report`) |
| Telegram state | Not shown | `Telegram: ENABLED (polling started/pending)` |
| Shadow mode | Not shown | `Shadow mode: ON/OFF` |
| Broker state | Not shown | `Broker execution: {state}` |
| Recovery | Not shown | `Recovery: {state}` |
| Market data | Not shown | `Market data: {state}` |
| Persistent buttons | Admin home panel returned as reply_markup | Status markup: `[📈 Strategy]` `[⚙️ Engine]` `[⬅️ Admin]` |
| Auth requirement | `in_admin_context` + any role | `/status` is public (no auth gate) |

---

## Section 5 — Research / Report / Debug

| Dimension | Legacy research | Current report | Current debug |
|---|---|---|---|
| Entry | Admin panel `[📊 Research]` | `/report` slash or `ADMIN_NAV:REPORT` | `/debug` slash or `ADMIN_NAV:DEBUG` |
| Content | Placeholder: "coming next — analytics_engine.py" | Latest strategy report from `admin_commands` | Latest decision debug snapshot |
| Auth | OWNER, ADMIN, ANALYST | `reports.view` permission | `debug.view` permission |
| Panel buttons | Admin home returned as reply_markup | `[⬅️ Admin]` | `[⬅️ Admin]` |
| Functional | Placeholder only | ✅ Real data | ✅ Real data |

---

## Section 6 — Docs viewer

| Dimension | Legacy | Current |
|---|---|---|
| Entry | Admin panel → `[📚 View Docs]` | **Not present** |
| Screen | File list from `/opt/binarybot/docs/*.md` | n/a |
| Callback format | `DOC:{filename}` | Retired |
| Action | `telegram_publisher.send_document(...)` | Not available |
| Auth | Any role with admin panel access | n/a |
| Canonical replacement | None (docs are not surfaced via bot at HEAD) | Docs exist as files in git; no bot-facing viewer |

---

## Section 7 — Roles and reload (new capability, no legacy equivalent)

| Dimension | Legacy | Current |
|---|---|---|
| Roles view | None | `/roles` slash or `ADMIN_NAV:ROLES` |
| Roles reload | None | `/roles_reload` (admin topic) or `ADMIN_NAV:RELOAD_ROLES_CONFIRM` → `ADMIN_NAV:RELOAD_ROLES_EXEC` |
| Affiliate | None | `/affiliate` slash or `ADMIN_NAV:AFFILIATE` |
| Confirmation screen | None | `♻️ Confirmation` with `[✅ Confirm Reload]` `[❌ Cancel]` |

---

## Section 8 — Authentication and access model

| Dimension | Legacy runner (`bot_control.py`) | Legacy admin panel (`bak_step16`) | Current (`9912c14`) |
|---|---|---|---|
| Password required | **No** | **No** | **No** |
| Session/token auth | None | None | None |
| Owner identity source | None (no auth) | `config/rbac.json` → `users` dict; fallback `ADMIN_USER_ID` | `config/admin_roles.json` `owner` list; env fallback `OWNER_TELEGRAM_ID` |
| Context gate (slash) | None | `in_admin_context(chat_id)` fail-open | `_can_run_admin_command`: owner-private subset OR admin topic |
| Context gate (callback) | None | `in_admin_context(chat_id)` fail-open | `_can_use_admin_callback`: owner-private OR admin topic; fail-closed |
| Role model | None / flat | OWNER/ADMIN/ANALYST/MODERATOR (legacy flat roles) | OWNER/PRIMARY_ADMIN/STRATEGY_ADMIN/RESEARCH_ADMIN/ANALYST/MODERATOR/AFFILIATE_ADMIN/USER |
| Permission model | Role string equality checks inline | Role string equality checks inline | Permission matrix (`admin_permissions.py`) + file-based overlay |
| Missing config behavior | n/a | Fail-open (allow if ADMIN_CONTROL_CHAT_ID == 0) | Fail-closed (deny if ADMIN_CONTROL_CHAT_ID == 0) |
| Owner private DM | Works (no chat gate in legacy dispatcher) | Works (no slash chat gate pre-49aaeb4) | Works for _OWNER_PRIVATE_COMMANDS subset |
| `/report` in private DM | N/A | Would work (no slash gate) | **Works** (`/report` is in `_OWNER_PRIVATE_COMMANDS`) |

> **Clarification on the `/report` "Access denied" question:**  
> Current code DOES allow `/report` in owner private DM — it is in `_OWNER_PRIVATE_COMMANDS`.  
> If an owner observes "Access denied (wrong chat)" for `/report` in their private DM, the most likely causes are:  
> 1. `OWNER_TELEGRAM_ID` is not set or set to the wrong value, so `is_owner(user_id)` returns `False`.  
> 2. `_is_owner_private_context` fails because the chat type is not `private` or the chat_id does not match user_id.  
> 3. A stale deployment does not yet include commit `64345ae` (owner-private access was introduced there).  
> Evidence: `send/core/bot_service.py:40-52` (OWNER_PRIVATE_COMMANDS includes `/report`), `send/core/bot_service.py:102-105` (gate logic).

---

## Section 9 — Legacy-to-current action mapping

| Legacy action / button | Current canonical equivalent | Notes |
|---|---|---|
| `/admin` (panel home) | `/admin` → `🛠️ Admin Panel` + nav buttons | Same slash, new UX |
| `ADMIN_STATUS` callback | `ADMIN_NAV:STATUS` or `/status` | No auth gate on `/status` now (public) |
| `ADMIN_SET_BUFFER` callback | `/thresholds`, `/sr`, `/spike` | Strategy params split into typed commands |
| `BUFFER_SMALL/MEDIUM/LARGE` | No direct equivalent button | Must use slash mutation commands |
| `ADMIN_SET_SYMBOLS` callback | `ADMIN_NAV:SYMBOLS` → view, then `/symbols add/remove` for mutations | View/mutation split |
| `SYM_TOGGLE:{sym}` | `/symbols add {sym}` or `/symbols remove {sym}` | Slash-based mutation |
| `ADMIN_RESEARCH` callback | `ADMIN_NAV:REPORT` + `ADMIN_NAV:DEBUG` | Split into two real panels |
| `ADMIN_DOCS` callback | Not present | No current bot-facing docs viewer |
| `DOC:{filename}` | Not present | Not implemented |
| `ADMIN_BACK` | `ADMIN_NAV:HOME` | Same function, new prefix |
| `/forex` + `/crypto` (runner) | Not present | Runner deleted; symbol mgmt via `/symbols` |
| `/buffer` (runner, Romanian) | Not present | Buffer management via strategy slashes |
| `/open {SYM}` (runner) | Not present | FSM-managed; no direct trade-confirm slash |
| `buffer_set:small/medium/large` | Not present | Runner deleted |
| `tg:<cat>:<sym>` | Not present | Runner deleted |
