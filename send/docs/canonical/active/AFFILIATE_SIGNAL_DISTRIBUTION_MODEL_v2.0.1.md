# AFFILIATE_SIGNAL_DISTRIBUTION_MODEL_v2.0.1

Version: 2.0.1  
Status: ACTIVE CANONICAL  
Path: /opt/binarybot/docs/canonical/active/AFFILIATE_SIGNAL_DISTRIBUTION_MODEL_v2.0.1.md  
Supersedes: `AFFILIATE_SIGNAL_DISTRIBUTION_MODEL_v2.0.0.md`  

Linked Documents:
- SYSTEM_INVARIANTS_v3.0.0.md
- SYSTEM_ARCHITECTURE_MAP_v3.0.0.md
- MODULE_INTERFACE_SPEC_v3.0.0.md
- GOVERNANCE_AND_CHANGE_CONTROL_v2.0.1.md
- SIGNAL_DISTRIBUTION_SPEC_v2.0.1.md
- SIGNAL_DISTRIBUTION_ARCHITECTURE_v2.0.1.md
- SIGNAL_ECONOMICS_AND_MONETIZATION_MODEL_v2.0.1.md
- TELEGRAM_UX_v2.0.1.md
- PERFORMANCE_ANALYTICS_SPEC_v3.0.0.md
- OUTCOME_TRACKING_SPEC_v3.0.0.md
- DECISION_AUDIT_SPEC_v3.0.0.md
- OBSERVABILITY_LOGGING_SPEC_v3.0.0.md
- DEPLOYMENT_PROTOCOL_v2.0.1.md
- ROLE_AND_PERMISSION_MATRIX_SPEC_v2.0.1.md

Depends on:
- SYSTEM_INVARIANTS_v3.0.0.md
- SYSTEM_ARCHITECTURE_MAP_v3.0.0.md
- MODULE_INTERFACE_SPEC_v3.0.0.md
- GOVERNANCE_AND_CHANGE_CONTROL_v2.0.1.md
- SIGNAL_DISTRIBUTION_ARCHITECTURE_v2.0.1.md
- SIGNAL_ECONOMICS_AND_MONETIZATION_MODEL_v2.0.1.md
- TELEGRAM_UX_v2.0.1.md
- OBSERVABILITY_LOGGING_SPEC_v3.0.0.md

Code Alignment:
- bot_service.py
- core/distribution_router.py
- core/telegram_publisher.py
- core/analytics_engine.py
- core/observability_logger.py
- core/outcome_service.py
- affiliate tracking layer
- subscription / entitlement layer
- referral attribution layer
- affiliate admin surfaces
- reporting/export surfaces

---

## 0. PATCH SCOPE

This successor preserves the complete affiliate participation, attribution, commission, payout, isolation, anti-fraud and governance semantics of v2.0.0.

The patch only updates normative references and version/status/path metadata. It does not grant new affiliate authority, change attribution rules, alter commission semantics, or modify signal/distribution ownership.

Promotion status: ACTIVE CANONICAL under `CANONICAL_ACTIVATION_RECORD_20260901.md` and `CANONICAL_MASTER_INDEX_v2.0.0.md`.

---

## 1. Purpose

This document defines the canonical affiliate signal distribution model for BinaryBot / DROPi Signals.

Its role is to ensure that affiliate-led growth is:
- commercially useful
- operationally controlled
- permission-bounded
- auditable
- isolated from strategy truth
- aligned with the canonical distribution and monetization model

This document does not define signal generation logic, strategy scoring internals, FSM transition rules, Trade Physics mathematics, or observability internals themselves. It defines how external promoters may participate in subscriber acquisition and limited commercial distribution workflows without gaining ownership over strategy or unrestricted operational control.

## 2. Canonical Position

This document sits at the controlled boundary between:
- monetization
- subscriber acquisition
- referral attribution
- affiliate-facing admin surfaces
- limited reporting access
- canonical signal distribution
- governance and permissions

It exists to answer eight questions:

1. What an affiliate is in canonical system terms.
2. What affiliate participation is allowed to do.
3. What affiliate participation is forbidden to do.
4. How affiliates relate to subscription conversion and tier access.
5. What data affiliates may see.
6. What data affiliates must never see.
7. How affiliate activity must be audited and governed.
8. How affiliate growth remains subordinate to architecture, strategy, and runtime truth.

