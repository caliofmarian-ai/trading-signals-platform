# NAVIGATION_RECONSTRUCTION.md

BinaryBot — Navigation Model Reconstruction  
Audit: telegram-application-reconstruction-01

---

## 1. CANONICAL NAVIGATION PRINCIPLES

Source: TELEGRAM_UX_v2.0.0.md §18; ADMIN_TREE_MAP_v2.0.0.md §2

From canonical documents:
- Navigation must behave like an application
- Avoid creating unnecessary Telegram messages
- Maintain application state and navigation state
- Maintain page hierarchy
- Allow intuitive movement between pages according to canonical design
- Buttons are the primary interaction model
- Commands are optional shortcuts only

---

## 2. NAVIGATION TREE

### 2.1 Root
```
/admin → Admin Home (canonical tree root)
```

### 2.2 Full Navigation Graph

```
Admin Home
├── ⚙️ Operations
│   ├── 🤖 Engine State         [OPS_ENGINE → engine handler]
│   ├── 🩺 Diagnose             [OPS_DIAGNOSE → diagnose handler]
│   └── ⬅️ Admin               [HOME]
│
├── 💱 Symbols & Coverage
│   ├── [symbol toggles]        [SYM_TOGGLE:<sym>]
│   ├── ✅ All                  [SYMBOLS_ALL]
│   ├── ⬜ None                 [SYMBOLS_NONE]
│   ├── 🔄 Refresh              [SYMBOLS_COV]
│   └── ⬅️ Admin               [HOME]
│
├── 🔍 Decision Visibility
│   ├── 🔄 Refresh              [DECISION_VIS]
│   └── ⬅️ Admin               [HOME]
│
├── 📡 Distribution Control
│   ├── 🔄 Refresh              [DISTRIBUTION]
│   └── ⬅️ Admin               [HOME]
│
├── 📊 Research & Analytics
│   ├── 📥 Download Report      [FILE_DL:rpt:<filename>] (when available)
│   ├── 🔄 Refresh              [RESEARCH]
│   └── ⬅️ Admin               [HOME]
│
├── 🧠 Intelligence
│   ├── 🔄 Refresh              [INTELLIGENCE]
│   └── ⬅️ Admin               [HOME]
│
├── 🤝 Affiliate / Partner
│   └── ⬅️ Admin               [HOME]
│
├── 👥 Roles & Identity
│   ├── 🔄 Reload Roles         [RELOAD_ROLES_CONFIRM] (Owner/Primary Admin only)
│   └── ⬅️ Admin               [HOME]
│
├── 🩺 System Health
│   ├── 🤖 Engine State         [SH_ENGINE → engine handler]
│   ├── 🩺 Diagnose             [SH_DIAGNOSE → diagnose handler]
│   ├── 🔍 Runtime Audit        [SH_AUDIT → audit handler]
│   └── ⬅️ Admin               [HOME]
│
├── 📖 Governance & Docs
│   ├── [canonical doc list]    [FILE_DL:doc:<filename>]
│   └── ⬅️ Admin               [HOME]
│
└── 🔒 Security & Audit
    ├── 🔍 Runtime Audit        [SECAUDIT_AUDIT → audit handler]
    ├── 📁 File Browser         [FILES_HOME]
    └── ⬅️ Admin               [HOME]
```

---

## 3. CALLBACK ACTION REGISTRY

All callbacks use the `ADMIN_NAV:` prefix (CALLBACK_PREFIX constant).

