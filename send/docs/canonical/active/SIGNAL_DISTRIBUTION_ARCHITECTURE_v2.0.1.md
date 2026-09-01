# SIGNAL_DISTRIBUTION_ARCHITECTURE_v2.0.1

Version: 2.0.1  
Status: ACTIVE CANONICAL  
Path: `send/docs/canonical/active/SIGNAL_DISTRIBUTION_ARCHITECTURE_v2.0.1.md`  
Supersedes: `SIGNAL_DISTRIBUTION_ARCHITECTURE_v2.0.0.md`  

---

**SCOPE AND AUTHORITY DECLARATION (OWNER-003 — canonical-reconciliation-01, reference-aligned 2026-09-01)**

This document and `SIGNAL_DISTRIBUTION_SPEC_v2.0.1.md` address complementary, non-overlapping domains within signal distribution.

**This document governs exclusively:**
- routing topology and architectural structure of the distribution layer;
- channel architecture and delivery-surface segmentation/mapping;
- distribution module relationships;
- boundaries between distribution and adjacent layers;
- router and publisher ownership;
- failure/retry/degraded-delivery architecture;
- canonical authorization boundaries for distribution paths.

**This document does not govern** entitlement rules, delivery-tier eligibility, stage-specific commercial routing policy, daily limits, or reset behavior. Those belong to `SIGNAL_DISTRIBUTION_SPEC_v2.0.1.md`.

Where ambiguity arises:
- topology/boundaries/module ownership -> this document;
- entitlement/commercial routing/delivery policy -> `SIGNAL_DISTRIBUTION_SPEC_v2.0.1.md`.

---

Linked Documents:
- `SYSTEM_INVARIANTS_v3.0.0.md`
- `SYSTEM_ARCHITECTURE_MAP_v3.0.0.md`
- `MODULE_INTERFACE_SPEC_v3.0.0.md`
- `SIGNAL_ENGINE_EXECUTION_SPEC_v3.0.0.md`
- `SIGNAL_DISTRIBUTION_SPEC_v2.0.1.md`
- `EVENT_SCHEMA_SPEC_v3.0.0.md`
- `TELEGRAM_UX_v2.0.1.md`
- `OBSERVABILITY_LOGGING_SPEC_v3.0.0.md`
- `DECISION_AUDIT_SPEC_v3.0.0.md`
- `OUTCOME_TRACKING_SPEC_v3.0.0.md`
- `PERFORMANCE_ANALYTICS_SPEC_v3.0.0.md`
- `GOVERNANCE_AND_CHANGE_CONTROL_v2.0.1.md`
- `STRATEGY_INTELLIGENCE_SYSTEM_v3.0.0.md`
- `AUTONOMOUS_STRATEGY_EVOLUTION_SYSTEM_v3.0.0.md`

Depends on:
- `SYSTEM_INVARIANTS_v3.0.0.md`
- `MODULE_INTERFACE_SPEC_v3.0.0.md`
- `SIGNAL_ENGINE_EXECUTION_SPEC_v3.0.0.md`
- `SIGNAL_DISTRIBUTION_SPEC_v2.0.1.md`
- `EVENT_SCHEMA_SPEC_v3.0.0.md`
- `TELEGRAM_UX_v2.0.1.md`
- `OBSERVABILITY_LOGGING_SPEC_v3.0.0.md`

Code Alignment:
- core/signal_engine.py
- core/distribution_router.py
- core/telegram_publisher.py
- core/fsm_runtime.py
- core/observability_logger.py
- core/outcome_service.py
- core/analytics_engine.py
- bot_service.py
- distribution configs
- channel/topic mapping configs
- admin routing surfaces

---

## 0. Purpose

This document defines the canonical signal distribution architecture for BinaryBot / DROPi Signals.

Its role is to define how canonical signal-event candidates move from the internal strategic/execution runtime into external delivery surfaces while preserving entitlement policy, routing discipline, restart safety, observability proof and operational control.

This document does not define strategy scoring, Trade Physics mathematics, FSM transition rules, Signal Engine execution outcomes, or Telegram message copy. It defines distribution topology, ownership boundaries, delivery pathways, routing constraints and safety rules.

---

## 1. Canonical Position

Distribution sits downstream of Signal Engine candidate release and upstream of external publishing.

