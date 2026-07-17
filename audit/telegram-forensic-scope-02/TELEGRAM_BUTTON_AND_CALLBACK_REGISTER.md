# TELEGRAM_BUTTON_AND_CALLBACK_REGISTER

## Audit metadata
- HEAD at audit time: `9912c14`
- No code modifications made during this audit.
- Evidence: `send/legacy/bot_control.py` (`0fb9112`), `send/_archive/backups/bot_service.py.bak_step16`, `send/core/telegram_admin_ui.py` (current), `send/core/bot_service.py` (current).

---

## Part 1 — Legacy runner callbacks (`send/legacy/bot_control.py`)

### Symbol toggle callbacks

| Button label | callback_data | Action |
|---|---|---|
| `✅ {SYMBOL}` or `⬜ {SYMBOL}` | `tg:forex:{SYMBOL}` | Toggle FOREX symbol active/inactive |
| `✅ {SYMBOL}` or `⬜ {SYMBOL}` | `tg:crypto:{SYMBOL}` | Toggle CRYPTO symbol active/inactive |
| `✅ All` or `⬜ All` | `tg:forex:__ALL__` | Activate all FOREX symbols |
| `⬜ All` or `✅ All` | `tg:crypto:__ALL__` | Activate all CRYPTO symbols |
| `✅ None` or `⬜ None` | `tg:forex:__NONE__` | Deactivate all FOREX symbols |
| `⬜ None` or `✅ None` | `tg:crypto:__NONE__` | Deactivate all CRYPTO symbols |
| `🔄 Refresh` | `tg:forex:__REFRESH__` | Re-render FOREX keyboard (no state change) |
| `🔄 Refresh` | `tg:crypto:__REFRESH__` | Re-render CRYPTO keyboard (no state change) |

Callback format: `tg:<category>:<symbol_or_special>`
- `<category>` ∈ `{forex, crypto}`
- `<symbol_or_special>` ∈ `{EURUSD, GBPUSD, ..., __ALL__, __NONE__, __REFRESH__}`

State file: `/opt/binarybot/active_symbols.json` (structure: `{"forex": [...], "crypto": [...]}`)

### Buffer callbacks (Romanian runner)

| Button label | callback_data | Action |
|---|---|---|
| `✅ MIC  ` (or `☐ MIC  `) | `buffer_set:small` | Set buffer mode to SMALL |
| `✅ MEDIU` (or `☐ MEDIU`) | `buffer_set:medium` | Set buffer mode to MEDIUM |
| `✅ MARE ` (or `☐ MARE `) | `buffer_set:large` | Set buffer mode to LARGE |

State file: `/opt/binarybot/settings.json` key `buffer_mode` (lowercase: `small/medium/large`)

---

## Part 2 — Legacy admin panel callbacks (`bot_service.py.bak_step16`)

### Admin panel home buttons

| Button label | callback_data | Roles that see it | Action |
|---|---|---|---|
| `🧱 Set Buffer` | `ADMIN_SET_BUFFER` | OWNER, ADMIN | Navigate to buffer sub-panel |
| `🧩 Set Symbols` | `ADMIN_SET_SYMBOLS` | OWNER, ADMIN | Navigate to symbols sub-panel |
| `📡 Status` | `ADMIN_STATUS` | OWNER, ADMIN, ANALYST, MODERATOR | Show system status (no nav) |
| `📊 Research` | `ADMIN_RESEARCH` | OWNER, ADMIN, ANALYST | Show placeholder research text |
| `📚 View Docs` | `ADMIN_DOCS` | OWNER, ADMIN, ANALYST, MODERATOR | Navigate to docs file list |

### Buffer sub-panel buttons

