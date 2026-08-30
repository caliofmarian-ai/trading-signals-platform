# Owner Knowledge Layer — Implementation Summary

**Base commit:** `6f32f5836f8d25bc7c5e974e22cef27f0140eb84`
**Implementation branch:** `feature/owner-knowledge-layer`
**Scope:** Telegram human-comprehension and operational-memory layer
**Runtime behavior changed:** presentation and navigation only

## Canonical authority

This implementation is anchored to:

- `HUMAN_COMPREHENSION_AND_SELF_EXPLAINING_CONTROL_SURFACE_CANON_v1.0.0.md`
- `ADMIN_SURFACE_AND_CONTROL_PLANE_CANON_v2.0.0.md`
- `ADMIN_CONTROL_SPEC_v2.0.0.md`
- `ADMIN_TREE_MAP_v2.0.0.md`
- `CONTROL_PANEL_HIERARCHY_AND_INTELLIGENCE_SPEC_v2.0.0.md`
- `ROLE_AND_PERMISSION_MATRIX_SPEC_v2.0.0.md`
- the active domain canon named by each registry entry

## Audited pre-change condition

The Telegram implementation already contained a substantial role-scoped application and admin tree, but its human explanations were mostly present only in Python comments and docstrings.

The visible pages still exposed technical names, states, parameters, and values without consistently explaining:

- what the surface represented;
- why it existed;
- where it sat in the pipeline;
- what a control changed;
- what the displayed evidence did not prove;
- which active canonical document owned the meaning.

The Admin Home text also retained a flat command dump even though navigation was already role-scoped.

## Implementation

### Canonical knowledge registry

`send/config/owner_knowledge_registry.json` now provides one versioned,
declarative mapping:

`surface -> explanation -> active canonical owner`

`send/core/owner_knowledge.py` is limited to strict schema validation,
immutable access, aliases, and rendering. Canonical explanatory content is not
embedded across Python handlers. The registry path may be selected through
`OWNER_KNOWLEDGE_REGISTRY_PATH`; invalid or incomplete registry data fails
closed at load time.

Each stable entry contains:

- identity;
- purpose;
- pipeline position;
- available controls;
- consequences;
- limitations;
- important term definitions where applicable;
- active canonical sources;
- public/admin visibility metadata;
- related role-scoped panel actions.

The registry covers:

- Home;
- Status;
- Help;
- Admin Home;
- Operations;
- Engine;
- Strategy;
- Thresholds;
- S/R and Corridor;
- Spike and Instability Filter;
- Symbols and Coverage;
- Decision Visibility;
- Distribution;
- Research and Analytics;
- Intelligence;
- Affiliate and Partner;
- Roles and Identity;
- Files and Reports;
- Governance and Documentation;
- Diagnostics;
- System Health and Recovery;
- Security and Audit.

### Two-layer presentation

Stable pages now expose:

1. an operational summary containing `What this is`, `Why it exists`, an immediate limitation, and a separately labeled `Current state`;
2. a contextual `What is this?` page containing deeper pipeline, control, consequence, limitation, glossary, and canonical-source information.

### Navigation

Public contextual knowledge uses the existing `APP:` navigation model.

Admin contextual knowledge uses the existing `ADMIN_NAV:` model.

Both preserve existing single-message editing behavior and return navigation.

### Role and security boundaries

- Public `APP:` knowledge is limited to Home, Status, and Help.
- Admin knowledge visibility is derived from the same role-scoped panel visibility model as the admin tree.
- Knowledge visibility does not grant mutation authority.
- A forged knowledge callback cannot create a mutation return button.
- Only allow-listed read/navigation return actions are accepted.
- File-browser return routes are limited to canonical short directory keys and numeric pages.
- No credential, token, password, secret value, or protected identity is stored in the registry.

### Admin Home correction

The obsolete flat command dump is removed from the visible Admin Home response.

The page now explains that its buttons are role-filtered and that opening a panel is read-only unless a separate authorized and auditable control is presented.

### No-hardcoded-operational-data rule

`send/core/operational_snapshot.py` now supplies one evidence-backed status
projection to Status, System Health, and Diagnose surfaces.

- runtime values come from `runtime_status`;
- effective feature flags come from explicit configuration;
- FSM mode and coverage come from persisted FSM state;
- an absent FSM artifact remains `UNAVAILABLE` instead of materializing the
  state store's default `WIDE_SCAN` value as observed evidence;
- absent runtime tick evidence and absent engine-event, active-symbol, or
  report artifacts remain explicit evidence gaps rather than becoming interval
  `2`, count `0`, or an empty operational state;
- derived overall `READY` requires reported runtime phase, recovery, and
  market-data readiness evidence;
- derived states are labeled as derived;
- absent or unreadable evidence remains `UNKNOWN` or `UNAVAILABLE`;
- the broker gate reports its effective fail-closed default when configuration
  is absent rather than presenting an invented availability state.

The previous display fallbacks that could imply `HEALTHY`, `DEGRADED`,
`OFF`, or `DISABLED` without enough evidence were removed. Static interface
labels remain presentation structure; they are not current-state observations.

## Preserved boundaries

This implementation does not change:

- strategy calculations;
- score thresholds or their stored values;
- FSM behavior;
- market-data access;
- signal generation;
- distribution routing;
- outcome truth;
- analytics truth;
- broker execution;
- role membership;
- permission checks;
- Telegram session persistence;
- Railway deployment configuration.

## Automated verification

New focused coverage verifies:

- declarative registry loading and schema versioning;
- absence of canonical explanatory prose from the Python loader;
- missing runtime evidence cannot be presented as healthy or ready;
- partial runtime evidence cannot be presented as overall ready;
- missing persisted artifacts remain distinguishable from explicit empty or
  zero-valued artifacts;
- missing shadow-mode evidence remains explicit;
- complete registry materialization;
- all required comprehension fields;
- active canonical-source existence;
- rejection of proposed/deprecated authority;
- Telegram message-size bounds;
- all stable admin-root information buttons;
- parameter-specific explanation routes;
- role-aware knowledge visibility;
- public/admin separation;
- forged-return mutation prevention;
- safe file return routes;
- single-message information callbacks;
- removal of the flat Admin Home command dump.

Full repository result:

`766 passed`

## Remaining live acceptance

Automated repository tests do not prove Railway deployment or live Telegram rendering.

After review and deployment, live acceptance should verify with the Owner account that:

1. Home opens the Admin Control Surface;
2. every visible root panel exposes `What is this?`;
3. the information page edits the same active Telegram message;
4. Back returns to the correct originating page;
5. an unauthorized role cannot reveal a hidden admin branch;
6. no mutation occurs while opening or closing contextual knowledge;
7. restart/redeploy behavior remains consistent with the existing Telegram session model.
