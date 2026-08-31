# CANONICAL_STRATEGY_STACK_v2.0.0

Path: /opt/binarybot/docs/canonical/proposed/CANONICAL_STRATEGY_STACK_v2.0.0.md  
Version: 2.0.0  
Status: PROPOSED COMPLETE SUCCESSOR — NOT ACTIVE CANONICAL  
Owner: BinaryBot / DROPi Signals  
Scope: Root strategy stack, canonical authority order, module contract chain, staged execution handoff, document precedence

Supersession Intent: CANONICAL_STRATEGY_STACK_v1.0.0.md

Linked Documents:
- canonical/active/ALGO_SPEC_v2.0.0.md
- canonical/active/TIME_MODEL_UNIFIED_CANON_v2.0.0.md
- canonical/active/SR_CORRIDOR_ENGINE_SPEC_v2.0.0.md
- canonical/active/DECISION_OBJECT_CANONICAL_SPEC_v1.0.0.md
- canonical/proposed/FSM_DECISION_ENGINE_SPEC_v2.0.0.md
- canonical/proposed/SIGNAL_ENGINE_EXECUTION_SPEC_v3.0.0.md
- canonical/proposed/OBSERVABILITY_SPEC_v3.0.0.md
- canonical/proposed/MODULE_INTERFACE_SPEC_v3.0.0.md
- canonical/proposed/EVENT_SCHEMA_SPEC_v3.0.0.md
- canonical/proposed/OBSERVABILITY_LOGGING_SPEC_v3.0.0.md
- canonical/active/SIGNAL_DISTRIBUTION_ARCHITECTURE_v2.0.0.md
- canonical/active/SIGNAL_DISTRIBUTION_SPEC_v2.0.0.md

Depends on:
- canonical/active/ALGO_SPEC_v2.0.0.md
- canonical/active/TIME_MODEL_UNIFIED_CANON_v2.0.0.md
- canonical/active/SR_CORRIDOR_ENGINE_SPEC_v2.0.0.md
- canonical/active/DECISION_OBJECT_CANONICAL_SPEC_v1.0.0.md
- canonical/proposed/FSM_DECISION_ENGINE_SPEC_v2.0.0.md
- canonical/proposed/SIGNAL_ENGINE_EXECUTION_SPEC_v3.0.0.md
- canonical/proposed/OBSERVABILITY_SPEC_v3.0.0.md
- canonical/proposed/MODULE_INTERFACE_SPEC_v3.0.0.md
- canonical/proposed/EVENT_SCHEMA_SPEC_v3.0.0.md
- canonical/proposed/OBSERVABILITY_LOGGING_SPEC_v3.0.0.md
- canonical/active/SYSTEM_INVARIANTS_v2.0.0.md
- canonical/active/GOVERNANCE_AND_CHANGE_CONTROL_v2.0.0.md

---

## 0. AUTHORITY AND PROMOTION STATUS

This document is a complete proposed successor to `CANONICAL_STRATEGY_STACK_v1.0.0.md`.

It defines the intended strategy-cluster authority after the staged-execution/observability remediation is promoted. It does not become authoritative merely by being merged into `canonical/proposed`.

Until explicit promotion:
- `CANONICAL_STRATEGY_STACK_v1.0.0.md` remains the active root manifest;
- all currently active subordinate versions remain authoritative;
- runtime code must not claim conformance to this proposal;
- PR #73 remains blocked.

---

## 1. PURPOSE

Acest document este manifestul root propus al stack-ului strategic BinaryBot.

Scopul lui este:
- să definească setul oficial de documente root ale strategiei;
- să stabilească ordinea de autoritate între documente;
- să definească fluxul oficial de la piață la lifecycle candidate și execution truth;
- să definească contractul oficial dintre strategie, DecisionObject, FSM, signal engine și observability;
- să păstreze distribution ca autoritate downstream distinctă;
- să elimine ambiguitatea dintre stage lifecycle handoff, final trade readiness, SignalEvent candidate și external publication;
- să ofere punct unic de pornire pentru audit, patch și refactor.

Acest document nu înlocuiește specificațiile detaliate. El stabilește care specificații sunt autoritare și cum se leagă.

---

## 2. CORE PRINCIPLE

Strategia BinaryBot este un stack de layere separate:
- market model;
- SR/corridor structure;
- time model;
- scoring;
- DecisionObject strategic truth;
- FSM operational/lifecycle truth;
- signal-engine execution truth;
- observability;
- distribution/publication downstream.

Niciun document sau modul nu poate recombina aceste layere într-o logică opacă sau să înlocuiască truth domain-ul altui layer.

---

## 3. OFFICIAL STRATEGY FLOW

Fluxul oficial propus este:

