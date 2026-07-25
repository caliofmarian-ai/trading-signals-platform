# GAPS_AND_IMPLEMENTATION_DECISIONS.md

BinaryBot — Telegram Application Reconstruction  
Audit: telegram-application-reconstruction-01  
Document: GAPS_AND_IMPLEMENTATION_DECISIONS.md  
Status: RECONSTRUCTION AUDIT

---

## PURPOSE

This document records every implementation decision made outside explicit canonical wording,
every canonical gap encountered, and the minimum neutral behavior implemented for each gap.

All decisions here must NOT redefine business behavior. They implement minimum neutral
presentation behavior only.

---

## DECISION FORMAT

Each entry records:
- **Gap ID**: Unique identifier
- **Area**: Which part of the application
- **Canonical Gap Description**: What the canonical docs do not specify
- **Decision Made**: The minimum neutral behavior implemented
- **Canonical Basis**: Closest applicable canonical authority
- **Impact**: Whether this affects business behavior
- **Risk**: Whether this decision could be wrong

---

## GAP-APP-001: /start behavior not canonically specified

**Area:** Entry flow — /start command  
**Canonical Gap:** TELEGRAM_UX_v2.0.0.md does not specify the content or behavior of the /start command. The document specifies /admin behavior (§16.2) but not /start.  
**Decision Made:** /start renders a role-scoped welcome page that:
  1. Identifies the platform (BinaryBot)
  2. Shows a shadow mode notice if active
  3. Greets the user by first name if available
  4. Describes the user's role/access level
  5. Provides buttons for authorized next actions
**Canonical Basis:** TELEGRAM_UX_v2.0.0.md §15.2 (role-scoped rendering); §16.2 (identify role/scope; show allowed branches); ROLE_AND_PERMISSION_MATRIX_SPEC_v2.0.0.md §2.7 (invisible-by-default for unauthorized)  
**Impact:** Presentation only. No business behavior changed.  
**Risk:** Low. The decision adds value without restricting or extending canonical authority.

---

## GAP-APP-002: USER interactive menu not canonically defined

**Area:** USER role experience  
**Canonical Gap:** ROLE_AND_PERMISSION_MATRIX_SPEC_v2.0.0.md §5.7 defines USER as "non-admin consumers of public or paid-facing system outputs" with "no admin privileges" and "no internal system visibility." No interactive control surface is defined for USER.  
**Decision Made:** USER receives:
  - /start: Platform introduction + [Status] + [Help] buttons
  - /status: Full status page (public information, existing canonical behavior)
  - /help: Public commands only
  - Signal delivery: automatic, via configured channels (unchanged)
  - Outcome votes: via VOTE_* callbacks (unchanged)
**Canonical Basis:** TELEGRAM_UX_v2.0.0.md §5–§8 (live signal UX); §13–§14 (outcome UX); §17 (command families: /start, /status, /help listed)  
**Impact:** Presentation only. Existing signal and outcome behavior unchanged.  
**Risk:** Low. Neutral presentation without inventing business capabilities.

---

## GAP-APP-003: Navigation state persistence not canonically specified

**Area:** Single active UI message — persistence  
**Canonical Gap:** No canonical document specifies that navigation state (the active UI message ID per user) must survive bot restarts.  
**Decision Made:** Navigation state is tracked in-memory (`_active_ui` dict in telegram_app_nav.py). After a bot restart, users receive a new message on their next interaction. No database or persistent storage added.  
**Canonical Basis:** TELEGRAM_UX_v2.0.0.md §16.2 implies edit-not-send pattern but does not require persistence.  
**Impact:** After a bot restart, a user's next /start or navigation press sends a new message rather than editing the previous one. This is cosmetic. Behavior is canonical (new message is created and tracked).  
**Risk:** Low. The canonical docs do not forbid this. Persistence can be added later if required.

---

## GAP-APP-004: Non-owner admin in private DM — experience not canonically specified

**Area:** Non-owner admin roles in private DM  
**Canonical Gap:** TELEGRAM_UX_v2.0.0.md §31.1 specifies that admin/operator UX must remain on the admin control surface. It does not define what happens when a non-owner admin sends /start in a private DM.  
**Decision Made:** Non-owner admins in private DM receive:
  - Their role label identified
  - A message directing them to the admin control channel
  - [Status] and [Help] buttons for public functions
  - No admin surface buttons (admin context required)
**Canonical Basis:** TELEGRAM_UX_v2.0.0.md §31.1 (surface distinction); §31.2 (admin route boundary)  
**Impact:** Cosmetic. Admin access was already denied; now the user receives a clear explanation.  
**Risk:** Low. Does not grant unauthorized access.

---

## GAP-APP-005: OWNER private DM admin button scope

**Area:** OWNER experience on /start  
**Canonical Gap:** TELEGRAM_UX_v2.0.0.md does not define the /start page content for OWNER in private DM. The existing codebase grants OWNER private DM access to admin commands (established in commit 49aaeb4 per repository memory).  
**Decision Made:** OWNER /start in private DM shows [⚙️ Admin Control Surface] button in addition to [📊 System Status].  
**Canonical Basis:** TELEGRAM_UX_v2.0.0.md §15.2 (role-scoped rendering); existing private-DM owner privilege  
**Impact:** Cosmetic. The button leads to an informational page directing to /admin or admin channel. No new access granted — OWNER already had this access via slash commands.  
**Risk:** Low. Consistent with existing owner-private-DM privilege.

---

## GAP-APP-006: Help page content for admin roles

**Area:** /help command for admin-tier users  
**Canonical Gap:** TELEGRAM_UX_v2.0.0.md §17 lists illustrative admin command families but does not specify the exact /help text for each role.  
**Decision Made:** Admin-tier /help shows: public commands + admin command families as hints + role label. Exact admin sub-commands not listed (too verbose; /admin tree is the canonical discovery surface).  
**Canonical Basis:** TELEGRAM_UX_v2.0.0.md §17 (command families)  
**Impact:** Presentation only.  
**Risk:** Low.

---

## GAP-APP-007: APP:ADMIN button for non-owner roles

**Area:** APP:ADMIN callback behavior for non-owner  
**Canonical Gap:** The APP:ADMIN button is shown only to OWNER. Non-owner roles pressing this callback (e.g., via stale message) receive an informational response about the admin control channel.  
**Decision Made:** APP:ADMIN for non-owner returns a page directing to the admin control channel, with a [Home] button. No exception or error message.  
**Canonical Basis:** TELEGRAM_UX_v2.0.0.md §16.2; §21.4 (no ambiguous result state)  
**Impact:** Cosmetic. Non-owners cannot access admin from private DM regardless.  
**Risk:** Low.

---

## ITEMS NOT IMPLEMENTED (Canonical Gap — no canonical specification and no minimum neutral behavior required)

| Item | Why Not Implemented |
|---|---|
| In-bot role assignment UI | ROLE_AND_PERMISSION_MATRIX_SPEC_v2.0.0.md §13: roles are stored in config file; no in-bot assignment flow is defined canonically |
| Approval queue for governance-bound changes | CONTROL_PANEL_HIERARCHY §6: no approval workflow backend exists |
| Commission/payout processing via Affiliate panel | AFFILIATE_SIGNAL_DISTRIBUTION_MODEL: no commission backend |
| Drift/anomaly auto-detection backend | No drift detection service; Intelligence panel shows available engine events |
| Member statistics interactive UX | TELEGRAM_UX_v2.0.0.md §29 specifies DM-only access but does not define an interactive member stats flow |

---

End of GAPS_AND_IMPLEMENTATION_DECISIONS.md
