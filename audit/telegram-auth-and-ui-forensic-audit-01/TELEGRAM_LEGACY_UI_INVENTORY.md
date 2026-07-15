# TELEGRAM_LEGACY_UI_INVENTORY

## Audit metadata

- **Audited HEAD:** `0e736ae251dcb81dee7d13a34bbcfafcafe36967`
- **No code modifications were made during this audit.**
- **Evidence sources:**
  - `send/legacy/bot_control.py` — deleted at commit `63834b3` (BATCH-09), recovered from git history; commit `0fb9112` version
  - `send/_archive/backups/bot_service.py.bak_step16` — Hetzner import snapshot
  - Prior audit: `audit/telegram-forensic-scope-02/TELEGRAM_LEGACY_UI_INVENTORY.md`

---

## ERA A — Legacy Symbol Runner (`send/legacy/bot_control.py`)

This was a standalone `python-telegram-bot` polling process running on Hetzner.
Deleted in BATCH-09 (`63834b3`). No authentication gate on any command.

### Entry commands

| Command | Purpose | Auth gate |
|---|---|---|
| `/start` | Sends FOREX selector + CRYPTO selector simultaneously | None |
| `/forex` | Sends FOREX symbol selector only | None |
| `/crypto` | Sends CRYPTO symbol selector only | None |
| `/buffer` | Sends buffer mode selector | None |
| `/open <SYMBOL>` | Marks symbol as "open" in focus_state.json | None |

### Screen A1 — FOREX Symbol Selector

```
Message text:
📊 FOREX — Symbol Selector
Bifezi/debifezi simbolurile pe care vrei să le scanez.

Active acum: <N>

Inline keyboard (3 buttons per row):
[✅ EURUSD] [✅ GBPUSD] [⬜ USDJPY]
[✅ USDCHF] [⬜ USDCAD] [✅ AUDUSD]
...
[✅ All   ] [⬜ None  ] [🔄 Refresh]
```

- Text: Romanian
- Symbol source: `/opt/binarybot/symbols.json` (static list, category `"forex"`)
- Active state: `/opt/binarybot/active_symbols.json` (key `"forex": [...]`)
- Toggle logic: checked if symbol in active list; ✅ = active, ⬜ = inactive
- Row width: 3 per row for individual symbols; All/None/Refresh always last row
- State file mutated on each toggle; message edited in-place

### Screen A2 — CRYPTO Symbol Selector

```
Message text:
🪙 CRYPTO — Symbol Selector
Bifezi/debifezi simbolurile pe care vrei să le scanez.

Active acum: <N>

Inline keyboard (3 buttons per row):
[✅ BTC/USD] [✅ ETH/USD] [⬜ XRP/USD]
...
[✅ All    ] [⬜ None   ] [🔄 Refresh]
```

- Identical layout to FOREX; category key `"crypto"`
- Text: Romanian

### Screen A3 — Buffer Mode Selector

```
Message text:
Alege Buffer (Mic / Mediu / Mare):

Inline keyboard (one row, 3 buttons):
[✅ MIC  ] [☐ MEDIU] [☐ MARE ]
```

- Labels padded with NBSP so all buttons equal width
- `✅` = current active mode; `☐` = inactive option
- State file: `/opt/binarybot/settings.json`, key `"buffer_mode"`, values: `"small"/"medium"/"large"`
- On tap: save new mode; edit message to update checkmarks

### Screen A4 — /open confirmation (no keyboard)

```
✅ Confirmed OPEN for {SYMBOL}. Scanner revine la scanare generală când focus se eliberează.
```

- Romanian text: "Scanner returns to general scanning when focus is released."
- No inline keyboard
- Writes to `/opt/binarybot/focus_state.json`

---

## ERA B — Legacy Admin Panel (`send/_archive/backups/bot_service.py.bak_step16`)

This was the Hetzner-era admin control plane integrated into `bot_service.py`.
Entry: `/admin` slash command.
Auth gate: `in_admin_context(chat_id)` + `get_role(user_id)` (RBAC via `config/rbac.json` or `ADMIN_USER_ID` env fallback).
`in_admin_context` was **fail-open** at this revision: if `ADMIN_CONTROL_CHAT_ID == 0`, access was **allowed**.

### Screen B1 — Admin Panel Home

```
Message text:
🔐 Admin Panel
Role: {OWNER|ADMIN|ANALYST|MODERATOR}

Inline keyboard (role-filtered):
```

| Button | callback_data | Visible to |
|---|---|---|
| 🧱 Set Buffer | `ADMIN_SET_BUFFER` | OWNER, ADMIN |
| 🧩 Set Symbols | `ADMIN_SET_SYMBOLS` | OWNER, ADMIN |
| 📡 Status | `ADMIN_STATUS` | OWNER, ADMIN, ANALYST, MODERATOR |
| 📊 Research | `ADMIN_RESEARCH` | OWNER, ADMIN, ANALYST |
| 📚 View Docs | `ADMIN_DOCS` | OWNER, ADMIN, ANALYST, MODERATOR |

