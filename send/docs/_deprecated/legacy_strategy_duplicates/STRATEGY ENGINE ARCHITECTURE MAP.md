BINARYBOT CANONICAL SPECIFICATION

STRATEGY ENGINE ARCHITECTURE MAP

Version: 1.0.0
Status: Canonical
Scope: Strategy Engine / Signal Engine / Decision FSM / Execution Model

Dependencies:

- TIME_MODEL_CANON_v1.0.0.md
- SR_CORRIDOR_DETECTION_ENGINE_SPEC_v1.0.0.md
- SIGNAL_TIME_MODEL_SPEC_v1.0.0.md

---

1. PURPOSE OF THIS DOCUMENT

Acest document definește arhitectura matematică completă a strategiei BinaryBot.

Scopul acestui document este:

- să definească motoarele matematice ale strategiei
- să stabilească pipeline-ul complet de evaluare al pieței
- să definească rolul fiecărei componente în decizia finală
- să separe clar modelul matematic de logica FSM
- să ofere baza canonică pentru implementarea codului

Acest document este harta oficială a strategiei botului.

---

2. FUNDAMENTAL PRINCIPLE

Strategia nu produce direct semnale.

Strategia produce un obiect matematic de decizie.

Acest obiect rezultă din interacțiunea a patru motoare strategice:

- Market Model
- Time Model
- Scoring Model
- Decision FSM

Aceste motoare funcționează într-un pipeline determinist.

---

3. HIGH LEVEL PIPELINE

Pipeline-ul complet al strategiei este:

MARKET DATA
      ↓
MARKET MODEL
      ↓
TIME MODEL
      ↓
SCORING MODEL
      ↓
DECISION FSM
      ↓
EXECUTION MODEL
      ↓
SIGNAL ENGINE

Fiecare layer are responsabilități clar separate.

---

4. MARKET MODEL

Market Model transformă datele brute ale pieței în parametri operaționali.

Input

price
spread
candle_range
volatility
support_levels
resistance_levels

Output

price_speed
buffer_distance
trend_context
volatility_state
structure_context

---

4.1 PRICE SPEED

Speed reprezintă viteza estimată a mișcării prețului.

V = price_speed

Unitate:

price_units / minute

Speed este derivat din:

candle progression
momentum
volatility
trend persistence

---

4.2 BUFFER DISTANCE

Distanța până la targetul strategiei.

D = |target_price - current_price|

Această valoare devine baza calculului temporal.

---

5. TIME MODEL

Time Model evaluează fezabilitatea temporală a mișcării.

Acesta este locul unde se află formula veche a strategiei.

---

5.1 RAW TIME ESTIMATE

t_needed = D / V

Interpretare:

timpul necesar pentru atingerea bufferului.

---

5.2 STRUCTURAL ADJUSTMENT

Se aplică multiplicatori contextuali.

t_needed_adjusted
=
t_needed
× trend_factor
× volatility_factor
× structure_factor

---

5.3 MODEL EXPIRY

Time horizon-ul intern al modelului.

model_expiry_minutes
=
t_needed_adjusted × expiry_tolerance

unde:

expiry_tolerance ∈ [1.1 , 1.5]

Acest timp definește cât timp este realist să existe oportunitatea.

---

5.4 MODEL TIME REACH RATIO

Acesta este succesorul canonic al vechiului "expiry_reach_ratio".

model_time_reach_ratio
=
(price_speed × model_expiry_minutes) / buffer_distance

Interpretare:

distanță maxim posibilă
--------------------------------
distanță necesară

---

5.5 CORRIDOR TIME PRESSURE

Presiunea temporală a setup-ului.

corridor_time_pressure
=
t_needed_adjusted / model_expiry_minutes

Interpretare:

cât de aproape este setup-ul de limita temporală

---

5.6 TIME STATE

Din pressure rezultă starea temporală.

EARLY
BUILDING
READY
CRITICAL
EXPIRED

---

6. SCORING MODEL

Scoring Model evaluează calitatea setup-ului.

Input

momentum
structure
corridor width
timing
feasibility

Output

score_total
score_components

---

6.1 NORMALIZED SCORE

Scorul total este normalizat:

S = score_total / 100

---

6.2 CORRIDOR WIDTH SCORE

Evaluarea geometriei corridorului.

W ∈ [0,1]

Interpretare:

0 → corridor invalid
1 → corridor foarte sănătos

---

7. DECISION FSM

FSM transformă matematica strategiei în stări de semnal.

Pipeline-ul canonic:

NO_SIGNAL
REJECT
PRE
CONFIRM
OPEN_NOW

---

8. DECISION VARIABLES

FSM folosește 4 variabile principale:

R = model_time_reach_ratio
P = corridor_time_pressure
S = normalized_score
W = corridor_width_score

---

9. REJECT CONDITION

Setup-ul este respins dacă:

R < 0.7
OR
S < 0.55
OR
W < 0.40

---

10. PRE CONDITION

Setup-ul devine PRE dacă:

R ≥ 0.85
S ≥ 0.60
W ≥ 0.45
P < 0.85

Interpretare:

setup promițător dar încă imatur.

---

11. CONFIRM CONDITION

Setup-ul devine CONFIRM dacă:

R ≥ 1.00
S ≥ 0.72
W ≥ 0.55
0.70 ≤ P < 1.00

Interpretare:

setup pregătit pentru execuție.

---

12. OPEN_NOW CONDITION

Setup-ul devine OPEN_NOW dacă:

R ≥ 1.05
S ≥ 0.80
W ≥ 0.60
1.00 ≤ P ≤ 1.20

Interpretare:

moment optim de execuție.

---

13. EXECUTION MODEL

Execuția traderului este derivată din modelul intern.

---

13.1 CONFIRM EXPIRY RANGE

confirm_delta
=
model_expiry_minutes × confirm_window_factor

Interval:

confirm_expiry_min_minutes
=
model_expiry_minutes - confirm_delta

confirm_expiry_max_minutes
=
model_expiry_minutes + confirm_delta

---

13.2 OPEN NOW EXPIRY

Momentul optim.

open_now_expiry_minutes
=
model_expiry_minutes × (1 - pressure_bias)

unde:

pressure_bias
=
corridor_time_pressure × bias_factor

Această valoare poate fi fracționară.

---

14. CONSISTENCY RULE

Trebuie să fie adevărat:

confirm_expiry_min ≤ open_now_expiry ≤ confirm_expiry_max

Dacă nu:

strategy inconsistency

---

15. COMPLETE STRATEGY FLOW

Pipeline-ul complet devine:

MARKET DATA
      ↓
Market Model
      ↓
Time Model
      ↓
Scoring Model
      ↓
Decision FSM
      ↓
Execution Model
      ↓
Signal Engine

---

16. FINAL PRINCIPLE

Strategia este compusă din două componente fundamentale:

MATHEMATICAL MODEL
+
DECISION FSM

Matematica definește fezabilitatea mișcării.

FSM definește momentul livrării semnalului.

Separarea acestor două componente este principiul canonic al arhitecturii BinaryBot.