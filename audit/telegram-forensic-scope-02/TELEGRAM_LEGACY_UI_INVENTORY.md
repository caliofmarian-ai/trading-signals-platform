# TELEGRAM_LEGACY_UI_INVENTORY

## Audit metadata
- HEAD at audit time: `9912c14` (branch `copilot/telegram-capability-recovery-audit`)
- Evidence sources: `send/legacy/bot_control.py` (git: `0fb9112`), `send/_archive/backups/bot_service.py.bak_step16` through `bak_step26`, full git history after `git fetch --unshallow`.
- No code modifications were made during this audit.

---

## Surface 1 — Legacy Symbol Runner (`send/legacy/bot_control.py`, commit `0fb9112`)

This file was the Hetzner-era operator control plane for symbol and buffer management.
It was later deleted in BATCH-09 (commit `63834b3`). The full file is preserved in git history.

### Entry points (slash commands)

| Command | Purpose | Auth gate |
|---|---|---|
| `/start` | Sends both FOREX and CRYPTO selector panels simultaneously | None (any chat) |
| `/forex` | Sends the FOREX symbol selector panel | None |
| `/crypto` | Sends the CRYPTO symbol selector panel | None |
| `/buffer` | Shows the buffer-mode selector (MIC / MEDIU / MARE) | None |
| `/open <SYMBOL>` | Marks a symbol as "open" in focus_state.json (live trade confirmation) | None |

No chat-context gate existed on any of these commands. No role check. No password prompt.

### Screen: FOREX Symbol Selector

```
📊 FOREX — Symbol Selector
Bifezi/debifezi simbolurile pe care vrei să le scanez.

Active acum: <count>

[✅/⬜ SYM1] [✅/⬜ SYM2] [✅/⬜ SYM3]
[✅/⬜ SYM4] [✅/⬜ SYM5] [✅/⬜ SYM6]
...
[✅ All] [✅ None] [🔄 Refresh]
```

- Symbols loaded from `/opt/binarybot/symbols.json` (static list).
- Active state loaded from `/opt/binarybot/active_symbols.json`.
- Rendered 3 buttons per row.
- Language: Romanian (`Bifezi/debifezi simbolurile pe care vrei să le scanez.`).
- All/None toggle compares against full symbol list.

### Screen: CRYPTO Symbol Selector

```
🪙 CRYPTO — Symbol Selector
Bifezi/debifezi simbolurile pe care vrei să le scanez.

Active acum: <count>

[✅/⬜ BTC/USD] [✅/⬜ ETH/USD] ...
[✅ All] [✅ None] [🔄 Refresh]
```

Identical layout to FOREX; different category key.

### Screen: Buffer Mode Selector (Romanian labels)

```
Alege Buffer (Mic / Mediu / Mare):
[✅ MIC  ] [☐ MEDIU] [☐ MARE ]
```

- Labels padded with NBSP so widths align.
- Current mode shown with `✅`; others with `☐`.
- Persisted to `/opt/binarybot/settings.json` (`buffer_mode` key, lowercase: `small/medium/large`).

### Screen: /open confirmation

No inline keyboard. Plain text reply:
```
✅ Confirmed OPEN for {SYMBOL}. Scanner revine la scanare generală când focus se eliberează.
```
(Romanian text: "Scanner returns to general scanning when focus is released.")

---

## Surface 2 — Legacy Admin Panel (`send/_archive/backups/bot_service.py.bak_step16`, commit `0fb9112`)

This was the imported Hetzner snapshot of `bot_service.py`. It contained an inline-keyboard admin panel
exposed via the `/admin` slash command within the legacy dispatcher path.

### Entry point

| Slash command | Dispatcher | Auth gate |
|---|---|---|
| `/admin` | `handle_admin_command(chat_id, user_id)` | `in_admin_context(chat_id)` → role check via `get_role(user_id)` |
| All other admin slashes (`/strategy`, etc.) | `handle_admin_command_v2(text, user_id)` (canonical) | No slash chat gate at this stage |

`in_admin_context` at this revision was **fail-open**: if `ADMIN_CONTROL_CHAT_ID` is `0` (unset), access was **allowed**.

