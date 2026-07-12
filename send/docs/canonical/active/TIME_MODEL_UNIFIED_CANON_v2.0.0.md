
## 18A. ANCHOR ARCHITECTURE TRUTHS

This document explicitly adopts the following canonical truths:

- `Corridor Engine` is before `Time Model`.
- `DecisionObject` is produced before FSM.

The time model operates on already-derived corridor/structural context and remains upstream of the standardized `DecisionObject` handoff to FSM.

---

# TIME_MODEL_UNIFIED_CANON_v2.0.0


Path: /opt/binarybot/docs/canonical/active/TIME_MODEL_UNIFIED_CANON_v2.0.0.md  
Version: 2.0.0  
Status: Canonical Unified  
Owner: BinaryBot / DROPi Signals  
Scope: Strategy Time Model / Execution Time Semantics / Telemetry Time Semantics / DecisionObject Time Contract  
Supersedes:

Linked Documents:
- /opt/binarybot/docs/canonical/active/CANONICAL_STRATEGY_STACK_v1.0.0.md
- /opt/binarybot/docs/canonical/active/ALGO_SPEC_v2.0.0.md
- /opt/binarybot/docs/canonical/active/SR_CORRIDOR_ENGINE_SPEC_v2.0.0.md
- /opt/binarybot/docs/canonical/active/DECISION_OBJECT_CANONICAL_SPEC_v1.0.0.md
- /opt/binarybot/docs/canonical/active/FSM_DECISION_ENGINE_SPEC_v1.0.0.md
- /opt/binarybot/docs/canonical/active/TRADE_TEMPORAL_TELEMETRY_SPEC_v2.0.0.md

- superseded pre-unification time-model documents (legacy reference only)
- SIGNAL_TIME_MODEL_SPEC_v2.0.0.md
- signal_time_model_and_decision_object_v1.0.0.md
Related:
- WAVE1_TIME_MODEL_PATCH_SPEC_v1.0.0.md (transitional / not source of truth)
Depends on:
- CANONICAL_STRATEGY_STACK_v1.0.0.md
- DOCUMENT_NORMALIZATION_AND_DEPRECATION_PLAN_v1.0.0.md
- ALGO_SPEC_v2.0.0.md
- SR_CORRIDOR_ENGINE_SPEC_v2.0.0.md
- FSM_DECISION_ENGINE_SPEC_v1.0.0.md
- DECISION_OBJECT_CANONICAL_SPEC_v1.0.0.md
- SIGNAL_ENGINE_EXECUTION_SPEC_v2.0.0.md
- OBSERVABILITY_SPEC_v2.0.0.md

---

# 1. PURPOSE

Acest document este sursa canonică unificată pentru întreg modelul temporal BinaryBot.

Scopul acestui document este:

- să înlocuiască documentele paralele și suprapuse despre time model
- să definească un singur adevăr canonic pentru timpul intern al modelului
- să definească separat timpul de execuție livrat traderului
- să definească separat timpul de observabilitate / telemetry
- să stabilească legătura dintre time model, FSM, DecisionObject și Signal Engine
- să elimine ambiguitatea istorică produsă de termeni precum `expiry` și `expiry_minutes`

Acest document este documentul root canonic pentru domeniul timpului.

De la această versiune înainte, niciun alt document despre timp nu are voie să redefinească separat modelul temporal principal.

---

# 2. WHY THIS DOCUMENT EXISTS

În documentația istorică au existat simultan mai multe variante despre același subiect:

- canon time model
- signal time model
- time model + DecisionObject
- patch wave time model

Aceste documente au avut valoare în faze diferite, dar împreună au produs:

- duplicare
- vocabular amestecat
- responsabilități suprapuse
- conflict de autoritate

Prin urmare, acest document unifică toate definițiile valide și elimină rolul de sursă principală de adevăr al documentelor vechi.

---

# 3. FUNDAMENTAL PRINCIPLE

În BinaryBot, timpul nu este un singur câmp.

Timpul este un sistem compus din trei layere distincte:

1. model time
2. execution time
3. telemetry time

Aceste layere sunt conectate, dar nu sunt identice.

Confuzia dintre ele este interzisă canonic.

---

# 4. CANONICAL TIME LAYERS

## 4.1 Model Time

Model Time este timpul intern al strategiei.

Acesta descrie fezabilitatea matematică a oportunității și presiunea temporală a setup-ului.

Model Time aparține exclusiv layerului de strategie.

## 4.2 Execution Time

Execution Time este timpul livrat layerului de execuție și, indirect, traderului.

Acesta este derivat din model time, dar nu este identic cu acesta.

Execution Time aparține layerului de signal delivery / execution semantics.

## 4.3 Telemetry Time