If any affiliate workflow, dashboard, payment model, or promotional process conflicts with active canonical architecture, distribution, permissions, or governance documents, those documents take precedence until this document is updated canonically.

## 3. Final Principle

Affiliates may expand the signal ecosystem commercially, but they must never gain control over strategy truth, hidden system intelligence, or unrestricted operational authority.

Affiliate participation is canonical only when it remains limited to:
- referral acquisition
- subscription attribution
- commercial reporting within owned scope
- approved affiliate dashboard surfaces
- governed commission participation

Affiliate participation becomes non-canonical if it introduces:
- access to strategy internals
- visibility into unrelated user data
- access to observability internals beyond approved affiliate evidence
- authority over runtime routing or signal quality
- hidden privileges outside the role model
- commercial pressure that rewrites canonical distribution truth

## 4. Affiliate Concept

An affiliate is an external promoter or partner who brings users into the BinaryBot / DROPi Signals ecosystem.

Typical affiliate profiles may include:
- trading influencers
- Telegram community owners
- signal-network resellers under approved policy
- trading educators
- community leaders with an audience relevant to the signal product

Affiliates do not create signals.
Affiliates do not own signal quality.
Affiliates do not become strategy operators by virtue of commercial performance.

Their function is acquisition, attribution, and commercial expansion under controlled permissions.

## 5. Canonical Affiliate Role

The affiliate role is a restricted operational-commercial role, not a core strategy or system-control role.

Canonical role label:
- AFFILIATE_ADMIN

This role must be interpreted as:
- limited-scope affiliate operator
- commercial referral participant
- dashboard-limited admin surface user

This role must not be interpreted as:
- full admin
- strategy admin
- observability admin
- deployment operator
- parameter owner
- unrestricted system operator

The AFFILIATE_ADMIN role must remain aligned with `ROLE_AND_PERMISSION_MATRIX_SPEC_v2.0.1.md`.

## 6. Affiliate Position in the Admin Hierarchy

The affiliate role sits below owner-level and primary-admin authority.

Canonical authority principle:
- Owner remains supreme authority.
- Primary admin and approved functional admins control governance and platform operations.
- Affiliate admins are limited-role participants with access only to approved affiliate surfaces.

Affiliate admins are not peers of top-level operational admins.

They may receive a dedicated dashboard or role-bound surface, but that surface must expose only affiliate-relevant information and actions.

## 7. Affiliate Functional Scope

Affiliates may participate in:
- referral link distribution
- audience acquisition
- subscription attribution
- campaign performance review
- commission visibility
- owned-scope subscriber statistics
- limited conversion analytics
- approved promotional tooling

Affiliates must not participate directly in:
- strategy evaluation
- signal scoring
- Trade Physics evaluation
- signal approval
- parameter mutation
- runtime control
- restart control
- deployment execution
- observability-log inspection outside approved summaries
- user management outside their governed scope

## 8. Affiliate Onboarding Model

Canonical affiliate onboarding flow:

1. prospective affiliate requests affiliate participation
2. admin or approved control surface reviews eligibility
3. affiliate record is approved or rejected
4. system assigns a unique affiliate identity
5. referral code or referral link is generated
6. affiliate receives access to approved dashboard surfaces
7. all onboarding actions are audit-visible

Onboarding must be explicit, reversible, and attributable.

No affiliate should exist as an undocumented or manually improvised commercial actor.

## 9. Referral Identity and Attribution

Each affiliate must have a unique canonical referral identity.

Possible canonical attribution fields may include:
- affiliate_id
- affiliate_code
- campaign_id
- source_channel
- created_at
- status
- payout_profile_id
- commission_policy_id

A subscriber entering through an affiliate path must be attributable to the approved referral identity where attribution is valid and accepted.

Attribution must be explicit and auditable rather than inferred loosely from informal marketing claims.

## 10. Referral Link Model

Affiliates may receive referral links or equivalent referral entry mechanisms.

Conceptually:

`https://signals.example/join?ref=AFFILIATE_CODE`

