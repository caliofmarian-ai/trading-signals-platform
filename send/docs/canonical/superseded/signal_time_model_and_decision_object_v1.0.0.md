# BINARYBOT CANONICAL SPECIFICATION  
## SIGNAL TIME MODEL, STATE TRANSITIONS AND DECISION OBJECT

Version: 1.0.0  
Status: Canonical  
Scope: Strategy Engine / Signal Engine / Distribution Layer

---

# 1. PURPOSE OF THIS DOCUMENT

Acest document definește modelul canonic de timp al strategiei, stările semnalului, regulile de tranziție FSM și contractul oficial al obiectului de decizie (DecisionObject).

Scopul acestui document este:

- eliminarea ambiguității între timpul intern al modelului și timpul extern livrat traderului  
- definirea clară a pipeline-ului de validare al semnalelor  
- stabilirea contractului stabil dintre Strategy Engine și Signal Engine  
- furnizarea bazei canonice pentru implementarea codului  

Acest document este **sursa canonică de adevăr pentru implementarea codului**.

---

# 2. FUNDAMENTAL PRINCIPLE

Strategia nu produce direct mesaje pentru trader.

Strategia produce un **obiect matematic de decizie**.

Acest obiect conține:

- contextul pieței  
- rezultatele calculelor  
- starea FSM  
- modelul temporal  
- instrucțiunile de execuție  

Acest obiect se numește:

DecisionObject

Acesta este consumat ulterior de:

- Signal Engine  
- Distribution Router  
- Analytics Engine  
- Observability System  
- Trade Journal  

---

# 3. SIGNAL STATE MACHINE

Semnalele strategiei evoluează într-o mașină de stări finite (FSM).

Pipeline-ul canonic este:

NO_SIGNAL → REJECT → PRE → CONFIRM → OPEN_NOW

Aceste stări reprezintă **niveluri progresive de validare a oportunității de trade**.

---

# 4. STATE DEFINITIONS

## 4.1 NO_SIGNAL

Nu există oportunitate validă.

Strategia rulează scan normal, dar nu produce setup executabil.

Nu există instrucțiuni de execuție.

---

## 4.2 REJECT

A fost detectat un setup posibil, dar a fost respins de gates strategice.

Exemple:

- spike filter  
- feasibility gate  
- corridor invalid  
- volatilitate incompatibilă  

REJECT există pentru **observability și analytics**, nu pentru execuție.

---

## 4.3 PRE

PRE reprezintă o oportunitate detectată și promițătoare.

Setup-ul:

- are direcție coerentă  
- are corridor valid preliminar  
- depășește scorul minim  

Dar momentul optim nu a fost încă atins.

PRE este o stare de **monitorizare activă a oportunității**.

PRE nu trebuie obligatoriu să conțină expiry extern.

---

## 4.4 CONFIRM

CONFIRM indică faptul că setup-ul este **valid și aproape executabil**.

Condiții tipice:

- scor consolidat  
- corridor confirmat  
- presiune temporală pozitivă  
- direcție stabilă  

CONFIRM livrează **un interval de expiry**, nu o valoare exactă.

Acest interval exprimă **fereastra probabilă de execuție**.

---

## 4.5 OPEN_NOW

OPEN_NOW indică faptul că **momentul optim de execuție a fost atins**.

Condiții tipice:

- pressure temporal critic  
- corridor valid pentru execuție  
- scor ridicat  
- direcție stabilă  

OPEN_NOW livrează **o valoare exactă de expiry**.

Această valoare poate fi **fracționară**.

Nu trebuie rotunjită arbitrar deoarece reflectă **produsul matematic al modelului**.

---

# 5. INTERNAL TIME MODEL

Strategia utilizează un model temporal intern.

Acest model nu trebuie confundat cu expiry-ul extern.

Câmpurile interne principale sunt:

- t_needed_minutes  
- t_needed_adjusted_minutes  
- model_expiry_minutes  
- corridor_time_pressure  
- time_state  

---

## 5.1 t_needed_minutes

Timpul brut estimat necesar pentru ca prețul să atingă bufferul sau distanța relevantă.

---

## 5.2 t_needed_adjusted_minutes

Timpul ajustat după:

- trend context  
- volatility  
- structure factors  
- multiplicatori strategici  

---

## 5.3 model_expiry_minutes

Expiry intern al modelului.

Este derivat matematic din:

t_needed_adjusted_minutes

Acest expiry este utilizat pentru:

- feasibility  
- corridor evaluation  
- scoring  
- analytics  

Nu este livrat direct traderului.

---

## 5.4 corridor_time_pressure

Indicator temporal derivat din relația dintre:

- distanță  
- viteză  
- expiry intern  

Acest indicator descrie **cât de critică este fereastra de oportunitate**.

---

## 5.5 time_state

Starea temporală a oportunității.

Valori canonice:

EARLY  
BUILDING  
READY  
CRITICAL  
LATE  
EXPIRED  

Acest câmp influențează **tranzițiile FSM**.

---

# 6. EXTERNAL EXPIRY MODEL

Expiry-ul livrat traderului este derivat din modelul intern.

Există două tipuri de expiry extern:

confirm_expiry_range  
open_now_expiry  

---

## 6.1 CONFIRM EXPIRY

CONFIRM livrează **un interval de expiry**.

Câmpuri:

confirm_expiry_min_minutes  
confirm_expiry_max_minutes  

Acest interval exprimă **toleranța de execuție**.

Traderul poate executa trade-ul în interiorul acestui interval.