```text
MARKET DATA
   ↓
MARKET MODEL
   ↓
SR / CORRIDOR ENGINE
   ↓
TIME MODEL
   ↓
SCORING MODEL
   ↓
DECISION OBJECT
   ↓
DECISION FSM
   ↓
EXACT-STAGE FSM HANDOFF
   ↓
SIGNAL ENGINE
   ↓
SIGNAL EVENT CANDIDATE / SIGNAL_EXECUTION_RESULT
   ↓
DISTRIBUTION ROUTER / DELIVERY / OBSERVABILITY
   ↓
EXTERNAL VISIBILITY / OUTCOMES WHERE APPLICABLE
```

Reguli:
- DecisionObject precede FSM;
- FSM precede SignalEvent candidate construction;
- SignalEvent candidate precede distribution;
- candidate construction nu înseamnă external publication;
- distribution truth rămâne în distribution canon;
- outcome truth rămâne downstream și separat.

Orice document care descrie alt flux trebuie reconciliat prin governance înainte de implementare.

---

## 4. ROOT CANONICAL DOCUMENT SET

Setul root propus al strategiei este:
1. `ALGO_SPEC_v2.0.0.md`
2. `TIME_MODEL_UNIFIED_CANON_v2.0.0.md`
3. `SR_CORRIDOR_ENGINE_SPEC_v2.0.0.md`
4. `DECISION_OBJECT_CANONICAL_SPEC_v1.0.0.md`
5. `FSM_DECISION_ENGINE_SPEC_v2.0.0.md`
6. `SIGNAL_ENGINE_EXECUTION_SPEC_v3.0.0.md`
7. `OBSERVABILITY_SPEC_v3.0.0.md`

Aceste șapte documente formează stack-ul strategic root intenționat după promovare.

Nu se adaugă un document separat de handoff: ownership-ul rămâne în FSM, Signal Engine și Module Interface, conform `SYSTEM_ARCHITECTURE_MAP_v2.0.0.md`.

---

## 5. SUPPORTING ACTIVE/PROPOSED CANONICAL CONTRACTS

Implementarea stack-ului trebuie să respecte și:
- `MODULE_INTERFACE_SPEC_v3.0.0.md` — shared contracts și ownership boundaries;
- `EVENT_SCHEMA_SPEC_v3.0.0.md` — event envelope/families;
- `OBSERVABILITY_LOGGING_SPEC_v3.0.0.md` — logging mechanics;
- `DECISION_AUDIT_SPEC_v2.0.0.md` — decision audit;
- `SYSTEM_INVARIANTS_v2.0.0.md` — hard invariants;
- `SIGNAL_DISTRIBUTION_ARCHITECTURE_v2.0.0.md` — downstream distribution topology;
- `SIGNAL_DISTRIBUTION_SPEC_v2.0.0.md` — downstream entitlement/delivery policy;
- `TEST_PLAN_v2.0.0.md` — validation authority;
- `DEPLOYMENT_PROTOCOL_v2.0.0.md` — deployment safety;
- `GOVERNANCE_AND_CHANGE_CONTROL_v2.0.0.md` — change governance.

Supporting non-canonical audit/planning documents may guide reconciliation but cannot override active canonical truth.

---

## 6. AUTHORITY ORDER

În conflict/ambiguity, ordinea este:

### Nivel 1 — Root Strategy Manifest and Root Specs
1. `CANONICAL_STRATEGY_STACK_v2.0.0.md`
2. topic-specific root spec from Section 4

### Nivel 2 — Canonical Interface / Schema / Logging / Invariants
- `MODULE_INTERFACE_SPEC_v3.0.0.md`
- `EVENT_SCHEMA_SPEC_v3.0.0.md`
- `OBSERVABILITY_LOGGING_SPEC_v3.0.0.md`
- `SYSTEM_INVARIANTS_v2.0.0.md`
- other active domain specs within their own scope

### Nivel 3 — Supporting Audit / Planning / Governance Records
Supporting non-canonical artifacts may document rationale, impact, migration and audits, but may not redefine active truth.

### Nivel 4 — Transitional / Compatibility Material
Migration notes and compatibility records are subordinate to active canon.

### Nivel 5 — Superseded / Deprecated / Historical
Historical only; never primary implementation authority.

If lower-level material contradicts higher authority, the higher authority wins and the contradiction must be resolved before implementation.

---

## 7. OFFICIAL VOCABULARY LOCK

### 7.1 Market / Structure
- price_speed
- buffer_distance
- support_levels
- resistance_levels
- corridor_width
- structure_context
- volatility_state
- trend_context

### 7.2 Time
- t_needed
- t_needed_adjusted
- model_expiry
- model_time_reach_ratio
- corridor_time_pressure
- time_state

