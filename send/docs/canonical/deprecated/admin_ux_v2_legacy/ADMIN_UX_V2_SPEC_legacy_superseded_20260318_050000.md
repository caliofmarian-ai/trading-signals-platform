# ADMIN_UX_V2_SPEC

Status: Legacy Superseded Reference
Superseded By: ADMIN_CONTROL_SPEC_v2.0.0.md ; ADMIN_OPERATIONS_SPEC_v2.0.0.md ; TELEGRAM_UX_v2.0.0.md ; CONTROL_PANEL_HIERARCHY_AND_INTELLIGENCE_SPEC_v2.0.0.md
Canonical Position: Deprecated; do not use as active truth.

---

# ADMIN_UX_V2_SPEC

## Status
planned

## Purpose

This document defines the canonical Telegram Admin UX v2 for BinaryBot / DROPi Signals.

It replaces the current flat command-list style admin panel with a hierarchical tree UX driven by inline buttons, callback routing, and RBAC-aware visibility.

This is a design and architecture specification only. It does not imply that all described nodes are already implemented in code.

---

## Design goals

1. Owner-first control model
2. Clear tree navigation instead of flat command list
3. RBAC-aware visibility
4. Button-driven interaction for high-frequency admin actions
5. Minimal text input for operational changes
6. Canonical separation between:
   - navigation
   - rendering
   - callback handling
   - permissions
   - state
7. No ambiguity between:
   - available symbols
   - active symbols
   - wide scan selection
   - focus/watchlist symbols
8. Buffer mode must be selectable visually
9. Admin UX must be compatible with Telegram inline keyboard navigation
10. All admin actions must remain auditable

---

## Canonical admin role hierarchy

1. OWNER
2. PRIMARY_ADMIN
3. STRATEGY_ADMIN
4. RESEARCH_ADMIN
5. ANALYST
6. MODERATOR
7. AFFILIATE_ADMIN
8. USER

---

## Visibility principle

Each role sees only the branches it is allowed to access.

### OWNER
Sees all branches.

### PRIMARY_ADMIN
Sees all operational branches except owner-exclusive governance branches.

### STRATEGY_ADMIN
Sees strategy, symbols, buffer, engine diagnostics related to trading logic.

### RESEARCH_ADMIN
Sees research, analytics, intelligence, diagnostics, reports.

### ANALYST
Sees read-only diagnostics, reports, engine status, strategy status.

### MODERATOR
Sees moderation-safe operational status and limited channel visibility.

### AFFILIATE_ADMIN
Sees only affiliate-scoped data and affiliate program tools.

---

## Canonical admin root tree

/admin
- Dashboard
- Strategy
- Symbols
- Engine
- Intelligence
- Distribution
- Reports
- Roles
- Affiliate
- System
- Docs

---

## Node definitions

### 1. Dashboard
Purpose:
- entry point for operator
- summary of system status
- high-level shortcuts

Contains:
- Engine status
- Active buffer mode
- Active symbol count
- Current role
- Last decision summary
- Shortcuts to major branches

### 2. Strategy
Purpose:
- trading logic controls

Contains:
- Thresholds
- SR Buffer
- Spike Filters
- Strategy Status

Subtree:
- Strategy > View Status
- Strategy > Thresholds
- Strategy > SR Buffer
- Strategy > Spike Filters

### 3. Symbols
Purpose:
- visual management of active scan universe

Contains:
- Active Symbols
- Available Symbols
- Toggle state
- Category filters

Subtree:
- Symbols > Forex
- Symbols > Crypto
- Symbols > Active Only
- Symbols > Available Only
- Symbols > Save Selection

Rules:
- operator toggles symbols via buttons
- active symbols are visibly marked
- tree must support pagination if symbol count is large
- no manual typing required for standard selection workflow

### 4. Engine
Purpose:
- operational runtime visibility

Contains:
- Running status
- Tick interval
- Last decision
- Last signal
- Focus state
- Scan mode

Subtree:
- Engine > Status
- Engine > Last Decision
- Engine > Last Signal
- Engine > Focus State
- Engine > Scan State

### 5. Intelligence
Purpose:
- diagnostics and research layer

Contains:
- Signal scores
- Reject reasons
- Decision diagnostics
- Bottlenecks
- Symbol health
- Heatmaps
- Optimizer reports

Subtree:
- Intelligence > Diagnostics
- Intelligence > Reject Reasons
- Intelligence > Symbol Health
- Intelligence > Heatmap
- Intelligence > Optimizer
- Intelligence > Research

### 6. Distribution
Purpose:
- signal publishing visibility and routing checks

Contains:
- Tier routing state
- Daily counters
- Channel targets
- Admin mirror
- Dedup state

Subtree:
- Distribution > Tier Status
- Distribution > Limits
- Distribution > Destinations
- Distribution > Dedup
- Distribution > Routing Diagnostics

### 7. Reports
Purpose:
- reporting and summaries

