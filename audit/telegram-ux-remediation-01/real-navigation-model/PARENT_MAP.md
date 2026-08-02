# Parent Map — Issue #38

**Scope:** Static canonical parent map for ADMIN_NAV: pages  
**Date:** 2026-08-02  
**Issue:** #38 — Implement real Back, Home, and Refresh navigation

---

## Canonical Admin Parent Map

Source: `CANONICAL_ADMIN_PARENT_MAP` in `send/core/telegram_admin_ui.py`  
Reference: `ADMIN_TREE_MAP_v2.0.0.md §6`

| Page | Action | Canonical Parent | Notes |
|------|--------|-----------------|-------|
| Status | STATUS | HOME | Direct child of admin home |
| Engine | ENGINE | HOME | Direct child of admin home |
| Operations | OPERATIONS | HOME | Direct panel child |
| Symbols & Coverage | SYMBOLS_COV | HOME | Direct panel child |
| Decision Visibility | DECISION_VIS | HOME | Direct panel child |
| Distribution | DISTRIBUTION | HOME | Direct panel child |
| Research & Analytics | RESEARCH | HOME | Direct panel child |
| Intelligence | INTELLIGENCE | HOME | Direct panel child |
| Affiliate | AFFILIATE | HOME | Direct panel child |
| Roles & Identity | ROLES | HOME | Direct panel child |
| System Health | SYSHEALTH | HOME | Direct panel child |
| Governance & Docs | GOVDOCS | HOME | Direct panel child |
| Security & Audit | SECAUDIT | HOME | Direct panel child |
| File Browser | FILES_HOME | HOME | Direct child of admin home |
| Strategy | STRATEGY | OPERATIONS | Child of Operations |
| Symbols (toggle) | SYMBOLS | STRATEGY | Child of Strategy |
| Profile Select | PROFILE_HOME | STRATEGY | Child of Strategy |
| Thresholds | THRESHOLDS | STRATEGY | Child of Strategy |
| S/R | SR | STRATEGY | Child of Strategy |
| Spike Filter | SPIKE | STRATEGY | Child of Strategy |
| Engine (Operations) | OPS_ENGINE | OPERATIONS | Context-specific via parent_action |
| Diagnose (Operations) | OPS_DIAGNOSE | OPERATIONS | Context-specific via parent_action |
| Engine (System Health) | SH_ENGINE | SYSHEALTH | Context-specific via parent_action |
| Diagnose (System Health) | SH_DIAGNOSE | SYSHEALTH | Context-specific via parent_action |
| Audit (System Health) | SH_AUDIT | SYSHEALTH | Child of System Health |
| Audit (Security) | SECAUDIT_AUDIT | SECAUDIT | Child of Security & Audit |
| Diagnose (general) | DIAGNOSE | HOME | General diagnose fallback |
| Audit (general) | AUDIT | HOME | General audit fallback |
| Reload Roles Confirm | RELOAD_ROLES_CONFIRM | ROLES | Confirm child of Roles |

---

## Context-Sensitive Parent Resolution

Some pages are reachable from multiple parents. The correct parent is encoded in the
markup at render time via the `parent_action` parameter.

| Triggering Action | Markup Function | parent_action | Back Target |
|-------------------|-----------------|---------------|-------------|
| SYMBOLS_COV | symbols_toggle_markup | HOME | Admin Home |
| SYMBOLS | symbols_toggle_markup | STRATEGY | Strategy |
| OPS_ENGINE | engine_markup | OPERATIONS | Operations |
| SH_ENGINE | engine_markup | SYSHEALTH | System Health |
| ENGINE (general) | engine_markup | HOME | Admin Home |
| OPS_ENGINE refresh | engine_markup | OPERATIONS | Operations |
| SH_ENGINE refresh | engine_markup | SYSHEALTH | System Health |
| OPS_DIAGNOSE | diagnose_markup | OPERATIONS | Operations |
| SH_DIAGNOSE | diagnose_markup | SYSHEALTH | System Health |
| DIAGNOSE (general) | diagnose_markup | HOME | Admin Home |
| OPS_DIAGNOSE refresh | diagnose_markup | OPERATIONS | Operations |
| SH_DIAGNOSE refresh | diagnose_markup | SYSHEALTH | System Health |

---

## Tree Diagram

```
Admin Home (ADMIN_NAV:HOME)
├── APP:HOME [🏠 Home button → welcome page]
├── Operations
│   ├── Strategy
│   │   ├── Symbols (toggle)
│   │   ├── Profile Select
│   │   │   └── Profile Confirm → apply/cancel
│   │   ├── Thresholds
│   │   ├── S/R
│   │   └── Spike Filter
│   ├── Engine (ops) [← Operations]
│   └── Diagnose (ops) [← Operations]
├── Symbols & Coverage [toggle, ← Admin Home]
├── Decision Visibility
├── Distribution
├── Research & Analytics
├── Intelligence
├── Affiliate
├── Roles & Identity
│   └── Reload Roles Confirm
├── System Health
│   ├── Engine (syshealth) [← System Health]
│   ├── Diagnose (syshealth) [← System Health]
│   └── Audit (syshealth) [← System Health]
├── Governance & Docs
├── Security & Audit
│   ├── Audit (secaudit) [← Security & Audit]
│   └── File Browser
│       └── File List [← File Browser]
├── File Browser (direct)
│   └── File List
├── Status
└── Engine (general) [← Admin Home]
```

---

## Gap Analysis (Pre-Fix)

| Page | Pre-Fix Back | Post-Fix Back |
|------|-------------|--------------|
| Strategy | HOME (wrong) | OPERATIONS (correct) |
| Symbols toggle (via SYMBOLS) | HOME (wrong) | STRATEGY (correct) |
| Engine via OPS_ENGINE | HOME (wrong) | OPERATIONS (correct) |
| Engine via SH_ENGINE | HOME (wrong) | SYSHEALTH (correct) |
| Diagnose via OPS_DIAGNOSE | HOME (wrong) | OPERATIONS (correct) |
| Diagnose via SH_DIAGNOSE | HOME (wrong) | SYSHEALTH (correct) |
| All other pages | HOME (correct) | HOME (correct) |