### 7.3 Decision
- score_total
- score_components
- DecisionObject
- decision_state
- requested_stage

### 7.4 FSM / Handoff
- accepted_stage
- stage_handoff_ready
- trade_execution_ready
- reason / reason_family
- transition evidence

### 7.5 Signal Execution
- SignalEvent
- execution_attempt_id
- execution_phase
- execution_outcome
- signal_execution_result
- PRE_DISTRIBUTION_UNRESOLVED

### 7.6 Distribution / Visibility
- distribution router
- route_publish_attempt
- route_publish_result
- signal_stage_visible

---

## 8. FORBIDDEN PRIMARY TERMS / CONFLATIONS

Nu pot fi folosite ca adevăr canonic primar:
- expiry_reach_ratio în locul time-model vocabulary activ;
- expiry_minutes ca unic adevăr temporal final;
- buffer_price ca substitut primar pentru buffer_distance;
- legacy dict output ca final strategy contract;
- runtime flows care omit DecisionObject;
- transition_event ca implicit stage acceptance;
- generic accepted flag ca exact-stage release;
- stage_handoff_ready ca sinonim pentru trade_execution_ready;
- SignalEvent candidate ca sinonim pentru published/emitted external signal;
- FSM state ca proof de external visibility;
- generic decision debug ca unic execution truth.

Legacy terms pot exista doar cu compatibility/migration status explicit.

---

## 9. MODULE CONTRACT CHAIN

Lanțul contractual oficial este:

```text
strategy_v2.py
   produces
DecisionObject
   consumed by
FSM decision layer
   produces
FSMExecutionHandoff
   {requested_stage, accepted_stage,
    stage_handoff_ready, trade_execution_ready, ...}
   consumed by
signal_engine.py
   produces
SignalEvent candidate + signal_execution_result
   consumed by
Distribution Router (when authorized/active)
   produces
route-level publication evidence
   supports
external visibility / outcomes
```

Nicio etapă nu poate bypassa authority boundary precedent.

---

## 10. STRATEGY MODULE RESPONSIBILITIES

### 10.1 Market Model
Responsabil pentru market context, trend/volatility, price_speed și buffer semantics conform ALGO.

Root: `ALGO_SPEC_v2.0.0.md`

### 10.2 SR / Corridor Engine
Responsabil pentru structure/corridor detection și validity.

Root: `SR_CORRIDOR_ENGINE_SPEC_v2.0.0.md`

### 10.3 Time Model
Responsabil pentru t_needed, adjusted timing, model_expiry, time reach ratio/pressure și time_state.

Root: `TIME_MODEL_UNIFIED_CANON_v2.0.0.md`

### 10.4 Scoring Model
Responsabil pentru score components și score_total.

Root: `ALGO_SPEC_v2.0.0.md`

### 10.5 DecisionObject Contract
Responsabil pentru standardizarea strategic truth și predarea către FSM.

Root: `DECISION_OBJECT_CANONICAL_SPEC_v1.0.0.md`

### 10.6 Decision FSM
Responsabil pentru lifecycle/operational truth și exact-stage handoff.

Root: `FSM_DECISION_ENGINE_SPEC_v2.0.0.md`

Important:
- PRE/CONFIRM pot avea `stage_handoff_ready=true` cu `trade_execution_ready=false`;
- OPEN_NOW poate avea ambele true numai după valid canonical path/actionability;
- blocker/no-op/duplicate evidence nu este release.

### 10.7 Signal Engine Execution
Responsabil pentru candidate construction și execution truth după FSM handoff.

Root: `SIGNAL_ENGINE_EXECUTION_SPEC_v3.0.0.md`

Important:
- SignalEvent candidate nu este publication;
- pre-distribution valid candidate poate fi DEFERRED;
- EMITTED cere downstream publication success evidence.

### 10.8 Observability
Responsabil pentru end-to-end traceability și truth-domain separation.

Root: `OBSERVABILITY_SPEC_v3.0.0.md`

---

## 11. ROOT DOCUMENT PRECEDENCE BY TOPIC

### 11.1 Time mathematics
1. `TIME_MODEL_UNIFIED_CANON_v2.0.0.md`
2. `ALGO_SPEC_v2.0.0.md`

### 11.2 Strategic output
1. `DECISION_OBJECT_CANONICAL_SPEC_v1.0.0.md`
2. `ALGO_SPEC_v2.0.0.md`

### 11.3 FSM lifecycle / exact-stage acceptance
1. `FSM_DECISION_ENGINE_SPEC_v2.0.0.md`
2. `DECISION_OBJECT_CANONICAL_SPEC_v1.0.0.md`
3. `SYSTEM_INVARIANTS_v2.0.0.md`

