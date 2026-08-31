# SIGNAL_ENGINE_EXECUTION_SPEC_v3.0.0

Path: /opt/binarybot/docs/canonical/proposed/SIGNAL_ENGINE_EXECUTION_SPEC_v3.0.0.md  
Version: 3.0.0  
Status: PROPOSED COMPLETE SUCCESSOR — NOT ACTIVE CANONICAL  
Owner: BinaryBot / DROPi Signals  
Scope: Signal execution after FSM handoff, SignalEvent candidate construction, execution outcomes, distribution handoff, and execution observability

Supersession Intent: SIGNAL_ENGINE_EXECUTION_SPEC_v2.0.0.md

Linked Documents:
- CANONICAL_STRATEGY_STACK_v2.0.0.md
- ALGO_SPEC_v2.0.0.md
- DECISION_OBJECT_CANONICAL_SPEC_v1.0.0.md
- FSM_DECISION_ENGINE_SPEC_v2.0.0.md
- MODULE_INTERFACE_SPEC_v3.0.0.md
- OBSERVABILITY_SPEC_v3.0.0.md
- EVENT_SCHEMA_SPEC_v3.0.0.md
- SIGNAL_DISTRIBUTION_ARCHITECTURE_v2.0.0.md
- SIGNAL_DISTRIBUTION_SPEC_v2.0.0.md
- CHANNEL_CONFIG_SPEC_v2.0.0.md

Depends on:
- CANONICAL_STRATEGY_STACK_v2.0.0.md
- ALGO_SPEC_v2.0.0.md
- DECISION_OBJECT_CANONICAL_SPEC_v1.0.0.md
- FSM_DECISION_ENGINE_SPEC_v2.0.0.md
- SYSTEM_INVARIANTS_v2.0.0.md

---

## 0. AUTHORITY AND PROMOTION STATUS

This document is a complete proposed successor. It contains the full intended signal-execution authority and does not require the superseded v2 document to define omitted behavior.

Until explicit promotion, `SIGNAL_ENGINE_EXECUTION_SPEC_v2.0.0.md` remains active. Merge of this proposal alone does not authorize runtime implementation or distribution activation.

---

## 1. PURPOSE

Acest document definește specificația completă propusă a layerului de signal execution.

Signal engine-ul are rolul de a:
- consuma verdictul operațional explicit post-FSM
- aplica execution gating
- materializa `SignalEvent` candidates pentru stage-uri acceptate
- orchestra handoff-ul către distribution fără a-i prelua autoritatea
- păstra outcome-uri de execuție distincte
- furniza execution observability și corelare

Signal engine-ul nu definește matematica strategiei, `DecisionObject`, FSM lifecycle, route entitlement, Telegram formatting, outcome settlement sau broker execution.

---

## 2. CORE PRINCIPLE

Signal engine-ul este layerul de execuție dintre FSM și distribution.

Ordinea blocată:
1. market model
2. corridor engine
3. time model
4. scoring
5. `DecisionObject`
6. FSM
7. signal engine
8. `SignalEvent` candidate / execution result
9. distribution router
10. publisher / external surface

Nu există shortcut canonic de la strategie, score, expiry sau DecisionObject direct la publication.

---

## 3. ROLE OF SIGNAL ENGINE

Responsabilități fundamentale:
1. **execution gating** — verifică handoff-ul exact al FSM și blocker-ele;
2. **SignalEvent candidate construction** — construiește obiectul engine-to-distribution numai pentru stage acceptat;
3. **distribution handoff orchestration** — pasează candidate downstream doar când acea fază este autorizată;
4. **engine-level duplicate protection** — previne release duplicat înainte de routing;
5. **execution traceability** — produce execution outcomes și probe corelate.

---

## 4. WHAT SIGNAL ENGINE IS NOT

Signal engine-ul nu este:
- motor strategic
- time model
- DecisionObject producer
- FSM authority
- distribution policy owner
- Telegram publisher authority
- outcome truth owner
- broker execution authority
- substitut pentru observability/audit

---

## 5. REQUIRED INPUT CONTRACT

Inputul primar este verdictul operațional post-FSM, cu minimum:
- requested_stage
- accepted_stage
- stage_handoff_ready
- trade_execution_ready
- state/outcome
- reason / reason family
- signal_id unde este aplicabil
- transition/handoff metadata