No back button on home panel (it is the root screen).

### Screen B2 — Buffer Mode Selector (admin panel variant)

```
Message text:
Select Buffer Mode
Current: {MEDIUM|SMALL|LARGE}

Inline keyboard:
[SMALL] [MEDIUM] [LARGE]
[⬅️ Back]
```

- No emoji on SMALL/MEDIUM/LARGE buttons (plain text only)
- Current mode shown in title, not in button labels
- State file: `settings.json` key `"buffer_mode"`
- `⬅️ Back` → `ADMIN_BACK` → returns to admin home

### Screen B3 — Active Symbols (admin panel variant)

```
Message text:
Active Symbols (<N>)
Tap to toggle (will remove/add).

Inline keyboard (one symbol per row, up to 12):
[✅ EURUSD]
[✅ GBPUSD]
[✅ USDJPY]
...
[⬅️ Back]
```

- Only active symbols shown (not all symbols)
- Each shown as `✅ {SYMBOL}` → `SYM_TOGGLE:{SYMBOL}` (toggle removes it)
- Max 12 symbols displayed
- No "All" / "None" / "Refresh" controls
- State file: `symbols.json`

### Screen B4 — Status

```
Message text:
📡 System Status
Mode: FOCUS_MODE | WIDE_SCAN
Buffer: {SMALL|MEDIUM|LARGE}
Active symbols: <N>
Focus/watchlist: {list | —}

Tiers:
- FREE: {active|inactive} ({count} today)
- BASIC: {active|inactive} ({count} today)
- PRO: {active|inactive} ({count} today)
- ELITE: {active|inactive} ({count} today)
```

- Reply markup: admin home panel buttons returned alongside status (persistent button row)
- Access: `ADMIN_STATUS` callback or inline from admin home

### Screen B5 — Research Panel

```
Message text:
📊 Research panel: (coming next) — analytics_engine.py
```

- Placeholder text only; no navigation buttons beyond admin home panel
- Access: `ADMIN_RESEARCH` callback

### Screen B6 — Docs Viewer (directory listing)

```
Message text:
📚 Docs Viewer
Select a document:

Inline keyboard (one file per row, up to 20):
[README.md          ]
[CANONICAL_SPEC.md  ]
[SECURITY_MODEL.md  ]
...
[⬅️ Back]
```

- Lists `.md` files from `/opt/binarybot/docs/`
- File button triggers `send_document` (Telegram file attachment), not inline text display
- Access: `ADMIN_DOCS` callback

### Screen B7 — Document sent (action result)

Bot sends the markdown file as a Telegram document attachment.
No separate text screen rendered; bot calls `sendDocument` API.

### Screen B8 — Back navigation (universal)

`ADMIN_BACK` callback always renders admin home panel (Screen B1) with role-filtered buttons for the current user.

---

## ERA C — Legacy signal voting buttons (both eras, still active)

These appear on signal distribution messages in subscriber channels, not the admin panel.

| Button label | callback_data | Status |
|---|---|---|
| `✅ WIN` | `VOTE_\|<signal_id>\|WIN` | Active (BATCH-04 canonical) |
| `❌ LOSS` | `VOTE_\|<signal_id>\|LOSS` | Active |
| `—` | `VOTE_\|<signal_id>\|NEUTRAL` | Active |
| Various | `OUTCOME:<outcome>:<signal_id>` | Active (legacy format, delegated) |

---

## Summary: legacy screens vs current screens

| Legacy screen | Exists at HEAD? | Canonical replacement |
|---|---|---|
| A1: FOREX Symbol Selector (checkbox grid) | ❌ Not present | `/symbols list` (text only) |
| A2: CRYPTO Symbol Selector (checkbox grid) | ❌ Not present | `/symbols list` (text only) |
| A3: Buffer Mode Selector (3 buttons) | ❌ Not present | `/thresholds` slash (no button) |
| A4: /open confirmation | ❌ Not present | No equivalent |
| B1: Admin Panel Home (role-filtered) | ✅ Present (restructured) | `ADMIN_NAV:HOME` → admin_home_markup |
| B2: Buffer Mode Selector (admin panel) | ❌ Not present | No direct equivalent |
| B3: Active Symbols (toggle list) | ❌ Not present | `/symbols list` (text only) |
| B4: Status | ✅ Present (restructured) | `ADMIN_NAV:STATUS` → status_markup |
| B5: Research Panel | ❌ Not present | No equivalent (analytics via /report, /debug) |
| B6: Docs Viewer | ❌ Not present | No equivalent button |
| B7: Document sent | ❌ Not present | No equivalent |
| B8: Back navigation | ✅ Present | `ADMIN_NAV:HOME` |
