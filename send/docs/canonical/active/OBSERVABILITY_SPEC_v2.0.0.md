# OBSERVABILITY_SPEC_v2.0.0


Path: /opt/binarybot/docs/canonical/active/OBSERVABILITY_SPEC_v2.0.0.md  
Version: 2.0.0  
Status: Canonical Active Observability Specification  
Owner: BinaryBot / DROPi Signals  
Scope: End-to-end observability, auditability, rejection analytics, and semantic traceability across strategy, DecisionObject, FSM, and signal execution  

Linked Documents:
- /opt/binarybot/docs/canonical/active/CANONICAL_STRATEGY_STACK_v1.0.0.md
- /opt/binarybot/docs/canonical/active/ALGO_SPEC_v2.0.0.md
- /opt/binarybot/docs/canonical/active/DECISION_OBJECT_CANONICAL_SPEC_v1.0.0.md
- /opt/binarybot/docs/canonical/active/FSM_DECISION_ENGINE_SPEC_v1.0.0.md
- /opt/binarybot/docs/canonical/active/SIGNAL_ENGINE_EXECUTION_SPEC_v2.0.0.md
- /opt/binarybot/docs/canonical/active/OBSERVABILITY_LOGGING_SPEC_v2.0.0.md
- /opt/binarybot/docs/canonical/active/EVENT_SCHEMA_SPEC_v2.0.0.md
- /opt/binarybot/docs/canonical/active/DECISION_AUDIT_SPEC_v2.0.0.md
- /opt/binarybot/docs/canonical/active/FAILURE_RECOVERY_SPEC_v2.0.0.md


Depends on:
- canonical/active/CANONICAL_STRATEGY_STACK_v1.0.0.md
- canonical/active/ALGO_SPEC_v2.0.0.md
- canonical/active/DECISION_OBJECT_CANONICAL_SPEC_v1.0.0.md
- canonical/active/FSM_DECISION_ENGINE_SPEC_v1.0.0.md
- canonical/active/SIGNAL_ENGINE_EXECUTION_SPEC_v2.0.0.md

---

## 1. PURPOSE

Acest document definește specificația canonică de observability pentru BinaryBot.

Observability are rolul de a face sistemul:
- explicabil
- auditabil
- debuggable
- replayable
- măsurabil
- optimizabil

Observability nu este doar logging brut.
Observability este layerul semantic care permite înțelegerea traseului complet al unui setup,
de la contextul strategic până la emiterea sau moartea semnalului.

---

## 2. CORE PRINCIPLE

Observability trebuie să urmărească **lanțul complet al semnificației**.

Lanțul canonic este:
1. market model
2. corridor engine
3. time model
4. scoring
5. `DecisionObject`
6. FSM
7. signal engine

Prin urmare, observability nu trebuie construit doar la nivel de output final.
Trebuie să poată vedea unde s-a rupt sau unde s-a confirmat fluxul.

---

## 3. OBSERVABILITY GOALS

Sistemul de observability trebuie să poată răspunde clar la întrebările:

- ce setup a fost evaluat?
- ce context strategic exista?
- ce corridor a fost identificat?
- ce a spus time modelul?
- ce scor a rezultat?
- ce `DecisionObject` a fost produs?
- ce a decis FSM-ul?
- s-a emis sau nu s-a emis semnalul?
- dacă nu, de ce nu?
- în ce etapă a murit?

Dacă nu putem răspunde la aceste întrebări,
observability este incompletă.

---

## 4. WHAT OBSERVABILITY IS NOT

Observability nu este:
- doar stdout logging
- doar erori tehnice
- doar mesaje Telegram admin
- doar metrici numerice fără context semantic
- substitut pentru contractele canonice ale strategiei
- scuză pentru a lăsa sistemul opac și a reconstrui manual cauza

---

## 5. REQUIRED COVERAGE LAYERS

Observability trebuie să acopere minimum următoarele layere:

- strategy context layer
- structure / corridor layer
- time layer
- scoring layer
- `DecisionObject` layer
- FSM layer
- signal execution layer
- failure / rejection / degradation layer

Acest coverage este obligatoriu.