| Button label | callback_data | Roles | Action |
|---|---|---|---|
| `SMALL` | `BUFFER_SMALL` | OWNER, ADMIN | Set buffer = SMALL |
| `MEDIUM` | `BUFFER_MEDIUM` | OWNER, ADMIN | Set buffer = MEDIUM |
| `LARGE` | `BUFFER_LARGE` | OWNER, ADMIN | Set buffer = LARGE |
| `⬅️ Back` | `ADMIN_BACK` | All | Return to admin home panel |

### Symbol sub-panel buttons

| Button label | callback_data | Roles | Action |
|---|---|---|---|
| `✅ {sym}` (up to 12 symbols) | `SYM_TOGGLE:{sym}` | OWNER, ADMIN | Toggle symbol in symbols.json |
| `⬅️ Back` | `ADMIN_BACK` | All | Return to admin home panel |

### Docs sub-panel buttons

| Button label | callback_data | Roles | Action |
|---|---|---|---|
| `{filename}.md` (up to 20) | `DOC:{filename}` | All | Send file as Telegram document |
| `⬅️ Back` | `ADMIN_BACK` | All | Return to admin home panel |

### Global navigation

| Button label | callback_data | Action |
|---|---|---|
| `⬅️ Back` | `ADMIN_BACK` | Returns to `🔐 Admin Panel` home screen |

### Retired callback_data set (still named in current bot_service.py as `_RETIRED_ADMIN_CALLBACKS`)

```python
_RETIRED_ADMIN_CALLBACKS = frozenset({
    "ADMIN_STATUS",
    "ADMIN_SET_BUFFER",
    "ADMIN_SET_SYMBOLS",
    "ADMIN_RESEARCH",
    "ADMIN_DOCS",
    "ADMIN_BACK",
})
_RETIRED_ADMIN_PREFIXES = ("BUFFER_", "SYM_TOGGLE:", "DOC:")
```

These are explicitly rejected in the current dispatcher with:
`"Admin panel buttons are retired. Use canonical slash commands (/admin, /strategy, /engine, etc.)."`

---

## Part 3 — Current canonical admin UI callbacks (`send/core/telegram_admin_ui.py`, HEAD `9912c14`)

Callback prefix: `ADMIN_NAV:` (all current admin panel callbacks use this prefix)

### Admin home panel (`admin_home_markup`)

| Button label | callback_data | Action dispatched | Visible in private? |
|---|---|---|---|
| `📡 Status` | `ADMIN_NAV:STATUS` | `/status` | Yes |
| `📈 Strategy` | `ADMIN_NAV:STRATEGY` | `/strategy` | Yes |
| `🧩 Symbols` | `ADMIN_NAV:SYMBOLS` | `/symbols list` | Yes |
| `⚙️ Engine` | `ADMIN_NAV:ENGINE` | `/engine` | Yes |
| `🧪 Debug` | `ADMIN_NAV:DEBUG` | `/debug` | Yes |
| `📊 Report` | `ADMIN_NAV:REPORT` | `/report` | Yes |
| `👥 Roles` | `ADMIN_NAV:ROLES` | `/roles` | Yes |
| `💼 Affiliate` | `ADMIN_NAV:AFFILIATE` | `/affiliate` | Yes |
| `♻️ Reload Roles` | `ADMIN_NAV:RELOAD_ROLES_CONFIRM` | Confirm screen | **No** (hidden in private) |

### Status panel (`status_markup`)

| Button label | callback_data | Action dispatched |
|---|---|---|
| `📈 Strategy` | `ADMIN_NAV:STRATEGY` | `/strategy` |
| `⚙️ Engine` | `ADMIN_NAV:ENGINE` | `/engine` |
| `⬅️ Admin` | `ADMIN_NAV:HOME` | `/admin` |

### Strategy panel (`strategy_markup`)

| Button label | callback_data | Action dispatched |
|---|---|---|
| `🎯 Thresholds` | `ADMIN_NAV:THRESHOLDS` | `/thresholds` |
| `📐 SR` | `ADMIN_NAV:SR` | `/sr` |
| `⚡ Spike` | `ADMIN_NAV:SPIKE` | `/spike` |
| `🧩 Symbols` | `ADMIN_NAV:SYMBOLS` | `/symbols list` |
| `⬅️ Admin` | `ADMIN_NAV:HOME` | `/admin` |

