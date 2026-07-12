BINARYBOT CANONICAL SPECIFICATION

ALGO SPEC — STRATEGY ENGINE

Version: 2.0.0
Status: Canonical
Scope: Strategy Engine / Mathematical Model

Dependencies:

- STRATEGY_ENGINE_ARCHITECTURE_MAP_v1.0.0.md
- DECISION_OBJECT_CANONICAL_SPEC_v1.0.0.md
- TIME_MODEL_CANON_v1.0.0.md

Supersedes:

- ALGO_SPEC.md (legacy versions)

---

1. PURPOSE OF THIS DOCUMENT

Acest document definește modelul matematic oficial al strategiei BinaryBot.

Strategia are rolul de a analiza structura pieței și de a produce un obiect matematic de decizie.

Strategia nu produce semnale direct.

Strategia produce:

DecisionObject

Acest obiect este consumat ulterior de:

FSM Decision Engine
Signal Engine
Observability System

---

2. STRATEGY ENGINE PRINCIPLE

Principiul fundamental al strategiei este:

Market Data
→ Mathematical Evaluation
→ DecisionObject

Strategia nu conține:

signal delivery
message generation
telegram formatting
execution logic

Aceste responsabilități aparțin altor module.

---

3. STRATEGY PIPELINE

Pipeline-ul matematic al strategiei este:

MARKET DATA
      ↓
MARKET MODEL
      ↓
TIME MODEL
      ↓
CORRIDOR MODEL
      ↓
SCORING MODEL
      ↓
DECISION OBJECT BUILDER

---

4. MARKET MODEL

Market Model transformă datele brute ale pieței în parametri operaționali.

Input:

price
spread
candle_range
volatility
support_levels
resistance_levels

Output:

price_speed
trend_context
volatility_state
structure_context
buffer_distance

---

5. TIME MODEL

Time Model evaluează fezabilitatea temporală a mișcării.

---

5.1 RAW TIME ESTIMATION

Timpul necesar pentru atingerea targetului:

t_needed = buffer_distance / price_speed

---

5.2 STRUCTURAL ADJUSTMENT

Estimarea temporală este ajustată în funcție de contextul pieței:

t_needed_adjusted =
t_needed
× trend_factor
× volatility_factor
× structure_factor

---

5.3 MODEL EXPIRY

Orizontul temporal al modelului:

model_expiry_minutes =
t_needed_adjusted × expiry_tolerance

unde:

expiry_tolerance ∈ [1.1 , 1.5]

Acest timp reprezintă durata maximă realistă a oportunității.

---

5.4 MODEL TIME REACH RATIO

Raportul dintre distanța posibilă și distanța necesară.

model_time_reach_ratio =
(price_speed × model_expiry_minutes) / buffer_distance

Interpretare:

>1   mișcarea este fezabilă
≈1   mișcarea este limită
<1   mișcarea este improbabilă

---

5.5 CORRIDOR TIME PRESSURE

Presiunea temporală asupra setup-ului.

corridor_time_pressure =
t_needed_adjusted / model_expiry_minutes

Interpretare:

0 → setup foarte devreme
1 → setup aproape de limită

---

6. CORRIDOR MODEL

Corridor Model analizează geometria setup-ului.

Corridor Engine produce:

corridor_valid
corridor_width
corridor_open_ok
corridor_geometry_score

Corridor Engine nu calculează expiry.

Responsabilitatea lui este exclusiv:

structural feasibility

---

7. SCORING MODEL

Scoring Model evaluează calitatea setup-ului.

Input:

momentum
structure
corridor_width
time_feasibility
volatility

Output:

score_total
score_components

---

7.1 NORMALIZED SCORE

Scorul total este normalizat:

normalized_score = score_total / 100

---

8. DECISION OBJECT BUILDER

După evaluarea tuturor modelelor strategia construiește:

DecisionObject

Structura acestui obiect este definită în:

DECISION_OBJECT_CANONICAL_SPEC_v1.0.0.md

---

8.1 DECISION OBJECT COMPONENTS

DecisionObject conține:

market_context
time_model
corridor_model
scoring
decision_state
execution_parameters
diagnostics

---

9. STRATEGY OUTPUT

Outputul final al strategiei este:

DecisionObject

Acest obiect este transmis către:

FSM Decision Engine

---

10. STRATEGY RESTRICTIONS

Strategia nu are voie să facă următoarele lucruri:

generate signals
send messages
calculate execution expiry
communicate with telegram

Aceste responsabilități aparțin altor module.

---

11. STRATEGY RESPONSIBILITY BOUNDARY

Separarea responsabilităților este:

Strategy Engine
→ produce DecisionObject

FSM Decision Engine
→ decide state transition

Signal Engine
→ livrează mesajul către utilizator

---

12. OBSERVABILITY

Strategia trebuie să producă date pentru audit:

model_time_reach_ratio
corridor_time_pressure
normalized_score
corridor_width
decision_inputs

Aceste date sunt înregistrate pentru:

strategy diagnostics
performance analysis
decision audit

---

13. FINAL PRINCIPLE

Strategia BinaryBot este un model matematic pur.

Ea nu produce semnale.

Ea produce un obiect de decizie.

Strategy
→ DecisionObject

Acest principiu garantează:

predictability
auditability
modular architecture
stable system evolution