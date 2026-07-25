# CANONICAL_SOURCE_REGISTER.md

BinaryBot — Telegram Application Reconstruction  
Audit: telegram-application-reconstruction-01  
Document: CANONICAL_SOURCE_REGISTER.md  
Status: RECONSTRUCTION AUDIT

---

## PURPOSE

This register records every active canonical document consulted during this reconstruction,
its version, authority area, and relevance to the Telegram application implementation.

---

## DOCUMENT AUTHORITY REGISTER

| Document | Version | Path | Relevance to Telegram Application |
|---|---|---|---|
| TELEGRAM_UX_v2.0.0.md | 2.0.0 | /opt/binarybot/docs/canonical/active/ | **Primary UX authority** — defines all Telegram UX domains, routing model, admin UX, button principles, active message model, role-scoped rendering, signal lifecycle, outcome UX, system alert UX, documentation UX, research UX, access rules |
| ROLE_AND_PERMISSION_MATRIX_SPEC_v2.0.0.md | 2.0.0 | /opt/binarybot/docs/canonical/active/ | **Primary role authority** — defines canonical role family, hierarchy, role definitions (Owner through User), permission domains, least-privilege principle, affiliate isolation |
| ADMIN_TREE_MAP_v2.0.0.md | 2.0.0 | /opt/binarybot/docs/canonical/active/ | **Admin tree structure** — canonical 11-panel root tree, role-panel visibility matrix, sub-tree definitions for each panel |
| ADMIN_CONTROL_SPEC_v2.0.0.md | 2.0.0 | /opt/binarybot/docs/canonical/active/ | **Admin surface detail** — panel contents, operator visibility/control model, guarded action rules |
| ADMIN_OPERATIONS_SPEC_v2.0.0.md | 2.0.0 | /opt/binarybot/docs/canonical/active/ | **Operations panel** — governed operational control procedures |
| ADMIN_SURFACE_AND_CONTROL_PLANE_CANON_v2.0.0.md | 2.0.0 | /opt/binarybot/docs/canonical/active/ | **Root manifest** for admin/control-plane canonical cluster |
| AFFILIATE_SIGNAL_DISTRIBUTION_MODEL_v2.0.0.md | 2.0.0 | /opt/binarybot/docs/canonical/active/ | **Affiliate isolation** — AFFILIATE_ADMIN must not see global admin data; scoped to own program |
| CONTROL_PANEL_HIERARCHY_AND_INTELLIGENCE_SPEC_v2.0.0.md | 2.0.0 | /opt/binarybot/docs/canonical/active/ | **Control panel hierarchy** — intelligence/insight axis, panel authority assignments |
| SIGNAL_DISTRIBUTION_SPEC_v2.0.0.md | 2.0.0 | /opt/binarybot/docs/canonical/active/ | Signal routing; relevant to Distribution panel |
| CHANNEL_CONFIG_SPEC_v2.0.0.md | 2.0.0 | /opt/binarybot/docs/canonical/active/ | Channel configuration; relevant to Distribution panel |
| OUTCOME_TRACKING_SPEC_v2.0.0.md | 2.0.0 | /opt/binarybot/docs/canonical/active/ | Outcome UX rules (single-vote, lock-first, WIN/LOSE/MISSED) |
| PERFORMANCE_ANALYTICS_SPEC_v2.0.0.md | 2.0.0 | /opt/binarybot/docs/canonical/active/ | Research & Analytics panel backend |
| DECISION_AUDIT_SPEC_v2.0.0.md | 2.0.0 | /opt/binarybot/docs/canonical/active/ | Decision Visibility panel; debug/audit surfaces |
| OBSERVABILITY_LOGGING_SPEC_v2.0.0.md | 2.0.0 | /opt/binarybot/docs/canonical/active/ | System Health / Observability panel |
| GOVERNANCE_AND_CHANGE_CONTROL_v2.0.0.md | 2.0.0 | /opt/binarybot/docs/canonical/active/ | Governance actions; approval requirements; Security & Audit panel |
| TEST_PLAN_v2.0.0.md | 2.0.0 | /opt/binarybot/docs/canonical/active/ | Testing standards |

---

## CANONICAL DOCUMENT PRECEDENCE APPLIED

When documents conflict, the following precedence was applied:

1. **TELEGRAM_UX_v2.0.0.md** — primary UX authority; supersedes older UX framing
2. **ROLE_AND_PERMISSION_MATRIX_SPEC_v2.0.0.md** — primary role authority
3. **ADMIN_TREE_MAP_v2.0.0.md** — navigation structure
4. **ADMIN_CONTROL_SPEC_v2.0.0.md** — panel content detail
5. All other documents support the above four

---

## CANONICAL GAPS IDENTIFIED

The following areas were found to have no canonical specification:

| Area | Gap Description |
|---|---|
| /start behavior | TELEGRAM_UX_v2.0.0.md does not specify the exact /start response content or onboarding flow. Implementation follows §16.2 (admin entry) and §15.2 (role-scoped rendering) as the closest applicable guidance. |
| USER-facing interactive menu | ROLE_AND_PERMISSION_MATRIX_SPEC_v2.0.0.md §5.7 defines User as "non-admin consumers of public or paid-facing system outputs" — no interactive control surface specified. Minimum neutral implementation provided. |
| Navigation state persistence | No canonical document specifies that navigation state (active message) must survive bot restarts. In-memory tracking implemented. |
| Member statistics UX | TELEGRAM_UX_v2.0.0.md §29 specifies DM-only access but does not define the full member statistics flow for end users. |

All gaps are recorded in GAPS_AND_IMPLEMENTATION_DECISIONS.md.

---

End of CANONICAL_SOURCE_REGISTER.md
