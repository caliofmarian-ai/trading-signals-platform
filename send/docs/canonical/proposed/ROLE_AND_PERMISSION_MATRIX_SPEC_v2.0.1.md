# ROLE_AND_PERMISSION_MATRIX_SPEC_v2.0.1.md

BinaryBot — Role and Permission Matrix Specification  
Version: 2.0.1  
Status: PROPOSED PATCH SUCCESSOR — NOT ACTIVE CANONICAL  
Path: /opt/binarybot/docs/canonical/proposed/ROLE_AND_PERMISSION_MATRIX_SPEC_v2.0.1.md  
Supersession Intent: `ROLE_AND_PERMISSION_MATRIX_SPEC_v2.0.0.md`

Linked Documents:
- ADMIN_CONTROL_SPEC_v2.0.1.md
- CONTROL_PANEL_HIERARCHY_AND_INTELLIGENCE_SPEC_v2.0.1.md
- ADMIN_TREE_MAP_v2.0.1.md
- ADMIN_OPERATIONS_SPEC_v2.0.1.md
- GOVERNANCE_AND_CHANGE_CONTROL_v2.0.1.md
- SIGNAL_DISTRIBUTION_SPEC_v2.0.1.md
- CHANNEL_CONFIG_SPEC_v2.0.1.md
- DECISION_AUDIT_SPEC_v3.0.0.md
- OBSERVABILITY_LOGGING_SPEC_v3.0.0.md

---

## 0. PATCH SCOPE

This successor preserves the role family, permission matrix, action classes, scope model, authorization flow and emergency-access boundaries of v2.0.0.

The patch only updates normative canonical references and version/status/path metadata. No role receives additional access and no existing permission is widened or narrowed by this patch.

Until explicit active promotion, `ROLE_AND_PERMISSION_MATRIX_SPEC_v2.0.0.md` remains authoritative.

---

## 1. PURPOSE

This document defines the canonical role hierarchy, permission domains, visibility scopes and action boundaries for the BinaryBot operational system.

The role and permission model governs:

- who can access which admin surfaces
- who can perform read-only inspection
- who can perform operational control actions
- who can perform governance-bound actions
- who can access decision, observability, research and intelligence outputs
- who can manage distribution scope and publication state
- who can manage affiliate data and affiliate operations
- who can manage user/community functions
- who can approve or execute high-sensitivity changes

This specification must remain aligned with:

- `ADMIN_CONTROL_SPEC_v2.0.1.md`
- `CONTROL_PANEL_HIERARCHY_AND_INTELLIGENCE_SPEC_v2.0.1.md`
- `ADMIN_TREE_MAP_v2.0.1.md`
- `ADMIN_OPERATIONS_SPEC_v2.0.1.md`
- `GOVERNANCE_AND_CHANGE_CONTROL_v2.0.1.md`

This specification replaces the earlier simplified permission framing by introducing:

- role-scoped visibility
- domain-based authority
- action-class separation
- governance-bound approval boundaries
- affiliate isolation from unrestricted system administration
- distinction between operational control and strategic governance

---

## 2. DESIGN PRINCIPLES

The role and permission model must obey the following principles.

### 2.1 Least privilege
A role receives only the minimum authority required for its function.

### 2.2 Separation of domains
Authority in one domain does not automatically grant authority in another.

### 2.3 Read and write separation
Read access does not imply write access.

### 2.4 Governance separation
Operational admins do not automatically inherit governance authority.

### 2.5 Future-facing mutation only
Authorized mutations affect future system behavior and must not silently rewrite historical truth.

### 2.6 Auditability
Every mutating admin action must be attributable, timestamped and logged.

### 2.7 Invisible-by-default for unauthorized capability
When a role should not know that a capability exists, the control should be absent rather than shown as disabled.

### 2.8 Explicit emergency boundaries
Emergency powers must be documented separately and cannot exist as hidden blanket overrides.

---

## 3. CANONICAL ROLE FAMILY

BinaryBot uses a governed multi-layer role model.

The canonical role family is:

- **Owner**
- **Primary Admin**
- **Functional Admin**
- **Affiliate Admin**
- **Analyst / Read-only specialist roles**
- **Support / Moderator-style limited roles**
- **User**

This replaces the legacy flat mental model in which all admin-like authority was treated as roughly equivalent.

---

## 4. ROLE HIERARCHY

Roles are ordered by governance and operational authority, but hierarchy does not mean unlimited inheritance across all domains.

Conceptual hierarchy:

