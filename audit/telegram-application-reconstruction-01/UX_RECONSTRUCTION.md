# UX_RECONSTRUCTION.md

BinaryBot — UX Reconstruction from Canonical Documentation  
Audit: telegram-application-reconstruction-01

---

## 1. UX RECONSTRUCTION PRINCIPLE

Source: TELEGRAM_UX_v2.0.0.md §2

> "Telegram commands must map to canonical governed actions.  
> Telegram messages must reflect canonical signal truth.  
> Telegram UI structure must respect role, scope and audit rules."

This reconstruction derives UX exclusively from canonical documents. Where the canonical document is silent on a specific UX detail, the gap is explicitly documented.

---

## 2. LIVE SIGNAL UX RECONSTRUCTION

Source: TELEGRAM_UX_v2.0.0.md §5–§8

### Signal Lifecycle
```
PRE → CONFIRM → OPEN_NOW → OUTCOME_PANEL
```

Not every signal must pass every visible stage; but any visible stage must be truthful.

### PRE Message Fields (canonical minimum)
- Stage label
- Symbol
- Direction
- Timing or expiry indication
- Confidence or readiness summary if allowed
- Status wording indicating monitoring / watch-stage semantics

### CONFIRM Message Fields (canonical minimum)
- Stage label
- Symbol
- Direction
- Buffer or timing context where relevant
- Expiry indication
- Readiness strengthening wording

### OPEN_NOW Message Fields (canonical minimum)
- Stage label
- Symbol
- Direction
- Execution-relevant timing / expiry
- Confidence or readiness wording if policy allows
- Action wording suitable for destination and audience

### Assessment
The existing telegram_publisher.py correctly produces these stages. No changes required to live signal UX.

---

## 3. OUTCOME UX RECONSTRUCTION

Source: TELEGRAM_UX_v2.0.0.md §13–§14

### Canonical Requirements
- Outcome panel attached to OPEN_NOW message (preferred) or second message (fallback)
- Options: WIN, LOSE, MISSED
- Single-vote rule per user per signal
- Lock-first policy (no silent overwrites)
- Delayed activation (not before trade window closes)
- Aggregate statistics only in public-facing updates

### Assessment
The existing outcome_service.py and VOTE_ callback handling correctly implement the canonical outcome model. No changes required.

---

## 4. SYSTEM ALERT UX RECONSTRUCTION

Source: TELEGRAM_UX_v2.0.0.md §11

### Canonical Requirements
- System alerts must route to operational/system destinations, NOT live trading destinations
- Alerts must clearly identify the event
- System alerts must not visually imitate PRE/CONFIRM/OPEN_NOW messages

### Assessment
The existing observability_logger.py and alert routing are functionally correct. No changes required.

---

## 5. ADMIN UX RECONSTRUCTION

Source: TELEGRAM_UX_v2.0.0.md §15–§18; ADMIN_TREE_MAP_v2.0.0.md; ADMIN_CONTROL_SPEC_v2.0.0.md

### 5.1 Admin UX Philosophy (Canonical)
> "Buttons become the primary interaction model."  
> "Commands remain only as optional shortcuts."  
> "Admin surfaces must render according to role and scope."  
> "A user must not see all admin buttons merely because they can open /admin."

### 5.2 Admin Entry
Canonical entry: `/admin`

Expected behavior:
- Identify current role/scope context
- Show allowed top-level branches only
- Provide quick status summary
- Make visibility vs. mutation differences clear

### 5.3 Canonical Admin Home Reconstruction
Based on ADMIN_TREE_MAP_v2.0.0.md §4, the admin home must render the canonical tree:

```
/admin → Home
  [⚙️ Operations]       [💱 Symbols & Coverage]
  [🔍 Decision Vis.]    [📡 Distribution]
  [📊 Research & Ana.]  [🧠 Intelligence]
  [🤝 Affiliate]        [👥 Roles & Identity]
  [🩺 System Health]    [📖 Governance & Docs]
  [🔒 Security & Audit]
```

Role-scoped: each role sees only authorized panels (see ROLE_MAPPING.md §4).

### 5.4 Operations Panel Reconstruction
Source: ADMIN_TREE_MAP_v2.0.0.md §6.2; ADMIN_CONTROL_SPEC_v2.0.0.md §6

Content: engine state, freeze/pause, incident queue, recovery actions, restart/recovery  
Backing: existing engine status + diagnose handlers  
Sub-navigation: Engine Status | Diagnose | Back to Admin

### 5.5 Symbols & Coverage Panel Reconstruction
Source: ADMIN_TREE_MAP_v2.0.0.md §6.3; ADMIN_CONTROL_SPEC_v2.0.0.md §7