### 11.4 SignalEvent candidate / execution outcomes
1. `SIGNAL_ENGINE_EXECUTION_SPEC_v3.0.0.md`
2. `FSM_DECISION_ENGINE_SPEC_v2.0.0.md`
3. `MODULE_INTERFACE_SPEC_v3.0.0.md`
4. `EVENT_SCHEMA_SPEC_v3.0.0.md` for structural event mechanics

### 11.5 Observability policy vs mechanics
1. `OBSERVABILITY_SPEC_v3.0.0.md` for policy/architecture
2. `OBSERVABILITY_LOGGING_SPEC_v3.0.0.md` for logging mechanics
3. `EVENT_SCHEMA_SPEC_v3.0.0.md` for event structure

### 11.6 Distribution / publication
1. `SIGNAL_DISTRIBUTION_ARCHITECTURE_v2.0.0.md` for topology/architecture
2. `SIGNAL_DISTRIBUTION_SPEC_v2.0.0.md` for entitlement/delivery policy
3. `EVENT_SCHEMA_SPEC_v3.0.0.md` for route-event structure

Signal engine cannot override distribution route truth.

---

## 12. ROOT IMPLEMENTATION RULE

Niciun code patch nu poate fi definit din:
- proposed docs înainte de promotion;
- superseded/deprecated docs;
- mixed/unreconciled docs;
- runtime behavior care contrazice active canon.

După promotion și re-audit, fiecare patch trebuie să citeze authority relevantă.

Exemple intenționate după promotion:
- FSM patch -> `FSM_DECISION_ENGINE_SPEC_v2.0.0.md`
- execution patch -> `SIGNAL_ENGINE_EXECUTION_SPEC_v3.0.0.md`
- event schema patch -> `EVENT_SCHEMA_SPEC_v3.0.0.md`
- observability logging patch -> `OBSERVABILITY_LOGGING_SPEC_v3.0.0.md`

---

## 13. ROOT AUDIT RULE

Orice audit strategy/runtime:
1. verifică manifestul root activ;
2. identifică root spec relevant;
3. verifică interface/schema/invariants/supporting active canon;
4. verifică distribution/outcome authority dacă path-ul ajunge downstream;
5. verifică runtime code mapping;
6. verifică historical docs numai pentru context.

Ordinea este obligatorie pentru a evita revenirea la truth superseded.

---

## 14. RELATION TO SUPERSEDED / DEPRECATED DOCS

Superseded/deprecated docs pot fi păstrate pentru:
- historical traceability;
- audit;
- migration rationale;
- intellectual rollback context.

Nu pot fi primary implementation source după supersession.

---

## 15. RELATION TO PROPOSED DOCS

`canonical/proposed` nu este active authority.

Un proposed document poate fi:
- design material;
- complete successor candidate;
- review target.

El devine binding numai după explicit promotion și active-index reconciliation.

---

## 16. PROMOTION ORDER FOR THIS REMEDIATION

Pentru staged execution remediation, promotion trebuie să fie atomic la nivel documentar:
1. finalize complete successor specs;
2. finalize this complete root manifest;
3. finalize complete Master Index successor;
4. enumerate and prepare all active reference-only repairs;
5. move/supersede old versions through governance;
6. install new versions in `canonical/active`;
7. repair all active references;
8. validate unique authority and inventory;
9. re-audit active canon;
10. only then authorize a separate runtime code remediation.

No distribution/broker activation is implied.

---

## 17. SINGLE SOURCE OF TRUTH RULE

Nu există un singur fișier cu toate detaliile strategiei, dar există un singur stack canonic oficial.

Truth-ul este compus din:
- active root manifest;
- active topic-specific root specs;
- active interface/schema/invariant/domain specs;
- precedence rules.

Acestea formează sursa unică de adevăr operațional.

---

## 18. NO-DUPLICATE-AUTHORITY RULE

O frontieră nu primește un nou canonical owner dacă ownership-ul există deja.

Pentru această remediere:
- FSM deține stage acceptance/handoff truth;
- Module Interface definește shared contract;
- Signal Engine deține candidate/execution truth;
- Event Schema definește event structure;
- Observability definește policy/logging;
- Distribution deține route/publication truth.

Nu există `SIGNAL_EXECUTION_HANDOFF_CANON` separat.

---

## 19. FINAL PRINCIPLE

Documentația canonică trebuie să fie:
- ierarhică;
- explicită;
- auditată;
- separată pe responsabilități;
- versionată;
- mai rapid clarificată decât codul;
- lipsită de ownership duplicat.

Acest document este manifestul complet propus pentru strategia v2. El devine autoritate numai prin promotion explicit și re-audit.