Owner  
↓  
Primary Admin  
↓  
Functional Admin  
↓  
Analyst / Read-only specialist  
↓  
Support / Moderator-style limited roles  
↓  
Affiliate Admin  
↓  
User

Important clarification:

- hierarchy expresses escalation and governance position
- hierarchy does **not** mean every upstream role should routinely perform every downstream task
- affiliate roles are intentionally segregated from unrestricted operational authority
- some domains require explicit grant even for otherwise powerful roles

---

## 5. ROLE DEFINITIONS

### 5.1 Owner

The Owner is the supreme governance authority of the system.

Responsibilities:

- system-wide architectural direction
- strategic governance
- approval of high-sensitivity changes
- supervision of the entire admin hierarchy
- final authority over canonical control policy

Capabilities:

- full visibility across all governed domains
- approval authority for governance-bound actions
- authority to appoint or remove top-level admins according to policy
- access to operational, decision, observability, research, intelligence, distribution and affiliate oversight surfaces
- access to audit artifacts and governance records

Restrictions:

- must still operate through governed and auditable mechanisms
- must not rely on undocumented hidden controls

### 5.2 Primary Admin

The Primary Admin is the highest day-to-day operational controller below the Owner.

Responsibilities:

- supervise day-to-day operations
- coordinate functional admins
- manage operational continuity
- supervise distribution readiness and operational health
- execute approved changes within delegated authority

Capabilities:

- broad operational visibility
- broad operational control across authorized domains
- management of approved future-facing configuration
- access to diagnostics, research and intelligence outputs needed for operations
- limited admin management according to governance policy

Restrictions:

- cannot usurp Owner-reserved governance authority
- cannot silently alter canonical governance rules
- cannot bypass approval requirements where change control applies

### 5.3 Functional Admin

Functional Admins are domain-specific operators.

Typical functional tracks may include:

- Operations Admin
- Distribution Admin
- Monitoring / Observability Admin
- Research Admin
- Affiliate Program Admin
- Support Operations Admin

Capabilities:

- authority limited to the assigned domain(s)
- access to read and write actions only within delegated scope
- visibility into the surfaces required for their function

Restrictions:

- no unrestricted cross-domain authority
- no Owner-level governance authority
- no role-hierarchy mutation unless explicitly granted by policy

### 5.4 Affiliate Admin

Affiliate Admins are operators or partner-facing managers associated with the affiliate / influencer program.

Responsibilities:

- affiliate onboarding workflows
- partner support
- referral performance review
- commission and campaign oversight within assigned scope

Capabilities:

- visibility into affiliate-specific statistics and program data within authorized scope
- access to affiliate-related support tools and reporting surfaces

Restrictions:

- no unrestricted access to strategy internals
- no access to sensitive diagnostics outside affiliate scope
- no access to global admin control
- no access to full-system research or audit surfaces unless explicitly and narrowly granted

### 5.5 Analyst / Read-only Specialist

This role family includes research and read-only specialist functions.

Responsibilities:

- analyze performance
- inspect governed reports
- produce insights for governance and operations
- review audit or observability outputs where authorized

Capabilities:

- read-only access to approved reports, diagnostics or analytics
- export/reporting authority where permitted

Restrictions:

- no mutating operational control
- no strategy parameter changes
- no distribution-control mutation
- no role or governance mutation

### 5.6 Support / Moderator-style Limited Roles

These are limited roles used for community, support or restricted operational assistance.

Capabilities may include:

- user/community moderation
- support workflow visibility
- limited distribution/community actions if policy allows

Restrictions:

- no strategy control
- no system governance powers
- no access to sensitive decision or intelligence internals unless explicitly required

### 5.7 User

Users are non-admin consumers of public or paid-facing system outputs.

Capabilities:

- receive end-user outputs according to their subscription or channel entitlements

Restrictions:

- no admin privileges
- no internal system visibility

---

## 6. PERMISSION MODEL STRUCTURE

Permissions must be defined along four axes:

1. **Role**
2. **Domain**
3. **Action class**
4. **Scope**

A permission grant is valid only when all four dimensions allow it.

Example conceptual grant:

- Role: Functional Admin
- Domain: Distribution
- Action class: Operational control
- Scope: Assigned channels only

Without the correct scope, the action is not authorized.

---

## 7. PERMISSION DOMAINS

The canonical permission domains are:

- **Governance Domain**
- **Operations Domain**
- **Decision Visibility Domain**
- **Distribution Domain**
- **Observability Domain**
- **Research & Analytics Domain**
- **Intelligence Domain**
- **Affiliate Domain**
- **Community / Support Domain**
- **Role & Identity Domain**
- **Documentation Domain**
- **Security Domain**

