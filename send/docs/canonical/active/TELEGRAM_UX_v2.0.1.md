# TELEGRAM_UX_v2.0.1.md

BinaryBot — Telegram Experience, Routing & Interaction Specification  
Version: 2.0.1  
Status: ACTIVE CANONICAL  
Path: `send/docs/canonical/active/TELEGRAM_UX_v2.0.1.md`  
Supersedes: `TELEGRAM_UX_v2.0.0.md`  

Linked Documents:
- ADMIN_CONTROL_SPEC_v2.0.1.md
- ADMIN_OPERATIONS_SPEC_v2.0.1.md
- ADMIN_TREE_MAP_v2.0.1.md
- CONTROL_PANEL_HIERARCHY_AND_INTELLIGENCE_SPEC_v2.0.1.md
- ROLE_AND_PERMISSION_MATRIX_SPEC_v2.0.1.md
- DECISION_AUDIT_SPEC_v3.0.0.md
- TRADE_TEMPORAL_TELEMETRY_SPEC_v3.0.0.md
- OUTCOME_TRACKING_SPEC_v3.0.0.md
- COMMUNITY_FEEDBACK_AND_PRIVACY_SPEC_v3.0.0.md
- PERFORMANCE_ANALYTICS_SPEC_v3.0.0.md
- SIGNAL_DISTRIBUTION_ARCHITECTURE_v2.0.1.md
- SIGNAL_DISTRIBUTION_SPEC_v2.0.1.md
- CHANNEL_CONFIG_SPEC_v2.0.1.md
- OBSERVABILITY_LOGGING_SPEC_v3.0.0.md
- EVENT_SCHEMA_SPEC_v3.0.0.md
- GOVERNANCE_AND_CHANGE_CONTROL_v2.0.1.md
- HUMAN_COMPREHENSION_AND_SELF_EXPLAINING_CONTROL_SURFACE_CANON_v1.0.1.md

---

## 0. Patch status

Promotion status: ACTIVE CANONICAL under `CANONICAL_ACTIVATION_RECORD_20260901.md` and `CANONICAL_MASTER_INDEX_v2.0.0.md`.

This v2.0.1 successor preserves Telegram UX behavior and repairs canonical references/truth-source wording for the staged-execution + Trade Physics graph.

No route entitlement, signal-generation, strategy, outcome authority, RBAC or broker behavior is changed.

---

## 1. Purpose

Telegram is a governed operational interface for:
- signal delivery;
- community/outcome interaction where eligible;
- admin interaction;
- system alerts;
- documentation access;
- operational/research summaries.

This document governs:
- Telegram message families;
- routing semantics visible at UX level;
- admin/operator interaction flows;
- feedback/outcome-panel presentation;
- anti-spam/dedup UX expectations;
- formatting/message lifecycle;
- role-scoped admin UX.

---

## 2. Telegram Is Interface, Not Architecture

Telegram commands/messages must map to canonical governed actions and truth.

Telegram MUST NOT:
- create strategy validity;
- reinterpret TPS/score/FSM/execution truth;
- bypass Distribution Router;
- bypass permissions/governance;
- turn a SignalEvent candidate into a claimed delivered signal before successful publication;
- collapse telemetry, admin reconciliation and community self-report into one unlabeled outcome.

Presentation may evolve; underlying canonical meaning remains governed by its owner documents.

---

## 3. Canonical Telegram UX Domains

### 3.1 Live Signal UX
Trading-facing stage delivery.

### 3.2 Feedback / Outcome UX
Self-reported or operational interaction attached to eligible signals according to truth-source policy.

### 3.3 System Alert UX
Failures, warnings and critical operational state.

### 3.4 Admin UX
Private, role-scoped operator control/visibility.

### 3.5 Research / Summary UX
Analytics, research and intelligence summaries where authorized.

### 3.6 Documentation UX
Governed delivery of active canonical references and help.

---

## 4. Telegram Routing Model

Conceptual classes:

```text
TELEGRAM ROUTING
├── Live Signal Destinations
├── Feedback / Outcome Interaction Destinations
├── System Alert Destinations
├── Admin / Control Destinations
├── Research / Summary Destinations
└── Documentation Delivery Destinations
```

Exact chat/topic IDs are configuration, not UX authority.

---

## 5. Live Signal UX

Canonical visible trading stages remain:
- PRE
- CONFIRM
- OPEN_NOW

Visible stages for the same trade idea preserve stable signal identity.

Typical visible lifecycle:

`PRE -> CONFIRM -> OPEN_NOW -> governed feedback/outcome surface where eligible`

A stage may be visible only after successful governed publication. Internal FSM acceptance or SignalEvent candidate construction alone is not user-visible proof.

Live destinations remain clean:
- no raw debug dumps;
- no unrelated admin text;
- no uncontrolled spam;
- no contradictory duplicate stages.

