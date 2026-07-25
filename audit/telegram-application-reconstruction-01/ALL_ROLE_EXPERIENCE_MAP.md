# ALL_ROLE_EXPERIENCE_MAP.md

BinaryBot — Telegram Application Reconstruction  
Audit: telegram-application-reconstruction-01  
Document: ALL_ROLE_EXPERIENCE_MAP.md  
Status: RECONSTRUCTION AUDIT

---

## PURPOSE

This document maps every canonical role to its complete Telegram experience:
entry point, home page, available actions, navigation paths, and restrictions.

Source: TELEGRAM_UX_v2.0.0.md §15; ROLE_AND_PERMISSION_MATRIX_SPEC_v2.0.0.md §5; ADMIN_TREE_MAP_v2.0.0.md §7

---

## 1. OWNER

**Canonical Label:** Owner  
**Source:** ROLE_AND_PERMISSION_MATRIX_SPEC_v2.0.0.md §5.1

### Entry Points
| Entry | Where | Result |
|---|---|---|
| /start | Private DM | Role-scoped welcome page with [Admin Control Surface] + [Status] buttons |
| /admin | Private DM or admin control topic | Full 11-panel admin tree (all panels visible) |
| /help | Private DM or admin control topic | Help page listing all commands including admin |
| /status | Any chat | Status page with Refresh + Home |

### Telegram Experience
- Full visibility of all 11 canonical admin tree panels
- Access to admin control surface from private DM (owner-exclusive DM privilege)
- Can view and edit: operations, symbols, strategy, thresholds, SR, spike filter
- Can view: distribution, research, intelligence, affiliate, roles, system health, governance docs, security audit
- Can reload roles config
- All panels navigable via inline keyboard
- Single active message maintained per session

### Admin Panels Accessible
All 11: Operations, Symbols & Coverage, Decision Visibility, Distribution, Research & Analytics, Intelligence, Affiliate / Partner, Roles & Identity, System Health, Governance & Docs, Security & Audit

---

## 2. PRIMARY ADMIN

**Canonical Label:** Primary Admin  
**Source:** ROLE_AND_PERMISSION_MATRIX_SPEC_v2.0.0.md §5.2

### Entry Points
| Entry | Where | Result |
|---|---|---|
| /start | Private DM | Welcome page informing of configured admin channel |
| /admin | Admin control topic | Full 11-panel admin tree |
| /help | Admin control topic | Help page listing all commands |
| /status | Any chat | Status page |

### Telegram Experience
- Welcome page informs that admin access is in the configured admin control channel
- From admin control channel: full 11-panel tree (same visibility as OWNER)
- Cannot access admin surface from private DM (requires admin control topic)
- Public commands (/status, /help) available everywhere

### Admin Panels Accessible
All 11: Operations, Symbols & Coverage, Decision Visibility, Distribution, Research & Analytics, Intelligence, Affiliate / Partner, Roles & Identity, System Health, Governance & Docs, Security & Audit

---

## 3. STRATEGY ADMIN (Functional Admin — Operations)

**Canonical Label:** Functional Admin (Operations)  
**Source:** ROLE_AND_PERMISSION_MATRIX_SPEC_v2.0.0.md §5.3

### Entry Points
| Entry | Where | Result |
|---|---|---|
| /start | Private DM | Welcome page informing of configured admin channel |
| /admin | Admin control topic | 3-panel admin tree (Operations, Symbols, Decision Visibility) |
| /status | Any chat | Status page |

### Telegram Experience
- Can access: engine state, symbol toggles, decision visibility (debug snapshot)
- Cannot access: distribution, research, affiliate, roles, system health, governance, security audit
- Must use admin control topic for all admin functions

### Admin Panels Accessible
Operations, Symbols & Coverage, Decision Visibility

---

## 4. RESEARCH ADMIN (Functional Admin — Research)

**Canonical Label:** Functional Admin (Research)  
**Source:** ROLE_AND_PERMISSION_MATRIX_SPEC_v2.0.0.md §5.3

### Entry Points
| Entry | Where | Result |
|---|---|---|
| /start | Private DM | Welcome page informing of configured admin channel |
| /admin | Admin control topic | 3-panel admin tree (Decision Visibility, Research, Intelligence) |