Telemetry Time este programul de observație folosit după deschiderea trade-ului.

Acesta este folosit pentru audit, analiză post-expiry și calibrare.

Telemetry Time nu redefinește strategia și nu trebuie confundat cu model time sau execution time.

---

# 5. OFFICIAL VOCABULARY

Începând cu această versiune, vocabularul canonic oficial pentru domeniul timpului este:

## 5.1 Internal Strategy Metrics

- `buffer_distance`
- `price_speed`
- `t_needed`
- `t_needed_adjusted`

## 5.2 Canonical Time Model Metrics

- `model_expiry`
- `model_time_reach_ratio`
- `corridor_time_pressure`
- `time_state`

## 5.3 Execution Time Metrics

- `confirm_expiry_min_minutes`
- `confirm_expiry_max_minutes`
- `open_now_expiry_minutes`

## 5.4 Telemetry Time Metrics

- `telemetry_checkpoints`
- `expected_expiry_ts`
- `checkpoint_ts`
- `post_expiry_checkpoints`

---

# 6. FORBIDDEN PRIMARY TERMS

Următorii termeni nu mai pot funcționa ca termeni canonici principali necalificați:

- `expiry`
- `expiry_minutes`
- `trade_expiry_minutes`
- `model_expiry_minutes`
- `t_needed_minutes`
- `t_needed_adjusted_minutes`

Acești termeni pot apărea doar:

- în secțiuni de migrare
- în documente superseded / deprecated
- în secțiuni de compatibilitate istorică
- când se face mapare explicită vechi → nou

Termenii canonici activi sunt fără sufixul `_minutes` acolo unde documentul descrie modelul intern conceptual.

---

# 7. CANONICAL RELATION BETWEEN TIME METRICS

Relația oficială este:

```text
buffer_distance + price_speed
        ↓
      t_needed
        ↓
  t_needed_adjusted
        ↓
   model_expiry
        ↓
model_time_reach_ratio
        ↓
corridor_time_pressure
        ↓
     time_state
        ↓
FSM transition impact
        ↓
execution expiry derivation
        ↓
telemetry schedule``` 


Aceasta este secvența conceptuală oficială.


---

# 8. INPUT METRICS

## 8.1 buffer_distance

buffer_distance reprezintă distanța operațională relevantă pe care prețul trebuie să o parcurgă pentru validarea setup-ului, atingerea bufferului sau atingerea unei zone relevante de execuție.

Acesta este termenul canonic.

buffer_price este termen legacy și nu mai trebuie folosit ca termen principal.

## 8.2 price_speed

price_speed reprezintă viteza estimată a mișcării prețului în contextul actual de piață.

Aceasta poate fi influențată de:

trend

volatility

structure quality

momentum

market regime



---

# 9. RAW TIME ESTIMATION

## 9.1 t_needed

t_needed este estimarea brută a timpului necesar pentru ca prețul să parcurgă buffer_distance, în funcție de price_speed.

Conceptual:

t_needed = buffer_distance / price_speed

Aceasta este o formulă conceptuală.

Implementarea exactă poate conține protecții numerice, cap-uri și ajustări.

## 9.2 Validity of t_needed

t_needed trebuie interpretat ca metrică brută.

Nu este încă verdict final de fezabilitate și nu este încă timpul de execuție livrat traderului.


---

# 10. ADJUSTED TIME ESTIMATION

## 10.1 t_needed_adjusted

t_needed_adjusted este timpul ajustat după aplicarea contextului strategic.

Ajustările pot include:

trend multipliers

volatility multipliers

structure multipliers

corridor factors

feasibility modifiers

risk-aware bias


## 10.2 Canonical Role

t_needed_adjusted este baza principală din care se derivează model_expiry.


---

# 11. MODEL EXPIRY

## 11.1 Definition

model_expiry este orizontul temporal intern al modelului.

Acesta exprimă fereastra în care oportunitatea este considerată matematic fezabilă de strategie.

## 11.2 Canonical Role

model_expiry este utilizat pentru:

feasibility

scoring

corridor evaluation

temporal gating

FSM decision logic

analytics


## 11.3 Nature

model_expiry este intern.

Nu este transmis automat traderului și nu trebuie confundat cu expiry-ul extern de execuție.


---

# 12. MODEL TIME REACH RATIO

## 12.1 Definition

model_time_reach_ratio exprimă raportul dintre timpul necesar atingerii țintei relevante și fereastra temporală internă disponibilă.

Conceptual, acesta măsoară cât de “ușor” sau cât de “strâns” poate fi atinsă ținta în interiorul model_expiry.

## 12.2 Conceptual Relation

Conceptual:

model_time_reach_ratio = t_needed_adjusted / model_expiry

Interpretare conceptuală:

ratio mic → ținta este confortabil atinsă în fereastra modelului

ratio mediu → oportunitate fezabilă, dar sensibilă

ratio mare → setup tensionat sau limită

ratio peste limita acceptată → setup nefezabil


## 12.3 Role

model_time_reach_ratio este utilizat pentru:

feasibility gating

timing quality

corridor pressure interpretation

score timing component

FSM promotion / degradation logic



---

# 13. CORRIDOR TIME PRESSURE

## 13.1 Definition

corridor_time_pressure este indicatorul care exprimă cât de critică este fereastra temporală a setup-ului, în raport cu geometria corridorului și fezabilitatea temporală.

## 13.2 Inputs

Acesta este derivat din combinația dintre:

buffer_distance

price_speed

t_needed_adjusted

model_expiry

model_time_reach_ratio

corridor geometry / corridor width


## 13.3 Role

corridor_time_pressure influențează:

pregătirea setup-ului

proximitatea față de execuție

tranzițiile FSM

derivarea open_now_expiry_minutes



---

# 14. TIME STATE

## 14.1 Definition

time_state este clasificarea discretă a stării temporale a oportunității.

## 14.2 Canonical Values

Valorile canonice recomandate sunt:

EARLY

BUILDING

READY

CRITICAL

LATE

EXPIRED


## 14.3 Role

time_state nu este doar descriptiv.

Acesta influențează direct:

PRE / CONFIRM / OPEN_NOW transitions

degradation paths

delivery semantics

observability reasons



---

# 15. EXECUTION TIME PRINCIPLE

Execution Time este downstream față de Model Time.

Strategia nu livrează direct “același timp” pe care îl calculează intern.

Strategia produce mai întâi modelul intern.

Abia ulterior layerul de decizie / execuție derivează timpul livrabil traderului.


---

# 16. CONFIRM EXECUTION TIME

## 16.1 Definition

În starea CONFIRM, sistemul livrează un interval de expiry recomandat, nu o valoare punctuală.

Câmpurile canonice sunt:

confirm_expiry_min_minutes

confirm_expiry_max_minutes


## 16.2 Derivation Principle

Intervalul CONFIRM este derivat din model_expiry, nu este identic cu acesta.

Conceptual:

se pornește de la model_expiry

se aplică o fereastră de toleranță

rezultă o bandă minim-maxim pentru execuție


## 16.3 Role

Acest interval exprimă flexibilitatea acceptabilă de execuție pentru trader sau execution layer.


---

# 17. OPEN_NOW EXECUTION TIME

## 17.1 Definition

În starea OPEN_NOW, sistemul livrează o valoare exactă de execuție:

open_now_expiry_minutes


## 17.2 Derivation Principle

Această valoare este derivată din model_expiry și este ajustată în funcție de presiunea temporală și starea setup-ului.

Conceptual:

pressure mai mare

corridor mai critic

timing mai matur


→ expiry livrat mai precis și mai strict

## 17.3 Fractional Values

open_now_expiry_minutes poate fi fracționar.

Nu trebuie rotunjit arbitrar dacă modelul necesită precizie.


---

# 18. EXECUTION CONSISTENCY RULE

Trebuie să fie întotdeauna adevărat:

confirm_expiry_min_minutes ≤ open_now_expiry_minutes ≤ confirm_expiry_max_minutes

Dacă această regulă este încălcată, există o inconsistență canonică de time model și aceasta trebuie logată explicit.


---

# 19. TELEMETRY TIME MODEL

## 19.1 Definition

telemetry_checkpoints reprezintă programul de observație folosit după deschiderea trade-ului.

## 19.2 Examples

Checkpoint-uri tipice pot include:

midpoint checkpoint

at-expiry checkpoint

post-expiry +1 minute

post-expiry +3 minutes

post-expiry +5 minutes


## 19.3 Role

Telemetry Time este folosit pentru:

result observation

post-expiry recovery analysis

expiry calibration

quality diagnostics

separation between bad signal and wrong expiry selection



---

# 20. RELATION BETWEEN THE THREE LAYERS

Relația canonică este:

MODEL TIME
  produces feasibility and pressure interpretation
        ↓
EXECUTION TIME
  produces trader-facing expiry semantics
        ↓
TELEMETRY TIME
  produces observation and audit schedule

Aceste layere sunt corelate, dar nu sunt niciodată același lucru.


---

# 21. FSM RELATION

FSM consumă starea temporală a setup-ului.

Time model influențează FSM prin:

model_expiry

model_time_reach_ratio

corridor_time_pressure

time_state


## 21.1 PRE

PRE poate conține doar model time intern.