| Action String | Panel | Handler |
|---|---|---|
| `HOME` | Admin Home | _render_panel_for_command("/admin") |
| `OPERATIONS` | Operations | render_operations_panel() + operations_markup() |
| `OPS_ENGINE` | Operations → Engine State | _render_panel_for_command("/engine") |
| `OPS_DIAGNOSE` | Operations → Diagnose | handle_diagnose() |
| `SYMBOLS_COV` | Symbols & Coverage | symbols_toggle_markup() + /symbols list |
| `SYM_TOGGLE:<sym>` | Symbols & Coverage | handle_symbols_toggle(sym) |
| `SYMBOLS_ALL` | Symbols & Coverage | handle_symbols_all() |
| `SYMBOLS_NONE` | Symbols & Coverage | handle_symbols_none() |
| `DECISION_VIS` | Decision Visibility | handle_admin_command("/debug") + decision_visibility_markup() |
| `DISTRIBUTION` | Distribution Control | render_distribution_panel() + distribution_markup() |
| `RESEARCH` | Research & Analytics | handle_admin_command("/report") + research_markup() |
| `INTELLIGENCE` | Intelligence | render_intelligence_panel() + intelligence_markup() |
| `AFFILIATE` | Affiliate / Partner | handle_admin_command("/affiliate") |
| `ROLES` | Roles & Identity | handle_admin_command("/roles") + roles_identity_markup() |
| `SYSHEALTH` | System Health | render_system_health_summary() + system_health_markup() |
| `SH_ENGINE` | System Health → Engine | _render_panel_for_command("/engine") |
| `SH_DIAGNOSE` | System Health → Diagnose | handle_diagnose() |
| `SH_AUDIT` | System Health → Audit | handle_audit_runtime() |
| `GOVDOCS` | Governance & Docs | handle_docs_list() + governance_docs_markup() |
| `SECAUDIT` | Security & Audit | render_security_audit_panel() + security_audit_markup() |
| `SECAUDIT_AUDIT` | Security & Audit → Audit | handle_audit_runtime() |
| `RELOAD_ROLES_CONFIRM` | Roles → Confirm Reload | reload_confirm_markup() |
| `RELOAD_ROLES_EXEC` | Roles → Execute Reload | reload_roles_config() |
| `FILE_DL:<dir>:<name>` | File Download | handle_file_download_path() |
| `FILES_HOME` | File Browser | files_home_markup() |
| `FILES:<dir>:<page>` | File Browser Paginated | handle_files_list() |
| `STATUS` | Status | render_status_text() (legacy shortcut) |
| `ENGINE` | Engine | /engine (legacy shortcut) |
| `DEBUG` | Debug | /debug (legacy shortcut) |
| `REPORT` | Report | /report (legacy shortcut) |
| `PROFILE_HOME` | Strategy Profile | strategy_quick_markup() |
| `PROFILE_CONFIRM:<p>` | Strategy Profile Confirm | strategy_profile_confirm_markup() |
| `PROFILE_EXEC:<p>` | Strategy Profile Execute | handle_strategy_profile() |
| `DOCS` | Docs | handle_docs_list() |
| `DIAGNOSE` | Diagnose | handle_diagnose() |
| `AUDIT` | Runtime Audit | handle_audit_runtime() |
| `LOG` | Log Export | handle_log_export() |

---

## 4. APPLICATION STATE MODEL

State is maintained via Telegram's inline keyboard attached to the bot message. Navigation happens through callback queries that update the message content and keyboard in place.

The canonical pattern: **edit existing message + keyboard** rather than sending new messages. This avoids unnecessary message creation.

Implementation note: The existing `handle_callback` dispatcher uses `edit_message` when a `message_id` is available, falling back to `send_message` when not. This is the correct Telegram application pattern.

---

## 5. NAVIGATION DESIGN PRINCIPLES

| Principle | Source | Implementation |
|---|---|---|
| Role-scoped navigation | ADMIN_TREE_MAP_v2.0.0.md §2.1 | admin_home_markup(role=...) renders only allowed panels |
| Domain separation | ADMIN_TREE_MAP_v2.0.0.md §2.2 | Each domain has its own panel and callback namespace |
| Visibility vs. control separation | ADMIN_TREE_MAP_v2.0.0.md §2.3 | Read-only panels don't include mutating buttons |
| Future-facing mutation only | ADMIN_TREE_MAP_v2.0.0.md §2.4 | All mutation callbacks route to existing governed handlers |
| Audit-first control actions | ADMIN_TREE_MAP_v2.0.0.md §2.5 | All mutations use existing _audit() function |
| No legacy flat menu | ADMIN_TREE_MAP_v2.0.0.md §8.1 | admin_home_markup replaced with canonical tree |
| No affiliate leakage | ADMIN_TREE_MAP_v2.0.0.md §8.4 | AFFILIATE_ADMIN sees only Affiliate panel |

---

## 6. BACKWARD COMPATIBILITY

Slash commands remain available as shortcuts:
- `/admin` → navigates to Admin Home (canonical tree)
- `/strategy` → Strategy-related content (reachable via Operations or Symbols panel)
- `/thresholds`, `/sr`, `/spike` → Strategy parameter content (reachable via Operations)
- `/symbols` → Symbols & Coverage panel
- `/engine` → Engine State content (reachable via Operations or System Health)
- `/debug` → Decision Visibility panel content
- `/report` → Research & Analytics panel content
- `/files` → File Browser (reachable via Security & Audit panel)
- `/docs` → Governance & Docs panel content
- `/diagnose` → Diagnose content (reachable via Operations or System Health)
- `/audit_runtime` → Runtime Audit (reachable via Security & Audit panel)
- `/roles` → Roles & Identity panel content
- `/affiliate` → Affiliate / Partner panel content
