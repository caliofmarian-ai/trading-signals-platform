# ROLE_MAPPING.md

BinaryBot — Canonical Role Mapping  
Audit: telegram-application-reconstruction-01

---

## 1. CANONICAL ROLE HIERARCHY

Source: ROLE_AND_PERMISSION_MATRIX_SPEC_v2.0.0.md §3–§5

```
Owner
  ↓
Primary Admin
  ↓
Functional Admin (Operations / Distribution / Monitoring / Research / Affiliate Program / Support)
  ↓
Analyst / Read-only Specialist
  ↓
Support / Moderator-style Limited Roles
  ↓
Affiliate Admin
  ↓
User
```

---

## 2. CANONICAL ROLES → CODEBASE CONSTANTS

| Canonical Role | Code Constant | admin_permissions.py |
|---|---|---|
| Owner | ROLE_OWNER = "OWNER" | ✅ Implemented |
| Primary Admin | ROLE_PRIMARY_ADMIN = "PRIMARY_ADMIN" | ✅ Implemented |
| Functional Admin (Operations/Strategy) | ROLE_STRATEGY_ADMIN = "STRATEGY_ADMIN" | ✅ Implemented (as Functional Admin / Operations track) |
| Functional Admin (Research) | ROLE_RESEARCH_ADMIN = "RESEARCH_ADMIN" | ✅ Implemented (as Functional Admin / Research track) |
| Analyst / Read-only Specialist | ROLE_ANALYST = "ANALYST" | ✅ Implemented |
| Support / Moderator-style | ROLE_MODERATOR = "MODERATOR" | ✅ Implemented |
| Affiliate Admin | ROLE_AFFILIATE_ADMIN = "AFFILIATE_ADMIN" | ✅ Implemented |
| User | ROLE_USER = "USER" | ✅ Implemented |

---

## 3. PERMISSION DOMAINS → CODEBASE PERMISSIONS

Source: ROLE_AND_PERMISSION_MATRIX_SPEC_v2.0.0.md §7

| Canonical Domain | Codebase Permission |
|---|---|
| Governance Domain | (governance-bound; OWNER only via approval) |
| Operations Domain | engine.view, engine.restart |
| Decision Visibility Domain | debug.view, strategy.view |
| Distribution Domain | channels.view, channels.test |
| Observability Domain | diagnostics.view, files.view |
| Research & Analytics Domain | reports.view |
| Intelligence Domain | (partially covered by reports.view and debug.view) |
| Affiliate Domain | affiliate.view.own, affiliate.view.any |
| Community / Support Domain | (moderator via channels.view) |
| Role & Identity Domain | roles.view, roles.write |
| Documentation Domain | files.view (canonical docs via /docs) |
| Security Domain | (OWNER-reserved governance actions) |

---

## 4. ROLE → CANONICAL PANEL VISIBILITY MAPPING

Source: ADMIN_TREE_MAP_v2.0.0.md §7; CONTROL_PANEL_HIERARCHY_AND_INTELLIGENCE_SPEC_v2.0.0.md §4–§12

| Role Constant | Visible Admin Panels |
|---|---|
| OWNER | Operations, Symbols & Coverage, Decision Visibility, Distribution, Research & Analytics, Intelligence, Affiliate / Partner, Roles & Identity, System Health, Governance & Docs, Security & Audit |
| PRIMARY_ADMIN | Operations, Symbols & Coverage, Decision Visibility, Distribution, Research & Analytics, Intelligence, Affiliate / Partner, Roles & Identity, System Health, Governance & Docs, Security & Audit |
| STRATEGY_ADMIN | Operations, Symbols & Coverage, Decision Visibility |
| RESEARCH_ADMIN | Decision Visibility, Research & Analytics, Intelligence |
| ANALYST | Decision Visibility, Research & Analytics, Intelligence |
| MODERATOR | System Health |
| AFFILIATE_ADMIN | Affiliate / Partner |
| USER | (none — no admin surface) |

---

## 5. PANEL → CANONICAL ACTION → EXISTING HANDLER MAPPING

| Canonical Panel | Callback Action | Backing Handler / Command |
|---|---|---|
| Operations | OPERATIONS | Engine: handle_admin_command("/engine"); Diagnose: handle_diagnose() |
| Symbols & Coverage | SYMBOLS_COV | handle_symbols_toggle(), handle_symbols_all/none, /symbols list |
| Decision Visibility | DECISION_VIS | handle_admin_command("/debug") — last decision event |
| Distribution Control | DISTRIBUTION | render_distribution_panel() — NEW view, no mutation handler |
| Research & Analytics | RESEARCH | handle_admin_command("/report"); _find_latest_report_json() |
| Intelligence | INTELLIGENCE | render_intelligence_panel() — NEW view; reads engine events |
| Affiliate / Partner | AFFILIATE | handle_admin_command("/affiliate") |
| Roles & Identity | ROLES | handle_admin_command("/roles"); reload_roles_config() |
| System Health | SYSHEALTH | handle_diagnose() + render_status_text(_build_status_snapshot()) |
| Governance & Docs | GOVDOCS | handle_docs_list() — canonical docs file browser |
| Security & Audit | SECAUDIT | handle_audit_runtime() + handle_files_list() |

---

## 6. AFFILIATE ADMIN ISOLATION (FROM AFFILIATE_SIGNAL_DISTRIBUTION_MODEL_v2.0.0.md)

The canonical affiliate model requires strict isolation:
- Affiliate Admin sees ONLY the Affiliate / Partner panel
- Affiliate Admin must NEVER access strategy internals, engine diagnostics, global admin data, full-system research, or unrelated user data
- Scoped to own referral network and assigned program data only

Implementation: `ROLE_AFFILIATE_ADMIN` maps only to `{"AFFILIATE"}` in the panel visibility map.

---

## 7. ROLE STORAGE MODEL

Source: ROLE_AND_PERMISSION_MATRIX_SPEC_v2.0.0.md §13

Roles are stored in `/opt/binarybot/config/admin_roles.json` (configurable via `ADMIN_ROLES_CONFIG` env var).

Format:
```json
{
  "owner": [<telegram_id>],
  "primary_admin": [<telegram_id>],
  "strategy_admin": [<telegram_id>],
  "research_admin": [],
  "analyst": [],
  "moderator": [],
  "affiliate_admin": {
    "<code>": {
      "telegram_id": <id>,
      "referral_code": "<code>"
    }
  }
}
```

This is consistent with the canonical structure defined in ROLE_AND_PERMISSION_MATRIX_SPEC_v2.0.0.md §13.