The exact domain or implementation surface may vary, but the canonical model requires:
- unique referral identification
- deterministic capture of referral source where valid
- safe storage of attribution
- alignment with entitlement and subscription logic
- auditability of referral registration events

Referral link mechanics must not bypass permission, privacy, or governance controls.

## 11. Subscriber Attribution Rule

When a user enters the ecosystem through an affiliate path, the system may record:
- affiliate ownership of the referral relationship
- referral timestamp
- initial campaign context where approved
- later subscription conversion linkage where valid
- current commercial status relevant to payouts and reporting

This attribution exists for:
- commission calculation
- growth analytics
- partner accountability
- conversion measurement
- bounded affiliate dashboard visibility

Subscriber attribution is commercial metadata, not strategy metadata.

## 12. Tier Relationship

Affiliate participation is tied to the canonical commercial tier model:
- FREE
- BASIC
- PRO
- ELITE

Affiliates may refer users who later exist in any tier allowed by the active commercial and entitlement model.

Affiliate logic must not redefine tier meaning.

The role of the affiliate model is to:
- attribute who brought the subscriber
- connect conversion to commission logic
- expose approved statistics
- support growth operations

It must not redefine:
- distribution truth
- tier semantics
- signal quality
- lifecycle stage meaning
- routing ownership

## 13. Subscription Conversion Model

When an attributed user later converts to a paid subscription, commission logic may be applied according to approved commercial policy.

Canonical conversion sequence:

Referral acquisition  
→ user enters ecosystem  
→ attribution stored  
→ subscription created or upgraded  
→ conversion associated with affiliate  
→ commission policy applied  
→ ledger updated  
→ reporting surfaces refreshed

This model must remain governed by the active monetization and entitlement truth.

No informal spreadsheet-only process should replace canonical system attribution where the platform claims affiliate governance.

## 14. Commission Model

Commission policy may vary over time, but the architecture of commission participation remains canonical.

Possible commission structures may include:
- percentage share by tier
- flat acquisition bonus
- first-payment-only reward
- lifetime revenue share
- fixed-duration revenue share
- campaign-specific commission policy
- performance-based bonus layer

Exact percentages are business policy and may evolve without requiring architecture rewrite, provided:
- the commission policy remains governed
- the policy is attributable
- the policy is not hidden from authorized review
- payout logic remains auditable
- the policy does not violate broader governance or legal obligations

## 15. Commission Isolation Rule

Affiliate commissions must be calculated from their own attributed subscriber base only.

Affiliates must not gain:
- visibility into other affiliates’ commissions
- visibility into full platform revenue
- visibility into unrelated subscriber conversions
- authority to modify their own commission rules unless explicitly granted through governance and admin control

Commission truth must remain centralized and auditable.

## 16. Affiliate Dashboard Scope

Affiliates may access a limited affiliate dashboard or equivalent reporting surface.

Allowed dashboard categories may include:
- referred users count
- active subscribers count within owned attribution scope
- tier distribution of owned referrals
- subscription conversion rate
- monthly commission totals
- lifetime earnings totals
- payout status
- campaign performance summaries
- approved warning flags related to their own affiliate account

The dashboard must remain role-bounded and isolated.

## 17. Data Isolation Rule

Affiliate data visibility is restricted to owned-scope affiliate data.

Canonical isolation rule:

`affiliate_data_scope = own_referrals_only`

Affiliates must never see:
- users referred by other affiliates
- unrelated subscriber identities
- total system revenue unless explicitly approved in a separate governed reporting context
- system-wide strategy diagnostics
- full observability logs
- admin-only moderation data
- unrelated payment records
- hidden system intelligence outputs
- sensitive strategy-development information

This rule is mandatory, not optional.

## 18. Privacy and Permission Boundary

Affiliate reporting must expose only the minimum information required for legitimate commercial participation.

The platform must not overexpose:
- personal user data
- private operational data
- strategy research data
- admin governance data
- deployment data
- internal incident data

Where user-level affiliate visibility is allowed, it must remain bounded, justified, and aligned with the active permission model and privacy rules.

## 19. Affiliate Admin Events

Affiliate workflows must generate auditable events.

Canonical examples may include:
- affiliate_created
- affiliate_approved
- affiliate_suspended
- referral_registered
- subscription_converted_from_affiliate
- commission_calculated
- payout_generated
- payout_blocked
- fraud_flag_raised
- affiliate_dashboard_accessed

