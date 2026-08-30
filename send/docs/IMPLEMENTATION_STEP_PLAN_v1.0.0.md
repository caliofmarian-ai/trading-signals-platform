# IMPLEMENTATION STEP PLAN

Version: 1.0.0  
Status: Implementation Blueprint  
Scope: Step-by-step migration from legacy strategy engine to canonical architecture  

Dependencies:

- CANONICAL_REFACTOR_PLAN_v1.0.0.md
- STRATEGY_ENGINE_ARCHITECTURE_MAP_v1.0.0.md
- canonical/active/DECISION_OBJECT_CANONICAL_SPEC_v1.0.0.md
- canonical/active/FSM_DECISION_ENGINE_SPEC_v1.0.0.md
- canonical/active/SR_CORRIDOR_ENGINE_SPEC_v2.0.0.md
- SIGNAL_TIME_MODEL_SPEC_v2.0.0.md
- canonical/active/SIGNAL_ENGINE_EXECUTION_SPEC_v2.0.0.md
- CANONICAL_CODE_ALIGNMENT_MATRIX_v1.0.0.md

---

## 1. PURPOSE OF THIS DOCUMENT

Acest document definește **pașii concreți de implementare în cod** ai arhitecturii canonice BinaryBot.

Scopul documentului este:

- să transforme planul de refactorizare în pași executabili
- să definească ordinea exactă a modificărilor
- să prevină riscurile operaționale
- să mențină botul funcțional pe durata migrării

Acest document este **planul operațional de implementare**.

---

## 2. IMPLEMENTATION STRATEGY

Migrarea codului se va face prin:

SHADOW IMPLEMENTATION

Adică:

noua arhitectură rulează în paralel cu cea existentă până la validare completă.

Principii:

- nu se modifică direct logica existentă
- se creează module noi
- se verifică outputurile
- se activează gradual prin flaguri

---

## 3. IMPLEMENTATION STEPS OVERVIEW

Migrarea completă se va face în următoarele etape:

STEP 107 — DecisionObject module  
STEP 108 — MarketModel extraction  
STEP 109 — SR Corridor Engine extraction  
STEP 110 — TimeModel extraction  
STEP 111 — ScoringModel extraction  
STEP 112 — Decision FSM integration  
STEP 113 — Execution Model separation  
STEP 114 — Strategy engine rebuild  
STEP 115 — Signal Engine cleanup  

---

## 4. STEP 107 — DECISION OBJECT MODULE

Scop:

Introducerea obiectului central al strategiei.

Creare fișier:

core/decision_object.py

Conținut:

dataclass

DecisionObject

Câmpuri principale:

symbol direction price_speed buffer_distance corridor_width model_expiry model_time_reach_ratio corridor_time_pressure score_total score_components timestamp

Acest obiect nu este încă folosit de strategie.

Este doar definit.

Implementation status (2026-08-30):

- the contract is defined in `core/decision_object.py`
- synchronized Market Model, SR/Corridor, Time Model and Scoring Model outputs are assembled by `core/decision_assembly.py`
- reject semantics, strategic flags, explanations and immutable FSM-ready inputs are materialized explicitly
- the assembled object is deterministic and JSON-serializable for later observability
- it remains shadow-only and is not yet consumed by FSM or Signal Engine

---

## 5. STEP 108 — MARKET MODEL MODULE

Creare fișier:

core/market_model.py

Responsabilități:

- calcul price_speed
- determinare buffer_distance
- evaluare trend_context
- evaluare volatility_state

Input:

market_data

Output:

MarketContext

Structură:

MarketContext price_speed buffer_distance trend_context volatility_state

Implementation status (2026-08-30):

- implemented as a deterministic shadow module in `core/market_model.py`
- uses only real newest-first M1/M5 candles and versioned `algo_params.json` values
- preserves the established strategy mathematics for EMA, RSI, ATR, price speed, buffer and spike evidence
- also exposes `noise_context`; `target_distance` remains unavailable until the SR Corridor layer supplies real structure evidence
- rejects incomplete history, invalid OHLC evidence, invalid ordering and missing configuration instead of fabricating values
- does not score, emit signals, select expiry, mutate the live strategy or execute trades

---

## 6. STEP 109 — SR CORRIDOR ENGINE

Creare fișier:

core/sr_corridor_engine.py

Responsabilități:

- detectare support/resistance
- calcul corridor_width
- determinare corridor_direction
- evaluare breakout feasibility

Output:

CorridorContext

Structură:

CorridorContext corridor_width corridor_direction corridor_structure

Implementation status (2026-08-30):

