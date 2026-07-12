BINARYBOT CANONICAL SPECIFICATION

DECISION OBJECT CANONICAL SPECIFICATION

Version: 1.0.0
Status: Canonical
Scope: Strategy Engine / Signal Engine / Distribution / Observability

Dependencies:

- STRATEGY_ENGINE_ARCHITECTURE_MAP_v1.0.0.md
- TIME_MODEL_CANON_v1.0.0.md
- SR_CORRIDOR_DETECTION_ENGINE_SPEC_v1.0.0.md

---

1. PURPOSE OF THIS DOCUMENT

Acest document definește structura canonică a obiectului de decizie ("DecisionObject") produs de Strategy Engine.

"DecisionObject" reprezintă rezultatul matematic final al evaluării pieței și este obiectul care circulă în pipeline-ul sistemului.

Acest document stabilește:

- structura JSON oficială produsă de strategie
- câmpurile interne ale modelului matematic
- câmpurile utilizate pentru execuția semnalelor
- contractul stabil între Strategy Engine și celelalte componente

Acest document este sursa canonică de adevăr pentru structura datelor strategiei.

---

2. FUNDAMENTAL PRINCIPLE

Strategia nu produce direct mesaje pentru trader.

Strategia produce un obiect de decizie structurat.

Acest obiect conține:

- contextul pieței
- rezultatele modelului matematic
- scorul strategiei
- starea FSM a semnalului
- instrucțiunile de execuție

Acest obiect este denumit:

DecisionObject

Acesta este consumat ulterior de:

- Signal Engine
- Distribution Layer
- Observability
- Analytics
- Trade Journal

---

3. DECISION OBJECT HIGH LEVEL STRUCTURE

Structura generală a obiectului este:

{
  "identity": {},
  "market_context": {},
  "strategy_metrics": {},
  "time_model": {},
  "corridor_model": {},
  "scoring": {},
  "state": {},
  "execution": {},
  "observability": {}
}

Fiecare block reprezintă o componentă logică a deciziei strategice.

---

4. IDENTITY BLOCK

Acest block identifică unic oportunitatea de trade.

"identity": {
  "signal_id": "",
  "symbol": "",
  "direction": "",
  "timeframe": "",
  "candle_ts": ""
}

Câmpuri

"signal_id"
identificator unic al ideii de trade.

Acesta trebuie să rămână constant pe tot pipeline-ul:

PRE → CONFIRM → OPEN_NOW

"symbol"
instrumentul tranzacționat.

"direction"

CALL
PUT

"timeframe"
timeframe-ul pe care a fost detectată oportunitatea.

"candle_ts"
timestamp-ul lumânării analizate.

---

5. MARKET CONTEXT BLOCK

Conține contextul brut al pieței în momentul evaluării.

"market_context": {
  "price": 0,
  "spread": 0,
  "volatility": 0,
  "candle_range": 0
}

Descriere

"price"
prețul curent al instrumentului.

"spread"
diferența bid–ask.

"volatility"
măsura volatilitații curente.

"candle_range"
dimensiunea lumânării analizate.

---

6. STRATEGY METRICS BLOCK

Conține metricile brute calculate de modelul de piață.

"strategy_metrics": {
  "buffer_distance": 0,
  "price_speed": 0,
  "t_needed_minutes": 0,
  "t_needed_adjusted_minutes": 0
}

Descriere

"buffer_distance"
distanța până la nivelul target sau buffer.

"price_speed"
viteza estimată a mișcării prețului.

"unitate"

price_units / minute

"t_needed_minutes"

t_needed = distance / speed

"t_needed_adjusted_minutes"

timpul ajustat după contextul structural:

trend
volatility
structure

---

7. TIME MODEL BLOCK

Acest block conține modelul temporal intern al strategiei.

"time_model": {
  "model_expiry_minutes": 0,
  "corridor_time_pressure": 0,
  "model_time_reach_ratio": 0,
  "time_state": ""
}

Câmpuri

"model_expiry_minutes"

expiry intern al modelului matematic.

