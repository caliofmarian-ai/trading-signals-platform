# OPERATOR ACCEPTANCE TEST

## Prerequisites

Before running these tests, ensure:
- Railway deployment is live and healthy.
- `OWNER_TELEGRAM_ID` is set to your personal Telegram numeric user ID.
- `ADMIN_CONTROL_CHAT_ID` is set to your admin group.
- `BINARYBOT_BASE_DIR` points to a writeable directory with `observability/`, `docs/`, etc.

---

## 1. Owner Private DM Access

Open a private conversation with the bot (not in the admin group).

| Step | Action | Expected |
|---|---|---|
| 1.1 | Send `/admin` | Bot replies with admin home panel (inline buttons) |
| 1.2 | Tap 📊 Status | Bot replies with status text |
| 1.3 | Tap ⚙️ Strategy | Bot replies with strategy text |
| 1.4 | Tap 💱 Symbols | Bot shows symbol toggle grid |
| 1.5 | Tap 🩺 Diagnose | Bot replies with operational diagnostics |
| 1.6 | Tap 🔍 Runtime Audit | Bot sends a `.txt` document with sanitized audit |
| 1.7 | Tap ⬅️ Admin (back) | Bot shows admin home panel again |
| 1.8 | Send `/status` | Bot replies with status |
| 1.9 | Send `/symbols` | Bot shows symbol toggle grid |
| 1.10 | Send `/files` | Bot shows file browser home or files list |
| 1.11 | Send `/log` | Bot sends a `.log` document |
| 1.12 | Send `/diagnose` | Bot replies with diagnostics |
| 1.13 | Send `/audit_runtime` | Bot sends a `.txt` document |
| 1.14 | Send `/help` | Help text lists all new commands |

---

## 2. Unauthorized Private DM Denial

Ask a team member (non-owner) to send `/admin` to the bot in private DM.

| Step | Action | Expected |
|---|---|---|
| 2.1 | Non-owner sends `/admin` | Bot returns "unauthorized" or no reply |

---

## 3. Symbol Management

From the admin home (private DM or admin group):

| Step | Action | Expected |
|---|---|---|
| 3.1 | Tap 💱 Symbols | Shows symbol grid with ✅/⬜ state |
| 3.2 | Tap any ✅ active symbol | Symbol becomes ⬜ (disabled), grid refreshes |
| 3.3 | Tap any ⬜ inactive symbol | Symbol becomes ✅ (enabled), grid refreshes |
| 3.4 | Tap ⬜ None | All symbols disabled, grid shows all ⬜ |
| 3.5 | Tap ✅ All | All symbols enabled, grid shows all ✅ |
| 3.6 | Tap 🔄 Refresh | Grid refreshes with current state |
| 3.7 | Check admin events | Each toggle generates an Admin Proof entry |

---

## 4. Strategy Profile

From the admin home:

| Step | Action | Expected |
|---|---|---|
| 4.1 | Tap ⚙️ Strategy | Shows strategy panel |
| 4.2 | Tap 🎯 Thresholds → show profile selector | Profile selector with MIC/SMALL, MEDIU/MEDIUM, MARE/LARGE |
| 4.3 | Tap MEDIU / MEDIUM | Confirmation screen shows parameter values |
| 4.4 | Tap ❌ Cancel | Returns to profile selector, no change |
| 4.5 | Tap MARE / LARGE | Confirmation screen appears |
| 4.6 | Tap ✅ Apply | Profile applied, success message shown |
| 4.7 | Check algo_params.json | PRE=50, CONFIRM=60, OPEN=65, SR=1.2 |
| 4.8 | Check admin events | Admin Proof generated for the profile change |

---

## 5. File Browser

| Step | Action | Expected |
|---|---|---|
| 5.1 | Send `/files` | Shows directory chooser OR file list |
| 5.2 | Tap 📁 observability | Lists .jsonl files in observability dir |
| 5.3 | Tap a .jsonl file button | Bot sends the file as a document |
| 5.4 | Send `/docs` | Lists .md files in docs dir |
| 5.5 | Send `/download obs engine_events.jsonl` | Downloads that specific file |
| 5.6 | Send `/download obs ../../../etc/passwd` | Bot rejects with security error |
| 5.7 | Send `/download obs secret_token.txt` | Bot rejects with security error |

---

## 6. Diagnostics

| Step | Action | Expected |
|---|---|---|
| 6.1 | Send `/diagnose` | Multi-line diagnostics with emoji markers |
| 6.2 | Check output for tokens | TELEGRAM_BOT_TOKEN must NOT appear |
| 6.3 | Check output for secrets | No API keys or secrets visible |
| 6.4 | Send `/audit_runtime` | Bot sends `.txt` document |
| 6.5 | Open the document | Contains env matrix (presence only, no values) |
| 6.6 | Check document for secrets | TELEGRAM_BOT_TOKEN must NOT appear |

---

## 7. Rate Limiting

| Step | Action | Expected |
|---|---|---|
| 7.1 | Send `/diagnose` 6 times rapidly | 6th call returns "Rate limit exceeded" |
| 7.2 | Send `/audit_runtime` 4 times rapidly | 4th call returns "Rate limit exceeded" |
| 7.3 | Wait 60 seconds | Commands work again normally |

---

## 8. Admin Group Access

From the admin Telegram group:

| Step | Action | Expected |
|---|---|---|
| 8.1 | Send `/admin` | Bot shows admin home panel |
| 8.2 | Tap 🔄 Reload Roles | Confirmation prompt shown |
| 8.3 | Tap ✅ Confirm | Roles reloaded successfully |

---

## 9. Help Text

| Step | Action | Expected |
|---|---|---|
| 9.1 | Send `/help` (owner private DM) | Lists /admin, /files, /docs, /log, /diagnose, /audit_runtime |
| 9.2 | Check help text | No mention of password authentication |

---

## Acceptance Criteria Checklist

- [ ] Owner can open `/admin` in private DM
- [ ] Non-owner in private DM is denied
- [ ] Visual Admin UI works (buttons, navigation, back)
- [ ] Symbol management works (toggle, all, none)
- [ ] Strategy profile works (with confirmation)
- [ ] `/files`, `/docs`, `/download` work
- [ ] `/log`, `/diagnose`, `/audit_runtime` work
- [ ] Path traversal is blocked
- [ ] Secret files are never delivered
- [ ] Admin Proof is generated for mutations
- [ ] `/help` lists new commands
- [ ] Rate limiting is enforced
- [ ] No second bot process is running
