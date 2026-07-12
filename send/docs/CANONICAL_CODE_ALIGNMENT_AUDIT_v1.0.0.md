# CANONICAL_CODE_ALIGNMENT_AUDIT_v1.0.0

Status: Satellite / Non-Canonical Reference
Canonical Position: Supporting document only; does not define active canonical truth.
Primary Active Canon: Refer to active canonical documents under /opt/binarybot/docs/canonical/active/

---

BINARYBOT CANONICAL SPECIFICATION

CANONICAL CODE ALIGNMENT AUDIT

Version: 1.0.0
Status: Canonical Audit Framework
Scope: Codebase Consistency / Strategy Implementation
Target: BinaryBot Runtime System

Dependencies:

- STRATEGY_ENGINE_ARCHITECTURE_MAP_v1.0.0.md
- canonical/active/DECISION_OBJECT_CANONICAL_SPEC_v1.0.0.md
- canonical/active/FSM_DECISION_ENGINE_SPEC_v1.0.0.md
- SIGNAL_ENGINE_EXECUTION_SPEC_v1.0.0.md

---

1. PURPOSE OF THIS DOCUMENT

Acest document definește procedura oficială de audit al codului față de documentația canonică.

Scopul auditului este:

- verificarea implementării reale a strategiei
- detectarea divergențelor între cod și documentație
- identificarea logicilor greșite sau redundante
- pregătirea patch-urilor necesare pentru alinierea codului

Principiul fundamental al sistemului este:

DOCUMENTATION DEFINES SYSTEM
CODE IMPLEMENTS DOCUMENTATION

---

2. AUDIT OBJECTIVE

Auditul urmărește verificarea următoarelor componente:

Strategy Engine
Time Model
Corridor Engine
Decision FSM
Signal Engine
Observability Layer

Fiecare componentă trebuie să respecte documentația canonică.

---

3. CODEBASE STRUCTURE TARGET

Auditul trebuie să analizeze fișierele din:

/opt/binarybot

Zonele principale ale codului sunt:

strategy/
engine/
signal_engine/
fsm/
telemetry/
observability/

---

4. AUDIT PRINCIPLE

Auditul compară două realități:

CANONICAL DOCUMENTATION
vs
REAL CODE IMPLEMENTATION

Rezultatul auditului trebuie să determine:

ALIGNED
PARTIAL
CONFLICT
BROKEN

---

5. STRATEGY ENGINE AUDIT

Trebuie verificat dacă strategia produce:

DecisionObject

și nu semnale directe.

---

Verificări

Codul trebuie să conțină:

market_model
time_model
scoring_model
decision_object_builder

Nu trebuie să existe:

direct signal generation
telegram message creation

în strategia matematică.

---

6. TIME MODEL AUDIT

Trebuie verificată separarea corectă între:

model_expiry_minutes

și

trade_expiry

---

Regula canonică

model_expiry_minutes
≠
execution expiry

Modelul temporal este folosit doar pentru evaluare matematică.

---

7. CORRIDOR ENGINE AUDIT

Corridor Engine trebuie să producă exclusiv:

corridor_valid
corridor_width
corridor_open_ok

---

Interdicție

Corridor Engine nu trebuie să calculeze:

expiry
recommended expiry
expiry optimization

Aceste calcule aparțin Time Model.

---

8. DECISION OBJECT AUDIT

Trebuie verificat dacă există implementarea structurii:

DecisionObject

cu componentele:

market_context
time_model
scoring
decision_state
execution
diagnostics

---

Verificări

Auditul trebuie să confirme:

DecisionObject este construit o singură dată
DecisionObject este transmis către FSM
DecisionObject nu este modificat de Signal Engine

---

9. FSM ENGINE AUDIT

FSM trebuie să implementeze exact stările canonice:

NO_SIGNAL
REJECT
PRE
CONFIRM
OPEN_NOW

---

Verificări

FSM trebuie să utilizeze exclusiv variabilele:

R = model_time_reach_ratio
P = corridor_time_pressure
S = normalized_score
W = corridor_width_score

și să respecte regulile definite în:

canonical/active/FSM_DECISION_ENGINE_SPEC_v1.0.0.md

---

10. SIGNAL ENGINE AUDIT

Signal Engine trebuie să consume:

DecisionObject.execution

și să genereze mesajele pentru utilizatori.

---

Interdicții

Signal Engine nu trebuie să recalculze:

expiry
strategy score
corridor width

Signal Engine este doar un translator al deciziei.

---

11. OBSERVABILITY AUDIT

Codul trebuie să înregistreze:

DecisionObject
state_transition
reject_reason
execution_parameters
diagnostics

---

Obiectiv

Sistemul trebuie să permită analiza:

de ce a fost generat semnalul
de ce a fost respins
de ce a fost degradat

---

12. CONFLICT TYPES

Auditul poate detecta trei tipuri majore de conflicte.

---

TYPE 1 — ARCHITECTURAL CONFLICT

Exemple:

strategy produce direct semnale
signal engine modifică strategia

---

TYPE 2 — TIME MODEL CONFLICT

Exemple:

expiry calculat în mai multe module
expiry amestecat cu model_expiry

---

TYPE 3 — FSM LOGIC CONFLICT

Exemple:

stări FSM diferite de canon
condiții diferite de cele definite

---

13. PATCH STRATEGY

Rezultatul auditului produce patch-uri de aliniere.

---

PATCH TYPE A

CODE REALIGNMENT

Refactorizarea codului pentru a respecta documentația.

---

PATCH TYPE B

MODULE EXTRACTION

Separarea logicilor amestecate.

---

PATCH TYPE C

DEPRECATED CODE REMOVAL

Eliminarea logicilor vechi.

---

14. AUDIT OUTPUT

Rezultatul auditului trebuie să includă:

listă completă a fișierelor analizate
status pentru fiecare modul
conflicte identificate
patch-uri recomandate

Acest raport devine baza pentru Wave 3 Code Refactor.

---

15. FINAL PRINCIPLE

Arhitectura BinaryBot este bazată pe separarea clară a responsabilităților:

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
- transparența deciziilor
- auditabilitatea completă a strategiei.

## Non-Canonical Usage Note

This document is retained as a supporting/satellite reference only. It must not be treated as active canonical truth. Where conflict exists, active canonical documents in /opt/binarybot/docs/canonical/active/ take precedence.
