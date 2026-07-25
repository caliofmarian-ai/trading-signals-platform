# PAGE_CONTRACT_REGISTER.md

BinaryBot — Telegram Application Reconstruction  
Audit: telegram-application-reconstruction-01  
Document: PAGE_CONTRACT_REGISTER.md  
Status: RECONSTRUCTION AUDIT

---

## PURPOSE

This register defines the page contract for every page in the canonical Telegram application.

Page contract (canonical §F):
- Identifiable page title
- Concise canonical explanation
- Only authorized actions
- Understandable button labels
- Appropriate navigation (Back/Home/Refresh where applicable)
- No dead end
- Consistent rendering from slash command and callback entry points

---

## APP: PAGES (Universal — accessible from any chat context)

### PAGE: Welcome / Home
| Field | Value |
|---|---|
| Title | 🤖 BinaryBot |
| Entry points | /start command; APP:HOME callback |
| Description | Role-scoped platform introduction and entry point |
| Authorized actions | Varies by role (see table below) |
| Navigation | N/A (this IS home) |
| Dead end | No — always has ≥1 button |
| Rendering consistency | Same content from /start and APP:HOME callback |

**Buttons by role:**

| Role | Button 1 | Button 2 |
|---|---|---|
| OWNER | ⚙️ Admin Control Surface (APP:ADMIN) | 📊 System Status (APP:STATUS) |
| All admin tiers (non-owner) | 📊 System Status (APP:STATUS) | ❓ Help (APP:HELP) |
| USER | 📊 System Status (APP:STATUS) | ❓ Help (APP:HELP) |

---

### PAGE: System Status
| Field | Value |
|---|---|
| Title | 📊 System Status |
| Entry points | /status command; APP:STATUS callback |
| Description | Read-only view of overall runtime health, market data state, FSM state, shadow mode |
| Authorized actions | All roles (public page) |
| Navigation | [🔄 Refresh] [🏠 Home] |
| Dead end | No — Refresh and Home buttons always present |
| Rendering consistency | Same fields from /status and APP:STATUS |

**Fields shown:** Overall, Runtime phase, Health, Recovery, Market data, Telegram, FSM, Shadow mode, Broker execution, Market note (if present)

---

### PAGE: Help
| Field | Value |
|---|---|
| Title | ❓ Help — BinaryBot |
| Entry points | /help command; APP:HELP callback |
| Description | Role-scoped command reference |
| Authorized actions | All roles (content filtered by role) |
| Navigation | [📊 System Status] [🏠 Home] |
| Dead end | No |
| Rendering consistency | Same from /help and APP:HELP |

**Content by role:**
- USER: public commands only (/start, /status, /help)
- Admin tiers: public commands + admin command families listed

---

### PAGE: Admin Info (OWNER only via app nav)
| Field | Value |
|---|---|
| Title | ⚙️ Admin Control Surface |
| Entry points | APP:ADMIN callback (OWNER only) |
| Description | Bridge page directing to full admin tree via /admin or admin channel |
| Authorized actions | OWNER only |
| Navigation | [🏠 Home] |
| Dead end | No |

---

## ADMIN TREE PAGES (Admin control topic or owner private DM)

### PAGE: Admin Home
| Field | Value |
|---|---|
| Title | Admin panel header with role identification |
| Entry points | /admin command; ADMIN_NAV:HOME callback |
| Description | Role-scoped canonical admin tree navigation |
| Authorized actions | Varies by role (panel visibility from ADMIN_TREE_MAP_v2.0.0.md §7) |
| Navigation | All panel buttons; [🔄 Roles Reload] if allowed |
| Dead end | No — always has panel buttons |

---

### PAGE: Operations
| Field | Value |
|---|---|
| Entry points | ADMIN_NAV:OPERATIONS |
| Buttons | [🤖 Engine State] [🩺 Diagnose] [📋 Strategy] [🏠 Admin Home] |

### PAGE: Symbols & Coverage
| Field | Value |
|---|---|
| Entry points | ADMIN_NAV:SYMBOLS_COV |
| Buttons | Symbol toggle checkboxes + [✅ All] [⬜ None] [🔄 Refresh] [🏠 Admin Home] |

### PAGE: Decision Visibility
| Field | Value |
|---|---|
| Entry points | ADMIN_NAV:DECISION_VIS |
| Buttons | [🔄 Refresh] [🏠 Admin Home] |

### PAGE: Distribution
| Field | Value |
|---|---|
| Entry points | ADMIN_NAV:DISTRIBUTION |
| Buttons | [🔄 Refresh] [🏠 Admin Home] |

### PAGE: Research & Analytics
| Field | Value |
|---|---|
| Entry points | ADMIN_NAV:RESEARCH |
| Buttons | [📥 Download] (if file available) [🔄 Refresh] [🏠 Admin Home] |

### PAGE: Intelligence
| Field | Value |
|---|---|
| Entry points | ADMIN_NAV:INTELLIGENCE |
| Buttons | [🔄 Refresh] [🏠 Admin Home] |

### PAGE: Affiliate / Partner
| Field | Value |
|---|---|
| Entry points | ADMIN_NAV:AFFILIATE |
| Buttons | [🏠 Admin Home] |

### PAGE: Roles & Identity
| Field | Value |
|---|---|
| Entry points | ADMIN_NAV:ROLES |
| Buttons | [🔄 Reload Roles] (owner/primary admin only) [🏠 Admin Home] |

### PAGE: System Health
| Field | Value |
|---|---|
| Entry points | ADMIN_NAV:SYSHEALTH |
| Buttons | [🤖 Engine State] [🩺 Diagnose] [🔍 Runtime Audit] [🏠 Admin Home] |

### PAGE: Governance & Docs
| Field | Value |
|---|---|
| Entry points | ADMIN_NAV:GOVDOCS |
| Buttons | Document list items + [🏠 Admin Home] |

### PAGE: Security & Audit
| Field | Value |
|---|---|
| Entry points | ADMIN_NAV:SECAUDIT |
| Buttons | [🔍 Runtime Audit] [📁 Files] [🏠 Admin Home] |

---

## PAGE CONTRACT VERIFICATION SUMMARY

| Contract Requirement | Met? | Evidence |
|---|---|---|
| Identifiable page title | ✅ | All pages have emoji + title text |
| Concise canonical explanation | ✅ | All pages include description text |
| Only authorized actions | ✅ | Role-scoped rendering in both app_nav and admin_ui |
| Understandable button labels | ✅ | Emoji + text labels throughout |
| Appropriate navigation | ✅ | Back/Home on all admin pages; Home on all app pages |
| No dead end | ✅ | All pages tested for ≥1 button |
| Consistent slash/callback rendering | ✅ | Same functions called for both entry types |

---

End of PAGE_CONTRACT_REGISTER.md
