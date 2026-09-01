# ADMIN_SURFACE_AND_CONTROL_PLANE_CANON_v2.0.1

**Canonical Name:** ADMIN_SURFACE_AND_CONTROL_PLANE_CANON  
**Version:** 2.0.1  
**Status:** ACTIVE CANONICAL
**Owner:** BinaryBot / DROPi Signals  
**Canonical Path:** `send/docs/canonical/active/ADMIN_SURFACE_AND_CONTROL_PLANE_CANON_v2.0.1.md`  
**Governance Record:** canonical-reconciliation-01 (OWNER-007 = A)  
**Supersedes:** `ADMIN_SURFACE_AND_CONTROL_PLANE_CANON_v2.0.0.md`
**Scope:** Canonical root manifest for the admin/control-plane specification cluster. Defines the human/operator control plane: Owner authority, hierarchical admin layers, Telegram admin interface relation, observability consumption, affiliate/admin segmentation, and separation between truth, control, execution, delivery and governance surfaces.

**Predecessor / Superseded Documents:**
- `send/docs/canonical/superseded/ADMIN_SURFACE_AND_CONTROL_PLANE_CANON_v2.0.0.md` — superseded predecessor after the executed 2026-09-01 promotion of this patch successor.
- `send/docs/canonical/proposed/ADMIN_SURFACE_AND_CONTROL_PLANE_CANON_v1.0.0.md` — proposed historical source.

---

## 0. PATCH SCOPE

This successor preserves the authority hierarchy and human-control-plane semantics of v2.0.0.

The patch:
- updates all normative links to the active successor filenames established by the Trade Physics + staged-execution promotion;
- updates this document's version/status/path metadata;
- clarifies the already-governed delivery ownership boundary so Signal Engine handoff/candidate construction is not described as external delivery.

It does not change Owner authority, admin roles, permissions, control-plane hierarchy, distribution policy, strategy truth, or publication entitlement.

Promotion status: ACTIVE CANONICAL under `CANONICAL_ACTIVATION_RECORD_20260901.md` and `CANONICAL_MASTER_INDEX_v2.0.0.md`.

---

## CLUSTER AUTHORITY DECLARATION

This document is the **root manifest** for the admin/control-plane specification cluster of BinaryBot / DROPi Signals. It is the canonical authority on the structure, hierarchy, and authority relationships of the human control plane.

The following documents are subordinate members of this cluster. They govern their respective implementation domains and must not contradict this root manifest:

| Document | Role within cluster | Authority scope |
|---|---|---|
| `ADMIN_CONTROL_SPEC_v2.0.1.md` | Primary implementation spec | Admin command surface, command validation, role enforcement, Telegram control interface |
| `ADMIN_OPERATIONS_SPEC_v2.0.1.md` | Operations spec | Day-to-day operational procedures, runbook-style admin actions, operational state transitions |
| `ADMIN_TREE_MAP_v2.0.1.md` | Structural map | Hierarchical map of the admin control surface, topic/command routing layout |
| `CONTROL_PANEL_HIERARCHY_AND_INTELLIGENCE_SPEC_v2.0.1.md` | Intelligence integration | Control panel structure, intelligence layer consumption, display and drill-down surfaces |
| `ROLE_AND_PERMISSION_MATRIX_SPEC_v2.0.1.md` | Permission authority | Role definitions, permission matrix, access boundaries for each role |
| `STRATEGY_PARAMETER_CONTROL_SPEC_v3.0.0.md` | Parameter governance | Admin authority over strategy parameters, controlled parameter change procedures |

**Ordering of authority within the cluster:**

1. This root manifest (`ADMIN_SURFACE_AND_CONTROL_PLANE_CANON_v2.0.1.md`) — establishes architectural principles and hierarchy; governs when cluster members conflict.
2. `ROLE_AND_PERMISSION_MATRIX_SPEC_v2.0.1.md` — governs role definitions and access control for all other cluster members.
3. `ADMIN_CONTROL_SPEC_v2.0.1.md` — governs the command surface and Telegram control interface.
4. `ADMIN_OPERATIONS_SPEC_v2.0.1.md` — governs operational procedures within constraints set by ADMIN_CONTROL_SPEC.
5. `ADMIN_TREE_MAP_v2.0.1.md` — maps the structural layout; must be consistent with ADMIN_CONTROL_SPEC and ADMIN_OPERATIONS_SPEC.
6. `CONTROL_PANEL_HIERARCHY_AND_INTELLIGENCE_SPEC_v2.0.1.md` — governs display and intelligence integration within the control surface.
7. `STRATEGY_PARAMETER_CONTROL_SPEC_v3.0.0.md` — governs parameter changes; must comply with role restrictions in ROLE_AND_PERMISSION_MATRIX_SPEC.

