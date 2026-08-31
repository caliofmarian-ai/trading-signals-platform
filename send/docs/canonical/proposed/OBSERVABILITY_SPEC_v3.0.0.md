# OBSERVABILITY_SPEC_v3.0.0

Path: `send/docs/canonical/proposed/OBSERVABILITY_SPEC_v3.0.0.md`  
Version: 3.0.0  
Status: PROPOSED COMPLETE SUCCESSOR — NOT ACTIVE CANONICAL  
Owner: BinaryBot / DROPi Signals  
Scope: End-to-end observability policy, auditability, rejection analytics, semantic traceability, and explicit signal-execution truth across strategy, DecisionObject, FSM, signal engine, distribution, visibility and outcomes

Supersession Intent: OBSERVABILITY_SPEC_v2.0.0.md

---

## 0. AUTHORITY DECLARATION AND PROMOTION STATUS

This document is the proposed **system policy and architectural authority** for the observability domain.

- `OBSERVABILITY_LOGGING_SPEC_v3.0.0.md` is the proposed implementation-level logging/telemetry contract.
- `EVENT_SCHEMA_SPEC_v3.0.0.md` defines the proposed structural event schema.
- Where policy/architecture and mechanics differ, this document governs policy/architecture; logging/schema documents govern their mechanics within this policy.
- No implementation-level logging decision may contradict this document.

This is a complete proposed successor and does not depend normatively on v2 for omitted rules. Until explicit promotion, `OBSERVABILITY_SPEC_v2.0.0.md` remains active. Merge of this proposed file alone does not authorize code changes or distribution activation.

Linked Documents:
- CANONICAL_STRATEGY_STACK_v2.0.0.md
- ALGO_SPEC_v2.0.0.md
- DECISION_OBJECT_CANONICAL_SPEC_v1.0.0.md
- FSM_DECISION_ENGINE_SPEC_v2.0.0.md
- SIGNAL_ENGINE_EXECUTION_SPEC_v3.0.0.md
- MODULE_INTERFACE_SPEC_v3.0.0.md
- OBSERVABILITY_LOGGING_SPEC_v3.0.0.md
- EVENT_SCHEMA_SPEC_v3.0.0.md
- DECISION_AUDIT_SPEC_v2.0.0.md
- SIGNAL_DISTRIBUTION_ARCHITECTURE_v2.0.0.md
- SIGNAL_DISTRIBUTION_SPEC_v2.0.0.md
- FAILURE_RECOVERY_SPEC_v2.0.0.md

Depends on:
- CANONICAL_STRATEGY_STACK_v2.0.0.md
- ALGO_SPEC_v2.0.0.md
- DECISION_OBJECT_CANONICAL_SPEC_v1.0.0.md
- FSM_DECISION_ENGINE_SPEC_v2.0.0.md
- SIGNAL_ENGINE_EXECUTION_SPEC_v3.0.0.md

---

## 1. PURPOSE

Observability face sistemul:
- explicabil
- auditabil
- debuggable
- replayable
- măsurabil
- optimizabil
- forensic reconstructable

Observability nu este logging brut. Este layerul semantic care permite urmărirea completă a unui setup de la context strategic până la emission/non-emission, distribution, external visibility sau moarte.

---

## 2. CORE PRINCIPLE

Observability urmărește **lanțul complet al semnificației**:
1. market model
2. corridor engine
3. time model
4. scoring
5. DecisionObject
6. FSM decision + exact-stage handoff
7. signal-engine execution result
8. SignalEvent candidate unde există
9. distribution result unde routing este activ
10. external visibility unde există
11. outcome/reconciliation unde este aplicabil

Nu este suficient să observăm doar outputul final.

---

## 3. OBSERVABILITY GOALS

Sistemul trebuie să poată răspunde:
- ce setup a fost evaluat?
- ce context strategic exista?
- ce corridor/time/score semantics au rezultat?
- ce DecisionObject a fost produs?
- ce stage actionable a cerut strategia?
- ce a decis FSM?
- FSM a eliberat exact acel stage?
- `stage_handoff_ready` a fost true/false și de ce?
- `trade_execution_ready` a fost true/false și de ce?
- signal engine a construit SignalEvent?
- ce execution outcome a rezultat?
- routing a început sau nu?
- ce route/publication evidence există?
- stage-ul a devenit extern vizibil?
- dacă flow-ul a murit, unde și de ce?