Role check: `get_role(user_id)` looked up `config/rbac.json` → `users: {"<id>": "OWNER/ADMIN/..."}`.
Fallback: `ADMIN_USER_ID` env var treated that user as OWNER.

### Screen: Admin Panel Home

```
🔐 Admin Panel
Role: {role}
```

Buttons rendered by role:

| Button label | callback_data | Visible to roles |
|---|---|---|
| 🧱 Set Buffer | `ADMIN_SET_BUFFER` | OWNER, ADMIN |
| 🧩 Set Symbols | `ADMIN_SET_SYMBOLS` | OWNER, ADMIN |
| 📡 Status | `ADMIN_STATUS` | OWNER, ADMIN, ANALYST, MODERATOR |
| 📊 Research | `ADMIN_RESEARCH` | OWNER, ADMIN, ANALYST |
| 📚 View Docs | `ADMIN_DOCS` | OWNER, ADMIN, ANALYST, MODERATOR |

No `/` Back button on the home panel (it is the root).

### Screen: Buffer Mode Selector

```
Select Buffer Mode
Current: {MEDIUM|SMALL|LARGE}

[SMALL] [MEDIUM] [LARGE]
[⬅️ Back]
```

No emoji on SMALL/MEDIUM/LARGE buttons. Plain text labels.
Persisted to `settings.json` under key `buffer_mode`.

### Screen: Active Symbols

```
Active Symbols (<count>)
Tap to toggle (will remove/add).

[✅ EURUSD]
[✅ GBPUSD]
...
[⬅️ Back]
```

- Shows first 12 active symbols.
- Each symbol shown as `✅ {sym}` → `SYM_TOGGLE:{sym}` callback.
- Toggling removes or adds the symbol.
- State persisted to `symbols.json`.

### Screen: Status

```
📡 System Status
Mode: FOCUS_MODE | WIDE_SCAN
Buffer: {mode}
Active symbols: {count}
Focus/watchlist: {list | —}

Tiers:
- FREE: {state} ({count} today)
- BASIC: {state} ({count} today)
- PRO: {state} ({count} today)
- ELITE: {state} ({count} today)
```

Reply markup: admin home panel is returned as `reply_markup` (persistent buttons under status text).

### Screen: Research Panel

```
📊 Research panel: (coming next) — analytics_engine.py
```

Placeholder only. No buttons beyond admin home panel returned as reply markup.

### Screen: Docs Viewer (directory listing)

```
📚 Docs Viewer
Select a document:

[README.md]
[CANONICAL_SPEC.md]
...
[⬅️ Back]
```

- Lists up to 20 `.md` files from `/opt/binarybot/docs/`.
- Clicking a doc triggers `send_document` (Telegram file send), not inline display.

### Screen: Doc sent (action result)

Bot sends the actual markdown file as a Telegram document attachment.
No text screen; action returns `{"send_document": {...}}`.

### Back navigation

`ADMIN_BACK` callback always renders admin home panel:
```
🔐 Admin Panel
[role-filtered buttons as above]
```

---

## Surface 3 — Legacy Signal-vote buttons (historical, both eras)

These appear on signal distribution messages (public channels), not the admin panel.

| callback_data format | Purpose | Still active? |
|---|---|---|
| `VOTE_\|<signal_id>\|<outcome>` | Canonical BATCH-04 vote | **Yes** (current) |
| `OUTCOME:<outcome>:<signal_id>` | Older format | Handled via delegation (current) |
| `VOTE_<...>` generic | Broad vote prefix | **Yes** (current) |

---

## Summary: what was real vs what was not

| Claim | Evidence finding |
|---|---|
| Admin password prompt existed | **False** — no code, no env var, no hash, no session found in any commit or backup |
| Admin sessions existed | **False** — no session token, TTL, or session state machine in any file |
| Owner private chat worked natively | **True** — pre-`49aaeb4`, slash dispatch had no chat gate |
| Romanian-language UI existed | **True** — `bot_control.py` has full Romanian UI text |
| Symbol selector existed | **True** — checkbox-style per `bot_control.py` |
| Docs viewer existed | **True** — in `bot_service.py.bak_step16` |
| Buffer SMALL/MEDIUM/LARGE UI existed | **True** — in both surfaces with different labels |