`DecisionObject` poate fi consumat auxiliar pentru context și payload evidence, dar nu poate bypassa FSM.

Pentru PRE, CONFIRM și OPEN_NOW, SignalEvent consideration necesită `stage_handoff_ready=true` și `accepted_stage` identic cu stage-ul DecisionObject.

---

## 6. CANONICAL SIGNAL EVENT CONSTRUCTION RULE

Un `SignalEvent` poate fi construit numai dacă:
- DecisionObject este actionable PRE / CONFIRM / OPEN_NOW;
- există stable `signal_id` conform lifecycle;
- FSM a acceptat exact același stage;
- `stage_handoff_ready=true`;
- `accepted_stage == DecisionObject.stage`;
- payload-ul poate fi construit din evidence real, coerent;
- nu există execution blocker care interzice candidate construction.

`trade_execution_ready`:
- MUST fi false pentru PRE/CONFIRM;
- MAY fi true pentru OPEN_NOW;
- nu este condiție pentru existența PRE/CONFIRM lifecycle candidates.

---

## 7. SIGNAL EVENT IS NOT DELIVERY

Construirea unui `SignalEvent` înseamnă doar existența unui candidat intern engine-to-distribution.

Nu dovedește și nu autorizează:
- route selection
- entitlement
- destination resolution
- Telegram publication
- external visibility
- outcome registration
- broker execution

**SignalEvent construction alone MUST NOT be classified as `EMITTED`.**

---

## 8. FORBIDDEN DIRECT PATHS

Sunt interzise:
- strategy -> signal direct
- score -> signal direct
- expiry -> signal direct
- raw legacy dict -> Telegram direct
- DecisionObject -> SignalEvent fără exact-stage FSM handoff
- transition-event existence -> automatic SignalEvent
- stage_handoff_ready -> automatic broker execution
- SignalEvent -> Telegram bypassing distribution router
- SignalEvent construction -> EMITTED

---

## 9. EXECUTION OUTCOME FAMILIES

Signal engine trebuie să poată exprima:
- `EMITTED`
- `NOT_EMITTED`
- `BLOCKED`
- `SKIPPED`
- `FAILED`
- `DEFERRED`

Acestea sunt signal-engine execution truth și trebuie separate de strategic, FSM și route-level truth.

---

## 10. EMITTED FAMILY

`EMITTED` este final execution evidence că cel puțin o publicare autorizată downstream a reușit.

Necesită:
- linked governed publication evidence;
- cel puțin un `route_publish_result` sau dovadă canonic echivalentă de succes;
- correlation cu execution attempt și signal/stage.

Insuficiente pentru EMITTED:
- FSM acceptance;
- SignalEvent construction;
- route selection fără publish success;
- publisher intent fără success evidence.

Exact route-by-route truth rămâne la distribution.

---

## 11. NOT_EMITTED FAMILY

`NOT_EMITTED` descrie non-emission fără technical failure.

Exemple:
- stage_handoff_ready=false din motiv non-blocker explicit;
- readiness insuficient;
- candidate nu poate fi format coerent;
- setup nu a ajuns la un execution-relevant candidate.

Nu trebuie confundat cu strategic reject, BLOCKED sau FAILED.

---

## 12. BLOCKED FAMILY

`BLOCKED` descrie oprirea prin regulă explicită.

Exemple:
- cooldown
- focus/watchlist gating
- duplicate prevention
- policy/control guardrail
- invariant blocker
- channel/system gate aplicabil la execution boundary

Reason/blocker trebuie înregistrat explicit.

---

## 13. SKIPPED FAMILY

`SKIPPED` descrie o decizie de flux de a nu continua fără technical failure.

Exemple:
- opportunity window depășit
- setup superseded
- flow branch intenționat neexecutat
- alt eveniment canonical prioritar a preluat flow-ul

---

## 14. FAILED FAMILY

`FAILED` înseamnă că un path intenționa să continue, dar a eșuat tehnic/infrastructural.

Exemple:
- candidate/payload construction exception
- serialization failure
- transport/infrastructure error după handoff către path-ul relevant
- observability persistence failure pentru un event obligatoriu, dacă policy îl clasifică astfel