These events must be attributable and structured.

Affiliate events belong to the observability and audit surface, but visibility of raw event detail to affiliates themselves must remain limited according to role boundaries.

## 20. Observability Rule

Affiliate activity must be observable to the platform, not fully observable to the affiliate.

The system must be able to reconstruct:
- who created or approved the affiliate
- what referral code or identity was assigned
- when a referral was registered
- when conversion occurred
- how commission was calculated
- whether payout was issued, held, or rejected
- whether fraud or suspension flags were raised

Observability exists for platform control, auditability, and dispute resolution.

It does not imply unrestricted affiliate access to internal logs.

## 21. Fraud Protection Rule

The affiliate system must include controlled anti-abuse protections.

Potential abuse patterns may include:
- self-referral loops
- fake-account creation
- artificial subscription bursts
- cancellation/rejoin manipulation
- repeated payment abuse
- multi-account farming
- coordinated fraud rings
- referral attribution spoofing

Fraud detection may consider:
- repeated device or IP patterns where legally and operationally allowed
- abnormal velocity
- suspicious subscription timing
- repeated refund/cancellation behavior
- repeated cross-account similarities
- manual admin review triggers

Anti-fraud must remain governed and auditable.

## 22. Suspension and Restriction Rule

Admins must be able to:
- suspend an affiliate
- disable referral links
- freeze commissions pending review
- lock payout issuance
- restrict dashboard access
- mark the affiliate account for investigation

These actions must be governed and auditable.

Affiliate suspension must not require architectural workarounds or undocumented operator behavior.

## 23. Payout Model

Affiliate earnings may accumulate in a governed ledger or equivalent payout-tracking mechanism.

Possible payout rules may include:
- monthly payout cycle
- minimum payout threshold
- hold period before payout
- manual review before release
- dispute hold
- fraud hold
- country or payment-method restrictions
- compliance-based payout validation

Payout processing is part of commercial operations, not part of signal strategy.

## 24. Payout Methods

Approved payout methods may vary based on operational policy.

Possible methods may include:
- bank transfer
- approved digital wallet
- approved crypto payout where legally and operationally allowed
- third-party payment processor
- internal balance or credit model if canonically introduced later

The method itself is not canonical strategy truth.
What is canonical is that payout logic must remain governed, attributable, and auditable.

## 25. Admin Control Surface

Approved admins must be able to control the affiliate program through dedicated surfaces or command pathways.

Allowed admin capabilities may include:
- approve affiliate accounts
- suspend affiliate accounts
- modify affiliate status
- assign or adjust commission policies
- review referral performance
- investigate fraud signals
- release or block payouts
- review dashboard integrity
- export affiliate reports
- correct attribution issues through governed processes

These controls belong to operational governance, not affiliate self-management.

## 26. Relationship to Signal Distribution

Affiliate distribution is a growth and acquisition layer attached to the signal ecosystem.

It is not the same as core signal distribution logic.

Core signal distribution governs:
- which validated SignalEvent candidates are routed
- which tiers receive what governed stage
- how Telegram publication occurs
- how distribution states are tracked
- how routing invariants are enforced

Affiliate distribution governs:
- how users are brought into the ecosystem
- how commercial attribution is captured
- how partner commissions are governed
- how affiliate-limited dashboards are provided

The affiliate model must never override `SIGNAL_DISTRIBUTION_ARCHITECTURE_v2.0.1.md` or `SIGNAL_DISTRIBUTION_SPEC_v2.0.1.md`.

## 27. Relationship to Monetization Model

This document is subordinate to and complementary with `SIGNAL_ECONOMICS_AND_MONETIZATION_MODEL_v2.0.1.md`.

The monetization model governs:
- commercial tier meaning
- premium differentiation boundaries
- entitlement logic
- premium feature framing
- high-level revenue architecture

This affiliate document governs:
- referral participation
- attribution mechanics
- affiliate dashboard scope
- commission and payout architecture
- affiliate permissions and limitations

If the two conflict, both must be aligned canonically before implementation continues.

## 28. Relationship to Role and Permission Model