Expiry extern este opțional și, de regulă, omis.

## 21.2 CONFIRM

CONFIRM presupune:

setup fezabil

pressure pozitiv

apropiere de fereastra executabilă


CONFIRM livrează interval de expiry.

## 21.3 OPEN_NOW

OPEN_NOW presupune:

oportunitate matură

presiune temporală critică

fereastră de execuție precisă


OPEN_NOW livrează expiry exact.


---

# 22. DECISION OBJECT RELATION

DecisionObject trebuie să separe clar layerul temporal intern de layerul de execuție și de layerul de telemetry.

Structura canonică recomandată este:

strategy_metrics
  buffer_distance
  price_speed
  t_needed
  t_needed_adjusted

time_model
  model_expiry
  model_time_reach_ratio
  corridor_time_pressure
  time_state

execution
  confirm_expiry_min_minutes
  confirm_expiry_max_minutes
  open_now_expiry_minutes

telemetry
  telemetry_checkpoints

Nu este permisă utilizarea unui singur câmp ambiguu de tip:

expiry

expiry_minutes


ca reprezentare totală a modelului temporal.


---

# 23. SIGNAL ENGINE RELATION

Signal Engine nu recalculă time model-ul.

Signal Engine:

citește DecisionObject

citește starea FSM

citește blocul execution

transformă aceste date în payload livrabil


Signal Engine nu are voie să rescrie adevărul matematic al strategiei.


---

# 24. OBSERVABILITY RELATION

Pentru audit și telemetrie, sistemul trebuie să poată loga distinct:

buffer_distance

price_speed

t_needed

t_needed_adjusted

model_expiry

model_time_reach_ratio

corridor_time_pressure

time_state

confirm_expiry_min_minutes

confirm_expiry_max_minutes

open_now_expiry_minutes

telemetry_checkpoints


Aceste valori sunt necesare pentru:

time diagnostics

rejection analytics

expiry calibration

strategy performance review

decision audit



---

# 25. LEGACY TERM MAPPING

Maparea oficială vechi → nou este:

buffer_price → buffer_distance

t_needed_minutes → t_needed

t_needed_adjusted_minutes → t_needed_adjusted

model_expiry_minutes → model_expiry


Termenii de execuție externă rămân în minute deoarece descriu explicit durata livrată traderului:

confirm_expiry_min_minutes

confirm_expiry_max_minutes

open_now_expiry_minutes



---

# 26. DOCUMENT PRECEDENCE FOR TIME DOMAIN

Pentru orice conflict privind domeniul timpului, acest document are prioritate față de:

legacy pre-unification time-model canon

SIGNAL_TIME_MODEL_SPEC_v2.0.0.md

signal_time_model_and_decision_object_v1.0.0.md


FSM rules rămân în FSM_DECISION_ENGINE_SPEC_v1.0.0.md, dar orice conflict despre definiția metricilor temporale este rezolvat de acest document.

Contractul final de payload rămâne în DECISION_OBJECT_CANONICAL_SPEC_v1.0.0.md, dar orice conflict despre semnificația câmpurilor temporale este rezolvat de acest document.


---

# 27. STATUS OF PREVIOUS DOCUMENTS

## 27.1 Legacy pre-unification time-model canon

Status nou recomandat:

Superseded by TIME_MODEL_UNIFIED_CANON_v2.0.0.md

## 27.2 SIGNAL_TIME_MODEL_SPEC_v2.0.0.md

Status nou recomandat:

Superseded by TIME_MODEL_UNIFIED_CANON_v2.0.0.md

## 27.3 signal_time_model_and_decision_object_v1.0.0.md

Status nou recomandat:

Superseded / split into domain-specific canonical docs

## 27.4 WAVE1_TIME_MODEL_PATCH_SPEC_v1.0.0.md

Status nou recomandat:

Transitional historical patch spec

Nu mai este sursă de adevăr pentru modelul temporal.


---

# 28. IMPLEMENTATION RULE

De la această versiune înainte:

orice patch pe time model trebuie ancorat în acest document

niciun document nou nu trebuie să redefinească separat modelul temporal

documentele vecine trebuie să refere acest document, nu să-l dubleze

orice cod patch privind metricile temporale trebuie să map-eze explicit la acest document



---

# 29. FINAL PRINCIPLE

Time model-ul BinaryBot este un sistem stratificat.

Strategia calculează:

distanță

viteză

timp necesar

fezabilitate

presiune temporală


FSM decide maturitatea oportunității.

Execution layer livrează expiry-ul executabil.

Telemetry layer observă rezultatul.

Aceste layere trebuie să rămână separate, explicite și auditabile.

Acest document este singurul canon unificat pentru domeniul timpului. ce
