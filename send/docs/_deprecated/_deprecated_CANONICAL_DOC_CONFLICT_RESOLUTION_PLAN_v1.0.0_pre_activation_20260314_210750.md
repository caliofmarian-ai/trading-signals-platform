BINARYBOT CANONICAL SPECIFICATION

CANONICAL DOC CONFLICT RESOLUTION PLAN

Version: 1.0.0
Status: Canonical Governance Document
Scope: Documentation Alignment / Canon Freeze Preparation

Dependencies:

- STRATEGY_ENGINE_ARCHITECTURE_MAP_v1.0.0.md
- DECISION_OBJECT_CANONICAL_SPEC_v1.0.0.md
- FSM_DECISION_ENGINE_SPEC_v1.0.0.md
- CANONICAL_DOC_REALITY_REPORT_v1.0.0.md
- DECISION_OBJECT_INTEGRATION_AUDIT_v1.0.0.md

---

1. PURPOSE OF THIS DOCUMENT

Acest document definește planul oficial de rezolvare a conflictelor din documentația canonică a sistemului BinaryBot.

Scopul planului este:

- identificarea documentelor care conțin concepte contradictorii
- stabilirea documentelor care rămân canonice
- definirea documentelor care trebuie patch-uite sau rescrise
- stabilirea ordinii de corectare a documentației

Acest plan trebuie finalizat înainte de orice audit al codului.

---

2. FUNDAMENTAL PRINCIPLE

În arhitectura BinaryBot:

DOCUMENTATION
DEFINES
SYSTEM ARCHITECTURE

și

CODE
IMPLEMENTS
DOCUMENTATION

Prin urmare:

documentation conflicts
must be resolved
before code audit

---

3. CURRENT DOCUMENTATION STATE

Documentația existentă provine din mai multe faze ale proiectului.

Acest lucru a produs:

- concepte suprapuse
- modele temporale diferite
- FSM-uri diferite
- module cu responsabilități amestecate

Principalele conflicte apar în jurul conceptelor:

expiry
signal generation
corridor responsibility
FSM transitions
data contracts

---

4. CANONICAL BASELINE DOCUMENTS

Următoarele documente devin baza canonică a sistemului.

STRATEGY_ENGINE_ARCHITECTURE_MAP_v1.0.0.md
DECISION_OBJECT_CANONICAL_SPEC_v1.0.0.md
FSM_DECISION_ENGINE_SPEC_v1.0.0.md
CANONICAL_CODE_ALIGNMENT_AUDIT_v1.0.0.md

Aceste documente stabilesc:

- arhitectura strategiei
- contractul obiectului de decizie
- mașina de stări a semnalului
- principiile de audit al codului

Toate celelalte documente trebuie aliniate la acestea.

---

5. DOCUMENT CATEGORIES

Documentele existente sunt împărțite în patru categorii.

---

CATEGORY A — CANONICAL

Documente deja aliniate cu noul model.

Acestea devin baza sistemului.

---

CATEGORY B — PATCH REQUIRED

Documente care sunt parțial compatibile dar conțin concepte vechi.

Acestea trebuie corectate.

---

CATEGORY C — REWRITE REQUIRED

Documente care conțin conflicte majore cu noua arhitectură.

Acestea trebuie rescrise complet.

---

CATEGORY D — DEPRECATED

Documente care nu mai sunt relevante pentru noul model.

Acestea trebuie mutate în:

/docs/_deprecated

---

6. PRIMARY DOCUMENTS TO ALIGN

Următoarele documente trebuie evaluate și aliniate.

ALGO_SPEC.md
SR_CORRIDOR_ENGINE_SPEC.md
SIGNAL_ENGINE_SPEC.md
SIGNAL_TIME_MODEL_SPEC.md
OBSERVABILITY_SPEC.md

---

7. CONFLICT TYPES

Auditul documentației a identificat trei tipuri principale de conflicte.

---

TYPE 1 — EXPIRY MODEL CONFLICT

Documentele vechi folosesc concepte precum:

expiry_minutes
recommended expiry
expiry optimization

Aceste concepte amestecă:

model_expiry
execution expiry

Modelul canonic separă aceste concepte.

---

TYPE 2 — STRATEGY / SIGNAL MIX

Unele documente definesc strategia ca generator direct de semnale.

Modelul canonic definește:

Strategy → DecisionObject
FSM → state decision
Signal Engine → message delivery

---

TYPE 3 — CORRIDOR RESPONSIBILITY CONFLICT

Unele documente permit corridor engine să calculeze expiry.

Modelul canonic definește:

Corridor Engine → geometry
Time Model → temporal feasibility

---

8. DOCUMENT PATCH ORDER

Rezolvarea conflictelor trebuie făcută într-o ordine strictă.

---

STEP 1

Alinierea documentului:

ALGO_SPEC.md

Acest document trebuie modificat pentru a produce:

DecisionObject

---

STEP 2

Corectarea documentului:

SR_CORRIDOR_ENGINE_SPEC.md

Responsabilitatea acestuia devine:

corridor detection only

---

STEP 3

Corectarea documentului:

SIGNAL_ENGINE_SPEC.md

Acesta trebuie să consume:

DecisionObject.execution

---

STEP 4

Alinierea documentului:

SIGNAL_TIME_MODEL_SPEC.md

Trebuie să reflecte separarea:

model_expiry
execution expiry

---

STEP 5

Actualizarea documentului:

OBSERVABILITY_SPEC.md

Acesta trebuie să logheze:

DecisionObject
state transitions
reject reasons
execution parameters

---

9. CANON FREEZE

După finalizarea patch-urilor documentare se declară:

CANONICAL DOCUMENT FREEZE

Aceasta înseamnă:

- documentația devine referință oficială
- orice modificare ulterioară necesită versiune nouă

---

10. POST-RESOLUTION PHASE

După rezolvarea conflictelor documentare urmează:

REAL CODE ALIGNMENT AUDIT

Această etapă verifică:

documentation vs real implementation

---

11. FINAL PRINCIPLE

Arhitectura BinaryBot este construită pe separarea clară a responsabilităților.

Strategy Model
produces
DecisionObject

FSM
interprets
DecisionObject

Signal Engine
delivers
execution messages

Această separare garantează:

- consistența sistemului
- auditabilitatea deciziilor
- stabilitatea evoluției strategiei.