It exists to answer:
1. what upstream objects are eligible to enter distribution;
2. which module owns route selection;
3. which delivery surfaces exist;
4. how route/topic/channel selection is organized;
5. how duplicate/invalid delivery is prevented;
6. what proof must exist for route/publish actions;
7. how failures/retries/degraded delivery are handled;
8. how affiliate/admin/public surfaces remain separated from core strategy ownership.

If runtime behavior conflicts with this architecture, implementation must be corrected or canon must be changed through governance before architecture changes proceed.

---

## 2. Final Principle

No signal stage may be delivered externally unless its path is canonically authorized, state-valid, entitlement-valid, observable and bounded by module ownership.

Non-canonical behavior includes:
- external delivery without a canonical upstream candidate;
- channel/topic routing outside declared policy;
- bypass of the distribution router;
- publishing without observability proof;
- duplicate/replay publication without canonical justification;
- affiliate/admin access to restricted internal surfaces;
- hidden coupling between strategy mathematics and delivery presentation;
- direct publish policy inside the wrong module boundary.

---

## 3. Distribution Scope

This architecture applies to:
- PRE distribution;
- CONFIRM distribution;
- OPEN_NOW distribution;
- RESULT/closure distribution where governed;
- route/tier segmentation;
- channel/topic mapping;
- publisher invocation;
- retry/failure handling;
- delivery observability;
- restart-safe re-entry;
- admin-controlled routing surfaces;
- affiliate-adjacent surfaces;
- future compatible external delivery abstractions.

Volume does not alter the obligation to respect canonical routing.

---

## 4. Position in Runtime Pipeline

The aligned high-level distribution path is:

```text
Market Data
→ Strategy Runtime
→ DecisionObject
→ FSM Runtime
→ Signal Engine
→ governed SignalEvent candidate
→ Distribution Router
→ Route / Topic Policy Filter
→ Publisher Abstraction
→ External Delivery Surface
→ User Consumption
→ Telemetry / Outcome / Analytics surfaces
```

This PATCH makes explicit a boundary already governed by the staged-execution successors:
- Signal Engine owns candidate construction/execution truth;
- Distribution Router consumes governed candidates;
- candidate construction is not publication;
- Distribution remains downstream and does not redefine strategy/FSM/Trade Physics truth.

---

## 5. Canonical Distribution Objects

Distribution may act only on canonical upstream objects and state, including:
- a governed `SignalEvent` candidate released by Signal Engine;
- stable signal identity and stage;
- FSM/Decision correlation carried through upstream contracts;
- distribution state/message registry where persisted;
- route/topic/channel mapping configuration;
- route-level observability state;
- outcome-linked references for later closure publication.

Distribution MUST NOT reconstruct strategy validity, TPS, DecisionObject mathematics or FSM acceptance from raw market data.

---

## 6. Externally Relevant Lifecycle States

The externally relevant lifecycle family remains:
- PRE;
- CONFIRM;
- OPEN_NOW;
- RESULT/closure where governed.

### 6.1 PRE
Early external awareness. Publication remains subject to route entitlement and policy.

### 6.2 CONFIRM
Stronger lifecycle state. A formatted message alone never establishes eligibility; distribution consumes an upstream governed candidate.

### 6.3 OPEN_NOW
Most operationally sensitive trading stage. Routing must be tightly controlled, deduplicated, observable and restart-safe.

### 6.4 RESULT / closure
Closure publication must preserve identity continuity with the prior visible signal lifecycle and the canonical outcome/telemetry truth source being presented.

---

## 7. Access Segmentation

Distribution supports governed entitlement segmentation such as:
- FREE;
- BASIC;
- PRO;
- ELITE;
- internal/admin observation surfaces;
- scoped affiliate/reporting surfaces.

Commercial names and entitlement mechanics are governed by Distribution Policy/Economics documents. Architectural truth is that entitlement-based segmentation exists and is enforced.

---

## 8. Visibility Principles

1. A destination receives only stages authorized by its route policy.
2. Topic/channel selection follows entitlement, not convenience.
3. Presentation differences do not silently change entitlement.
4. Every publish path is explainable and observable.
5. Distribution policy belongs to the routing/distribution cluster, not ad hoc send code.

---

## 9. Channel and Topic Structure

External delivery may use:
- Telegram channels;
- supergroup topics;
- mixed channel/topic structures;
- future compatible publisher abstractions.

Each external surface requires:
- explicit destination identity;
- explicit entitlement role;
- explicit stage/event mapping;
- operational owner path;
- observability traceability.

No unnamed hardcoded sink is canonical.

---

## 10. Distribution Router Ownership

