# UI RESTORATION REPORT

## Admin Home Panel

The admin home markup was updated to expose all 16 canonical admin buttons:

| Row | Button 1 | Button 2 |
|---|---|---|
| 1 | 📊 Status | ⚙️ Strategy |
| 2 | 🎯 Thresholds | 📐 S/R |
| 3 | ⚡ Spike Filter | 💱 Symbols |
| 4 | 🤖 Engine | 🐞 Debug |
| 5 | 📈 Reports | 📁 Files |
| 6 | 📄 Documents | 🩺 Diagnose |
| 7 | 🔍 Runtime Audit | 👥 Roles |
| 8 | 🤝 Affiliate | |
| 9 (admin-topic only) | 🔄 Reload Roles | |

All buttons use the `ADMIN_NAV:` callback prefix and are routed through
the canonical `_handle_admin_navigation_action` dispatcher.

---

## Symbol Management

The symbol toggle UI has been restored as a visual checkbox grid.

### Markup: `symbols_toggle_markup(all_symbols, active_symbols)`

- FOREX symbols and CRYPTO symbols separated by type detection.
- 3 symbols per row.
- Active symbols: ✅ `{SYM}`.
- Inactive symbols: ⬜ `{SYM}`.
- Control row: `[✅ All]`, `[⬜ None]`, `[🔄 Refresh]`.
- Back row: `[⬅️ Admin]`.

### Canonical symbol list

**FOREX:** EURUSD, GBPUSD, USDJPY, USDCHF, AUDUSD, USDCAD, NZDUSD, EURGBP, EURJPY,
GBPJPY, EURAUD, GBPAUD

**CRYPTO:** BTCUSD, ETHUSD, XRPUSD, LTCUSD, ADAUSD

### Callback families

| Action | Callback |
|---|---|
| Toggle individual symbol | `ADMIN_NAV:SYM_TOGGLE:{SYM}` |
| Activate all | `ADMIN_NAV:SYMBOLS_ALL` |
| Deactivate all | `ADMIN_NAV:SYMBOLS_NONE` |
| Refresh list | `ADMIN_NAV:SYMBOLS` |

---

## Strategy Profile Selector (Buffer Mode Equivalent)

The three-button strategy-profile selector has been restored as a canonical UI.

### Button labels and mappings

| Button | Historical name | Canonical profile | PRE | CONFIRM | OPEN | SR |
|---|---|---|---|---|---|---|
| MIC / SMALL | `buffer_set:small` | CONSERVATIVE | 60 | 70 | 75 | 1.8 |
| MEDIU / MEDIUM | `buffer_set:medium` | BALANCED | 55 | 65 | 70 | 1.5 |
| MARE / LARGE | `buffer_set:large` | AGGRESSIVE | 50 | 60 | 65 | 1.2 |

**Note:** These mappings use the current canonical parameter model
(`score_thresholds` + `sr_required_multiplier`). The historical "buffer" concept
mapped to signal confidence strictness; CONSERVATIVE = fewer signals (stricter),
AGGRESSIVE = more signals (looser). No hidden state is created.

### Confirmation flow

Profile application requires a confirmation step:
1. User taps MIC / SMALL → confirmation screen with parameter preview.
2. User taps ✅ Apply → mutation executed, Admin Proof generated.
3. User taps ❌ Cancel → returns to profile selector.

### Callback families

| Action | Callback |
|---|---|
| Show confirmation | `ADMIN_NAV:PROFILE_CONFIRM:{PROFILE}` |
| Execute profile | `ADMIN_NAV:PROFILE_EXEC:{PROFILE}` |
| Back to profile list | `ADMIN_NAV:PROFILE_HOME` |

---

## Navigation

All panels include a back button:
- `[⬅️ Admin]` → `ADMIN_NAV:HOME` navigates to the admin home panel.
- `[⬅️ Strategy]` → `ADMIN_NAV:STRATEGY` navigates to strategy panel.
- `[⬅️ Files]` → `ADMIN_NAV:FILES_HOME` navigates to file browser home.

---

## Callback Acknowledgement and Edit-in-Place

- When a callback produces a text + markup response, `edit_message` is attempted first.
- If `edit_message` fails (e.g., message too old, already edited), a new message is sent.
- File delivery callbacks (`FILE_DL:*`, `LOG`, `AUDIT`) trigger `send_document` directly.

---

## Emojis updated

The following button emojis were updated to match the specification:

| Button | Old | New |
|---|---|---|
| Status | 📡 | 📊 |
| Engine | ⚙️ | 🤖 |
| Report | 📊 | 📈 |
| Debug | 🧪 | 🐞 |
| Symbols | 🧩 | 💱 |
| Strategy | 📈 | ⚙️ |
| SR | SR | S/R |
| Affiliate | 💼 | 🤝 |
| Reload Roles | ♻️ | 🔄 |