Dacă răspunsurile nu pot fi reconstruite, observability este incompletă.

---

## 4. WHAT OBSERVABILITY IS NOT

Observability nu este:
- doar stdout
- doar erori tehnice
- doar Telegram admin messages
- doar metrici fără semantică
- substitut pentru strategy/FSM/execution/distribution contracts
- generic debug blob folosit ca unic adevăr
- layer de mutație a trading behavior

---

## 5. REQUIRED COVERAGE LAYERS

Coverage minim obligatoriu:
- strategy context
- structure/corridor
- time
- scoring
- DecisionObject
- FSM lifecycle and handoff
- signal execution
- SignalEvent candidate existence
- distribution/route evaluation unde există
- external visibility unde există
- failure/rejection/degradation/suppression
- outcome/reconciliation unde există

---

## 6. PRIMARY OBSERVABILITY OBJECTIVE

**Orice setup relevant trebuie urmărit semantic de la naștere până la emitere, blocare, degradare, defer, skip, fail, suppression sau moarte.**

Niciun truth domain nu poate fi înlocuit de altul.

---

## 7. TRACEABILITY PRINCIPLE

Fiecare setup relevant trebuie să aibă identitate de corelare suficientă pentru:
- context input
- structure/time/score evaluation
- DecisionObject
- FSM transition/handoff
- execution attempt/result
- SignalEvent candidate
- distribution events
- external visibility
- outcomes
- reject/degrade/fail/skip/suppress paths

Corelarea este obligatorie pentru replay și audit.

---

## 8. MINIMUM CORRELATION FIELDS

Observability trebuie să poată asocia minimum, după domeniu:
- setup correlation identity
- `execution_attempt_id` pentru execution domain
- `signal_id` pentru actionable lifecycle
- symbol
- direction
- timeframe/context temporal
- evaluation timestamp
- run/cycle identity
- stage
- outcome family
- route/distribution references când routing există

Aceeași oportunitate trebuie să rămână corelabilă end-to-end.

---

## 9. STRATEGY OBSERVABILITY REQUIREMENT

Layerul strategic expune semantic:
- context summary
- structure summary
- time summary
- score summary
- gating summary
- resulting DecisionObject family

Nu este obligatoriu să expună toate valorile brute, dar trebuie să expună adevărul relevant auditului.

---

## 10. DECISIONOBJECT OBSERVABILITY REQUIREMENT

Trebuie să putem vedea:
- dacă DecisionObject a fost produs
- contract/schema version
- semantic families
- stage/kind
- stable signal identity unde este actionable
- reject/degrade semantics
- evidence predată FSM-ului

DecisionObject este strategic truth node, nu execution truth container.

---

## 11. FSM OBSERVABILITY REQUIREMENT

Observability trebuie să vadă:
- requested_stage
- accepted_stage
- state/outcome
- reason/reason family
- transition evidence
- lifecycle/identity continuity
- block/suppression semantics
- `stage_handoff_ready`
- `trade_execution_ready`
- progresie/stagnare/degradare/reject

Important:
- FSM state nu este publication proof;
- transition event nu este implicit stage-release proof;
- `stage_handoff_ready` și `trade_execution_ready` sunt adevăruri distincte.

---

## 12. SIGNAL EXECUTION OBSERVABILITY REQUIREMENT

Observability trebuie să vadă pentru fiecare material execution attempt:
- dacă signal engine a evaluat handoff-ul
- dacă SignalEvent a fost construit
- `execution_phase`
- `execution_outcome`
- reason/blocker/failure detail
- destination state/context
- candidate/payload reference
- distribution references unde routing a început
- publication evidence dacă outcome este EMITTED

Execution outcomes minime:
- EMITTED
- NOT_EMITTED
- BLOCKED
- SKIPPED
- FAILED
- DEFERRED

---

## 13. EXECUTION PHASE MODEL

Execution observability trebuie să distingă minimum:
- `PRE_DISTRIBUTION`
- `POST_DISTRIBUTION`