### Symbols panel (`symbols_markup`)

| Button label | callback_data | Action dispatched |
|---|---|---|
| `🔄 Refresh Symbols` | `ADMIN_NAV:SYMBOLS` | `/symbols list` (re-render) |
| `📈 Strategy` | `ADMIN_NAV:STRATEGY` | `/strategy` |
| `⬅️ Admin` | `ADMIN_NAV:HOME` | `/admin` |

### Engine panel (`engine_markup`)

| Button label | callback_data | Action dispatched | Visible in private? |
|---|---|---|---|
| `🔄 Refresh Engine` | `ADMIN_NAV:ENGINE` | `/engine` (re-render) | Yes |
| `📡 Status` | `ADMIN_NAV:STATUS` | `/status` | Yes |
| `♻️ Reload Roles` | `ADMIN_NAV:RELOAD_ROLES_CONFIRM` | Confirm screen | **No** (hidden in private) |
| `⬅️ Admin` | `ADMIN_NAV:HOME` | `/admin` | Yes |

### Standard back markup (`standard_back_markup`)

Used by: Debug, Report, Roles, Affiliate sub-panels.

| Button label | callback_data | Action |
|---|---|---|
| `⬅️ Admin` | `ADMIN_NAV:HOME` | Return to admin home |

### Reload confirmation markup (`reload_confirm_markup`)

Only reachable from admin topic context.

| Button label | callback_data | Action |
|---|---|---|
| `✅ Confirm Reload` | `ADMIN_NAV:RELOAD_ROLES_EXEC` | Execute `/roles_reload` |
| `❌ Cancel` | `ADMIN_NAV:HOME` | Return to admin home |

---

## Part 4 — Outcome/vote callbacks (public signals, all eras)

These appear on signal distribution messages, not admin panels.

| callback_data pattern | Handler | Still active? |
|---|---|---|
| `VOTE_\|<signal_id>\|<outcome>` | `outcome_service.handle_vote_callback` | **Yes** |
| `VOTE_<data>` (generic) | `outcome_service.handle_vote_callback_data` | **Yes** |
| `OUTCOME:<outcome>:<signal_id>` | `outcome_service.handle_vote_callback` (delegation) | **Yes** |

No chat context required for VOTE_ callbacks. Any chat/user can submit.

---

## Complete callback_data namespace summary

| Namespace / prefix | Era | Status |
|---|---|---|
| `tg:<cat>:<sym\|__ALL__\|__NONE__\|__REFRESH__>` | Hetzner runner | ❌ File deleted (BATCH-09); callback code gone |
| `buffer_set:<small\|medium\|large>` | Hetzner runner | ❌ File deleted; callback code gone |
| `ADMIN_STATUS`, `ADMIN_SET_BUFFER`, `ADMIN_SET_SYMBOLS`, `ADMIN_RESEARCH`, `ADMIN_DOCS`, `ADMIN_BACK` | Legacy panel | ❌ Explicitly retired (returns error message) |
| `BUFFER_SMALL`, `BUFFER_MEDIUM`, `BUFFER_LARGE` | Legacy panel | ❌ Explicitly retired (BUFFER_ prefix) |
| `SYM_TOGGLE:<symbol>` | Legacy panel | ❌ Explicitly retired (SYM_TOGGLE: prefix) |
| `DOC:<filename>` | Legacy panel | ❌ Explicitly retired (DOC: prefix) |
| `ADMIN_NAV:<action>` | Current canonical | ✅ Active |
| `VOTE_\|...\|...` | BATCH-04+ canonical | ✅ Active |
| `VOTE_<...>` | Canonical | ✅ Active |
| `OUTCOME:<...>:<...>` | Legacy format, delegated | ✅ Active |
