BINARYBOT — STRATEGY INTELLIGENCE SYSTEM
Version: 1.0
Status: CANONICAL SPECIFICATION

SECTION 1 — PURPOSE

Strategy Intelligence System este un subsistem al arhitecturii BinaryBot care transformă logurile operaționale generate de motorul de semnale într-un sistem complet de analiză, diagnostic și control al strategiei.

Acest sistem are rolul de a permite operatorului să înțeleagă exact modul în care strategia funcționează, de ce anumite semnale sunt respinse, care sunt blocajele strategiei și ce parametri trebuie ajustați pentru optimizare.

Subsystemul introduce trei componente majore:

1. Strategy Heatmap (AI Strategy Auditor)
2. Admin Control Panel (Telegram Strategy Control Interface)
3. Signal Debug Dashboard (Operational Signal Diagnostic Interface)

Aceste componente permit operatorului să controleze și să optimizeze strategia fără modificări directe în codul motorului de semnale.

Prin implementarea acestui sistem, BinaryBot evoluează de la un simplu generator de semnale către o platformă completă de analiză și optimizare strategică.

SECTION 2 — ARCHITECTURE OVERVIEW

Strategy Intelligence System este construit peste infrastructura existentă a motorului de semnale.

Fluxul operațional este următorul:

Signal Engine
↓
Observability Logger
↓
engine_events.jsonl
↓
Strategy Intelligence System
↓
Analytics Reports
↓
Telegram Admin Control

Fluxul complet de date:

Signal Engine execută scanarea pieței
↓
Motorul produce evenimente de decizie
↓
Evenimentele sunt scrise în observability logs
↓
Strategy Auditor analizează logurile
↓
Sunt generate rapoarte analitice
↓
Operatorul controlează strategia prin Telegram

Subsystemul utilizează următoarele componente existente:

core.signal_engine
core.observability_logger
observability/engine_events.jsonl

și introduce noi componente analitice în directorul analytics.

SECTION 3 — COMPONENT 1 — STRATEGY HEATMAP

3.1 PURPOSE

Strategy Heatmap reprezintă un modul de analiză statistică care examinează comportamentul strategiei pe baza deciziilor motorului de semnale.

Acest modul detectează automat blocajele strategiei și generează diagnostice privind comportamentul sistemului.

Exemple de diagnostice generate automat:

SR too tight
RSI threshold too strict
Trend filter too aggressive
Spike filter blocking signals
Structure score insufficient
Feasibility gate too restrictive

Strategy Heatmap permite identificarea rapidă a cauzelor pentru care strategia produce prea puține semnale sau respinge oportunități valide.

3.2 DATA SOURCE

Fișierul principal analizat este:

/opt/binarybot/observability/engine_events.jsonl

Acest fișier conține evenimente generate de motorul de semnale pentru fiecare analiză de piață.

Evenimente relevante pentru analiză:

event_type = decision

Tipuri de decizie:

decision_kind = REJECT
decision_kind = PRE
decision_kind = CONFIRM
decision_kind = OPEN_NOW

Fiecare eveniment include informații detaliate despre:

symbol
score_total
gates
reject_reason
trend_class
rsi
ema values
support/resistance distances

Aceste informații sunt utilizate pentru generarea heatmap-ului strategiei.

3.3 METRICS GENERATED

Strategy Heatmap calculează următoarele metrici strategice.

DECISION DISTRIBUTION

Distribuția deciziilor motorului:

total decisions
PRE signals
CONFIRM signals
OPEN signals
REJECT signals

Această distribuție indică dacă strategia produce semnale sau respinge majoritatea oportunităților.

REJECT REASON DISTRIBUTION

Distribuția motivelor de respingere:

SR_SPACE_INSUFFICIENT
SPIKE_FILTER
RSI_FILTER
TREND_MISMATCH
FEASIBILITY_FAIL
STRUCTURE_FAIL

Exemplu de raport:

Top Reject Reasons

SR_SPACE_INSUFFICIENT : 64%
RSI_FILTER : 21%
SPIKE_FILTER : 8%
OTHER : 7%

Interpretare:

Strategia respinge majoritatea semnalelor din cauza distanței insuficiente față de suport/rezistență.

Acest lucru indică faptul că parametrul SR buffer este prea restrictiv.

SYMBOL ACTIVITY

Analiza activității pe simboluri:

EURUSD
GBPUSD
USDJPY
EURAUD
BTCUSD
ETHUSD

Această analiză permite identificarea simbolurilor care generează oportunități frecvente.

AVERAGE SCORE ANALYSIS

Analiza scorurilor strategiei:

avg_score
max_score
min_score

Această metrică indică dacă pragurile strategiei sunt prea ridicate sau prea scăzute.

STRATEGY BOTTLENECKS

Strategy Heatmap detectează automat blocajele strategiei.

Exemplu:

SR distance too strict
RSI threshold too restrictive
Trend alignment filter blocking signals
Spike detection too sensitive

Aceste blocaje sunt raportate operatorului pentru optimizare.

