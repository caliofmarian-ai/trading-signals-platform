# ADMIN_OPERATIONS_SPEC.md
BinaryBot — Admin Operations, Roles & Control Procedures
Version: 1.0.0
Status: CANONICAL

Linked Documents:
- TELEGRAM_UX.md
- SIGNAL_DISTRIBUTION_SPEC.md
- CHANNEL_CONFIG_SPEC.md
- OBSERVABILITY_LOGGING_SPEC.md
- EVENT_SCHEMA_SPEC.md
- SYSTEM_INVARIANTS.md
- FAILURE_RECOVERY_SPEC.md
- GOVERNANCE_AND_CHANGE_CONTROL.md
- TEST_PLAN.md
- CHANGELOG.md

---

## 1. PURPOSE

This document defines the operational control layer of BinaryBot:
- Who can do what (roles & permissions)
- How admin actions are executed via Telegram
- How changes are audited (proof logs)
- How to operate safely in production
- How emergencies are handled (freeze, recovery)

This is the “human control plane” of the system.

If an action is not defined here, it is not allowed.

---

## 2. DEFINITIONS

**Control Plane**
The Telegram-based operational interface used to control the engine.

**RBAC**
Role-Based Access Control:
OWNER / ADMIN / ANALYST / MODERATOR

**Admin Topic / Control Topic**
Private admin supergroup topic(s) where control actions and proof logs occur.

**Proof Log**
A deterministic audit message + JSONL event proving an action happened, by whom, when, and with what effect.

**Freeze Mode**
Emergency state that stops scanning and prevents signals, while preserving state.

---

## 3. ROLES (RBAC)

BinaryBot supports four roles:

### 3.1 OWNER
Highest authority.

Owner can:
- Configure everything
- Promote/demote roles
- Enable/disable engine
- Edit distribution policy config
- Edit channel mappings
- Trigger freeze/unfreeze
- View all analytics and logs (global)
- Export data (logs/outcomes/aggregates)
- Approve releases and version bumps

Owner is the only role allowed to:
- Change channel IDs
- Change tier limits and reset time
- Change governance policies
- Delete/rotate logs manually (if ever allowed)

### 3.2 ADMIN
Operational administrator.

Admin can:
- Change buffer mode
- Change symbol selection (Set Symbols)
- View engine status
- View tier counters and tier state
- Trigger safe restart (if enabled)
- Trigger freeze (but cannot change freeze rules)
- Access docs viewer
- Moderate operational noise in admin channels

Admin cannot:
- Change channel IDs
- Change tier daily limits
- Change reset time
- Change algo_params.json directly (unless OWNER grants temporary override)

### 3.3 ANALYST
Read-only + research.

Analyst can:
- View analytics dashboards
- View symbol ranking, focus history, conversion funnel
- View aggregated outcomes stats
- View observability summaries (not raw sensitive IDs)
- Request “recommendations” but cannot apply changes

Analyst cannot:
- Change buffer/symbols
- Freeze/unfreeze
- Restart engine
- Change configs

### 3.4 MODERATOR
Community moderation (tier channels), minimal bot control.

Moderator can:
- Run safe informational commands (read-only)
- View limited status (uptime, last signal time)
- Review per-signal aggregated stats (ELITE) if visible in channel
- Report abuse (spam, scam) to admin logs

Moderator cannot:
- Change trading behavior
- Change distribution settings
- Access raw logs or user outcome identity data

---

## 4. PERMISSION MODEL (CANONICAL)

Each action is assigned a minimum role.

### 4.1 Critical Actions (OWNER only)
- Set / change channel IDs
- Set tier limits (FREE/BASIC/PRO)
- Set daily reset time
- Enable/disable ELITE outcomes system
- Rotate/purge logs
- Change “governance mode”
- Deploy / version bump approval actions

### 4.2 Operational Actions (OWNER, ADMIN)
- Set Buffer Mode
- Set Symbols (active_symbols.json)
- Request Engine Status
- View Tier Counters/States
- Trigger Freeze (immediate)
- Trigger Safe Restart (if enabled)

### 4.3 Analytics Actions (OWNER, ADMIN, ANALYST)
- View Symbol Ranking
- View Focus History
- View Conversion Funnel
- View Drift Alerts
- View Daily/Weekly Reports

### 4.4 Moderation Actions (OWNER, ADMIN, MODERATOR)
- Request limited public info
- Forward issues / incidents to Admin logs

---

## 5. TELEGRAM CONTROL SURFACE

### 5.1 Control Location
All control actions MUST occur in:
- Admin Supergroup
- Dedicated Admin topic(s)

Rule:
- No control actions in public tier channels.

### 5.2 Required Admin Topics (Recommended)
- **ADMIN_CONTROL**: buttons + commands
- **ADMIN_PROOFS**: proof logs only (immutable record)
- **ADMIN_ALERTS**: critical issues (crash, API, invariants)
- **ADMIN_RESEARCH**: analytics outputs (optional)

(Exact topic names are implementation details; routing rules must match TELEGRAM_UX.md.)

---

## 6. ADMIN PANEL (BUTTONS + FLOWS)

### 6.1 Admin Panel Entry
Command:
- `/admin`

Shows role + available actions.

Panel must be role-filtered:
- users only see actions they are allowed to execute.

### 6.2 Core Buttons (OWNER/ADMIN)
- **Set Buffer**
  - options: SMALL / MEDIUM / LARGE
  - effect: updates settings.json
  - emits proof log: ADMIN_CHANGE(buffer_mode)