### PRE_DISTRIBUTION
Poate exista SignalEvent valid cu `DEFERRED` atunci când distribution este intenționat disabled/not invoked.

În această fază:
- destination state trebuie să fie explicit unresolved;
- EMITTED este interzis;
- external visibility nu poate fi pretinsă.

### POST_DISTRIBUTION
Există numai când downstream distribution evidence este disponibilă.

EMITTED necesită dovadă că cel puțin o publicare autorizată a reușit. Exact route-level truth rămâne în distribution events.

---

## 14. PRE-DISTRIBUTION DESTINATION STATE

Dacă routing nu a început, lipsa destination data nu trebuie să pară defect de logging sau delivery failure.

Baseline semantic:
- `destination_state = PRE_DISTRIBUTION_UNRESOLVED`

Înseamnă:
- route evaluation nu a început;
- destination nu a fost selectată;
- nu este transport failure;
- nu este publication authorization.

---

## 15. ROUTE-LEVEL TRUTH PRESERVATION

Când distribution începe:
- exact route selection
- destination
- entitlement
- publish attempt
- publish result
- per-route skip/failure/duplicate
rămân truth domain al distribution.

Signal-engine observability poate agrega final execution outcome numai cu referințe către route evidence și fără a pierde mixed-route detail.

---

## 16. REJECTION ANALYTICS PRINCIPLE

Sistemul trebuie să poată analiza motivele pentru care semnalele:
- nu au ajuns la execution candidate
- au murit pe traseu
- au fost respinse strategic
- au fost degradate
- au fost blocate/suppressed în FSM
- au fost not-emitted/skipped/failed/deferred în signal engine
- au eșuat sau au fost skipped per route

Rejection analytics este parte canonică a observability.

---

## 17. REQUIRED REJECTION QUESTIONS

Minimum:
- unde a murit setup-ul?
- strategic, FSM, execution sau distribution?
- hard reject, soft degrade, block, suppression, skip sau fail?
- identity/lifecycle continuity a eșuat?
- stage_handoff_ready a fost refuzat?
- candidate construction a eșuat?
- technical fail sau non-emission logică?

---

## 18. STAGE-OF-DEATH MODEL

Stage-of-death poate include:
- strategy gate
- structure gate
- time gate
- score gate
- DecisionObject reject/degrade
- FSM wait/reject/blocked/suppressed
- exact-stage handoff failure
- signal-engine candidate construction
- signal execution non-emission/block/skip/fail
- distribution route/publisher failure

Modelul poate fi rafinat, dar localizarea semantică a morții este obligatorie.

---

## 19. DEGRADATION ANALYTICS PRINCIPLE

Observability surprinde traseul de degradare, nu doar verdictul final.

Exemple:
- setup inițial bun care slăbește
- time pressure crește
- score coboară sub prag
- FSM devine DEGRADED/WAIT/BLOCKED
- execution devine NOT_EMITTED/DEFERRED din motive explicite

---

## 20. EXPLANATION REQUIREMENT

Pentru fiecare decizie relevantă trebuie să existe explanation snippets suficiente pentru:
- context
- structure
- time
- score
- strategic verdict
- FSM verdict/handoff
- execution outcome
- distribution result unde există

Explicația trebuie să fie semantică și corelată cu evidence, nu narativ inventat.

---

## 21. METRICS VS SEMANTICS RULE

Observability combină:
- metrici
- semantic states
- reasons
- correlation
- outcome families
- proof references

Un dashboard doar cu numere nu este observability complet.

---

## 22. ADMIN / OPERATOR VISIBILITY RULE

Admin/control surfaces trebuie să poată consuma observability structurat pentru:
- health views
- rejection summaries
- stage-of-death summaries
- lifecycle funnels
- FSM handoff diagnostics
- execution diagnostics
- distribution diagnostics
- audit drilldown

UI-ul nu devine source of truth.

---

## 23. TELEGRAM / ALERTING RELATION

Telegram admin/debug poate expune evidence derivată, dar nu înlocuiește persisted canonical observability.

Dacă Telegram view și persisted evidence diferă, persisted evidence guvernează până când corruption este demonstrată.

---

## 24. STORAGE / EVENT MODEL PRINCIPLE

