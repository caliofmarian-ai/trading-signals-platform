BINARYBOT CANONICAL SPECIFICATION

OBSERVABILITY SPEC

Version: 2.0.0
Status: Canonical
Scope: Strategy Observability / Decision Audit / Telemetry

Dependencies:

- STRATEGY_ENGINE_ARCHITECTURE_MAP_v1.0.0.md
- DECISION_OBJECT_CANONICAL_SPEC_v1.0.0.md
- FSM_DECISION_ENGINE_SPEC_v1.0.0.md
- SIGNAL_ENGINE_EXECUTION_SPEC_v2.0.0.md
- SIGNAL_TIME_MODEL_SPEC_v2.0.0.md

Supersedes:

- OBSERVABILITY_SPEC.md (legacy versions)

---

1. PURPOSE OF THIS DOCUMENT

Acest document definește sistemul de observability al strategiei BinaryBot.

Observability permite:

decision transparency
signal diagnostics
strategy performance analysis
failure investigation

Fiecare decizie a sistemului trebuie să poată fi reconstruită și explicată.

---

2. OBSERVABILITY PRINCIPLE

Principiul fundamental este:

every decision must be explainable

Sistemul trebuie să permită analiza:

why a signal was generated
why a signal was rejected
why a setup degraded
why execution timing changed

---

3. OBSERVABILITY POSITION IN PIPELINE

Observability colectează date din toate straturile sistemului.

Pipeline-ul complet devine:

MARKET DATA
      ↓
MARKET MODEL
      ↓
TIME MODEL
      ↓
CORRIDOR ENGINE
      ↓
SCORING MODEL
      ↓
DECISION OBJECT
      ↓
FSM DECISION ENGINE
      ↓
SIGNAL ENGINE
      ↓
DELIVERY

Observability poate înregistra date din fiecare layer.

---

4. CORE OBSERVABILITY OBJECT

Elementul central al observability este:

DecisionObject

Acest obiect reprezintă snapshot-ul complet al deciziei strategiei.

Observability trebuie să logheze:

DecisionObject

fără modificări.

---

5. OBSERVABILITY DATA CATEGORIES

Datele observate sunt împărțite în cinci categorii.

market diagnostics
time model diagnostics
corridor diagnostics
decision diagnostics
execution diagnostics

---

6. MARKET DIAGNOSTICS

Datele de piață utilizate de strategie.

symbol
current_price
spread
volatility_state
trend_context
structure_context

Aceste date permit analiza condițiilor pieței.

---

7. TIME MODEL DIAGNOSTICS

Datele generate de modelul temporal.

model_expiry_minutes
t_needed_adjusted
corridor_time_pressure
model_time_reach_ratio

Aceste date permit analiza fezabilității temporale.

---

8. CORRIDOR DIAGNOSTICS

Datele generate de Corridor Engine.

nearest_support
nearest_resistance
corridor_width
corridor_geometry_score
corridor_valid
corridor_open_ok

Aceste date permit analiza structurii setup-ului.

---

9. SCORING DIAGNOSTICS

Datele generate de Scoring Model.

score_total
normalized_score
score_components

Aceste date permit analiza calității setup-ului.

---

10. FSM DECISION DIAGNOSTICS

FSM trebuie să înregistreze:

previous_state
current_state
decision_variables
transition_reason

unde:

decision_variables =
R (model_time_reach_ratio)
P (corridor_time_pressure)
S (normalized_score)
W (corridor_width_score)

---

11. REJECT REASONS

Pentru starea "REJECT" trebuie înregistrate motivele exacte.

Exemple:

low_score
insufficient_corridor_width
time_feasibility_failure
structure_invalid

Aceste informații permit analiza ratelor de respingere.

---

12. EXECUTION DIAGNOSTICS

Datele legate de execuția semnalului.

confirm_expiry_min_minutes
confirm_expiry_max_minutes
open_now_expiry_minutes
signal_state
delivery_timestamp
delivery_channel

Aceste date permit analiza execuției reale.

---

13. SIGNAL LIFECYCLE TRACKING

Observability trebuie să permită urmărirea completă a unui semnal.

Lifecycle-ul unui semnal:

PRE
→ CONFIRM
→ OPEN_NOW
→ EXECUTION

Pentru fiecare etapă trebuie înregistrat:

timestamp
decision_state
key parameters

---

14. SIGNAL FAILURE ANALYSIS

Sistemul trebuie să permită analiza cazurilor în care:

signal expired
signal invalidated
setup degraded
execution missed

Aceste situații trebuie înregistrate pentru analiză ulterioară.

---

15. TELEMETRY OUTPUT

Datele de observability pot fi transmise către:

log files
analytics dashboards
monitoring systems
research tools

---

16. PERFORMANCE ANALYTICS

Observability trebuie să permită analiza:

signal success rate
average setup score
expiry model accuracy
decision distribution
state transition statistics

Aceste analize sunt utilizate pentru optimizarea strategiei.

---

17. ERROR DETECTION

Observability trebuie să detecteze:

decision inconsistencies
invalid expiry ranges
state transition errors
missing parameters

Aceste erori trebuie raportate pentru investigare.

---

18. RESPONSIBILITY BOUNDARY

Observability nu influențează strategia.

Responsabilitatea sa este exclusiv:

data collection
diagnostics
analytics

Strategia rămâne complet deterministă.

---

19. DATA INTEGRITY RULE

Datele de observability trebuie să respecte regula:

observability does not modify decision data

Observability înregistrează datele exact așa cum sunt produse.

---

20. FINAL PRINCIPLE

Observability este mecanismul care face strategia transparentă și auditabilă.

Principiul final este:

strategy decisions must be traceable

Acest lucru garantează:

decision transparency
strategy debugging capability
long term strategy improvement