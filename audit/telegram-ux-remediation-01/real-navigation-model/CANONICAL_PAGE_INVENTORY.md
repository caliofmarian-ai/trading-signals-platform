# Canonical Page and Callback Inventory — Issue #38

**Scope:** APP: and ADMIN_NAV: navigation surfaces  
**Date:** 2026-08-02  
**Issue:** #38 — Implement real Back, Home, and Refresh navigation  
**Parent:** #23

---

## 1. APP: Pages (telegram_app_nav.py)

| Page ID | Callback | Entry Points | Immediate Parent | Refresh Target | Role Access |
|---------|----------|--------------|-----------------|----------------|-------------|
| Welcome/Home | `APP:HOME` | `/start`, Back fallback | — (root) | `APP:HOME` | All roles |
| Status | `APP:STATUS` | Welcome page button, `/status`, Back | Home | `APP:STATUS` | All roles |
| Help | `APP:HELP` | Welcome page button, `/help`, Back | Home | `APP:HELP` | All roles |
| Admin Surface | `APP:ADMIN` | Welcome page button (OWNER), Back | Home | `APP:HOME` | OWNER (full), others (info) |
| Back | `APP:BACK` | Status/Help/Admin page Back button | — | — | Same as current page |

### APP: Action Constants
- `ACT_HOME = "HOME"` — Role-scoped welcome page
- `ACT_STATUS = "STATUS"` — System status page
- `ACT_HELP = "HELP"` — Role-scoped help page
- `ACT_ADMIN = "ADMIN"` — Admin surface bridge
- `ACT_BACK = "BACK"` — Navigate to immediate parent (Issue #38)

---

## 2. ADMIN_NAV: Pages (telegram_admin_ui.py, bot_service.py)

### Root

| Page ID | Callback | Immediate Parent | Refresh Target | Notes |
|---------|----------|-----------------|----------------|-------|
| Admin Home | `ADMIN_NAV:HOME` | — (admin root) | `ADMIN_NAV:HOME` | Entry via `/admin`, OWNER DM |

### Direct Children of Admin Home (Level 1)

| Page ID | Callback | Immediate Parent | Refresh Target |
|---------|----------|-----------------|----------------|
| Operations | `ADMIN_NAV:OPERATIONS` | HOME | `ADMIN_NAV:OPERATIONS` |
| Symbols & Coverage | `ADMIN_NAV:SYMBOLS_COV` | HOME | `ADMIN_NAV:SYMBOLS_COV` |
| Decision Visibility | `ADMIN_NAV:DECISION_VIS` | HOME | `ADMIN_NAV:DECISION_VIS` |
| Distribution | `ADMIN_NAV:DISTRIBUTION` | HOME | `ADMIN_NAV:DISTRIBUTION` |
| Research & Analytics | `ADMIN_NAV:RESEARCH` | HOME | `ADMIN_NAV:RESEARCH` |
| Intelligence | `ADMIN_NAV:INTELLIGENCE` | HOME | `ADMIN_NAV:INTELLIGENCE` |
| Affiliate | `ADMIN_NAV:AFFILIATE` | HOME | `ADMIN_NAV:AFFILIATE` |
| Roles & Identity | `ADMIN_NAV:ROLES` | HOME | `ADMIN_NAV:ROLES` |
| System Health | `ADMIN_NAV:SYSHEALTH` | HOME | `ADMIN_NAV:SYSHEALTH` |
| Governance & Docs | `ADMIN_NAV:GOVDOCS` | HOME | `ADMIN_NAV:GOVDOCS` |
| Security & Audit | `ADMIN_NAV:SECAUDIT` | HOME | `ADMIN_NAV:SECAUDIT` |
| File Browser | `ADMIN_NAV:FILES_HOME` | HOME | `ADMIN_NAV:FILES_HOME` |
| Status | `ADMIN_NAV:STATUS` | HOME | `ADMIN_NAV:STATUS` |
| Engine | `ADMIN_NAV:ENGINE` | HOME | `ADMIN_NAV:ENGINE` |

### Level 2: Operations Sub-pages

| Page ID | Callback | Immediate Parent | Refresh Target |
|---------|----------|-----------------|----------------|
| Strategy | `ADMIN_NAV:STRATEGY` | OPERATIONS | `ADMIN_NAV:STRATEGY` |
| Engine (ops) | `ADMIN_NAV:OPS_ENGINE` | OPERATIONS | `ADMIN_NAV:OPS_ENGINE` |
| Diagnose (ops) | `ADMIN_NAV:OPS_DIAGNOSE` | OPERATIONS | `ADMIN_NAV:OPS_DIAGNOSE` |

### Level 2: Strategy Sub-pages

| Page ID | Callback | Immediate Parent | Refresh Target |
|---------|----------|-----------------|----------------|
| Symbols (toggle) | `ADMIN_NAV:SYMBOLS` | STRATEGY | `ADMIN_NAV:SYMBOLS` |
| Profile Select | `ADMIN_NAV:PROFILE_HOME` | STRATEGY | `ADMIN_NAV:PROFILE_HOME` |
| Thresholds | `ADMIN_NAV:THRESHOLDS` | STRATEGY | `ADMIN_NAV:THRESHOLDS` |
| S/R | `ADMIN_NAV:SR` | STRATEGY | `ADMIN_NAV:SR` |
| Spike Filter | `ADMIN_NAV:SPIKE` | STRATEGY | `ADMIN_NAV:SPIKE` |

### Level 3: Profile Sub-pages

| Page ID | Callback | Immediate Parent | Notes |
|---------|----------|-----------------|-------|
| Profile Confirm | `ADMIN_NAV:PROFILE_CONFIRM:x` | PROFILE_HOME | Cancel → PROFILE_HOME |
| Profile Execute | `ADMIN_NAV:PROFILE_EXEC:x` | PROFILE_CONFIRM:x | After exec re-renders profile select |

### Level 2: System Health Sub-pages

| Page ID | Callback | Immediate Parent | Refresh Target |
|---------|----------|-----------------|----------------|
| Engine (syshealth) | `ADMIN_NAV:SH_ENGINE` | SYSHEALTH | `ADMIN_NAV:SH_ENGINE` |
| Diagnose (syshealth) | `ADMIN_NAV:SH_DIAGNOSE` | SYSHEALTH | `ADMIN_NAV:SH_DIAGNOSE` |
| Audit (syshealth) | `ADMIN_NAV:SH_AUDIT` | SYSHEALTH | — (file download) |

### Level 2: Security & Audit Sub-pages

| Page ID | Callback | Immediate Parent |
|---------|----------|-----------------|
| Audit (secaudit) | `ADMIN_NAV:SECAUDIT_AUDIT` | SECAUDIT |

### Level 2: File Browser Sub-pages

| Page ID | Callback | Immediate Parent | Refresh Target |
|---------|----------|-----------------|----------------|
| File List | `ADMIN_NAV:FILES:x:n` | FILES_HOME | `ADMIN_NAV:FILES:x:n` |
| File Download | `ADMIN_NAV:FILE_DL:x:name` | (parent list page) | — (file send) |

---

## 3. Pre-Issue-#38 Gaps (All Fixed)

| Gap | Affected Pages | Pre-fix Behavior | Post-fix Behavior |
|-----|---------------|-----------------|-------------------|
| No ACT_BACK constant | All APP: pages | Missing | `ACT_BACK = "BACK"` added |
| No bounded history | APP: navigation | Missing | 5-deep bounded stack per session |
| STRATEGY Back → HOME | strategy_markup | `⬅️ Admin` → HOME | `⬅️ Operations` → OPERATIONS |
| SYMBOLS toggle Back → HOME | symbols_toggle_markup | `⬅️ Admin` → HOME | Correct per parent_action |
| OPS_ENGINE Back → HOME | engine_markup | `⬅️ Admin` → HOME | `⬅️ Operations` → OPERATIONS |
| SH_ENGINE Back → HOME | engine_markup | `⬅️ Admin` → HOME | `⬅️ System Health` → SYSHEALTH |
| OPS_DIAGNOSE Back → HOME | diagnose_markup | `⬅️ Admin` → HOME | `⬅️ Operations` → OPERATIONS |
| SH_DIAGNOSE Back → HOME | diagnose_markup | `⬅️ Admin` → HOME | `⬅️ System Health` → SYSHEALTH |
| SYMBOLS Refresh wrong target | symbols_toggle_markup | `SYMBOLS` in all cases | Correct per context |
| No history cleared on /start | prepare_start_hard_reset | Missing | clear_nav_history called |
