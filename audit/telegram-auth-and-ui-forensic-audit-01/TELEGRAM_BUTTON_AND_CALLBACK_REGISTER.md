# TELEGRAM_BUTTON_AND_CALLBACK_REGISTER

## Audit metadata

- **Audited HEAD:** `0e736ae251dcb81dee7d13a34bbcfafcafe36967`
- **No code modifications were made during this audit.**
- **Evidence:** `send/legacy/bot_control.py` (git history), `send/_archive/backups/bot_service.py.bak_step16`, `send/core/telegram_admin_ui.py` (HEAD), `send/core/bot_service.py` (HEAD)

---

## PART 1 — Legacy runner callbacks (`send/legacy/bot_control.py`, pre-BATCH-09)

### Family: `tg:<category>:<symbol_or_control>`

Used for symbol toggle and control in the standalone runner.

| Button label | callback_data | Action | State file |
|---|---|---|---|
| `✅ EURUSD` or `⬜ EURUSD` | `tg:forex:EURUSD` | Toggle FOREX symbol active/inactive | `active_symbols.json["forex"]` |
| `✅ GBPUSD` or `⬜ GBPUSD` | `tg:forex:GBPUSD` | Toggle FOREX symbol | same |
| `✅ {SYM}` or `⬜ {SYM}` | `tg:forex:{SYM}` | Toggle any FOREX symbol | same |
| `✅ BTC/USD` or `⬜ BTC/USD` | `tg:crypto:BTC/USD` | Toggle CRYPTO symbol | `active_symbols.json["crypto"]` |
| `✅ {SYM}` or `⬜ {SYM}` | `tg:crypto:{SYM}` | Toggle any CRYPTO symbol | same |
| `✅ All` | `tg:forex:__ALL__` | Activate all FOREX symbols | same |
| `⬜ All` | `tg:forex:__ALL__` | (same button, state-dependent label) | same |
| `✅ All` | `tg:crypto:__ALL__` | Activate all CRYPTO symbols | same |
| `⬜ All` | `tg:crypto:__ALL__` | same | same |
| `✅ None` | `tg:forex:__NONE__` | Deactivate all FOREX symbols | same |
| `⬜ None` | `tg:forex:__NONE__` | same | same |
| `✅ None` | `tg:crypto:__NONE__` | Deactivate all CRYPTO symbols | same |
| `⬜ None` | `tg:crypto:__NONE__` | same | same |
| `🔄 Refresh` | `tg:forex:__REFRESH__` | Re-render FOREX keyboard (no mutation) | same |
| `🔄 Refresh` | `tg:crypto:__REFRESH__` | Re-render CRYPTO keyboard (no mutation) | same |

**Pattern:** `tg:<category>:<symbol_or_special>`
- `<category>` ∈ `{forex, crypto}`
- `<symbol_or_special>` ∈ `{EURUSD, GBPUSD, ..., __ALL__, __NONE__, __REFRESH__}`

### Family: `buffer_set:<mode>`

| Button label | callback_data | Action | State file |
|---|---|---|---|
| `✅ MIC  ` or `☐ MIC  ` | `buffer_set:small` | Set buffer mode to SMALL | `settings.json["buffer_mode"]` |
| `✅ MEDIU` or `☐ MEDIU` | `buffer_set:medium` | Set buffer mode to MEDIUM | same |
| `✅ MARE ` or `☐ MARE ` | `buffer_set:large` | Set buffer mode to LARGE | same |

**Pattern:** `buffer_set:<mode>` where `<mode>` ∈ `{small, medium, large}`

---

## PART 2 — Legacy admin panel callbacks (`bot_service.py.bak_step16`)

### Family: `ADMIN_*` (home panel navigation)

| Button label | callback_data | Visible to roles | Action |
|---|---|---|---|
| `🧱 Set Buffer` | `ADMIN_SET_BUFFER` | OWNER, ADMIN | Navigate to buffer sub-panel (Screen B2) |
| `🧩 Set Symbols` | `ADMIN_SET_SYMBOLS` | OWNER, ADMIN | Navigate to symbols sub-panel (Screen B3) |
| `📡 Status` | `ADMIN_STATUS` | OWNER, ADMIN, ANALYST, MODERATOR | Show system status inline |
| `📊 Research` | `ADMIN_RESEARCH` | OWNER, ADMIN, ANALYST | Show research placeholder |
| `📚 View Docs` | `ADMIN_DOCS` | OWNER, ADMIN, ANALYST, MODERATOR | Navigate to docs list (Screen B6) |
| `⬅️ Back` | `ADMIN_BACK` | All | Return to admin home panel |

### Family: `BUFFER_<mode>` (buffer sub-panel)

| Button label | callback_data | Visible to roles | Action |
|---|---|---|---|
| `SMALL` | `BUFFER_SMALL` | OWNER, ADMIN | Set buffer = SMALL; return to home |
| `MEDIUM` | `BUFFER_MEDIUM` | OWNER, ADMIN | Set buffer = MEDIUM; return to home |
| `LARGE` | `BUFFER_LARGE` | OWNER, ADMIN | Set buffer = LARGE; return to home |
| `⬅️ Back` | `ADMIN_BACK` | All | Return to admin home |