Contains:
- latest report
- daily strategy audit
- top reject reasons
- avg score

Subtree:
- Reports > Latest Summary
- Reports > Daily Audit
- Reports > Reject Reasons
- Reports > Score Trends

### 8. Roles
Purpose:
- RBAC visibility

Contains:
- My role
- All roles
- Role matrix
- Membership map

Subtree:
- Roles > My Identity
- Roles > Matrix
- Roles > Members
- Roles > Reload

### 9. Affiliate
Purpose:
- affiliate-scoped visibility and program operations

Contains:
- own affiliate scope
- affiliate code
- referrals
- commission visibility
- scoped users

Subtree:
- Affiliate > My Scope
- Affiliate > My Users
- Affiliate > My Metrics

Special rule:
- AFFILIATE_ADMIN must never see unrestricted admin data.

### 10. System
Purpose:
- operational safety visibility

Contains:
- health
- observability
- logs
- restart protections

Subtree:
- System > Health
- System > Observability
- System > Last Errors
- System > Restart Guard

### 11. Docs
Purpose:
- controlled document viewer

Contains:
- canonical docs list
- implementation matrix
- architecture docs

Subtree:
- Docs > Telegram UX
- Docs > Architecture Mapping
- Docs > Master Index
- Docs > Implementation Matrix

---

## Canonical navigation model

Navigation must be callback-based.

Each admin page is a view node with:
- page_id
- title
- body renderer
- button rows
- required permission

Each node must support:
- Back
- Home
- Refresh

Optional:
- Next page
- Previous page
- Toggle
- Apply
- Save

---

## Canonical UX rules

1. /admin opens root dashboard, not a flat command list
2. every major branch opens a dedicated page
3. symbols are managed by click/toggle buttons
4. buffer is selected by click buttons
5. thresholds and numeric parameters may still use controlled text command entry if needed
6. role visibility must be enforced in UI and backend
7. every callback action must be auditable
8. no branch should expose commands the current role cannot use
9. each page must have consistent navigation buttons
10. current selection state must be visually obvious

---

## Canonical Symbols UX

### Required visual states
- selected active symbol
- available but inactive symbol
- category view
- save/apply action

### Required controls
- category switch: FOREX / CRYPTO
- paging
- toggle symbol
- view active only
- save

### Visual convention
- active symbol button prefixed with checked marker
- inactive symbol button prefixed with empty marker

Example:
- ✅ EUR/USD
- ⬜ GBP/USD

---

## Canonical Buffer UX

### Root node
Strategy > Buffer

### Required options
- SMALL
- MEDIUM
- LARGE

### Required behavior
- current active buffer clearly marked
- selecting a buffer updates settings and returns confirmation
- audit proof is written
- role-gated to OWNER / PRIMARY_ADMIN / STRATEGY_ADMIN as policy permits

Example:
- ✅ MEDIUM
- ⬜ SMALL
- ⬜ LARGE

---

## Canonical implementation split

Target modules:

- core/admin_ui.py
- core/admin_navigation.py
- core/admin_callback_handlers.py
- core/admin_views.py
- core/admin_permissions.py
- core/symbol_selector.py
- core/buffer_selector.py

### Responsibilities

#### admin_ui.py
- root UI assembly
- page dispatch entry
- shared keyboard helpers

#### admin_navigation.py
- page ids
- tree structure
- back/home routing
- per-page metadata

#### admin_callback_handlers.py
- callback parsing
- action dispatch
- page transitions
- safe callback execution

#### admin_views.py
- page body rendering
- summaries
- compact view text generation

#### symbol_selector.py
- available symbol universe
- pagination
- toggling
- persistence of active scan symbols

#### buffer_selector.py
- current buffer mode
- selection buttons
- persistence
- audit proof

---

## Canonical backend invariants

1. UI visibility must match RBAC permissions
2. callback actions must not bypass permission checks
3. active symbols must be read from canonical config path only
4. buffer mode must be read from canonical settings path only
5. no root-level legacy symbols/settings file may remain source of truth for UX
6. docs shown in Docs branch must be canonical docs only
7. affiliate-admin views must always remain scoped

---

## Current deviation summary

Current implementation is only partial because:
- /admin currently resolves to a flat text command list
- strategy/symbols/buffer are still mostly command-driven
- callback routing exists only in fragmentary form
- no canonical dashboard exists
- no symbol toggle UX is exposed in runtime
- no buffer selector UX is exposed in runtime
- role-based UI subtree visibility is not fully implemented

---

## Migration principle

Admin UX v2 must be introduced without breaking existing command-based admin control.

Migration order:
1. create canonical tree navigation
2. add dashboard root
3. add buffer selector
4. add symbols selector
5. connect role-filtered branch visibility
6. keep slash commands as fallback during transition
7. retire flat command list after parity is reached



## Deprecation Note

This document has been superseded after bounded extraction into active canonical documents. It must not be used as parallel canonical truth.
