# IMPLEMENTATION_PLAN.md

BinaryBot — Implementation Plan  
Audit: telegram-application-reconstruction-01

---

## 1. SCOPE

This plan implements the canonical Telegram application experience as reconstructed from canonical documentation in:
- CANONICAL_ANALYSIS.md
- ROLE_MAPPING.md
- UX_RECONSTRUCTION.md
- NAVIGATION_RECONSTRUCTION.md
- APPLICATION_STATE_MODEL.md

---

## 2. FILES TO MODIFY

| File | Change Type | Reason |
|---|---|---|
| send/core/telegram_admin_ui.py | Refactor + extend | Replace flat admin home with canonical tree; add panel markups |
| send/core/admin_views.py | Extend | Add view renderers for new canonical panels |
| send/core/bot_service.py | Extend | Add canonical callback handlers; pass role to admin home markup |
| tests/telegram_admin_ui_restoration/test_admin_ui_restoration.py | Update | Update tests to reflect canonical navigation structure |

---

## 3. CHANGES TO telegram_admin_ui.py

### 3.1 Refactor admin_home_markup
- Add `role: str = ""` optional parameter (backward compatible)
- Role-scoped panel set: only show panels allowed by role
- Render 2-column layout of canonical panel buttons
- Keep `include_roles_reload` for compatibility

### 3.2 Add panel markup functions
New markup functions for each canonical panel:
- `operations_markup()` — Operations panel navigation
- `decision_visibility_markup()` — Decision Visibility panel navigation
- `distribution_markup()` — Distribution Control panel navigation
- `research_markup(*, has_file: bool, filename: str)` — Research & Analytics navigation
- `intelligence_markup()` — Intelligence panel navigation
- `roles_identity_markup(*, can_reload: bool)` — Roles & Identity navigation
- `system_health_markup()` — System Health panel navigation
- `governance_docs_markup(filenames: List[str])` — Governance & Docs navigation
- `security_audit_markup()` — Security & Audit panel navigation

---

## 4. CHANGES TO admin_views.py

### 4.1 Add render_distribution_panel
- Shows distribution configuration state
- Reads environment variables for channel/route info
- Read-only; no mutation

### 4.2 Add render_intelligence_panel
- Shows intelligence summary derived from recent decision events
- Reads engine events for pattern indicators
- Read-only; no mutation

### 4.3 Add render_system_health_summary
- Aggregates status snapshot + recent errors
- Read-only view derived from existing status data

### 4.4 Add render_security_audit_panel
- Shows audit trail summary
- Read-only; links to full audit file download

---

## 5. CHANGES TO bot_service.py

### 5.1 Pass role to admin_home_markup
- In `_admin_reply_markup`: compute `get_primary_role(user_id)` and pass as `role=...`
- In `_handle_admin_navigation_action` for HOME action: same

### 5.2 Add canonical callback handlers
New action handlers in `_handle_admin_navigation_action`:
- `OPERATIONS` → render_operations (engine handler + operations markup)
- `OPS_ENGINE` → existing engine panel
- `OPS_DIAGNOSE` → existing diagnose handler
- `SYMBOLS_COV` → existing symbols toggle (canonical action for Symbols & Coverage)
- `DECISION_VIS` → existing debug handler + decision_visibility_markup
- `DISTRIBUTION` → new render_distribution_panel + distribution_markup
- `RESEARCH` → existing report handler + research_markup
- `INTELLIGENCE` → new render_intelligence_panel + intelligence_markup
- `SYSHEALTH` → new render_system_health_summary + system_health_markup
- `SH_ENGINE` → existing engine panel
- `SH_DIAGNOSE` → existing diagnose handler
- `SH_AUDIT` → existing audit handler
- `GOVDOCS` → existing docs handler + governance_docs_markup
- `SECAUDIT` → new render_security_audit_panel + security_audit_markup
- `SECAUDIT_AUDIT` → existing audit handler

### 5.3 Update command_for_action mapping
Add `SYMBOLS_COV` → `/symbols list` mapping.

---

## 6. IMPLEMENTATION DECISIONS NOT EXPLICITLY DEFINED BY CANONICAL DOCUMENTS

| Decision | Canonical Gap | Justification |
|---|---|---|
| Back navigation always returns to Admin Home | Canonical does not specify sub-panel return targets | Admin Home (canonical tree root) is the logical home for all back navigation; prevents ambiguous state |
| Manual refresh buttons on read panels | Canonical does not specify auto-refresh | Manual refresh avoids unnecessary Telegram API calls; consistent with Telegram bot interaction patterns |
| 2-column layout for admin home buttons | Canonical does not specify exact column count | 2 columns is the existing pattern in the codebase and fits canonical labels |
| `render_distribution_panel` reads env vars | Canonical does not specify distribution view data source | Environment variables (ADMIN_CONTROL_CHAT_ID, etc.) are the available configuration data; no distribution mutation endpoint exists currently |
| `render_intelligence_panel` reads engine events | Canonical does not specify intelligence data source | Engine events (engine_events.jsonl) contain the available decision data from which intelligence indicators can be derived |
| `render_system_health_summary` aggregates status + errors | Canonical describes health summary content at high level | Status snapshot + last engine events provides the available health data |
| `render_security_audit_panel` links to audit download | Canonical calls for admin action log, access denials, role change audit | The existing audit file (admin_events.jsonl / binarybot_audit.json) is the canonical audit artifact; download links are the appropriate Telegram delivery mechanism |
| STRATEGY_ADMIN functional label | Canonical uses "Functional Admin (Operations)" but code already has STRATEGY_ADMIN | STRATEGY_ADMIN in code maps to the "Operations" functional admin track; no rename to avoid breaking changes |
| role="" default shows all panels | Canonical does not specify default behavior when role is absent | Fail-safe: unknown role shows all panels; this ensures backward compatibility when role is not passed |

---

## 7. EXPLICITLY NOT IMPLEMENTED (OUT OF SCOPE)

The following canonical concepts are defined but not yet implemented in the codebase, and remain out of scope for this reconstruction (they require deeper backend work):

| Concept | Canonical Source | Gap Documentation |
|---|---|---|
| Approval queues for governance-bound changes | CONTROL_PANEL_HIERARCHY_AND_INTELLIGENCE_SPEC §6 | No approval workflow backend exists; marked as missing |
| Role mutation controls in Roles & Identity panel | ADMIN_TREE_MAP §6.9 | Role mutation is admin-managed via config file, not via bot; no in-bot role assignment UI |
| Distribution route mutation controls | ADMIN_CONTROL_SPEC §9 | No distribution mutation handler exists; panel is read-only |
| Intelligence recommendations approval | ADMIN_CONTROL_SPEC §11 | No recommendation workflow backend exists |
| Commission/payout processing | AFFILIATE_SIGNAL_DISTRIBUTION_MODEL | No commission processing backend exists |
| Drift / anomaly auto-detection | CONTROL_PANEL_HIERARCHY §11.4 | No dedicated drift detection backend exists; intelligence panel shows available event data |