**Pattern:** `BUFFER_<MODE>` where `<MODE>` ∈ `{SMALL, MEDIUM, LARGE}`

### Family: `SYM_TOGGLE:<symbol>` (symbol sub-panel)

| Button label | callback_data | Visible to roles | Action |
|---|---|---|---|
| `✅ EURUSD` | `SYM_TOGGLE:EURUSD` | OWNER, ADMIN | Toggle EURUSD (remove from active if present) |
| `✅ {SYM}` | `SYM_TOGGLE:{SYM}` | OWNER, ADMIN | Toggle any active symbol |
| `⬅️ Back` | `ADMIN_BACK` | All | Return to admin home |

**Pattern:** `SYM_TOGGLE:<SYMBOL>` where `<SYMBOL>` is any uppercase symbol string

### Family: `DOC:<filename>` (docs viewer sub-panel)

| Button label | callback_data | Visible to roles | Action |
|---|---|---|---|
| `{filename}.md` | `DOC:{filename}` | All | Send file as Telegram document |
| `⬅️ Back` | `ADMIN_BACK` | All | Return to admin home |

**Pattern:** `DOC:<filename>` where `<filename>` is a `.md` filename without path

---

## PART 3 — Current canonical admin UI callbacks (HEAD `0e736ae`, `send/core/telegram_admin_ui.py`)

All current admin navigation callbacks use the prefix `ADMIN_NAV:`.
`parse_action(callback_data)` strips this prefix and returns the action string.
Source: `send/core/telegram_admin_ui.py` CALLBACK_PREFIX = `"ADMIN_NAV:"`

### Family: `ADMIN_NAV:<action>` (all current admin navigation)

#### Admin home panel (`admin_home_markup`)

| Button label | callback_data | Action dispatched | Visible in owner private? |
|---|---|---|---|
| `📡 Status` | `ADMIN_NAV:STATUS` | → `/status` | Yes |
| `📈 Strategy` | `ADMIN_NAV:STRATEGY` | → `/strategy` | Yes |
| `🧩 Symbols` | `ADMIN_NAV:SYMBOLS` | → `/symbols list` | Yes |
| `⚙️ Engine` | `ADMIN_NAV:ENGINE` | → `/engine` | Yes |
| `🧪 Debug` | `ADMIN_NAV:DEBUG` | → `/debug` | Yes |
| `📊 Report` | `ADMIN_NAV:REPORT` | → `/report` | Yes |
| `👥 Roles` | `ADMIN_NAV:ROLES` | → `/roles` | Yes |
| `💼 Affiliate` | `ADMIN_NAV:AFFILIATE` | → `/affiliate` | Yes |
| `♻️ Reload Roles` | `ADMIN_NAV:RELOAD_ROLES_CONFIRM` | → confirmation screen | **No** (hidden via `include_roles_reload=False`) |

#### Status panel (`status_markup`)

| Button label | callback_data | Action dispatched |
|---|---|---|
| `📈 Strategy` | `ADMIN_NAV:STRATEGY` | → `/strategy` |
| `⚙️ Engine` | `ADMIN_NAV:ENGINE` | → `/engine` |
| `⬅️ Admin` | `ADMIN_NAV:HOME` | → `/admin` |

#### Strategy panel (`strategy_markup`)

| Button label | callback_data | Action dispatched |
|---|---|---|
| `🎯 Thresholds` | `ADMIN_NAV:THRESHOLDS` | → `/thresholds` |
| `📐 SR` | `ADMIN_NAV:SR` | → `/sr` |
| `⚡ Spike` | `ADMIN_NAV:SPIKE` | → `/spike` |
| `🧩 Symbols` | `ADMIN_NAV:SYMBOLS` | → `/symbols list` |
| `⬅️ Admin` | `ADMIN_NAV:HOME` | → `/admin` |

#### Symbols panel (`symbols_markup`)

| Button label | callback_data | Action dispatched |
|---|---|---|
| `🔄 Refresh Symbols` | `ADMIN_NAV:SYMBOLS` | → `/symbols list` (re-render) |
| `📈 Strategy` | `ADMIN_NAV:STRATEGY` | → `/strategy` |
| `⬅️ Admin` | `ADMIN_NAV:HOME` | → `/admin` |

#### Engine panel (`engine_markup`)

| Button label | callback_data | Action dispatched | Visible in private? |
|---|---|---|---|
| `🔄 Refresh Engine` | `ADMIN_NAV:ENGINE` | → `/engine` | Yes |
| `📡 Status` | `ADMIN_NAV:STATUS` | → `/status` | Yes |
| `♻️ Reload Roles` | `ADMIN_NAV:RELOAD_ROLES_CONFIRM` | → confirmation | **No** (hidden in private) |
| `⬅️ Admin` | `ADMIN_NAV:HOME` | → `/admin` | Yes |

#### Standard back panel (`standard_back_markup`) — used by /debug, /report, /roles, /affiliate

| Button label | callback_data | Action dispatched |
|---|---|---|
| `⬅️ Admin` | `ADMIN_NAV:HOME` | → `/admin` |