The Distribution Router owns delivery selection.

Responsibilities:
- receive governed distribution candidates;
- determine destination set;
- apply route/state/topic policy;
- prevent unauthorized routing;
- prepare publisher tasks;
- trigger route-level observability;
- support retry-aware/restart-safe flow.

The router MUST NOT:
- redefine trading logic;
- compute TPS or strategy score;
- invent FSM state;
- fabricate Signal Engine execution outcomes;
- own transport API implementation;
- bypass entitlement policy.

---

## 11. Publisher Ownership

Publisher abstraction owns external send execution.

Responsibilities:
- message/payload handoff handling;
- transport execution;
- delivery attempt/result capture;
- external API interaction;
- rate-limit-aware sending;
- transport retry mechanics;
- transport failure reporting.

Publisher MUST NOT:
- decide entitlement;
- decide strategy validity;
- change signal lifecycle state;
- silently reroute unauthorized content;
- replace Router as policy owner.

---

## 12. Routing Policy Inputs

Routing is determined by the combination of:
- governed signal stage/candidate eligibility;
- destination entitlement class;
- topic/channel mapping;
- admin-approved configuration;
- anti-duplication state;
- restart/recovery safety;
- transport health where relevant.

These remain separable and testable concerns.

---

## 13. Signal Lifecycle vs Delivery Lifecycle

Signal lifecycle and delivery lifecycle are related but distinct.

Examples:
- a candidate may be valid internally but not entitled for one route;
- a candidate may be entitled but transport-delayed;
- a publish attempt may fail while upstream strategic truth remains unchanged;
- closure/result delivery may occur on a different timing edge than initial delivery.

Distribution preserves this distinction and reports route truth without rewriting upstream truth.

---

## 14. Duplicate Prevention and Replay Safety

Protection is required against:
- duplicate PRE;
- duplicate CONFIRM;
- duplicate OPEN_NOW;
- duplicate RESULT/closure;
- restart replay of already published content;
- retry-created duplicates;
- cross-topic duplicate leakage.

Controls may include:
- message identity keys;
- distribution state registry;
- idempotency checks;
- per-stage publish markers;
- restart recovery checks;
- retry-aware bookkeeping.

Externally sensitive duplicate protection must not rely only on process memory where restart risk exists.

---

## 15. Restart Safety

After restart, Distribution must not:
- re-publish an already published sensitive stage without canonical reason;
- lose route ownership boundaries;
- lose required delivery markers;
- publish stale candidates as new;
- confuse transport failure with candidate eligibility.

Persisted distribution state is a protected state surface.

---

## 16. Observability Proof

Material distribution actions must be observable.

Required proof families include, as applicable:
- route eligibility accepted/rejected;
- route selection;
- destination resolution;
- publish attempt;
- publish result;
- retry scheduling/exhaustion;
- duplicate suppression;
- unauthorized route block;
- closure/result linkage.

Exact event-family names and payload contracts belong to `EVENT_SCHEMA_SPEC_v3.0.0.md` and `OBSERVABILITY_LOGGING_SPEC_v3.0.0.md`.

---

## 17. Delivery Evidence Requirements

Evidence must answer:
- which signal/stage was routed;
- which route/destination was selected;
- which concrete external target was attempted;
- whether publish succeeded/failed/skipped;
- whether retry occurred;
- whether duplicate suppression occurred;
- whether final route result matched policy.

A delivery system without reconstructable evidence is non-canonical.

---

## 18. Failure Handling

Failure classes may include:
- network failure;
- publisher API failure;
- permission failure;
- invalid destination mapping;
- malformed payload;
- transport throttling;
- duplicate-state conflict;
- unavailable external surface.

Failure must never silently widen access, alter upstream validity, or fabricate successful publication.

---

## 19. Retry Rules

Retries must preserve:
- identity;
- entitlement semantics;
- idempotency;
- route ownership;
- observability.

Retry exhaustion is visible.
Retry is a transport/reliability concern, not policy guessing.

---

## 20. Rate-Limit Management

The architecture supports:
- send pacing;
- queue discipline;
- backoff;
- retry coordination;
- failure visibility;
- no silent dropping of critical classes without evidence.

Transport rate limits do not rewrite entitlement policy.

---

## 21. Security and Access Boundaries

Distribution surfaces must enforce:
- controlled bot permissions;
- controlled admin permissions;
- restricted route-config mutation;
- no affiliate path to strategy internals;
- no unauthorized read path into engine internals;
- protected credentials and destination mappings.

