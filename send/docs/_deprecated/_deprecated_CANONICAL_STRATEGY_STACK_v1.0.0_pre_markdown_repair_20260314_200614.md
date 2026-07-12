CANONICAL_STRATEGY_STACK_v1.0.0

Version: 1.0.0
Status: Canonical Root Manifest
Owner: BinaryBot / DROPi Signals
Scope: Root strategy stack, canonical authority order, module contract chain, document precedence

Depends on:

DOCUMENT_NORMALIZATION_AND_DEPRECATION_PLAN_v1.0.0.md

ALGO_SPEC_v2.0.0.md

canonical/active/TIME_MODEL_UNIFIED_CANON_v2.0.0.md

SR_CORRIDOR_ENGINE_SPEC_v2.0.0.md

DECISION_OBJECT_CANONICAL_SPEC_v1.0.0.md

FSM_DECISION_ENGINE_SPEC_v1.0.0.md

SIGNAL_ENGINE_EXECUTION_SPEC_v2.0.0.md

OBSERVABILITY_SPEC_v2.0.0.md

CANONICAL_CODE_ALIGNMENT_MATRIX_v1.0.0.md

CANONICAL_CODE_ALIGNMENT_AUDIT_v1.0.0.md

CANONICAL_REFACTOR_PLAN_v1.0.0.md

IMPLEMENTATION_STEP_PLAN_v1.0.0.md



---

1. PURPOSE

Acest document este manifestul root al stack-ului strategic BinaryBot.

Scopul lui este:

să definească setul oficial de documente canonice active

să stabilească ordinea de autoritate între documente

să definească fluxul oficial de la piață la semnal

să definească contractul oficial dintre modulele runtime

să elimine ambiguitatea atunci când două documente par să spună lucruri diferite

să ofere un punct unic de pornire pentru orice audit, patch sau refactor


Acest document nu înlocuiește specificațiile detaliate.

Acest document stabilește care specificații sunt autoritare și cum se leagă între ele.


---

2. CORE PRINCIPLE

Strategia BinaryBot nu este o singură formulă.

Strategia BinaryBot este un stack compus din layere separate, fiecare cu responsabilitate distinctă:

modelarea pieței

modelarea structurii SR / corridor

modelarea timpului

modelarea scorului

contractul DecisionObject

decizia FSM

execuția de semnal

observabilitatea și auditul


Separarea acestor layere este principiu canonic.

Niciun document nu trebuie să recombine informal aceste layere într-o singură logică opacă.


---

3. OFFICIAL STRATEGY FLOW

Fluxul oficial al strategiei este:

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
SIGNAL ENGINE
   ↓
DELIVERY / OBSERVABILITY

Acesta este singurul flux strategic oficial.

Orice document care descrie un alt flux trebuie:

fie patchuit

fie reclasificat ca transitional

fie marcat deprecated



---

4. ROOT CANONICAL DOCUMENT SET

Setul root canonical al strategiei este:

1. ALGO_SPEC_v2.0.0.md


2. canonical/active/TIME_MODEL_UNIFIED_CANON_v2.0.0.md


3. SR_CORRIDOR_ENGINE_SPEC_v2.0.0.md


4. DECISION_OBJECT_CANONICAL_SPEC_v1.0.0.md


5. FSM_DECISION_ENGINE_SPEC_v1.0.0.md


6. SIGNAL_ENGINE_EXECUTION_SPEC_v2.0.0.md


7. OBSERVABILITY_SPEC_v2.0.0.md



Aceste șapte documente formează stack-ul strategic activ.

Ele sunt documentele normative principale pentru logica de strategie.


---

5. SUPPORTING CANONICAL DOCUMENT SET

Documentele supporting canonical sunt:

1. CANONICAL_CODE_ALIGNMENT_MATRIX_v1.0.0.md


2. CANONICAL_CODE_ALIGNMENT_AUDIT_v1.0.0.md


3. CANONICAL_REFACTOR_PLAN_v1.0.0.md


4. IMPLEMENTATION_STEP_PLAN_v1.0.0.md


5. DOCUMENT_NORMALIZATION_AND_DEPRECATION_PLAN_v1.0.0.md


6. CANONICAL_DOC_REALITY_REPORT_v1.0.0.md


7. CANONICAL_DOC_CONFLICT_RESOLUTION_PLAN_v1.0.0.md


8. CANONICAL_DOC_DEPRECATION_PLAN_v1.0.0.md


9. CANONICAL_DOCUMENT_GRAPH_v1.0.0.md



Aceste documente au rol de:

audit

planning

mapping

governance

control de consistență


Ele nu trebuie să redefinească matematica dacă aceasta este deja stabilită în root canonical set.


---

6. AUTHORITY ORDER

Când apar conflicte sau ambiguități, ordinea oficială de autoritate este:

Nivel 1 — Root Canonical Strategy Specs

ALGO_SPEC_v2.0.0.md

canonical/active/TIME_MODEL_UNIFIED_CANON_v2.0.0.md

SR_CORRIDOR_ENGINE_SPEC_v2.0.0.md

