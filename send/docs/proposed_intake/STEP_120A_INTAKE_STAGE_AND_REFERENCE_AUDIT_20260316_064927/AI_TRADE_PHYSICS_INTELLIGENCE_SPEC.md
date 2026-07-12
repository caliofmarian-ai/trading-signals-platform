
DOCUMENT CANONIC

# AI_TRADE_PHYSICS_INTELLIGENCE_SPEC.md

## 1. Scopul documentului

Acest document definește arhitectura conceptuală pentru Self-Calibrating Intelligence Layer al botului DROPi Trading Engine.

Layerul AI va avea rolul de a:

1️⃣ modela probabilitatea reală a reușitei unui trade
2️⃣ învăța din istoricul deciziilor
3️⃣ recalibra strategia în mod controlat
4️⃣ modela piața în 4 dimensiuni

Implementarea acestui layer va avea loc după stabilizarea strategiei actuale și finalizarea testelor de scan (STEP 100).


---

## 2. Modelul fundamental: Trade Physics Model

Strategia botului este bazată pe ideea că un trade reușit trebuie să respecte 4 constrângeri fizice ale pieței.

Acestea sunt:

1️⃣ Energie (volatilitate)
2️⃣ Spațiu (structură)
3️⃣ Timp (expirare)
4️⃣ Flux (momentum)

Aceste dimensiuni sunt reprezentate de variabilele:

E = Buffer-ATR Efficiency
S = Reachability Ratio
T = Time-to-Buffer Ratio
F = Momentum Alignment Factor


---

## 3. Variabilele fundamentale

### 3.1 Buffer-ATR Efficiency (E)

Definește energia necesară pentru a atinge bufferul.

Formula:

E = buffer_distance / ATR

Interpretare:

E < 0.6   → buffer ușor de atins
E 0.6–1.0 → posibil
E > 1.0   → dificil


---

### 3.2 Reachability Ratio (S)

Definește dacă există spațiu structural pentru trade.

Formula:

S = available_space / required_space

unde:

available_space = distanța până la cel mai apropiat SR
required_space = buffer_distance

Interpretare:

S > 2 → spațiu excelent
S 1–2 → acceptabil
S < 1 → blocaj structural


---

### 3.3 Time-to-Buffer Ratio (T)

Definește dacă există timp suficient pentru mișcare.

Formula:

T = t_available / t_needed

unde:

t_needed = buffer_distance / directional_effective_speed


---

### 3.4 Momentum Alignment Factor (F)

Definește dacă fluxul pieței susține direcția trade-ului.

Formula aproximativă:

F = price_velocity / ATR

Interpretare:

F > 0 → momentum favorabil
F ≈ 0 → piață neutră
F < 0 → momentum opus


---

## 4. Trade Probability Score (TPS)

Cele 4 variabile sunt combinate într-un scor unic:

TPS = sigmoid(
    w1*(1/E) +
    w2*log(S) +
    w3*log(T) +
    w4*F
)

unde:

TPS ∈ [0,1]

Interpretare:

TPS < 0.55 → reject
TPS 0.55–0.75 → watchlist
TPS 0.75–0.85 → focus candidate
TPS > 0.85 → open candidate


---

## 5. Îmbunătățirea critică: Directional Effective Speed

În loc de:

avg_price_speed

se folosește:

directional_effective_speed

care este:

recency-weighted
directional
noise-filtered

Formula conceptuală:

directional_delta_i =
max(close_i − close_{i−1}, 0)   (BUY)

directional_delta_i =
max(close_{i−1} − close_i, 0)   (SELL)

Speed final:

directional_effective_speed =
weighted_sum(direction_moves) / weighted_time


---

## 6. Flow Efficiency

O metrică suplimentară:

flow_efficiency =
directional_speed / gross_speed

Interpretare:

≈1.0 → mișcare curată
≈0.5 → piață zgomotoasă
≈0.2 → consolidare

Această variabilă poate fi folosită de AI pentru filtrarea contextelor instabile.


---

## 7. Dataset pentru AI

Datasetul de training va conține:

symbol
trend_class
rsi
ema_gap
atr
avg_range
buffer_distance
buffer_to_atr
reachability
time_ratio
momentum_alignment
flow_efficiency
score_components
decision
outcome

Labelul principal:

trade_success_probability


---

## 8. Model AI recomandat

Modelul preferat pentru datele botului este:

Gradient Boosted Trees:

LightGBM

XGBoost


Motiv:

excelent pentru date tabulare
rapid
explicabil
robust


---

## 9. Self-Learning Architecture

Layerul AI va avea structura:

Decision Engine
      ↓
Outcome Recorder
      ↓
Signal Lineage
      ↓
Calibration Engine
      ↓
Parameter Recommendations
      ↓
Admin Approval


---

## 10. Safety Governance

AI nu poate modifica direct strategia.

Moduri de operare:

recommend-only
admin-approve
bounded-auto-adjust


---

## 11. Momentul implementării

Implementarea acestui sistem va începe după finalizarea fazei de stabilizare a strategiei.

Ordinea corectă:

1️⃣ stabilizare scan scheduler
2️⃣ calibrare thresholds
3️⃣ STEP 100 market coverage test
4️⃣ colectare dataset
5️⃣ AI training
6️⃣ calibration engine


---

## 12. Obiectivul final

Transformarea botului într-un sistem care nu doar detectează direcția pieței, ci modelează probabilitatea reală a mișcării prețului.

Modelul final descrie piața în:

4 dimensiuni
energie
spațiu
timp
flux


---

Concluzie

Acest model permite botului să evolueze de la:

rule-based trading bot

la:

quantitative probability engine

capabil să învețe din propriile decizii și să își ajusteze strategia în mod controlat.