---

## 22. Signal Leak Prevention

Leak mitigation may include:
- route separation;
- forwarding restrictions where supported;
- watermarking/attribution where appropriate;
- membership governance;
- differentiated entitlement;
- traceability of which surface received which class.

Leak prevention is part of architecture/governance, not merely copy formatting.

---

## 23. Affiliate Adjacency

Affiliates are not distribution owners.

Affiliate surfaces may expose governed commercial summaries but MUST NOT expose:
- strategy internals;
- restricted stages beyond entitlement;
- raw engine diagnostics;
- operational override capability;
- internal routing control;
- protected observability beyond authorized summaries.

---

## 24. Admin / Control Adjacency

Governed admin surfaces may support:
- route enable/disable;
- topic mapping;
- publication freeze/hold;
- health/send status;
- isolated test surfaces;
- evidence review.

Admin actions remain subordinate to RBAC, Governance and System Invariants.

---

## 25. Distribution Freeze / Controlled Hold

Explicit controlled hold states may include:
- temporary publish freeze;
- maintenance hold;
- mapping-change freeze;
- degraded delivery mode.

A hold must be observable, reversible and incapable of hidden entitlement drift.

---

## 26. Relationship to Telegram UX

Distribution Architecture defines:
- who may receive what;
- where it is routed;
- under what state conditions;
- with what safety/proof.

`TELEGRAM_UX_v2.0.1.md` defines how delivered content is presented.

Neither absorbs the other’s ownership.

---

## 27. Relationship to Decision Audit / Analytics

Distribution remains analyzable for:
- which decisions/candidates reached which routes;
- routing success/failure;
- entitlement blocks;
- duplicate suppression;
- publish latency/failure;
- closure linkage.

Analytics may inform governance; it does not silently mutate routing truth.

---

## 28. Relationship to Outcome / Community Feedback

Closure/result/feedback surfaces must preserve stable signal identity and truth-source separation.

Distribution does not decide whether a market outcome, operational reconciliation or community report is objectively true. It transports governed representations according to the relevant canonical authority.

This continuity is required for:
- user trust;
- traceability;
- analytics;
- dispute/reconciliation review;
- audit reconstruction.

---

## 29. Future Extension Rule

Future destinations such as Discord, web dashboards, mobile clients, APIs or partner surfaces are allowed only when they preserve:
- explicit entitlement;
- explicit destination identity;
- router ownership;
- observability proof;
- duplicate/restart safety;
- governance compatibility.

New destinations never justify bypassing Router/Publisher discipline.

---

## 30. Forbidden Distribution Behaviors

Non-canonical:
- direct external publish bypassing Router;
- route policy embedded ad hoc in unrelated modules;
- Publisher deciding entitlement;
- routing to undocumented destinations;
- unobservable publication;
- duplicate OPEN_NOW without canonical justification;
- closure publication without identity continuity;
- affiliate access to restricted operational surfaces;
- hidden topic remaps;
- retry logic causing unauthorized replay;
- Distribution mutating strategy/Trade Physics/FSM truth;
- candidate construction being treated as proof of delivery.

---

## 31. Canonical Success Standard

Distribution architecture is functioning canonically only when:
- eligible candidates route only to authorized destinations;
- unauthorized destinations receive nothing;
- Publisher is bounded by transport discipline;
- duplicates are prevented or explicitly explained;
- restart does not break routing safety;
- route/publish evidence proves the external lifecycle;
- admin/affiliate boundaries hold;
- architecture remains consistent with active canon.

---

## 32. PATCH Migration Note

v2.0.1 preserves v2.0.0 routing topology and ownership.

Changes are limited to:
- final successor cross-references;
- explicit Signal Engine -> SignalEvent candidate -> Router boundary already approved by staged-execution canon;
- multi-truth closure/feedback wording alignment;
- removal of ambiguity between candidate creation and external publication.

No entitlement, route limit, routing topology, publisher ownership or delivery-policy behavior is changed.

---

## 33. Version History

| Version | Date | Description |
|---|---|---|
| 2.0.1 | 2026-09-01 | Proposed PATCH: final canonical reference repair and explicit staged-execution boundary alignment; no distribution behavior change. |
| 2.0.0 | 2026-07-12 | Active canonical distribution architecture. |

---

## 34. Final Enforcement Statement

No future distribution implementation may bypass the ownership, routing, proof and safety rules defined here.

External delivery is allowed only through canonical control, never instead of it.