### 7.1 Governance Domain
Covers change control, approval authority, canonical rule changes and governance-sensitive operations.

### 7.2 Operations Domain
Covers engine state, freeze/pause behavior, operational continuity and approved future-facing operational controls.

### 7.3 Decision Visibility Domain
Covers inspection of decision objects, rejection reasons, lifecycle state and gate explanations.

### 7.4 Distribution Domain
Covers routing, publication readiness, channel state and controlled distribution actions.

### 7.5 Observability Domain
Covers service health, incidents, logs, alerts and diagnostics visibility.

### 7.6 Research & Analytics Domain
Covers performance summaries, outcome analytics, rejection analytics and governed analytical reporting.

### 7.7 Intelligence Domain
Covers higher-order recommendations, anomaly summaries, drift indicators and experiment candidate intelligence.

### 7.8 Affiliate Domain
Covers referral data, commissions, campaign metrics and affiliate support/oversight.

### 7.9 Community / Support Domain
Covers community moderation and limited support workflows.

### 7.10 Role & Identity Domain
Covers role assignment, identity-linked access control and admin hierarchy management.

### 7.11 Documentation Domain
Covers canonical docs, governed playbooks, change logs and implementation references.

### 7.12 Security Domain
Covers sensitive security actions, sensitive audit controls and privileged identity/security operations.

---

## 8. ACTION CLASSES

Permissions must distinguish between action classes.

### 8.1 Read
Inspection only. No state mutation.

### 8.2 Operational control
Controlled state changes that affect future operation, routing or readiness.

### 8.3 Administrative management
Management of users, scoped configurations or assigned operational entities.

### 8.4 Governance-bound
Actions requiring stronger authority, approval, justification or dual control.

### 8.5 Emergency
Special restricted actions available only through documented emergency procedure.

No role may receive broad action authority without class-specific definition.

---

## 9. VISIBILITY POLICY

Visibility must be role-scoped.

Rules:

- a user should see only what their role and scope authorize
- read access to one panel does not imply visibility into all sub-panels
- controls for unauthorized mutating actions should normally be absent
- sensitive intelligence, audit or security surfaces require explicit justification in the permission design
- affiliate users must never see global admin data merely because they are “admins” inside the affiliate program

---

## 10. CANONICAL PERMISSION MATRIX

The table below expresses the default conceptual authority model.  
Detailed implementation may refine scope, but must not exceed this model without governance approval.

| Role | Governance | Operations | Decision Visibility | Distribution | Observability | Research & Analytics | Intelligence | Affiliate | Community / Support | Role & Identity | Documentation | Security |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Owner | Full | Full | Full | Full | Full | Full | Full | Full | Full | Full | Full | Governed Full |
| Primary Admin | Delegated / Limited | Full | Full | Full | Full | Full | Limited to authorized use | Limited as needed | Limited / Assigned | Limited / Delegated | Full | Limited / Delegated |
| Functional Admin | None unless explicitly delegated | Scoped | Scoped Read / Limited Write where applicable | Scoped | Scoped | Scoped | Scoped Read | Scoped only if affiliate function assigned | Scoped | None unless explicitly delegated | Scoped Read | None unless explicitly delegated |
| Affiliate Admin | None | None | None | Affiliate-scope only if policy allows | Very limited | Limited affiliate reporting only | None | Scoped | None | None | Limited affiliate docs | None |
| Analyst / Read-only Specialist | None | Read-only where needed | Read-only | Read-only where needed | Read-only | Read-only / Analytical | Read-only where authorized | None unless assigned | None | None | Read-only | None |
| Support / Moderator-style Limited | None | None or very limited support ops | None or minimal summary only | Very limited if policy allows | Limited status only | None | None | None | Scoped | None | Limited | None |
| User | None | None | None | None | None | None | None | None | None | None | None | None |

Important rules:

- “Full” means subject to audit and existing governance controls.
- “Scoped” means limited to assigned entities, channels, programs or workflows.
- “Limited” means partial authority with explicit boundaries.
- No role below Owner automatically receives unrestricted Governance Domain authority.
- No affiliate role receives unrestricted operational or strategic authority.

---

## 11. DOMAIN-SPECIFIC ROLE NOTES

### 11.1 Strategy and decision truth
Strategy mutation is not a blanket admin right.  
Most roles may inspect decision truth only as needed; actual strategy-governing changes may require governance-bound approval.