- **Set Symbols**
  - opens full symbols list
  - admin toggles active symbols
  - effect: updates active_symbols.json
  - emits proof log: ADMIN_CHANGE(active_symbols)

- **Status**
  - shows:
    - engine mode (WIDE/FOCUS)
    - focus symbols / watchlist
    - cooldown symbols
    - current buffer mode
    - active symbols count
    - last signal timestamp
  - read-only

- **Tier Status**
  - shows per tier:
    - ACTIVE/SILENT
    - open_signals_today / limit
    - reset time (Europe/London)
  - read-only

### 6.3 Research Buttons (OWNER/ADMIN/ANALYST)
- **Symbol Ranking**
  - top symbols by OPEN_NOW volume
  - conversion rate PRE→OPEN_NOW
  - rejection breakdown

- **Focus History**
  - list/summary of focus entries/exits
  - focus_to_open conversion

- **Funnel**
  - PRE count
  - CONFIRM count
  - OPEN_NOW count
  - stage dropoffs

- **Drift Alerts**
  - recent rolling WR / anomaly flags
  - requires data source availability

### 6.4 Documentation Buttons (Role-based)
- **View Docs**
  - sends selected `.md` file as document
  - allowed roles:
    - OWNER/ADMIN: full docs list
    - ANALYST: research + specs (no sensitive governance/secrets if any)
    - MODERATOR: only public-facing docs if configured

Docs list (recommended):
- TELEGRAM_UX.md
- RISK_MODEL.md
- SIGNAL_DISTRIBUTION_SPEC.md
- CHANNEL_CONFIG_SPEC.md
- OBSERVABILITY_LOGGING_SPEC.md
- EVENT_SCHEMA_SPEC.md
- FAILURE_RECOVERY_SPEC.md
- SYSTEM_INVARIANTS.md
- ADMIN_OPERATIONS_SPEC.md
- TEST_PLAN.md
- CHANGELOG.md

---

## 7. PROOF LOGS (MANDATORY)

Every control action that changes state MUST generate:

1) **Telegram proof message** in ADMIN_PROOFS topic
2) **admin_change event** in JSONL logs

### 7.1 Proof Message Content (Canonical)
Must include:
- timestamp (UTC + Europe/London)
- actor user_id
- actor role
- action name
- before → after (diff)
- engine version (algo_version)
- success/failure status
- correlation_id (optional, recommended)

### 7.2 Proof Message Examples

BUFFER CHANGE:
- action=SET_BUFFER
- before=MEDIUM
- after=LARGE

SYMBOLS CHANGE:
- action=SET_SYMBOLS
- before_count=12
- after_count=9
- added=[...]
- removed=[...]

TIER RESET:
- action=TIER_RESET
- before: counters
- after: counters=0, states=ACTIVE

---

## 8. SAFETY & EMERGENCY CONTROLS

### 8.1 Freeze Mode (OWNER/ADMIN can trigger)
Commands:
- `/freeze`
- button: **Freeze**

Freeze behavior:
- stop scan loop (no strategy evaluations)
- stop signal emission
- preserve focus_state.json and dist_state.json
- emit CRITICAL alert + proof log

Unfreeze:
- `/unfreeze` (OWNER only by default; configurable)
- resumes scan loop safely

### 8.2 Crash Loop Handling
If crash loop detected (per OBSERVABILITY spec):
- engine should auto-enter FREEZE
- admin alerted in ADMIN_ALERTS
- require OWNER approval to resume

### 8.3 Invariant Breach Handling
If any SYSTEM_INVARIANTS.md rule is violated:
- immediate FREEZE
- critical log emitted
- admin proof emitted
- require incident review procedure (see FAILURE_RECOVERY_SPEC.md)

---

## 9. CHANGE OPERATIONS (GOVERNANCE)

### 9.1 Rule
Any behavior-changing modification requires:
- version bump
- changelog entry
- test plan run
- proof log "DEPLOY_MARKER"

### 9.2 Allowed Live Changes (No Deploy)
Allowed without deploy (OWNER/ADMIN):
- buffer mode
- active symbol selection

Disallowed without deploy (OWNER only):
- algo_params thresholds
- tier limits/reset time
- distribution policy behavior

---

## 10. DATA PRIVACY (ELITE OUTCOMES)

Outcome reporting is ELITE-only.

Rules:
- Users can only see:
  - per-signal aggregated stats
  - their own stats via DM
- Users must never see other users’ identities or raw IDs.
- Admin can view global aggregates.
- Raw USER_ID linkage is internal only and must not appear publicly.

(Outcome identity handling must follow EVENT_SCHEMA_SPEC.md + OBSERVABILITY_LOGGING_SPEC.md.)

---

## 11. OPERATIONAL ROUTINES (DAILY/WEEKLY)

### 11.1 Daily Checklist (Owner/Admin)
- check engine status
- check tier counters + reset time correctness
- check last signals timestamp
- check API error count
- review drift alerts

### 11.2 Weekly Checklist (Owner + Analyst)
- export weekly summary:
  - symbol ranking
  - focus efficiency
  - rejection breakdown
  - outcomes aggregates
  - drift analysis
- adjust symbol selection if needed (data-driven)
- note changes in CHANGELOG

---

## 12. CANONICAL GUARANTEES

If this spec is implemented:
- Role separation prevents accidental damage
- All changes are provable and auditable
- Emergency freezes prevent uncontrolled behavior
- Operations remain deterministic and enterprise-safe

---

End of ADMIN_OPERATIONS_SPEC.md