#### Reload confirmation panel (`reload_confirm_markup`)

| Button label | callback_data | Action dispatched |
|---|---|---|
| `✅ Confirm Reload` | `ADMIN_NAV:RELOAD_ROLES_EXEC` | → `/roles_reload` |
| `❌ Cancel` | `ADMIN_NAV:HOME` | → `/admin` |

---

## PART 4 — Vote/outcome callbacks (current canonical, `send/core/bot_service.py`)

### Family: `VOTE_|<signal_id>|<outcome>`

| Button label | callback_data | Auth gate | Action |
|---|---|---|---|
| `✅ WIN` | `VOTE_\|{signal_id}\|WIN` | None (public) | outcome_service.handle_vote_callback |
| `❌ LOSS` | `VOTE_\|{signal_id}\|LOSS` | None | same |
| `— NEUTRAL` | `VOTE_\|{signal_id}\|NEUTRAL` | None | same |

**Pattern:** `VOTE_|<signal_id>|<outcome>` where `<outcome>` ∈ `{WIN, LOSS, NEUTRAL}`

### Family: `VOTE_*` (generic prefix)

Handled by `outcome_service.handle_vote_callback_data(callback_data=data, ...)`.

### Family: `OUTCOME:<outcome>:<signal_id>`

| callback_data | Auth gate | Action |
|---|---|---|
| `OUTCOME:WIN:<signal_id>` | None | Delegated to outcome_service (legacy format) |
| `OUTCOME:LOSS:<signal_id>` | None | same |
| `OUTCOME:NEUTRAL:<signal_id>` | None | same |

---

## PART 5 — Retired callbacks (named in `bot_service.py` `_RETIRED_ADMIN_CALLBACKS`)

These are explicitly rejected in the current dispatcher with:
`"Admin panel buttons are retired. Use canonical slash commands (/admin, /strategy, /engine, etc.)."`

```python
# send/core/bot_service.py (HEAD 0e736ae)
_RETIRED_ADMIN_CALLBACKS: frozenset = frozenset({
    "ADMIN_STATUS",
    "ADMIN_SET_BUFFER",
    "ADMIN_SET_SYMBOLS",
    "ADMIN_RESEARCH",
    "ADMIN_DOCS",
    "ADMIN_BACK",
})
_RETIRED_ADMIN_PREFIXES = ("BUFFER_", "SYM_TOGGLE:", "DOC:")
```

| Retired callback | Was used for | Retired by | Current replacement |
|---|---|---|---|
| `ADMIN_STATUS` | Status view from admin panel | BATCH-05 | `ADMIN_NAV:STATUS` |
| `ADMIN_SET_BUFFER` | Navigate to buffer sub-panel | BATCH-05 | No direct replacement |
| `ADMIN_SET_SYMBOLS` | Navigate to symbols toggle sub-panel | BATCH-05 | `ADMIN_NAV:SYMBOLS` (view only) |
| `ADMIN_RESEARCH` | Research placeholder | BATCH-05 | No replacement |
| `ADMIN_DOCS` | Navigate to docs viewer | BATCH-05 | No replacement |
| `ADMIN_BACK` | Return to admin home from any sub-panel | BATCH-05 | `ADMIN_NAV:HOME` |
| `BUFFER_SMALL` | Set buffer = small | BATCH-05 | No button; slash `/thresholds` |
| `BUFFER_MEDIUM` | Set buffer = medium | BATCH-05 | same |
| `BUFFER_LARGE` | Set buffer = large | BATCH-05 | same |
| `SYM_TOGGLE:{sym}` | Toggle individual symbol | BATCH-05 | No button; slash `/symbols add/remove` |
| `DOC:{filename}` | Send document file | BATCH-05 | No replacement |

---

## Complete callback family register

| Family prefix | Era | Status |
|---|---|---|
| `tg:forex:` | Legacy runner (Era A) | Retired (runner deleted in BATCH-09) |
| `tg:crypto:` | Legacy runner (Era A) | Retired |
| `buffer_set:` | Legacy runner (Era A) | Retired |
| `ADMIN_SET_BUFFER` | Legacy panel (Era B) | Retired (BATCH-05) |
| `ADMIN_SET_SYMBOLS` | Legacy panel (Era B) | Retired |
| `ADMIN_STATUS` | Legacy panel (Era B) | Retired |
| `ADMIN_RESEARCH` | Legacy panel (Era B) | Retired |
| `ADMIN_DOCS` | Legacy panel (Era B) | Retired |
| `ADMIN_BACK` | Legacy panel (Era B) | Retired |
| `BUFFER_` | Legacy panel (Era B) | Retired |
| `SYM_TOGGLE:` | Legacy panel (Era B) | Retired |
| `DOC:` | Legacy panel (Era B) | Retired |
| `ADMIN_NAV:` | Current canonical (Era C) | **Active** |
| `VOTE_\|` | Canonical (BATCH-04+) | **Active** |
| `VOTE_` (generic) | Canonical (BATCH-04+) | **Active** |
| `OUTCOME:` | Legacy format (Era B+) | **Active** (delegated) |
