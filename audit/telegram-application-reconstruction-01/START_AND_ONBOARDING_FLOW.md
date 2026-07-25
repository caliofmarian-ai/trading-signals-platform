# START_AND_ONBOARDING_FLOW.md

BinaryBot — Telegram Application Reconstruction  
Audit: telegram-application-reconstruction-01  
Document: START_AND_ONBOARDING_FLOW.md  
Status: RECONSTRUCTION AUDIT

---

## PURPOSE

This document defines the /start entry flow and guided onboarding behavior, derived
exclusively from canonical documents.

---

## 1. CANONICAL AUTHORITY

There is no dedicated canonical specification for the /start flow or onboarding behavior.
The following sections of canonical documents are the closest applicable authority:

| Document | Section | Relevant Guidance |
|---|---|---|
| TELEGRAM_UX_v2.0.0.md | §16.2 | /admin should identify role/scope context; show allowed branches; no flat dump |
| TELEGRAM_UX_v2.0.0.md | §15.2 | Admin surfaces must render according to role and scope |
| TELEGRAM_UX_v2.0.0.md | §17 | Commands are interface affordances, not authority grants |
| ROLE_AND_PERMISSION_MATRIX_SPEC_v2.0.0.md | §2.7 | "Invisible-by-default for unauthorized capability" |
| ROLE_AND_PERMISSION_MATRIX_SPEC_v2.0.0.md | §5.7 | USER = non-admin consumer; no admin privileges; no internal system visibility |

**Design decision (gap implementation):** The /start canonical behavior is derived by applying
the above principles to the entry interaction. This derivation is documented in
GAPS_AND_IMPLEMENTATION_DECISIONS.md.

---

## 2. /START FLOW LOGIC

### 2.1 Input
- Trigger: `/start` command in any Telegram chat
- Context: user_id, chat_id, first_name, shadow_mode env flag
- Role resolution: `admin_permissions.get_primary_role(user_id)`

### 2.2 Role Resolution (Canonical)
Role is resolved from:
1. `OWNER_TELEGRAM_ID` environment variable (fallback owner)
2. `/opt/binarybot/config/admin_roles.json` (configurable via `ADMIN_ROLES_CONFIG`)
3. Default: `ROLE_USER` if no role is configured for this user_id

**No button press grants a role.** Roles are resolved exclusively from configuration.

### 2.3 Page Rendering per Role

```
/start received
    ↓
get_primary_role(user_id) → primary_role
    ↓
render_welcome_page(user_id, primary_role, first_name, shadow_mode)
    ↓
Send response via _send_app_nav_reply (single-message pattern)
    → Track message_id for future edits
```

#### OWNER
- Title: 🤖 BinaryBot
- Shadow mode notice if active
- Text: greeting + "You are connected as Owner — the supreme governance authority" + access description
- Buttons: [⚙️ Admin Control Surface] [📊 System Status]

#### NON-OWNER ADMIN ROLES (PRIMARY_ADMIN, STRATEGY_ADMIN, RESEARCH_ADMIN, ANALYST, MODERATOR, AFFILIATE_ADMIN)
- Title: 🤖 BinaryBot
- Shadow mode notice if active
- Text: greeting + role label + "access is configured for the designated admin control channel"
- Buttons: [📊 System Status] [❓ Help]

#### USER (and unknown users)
- Title: 🤖 BinaryBot
- Shadow mode notice if active
- Text: "Welcome to BinaryBot — an automated trading signal platform. This bot delivers trading signals to configured trading channels."
- Buttons: [📊 System Status] [❓ Help]

### 2.4 Active Message Tracking
After sending the /start response:
- If the publisher returns a message_id, it is stored as the active UI message
- Subsequent button presses (APP: callbacks) edit this message
- This implements the single-message navigation pattern (canonical §D)

---

## 3. PROGRESSIVE DISCLOSURE MODEL

| User Category | First Screen | Second Screen | Third Screen |
|---|---|---|---|
| USER | Platform intro + [Status] + [Help] | Status page | Help page |
| OWNER | Welcome + [Admin] + [Status] | Admin home (11 panels) | Any panel |
| Non-owner admin | Welcome + [Status] + [Help] | Status page | Help page |

**Non-owner admins are directed to the admin control channel.** This preserves the security
boundary defined in TELEGRAM_UX_v2.0.0.md §31.1: admin/operator UX must remain on the
admin control surface.

---

## 4. RETURNING USERS

A returning user who sends /start again:
- Gets the same role-scoped welcome page
- If there is an existing active UI message for them (same chat), the old message is edited
  to show the welcome page (no new message accumulated)
- If the old message was deleted or too old, a new message is sent and tracked

---

## 5. CHANGED ROLE BEHAVIOR

When a user's role changes (via config file update and `reload_roles_config()`):
- The NEXT interaction (including /start) resolves the updated role
- The welcome page shown will reflect the new role
- The lru_cache on `load_roles_config()` is cleared by `reload_roles_config()`

---

## 6. SHADOW MODE HANDLING

When `SHADOW_MODE=true` env var is set:
- All /start responses include: "⚠️ Shadow mode is active. No live signal delivery."
- This notice is placed prominently in the page header
- Canonical: shadow mode affects signal delivery, not admin access

---

## 7. PRIVATE CHAT RESTRICTIONS

Per TELEGRAM_UX_v2.0.0.md §29:
- Member statistics accessible only via DM/private chat
- Public channel requests must be blocked

Admin UX per §31.1:
- Admin control surface requires the configured admin control chat/topic
- Exception: OWNER can access admin from private DM (existing owner-private-DM privilege)

---

## 8. IMPLEMENTATION REFERENCE

| Component | File | Function |
|---|---|---|
| Start rendering | send/core/telegram_app_nav.py | render_welcome_page() |
| Bot dispatch | send/core/bot_service.py | process_update (cmd == "/start" branch) |
| Active message | send/core/bot_service.py | _send_app_nav_reply() |
| Role resolution | send/core/admin_permissions.py | get_primary_role() |
| Shadow mode | send/core/bot_service.py | _env_flag("SHADOW_MODE") |

---

End of START_AND_ONBOARDING_FLOW.md