Affiliate permissions must be implemented through `ROLE_AND_PERMISSION_MATRIX_SPEC_v2.0.1.md`, not through ad hoc exceptions.

The role and permission layer must clearly define:
- what affiliate admins can view
- what affiliate admins can export
- what affiliate admins can request
- what affiliate admins cannot touch
- which approval actions require higher authority

No affiliate capability should exist solely because it is “commercially useful” if it violates the permission hierarchy.

## 29. Relationship to Analytics

Affiliate analytics may interact with:
- acquisition analytics
- conversion analytics
- payout analytics
- retention analytics
- subscriber-tier distribution analytics
- campaign performance analytics

Affiliate analytics must remain commercially scoped.

They must not expose:
- unrelated user strategy outcomes
- hidden system diagnostics
- proprietary internal intelligence models
- raw operational telemetry beyond approved summaries

## 30. Relationship to Outcome and Performance Layers

Affiliate reporting may include high-level outcome-related summaries only where canonically approved and commercially justified.

Examples may include:
- subscriber retention quality
- engagement summaries
- aggregate conversion performance
- aggregate premium retention patterns

Affiliate reporting must not expose raw decision-audit detail, internal strategy reasoning, Trade Physics feature snapshots, model internals, or sensitive outcome internals that belong to system research or eligible user workflows.

## 31. Governance Rule

Changes to affiliate permissions, commission models, attribution logic, payout handling, dashboard scope, or referral identity structure are governance-relevant changes.

If such changes alter:
- permissions
- architecture
- user data visibility
- payout accountability
- runtime-linked entitlement behavior
- admin control logic

then the relevant canonical documents must be aligned before implementation.

Commercial urgency does not bypass governance.

## 32. Deployment Rule

If an affiliate-related change affects runtime behavior, payout processing, entitlement logic, dashboard visibility, or admin controls, it must follow `DEPLOYMENT_PROTOCOL_v2.0.1.md`.

No affiliate-system production mutation is valid if it bypasses:
- documentation-first alignment where required
- backup before mutation
- pre-scan and post-scan
- auditable deployment evidence
- restart verification where runtime is affected
- rollback readiness

Commercial partner operations must remain deployment-safe.

## 33. Future Extensions

Possible future extensions may include:
- campaign-level attribution models
- affiliate leaderboards
- performance-tiered commission programs
- limited team-based affiliate structures
- automated payout integrations
- affiliate asset libraries
- conversion funnel diagnostics
- moderation scoring for affiliate quality
- multi-brand or region-specific affiliate programs

Any future extension must preserve:
- permission boundaries
- attribution integrity
- commercial auditability
- strategy isolation
- canonical naming and governance discipline

## 34. Forbidden Affiliate Drift

The following are non-canonical:

- granting affiliates access to strategy parameters
- exposing internal diagnostics or observability internals without approval
- allowing affiliates to see other affiliates’ users or commissions
- using affiliate status as a path to hidden admin power
- permitting affiliate influence over signal quality or routing truth
- paying commissions through opaque, non-auditable flows while claiming governed operation
- creating undocumented attribution exceptions
- allowing business pressure to weaken permission isolation

Affiliate growth must remain controlled.

## 35. Success Standard

The affiliate model is considered canonically healthy only when:
- affiliates are permission-bounded
- referral attribution is explicit
- commissions are auditable
- payout logic is governed
- dashboards are isolated to owned scope
- strategy truth remains untouched
- canonical distribution remains authoritative
- governance and deployment discipline are preserved

## 36. Final Enforcement Statement

No future affiliate, influencer, referral, or partner-growth change may bypass the rules in this document.

If an affiliate-growth shortcut conflicts with architecture, permissions, governance, monetization truth, or runtime integrity, the shortcut is non-canonical.

Affiliate scale is allowed only inside canonical control, never instead of it.

---

## 37. VERSION HISTORY

| Version | Date | Description |
|---|---|---|
| 2.0.1 | 2026-09-01 | Proposed PATCH successor for canonical reference repair only; affiliate permissions, attribution, commission and payout semantics unchanged. |
| 2.0.0 | 2026-07-12 | Active canonical affiliate model before this proposed patch. |

---

End of AFFILIATE_SIGNAL_DISTRIBUTION_MODEL_v2.0.1.md