---

## 6. PRIMARY OBSERVABILITY OBJECTIVE

Obiectivul principal este:

**orice setup relevant trebuie să poată fi urmărit semantic de la naștere până la emitere, blocare, degradare, skip sau moarte.**

Aceasta este regula canonică centrală.

---

## 7. TRACEABILITY PRINCIPLE

Fiecare setup relevant trebuie să aibă o identitate de corelare suficientă pentru a conecta:

- contextul de intrare
- evaluarea structurală
- evaluarea temporală
- scorul
- `DecisionObject`
- starea FSM
- verdictul de execuție
- orice reject / degrade / fail / skip

Acest principiu este esențial pentru replay și audit.

---

## 8. MINIMUM CORRELATION FIELDS

Sistemul de observability trebuie să poată asocia minimum:

- setup correlation id
- symbol
- side / direction
- timeframe sau context temporal relevant
- evaluation timestamp
- cycle / run id dacă există
- stage identifier
- outcome family

Numele exacte pot varia,
dar aceste tipuri de corelare trebuie să existe.

---

## 9. STRATEGY OBSERVABILITY REQUIREMENT

Layerul strategic trebuie să poată expune semantic:

- context summary
- structure summary
- time summary
- score summary
- gating summary

Nu este obligatoriu să expună toate valorile brute,
dar trebuie să expună adevărul semantic relevant pentru audit.

---

## 10. DECISIONOBJECT OBSERVABILITY REQUIREMENT

Observability trebuie să poată vedea:
- dacă `DecisionObject` a fost produs
- ce versiune de contract a avut
- ce familii semantice a conținut
- dacă a conținut reject / degrade semantics
- ce material a fost predat FSM-ului

`DecisionObject` este nod central de observability.

---

## 11. FSM OBSERVABILITY REQUIREMENT

Observability trebuie să poată vedea:
- starea / outcome-ul FSM
- familia semantică a stării
- motivele majore ale stării
- tranzițiile importante
- dacă setup-ul a progresat, a stagnat, s-a degradat sau a fost respins

FSM-ul trebuie să fie observabil semantic, nu doar numeric sau textual brut.

---

## 12. SIGNAL EXECUTION OBSERVABILITY REQUIREMENT

Observability trebuie să poată vedea:
- dacă signal engine-ul a încercat emiterea
- ce outcome de execuție a rezultat
- dacă a existat emitere, blocare, skip, defer sau fail
- ce canal / destinație a fost implicată
- ce payload version sau referință a fost folosită

---

## 13. REJECTION ANALYTICS PRINCIPLE

Sistemul trebuie să poată analiza motivele pentru care semnalele:
- nu au ajuns la execuție
- au murit pe traseu
- au fost respinse
- au fost degradate sub prag
- au fost blocate operațional

Aceasta este componenta de rejection analytics
și este parte canonică a observability-ului, nu anexă opțională.

---

## 14. REQUIRED REJECTION QUESTIONS

Observability trebuie să poată răspunde minimum la:

- unde a murit setup-ul?
- a murit strategic, în FSM sau la execuție?
- a fost reject hard sau soft?
- a fost degradare progresivă?
- a fost blocaj de policy / focus / guardrail?
- a fost fail tehnic sau non-emission logică?

---

## 15. STAGE-OF-DEATH MODEL

Orice setup care nu ajunge la emitere trebuie, ideal, să poată fi clasificat printr-un stage-of-death recognoscibil.

Stage-urile tipice includ:
- strategy gate
- structure gate
- time gate
- score gate
- `DecisionObject` degradation / reject
- FSM reject / wait / blocked path
- signal execution non-emission / block / fail

Aceste stage-uri pot fi rafinate,
dar ideea de stage-of-death este canonică.

---

## 16. DEGRADATION ANALYTICS PRINCIPLE

Observability trebuie să surprindă nu doar verdictul final,
ci și traseul de degradare.

Exemple:
- setup inițial bun care s-a slăbit
- time pressure crescută
- score care a coborât sub prag
- FSM care a mutat outcome-ul spre `DEGRADED`
- signal engine care a refuzat emiterea din readiness insuficient

