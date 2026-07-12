BINARYBOT CANONICAL SPECIFICATION

SIGNAL TIME MODEL SPEC

Version: 2.0.0
Status: Canonical
Scope: Time Model / Execution Expiry Model

Dependencies:

- STRATEGY_ENGINE_ARCHITECTURE_MAP_v1.0.0.md
- ALGO_SPEC_v2.0.0.md
- FSM_DECISION_ENGINE_SPEC_v1.0.0.md
- SIGNAL_ENGINE_EXECUTION_SPEC_v2.0.0.md

Supersedes:

- SIGNAL_TIME_MODEL_SPEC.md (legacy versions)

---

1. PURPOSE OF THIS DOCUMENT

Acest document definește modelul oficial al timpului în sistemul BinaryBot.

Modelul separă clar:

model time (strategie)
execution time (semnal)

Această separare elimină confuziile istorice legate de conceptul generic:

expiry_minutes

---

2. TIME MODEL PRINCIPLE

În arhitectura BinaryBot există două tipuri distincte de timp:

1. MODEL TIME
2. EXECUTION TIME

Acestea au responsabilități diferite.

---

3. MODEL TIME

Model Time este utilizat exclusiv de strategie.

Acesta este calculat în:

TIME MODEL

și reprezintă orizontul temporal al oportunității.

---

3.1 MODEL EXPIRY

Valoarea principală este:

model_expiry_minutes

Aceasta este calculată în:

ALGO_SPEC_v2.0.0.md

Formula de bază:

model_expiry_minutes =
t_needed_adjusted × expiry_tolerance

unde:

expiry_tolerance ∈ [1.1 , 1.5]

---

3.2 ROLE OF MODEL EXPIRY

"model_expiry_minutes" este utilizat pentru:

time feasibility
corridor pressure calculation
FSM decision logic
scoring evaluation

Această valoare nu este transmisă utilizatorului.

---

4. EXECUTION TIME

Execution Time reprezintă timpul utilizat de trader pentru execuția semnalului.

Acesta este derivat din:

model_expiry_minutes

dar nu este identic cu acesta.

---

5. CONFIRM EXPIRY RANGE

În starea "CONFIRM" sistemul livrează un interval de expirare recomandat.

Acesta este definit de două valori:

confirm_expiry_min_minutes
confirm_expiry_max_minutes

---

5.1 CONFIRM EXPIRY DERIVATION

Intervalul este derivat din model expiry.

Formula generală:

confirm_delta =
model_expiry_minutes × confirm_window_factor

unde:

confirm_window_factor ∈ [0.1 , 0.25]

---

5.2 CONFIRM EXPIRY RANGE

Valorile finale sunt:

confirm_expiry_min_minutes =
model_expiry_minutes − confirm_delta

confirm_expiry_max_minutes =
model_expiry_minutes + confirm_delta

Acest interval oferă traderului flexibilitate de execuție.

---

6. OPEN NOW EXPIRY

În starea "OPEN_NOW" sistemul livrează expiry exact pentru execuție.

Valoarea este:

open_now_expiry_minutes

Această valoare reprezintă momentul optim calculat de strategie.

---

6.1 OPEN NOW DERIVATION

Valoarea este derivată din model expiry și din presiunea temporală a setup-ului.

Formula generală:

open_now_expiry_minutes =
model_expiry_minutes × (1 − pressure_bias)

unde:

pressure_bias =
corridor_time_pressure × bias_factor

---

6.2 FRACTIONAL VALUES

"open_now_expiry_minutes" poate fi:

fractional value

Aceasta permite ajustarea precisă a execuției.

---

7. TIME CONSISTENCY RULE

Trebuie să fie întotdeauna adevărat:

confirm_expiry_min_minutes
≤ open_now_expiry_minutes
≤ confirm_expiry_max_minutes

Dacă această regulă este încălcată, sistemul trebuie să înregistreze:

time_model_inconsistency

---

8. TIME MODEL FLOW

Fluxul temporal al strategiei este:

Time Model
→ model_expiry_minutes

FSM Decision Engine
→ confirm_expiry_range
→ open_now_expiry

Signal Engine
→ delivery to user

---

9. TIME MODEL RESTRICTIONS

Time Model nu are voie să genereze semnale.

Responsabilitatea sa este exclusiv:

temporal feasibility analysis

---

10. SIGNAL ENGINE ROLE

Signal Engine nu recalculază timpul.

El utilizează valorile din:

DecisionObject.execution_parameters

și le transmite utilizatorului.

---

11. OBSERVABILITY DATA

Pentru auditul strategiei trebuie logate următoarele valori:

model_expiry_minutes
confirm_expiry_min_minutes
confirm_expiry_max_minutes
open_now_expiry_minutes
corridor_time_pressure

Aceste date permit:

signal timing diagnostics
strategy performance analysis
expiry model validation

---

12. FINAL PRINCIPLE

Modelul temporal al BinaryBot separă clar:

MODEL TIME

și

EXECUTION TIME

Principiul fundamental este:

Strategy Model
→ calculează oportunitatea

Execution Layer
→ livrează timpul de execuție

Această separare garantează:

claritate conceptuală
predictabilitate a semnalelor
auditabilitate a strategiei