Acesta nu este livrat direct traderului.

"corridor_time_pressure"

t_needed_adjusted / model_expiry_minutes

descrie presiunea temporală a oportunității.

"model_time_reach_ratio"

(price_speed × model_expiry_minutes) / buffer_distance

raportul dintre distanța posibilă și distanța necesară.

"time_state"

EARLY
BUILDING
READY
CRITICAL
EXPIRED

---

8. CORRIDOR MODEL BLOCK

Acest block descrie geometria corridorului strategic.

"corridor_model": {
  "corridor_valid": false,
  "corridor_width": 0,
  "corridor_open_ok": false
}

Descriere

"corridor_valid"
indică dacă corridorul este valid.

"corridor_width"
lățimea corridorului de operare.

"corridor_open_ok"
indică dacă deschiderea trade-ului este posibilă în corridor.

---

9. SCORING BLOCK

Acest block conține scorul strategic.

"scoring": {
  "score_total": 0,
  "score_components": {}
}

"score_total"

scorul agregat al setup-ului.

interval:

0 – 100

"score_components"

descompunerea scorului:

exemple:

{
  "momentum": 0,
  "structure": 0,
  "corridor": 0,
  "timing": 0,
  "feasibility": 0
}

---

10. STATE BLOCK

Acest block definește starea FSM a semnalului.

"state": {
  "signal_state": ""
}

Valori posibile:

NO_SIGNAL
REJECT
PRE
CONFIRM
OPEN_NOW

Această stare controlează logica de distribuție a semnalului.

---

11. EXECUTION BLOCK

Acest block conține instrucțiunile pentru execuția traderului.

"execution": {
  "confirm_expiry_min_minutes": null,
  "confirm_expiry_max_minutes": null,
  "open_now_expiry_minutes": null
}

Popularea câmpurilor depinde de starea semnalului.

---

11.1 PRE STATE

nu este necesar expiry extern

"execution" poate rămâne gol.

---

11.2 CONFIRM STATE

Strategia livrează un interval de expiry.

confirm_expiry_min_minutes
confirm_expiry_max_minutes

Acest interval reprezintă fereastra probabilă de execuție.

---

11.3 OPEN_NOW STATE

Strategia livrează o valoare exactă.

open_now_expiry_minutes

Această valoare:

- poate fi fracționară
- nu trebuie rotunjită arbitrar
- reprezintă rezultatul final al modelului matematic

---

12. OBSERVABILITY BLOCK

Acest block este utilizat pentru audit și analiză.

"observability": {
  "decision_reason": "",
  "rejected_by": "",
  "diagnostics": {}
}

Descriere

"decision_reason"
motivul deciziei strategice.

"rejected_by"
componenta care a respins setup-ul.

exemple:

spike_filter
corridor_engine
feasibility_gate
scoring_gate

"diagnostics"
date suplimentare pentru debugging.

---

13. STATE FIELD MATRIX

State| Internal Time Model| External Expiry
NO_SIGNAL| optional| none
REJECT| yes| none
PRE| yes| optional
CONFIRM| yes| min–max range
OPEN_NOW| yes| exact value

---

14. CANONICAL TIME SEPARATION RULE

Un câmp nu poate reprezenta simultan:

expiry intern
și
expiry extern

Este interzis canonic utilizarea unui câmp ambiguu:

expiry_minutes

Separarea corectă este:

Intern

model_expiry_minutes

Extern CONFIRM

confirm_expiry_min_minutes
confirm_expiry_max_minutes

Extern OPEN_NOW

open_now_expiry_minutes

---

15. FINAL PRINCIPLE

Strategy Engine produce:

DecisionObject

Signal Engine:

- citește starea semnalului
- citește câmpurile de execuție
- construiește mesajul pentru trader

Distribuția nu recalculă strategia.

Fluxul canonic al sistemului este:

Strategy Engine
      ↓
DecisionObject
      ↓
Signal Engine
      ↓
Distribution Layer
      ↓
User Message

Aceasta este arhitectura canonică a deciziei strategice în BinaryBot.