Fără această vizibilitate,
optimizarea strategiei devine oarbă.

---

## 17. EXPLANATION REQUIREMENT

Pentru fiecare decizie relevantă,
sistemul trebuie să poată produce explanation snippets suficiente pentru a înțelege:
- contextul
- structura
- timpul
- scorul
- verdictul
- execuția sau non-execuția

Explicațiile pot fi scurte,
dar trebuie să fie semantic utile.

---

## 18. METRICS VS SEMANTICS RULE

Metricile numerice sunt utile,
dar nu suficiente.

Observability canonic în BinaryBot trebuie să combine:
- metrici
- stări semantice
- motive
- corelare
- outcome families

Un dashboard doar cu numere nu este observability complet.

---

## 19. ADMIN / OPERATOR VISIBILITY RULE

Panoul admin și instrumentele de control trebuie să poată consuma rezultatele observability-ului într-o formă structurată.

Asta înseamnă că observability trebuie să poată alimenta:
- health views
- rejection summaries
- stage-of-death summaries
- signal flow summaries
- debug / audit drilldown

Acest document nu definește UX-ul panoului,
dar definește ce adevăr trebuie să fie disponibil pentru acel panou.

---

## 20. TELEGRAM / ALERTING RELATION

Canalele administrative, alertele și mesajele de control pot consuma date derivate din observability,
dar nu sunt ele însele observability-ul canonic.

Telegram admin notifications pot fi o suprafață de expunere,
nu sursa fundamentală de adevăr.

---

## 21. STORAGE / EVENT MODEL PRINCIPLE

Observability poate fi implementat prin evenimente, loguri structurate, snapshot-uri, jsonl-uri sau alte mecanisme,
dar trebuie să păstreze separarea semantică dintre layere.

Important este ca modelul de stocare să permită:
- corelare
- filtrare
- audit
- replay
- analytics

---

## 22. REQUIRED OUTCOME FAMILIES FOR OBSERVABILITY

Observability trebuie să poată distinge minimum următoarele familii de outcome:

- strategic accept / degrade / reject
- FSM wait / confirm / open_now / reject / blocked / degraded
- signal emitted / not_emitted / blocked / skipped / failed / deferred

Aceste familii nu trebuie amestecate într-o singură etichetă opacă.

---

## 23. FORBIDDEN OBSERVABILITY PATTERNS

Sunt interzise ca modele canonice active:

- imposibilitatea de a corela setup-ul pe etape
- imposibilitatea de a spune unde a murit semnalul
- logging fără semantică recognoscibilă
- doar payload final fără istoric de decizie
- doar erori tehnice fără reject / degrade semantics
- amestecarea outcome-urilor strategice, FSM și execuție într-un singur blob neclar

---

## 24. CODE ALIGNMENT RULE

Orice implementare de observability trebuie să poată răspunde clar la întrebările:

- cum este corelat un setup de la strategie la execuție?
- unde este logat / emis `DecisionObject`?
- unde este logat outcome-ul FSM?
- unde este logat outcome-ul signal engine?
- cum sunt exprimate reject reason, degrade path și stage-of-death?
- cum pot fi consumate aceste date de admin tooling și audit?

Dacă aceste răspunsuri nu sunt clare,
alinierea codului este incompletă.

---

## 25. FINAL PRINCIPLE

Observability în BinaryBot este stratul care face întregul sistem inteligibil.

El trebuie să fie:
- end-to-end
- semantic
- corelat
- auditabil
- util pentru rejection analytics
- util pentru admin / operator tooling
- suficient pentru a explica de ce un semnal a trăit, a murit sau a fost emis

Aceasta este specificația canonică activă de observability.

## 17. Intelligence Pipeline Evidence Flow

This section absorbs bounded content from INTELLIGENCE_DATA_PIPELINE_DEFINITION.md.

### 17.1 Evidence continuity
Raw logs remain canonical evidence inputs to intelligence processing, and derived pipeline outputs must preserve traceability back to source event classes.

### 17.2 Admin/research utility
Aggregated intelligence outputs may feed diagnostics and research surfaces without mutating runtime truth.