---

## 6.2 OPEN_NOW EXPIRY

OPEN_NOW livrează o valoare exactă:

open_now_expiry_minutes

Aceasta poate fi **fracționară**.

Valoarea reprezintă **produsul matematic final al oportunității**.

---

# 7. EXPIRY DERIVATION RULES

Expiry-ul extern este derivat din:

model_expiry_minutes

---

## 7.1 CONFIRM WINDOW

Intervalul CONFIRM se construiește în jurul valorii modelului.

Conceptual:

confirm_delta = model_expiry_minutes × confirm_window_factor

Rezultat:

confirm_expiry_min_minutes = model_expiry_minutes − confirm_delta  
confirm_expiry_max_minutes = model_expiry_minutes + confirm_delta  

---

## 7.2 OPEN_NOW VALUE

OPEN_NOW produce o valoare punctuală derivată din model.

Această valoare reflectă **momentul optim de execuție**.

Ea poate fi **fracționară**.

---

# 8. EXPIRY CONSISTENCY RULE

Trebuie să fie adevărată relația:

confirm_expiry_min_minutes ≤ open_now_expiry_minutes ≤ confirm_expiry_max_minutes

Dacă această regulă nu este respectată, există **o eroare de strategie**.

---

# 9. STATE TRANSITION RULES

Tranzițiile între stări sunt controlate de:

- scoring  
- corridor validity  
- feasibility  
- time_state  

---

## 9.1 PRE → CONFIRM

Permis dacă:

- scorul depășește pragul confirm  
- corridor este valid  
- timing-ul indică apropierea execuției  

---

## 9.2 CONFIRM → OPEN_NOW

Permis dacă:

- momentul optim a fost atins  
- pressure temporal devine critic  
- execuția este fezabilă  

---

## 9.3 DEGRADATION

Setup-ul se poate degrada:

CONFIRM → PRE  
CONFIRM → REJECT  
OPEN_NOW → CONFIRM  
OPEN_NOW → REJECT  

---

# 10. DECISION OBJECT CONTRACT

Strategia trebuie să producă un obiect standardizat.

Structura canonică este:

identity  
market_context  
strategy_metrics  
time_model  
corridor_model  
scoring  
state  
execution  
observability  

---

# 11. IDENTITY BLOCK

identity  
signal_id  
symbol  
direction  
candle_ts  
timeframe  

Acest block identifică **unic ideea de trade**.

signal_id trebuie să persiste pe tot pipeline-ul:

PRE → CONFIRM → OPEN_NOW

---

# 12. MARKET CONTEXT BLOCK

market_context  
price  
spread  
volatility  
candle_range  

Acest block conține **contextul brut al pieței** la momentul evaluării.

---

# 13. STRATEGY METRICS BLOCK

strategy_metrics  
buffer_distance  
t_needed_minutes  
t_needed_adjusted_minutes  

Acest block conține metricile temporale și spațiale brute ale modelului.

---

# 14. TIME MODEL BLOCK

time_model  
model_expiry_minutes  
corridor_time_pressure  
time_state  

Acest block definește **modelul intern de timp**.

---

# 15. CORRIDOR MODEL BLOCK

corridor_model  
corridor_valid  
corridor_open_ok  
corridor_width  

Acest block definește **geometria operațională a setup-ului**.

---

# 16. SCORING BLOCK

scoring  
score_total  
score_components  

score_components poate conține:

momentum  
structure  
corridor  
timing  
feasibility  

---

# 17. STATE BLOCK

state  
signal_state  

Valori posibile:

NO_SIGNAL  
REJECT  
PRE  
CONFIRM  
OPEN_NOW  

---

# 18. EXECUTION BLOCK

execution  
confirm_expiry_min_minutes  
confirm_expiry_max_minutes  
open_now_expiry_minutes  

Popularea depinde de starea semnalului.

### PRE
Nu există expiry extern obligatoriu.

### CONFIRM
Se livrează intervalul:

confirm_expiry_min_minutes  
confirm_expiry_max_minutes  

### OPEN_NOW
Se livrează valoarea exactă:

open_now_expiry_minutes  

---

# 19. OBSERVABILITY BLOCK

observability  
decision_reason  
rejected_by  
diagnostics  

Acest block permite analizarea motivelor pentru care semnalele au fost:

- promovate  
- respinse  
- degradate  

---

# 20. CANONICAL STATE MATRIX

State | Internal Model Time | External Expiry
------|--------------------|----------------
NO_SIGNAL | optional | none
REJECT | yes | none
PRE | yes | optional
CONFIRM | yes | interval
OPEN_NOW | yes | exact value

---

# 21. CANONICAL PRINCIPLE OF SEPARATION

Același câmp nu poate reprezenta simultan:

- expiry intern de model  
- expiry extern de execuție  

Este interzis canonic să folosim un câmp ambiguu:

expiry_minutes

Separarea corectă este:

Intern:  
model_expiry_minutes  

Extern CONFIRM:  
confirm_expiry_min_minutes  
confirm_expiry_max_minutes  

Extern OPEN_NOW:  
open_now_expiry_minutes  

---

# 22. FINAL PRINCIPLE

Strategia produce **DecisionObject**.

Signal Engine:

- citește starea  
- citește câmpurile de execuție  
- construiește mesajul pentru trader  

Distribuția **nu recalculă strategia**.

Fluxul canonic al sistemului este:

Strategy → DecisionObject → Signal Engine → User Message

Aceasta este **arhitectura canonică a sistemului**.