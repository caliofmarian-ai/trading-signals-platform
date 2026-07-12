# ADMIN_CONTROL_SPEC_v2.0.0.md

BinaryBot — Admin Control Surface Specification  
Version: 2.0.0  
Status: CANONICAL  
Path: /opt/binarybot/docs/canonical/active/ADMIN_CONTROL_SPEC_v2.0.0.md

Linked Documents:
- ADMIN_OPERATIONS_SPEC_v2.0.0.md
- ADMIN_TREE_MAP_v2.0.0.md
- CONTROL_PANEL_HIERARCHY_AND_INTELLIGENCE_SPEC_v2.0.0.md
- ROLE_AND_PERMISSION_MATRIX_SPEC_v2.0.0.md
- TELEGRAM_UX_v2.0.0.md
- SIGNAL_DISTRIBUTION_SPEC_v2.0.0.md
- CHANNEL_CONFIG_SPEC_v2.0.0.md
- DECISION_AUDIT_SPEC_v2.0.0.md
- TRADE_TEMPORAL_TELEMETRY_SPEC_v2.0.0.md
- OUTCOME_TRACKING_SPEC_v2.0.0.md
- PERFORMANCE_ANALYTICS_SPEC_v2.0.0.md
- RESEARCH_AND_LEARNING_FRAMEWORK_SPEC_v2.0.0.md
- STRATEGY_INTELLIGENCE_SYSTEM_v2.0.0.md
- AUTONOMOUS_STRATEGY_EVOLUTION_SYSTEM_v2.0.0.md
- OBSERVABILITY_LOGGING_SPEC_v2.0.0.md
- GOVERNANCE_AND_CHANGE_CONTROL.md

---

## 1. PURPOSE

This document defines the canonical admin control surface for BinaryBot.

The admin control surface is the operator-facing control plane through which authorized human roles can:

- inspect live operational state
- inspect decision state and signal lifecycle state
- manage symbol activation and operational scope
- manage distribution configuration and publication readiness
- inspect research, analytics, audit and intelligence outputs
- trigger approved operational actions
- access canonical documentation and proof artifacts
- supervise affiliate / distribution / admin activity according to role

This document does **not** define raw permission policy in full detail.  
Detailed permission authority belongs to:

- `ADMIN_OPERATIONS_SPEC_v2.0.0.md`
- `ROLE_AND_PERMISSION_MATRIX_SPEC_v2.0.0.md`
- `CONTROL_PANEL_HIERARCHY_AND_INTELLIGENCE_SPEC_v2.0.0.md`

This document defines **what the admin surface is**, **what sections it exposes**, **what operators can see or trigger from it**, and **what safety rules apply**.

---

## 2. CANONICAL POSITION IN THE SYSTEM

The admin control surface is not the strategy engine and is not the decision engine.

It is a governed operator interface placed above the operational system.

Its role is to expose safe, auditable, role-scoped visibility and control over the following truth domains:

- **Operational Truth**  
  Service health, engine status, queue state, routing state, cooldowns, incidents, freezes, failover and recovery state.

- **Decision Truth**  
  Decision objects, gate outcomes, rejection reasons, readiness state, PRE / CONFIRM / OPEN_NOW transitions, score explanations, feasibility state, SR state, spike state and focus state.

- **Market / Timing Truth**  
  Time windows, corridor state, temporal gating state, session context, timing eligibility and lifecycle timing telemetry.

- **Outcome Truth**  
  Outcome capture status, verdict readiness, win / lose / missed classification state, source confidence and settlement completeness.

- **Research / Learning Truth**  
  Performance analytics, pattern learning, rejection analytics, experiment history, intelligence summaries and evolution recommendations.

- **Distribution Truth**  
  Channel routing, publication permissions, audience tiering, affiliate routing, message formatting state, distribution health and publishing audit state.

The admin surface must expose those truth domains **without collapsing them into one ambiguous dashboard**.

