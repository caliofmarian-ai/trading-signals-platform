# OLD_VS_CURRENT_TELEGRAM_UI_COMPARISON

## Audit metadata

- **Audited HEAD:** `0e736ae251dcb81dee7d13a34bbcfafcafe36967`
- **No code modifications were made during this audit.**
- **Evidence:** legacy files (git history), current HEAD source files

---

## Section 1 — Admin panel home screen

| Dimension | Legacy runner (Era A) | Legacy admin panel (Era B, bak_step16) | Current HEAD (Era C, 0e736ae) |
|---|---|---|---|
| Entry command | `/start` (auto-sends panels) | `/admin` | `/admin` |
| Title text | n/a | `🔐 Admin Panel\nRole: {role}` | `🛠️ Admin Panel\n{identity/summary text}` |
| Lock emoji | n/a | 🔐 | 🛠️ |
| Role shown in title | n/a | Yes | No (role in identity block) |
| Status button | n/a | `📡 Status` → `ADMIN_STATUS` | `📡 Status` → `ADMIN_NAV:STATUS` |
| Strategy button | n/a | None | `📈 Strategy` → `ADMIN_NAV:STRATEGY` |
| Symbols button | n/a | `🧩 Set Symbols` → `ADMIN_SET_SYMBOLS` | `🧩 Symbols` → `ADMIN_NAV:SYMBOLS` |
| Buffer button | n/a | `🧱 Set Buffer` → `ADMIN_SET_BUFFER` | **Not present** |
| Engine button | n/a | None | `⚙️ Engine` → `ADMIN_NAV:ENGINE` |
| Debug button | n/a | None | `🧪 Debug` → `ADMIN_NAV:DEBUG` |
| Report button | n/a | None | `📊 Report` → `ADMIN_NAV:REPORT` |
| Roles button | n/a | None | `👥 Roles` → `ADMIN_NAV:ROLES` |
| Affiliate button | n/a | None | `💼 Affiliate` → `ADMIN_NAV:AFFILIATE` |
| Research button | n/a | `📊 Research` → `ADMIN_RESEARCH` | **Not present** |
| Docs button | n/a | `📚 View Docs` → `ADMIN_DOCS` | **Not present** |
| Reload roles button | n/a | None | `♻️ Reload Roles` → `ADMIN_NAV:RELOAD_ROLES_CONFIRM` (admin topic only) |
| Per-button role filtering | n/a | Yes (different sets per role) | No (single set; permission gate inside admin_commands) |
| Back button on home | n/a | Not applicable | Not applicable |

---

## Section 2 — Buffer management

| Dimension | Legacy runner (Era A) | Legacy admin panel (Era B) | Current (Era C) |
|---|---|---|---|
| Access path | `/buffer` standalone command | Admin home → `[🧱 Set Buffer]` | **No direct path** |
| Sub-panel title | `Alege Buffer (Mic / Mediu / Mare):` (Romanian) | `Select Buffer Mode\nCurrent: {mode}` | n/a |
| Button labels | `✅ MIC  ` / `☐ MEDIU` / `☐ MARE ` (NBSP-padded) | `SMALL` / `MEDIUM` / `LARGE` (plain text, no emoji) | n/a |
| Callback format | `buffer_set:small/medium/large` | `BUFFER_SMALL/MEDIUM/LARGE` | Retired (error if received) |
| Current mode indicator | `✅` on active button | Shown in message text | n/a |
| Persistence | `settings.json["buffer_mode"]` | same | Strategy params via `/thresholds`, `/sr`, `/spike` |
| Mutation gate | None (any user any chat) | OWNER/ADMIN role + admin context | `strategy.thresholds.write` permission |
| Back navigation | n/a (standalone) | `[⬅️ Back]` → `ADMIN_BACK` | n/a |

---

## Section 3 — Symbol management

| Dimension | Legacy runner (Era A) | Legacy admin panel (Era B) | Current (Era C) |
|---|---|---|---|
| Entry path | `/start`, `/forex`, `/crypto` | Admin home → `[🧩 Set Symbols]` | `/symbols list` or `ADMIN_NAV:SYMBOLS` |
| FOREX screen title | `📊 FOREX — Symbol Selector\nBifezi/debifezi...` (Romanian) | `Active Symbols (<N>)\nTap to toggle` | `🧩 Symbols Panel\n{text list}` |
| CRYPTO screen title | `🪙 CRYPTO — Symbol Selector\n...` (Romanian) | same (combined with FOREX) | same |
| Per-symbol toggle button | `✅/⬜ {SYM}` → `tg:<cat>:<sym>` | `✅ {SYM}` → `SYM_TOGGLE:{sym}` | **Not present** (view only) |
| All symbols shown | Yes (all from static list) | No (only first 12 active) | Text list of all active |
| ALL/NONE control | `__ALL__`, `__NONE__` callbacks | None | None |
| Refresh control | `__REFRESH__` callback | Re-entry after back | `[🔄 Refresh Symbols]` → `ADMIN_NAV:SYMBOLS` |
| Add symbol | Not possible | Toggle-based (add missing) | `/symbols add {SYMBOL}` |
| Remove symbol | Toggle-based (deactivate) | Toggle-based (remove active) | `/symbols remove {SYMBOL}` |
| Row layout | 3 per row | 1 per row | Text only |
| Language | Romanian | English | English |
| State file | `active_symbols.json` | `symbols.json` | Canonical via admin_commands |
| Mutation gate | None | OWNER/ADMIN + admin context | `strategy.symbols.write` |
| Back navigation | n/a (standalone panel) | `[⬅️ Back]` → `ADMIN_BACK` | `[⬅️ Admin]` → `ADMIN_NAV:HOME` |