**No cluster member may:**
- Declare a role hierarchy that contradicts this document or `ROLE_AND_PERMISSION_MATRIX_SPEC_v2.0.1.md`.
- Define admin command behavior that contradicts `ADMIN_CONTROL_SPEC_v2.0.1.md`.
- Establish parameter change procedures that contradict `STRATEGY_PARAMETER_CONTROL_SPEC_v3.0.0.md`.
- Create authority relationships between the machine truth plane and the human control plane that contradict Section 3 of this document.

---

Depends on:

- `send/docs/canonical/active/CANONICAL_STRATEGY_STACK_v2.0.0.md`
- `send/docs/canonical/active/ALGO_SPEC_v3.0.0.md`
- `send/docs/canonical/active/DECISION_OBJECT_CANONICAL_SPEC_v2.0.0.md`
- `send/docs/canonical/active/FSM_DECISION_ENGINE_SPEC_v2.0.0.md`
- `send/docs/canonical/active/SR_CORRIDOR_ENGINE_SPEC_v3.0.0.md`
- `send/docs/canonical/active/TIME_MODEL_UNIFIED_CANON_v3.0.0.md`
- `send/docs/canonical/active/TRADE_PHYSICS_MODEL_SPEC_v1.0.0.md`
- `send/docs/canonical/active/SIGNAL_ENGINE_EXECUTION_SPEC_v3.0.0.md`
- `send/docs/canonical/active/OBSERVABILITY_SPEC_v3.0.0.md`
- `send/docs/canonical/active/GOVERNANCE_AND_CHANGE_CONTROL_v2.0.1.md`
- `send/docs/canonical/active/AFFILIATE_SIGNAL_DISTRIBUTION_MODEL_v2.0.1.md`
- `send/docs/canonical/active/SECURITY_MODEL_v2.0.1.md`

---

## 1. PURPOSE

This document defines the canonical root for the human control and operations surface of BinaryBot / DROPi Signals.

Its purpose is to establish, in a single source of truth:

- Who holds supreme authority
- What administrative layers exist
- What each layer can see
- What each layer can control
- How the surfaces of truth, control, and execution are separated
- How the admin surface consumes data from observability
- How Telegram admin integrates as an operational interface
- How affiliate / influencer admin integrates
- How research / AI / reporting tooling integrates
- How non-canonical mixing of strategy, execution, and human control is prevented

This document does not redefine the strategy, FSM, Signal Engine, Distribution, or Observability.

It defines **how those truths and capabilities are consumed, exposed, and controlled by humans**.

---

## 2. WHY THIS DOCUMENT EXISTS

In historical documentation, the following appeared separately and sometimes overlapping:

- Admin control specs
- Admin operations specs
- Telegram UX / command docs
- Dashboard / debug specs
- Distribution / channel control docs
- Affiliate distribution notes

These documents remain useful, but without a root canon for the control plane, the following inevitably emerge:

- Authority overlaps
- Unclear roles
- Excessive access
- Inconsistent interfaces
- Mixing of truth display and command execution
- Confusion between observability and chat notifications
- Lack of a canonical hierarchy for Owner, admins, and affiliate roles

This document exists to unify and lock the architectural truth of the human control surface.

---

## 3. FUNDAMENTAL PRINCIPLE

BinaryBot has two distinct but connected worlds:

1. **Machine truth plane**
2. **Human control plane**

The machine truth plane contains the system's truth:

- Market model
- Corridor engine
- Time model
- Scoring and deterministic Trade Physics evidence
- `DecisionObject`
- FSM
- Signal engine execution truth
- Distribution/publication truth
- Observability traces

The human control plane contains:

- Display surfaces
- Operational controls
- Administrative governance
- Audit views
- Analysis and reporting tooling

**The human control plane must not informally rewrite the canonical truth produced by the machine truth plane.**

It may:

- Read it
- Filter it
- Expose it
- Control it at the level of policy and operations
- Investigate it
- Apply explicitly permitted overrides

But it must not become a parallel source of strategic truth.

---

## 4. CORE CANONICAL SEPARATION

From this document forward, the mandatory canonical separation is:

### 4.1 Truth Layer

The system's semantic and operational truth lives here:

- Strategy outputs
- Structural truth
- Time truth
- Score / Trade Physics truth
- `DecisionObject`
- FSM operational truth
- Signal-execution truth
- Distribution/publication truth
- Observability truth

### 4.2 Display Layer

Surfaces that display truth live here:

- Admin dashboard
- Telegram admin views
- Health summaries
- Debug drill-down
- Audit summaries
- Affiliate stats surfaces
- Reporting surfaces

### 4.3 Control Layer

Commands and policies live here:

- Channel enable / disable
- Routing rules
- Admin permissions
- Role-based controls
- Operational cooldowns
- Maintenance mode
- Guardrails
- Symbol activation policies
- Distribution controls

### 4.4 Delivery Layer

Actual external publication to destinations lives here:

- Signal Engine handoff of a validated SignalEvent candidate
- Distribution Router route selection and policy application
- Publisher transport execution
- Channel orchestration
- Outbound notification surfaces
- Affiliate delivery segmentation

Signal Engine candidate construction or handoff is not by itself external delivery or `EMITTED` proof.

### 4.5 Governance Layer

Rules of change and authority live here:

- Owner authority
- Approval rules
- Change control
- Audit requirements
- Rollback authority
- Protected controls

These layers are connected but must not be confused.

---

## 5. OWNER PRINCIPLE

The Owner is the supreme level of the system.

In the context of this project, the Owner is the final human authority over:

- Approved strategy
- Canonical documentation
- Control plane governance
- Activating or deactivating major capabilities
- Administrative structure
- Affiliate program
- Distribution policies
- Research and AI priorities
- Product direction

The Owner is not merely a "larger" admin. The Owner is the final instance of authority.

Any hierarchical model must begin from this truth.

---

## 6. CANONICAL HUMAN CONTROL HIERARCHY

The canonical hierarchy of the control plane is:

1. **Owner**
2. **Primary Admin**
3. **Functional Admins**
4. **Affiliate / Influencer Admin**
5. **Research / AI / Reporting Operators**
6. **Read-only / Audit Observers** (optional, if required by system)

This order defines the official hierarchy of the human control surface.

Role-level details (permissions, command access, restrictions) are governed by `ROLE_AND_PERMISSION_MATRIX_SPEC_v2.0.1.md`.

---

## 7. ADMIN SURFACE COMPONENTS

The admin surface consists of:

### 7.1 Telegram Admin Interface

The primary operational control surface.

- Built on Telegram groups with topic segregation
- Owner and admin roles interact via defined commands
- Command validation is governed by `ADMIN_CONTROL_SPEC_v2.0.1.md`
- Topic layout is governed by `ADMIN_TREE_MAP_v2.0.1.md`

### 7.2 Debug and Health Dashboard

A specialized read-only display surface for system state.

- Governed by `CONTROL_PANEL_HIERARCHY_AND_INTELLIGENCE_SPEC_v2.0.1.md`
- Must not allow command execution
- Must consume observability truth from `OBSERVABILITY_SPEC_v3.0.0.md` and `OBSERVABILITY_LOGGING_SPEC_v3.0.0.md`

### 7.3 Strategy Parameter Control

Controlled parameter update surface.

- Governed by `STRATEGY_PARAMETER_CONTROL_SPEC_v3.0.0.md`
- Changes require role authorization per `ROLE_AND_PERMISSION_MATRIX_SPEC_v2.0.1.md`
- All parameter changes must be logged and auditable

### 7.4 Affiliate Admin Surface

A segmented view for affiliate and influencer roles.

- Governed by `AFFILIATE_SIGNAL_DISTRIBUTION_MODEL_v2.0.1.md`
- Must not expose internal truth plane data beyond explicitly authorized summaries
- Access restricted to affiliate-scoped distribution and performance metrics

### 7.5 Operations Surface

Runbook-style operational controls.

- Governed by `ADMIN_OPERATIONS_SPEC_v2.0.1.md`
- Includes freeze, restart, channel management, and maintenance procedures

---

## 8. OBSERVABILITY CONSUMPTION RULES

The human display/control plane consumes canonical observability truth rather than inventing its own alternative truth.

Rules:

- Admin views must read from canonical observability sources
- No admin surface may create alternative truth from raw code inspection
- Observability data is governed by `OBSERVABILITY_SPEC_v3.0.0.md` (policy) and `OBSERVABILITY_LOGGING_SPEC_v3.0.0.md` (implementation)
- Admin cannot override observability conclusions; it can only act on them through governed controls
- Mutating admin actions may cause the observability subsystem to record audit evidence, but the UI itself is not an alternate observability authority