---

## 6. Signal Message Families

### 6.1 PRE
Early awareness/watch state. Must not claim final trade-execution readiness.

### 6.2 CONFIRM
Stronger readiness state. Must not falsely claim final execution readiness.

### 6.3 OPEN_NOW
Action-oriented externally visible stage after the governed upstream path and successful distribution publication.

`trade_execution_ready` and Signal Engine execution truth are internal canonical concepts; Telegram text must represent their user-facing meaning without inventing them.

### 6.4 SYSTEM
Operational, non-trading message family and visually distinct from trading stages.

---

## 7. Message Content Principles

### Clarity
Recipient quickly understands stage and meaning.

### No false certainty
No guarantee/profit certainty from confidence, TPS or learned probability.

### Stable field order
Equivalent messages use stable reading order.

### Mobile readability
Messages remain scannable.

### Canonical truth only
No cosmetically inflated state.

### Explainability
When TPS, Trade Physics readiness, score, model probability or another material metric is shown to authorized humans, terminology/help must comply with Human Comprehension canon.

---

## 8. Live Signal Format Expectations

Exact phrasing may evolve.

### PRE
May include:
- stage;
- symbol;
- direction;
- timing indication;
- bounded readiness/confidence summary;
- monitoring semantics.

### CONFIRM
May include:
- stage;
- symbol;
- direction;
- buffer/timing context;
- expiry band where governed;
- strengthened readiness wording.

### OPEN_NOW
May include:
- stage;
- symbol;
- direction;
- execution-relevant expiry/timing;
- bounded confidence/readiness wording;
- action wording appropriate to the route.

Technical Trade Physics components, raw audit payloads and model diagnostics belong in authorized debug/intelligence surfaces, not ordinary live messages unless explicitly designed and explained.

---

## 9. Deduplication and Anti-Spam

Equivalent message emissions are deduplicated using governed identity/stage/timing context.

No duplicate bursts for:
- PRE;
- CONFIRM;
- OPEN_NOW.

No stage inversion should confuse the same active lifecycle unless a controlled correction is clearly explained.

Volatility/instability must not create uncontrolled message storms.

---

## 10. Message Priority

General UX priority remains:
1. critical safety/system alerts;
2. OPEN_NOW;
3. CONFIRM;
4. PRE;
5. lower-priority summaries.

This is a presentation/queue priority principle, not permission to bypass Distribution policy.

---

## 11. System Alert UX

Typical classes:
- engine start/stop;
- guarded restart;
- dependency/API degradation;
- runtime exception;
- state corruption;
- invariant breach;
- freeze entered;
- recovery completed.

Alerts must be actionable enough for operators without leaking secrets and must remain visually distinct from trading stages.

---

## 12. Debug / Technical Transparency UX

Dedicated technical/admin surfaces may expose:
- classical score composition;
- TPS and S/T/P/V components;
- Trade Physics readiness;
- learned probability plus model/readiness provenance when valid;
- gates;
- buffer/time calculations;
- FSM handoff;
- Signal Engine execution result;
- rejection reasons;
- route publication results;
- diagnostic trace summaries.

This domain aligns with:
- `DECISION_AUDIT_SPEC_v3.0.0.md`;
- `TRADE_TEMPORAL_TELEMETRY_SPEC_v3.0.0.md`;
- `OBSERVABILITY_LOGGING_SPEC_v3.0.0.md`;
- `EVENT_SCHEMA_SPEC_v3.0.0.md`.

Debug presentation never becomes a new truth authority.

---

## 13. Feedback / Outcome UX

Telegram may expose governed interaction for eligible OPEN_NOW signals.

The UX must distinguish source/domain:
- community/member feedback -> self-reported truth;
- admin outcome controls -> operational reconciliation truth;
- objective market result -> telemetry-derived truth when shown.

A button surface must not imply that a member vote overwrites market or admin truth.

Preferred attachment model:
- interaction attached to the OPEN_NOW message.

Fallback:
- immediately linked secondary message when Telegram constraints require it.

All interaction preserves signal identity.

---

## 14. Feedback / Outcome Reporting Rules

### 14.1 Delayed activation
Interaction must not open before the applicable expiry/reporting policy allows it.

### 14.2 Bounded reporting window
Window is governed by Outcome/Community Feedback contracts.

### 14.3 Single active member vote
Community feedback follows `(signal_id,user_id)` dedup where applicable.

### 14.4 Operational/admin reconciliation
Admin outcome mutation follows `OUTCOME_TRACKING_SPEC_v3.0.0.md`, not member-vote rules.

### 14.5 Baseline values
WIN / LOSE / MISSED remain available in the relevant truth domains, but storage/presentation must preserve source labels.

### 14.6 Aggregate privacy
Public surfaces show aggregate data only where allowed; no raw member identities.