---

## Section 4 — Status view

| Dimension | Legacy (Era B) | Current (Era C) |
|---|---|---|
| Entry | `[📡 Status]` → `ADMIN_STATUS` or `/status` | `/status` or `ADMIN_NAV:STATUS` |
| Title | `📡 System Status` | `📡 Status Panel\n{status text}` |
| Mode field | `Mode: FOCUS_MODE / WIDE_SCAN` | `Runtime phase: {RUNNING/BLOCKED/...}` |
| Buffer field | `Buffer: {mode}` | Not in status (accessible via `/strategy`) |
| Active symbols | `Active symbols: {N}` | Not in status (via `/symbols`) |
| Watchlist | `Focus/watchlist: {list}` | `FSM: {mode} watchlist={N}` |
| Tier lines | FREE/BASIC/PRO/ELITE breakdown | Not in status |
| Telegram state | Not shown | `Telegram: ENABLED (polling started/pending)` |
| Shadow mode | Not shown | `Shadow mode: ON/OFF` |
| Recovery state | Not shown | `Recovery: {state}` |
| Buttons below status | Admin home panel (persistent) | `[📈 Strategy] [⚙️ Engine]` + `[⬅️ Admin]` |

---

## Section 5 — Docs viewer

| Dimension | Legacy (Era B) | Current (Era C) |
|---|---|---|
| Entry | `[📚 View Docs]` → `ADMIN_DOCS` | **Not present** |
| Screen title | `📚 Docs Viewer\nSelect a document:` | n/a |
| File buttons | One per `.md` file from `/opt/binarybot/docs/`, up to 20 | n/a |
| Callback | `DOC:{filename}` | Retired (error if received) |
| Delivery | `sendDocument` API call | No equivalent |
| Back button | `[⬅️ Back]` → `ADMIN_BACK` | n/a |

---

## Section 6 — Research panel

| Dimension | Legacy (Era B) | Current (Era C) |
|---|---|---|
| Entry | `[📊 Research]` → `ADMIN_RESEARCH` | **Not present** |
| Content | Placeholder: "coming next — analytics_engine.py" | Analytics via `/report`, `/debug` |
| Buttons | Admin home panel persistent | n/a |
| Callback | `ADMIN_RESEARCH` | Retired |

---

## Section 7 — Confirmation screens

| Action | Legacy | Current |
|---|---|---|
| Buffer mode set | No confirmation; immediate mutation | No buffer button (slash only) |
| Symbol toggle | No confirmation; immediate mutation | No toggle button (slash only) |
| Roles reload | No equivalent | `[✅ Confirm Reload] [❌ Cancel]` via `ADMIN_NAV:RELOAD_ROLES_CONFIRM` |
| Strategy changes | No confirmation | Immediate on slash (no confirm screen) |

---

## Section 8 — Outcome buttons (signal channels)

| Dimension | Legacy | Current |
|---|---|---|
| Format | `OUTCOME:<outcome>:<signal_id>` | `VOTE_\|<signal_id>\|<outcome>` (primary); `OUTCOME:` still handled |
| Button labels | Varied | `✅ WIN`, `❌ LOSS`, `— NEUTRAL` |
| After vote | Unknown | Message edited; keyboard removed |
| Double-vote | Unknown | `"Outcome already recorded."` |

---

## Section 9 — Classification of each legacy UI capability

| Legacy capability | Classification | Reason |
|---|---|---|
| FOREX symbol toggle grid (`tg:forex:*`) | **Removed** | `bot_control.py` deleted; callbacks not handled |
| CRYPTO symbol toggle grid (`tg:crypto:*`) | **Removed** | same |
| Buffer mode selector — runner (`buffer_set:*`) | **Removed** | Runner deleted |
| /open trade confirmation | **Removed** | No equivalent |
| Admin home panel (buttons) | **Partially present** | Restructured with `ADMIN_NAV:` prefix and different button set |
| Buffer mode selector — admin panel (`BUFFER_*`) | **Superseded** | `/thresholds` slash command handles strategy params |
| Symbol toggle sub-panel (`SYM_TOGGLE:*`) | **Removed** (view only via `ADMIN_NAV:SYMBOLS`) | Toggle buttons not present; slash mutations available |
| Status view | **Still present** | Restructured via `ADMIN_NAV:STATUS` |
| Research panel | **Removed** | No equivalent; analytics available via /report, /debug |
| Docs viewer button (`ADMIN_DOCS`, `DOC:*`) | **Removed** | No equivalent button |
| Back navigation (`ADMIN_BACK`) | **Superseded** | `ADMIN_NAV:HOME` |
| Role-filtered buttons | **Partially present** | Permission gated inside admin_commands, not in UI rendering |
| Roles reload button | **Partially present** | Added in current era; private DM blocked |
| Signal vote buttons | **Still present** | `VOTE_\|` format; `OUTCOME:` legacy handled |
| Password authentication | **Never present** | No evidence in any era |
| Session management | **Never present** | No evidence in any era |
| Symbol toggle (`ADMIN_NAV:SYMBOLS_TOGGLE:*`) | **Recommended to restore** | Not present; design specified in CANONICAL_UI_RESTORATION_PLAN.md |
| Buffer quick-select buttons | **Recommended to restore** | Not present; design specified |
| Docs viewer from panel | **Recommended to restore** | Not present; design specified |