---

## 9. AFFILIATE AND ADMIN SEGMENTATION

The affiliate layer is a bounded commercial/distribution participant, not a global control-plane authority.

Rules:

- Affiliates may view their own distribution performance metrics
- Affiliates may not access internal strategy, FSM, or scoring data except explicitly authorized non-sensitive summaries
- Affiliate admin functions are governed by `AFFILIATE_SIGNAL_DISTRIBUTION_MODEL_v2.0.1.md`
- No affiliate role may hold unrestricted/global admin permissions outside its governed affiliate scope

---

## 10. CHANGE CONTROL FOR CONTROL PLANE MODIFICATIONS

Any modification to the human control plane must comply with `GOVERNANCE_AND_CHANGE_CONTROL_v2.0.1.md`.

Protected controls (Owner-only changes):

- Role hierarchy structure
- Owner authority declarations
- Canonical document status changes
- Major capability activations/deactivations

Admin-level controls (require authorized admin role and scope):

- Symbol activation/deactivation
- Channel routing changes
- Operational mode changes (freeze, maintenance)

---

## 11. FORBIDDEN CONTROL PLANE PATTERNS

The following are forbidden as active canonical patterns:

- Telegram treated as the primary source of truth
- Admin panel treated as the place where signals are "redefined"
- Affiliate admin with complete global access
- Roles without clear authority boundaries
- Views that combine strategic truth with execution in an opaque blob
- Absence of audit trail for critical controls
- Hidden or unexplained overrides
- Health defined only as "bot responds"
- Shadow truth produced manually instead of from observability
- Control commands without a clear role and without logging

---

## 12. CODE ALIGNMENT RULE

Any implementation of the control plane must be able to clearly answer:

- Where is the role hierarchy defined?
- What can each role see?
- What can each role control?
- How is display separated from control?
- How does the dashboard and Telegram consume observability truth?
- How are critical commands protected?
- How is each relevant action audited?
- How is the affiliate layer segmented?
- How is the research / AI / reporting layer integrated?
- How is shadow truth avoided?

If these answers are not clear, code alignment is incomplete.

---

## 13. IMPLEMENTATION PRINCIPLE

From this version forward:

- Any patch to the admin panel must be anchored to this document
- Any patch to the Telegram admin interface must be anchored to this document
- Any patch to affiliate admin must be anchored to this document
- Any patch to health / debug / audit surfaces must be anchored to this document
- Any new administrative role must be explicitly defined here or in a subordinate document aligned with this canon

No new document may separately redefine the primary human hierarchy without explicit reference to this canon.

---

## 14. FINAL PRINCIPLE

BinaryBot / DROPi Signals is not merely a signals bot. It is a system with internal semantic truth and human surfaces for control, audit, and governance.

Therefore, the canonical control plane must be:

- Hierarchically clear
- Separated from the truth plane
- Separated from the delivery plane
- Auditable
- Role-based
- Compatible with observability
- Compatible with affiliate segmentation
- Compatible with research / AI / reporting
- Secure from a privileges perspective
- Sufficiently structured for admin panel and Telegram admin

This is the canonical root document for the Admin Surface and Human Control Plane.

---

## 15. HUMAN COMPREHENSION AND OPERATIONAL MEMORY

All stable human-facing control surfaces governed by this canon MUST comply with `HUMAN_COMPREHENSION_AND_SELF_EXPLAINING_CONTROL_SURFACE_CANON_v1.0.1.md`.

The control plane MUST NOT depend on remembered chat history, operator folklore, developer memory, or unexplained technical terminology for correct human interpretation.

Presentation MUST remain traceable to active canonical ownership and MUST NOT become an alternate source of strategy, execution, analytics, permission, or governance truth.

---

## 16. CANONICAL VERSION HISTORY

| Version | Date | Description |
|---|---|---|
| 2.0.1 | 2026-09-01 | Proposed PATCH successor for canonical reference repair and execution/delivery ownership wording clarification; control-plane authority semantics unchanged. |
| 2.0.0 | 2026-07-12 | Promoted to active canonical status as root manifest for admin/control-plane cluster (OWNER-007 = A, canonical-reconciliation-01). |
| 1.0.0 | — | Proposed document: `send/docs/canonical/proposed/ADMIN_SURFACE_AND_CONTROL_PLANE_CANON_v1.0.0.md` |

---

*End of ADMIN_SURFACE_AND_CONTROL_PLANE_CANON_v2.0.1.md*