Trebuie separat de NOT_EMITTED și BLOCKED.

---

## 15. DEFERRED FAMILY

`DEFERRED` înseamnă că există un path/candidate valid, dar execuția downstream este deliberat amânată sau nu este încă activată.

În remedierea pre-distribution curentă:
- SignalEvent valid;
- distribution intentionally disabled/not invoked;
- outcome MUST fi `DEFERRED` cu reason explicit.

Baseline reason poate exprima clar că distribution nu este activată, fără a pretinde fail sau visibility.

---

## 16. STAGE-SPECIFIC HANDLING

### 16.1 PRE
PRE poate deveni SignalEvent candidate după exact-stage FSM handoff. `trade_execution_ready=false`. External visibility depinde integral de distribution policy.

### 16.2 CONFIRM
CONFIRM poate deveni SignalEvent candidate după exact-stage FSM handoff și continuity validation. `trade_execution_ready=false`. External visibility depinde de distribution.

### 16.3 OPEN_NOW
OPEN_NOW poate deveni SignalEvent candidate numai după lifecycle/focus/actionability valide și exact-stage FSM handoff. `trade_execution_ready` MAY fi true. External publication rămâne downstream.

---

## 17. PAYLOAD / SIGNAL EVENT CONSTRUCTION PRINCIPLE

SignalEvent trebuie construit din contracte canonice și evidence real.

Minimum semantic families pot include:
- signal_id
- symbol
- timeframe/context
- stage
- direction
- score/evidence summary unde contractul o cere
- buffer semantics canonice
- model expiry / timing evidence
- candle/setup correlation
- schema/version metadata

Payload-ul nu devine adevăr strategic primar și nu poate inventa valori lipsă.

---

## 18. EXECUTION GATING PRINCIPLE

Înainte de candidate construction / downstream handoff, signal engine verifică:
- exact-stage FSM acceptance
- stage_handoff_ready
- lifecycle/identity consistency
- absence of execution blockers
- candidate schema coherence
- duplicate protection
- distribution authorization state înainte de route invocation

Dacă o condiție lipsește, outcome trebuie clasificat explicit.

---

## 19. DUPLICATE / FLOOD CONTROL

Engine-side protection poate include:
- stage/candle duplicate suppression
- signal uniqueness
- repeated setup suppression
- cooldown/anti-flood controls unde ownership-ul este engine-side

Distribution-side dedup rămâne separat. Duplicate suppression trebuie observabilă și nu trebuie să corupă stable signal identity.

---

## 20. RELATION TO FSM

FSM decide truth operațional și exact-stage handoff. Signal engine consumă acea semantică și materializează candidate/result.

Signal engine nu poate reinterpretă un blocker/no-op ca acceptance și nu poate folosi generic `accepted=true` dacă exact-stage release nu este demonstrat.

---

## 21. RELATION TO DECISIONOBJECT

DecisionObject este strategic truth auxiliar pentru signal engine.

Signal engine îl poate utiliza pentru:
- payload evidence
- signal identity/context
- stage/direction/time/score fields canonice

Dar FSM verdict rămâne authority pentru operational release.

---

## 22. RELATION TO DISTRIBUTION

`SignalEvent` este obiectul engine-to-distribution.

Distribution router deține:
- route selection
- entitlement
- destination mapping
- publish/skip policy per route
- route-level dedup/counters conform propriului canon

Signal engine nu fabrică destination truth înainte de routing și nu bypass-ează router-ul.

---

## 23. RELATION TO OBSERVABILITY

Observability trebuie să poată răspunde:
- ce handoff FSM a intrat în signal engine?
- stage-ul a fost acceptat?
- SignalEvent a fost construit?
- ce execution outcome a rezultat?
- de ce?
- routing începuse sau nu?
- ce publication evidence a susținut eventual EMITTED?

Execution truth nu poate exista doar într-un generic decision debug blob.

---

## 24. SIGNAL_EXECUTION_RESULT EVENT

Event schema trebuie să definească `signal_execution_result` ca event family dedicată signal-engine truth.

Poate exista:
- checkpoint pre-distribution, de exemplu DEFERRED;
- result ulterior, când distribution este activă;