DECISION_OBJECT_CANONICAL_SPEC_v1.0.0.md

FSM_DECISION_ENGINE_SPEC_v1.0.0.md

SIGNAL_ENGINE_EXECUTION_SPEC_v2.0.0.md

OBSERVABILITY_SPEC_v2.0.0.md


Nivel 2 — Alignment / Planning / Governance

CANONICAL_CODE_ALIGNMENT_MATRIX_v1.0.0.md

CANONICAL_CODE_ALIGNMENT_AUDIT_v1.0.0.md

CANONICAL_REFACTOR_PLAN_v1.0.0.md

IMPLEMENTATION_STEP_PLAN_v1.0.0.md

toate documentele canonice de audit și conflict resolution


Nivel 3 — Transitional Migration Docs

documente care explică trecerea dintre modelul vechi și modelul nou

documente de compatibilitate temporară

documente shadow / migration patch notes


Nivel 4 — Deprecated / Historical Docs

documente vechi, superseded

documente one-off

documente păstrate doar pentru trasabilitate istorică


Dacă un document de nivel mai jos contrazice un document de nivel mai sus, câștigă documentul de nivel mai sus.


---

7. OFFICIAL VOCABULARY LOCK

Vocabularul oficial al stack-ului strategic este:

7.1 Market / Structure Vocabulary

price_speed

buffer_distance

support_levels

resistance_levels

corridor_width

structure_context

volatility_state

trend_context


7.2 Time Vocabulary

t_needed

t_needed_adjusted

model_expiry

model_time_reach_ratio

corridor_time_pressure

time_state


7.3 Decision Vocabulary

score_total

score_components

decision_fsm

decision_state

DecisionObject


7.4 Runtime Vocabulary

strategy_v2.py

signal_engine.py

DecisionObject

execution_semantics

compatibility layer

shadow mode numai dacă este explicit temporar



---

8. FORBIDDEN PRIMARY TERMS

Următorii termeni nu mai pot fi utilizați ca termeni canonici primari în strategia activă:

expiry_reach_ratio

expiry_minutes ca adevăr final unic al deciziei

buffer_price ca substitut canonic pentru buffer_distance

dict legacy output drept contract final al strategiei

runtime flows care omit DecisionObject din noua arhitectură


Acești termeni pot exista doar în:

secțiuni de migrare

secțiuni de compatibilitate

secțiuni istorice

documente deprecated



---

9. MODULE CONTRACT CHAIN

Lanțul oficial de contracte între module este:

strategy_v2.py
   produces
DecisionObject
   consumed by
FSM decision layer
   produces
FSM-approved execution semantics
   consumed by
signal_engine.py
   produces
signal payload / delivery action / observability event

Aceasta este relația contractuală oficială între strategia runtime și layerul de execuție.

Orice document care descrie alt contract trebuie actualizat.


---

10. STRATEGY MODULE RESPONSIBILITIES

10.1 Market Model

Responsabil pentru:

transformarea datelor brute de piață în parametri operaționali

estimarea contextului de trend și volatilitate

estimarea price_speed

estimarea buffer_distance


Document root:

ALGO_SPEC_v2.0.0.md


10.2 SR / Corridor Engine

Responsabil pentru:

detectarea structurii relevante

definirea corridorului de lucru

evaluarea geometriei și validității structurale


Document root:

SR_CORRIDOR_ENGINE_SPEC_v2.0.0.md


10.3 Time Model

Responsabil pentru:

calculul t_needed

calculul t_needed_adjusted

calculul model_expiry

calculul model_time_reach_ratio

calculul corridor_time_pressure

derivarea time_state


Document root:

canonical/active/TIME_MODEL_UNIFIED_CANON_v2.0.0.md


10.4 Scoring Model

Responsabil pentru:

evaluarea calității setup-ului

agregarea componentelor de scor

derivarea score_total


Document root:

ALGO_SPEC_v2.0.0.md


10.5 Decision Object Contract

Responsabil pentru:

standardizarea outputului strategiei

separarea deciziei matematice de execuția de semnal

livrarea contractului strategic către layerul FSM


Document root:

DECISION_OBJECT_CANONICAL_SPEC_v1.0.0.md


10.6 Decision FSM

Responsabil pentru:

consumul DecisionObject

clasificarea setup-ului în stări operaționale

aplicarea pragurilor și regulilor de tranziție

emiterea semnificației decizionale pentru execuție


Document root:

FSM_DECISION_ENGINE_SPEC_v1.0.0.md


10.7 Signal Engine Execution

Responsabil pentru:

consumul semanticii de execuție aprobate de FSM

transformarea deciziei în semnal livrabil

compatibilitatea runtime și regulile de emitere


Document root:

SIGNAL_ENGINE_EXECUTION_SPEC_v2.0.0.md


10.8 Observability / Audit

Responsabil pentru:

trasabilitate

audit de decizie

audit de semnal

motivarea respingerilor și a tranzițiilor


Document root:

OBSERVABILITY_SPEC_v2.0.0.md



