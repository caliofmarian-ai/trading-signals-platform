# DOCUMENT_NORMALIZATION_AND_DEPRECATION_PLAN_v1.0.0

Version: 1.0.0  
Status: Canonical Planning Document  
Owner: BinaryBot / DROPi Signals  
Scope: Documentation normalization, canonical stack locking, deprecation routing, reference repair  
Depends on:
- STEP 111 — FULL_DOCUMENT_CONSISTENCY_AUDIT
- CANONICAL_REFACTOR_PLAN_v1.0.0.md
- IMPLEMENTATION_STEP_PLAN_v1.0.0.md
- CANONICAL_CODE_ALIGNMENT_MATRIX_v1.0.0.md
- CANONICAL_CODE_ALIGNMENT_AUDIT_v1.0.0.md
- ALGO_SPEC_v2.0.0.md
- DECISION_OBJECT_CANONICAL_SPEC_v1.0.0.md
- FSM_DECISION_ENGINE_SPEC_v1.0.0.md
- SIGNAL_TIME_MODEL_SPEC_v2.0.0.md
- SIGNAL_ENGINE_EXECUTION_SPEC_v2.0.0.md
- SR_CORRIDOR_ENGINE_SPEC_v2.0.0.md
- OBSERVABILITY_SPEC_v2.0.0.md
- TIME_MODEL_CANON_v1.0.0.md
- CANONICAL_DOCUMENT_GRAPH_v1.0.0.md
- CANONICAL_DOC_DEPRECATION_PLAN_v1.0.0.md
- CANONICAL_DOC_CONFLICT_RESOLUTION_PLAN_v1.0.0.md
- CANONICAL_DOC_REALITY_REPORT_v1.0.0.md

---

# 1. PURPOSE

Acest document definește planul oficial de normalizare a documentației pentru stack-ul strategic BinaryBot.

Scopul acestui document este:

- să blocheze oficial setul de documente canonice active
- să separe explicit documentele canonice de documentele legacy / deprecated
- să elimine amestecul dintre vocabularul vechi și vocabularul nou
- să repare referințele lipsă dintre documentele canonice
- să definească ordinea de patchuire a documentelor înaintea oricărei migrări majore de cod
- să reducă riscul ca implementarea să urmeze documente contradictorii

Acest document nu modifică logica de cod.

Acest document stabilește doar ordinea oficială de curățare și stabilizare a stratului documentar.

---

# 2. CONTEXT

Auditul complet STEP 111 a demonstrat că ecosistemul de documente conține simultan:

- documente canonice noi, orientate pe modelul `DecisionObject`
- documente mixte, care combină formule vechi și formule noi
- documente runtime / arhitecturale care descriu încă fluxuri vechi
- documente vechi care trebuie scoase explicit din uz

Problema principală nu mai este lipsa de documentație.

Problema principală este **inconsistența documentației existente**.

Prin urmare, înainte de orice refactor major de cod, trebuie finalizată **normalizarea documentară**.

---

# 3. DOCUMENT NORMALIZATION OBJECTIVE

Obiectivul final al normalizării este:

- să existe un singur stack oficial al strategiei
- să existe un singur vocabular oficial al timpului și deciziei
- să existe un singur contract oficial între `strategy_v2.py` și `signal_engine.py`
- să existe marcaj explicit pentru documentele deprecated
- să existe trasabilitate clară între documente canonice, module runtime și audituri

---

# 4. OFFICIAL CANONICAL VOCABULARY

Începând cu normalizarea v1.0.0, vocabularul oficial canonic este:

## 4.1 Time Model Vocabulary

- `price_speed`
- `buffer_distance`
- `t_needed`
- `t_needed_adjusted`
- `model_expiry`
- `model_time_reach_ratio`
- `corridor_time_pressure`
- `time_state`

## 4.2 Decision Vocabulary

- `DecisionObject`
- `decision_state`
- `decision_fsm`
- `score_total`
- `score_components`
- `corridor_width`
- `execution_model`

## 4.3 Runtime Contract Vocabulary

- `strategy_v2.py`
- `signal_engine.py`
- `DecisionObject`
- `canonical output contract`
- `compatibility layer`
- `shadow mode` (numai dacă este explicit marcat ca temporar de migrare)

---

# 5. FORBIDDEN LEGACY TERMS IN CANONICAL DOCS

Următorii termeni nu mai trebuie folosiți ca termeni canonici principali în documentele active:

- `expiry_reach_ratio`
- `expiry_minutes` ca metrică finală unică a deciziei
- `buffer_price` dacă este folosit în locul lui `buffer_distance`
- contracte legacy de tip dict ca model canonic final
- descrieri runtime care omit `DecisionObject` acolo unde documentul descrie arhitectura nouă

Acești termeni pot apărea doar în unul din următoarele contexte:

- secțiune de migrare
- secțiune de compatibilitate temporară
- secțiune de audit istoric
- secțiune de deprecated / superseded

---

# 6. OFFICIAL CANONICAL STACK

Stack-ul oficial al strategiei devine:

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
DECISION FSM
   ↓
DECISION OBJECT
   ↓
EXECUTION MODEL
   ↓
SIGNAL ENGINE
   ↓
OBSERVABILITY / AUDIT```


Acesta este fluxul documentar și conceptual oficial.

Orice document care descrie alt flux trebuie:

fie patchuit

fie marcat deprecated

fie mutat în context istoric / migrare



---

# 7. ROOT CANONICAL DOCUMENT SET

Următorul set de documente devine setul canonical root pentru stack-ul strategic:

1. ALGO_SPEC_v2.0.0.md


2. TIME_MODEL_CANON_v1.0.0.md


3. SR_CORRIDOR_ENGINE_SPEC_v2.0.0.md


4. DECISION_OBJECT_CANONICAL_SPEC_v1.0.0.md


5. FSM_DECISION_ENGINE_SPEC_v1.0.0.md


6. SIGNAL_TIME_MODEL_SPEC_v2.0.0.md


7. SIGNAL_ENGINE_EXECUTION_SPEC_v2.0.0.md 


8. OBSERVABILITY_SPEC_v2.0.0.md


9. CANONICAL_CODE_ALIGNMENT_MATRIX_v1.0.0.md


10. CANONICAL_CODE_ALIGNMENT_AUDIT_v1.0.0.md


11. CANONICAL_REFACTOR_PLAN_v1.0.0.md


12. IMPLEMENTATION_STEP_PLAN_v1.0.0.md
  

Aceste documente trebuie tratate ca stratul oficial activ.


---

# 8. ROOT SUPPORTING GOVERNANCE DOCUMENTS

Următoarele documente rămân active ca documente de guvernanță și control, nu ca surse primare de logică:

CANONICAL_DOC_REALITY_REPORT_v1.0.0.md

CANONICAL_DOC_CONFLICT_RESOLUTION_PLAN_v1.0.0.md

CANONICAL_DOC_DEPRECATION_PLAN_v1.0.0.md

CANONICAL_DOCUMENT_GRAPH_v1.0.0.md

CANONICAL_REFACTOR_PLAN_v1.0.0.md

IMPLEMENTATION_STEP_PLAN_v1.0.0.md


Aceste documente pot orienta procesul, dar nu trebuie să redefinească logica matematică dacă aceasta este deja definită în documentele root canonical.


---

# 9. DOCUMENT CLASSES

Toate documentele din docs/ trebuie clasificate în una dintre cele patru clase:

9.1 Canonical Active

Document oficial activ, normativ, folosit direct pentru implementare.

9.2 Canonical Supporting

Document de guvernanță, audit, mapping, planning sau alignment.

9.3 Transitional Migration

Document permis temporar pentru explicarea trecerii dintre vechi și nou.

9.4 Deprecated

Document istoric, înlocuit, care nu mai trebuie folosit pentru implementare directă.


---

# 10. DEPRECATION POLICY

Un document trebuie trecut în Deprecated dacă îndeplinește oricare dintre condițiile următoare:

definește logica principală folosind numai expiry_reach_ratio

definește runtime mapping vechi fără DecisionObject

dublează un document canonical mai nou fără a adăuga clarificări reale

contrazice explicit ALGO_SPEC_v2.0.0.md

contrazice DECISION_OBJECT_CANONICAL_SPEC_v1.0.0.md

contrazice FSM_DECISION_ENGINE_SPEC_v1.0.0.md

folosește vocabular vechi ca adevăr final, nu ca context de migrare

descrie patchuri one-off care au fost absorbite în specificația canonică nouă



---

# 11. IMMEDIATE DEPRECATION CANDIDATES

Pe baza auditului existent, următoarele documente trebuie tratate ca prime candidate la deprecation sau superseded status:

ALGO_SPEC.md

FSM_SPEC.md

SIGNAL_DECISION_FSM_SPEC.md

signal_time_model_and_decision_object_v1.0.0.md

WAVE1_TIME_MODEL_PATCH_SPEC_v1.0.0.md

SR_CORRIDOR_DETECTION_ENGINE_SPEC.md

SR_CORRIDOR_CODE_PATCH_PLAN.md


Aceste documente nu trebuie șterse imediat.

Ele trebuie:

marcate explicit

legate spre documentele canonice noi

scoase din traseul de implementare activă



---

# 12. MIXED DOCUMENT POLICY

Documentele identificate cu MIXED_TIME_VOCAB nu sunt automat deprecated.

Ele trebuie tratate întâi ca patch candidates.

Ordinea de tratament pentru un document mixed este:

1. identificarea secțiunilor legacy


2. separarea secțiunilor de migrare de secțiunile canonice


3. promovarea vocabularului nou ca sursă principală


4. mutarea termenilor vechi în context de compatibility / migration notes


5. reverificarea documentului după patch




---

# 13. REQUIRED REFERENCE REPAIRS

Auditul a indicat documente-cheie cu referințe lipsă.

Acestea trebuie patchuite punctual.

## 13.1 IMPLEMENTATION_STEP_PLAN_v1.0.0.md

Trebuie să conțină explicit:

strategy_v2.py

rolul său în migrarea la contractul DecisionObject


## 13.2 CANONICAL_CODE_ALIGNMENT_AUDIT_v1.0.0.md

Trebuie să conțină explicit:

strategy_v2.py

signal_engine.py

mapping către DecisionObject


## 13.3 TIME_MODEL_CANON_v1.0.0.md

Trebuie să conțină explicit:

model_time_reach_ratio

legătura cu buffer_distance

legătura cu corridor_time_pressure


## 13.4 SIGNAL_TIME_MODEL_SPEC_v2.0.0.md

Trebuie să conțină explicit:

model_time_reach_ratio

relația dintre timp, decizie și execuție


## 13.5 SIGNAL_ENGINE_EXECUTION_SPEC_v2.0.0.md

Trebuie să conțină explicit:

signal_engine.py

model_expiry

corridor_time_pressure

consumul DecisionObject ca input contractual



---

## 14. RUNTIME DOCUMENT PATCH CANDIDATES

Următoarele documente runtime / architecture trebuie revizuite pentru a alinia explicit noul contract bazat pe DecisionObject:

ARCHITECTURE.md

ARCHITECTURE_CODE_MAPPING.md

DEPLOYMENT_PROTOCOL.md

DOCUMENT_IMPLEMENTATION_MATRIX.md

INTELLIGENCE_DATA_PIPELINE_DEFINITION.md

INTELLIGENCE_FILES_AND_MODULE_MAP.md

INTELLIGENCE_LAYER_ARCHITECTURE.md

MODULE_INTERFACE_SPEC.md

RUNBOOK.md

RUNTIME_EXECUTION_TIMELINE.md

SYSTEM_ARCHITECTURE_MAP.md


Aceste documente nu trebuie presupuse deprecated din start.

Mai întâi trebuie auditate și patchuite minim pentru:

flux runtime nou

referință la DecisionObject

separarea layerului de strategie de layerul de livrare / execuție



---

## 15. DOCUMENT NORMALIZATION PHASES

Normalizarea se execută în 5 faze.

### FAZA 1 — LOCK CANONICAL STACK

Obiectiv:

confirmarea documentelor root canonice

interzicerea extinderii necontrolate a surselor normative


Livrabile:

acest document

documentul de stack canonical dacă este necesar

marcarea root set-ului oficial


###  FAZA 2 — PATCH KEY CANONICAL DOCS

Obiectiv:

repararea referințelor lipsă în documentele root canonice


Ținte minime:

IMPLEMENTATION_STEP_PLAN_v1.0.0.md

CANONICAL_CODE_ALIGNMENT_AUDIT_v1.0.0.md

TIME_MODEL_CANON_v1.0.0.md

SIGNAL_TIME_MODEL_SPEC_v2.0.0.md

SIGNAL_ENGINE_EXECUTION_SPEC_v2.0.0.md


FAZA 3 — NORMALIZE MIXED DOCS

Obiectiv:

eliminarea statutului mixed

mutarea vocabularului vechi în secțiuni de migrare / compatibility


Ținte:

toate documentele marcate MIXED_TIME_VOCAB


### FAZA 4 — APPLY DEPRECATION MARKERS

Obiectiv:

adăugarea explicită de header status pentru documentele vechi


Template minim recomandat:

Status: Deprecated
Superseded by:
- ALGO_SPEC_v2.0.0.md
- DECISION_OBJECT_CANONICAL_SPEC_v1.0.0.md
- FSM_DECISION_ENGINE_SPEC_v1.0.0.md
Reason:
- legacy time vocabulary
- superseded runtime contract

FAZA 5 — FINAL CONSISTENCY RE-AUDIT

Obiectiv:

re-scanare completă a documentelor

confirmarea reducerii conflictelor

confirmarea root stack-ului final



---

# 16. PATCH PRIORITY ORDER

Ordinea oficială de patchuire este:

1. TIME_MODEL_CANON_v1.0.0.md


2. SIGNAL_TIME_MODEL_SPEC_v2.0.0.md


3. SIGNAL_ENGINE_EXECUTION_SPEC_v2.0.0.md


4. CANONICAL_CODE_ALIGNMENT_AUDIT_v1.0.0.md


5. IMPLEMENTATION_STEP_PLAN_v1.0.0.md


6. documentele runtime / architecture


7. documentele mixed rămase


8. documentele candidate la deprecated



Motivul ordinii:

întâi reparăm miezul matematic

apoi reparăm contractul runtime

apoi reparăm documentele de mapping

abia după aceea marcăm deprecation pe stratul vechi



---

# 17. CANONICAL HEADER POLICY

Toate documentele active trebuie să aibă header clar:

Version

Status

Scope

Depends on / Dependencies

eventual Supersedes / Superseded by


Fără acest header, documentul este mai greu de clasificat și mai predispus la conflict.


---

# 18. CROSS-REFERENCE POLICY

Toate documentele root canonice trebuie să se refere explicit la documentele vecine relevante.

Exemple:

ALGO_SPEC_v2.0.0.md trebuie să trimită spre:

TIME_MODEL_CANON_v1.0.0.md

FSM_DECISION_ENGINE_SPEC_v1.0.0.md

DECISION_OBJECT_CANONICAL_SPEC_v1.0.0.md


TIME_MODEL_CANON_v1.0.0.md trebuie să trimită spre:

ALGO_SPEC_v2.0.0.md

SIGNAL_TIME_MODEL_SPEC_v2.0.0.md

DECISION_OBJECT_CANONICAL_SPEC_v1.0.0.md


SIGNAL_ENGINE_EXECUTION_SPEC_v2.0.0.md trebuie să trimită spre:

DECISION_OBJECT_CANONICAL_SPEC_v1.0.0.md

FSM_DECISION_ENGINE_SPEC_v1.0.0.md

OBSERVABILITY_SPEC_v2.0.0.md



---

# 19. IMPLEMENTATION RULE

Până la finalizarea fazelor de normalizare documentară:

nu se introduce logică nouă mare în cod pe baza documentelor mixed

nu se folosesc documente deprecated ca sursă principală de implementare

orice patch de cod trebuie să indice explicit documentul canonic pe care se bazează

orice document nou trebuie să fie validat împotriva root canonical stack



---

# 20. SUCCESS CRITERIA

Planul de normalizare este considerat finalizat numai când:

documentele root canonice sunt confirmate oficial

documentele mixed principale sunt patchuite

documentele deprecated au marker explicit

documentele runtime cunosc DecisionObject

termenii legacy nu mai apar ca adevăr final în documentele active

un re-audit complet confirmă scăderea conflictelor documentare



---

# 21. NEXT REQUIRED DOCUMENT ACTION

După acest document, următoarea livrare corectă nu este încă un patch de cod.

Următoarea livrare corectă este una dintre următoarele:

Varianta recomandată

CANONICAL_STRATEGY_STACK_v1.0.0.md

Acest document va funcționa ca root manifest scurt și clar al întregului stack strategic.

Varianta operațională imediată

Patch plan punctual pentru cele 5 documente-cheie cu referințe lipsă.

Ordinea recomandată rămâne:

1. lock stack


2. repair canonical references


3. normalize mixed docs


4. apply deprecation markers


5. re-audit


6. abia apoi cod




---

# 22. FINAL PRINCIPLE

În BinaryBot, codul nu trebuie să migreze mai repede decât documentația canonică.

Documentația canonică stabilește adevărul sistemului.

Auditul stabilește unde adevărul este fragmentat.

Normalizarea stabilește un singur adevăr operațional.

Abia după aceea refactorul de cod devine sigur, trasabil și auditabil.