### 11.2 Distribution authority
Distribution authority is separate from signal validity.  
A role may control where approved outputs go without possessing the right to alter decision truth.

### 11.3 Research versus intelligence
Research access and intelligence access are related but distinct.  
A role may read performance analytics without having authority over recommendation approval.

### 11.4 Affiliate isolation
Affiliate program access is not a shortcut into system administration.  
Affiliate data must remain fenced.

### 11.5 Role management
Role and identity mutation is highly sensitive and must remain tightly restricted.

---

## 12. SCOPE MODEL

Permissions must be scoped wherever relevant.

Common scope dimensions include:

- assigned channels
- assigned affiliate program entities
- assigned users or cohorts
- assigned operational functions
- assigned documentation classes
- assigned diagnostics surfaces
- assigned regions, symbols or products if such segmentation exists

A permission without scope is invalid when the domain requires scoping.

---

## 13. ROLE STORAGE MODEL

Roles must be stored in persistent governed configuration.

Recommended implementation location:

`/opt/binarybot/config/roles.json`

Illustrative structure:

```json
{
  "owner": [12345678],
  "primary_admin": [23456789],
  "functional_admin": {
    "operations": [34567890],
    "distribution": [],
    "monitoring": [],
    "research": [],
    "affiliate_program": []
  },
  "analyst": [],
  "support": [],
  "affiliate_admin": {
    "partner_alpha": {
      "telegram_id": 45678901,
      "referral_code": "ALPHA01",
      "scope": ["partner_alpha"]
    }
  }
}
```

Implementation may evolve, but must preserve:

- explicit role identity
- explicit scope mapping where relevant
- auditability of role changes

---

## 14. ADMIN ACTION AUTHORIZATION FLOW

Every privileged action must pass a formal authorization flow.

Conceptual flow:

1. request received
2. actor identity resolved
3. role resolved
4. scope resolved
5. action class determined
6. domain determined
7. permission check executed
8. approval requirement evaluated if applicable
9. action allowed or denied
10. result logged

Example rejection language:

`Unauthorized command attempt.`

The system must prefer explicit denial over silent ambiguous failure.

---

## 15. REQUIRED AUDIT FIELDS FOR PERMISSIONED ACTIONS

Every mutating or sensitive privileged action must record at minimum:

- timestamp
- actor identity
- resolved role
- resolved scope
- domain
- action class
- requested action
- parameters or target
- approval context if required
- result
- downstream status if available

This must align with `OBSERVABILITY_LOGGING_SPEC_v3.0.0.md` and related audit documents.

---

## 16. PROHIBITED PERMISSION ANTI-PATTERNS

The system must not:

- grant hidden super-admin behavior outside documented roles
- treat affiliate admins as unrestricted admins
- allow read-only roles to mutate operational configuration
- let operational admins rewrite historical truth
- bypass governance approval with undocumented shortcuts
- expose sensitive panels merely because a role is “trusted”
- conflate distribution control with strategy ownership
- grant role mutation powers casually

---

## 17. EMERGENCY ACCESS RULE

Emergency authority, if implemented, must be:

- explicitly documented
- narrowly scoped
- time-bounded where possible
- fully audited
- consistent with separate emergency procedure documentation

Emergency access must never exist as an invisible permanent privilege.

---

## 18. MIGRATION NOTES FROM LEGACY VERSION

The legacy version had several limitations:

- a flatter role mental model
- a simpler yes/no matrix
- weaker distinction between read, write and governance authority
- insufficient affiliate isolation
- limited domain separation
- implicit assumptions that higher hierarchy automatically meant broader operational reach

The v2.0.0 specification replaced that with:

- domain-based authority
- action-class-aware permissions
- explicit scope boundaries
- governance separation
- role-scoped visibility
- affiliate isolation from unrestricted system administration
- compatibility with the newer admin control architecture

---

## 19. MINIMUM IMPLEMENTATION GUARANTEE

If this specification is implemented correctly, BinaryBot gains:

- auditable authority boundaries
- safer admin operations
- cleaner separation between governance, operations and analysis
- scalable multi-admin structure
- controlled affiliate integration
- stronger compatibility with the post-legacy canonical architecture

---

## 20. VERSION HISTORY

| Version | Date | Description |
|---|---|---|
| 2.0.1 | 2026-09-01 | Proposed PATCH successor for canonical reference repair only; permission semantics unchanged. |
| 2.0.0 | 2026-07-12 | Active canonical role/permission model before this proposed patch. |

---

End of ROLE_AND_PERMISSION_MATRIX_SPEC_v2.0.1.md