- implemented as a deterministic shadow module in `core/sr_corridor_engine.py`
- consumes the completed Market Model output and real newest-first M5 candles
- preserves the established support/resistance clustering and configured required-room mathematics
- exposes boundaries, directional room, proximity distances, feasibility, conflicts and an audit explanation
- missing boundaries remain `UNAVAILABLE`; they are never converted into infinite usable room
- does not calculate time, score, FSM state, signal stage or execution

---

## 7. STEP 110 — TIME MODEL

Creare fișier:

core/time_model.py

Formula principală:

t_needed = buffer_distance / price_speed

Apoi:

model_expiry = t_needed × expiry_tolerance

și:

model_time_reach_ratio = t_needed_adjusted / model_expiry

și:

corridor_time_pressure is derived from the canonical time metrics together
with corridor geometry; an exact formula requires an explicit, versioned
calibration rule.

Output:

TimeContext

Implementation status (2026-08-30):

- implemented as a deterministic shadow module in `core/time_model.py`
- consumes synchronized Market Model and VALID SR/Corridor evidence
- preserves the established buffer/speed, trend adjustment, structure adjustment and configured model-window mathematics
- emits canonical `t_needed`, `t_needed_adjusted`, `model_expiry`, `model_time_reach_ratio` and `time_state`
- `corridor_time_pressure` remains explicitly unavailable because active canon does not yet define a calibrated formula
- does not derive trader-facing execution expiry, telemetry checkpoints, score, FSM transitions, signals or trades

---

## 8. STEP 111 — SCORING MODEL

Creare fișier:

core/scoring_model.py

Responsabilități:

calculul scorului strategic.

Output:

ScoreContext

Structură:

ScoreContext score_total score_components normalized_score

Implementation status (2026-08-30):

- implemented as a deterministic shadow module in `core/scoring_model.py`
- consumes synchronized Market Model, SR/Corridor and Time Model evidence
- preserves the five established score formulas and their 30/20/15/20/15 maxima
- exposes immutable components, normalized total, score band, eligibility and hard blockers
- a high arithmetic score cannot bypass market instability, invalid structure or infeasible time
- does not produce a `DecisionObject`, FSM state, signal stage, execution expiry or trade

---

## 9. STEP 112 — DECISION FSM INTEGRATION

FSM va primi:

DecisionObject

și va produce stări:

NO_SIGNAL REJECT PRE CONFIRM OPEN_NOW

Modificări:

core/fsm_runtime.py

FSM nu mai va depinde de strategy_v2.

---

## 10. STEP 113 — EXECUTION MODEL

Creare fișier:

core/execution_model.py

Responsabilități:

calcul expiry final.

confirm_expiry open_now_expiry

Formula:

confirm_expiry = model_expiry ± confirm_delta



open_now_expiry = model_expiry × (1 - pressure_bias)

---

## 11. STEP 114 — STRATEGY ENGINE REBUILD

Creare modul:

core/strategy_engine_v3.py

Pipeline nou:

MarketModel ↓ CorridorEngine ↓ TimeModel ↓ ScoringModel ↓ DecisionObject ↓ DecisionFSM ↓ ExecutionModel

Strategy_v2 rămâne activ până la validare completă.

---

## 12. STEP 115 — SIGNAL ENGINE CLEANUP

Modificare fișier:

core/signal_engine.py

Signal engine devine responsabil doar pentru:

- construirea semnalului
- distribuția semnalului
- integrarea cu Telegram

Logica matematică va fi eliminată.

---

## 13. VALIDATION PROCEDURE

Pentru fiecare step:

1️⃣ CODE AUDIT  
2️⃣ SHADOW EXECUTION  
3️⃣ OUTPUT COMPARISON  
4️⃣ PERFORMANCE CHECK  

Numai după validare se activează noul modul.

---

## 14. FEATURE FLAGS

Se introduc flaguri interne:

USE_DECISION_OBJECT USE_NEW_MARKET_MODEL USE_NEW_CORRIDOR_ENGINE USE_NEW_TIME_MODEL USE_NEW_SCORING_MODEL USE_NEW_FSM USE_NEW_EXECUTION_MODEL

Acestea permit activarea progresivă.

---

## 15. FINAL CUTOVER

Cutover final va însemna:

- dezactivare strategy_v2
- activare strategy_engine_v3
- eliminare logică legacy

---

## 16. EXPECTED FINAL ARCHITECTURE

După implementare:

strategy_engine/

market_model.py sr_corridor_engine.py time_model.py scoring_model.py decision_object.py decision_fsm.py execution_model.py strategy_engine_v3.py

și

signal_engine/

signal_builder.py signal_router.py telegram_publisher.py

---

## 17. FINAL OBJECTIVE

Obiectivul implementării este:

crearea unei arhitecturi modulare stabile.

Această arhitectură permite:

- audit matematic clar
- dezvoltare rapidă a strategiei
- scalare fără risc operațional

---

END OF DOCUMENT