Implementarea poate folosi events, structured logs, snapshots, JSONL sau alte backend-uri, dar trebuie să păstreze:
- semantic-domain separation
- correlation
- filtering
- replay
- audit
- analytics
- append/reconstruction integrity unde este relevant

---

## 25. REQUIRED OUTCOME FAMILIES FOR OBSERVABILITY

Observability distinge minimum:

Strategic:
- accept / degrade / reject / no-signal

FSM:
- wait / prepare / confirm / open_now / reject / blocked / degraded / suppression semantics

Execution:
- EMITTED / NOT_EMITTED / BLOCKED / SKIPPED / FAILED / DEFERRED

Distribution:
- route publish/skip/fail/duplicate semantics definite de distribution canon

Aceste familii nu se colapsează într-o etichetă opacă.

---

## 26. `signal_execution_result` POLICY

`signal_execution_result` este event family propusă pentru signal-engine execution truth.

Trebuie să fie distinctă de:
- decision events
- fsm_transition
- signal_stage_visible
- route_publish_attempt/result
- outcome events

Poate exista un PRE_DISTRIBUTION checkpoint și un POST_DISTRIBUTION final result corelate prin același `execution_attempt_id`.

Execution truth nu poate exista numai într-un generic `decision.debug` blob.

---

## 27. EXTERNAL VISIBILITY POLICY

External lifecycle visibility este un truth domain separat.

- SignalEvent candidate nu este visibility.
- FSM WATCHLIST/CONFIRMED nu este visibility.
- `stage_handoff_ready` nu este visibility.
- successful governed publication poate produce `signal_stage_visible` conform event schema/distribution evidence.

Legacy `signal_emitted` poate rămâne istoric/compatibility, dar nu trebuie să fie primary v3 proof pentru candidate construction sau visibility.

---

## 28. FORBIDDEN OBSERVABILITY PATTERNS

Interzise:
- imposibilitatea de a corela setup-ul pe etape
- imposibilitatea de a localiza moartea semnalului
- logging fără semantică recognoscibilă
- doar payload final fără decision history
- doar errors fără rejection/degrade semantics
- amestecarea strategic/FSM/execution/distribution într-un singur blob
- generic decision debug ca unic execution record
- SignalEvent construction interpretat ca EMITTED
- FSM state interpretat ca publication proof
- distribution failure interpretat ca strategic rejection

---

## 29. CODE ALIGNMENT RULE

O implementare trebuie să răspundă clar:
- cum corelează setup-ul end-to-end?
- unde este DecisionObject evidence?
- unde este FSM handoff evidence?
- unde este signal_execution_result?
- cum separă PRE_DISTRIBUTION de POST_DISTRIBUTION?
- cum demonstrează EMITTED?
- unde este route-level evidence?
- cum exprimă reject/degrade/stage-of-death?
- cum consumă admin/audit aceste date?

Dacă nu, alignment este incomplet.

---

## 30. INTELLIGENCE PIPELINE EVIDENCE FLOW

Raw logs remain canonical evidence inputs to intelligence processing. Derived intelligence outputs trebuie să păstreze traceability către source event classes și nu pot muta runtime truth.

Aggregated outputs pot alimenta diagnostics/research/admin surfaces fără să devină source of truth pentru strategy/FSM/execution/distribution.

---

## 31. PROMOTION AND MIGRATION RULE

La promovare:
- v3 devine singura active observability policy authority;
- v2 este mutat în `canonical/superseded` cu traceability;
- active references către v2 sunt reparate atomic;
- OBSERVABILITY_LOGGING v3 și EVENT_SCHEMA v3 trebuie promovate compatibil;
- historical v2 events rămân interpretate prin schema lor originală;
- runtime code/schema nu se modifică până după re-auditul canonului promovat.

---

## 32. FINAL PRINCIPLE

Observability este stratul care face întregul sistem inteligibil.

Trebuie să fie:
- end-to-end
- semantic
- corelat
- auditabil
- truth-domain separated
- util pentru rejection analytics
- util pentru admin/operator tooling
- capabil să distingă lifecycle handoff, execution candidate, publication și outcome
- suficient pentru a explica de ce un semnal a trăit, a murit, a fost deferred sau a fost publicat

Aceasta este specificația completă propusă de observability v3.