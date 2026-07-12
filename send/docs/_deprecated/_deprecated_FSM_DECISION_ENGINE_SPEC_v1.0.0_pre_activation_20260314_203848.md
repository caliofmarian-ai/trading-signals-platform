BINARYBOT CANONICAL SPECIFICATION

FSM DECISION ENGINE SPEC

Version: 1.0.0
Status: Canonical
Scope: Decision FSM / Strategy Execution Layer

Dependencies:

- STRATEGY_ENGINE_ARCHITECTURE_MAP_v1.0.0.md
- DECISION_OBJECT_CANONICAL_SPEC_v1.0.0.md
- TIME_MODEL_CANON_v1.0.0.md

---

1. PURPOSE OF THIS DOCUMENT

Acest document definește motorul decizional FSM (Finite State Machine) al sistemului BinaryBot.

FSM are rolul de a transforma obiectul matematic de decizie ("DecisionObject") produs de strategie în stări operaționale de semnal.

FSM nu produce calcule matematice.

FSM interpretează rezultatul strategiei și decide momentul livrării semnalului.

---

2. POSITION IN STRATEGY PIPELINE

Pipeline-ul complet al strategiei este:

MARKET DATA
      ↓
MARKET MODEL
      ↓
TIME MODEL
      ↓
SCORING MODEL
      ↓
DecisionObject
      ↓
FSM DECISION ENGINE
      ↓
EXECUTION MODEL
      ↓
SIGNAL ENGINE

FSM este stratul de decizie operațională dintre modelul matematic și execuția semnalului.

---

3. INPUT OF FSM

FSM primește ca input exclusiv:

DecisionObject

Structura acestui obiect este definită în:

DECISION_OBJECT_CANONICAL_SPEC_v1.0.0.md

FSM nu recalculază parametri strategici.

---

4. CORE DECISION VARIABLES

FSM utilizează patru variabile principale extrase din "DecisionObject".

R = model_time_reach_ratio
P = corridor_time_pressure
S = normalized_score
W = corridor_width_score

---

4.1 MODEL TIME REACH RATIO (R)

Interpretare:

raportul dintre distanța maxim posibilă și distanța necesară pentru target.

R = (price_speed × model_expiry_minutes) / buffer_distance

---

4.2 CORRIDOR TIME PRESSURE (P)

Interpretare:

nivelul presiunii temporale asupra setup-ului.

P = t_needed_adjusted / model_expiry_minutes

---

4.3 NORMALIZED SCORE (S)

Scorul total al setup-ului.

S = score_total / 100

---

4.4 CORRIDOR WIDTH SCORE (W)

Evaluarea calității geometrice a corridorului.

W ∈ [0 , 1]

---

5. FSM STATES

FSM definește următoarele stări canonice:

NO_SIGNAL
REJECT
PRE
CONFIRM
OPEN_NOW

---

5.1 NO_SIGNAL

Starea implicită.

Nu există setup valid.

---

5.2 REJECT

Setup detectat dar respins.

Motivul respingerii este înregistrat în observability.

---

5.3 PRE

Setup promițător dar încă imatur.

Semnalul nu este încă executabil.

---

5.4 CONFIRM

Setup valid și pregătit pentru execuție.

Se transmite intervalul de expirare estimat.

---

5.5 OPEN_NOW

Momentul optim de execuție.

Se transmite expiry exact pentru execuție.

---

6. STATE TRANSITIONS

FSM permite următoarele tranziții:

NO_SIGNAL → REJECT
NO_SIGNAL → PRE
PRE → CONFIRM
CONFIRM → OPEN_NOW

---

7. REJECT CONDITION

Setup-ul este respins dacă:

R < 0.70
OR
S < 0.55
OR
W < 0.40

Interpretare:

setup-ul este matematic nefezabil sau slab calitativ.

---

8. PRE CONDITION

Setup-ul devine PRE dacă:

R ≥ 0.85
S ≥ 0.60
W ≥ 0.45
P < 0.85

Interpretare:

setup-ul este promițător dar nu este încă în zona optimă.

---

9. CONFIRM CONDITION

Setup-ul devine CONFIRM dacă:

R ≥ 1.00
S ≥ 0.72
W ≥ 0.55
0.70 ≤ P < 1.00

Interpretare:

setup-ul este pregătit pentru execuție.

---

10. OPEN_NOW CONDITION

Setup-ul devine OPEN_NOW dacă:

R ≥ 1.05
S ≥ 0.80
W ≥ 0.60
1.00 ≤ P ≤ 1.20

Interpretare:

momentul optim de execuție.

---

11. EXECUTION PARAMETERS

FSM transmite către Execution Model parametrii necesari.

---

11.1 CONFIRM EXECUTION RANGE

În starea CONFIRM se livrează intervalul:

confirm_expiry_min_minutes
confirm_expiry_max_minutes

Aceste valori sunt derivate din:

model_expiry_minutes

prin aplicarea unei ferestre de toleranță.

---

11.2 OPEN_NOW EXECUTION TIME

În starea OPEN_NOW se livrează:

open_now_expiry_minutes

Această valoare reprezintă momentul optim de expirare pentru execuție.

Valoarea poate fi fracționară.

---

12. STATE CONSISTENCY RULE

Trebuie să fie adevărat:

confirm_expiry_min ≤ open_now_expiry ≤ confirm_expiry_max

Dacă această regulă este încălcată, sistemul trebuie să marcheze:

strategy_inconsistency

---

13. FSM OUTPUT

FSM produce două elemente principale:

signal_state
execution_parameters

Acestea sunt transmise către:

Signal Engine

---

14. OBSERVABILITY

FSM trebuie să înregistreze următoarele date:

DecisionObject
state_transition
decision_variables
reject_reason

Aceste informații sunt utilizate pentru:

- auditul strategiei
- optimizarea parametrilor
- analiza performanței sistemului

---

15. FINAL PRINCIPLE

FSM reprezintă stratul care transformă:

mathematical feasibility

în

operational execution

Strategia produce DecisionObject.

FSM decide momentul livrării semnalului.

Signal Engine execută livrarea către utilizator.