### Telegram Experience
- Read-only: decision audit visibility, research/analytics reports, intelligence summaries
- Cannot access: operations, symbols, distribution, affiliate, roles, system health, governance, security

### Admin Panels Accessible
Decision Visibility (read), Research & Analytics, Intelligence

---

## 5. ANALYST

**Canonical Label:** Analyst  
**Source:** ROLE_AND_PERMISSION_MATRIX_SPEC_v2.0.0.md §5.5

### Entry Points
| Entry | Where | Result |
|---|---|---|
| /start | Private DM | Welcome page informing of configured admin channel |
| /admin | Admin control topic | 3-panel admin tree (Decision Visibility, Research, Intelligence) — read only |

### Telegram Experience
- Read-only: decision visibility, research & analytics, intelligence
- Same panel set as RESEARCH_ADMIN (read-only specialist)

### Admin Panels Accessible
Decision Visibility (read), Research & Analytics (read), Intelligence (read)

---

## 6. MODERATOR

**Canonical Label:** Moderator  
**Source:** ROLE_AND_PERMISSION_MATRIX_SPEC_v2.0.0.md §5.6

### Entry Points
| Entry | Where | Result |
|---|---|---|
| /start | Private DM | Welcome page informing of configured admin channel |
| /admin | Admin control topic | 1-panel admin tree (System Health only) |

### Telegram Experience
- Limited: System Health panel only
- Cannot access any other admin surface

### Admin Panels Accessible
System Health (limited)

---

## 7. AFFILIATE ADMIN

**Canonical Label:** Affiliate Admin  
**Source:** ROLE_AND_PERMISSION_MATRIX_SPEC_v2.0.0.md §5.4; AFFILIATE_SIGNAL_DISTRIBUTION_MODEL_v2.0.0.md

### Entry Points
| Entry | Where | Result |
|---|---|---|
| /start | Private DM | Welcome page informing of configured admin channel |
| /admin | Admin control topic | 1-panel admin tree (Affiliate / Partner only) |

### Telegram Experience
- Strictly scoped to own affiliate program data
- Can view: own affiliate scope, own referrals, own assigned users
- Cannot view: global system data, strategy internals, engine state, other affiliates' data
- AFFILIATE_SIGNAL_DISTRIBUTION_MODEL_v2.0.0.md mandates strict isolation

### Admin Panels Accessible
Affiliate / Partner (own scope only)

---

## 8. USER

**Canonical Label:** User  
**Source:** ROLE_AND_PERMISSION_MATRIX_SPEC_v2.0.0.md §5.7

### Entry Points
| Entry | Where | Result |
|---|---|---|
| /start | Private DM or any chat | Platform introduction page with [Status] + [Help] buttons |
| /status | Any chat | Status page with Refresh + Home |
| /help | Any chat | Public-commands-only help page |

### Telegram Experience
- Receives trading signals via configured trading channels (automatic, not interactive)
- Can submit outcome votes (WIN/LOSE/MISSED) on signal messages
- Can check /status
- Can view /help (public commands only)
- No admin surface visible or accessible
- No interactive control surface defined canonically

### Admin Panels Accessible
None — no admin surface

---

## 9. UNKNOWN / UNAUTHENTICATED USER

Not a canonical role; treated as USER in the permission system.

### Entry Points
Same as USER — /start shows platform introduction with public action buttons.

---

## ROLE COMPARISON MATRIX

| Feature | OWNER | PRIMARY_ADMIN | STRATEGY_ADMIN | RESEARCH_ADMIN | ANALYST | MODERATOR | AFFILIATE_ADMIN | USER |
|---|---|---|---|---|---|---|---|---|
| /start welcome page | ✅ + Admin button | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Admin from private DM | ✅ (DM privilege) | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Admin from admin topic | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ |
| Admin panels visible | All 11 | All 11 | 3 | 3 | 3 | 1 | 1 | 0 |
| Signal consumption | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Outcome vote | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Roles management | ✅ | View only | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Affiliate view | Any | Any | ❌ | ❌ | ❌ | ❌ | Own only | ❌ |

---

End of ALL_ROLE_EXPERIENCE_MAP.md