---

11. ROOT DOCUMENT PRECEDENCE BY TOPIC

11.1 Dacă există conflict despre matematica timpului

Au prioritate:

1. canonical/active/TIME_MODEL_UNIFIED_CANON_v2.0.0.md


2. ALGO_SPEC_v2.0.0.md



11.2 Dacă există conflict despre stările FSM

Au prioritate:

1. FSM_DECISION_ENGINE_SPEC_v1.0.0.md


2. DECISION_OBJECT_CANONICAL_SPEC_v1.0.0.md


3. ALGO_SPEC_v2.0.0.md



11.3 Dacă există conflict despre outputul strategiei

Au prioritate:

1. DECISION_OBJECT_CANONICAL_SPEC_v1.0.0.md


2. FSM_DECISION_ENGINE_SPEC_v1.0.0.md


3. SIGNAL_ENGINE_EXECUTION_SPEC_v2.0.0.md


4. CANONICAL_CODE_ALIGNMENT_MATRIX_v1.0.0.md



11.4 Dacă există conflict despre mapping cod ↔ documentație

Au prioritate:

1. CANONICAL_CODE_ALIGNMENT_MATRIX_v1.0.0.md


2. CANONICAL_CODE_ALIGNMENT_AUDIT_v1.0.0.md


3. IMPLEMENTATION_STEP_PLAN_v1.0.0.md



11.5 Dacă există conflict despre deprecation / status documente

Au prioritate:

1. DOCUMENT_NORMALIZATION_AND_DEPRECATION_PLAN_v1.0.0.md


2. CANONICAL_DOC_DEPRECATION_PLAN_v1.0.0.md


3. CANONICAL_DOC_CONFLICT_RESOLUTION_PLAN_v1.0.0.md




---

12. ROOT IMPLEMENTATION RULE

Niciun patch de cod nu trebuie să fie definit pe baza:

documentelor deprecated

documentelor mixed nepatchuite

documentelor runtime vechi care omit DecisionObject


Orice patch de cod trebuie să citeze explicit documentul root canonic relevant.

Exemple:

patch de time model → canonical/active/TIME_MODEL_UNIFIED_CANON_v2.0.0.md

patch de output strategy → DECISION_OBJECT_CANONICAL_SPEC_v1.0.0.md

patch de FSM → FSM_DECISION_ENGINE_SPEC_v1.0.0.md

patch de emitere semnal → SIGNAL_ENGINE_EXECUTION_SPEC_v2.0.0.md



---

13. ROOT AUDIT RULE

Orice audit viitor privind strategie / runtime trebuie să înceapă din acest document.

Ordinea corectă de audit este:

1. verifică manifestul root


2. identifică documentul root relevant pentru subiect


3. verifică documentele supporting


4. verifică runtime code mapping


5. abia apoi verifică documentele vechi pentru context istoric



Astfel se evită întoarcerea accidentală la documente vechi.


---

14. RELATION TO DEPRECATED DOCS

Documentele deprecated nu se șterg automat.

Ele rămân pentru:

trasabilitate istorică

audit

reconstrucția motivelor de migrare

rollback intelectual, nu rollback normativ


Dar ele nu mai au voie să fie folosite ca sursă primară de implementare.


---

15. RELATION TO MIXED DOCS

Documentele mixed rămân temporar active numai dacă:

încă servesc ca punte de migrare

nu contrazic direct root set-ul

sunt în curs de patch

nu sunt folosite singure pentru patchuri de cod


Scopul final este reducerea lor progresivă.


---

16. REQUIRED NEXT PATCH ORDER

După lock-ul acestui manifest, ordinea corectă este:

1. patch ALGO_SPEC_v2.0.0.md


2. patch DECISION_OBJECT_CANONICAL_SPEC_v1.0.0.md


3. patch FSM_DECISION_ENGINE_SPEC_v1.0.0.md


4. patch SR_CORRIDOR_ENGINE_SPEC_v2.0.0.md


5. patch SIGNAL_ENGINE_EXECUTION_SPEC_v2.0.0.md


6. patch OBSERVABILITY_SPEC_v2.0.0.md


7. patch documente runtime / architecture care omit, inversează sau aplatizează DecisionObject


8. aplicare status deprecated pe documentele legacy candidate


9. re-audit complet


10. abia apoi refactor major de cod




---

17. SINGLE SOURCE OF TRUTH RULE

Nu există un singur document care conține toate detaliile strategiei.

Există însă un singur stack canonic oficial.

Adevărul sistemului este definit de:

acest manifest

root canonical set

precedence rules

normalization policy


Împreună, ele formează sursa unică de adevăr operațional.


---

18. FINAL PRINCIPLE

În BinaryBot, documentația canonică trebuie să fie:

ierarhică

explicită

auditată

separată pe responsabilități

mai rapid clarificată decât codul


Acest document blochează oficial stack-ul strategic.

De aici înainte, orice patch, audit sau refactor privind strategia trebuie să pornească din acest manifest și din documentele root pe care acesta le autorizează.