### 14.7 Integrity
Protect against:
- early/late submission;
- duplicates;
- silent overwrite;
- broken signal identity;
- truth-source conflation.

Aligns with:
- `OUTCOME_TRACKING_SPEC_v3.0.0.md`;
- `COMMUNITY_FEEDBACK_AND_PRIVACY_SPEC_v3.0.0.md`;
- `PERFORMANCE_ANALYTICS_SPEC_v3.0.0.md`.

---

## 15. Admin UX

Admin UX is private and governed.

It supports:
- operational state inspection;
- approved future-facing control actions;
- decision/rejection/Trade Physics inspection;
- research/intelligence views;
- audit/system health;
- active canonical documentation.

Rendering is role-scoped. Opening `/admin` is not authority to see or execute everything.

Admin UX maps to:
- `ADMIN_TREE_MAP_v2.0.1.md`;
- `CONTROL_PANEL_HIERARCHY_AND_INTELLIGENCE_SPEC_v2.0.1.md`;
- `ADMIN_OPERATIONS_SPEC_v2.0.1.md`;
- `ROLE_AND_PERMISSION_MATRIX_SPEC_v2.0.1.md`.

---

## 16. Admin Entry and Navigation

Canonical entry remains `/admin` while Telegram is the control surface.

Expected behavior:
- identify role/scope when appropriate;
- show allowed branches;
- present quick status;
- hide unauthorized branches;
- separate visibility from mutation.

Flat unrestricted command dumps are non-canonical.

---

## 17. Admin Command Families

Illustrative:
- `/admin`
- `/status`
- `/ops`
- `/symbols`
- `/distribution`
- `/decision`
- `/research`
- `/intelligence`
- `/audit`
- `/docs`
- `/help`

Exact commands are implementation/UI details.

Availability remains role-scoped and guarded-action rules apply.

---

## 18. Admin Menu Principles

- show allowed actions only;
- visibly distinguish sensitive mutation from inspection;
- keep read and write surfaces separate;
- allow confirmation/multi-step flow for sensitive actions;
- return clear result state where possible;
- never imply hidden authority through a visible but unauthorized control.

---

## 19. Documentation UX

Telegram may deliver active canonical specs/help to authorized roles.

Rules:
- role-sensitive document access;
- active canon preferred over deprecated/superseded/intake material;
- when old material is shown for provenance it must be labelled historical;
- contextual explanations must not create alternate canon.

---

## 20. Research / Summary UX

Telegram may deliver authorized:
- daily/weekly summaries;
- performance snapshots;
- rejection analysis;
- TPS/Trade Physics analytics;
- model readiness/calibration/drift summaries;
- recommendation summaries;
- affiliate summaries.

Audience scope and privacy remain enforced.

---

## 21. Access Rules

- no public admin mutation;
- no role leakage;
- no hidden mutation behind read views;
- no ambiguous mutation result;
- no private member statistics in public channels;
- no protected model/security data to unauthorized users.

---

## 22. DM-Only Member Statistics and Privacy

Member statistics remain accessible only through authorized DM/private surfaces.

Public requests must be blocked or redirected to private chat.

Channel messages must never expose raw user identifiers or private member statistics.

Admin member-stat access remains role-bounded and must not leak identity into public UX.

---

## 23. Private / Public / Admin Surface Separation

Private member UX, public signal UX and admin/operator UX remain distinct.

Admin actions are control-plane surfaces only and must not be confused with member-facing feedback flows.

Older UX ideas may inform implementation only where consistent with this active canon.

---

## 24. UX Guarantees

Correct Telegram UX provides:
- clear message meaning;
- truthful visible stage progression;
- bounded feedback/outcome interaction;
- explicit truth-source handling;
- role-scoped admin visibility/control;
- reduced duplicate spam;
- clean signal/alert/admin/research separation;
- privacy-safe member statistics;
- canonical alignment.

---

## 25. PATCH Migration Note

v2.0.1 preserves the v2.0.0 Telegram interaction model.

Reference/clarification changes:
- final references to Audit/Telemetry/Outcome/Analytics/Observability v3;
- final references to adjacent admin/distribution/config PATCH successors;
- explicit candidate/publication boundary consistent with staged execution;
- community self-report vs admin reconciliation vs objective telemetry distinction;
- explicit TP/TPS/model metrics as eligible technical/intelligence content only when governed and explained.

No Telegram destination entitlement, route limits, admin permissions, signal-stage rules or broker behavior changes.

---

## 26. Version History

| Version | Date | Description |
|---|---|---|
| 2.0.1 | 2026-09-01 | Proposed PATCH: canonical reference and truth-source vocabulary repair; no Telegram behavioral-policy change. |
| 2.0.0 | 2026-07-12 | Active canonical Telegram UX specification. |

---

End of TELEGRAM_UX_v2.0.1.md