Content: active symbols list, symbol toggles, coverage selection  
Backing: existing symbols_toggle_markup + handle_symbols_toggle/all/none  
Sub-navigation: symbol checkboxes | ✅ All | ⬜ None | 🔄 Refresh | Back to Admin

### 5.6 Decision Visibility Panel Reconstruction
Source: ADMIN_TREE_MAP_v2.0.0.md §6.4; ADMIN_CONTROL_SPEC_v2.0.0.md §8

Content: current candidate, last decision, gate results, rejection reasons, score composition  
Backing: existing debug handler (render_debug_last)  
Sub-navigation: 🔄 Refresh | Back to Admin

### 5.7 Distribution Control Panel Reconstruction
Source: ADMIN_TREE_MAP_v2.0.0.md §6.5; ADMIN_CONTROL_SPEC_v2.0.0.md §9

Content: route status, channel readiness, tier routing, publication controls  
Backing: NEW view (render_distribution_panel) — reads environment configuration  
Sub-navigation: 🔄 Refresh | Back to Admin

### 5.8 Research & Analytics Panel Reconstruction
Source: ADMIN_TREE_MAP_v2.0.0.md §6.6; ADMIN_CONTROL_SPEC_v2.0.0.md §10

Content: latest summary, performance trends, rejection analytics, outcome analytics  
Backing: existing report handler + _find_latest_report_json  
Sub-navigation: 📥 Download | 🔄 Refresh | Back to Admin

### 5.9 Intelligence Panel Reconstruction
Source: ADMIN_TREE_MAP_v2.0.0.md §6.7; ADMIN_CONTROL_SPEC_v2.0.0.md §11

Content: decision intelligence, debug dashboard, drift signals, anomaly summaries  
Backing: NEW view (render_intelligence_panel) — reads engine events for intelligence summary  
Sub-navigation: 🔄 Refresh | Back to Admin

### 5.10 Affiliate / Partner Panel Reconstruction
Source: ADMIN_TREE_MAP_v2.0.0.md §6.8; ADMIN_CONTROL_SPEC_v2.0.0.md §12

Content: my scope, my referrals, active referred users, conversion summary, commission summary  
Backing: existing affiliate handler (render_affiliate_scope)  
Sub-navigation: Back to Admin

### 5.11 Roles & Identity Panel Reconstruction
Source: ADMIN_TREE_MAP_v2.0.0.md §6.9

Content: my identity, my role, scope summary, visible matrix, role references  
Backing: existing roles handler (render_roles)  
Sub-navigation: 🔄 Reload Roles (Owner/Primary Admin only) | Back to Admin

### 5.12 System Health Panel Reconstruction
Source: ADMIN_TREE_MAP_v2.0.0.md §6.10

Content: health summary, observability summary, last errors, alerts, diagnostics  
Backing: existing engine + diagnose + audit handlers  
Sub-navigation: 🤖 Engine State | 🩺 Diagnose | 🔍 Runtime Audit | Back to Admin

### 5.13 Governance & Docs Panel Reconstruction
Source: ADMIN_TREE_MAP_v2.0.0.md §6.11

Content: active canonical specs, architecture mapping, change-control references  
Backing: existing docs handler (handle_docs_list)  
Sub-navigation: canonical doc list | Back to Admin

### 5.14 Security & Audit Panel Reconstruction
Source: ADMIN_TREE_MAP_v2.0.0.md §6.12

Content: admin action log, access denials, role change audit, audit exports  
Backing: existing audit handler (handle_audit_runtime) + file browser  
Sub-navigation: 🔍 Runtime Audit | 📁 Files | Back to Admin

---

## 6. DOCUMENTATION UX RECONSTRUCTION

Source: TELEGRAM_UX_v2.0.0.md §19

Telegram may deliver canonical documentation to authorized roles. The Governance & Docs panel implements this by providing access to canonical active specs through the existing docs file browser.

---

## 7. RESEARCH / SUMMARY UX RECONSTRUCTION

Source: TELEGRAM_UX_v2.0.0.md §20

Research delivery is implemented via the Research & Analytics panel, accessible to authorized roles only.

---

## 8. PRIVATE/ADMIN UX ROUTING (FROM TELEGRAM_UX_v2.0.0.md §31)

| Surface | Implementation |
|---|---|
| Private member UX (DMs) | Owner private DM context: `/admin` and related commands accepted |
| Public channel UX | Live Signal UX only; no admin controls |
| Admin/operator UX | Admin control chat + thread context required; or owner private DM |

---

## 9. DM-ONLY MEMBER STATISTICS (FROM TELEGRAM_UX_v2.0.0.md §29)

Member statistics are accessible only through DM/private chat. Public channel requests must be blocked. This is already enforced by the existing `_is_owner_private_context` and `_is_admin_topic_context` gate logic.