---

## 3. DESIGN PRINCIPLES

The admin control surface must obey the following principles:

### 3.1 Role-scoped visibility
Users only see controls and data that match their role and authority.

### 3.2 No hidden mutation
Every admin action that changes future behavior must be explicit, logged and attributable.

### 3.3 Future-facing control only
Admin actions may affect future behavior, future routing, future readiness or future configuration, but must not silently rewrite historical truth.

### 3.4 Separation of truth domains
Operational truth, decision truth, outcome truth and research truth must remain visibly separated.

### 3.5 Auditability first
Every control action must have a corresponding audit trail, actor identity, timestamp and result state.

### 3.6 Read-only by default
Unsafe write access must never be the default interaction pattern.

### 3.7 Canonical-document-driven control
The panel must reference canonical documents and canonical data models rather than ad hoc operator folklore.

---

## 4. PRIMARY ENTRY POINTS

The admin surface may be reached through one or more delivery interfaces, such as Telegram or a future panel UI, but the canonical logical entry points are:

- **Admin Home**
- **Operations**
- **Symbols & Coverage**
- **Decision Visibility**
- **Distribution Control**
- **Research & Analytics**
- **Intelligence**
- **Affiliate / Partner Oversight**
- **Documentation & Governance**
- **System Health & Recovery**

The Telegram presentation details belong to `TELEGRAM_UX_v2.0.0.md`.  
The hierarchy and role structure belong to `CONTROL_PANEL_HIERARCHY_AND_INTELLIGENCE_SPEC_v2.0.0.md` and `ADMIN_TREE_MAP_v2.0.0.md`.

---

## 5. ADMIN HOME

The admin home is the top-level summary surface.

It must show a concise, role-appropriate overview of:

- current system status
- engine state
- signal pipeline state
- current operational mode
- active coverage scope
- active incidents or freezes
- current focus / readiness highlights
- recent important admin actions
- recent distribution events
- quick links into subordinate panels

The admin home must not attempt to replace specialized panels.  
It is a launch surface and summary layer, not the full operating environment.

---

## 6. OPERATIONS PANEL

The Operations panel exposes the operational control state of the system.

It must contain role-scoped visibility into:

- engine running / paused / frozen state
- watchdog and process health
- restart / recovery indicators
- active incidents
- current cooldown state
- backlog / queue pressure
- publishing status
- active restrictions
- operational notices and warnings

Where authorized by policy, this panel may expose controlled actions such as:

- pause approved future activity
- freeze selected distribution outputs
- disable selected publication pathways
- acknowledge incidents
- trigger approved recovery workflows
- request diagnostics snapshots

The Operations panel must never expose undocumented “magic” controls.

---

## 7. SYMBOLS & COVERAGE PANEL

This panel governs future coverage scope.

It defines what the system is allowed to monitor or publish for future activity.

It may include:

- active symbol list
- disabled symbol list
- scoped symbol groups
- per-market or per-category activation
- coverage limits
- operational notes about broker / venue / support constraints
- readiness restrictions for symbols or groups

Rules:

- changes apply prospectively
- changes must be audited
- removing or disabling a symbol must not rewrite historical decision or outcome records
- symbol availability must be distinct from decision readiness

This panel replaces the simplistic legacy idea of “set symbols because payout looks good” with a governed coverage model.

---

## 8. DECISION VISIBILITY PANEL

This panel exposes the decision pipeline in operator-readable form.

It must allow authorized users to inspect:

- current candidate state
- decision object state
- rejection reasons
- gate results
- score composition
- focus state
- readiness progression
- PRE / CONFIRM / OPEN_NOW lifecycle state
- why something is blocked, delayed, downgraded or rejected

This panel is visibility-first.

It is not a place for arbitrary operator overrides of strategy truth unless a separate governed emergency procedure explicitly allows a documented operational override.

The data shown here must align with:

- `DECISION_AUDIT_SPEC_v2.0.0.md`
- `TRADE_TEMPORAL_TELEMETRY_SPEC_v2.0.0.md`

---

## 9. DISTRIBUTION CONTROL PANEL

This panel governs how approved signals and related outputs are routed.

It may expose:

- channel availability state
- topic / route health
- audience tier eligibility
- publication readiness state
- mute / freeze state per route
- affiliate or partner distribution visibility
- message dispatch audit status
- fallback routing status

This panel does not decide whether a signal is valid.  
It governs where eligible outputs may be sent and under what operational conditions.

This panel must align with:

- `SIGNAL_DISTRIBUTION_SPEC_v2.0.0.md`
- `CHANNEL_CONFIG_SPEC_v2.0.0.md`
- `TELEGRAM_UX_v2.0.0.md`

---

## 10. RESEARCH & ANALYTICS PANEL

This panel provides role-scoped access to research and analytics surfaces.

It may expose:

- signal counts by lifecycle stage
- rejection analytics
- symbol or session performance trends
- outcome distributions
- research summaries
- experiment snapshots
- temporal performance patterns
- affiliate / channel performance summaries where authorized

This panel must be derived from governed data products rather than hand-built guesses.

It must align with:

- `OUTCOME_TRACKING_SPEC_v2.0.0.md`
- `PERFORMANCE_ANALYTICS_SPEC_v2.0.0.md`
- `RESEARCH_AND_LEARNING_FRAMEWORK_SPEC_v2.0.0.md`

---

## 11. INTELLIGENCE PANEL

This panel is for higher-order intelligence outputs.

It may expose:

- strategy intelligence summaries
- anomaly detection summaries
- recommendation queues
- experiment candidate proposals
- approval-needed intelligence items
- learning snapshots
- strategic drift warnings
- change-risk notices

This panel must never auto-modify production behavior merely because a recommendation exists.

It must align with:

- `STRATEGY_INTELLIGENCE_SYSTEM_v2.0.0.md`
- `AUTONOMOUS_STRATEGY_EVOLUTION_SYSTEM_v2.0.0.md`
- `GOVERNANCE_AND_CHANGE_CONTROL.md`

---

## 12. AFFILIATE / PARTNER OVERSIGHT PANEL

Where the affiliate layer exists, the admin surface may expose a dedicated role-scoped area for:

- affiliate account status
- partner routing visibility
- referred-user counts
- commission summaries
- campaign state
- limited support actions
- fraud or abuse indicators
- payout / accrual review status

Affiliate-facing or affiliate-admin-facing visibility must remain strictly limited to their own authorized scope.

This panel must not grant full administrative power to affiliate roles.

---

## 13. DOCUMENTATION & GOVERNANCE PANEL

The admin surface must provide a governed way to access canonical documentation.

It may expose:

- canonical active documents
- implementation matrices
- change-control references
- governance notes
- audit reports
- approved playbooks
- release / version references

Legacy document viewers that point to superseded files such as `ALGO_SPEC.md` or legacy FSM-era documents are non-canonical and must not define current operator truth.

The documentation panel must prioritize canonical-active documents and related governance artifacts.

---

## 14. SYSTEM HEALTH & RECOVERY PANEL

This panel provides visibility into health, failure and recovery status.

It may expose:

- service status
- dependency health
- restart history
- incident history
- degraded-mode status
- recovery steps available to authorized roles
- last successful audit or proof snapshot
- alert acknowledgements

Where policy permits action, recovery controls must be tightly governed and logged.

---

## 15. ROLE-SCOPED VISIBILITY MODEL

The admin control surface must render different sections depending on role.

The canonical role family is no longer the legacy set `OWNER / ADMIN / ANALYST / MODERATOR` shown in the old version.
The current hierarchy must align with the newer multi-layer admin structure already established for BinaryBot governance and affiliate oversight.

At minimum, the system must support the following conceptual roles:

- **Owner**
- **Primary Admin**
- **Functional Admin**
- **Affiliate Admin**
- **Read-only / Analyst-style roles**
- **Support / moderation-style limited roles**, if retained by policy

The exact permission matrix belongs to `ROLE_AND_PERMISSION_MATRIX_SPEC_v2.0.0.md`.

### 15.1 Owner
May view all panels and approve the highest-sensitivity actions allowed by governance.

### 15.2 Primary Admin
May operate the full control surface except owner-reserved governance powers.

### 15.3 Functional Admin
May access only the domains assigned to their function, for example operations, distribution, research or affiliate management.

### 15.4 Affiliate Admin
May access affiliate-specific oversight and only the limited data necessary for the affiliate program.

### 15.5 Read-only and limited roles
May inspect only permitted summaries, documentation or health surfaces.

Invisible controls are preferred over visible-but-forbidden controls when the role should not even know that a capability exists.

---

## 16. ACTION CLASSES

Admin-surface actions fall into the following classes:

### 16.1 Read actions
Inspection only. No state mutation.

### 16.2 Operational controls
Controlled actions that affect future operation, routing or readiness state.

### 16.3 Governance-bound actions
Actions that require stronger approval, justification or dual control.

### 16.4 Emergency actions
Restricted actions available only through documented emergency procedures.

Each action class must be visibly distinguished in the UI/UX.

---

## 17. REQUIRED AUDIT TRAIL FOR ADMIN ACTIONS

Every mutating admin action must record:

- actor identity
- role at time of action
- timestamp
- action requested
- target scope
- justification if required
- approval context if required
- action result
- downstream effect status if known

No undocumented state mutation is allowed.

---

## 18. PROHIBITED BEHAVIORS

The admin control surface must never:

- expose private controls to unauthorized roles
- rewrite historical decision truth
- rewrite historical outcome truth
- bypass readiness gates without a governed emergency procedure
- auto-accept intelligence recommendations into production without change control
- silently alter distribution scope
- mix affiliate scope with unrestricted system-admin power
- rely on superseded documents as current truth
- present research summaries as if they were real-time execution truth

---

## 19. MINIMUM IMPLEMENTATION GUARANTEE

If this specification is implemented correctly, the result is:

- a governed operator control surface
- role-scoped visibility and actionability
- auditable future-facing control
- clean separation between execution truth, outcome truth and research truth
- consistent access to documentation, analytics and operational status
- compatibility with the post-legacy BinaryBot architecture

---

## 20. MIGRATION NOTES FROM LEGACY VERSION

The legacy version defined a simpler Telegram-first panel with:

- legacy roles (`OWNER`, `ADMIN`, `ANALYST`, `MODERATOR`)
- direct buffer-setting concepts
- simplistic symbol toggles
- a documentation viewer centered on superseded files like `ALGO_SPEC.md` and legacy FSM-era specifications, while active canonical analytics must come from `PERFORMANCE_ANALYTICS_SPEC_v2.0.0.md`

This v2.0.0 specification replaces that legacy framing with:

- truth-domain separation
- role-layered governance
- future-facing operational control
- canonical-active document references
- explicit distinction between decision visibility, distribution control, research and intelligence

---

End of ADMIN_CONTROL_SPEC_v2.0.0.md

## 32. Admin UX Merge-Derived Canonical Clarifications

This section absorbs bounded clarifications extracted from ADMIN_UX_V2_SPEC.md.

### 32.1 Canonical UI boundary
Admin UX must remain a presentation/control surface over already-canonical admin and system truths. UI structure must not create alternate ownership of strategy, lifecycle, or routing behavior.

### 32.2 Operator visibility principle
Admin surfaces may aggregate control, observability, analytics, and execution-adjacent views, but any displayed field must map back to active canonical ownership.

### 32.3 No shadow admin truth
Any older admin UX planning material is informative only. Canonical admin truth remains defined by the active admin/control-plane document set.