Evenimentele pentru același attempt trebuie corelate prin `execution_attempt_id` și signal/stage identity.

`signal_execution_result` nu înlocuiește FSM events sau route events.

---

## 25. DELIVERY / EXECUTION TRACE REQUIREMENT

Pentru fiecare execution attempt material trebuie păstrat minimum:
- `execution_attempt_id`
- signal/setup correlation identity
- `signal_id` unde există
- symbol
- timeframe/context unde există
- stage unde există
- execution outcome
- reason/blocker/failure detail
- timestamp
- destination state/context
- candidate/payload reference unde există
- linked FSM handoff evidence
- linked publication evidence dacă outcome=EMITTED

Înainte de routing:
- `destination_state = PRE_DISTRIBUTION_UNRESOLVED`

Acest value înseamnă că nicio rută nu a fost încă evaluată; nu este fail și nu este publish authorization.

---

## 26. STRATEGY / FSM / EXECUTION / DISTRIBUTION SEPARATION

Nu se confundă:
- strategic REJECT/NO_SIGNAL;
- FSM WAIT/PREPARE/CONFIRM/OPEN_NOW/REJECT/BLOCKED/DEGRADED;
- execution EMITTED/NOT_EMITTED/BLOCKED/SKIPPED/FAILED/DEFERRED;
- route publish attempt/result;
- external stage visibility;
- outcome settlement.

Fiecare truth domain trebuie corelat, nu colapsat.

---

## 27. LEGACY `signal_emitted` SEMANTICS

În modelul v3 propus, legacy `signal_emitted` nu mai este sursa primară pentru noua execution truth deoarece numele poate confunda candidate generation cu successful publication.

La migrare:
- poate fi păstrat ca compatibility/historical event;
- noile execution decisions folosesc `signal_execution_result`;
- governed external visibility folosește `signal_stage_visible` și route publication evidence.

Nicio reinterpretare retroactivă a istoricului nu este permisă fără migration note explicită.

---

## 28. REJECTION VS NON-EMISSION RULE

Signal engine nu confundă:
- strategic reject
- FSM reject/block
- execution not_emitted
- execution blocked
- execution skipped
- execution failed
- execution deferred
- distribution publish failure

Separarea este obligatorie pentru forensic reconstruction.

---

## 29. FORBIDDEN EXECUTION PATTERNS

Interzise:
- emitere directă din score/expiry/DecisionObject
- transition event folosit ca handoff implicit
- SignalEvent candidate tratat ca publication
- EMITTED fără downstream success evidence
- PRE/CONFIRM excluse din lifecycle doar pentru că `trade_execution_ready=false`
- payload final tratat ca strategic truth
- route truth inventat înainte de router
- generic debug ca singura execution evidence
- broker execution activat prin acest contract

---

## 30. CODE ALIGNMENT RULE

Implementarea trebuie să răspundă clar:
- ce handoff post-FSM consumă?
- unde validează requested/accepted stage?
- cum separă stage_handoff_ready de trade_execution_ready?
- cum construiește PRE/CONFIRM/OPEN_NOW SignalEvent candidates?
- cum previne duplicatele?
- cum clasifică toate execution outcomes?
- cum produce `signal_execution_result`?
- cum demonstrează EMITTED prin publication evidence?
- cum trimite candidate către distribution fără bypass?

Dacă nu, alignment este incomplet.

---

## 31. PROMOTION AND MIGRATION RULE

La promovare:
- v3 devine singura active signal-execution authority;
- v2 este mutat în `canonical/superseded` cu traceability;
- toate active references către v2 sunt reparate atomic;
- FSM, Module Interface, Event Schema, Observability, root stack și master index trebuie să fie versiuni compatibile;
- runtime rămâne neschimbat până după post-promotion canonical re-audit.

---

## 32. FINAL PRINCIPLE

Signal engine este execution layer dintre FSM și distribution.

El trebuie să fie:
- separat de strategic/FSM truth
- explicit în exact-stage gating
- capabil să construiască governed SignalEvent candidates
- incapabil să confunde candidate construction cu delivery
- capabil să distingă execution outcome families
- corelat complet cu observability și route evidence
- incapabil să activeze broker execution implicit

Aceasta este specificația completă propusă a signal execution layer v3.