SECTION 4 — STRATEGY AUDITOR OUTPUT

Strategy Auditor generează rapoarte zilnice care documentează comportamentul strategiei.

Formate generate:

JSON
Markdown

Locația rapoartelor:

/opt/binarybot/analytics/reports/

Exemple de fișiere generate:

daily_strategy_audit_2026_03_06.json
daily_strategy_audit_2026_03_06.md

Raportul include:

Overview
Decision statistics
Reject reasons
Symbol activity
Strategy bottlenecks

Aceste rapoarte permit analiza evoluției strategiei în timp.

SECTION 5 — COMPONENT 2 — ADMIN CONTROL PANEL

5.1 PURPOSE

Admin Control Panel oferă operatorului control direct asupra parametrilor strategiei prin Telegram.

Acest sistem permite ajustarea strategiilor fără modificarea codului sau repornirea motorului.

5.2 COMMAND INTERFACE

Telegram Bot Admin Commands:

/strategy
/symbols
/thresholds
/sr
/spike

Aceste comenzi sunt disponibile exclusiv administratorului botului.

5.3 COMMAND DETAILS

COMMAND: /strategy

Afișează configurarea completă a strategiei.

Exemplu output:

Strategy Status

Trend Weight: 30
RSI Weight: 20
Structure Weight: 15
Body Weight: 10

Thresholds

PRE: 70
CONFIRM: 75
OPEN: 80

Această comandă permite verificarea rapidă a parametrilor activi.

COMMAND: /symbols

Afișează simbolurile monitorizate.

Exemplu:

FOREX

EUR/USD
GBP/USD
USD/JPY
USD/CHF
EURAUD

CRYPTO

BTC/USD
ETH/USD
SOL/USD

Operatorul poate modifica lista simbolurilor prin această interfață.

COMMAND: /thresholds

Permite modificarea pragurilor strategiei.

Exemple:

/thresholds PRE 68
/thresholds CONFIRM 72
/thresholds OPEN 78

Aceste valori sunt aplicate imediat strategiei.

COMMAND: /sr

Controlează distanța minimă față de suport și rezistență.

Exemplu:

/sr 0.0005

Interpretare:

Minimum space required between price and support/resistance.

COMMAND: /spike

Controlează parametrii filtrului de spike.

Exemple:

/spike wick_ratio 5.5
/spike jump_atr 2.2

Aceste valori controlează sensibilitatea detecției de spike.

SECTION 6 — COMPONENT 3 — SIGNAL DEBUG DASHBOARD

6.1 PURPOSE

Signal Debug Dashboard oferă explicația completă pentru fiecare decizie de semnal.

Operatorul poate vedea exact de ce un semnal a fost respins sau acceptat.

6.2 TELEGRAM DEBUG OUTPUT

Exemplu de mesaj generat:

PAIR: EURAUD
TF: M15

TREND: WITH_TREND
RSI: 35.6

SCORE: 66.5

STATUS: REJECT

REASON:
SR_SPACE_INSUFFICIENT

DETAILS

Available space: 0.00005
Required space: 0.00066
Nearest support: 1.65097
Nearest resistance: 1.6511

Acest mesaj oferă transparență completă asupra deciziilor motorului.

6.3 DEBUG FIELDS

Dashboardul expune următoarele informații:

symbol
timeframe
trend_class
rsi
ema_gap
atr
score
thresholds
reject_reason
support_distance
resistance_distance

Aceste informații permit diagnosticarea precisă a comportamentului strategiei.

SECTION 7 — BENEFITS

Strategy Intelligence System oferă următoarele beneficii:

Transparent Strategy Behavior

Operatorul poate vedea exact:

why signals fail
why signals trigger

Strategy Optimization

Se pot ajusta:

thresholds
filters
distance rules

Faster Development

Nu mai este necesară modificarea codului pentru:

strategy tuning
symbol changes
parameter adjustments

SECTION 8 — FILE STRUCTURE

Fișierele principale ale sistemului:

/opt/binarybot/tools/strategy_auditor_daily.py
/opt/binarybot/tools/strategy_auditor_lib.py

Directoare analitice:

/opt/binarybot/analytics/reports/
/opt/binarybot/analytics/cache/

Extensii ulterioare:

strategy_auditor_compare.py
strategy_auditor_send_summary.py

SECTION 9 — FUTURE EXTENSIONS

AI Strategy Optimizer

Algoritm care sugerează automat:

new thresholds
optimal SR distance
RSI tuning

Signal Performance Tracking

Tracking pentru:

win rate
expiry accuracy
symbol performance

Strategy Evolution Engine

Motor de testare automată:

A/B strategy testing
parameter simulation
historical replay

SECTION 10 — CONCLUSION

Strategy Intelligence System transformă BinaryBot dintr-un simplu generator de semnale într-un sistem complet de:

Strategy Monitoring
Strategy Diagnostics
Strategy Optimization
Operational Control

Acest subsistem reprezintă fundamentul pentru evoluția viitoare a platformei către:

Autonomous Strategy AI