# ARCHITECTURE_CODE_MAPPING.md
BinaryBot — Architecture → Code Mapping
Version: 1.0.0
Status: Canonical

Linked Docs:
- ALGO_SPEC.md
- FSM_SPEC.md
- TELEGRAM_UX.md
- RISK_MODEL.md
- SIGNAL_DISTRIBUTION_SPEC.md
- CHANNEL_CONFIG_SPEC.md
- OBSERVABILITY_LOGGING_SPEC.md
- PERFORMANCE_ANALYTICS_SPEC.md
- PARAMS_REFERENCE.md
- CHECKLIST.md
- CHANGELOG.md

---

## 0) PURPOSE

Documentul acesta mapează (1:1) **arhitectura + documentele canonice** la **modulele reale din cod**.

Regulă:
- Documentele din `/opt/binarybot/docs` sunt „constituția”.
- Codul trebuie să indice clar *unde* se aplică fiecare regulă.
- Nicio logică canonică nu rămâne “în aer”.

---

## 1) FOLDER MAP (SERVER)

Root runtime:
- `/opt/binarybot/`

Config & state (persistente):
- `/opt/binarybot/config/algo_params.json`              (SINGLE SOURCE OF TRUTH: parametri strategie)
- `/opt/binarybot/active_symbols.json`                  (simboluri selectate din UI)
- `/opt/binarybot/focus_state.json`                     (watchlist/pending_open/cooldown + FSM state)
- `/opt/binarybot/settings.json`                        (buffer_mode + setări operator)
- `/opt/binarybot/dist_state.json`                      (tier counters/state/reset; distribuție semnale)
- `/opt/binarybot/observability/`                       (loguri JSONL / rotire)
- `/opt/binarybot/analytics/`                           (agregări, rapoarte, baseline-uri)
- `/opt/binarybot/outcomes/outcomes.jsonl`  (ELITE outcomes)

Docs (canonice):
- `/opt/binarybot/docs/*.md`

Cod (numele pot varia, dar rolurile sunt fixe):
- `/opt/binarybot/strategy_v2.py`
- `/opt/binarybot/signal_engine.py`                     (orchestrator: scan wide/focus + FSM calls + emit events)
- `/opt/binarybot/bot_service.py`                       (Telegram commands/UI/admin panel)
- `/opt/binarybot/distribution_router.py`               (tier routing: FREE/BASIC/PRO/ELITE)
- `/opt/binarybot/observability_logger.py`              (events -> JSONL + admin topic logs)
- `/opt/binarybot/analytics_engine.py`                  (stats/perf/leaderboards)
- `/opt/binarybot/fsm_runtime.py`                       (state transitions + invariants)
- `/opt/binarybot/storage.py`                           (atomic read/write JSON, locks)
- `/opt/binarybot/outcome_service.py` 

NOTĂ:
- Dacă unele fișiere nu există încă, acesta este CONTRACTUL de creat (nume identice recomandate).



## 1A) HIGH-LEVEL SYSTEM FLOW (DIAGRAM)

This section describes the complete operational flow of BinaryBot, showing how market data moves through the engine, how signals are generated, distributed, and how feedback is collected and analyzed.

This diagram represents the real architecture defined across all canonical documents.

System Flow:

MARKET DATA
(TwelveData API / Candle Feed)
↓
CANDLE ADAPTER
(normalizes candle format, ensures newest-first ordering)
↓
SIGNAL ENGINE
(orchestrator loop controlling WIDE_SCAN and FOCUS_MODE)
↓
STRATEGY CORE (strategy_v2.py)
(scoring engine, buffer calculation, expiry logic, risk gates)
↓
DECISION OUTPUT
PRE / CONFIRM / OPEN_NOW / REJECT
↓
FSM RUNTIME
(state management: IDLE → WATCHLIST → LIVE_SENT → COOLDOWN)
↓
SIGNAL EVENT EMITTED
(normalized internal event with SIGNAL_ID)
↓
DISTRIBUTION ROUTER
(decides which tiers receive the signal)
↓
TELEGRAM CHANNEL TIERS
FREE
BASIC
PRO
ELITE
↓
ELITE OUTCOME SERVICE
(WIN / LOSE / MISSED reporting system)
↓
OBSERVABILITY LOGGER
(all events written to JSONL logs)
↓
ANALYTICS ENGINE
(statistical analysis and research layer)
↓
ADMIN CONTROL PANEL
(configuration, monitoring, research)

---

SIGNAL FLOW EXPLANATION

1. Market Data Layer

BinaryBot receives candle data from external market APIs.

Primary source:

TwelveData API

Data received:

symbol
timestamp
open
high
low
close
volume

The Candle Adapter converts this raw data into the normalized internal format used by the strategy engine.

---

2. Signal Engine (Orchestrator)

Module:

signal_engine.py

This component controls the main runtime loop of the system.

It operates in two scanning modes:

WIDE_SCAN

Scans all symbols selected by the operator via the Admin Panel.

FOCUS_MODE

Activated when a PRE signal appears.
Engine prioritizes that symbol and attempts to confirm the setup.

The engine sends candle data to the strategy module and receives trading decisions.

---

3. Strategy Core

Module:

strategy_v2.py

This module implements the trading logic defined in ALGO_SPEC.md.

Responsibilities include:

buffer calculation
expiry calculation
trend scoring
momentum scoring
support/resistance rejection
spike detection
feasibility validation

Output is a normalized Decision object.

Possible results:

PRE
CONFIRM
OPEN_NOW
REJECT

---

4. FSM Runtime

Module:

fsm_runtime.py

The Finite State Machine ensures the strategy behaves in a structured lifecycle.

Possible states:

IDLE
WATCHLIST
LIVE_SENT
COOLDOWN

State transitions enforce several invariants:

maximum two symbols in focus
no duplicate signals within the same candle
cooldown after trade execution

FSM state is stored in:

focus_state.json

This allows the system to survive restarts without losing state.

---

5. Signal Event Emission

When the engine decides to emit a signal, a standardized internal object is created.

Example structure:

SignalEvent
signal_id
symbol
direction
timeframe
stage (PRE / CONFIRM / OPEN_NOW)
buffer
expiry
confidence
timestamp

This event is passed to the distribution layer.

---

6. Distribution Router

Module:

distribution_router.py

This module decides which Telegram channels receive the signal.

Tier system:

FREE
BASIC
PRO
ELITE

Rules include:

OPEN_NOW limits per tier
silent mode when limit reached
daily reset at 08:10 Europe/London

Tier counters and state are stored in:

dist_state.json

Distribution also ensures deduplication:

tier + SIGNAL_ID + stage

---

7. Telegram Channels

Signals appear in Telegram channels in three stages:

PRE
CONFIRM
OPEN_NOW

FREE, BASIC, and PRO channels follow distribution limits.

ELITE receives all signals without restriction.

---

8. Outcome Reporting System

Module:

outcome_service.py

Only active in the ELITE channel.

After an OPEN_NOW signal, users can report trade results.

Available outcomes:

WIN
LOSE
MISSED

Rules:

one outcome per user per signal
first vote wins
vote window expires after trade expiry + 5 minutes

Votes are stored in:

/opt/binarybot/outcomes/outcomes.jsonl

This dataset provides real-world feedback about signal performance.

---

9. Observability Logger

Module:

observability_logger.py

Every significant system event is recorded in structured logs.

Log examples include:

engine_start
signal_pre
signal_confirm
signal_open_now
tier_publish
user_outcome
tier_reset

Logs are stored in:

/opt/binarybot/observability/*.jsonl

These logs form the primary data source for analytics.

---

10. Analytics Engine

Module:

analytics_engine.py

Processes both system logs and outcome reports.

Key metrics include:

win rate
expectancy
symbol performance
focus efficiency
signal conversion rates
session performance

Analytics data supports research and algorithm improvement.

---

11. Admin Control Panel

Module:

bot_service.py

Provides operational control of the system.

Admin can:

select active symbols
change buffer mode
view engine status
view tier counters
view analytics reports
view system logs

The Admin Panel also allows direct access to architecture documents stored in "/docs".

Documents are sent as ".md" files to prevent message truncation.

---

FOUR PRIMARY SYSTEM FLOWS

BinaryBot operates through four major flows.

Trading Flow

Market Data
→ Strategy Engine
→ Signal Decision
→ FSM Transition

---

Distribution Flow

Signal Event
→ Distribution Router
→ Telegram Channels

---

Feedback Flow

OPEN_NOW
→ User Outcome Voting
→ Outcome Storage

---

Analytics Flow

Logs + Outcomes
→ Analytics Engine
→ Admin Research Dashboard

---

This architecture guarantees separation between trading logic, signal distribution, user feedback, and statistical analysis.


---

## 1B) INTERNAL MODULE ARCHITECTURE (DIAGRAM)

The following diagram illustrates the internal architecture of BinaryBot and the relationships between the core modules.
It represents the operational pipeline from market data ingestion to signal generation, distribution, user feedback, and analytics.

IMPORTANT:
- Wide Scan + Focus scheduling live inside `signal_engine.py` (the orchestrator).
- Strategy is pure logic (`strategy_v2.py`).
- FSM is invoked by the engine to persist/validate lifecycle states.
- Distribution is a separate layer that only routes already-decided signal events.

                    MARKET DATA (API)
                         │
                         ▼
                 [A] CANDLE ADAPTER
        (normalize external market data; newest-first)
                         │
                         ▼
                 [B] PARAMS LOADER
         (load + validate config/algo_params.json)
                         │
                         ▼
                [C] SIGNAL ENGINE LOOP
     signal_engine.py (ORCHESTRATOR / SCHEDULERS)
   ┌───────────────────────────────────────────────┐
   │  - WIDE_SCAN scheduler (scan active symbols)  │
   │  - FOCUS scheduler (max 2 focus symbols)      │
   │  - engine dedup (symbol+candle+stage)         │
   └───────────────┬───────────────────────────────┘
                   │ calls
                   ▼
            [D] STRATEGY CORE (PURE LOGIC)
                 strategy_v2.py
      (gates + scoring + buffer + expiry decision)
                   │ returns Decision
                   ▼
        [E] FSM RUNTIME (LIFECYCLE + INVARIANTS)
               fsm_runtime.py
      (IDLE→WATCHLIST→LIVE_SENT→COOLDOWN; persist)
                   │ persists
                   ▼
               focus_state.json
                   │ emits
                   ▼
        [F] SIGNAL EVENT WRAPPER / EMITTER
      (Decision → SignalEvent with stable SIGNAL_ID)
                   │
                   ▼
          [G] DISTRIBUTION ROUTER (TIERS)
             distribution_router.py
 (FREE/BASIC/PRO/ELITE routing + limits + silent mode)
                   │ persists
                   ▼
               dist_state.json
                   │ publishes
                   ▼
            [H] TELEGRAM PUBLISHER (API)
         (sendMessage / editMessage abstraction)
                   │
     ┌─────────────┼───────────────────────────┐
     ▼             ▼                           ▼
   FREE          BASIC                         PRO
 Telegram       Telegram                      Telegram
 Channel        Channel                       Channel
                   │
                   ▼
                  ELITE
              Telegram Channel
                   │
                   ▼
      [I] OUTCOME SERVICE (ELITE ONLY)
            outcome_service.py
  (WIN/LOSE/MISSED buttons tied to SIGNAL_ID)
  - buttons become active AFTER expiry
  - vote window: 5 minutes
  - LOCK: first vote wins
  - buttons disappear after vote
  - updates per-signal aggregated stats
                   │ stores
                   ▼
      /opt/binarybot/outcomes/outcomes.jsonl

All significant events (engine + fsm + distribution + outcomes) →
      [J] OBSERVABILITY LOGGER
           observability_logger.py
        (append-only JSONL + admin proof logs)
                   │
                   ▼
        /opt/binarybot/observability/*.jsonl
                   │
                   ▼
          [K] ANALYTICS ENGINE
            analytics_engine.py
 (research + performance metrics + symbol rankings)
                   │
                   ▼
            ADMIN CONTROL PANEL
              bot_service.py
 (status, config changes, docs viewer, research reports)

Module Overview (canonical responsibilities)

- Candle Adapter: normalize market data format.
- Params Loader: load/validate algo_params.json.
- Signal Engine: orchestrator scheduling WIDE_SCAN/FOCUS + dedup + emit events.
- Strategy Core: compute PRE/CONFIRM/OPEN_NOW decisions (pure logic).
- FSM Runtime: enforce lifecycle/invariants and persist focus_state.json.
- Distribution Router: route to tiers, enforce limits/silent/reset, persist dist_state.json.
- Telegram Publisher: Telegram API send/edit abstraction.
- Outcome Service (ELITE): voting workflow + outcome storage + per-signal stats.
- Observability Logger: structured JSONL logs + admin proofs.
- Analytics Engine: performance/research layer and reporting to admin.

## 2) MODULES (CE FACE FIECARE)

### 2.1 strategy_v2.py  (PURE LOGIC)
Responsabil:
- Implementarea completă a logicii strategiei (buffer, expiry, gates, scoring, PRE/CONFIRM/OPEN_NOW decision).

Interzis:
- Telegram send
- file I/O
- tier routing
- FSM persistence

Input:
- candles M1/M5 (newest-first)
- params dict (din algo_params.json)
- buffer_mode

Output:
- Decision(kind=PRE/CONFIRM/OPEN_NOW/REJECT/NO_SIGNAL, score, buffer, expiry, gates, debug)

Documente care îl guvernează:
- ALGO_SPEC.md
- RISK_MODEL.md
- PARAMS_REFERENCE.md
- SYSTEM_INVARIANTS.md

---

### 2.2 signal_engine.py  (ORCHESTRATOR / ENGINE LOOP)
Responsabil:
- WIDE_SCAN loop: iterare simboluri active -> detectare PRE candidates
- FOCUS loop: prioritizare watchlist -> CONFIRM/OPEN_NOW
- Cheamă `strategy_v2.decide_*`
- Cheamă FSM transitions (watchlist/live/cooldown)
- Emite „Signal Events” către router (PRE/CONFIRM/OPEN_NOW)
- Aplică dedup global (per symbol + candle + stage)

Documente care îl guvernează:
- FSM_SPEC.md
- TELEGRAM_UX.md (format + anti-spam)
- OBSERVABILITY_LOGGING_SPEC.md (evenimente)
- SIGNAL_DISTRIBUTION_SPEC.md (NU decide tier, doar emite event)
- CHECKLIST.md (control patch)

---

### 2.3 bot_service.py  (TELEGRAM UX + ADMIN PANEL)
Responsabil:
- /start, /buffer, /open, set symbols UI
- Admin Control Panel (butoane + help pages)
- Trimite confirmări în topicul special (audit)
- Afișează starea (buffer, watchlist, counters tiers, reset time)
- “Docs viewer”: trimite fișier .md (fără spam, 1 click)

Documente care îl guvernează:
- TELEGRAM_UX.md
- CHANNEL_CONFIG_SPEC.md (IDs, vizibilitate, audit)
- GOVERNANCE_AND_CHANGE_CONTROL.md (cine poate schimba ce)
- OBSERVABILITY_LOGGING_SPEC.md

---

### 2.4 distribution_router.py  (TIER DISTRIBUTION LAYER)
Responsabil:
- Primește event (stage + payload + SIGNAL_ID)
- Decide *unde* se postează (FREE/BASIC/PRO/ELITE)
- Aplică silent mode + daily limits
- Persistă `dist_state.json` (counters + tier_state + last_reset)
- Reset zilnic 08:10 Europe/London (DST safe)
- Dedup per (tier, SIGNAL_ID, stage)

Documente care îl guvernează:
- SIGNAL_DISTRIBUTION_SPEC.md
- CHANNEL_CONFIG_SPEC.md
- SYSTEM_INVARIANTS.md
- OBSERVABILITY_LOGGING_SPEC.md

---

### 2.5 observability_logger.py  (EVENTS / DEBUG / AUDIT)
Responsabil:
- Scrie JSONL (append-only)
- Emită admin logs în topic special (dovada schimbărilor + dovada distribuției)
- Normalizează fiecare eveniment într-un schema fixă:
  - engine_start/stop
  - fsm_transition
  - decision (REJECT/NO_SIGNAL)
  - signal_emitted (PRE/CONFIRM/OPEN_NOW)
  - tier_publish_result
  - user_outcome (WIN/LOSE/MISSED)
  - reset_event (tiers)

Documente care îl guvernează:
- OBSERVABILITY_LOGGING_SPEC.md
- CHECKLIST.md (validation)
- CHANGELOG.md (versioned behavior)

---

### 2.6 analytics_engine.py  (PERFORMANCE / RESEARCH / LEADERBOARDS)
Responsabil:
- Agregă datele (din observability logs + outcomes)
- Produce:
  - winrate/expectancy/funnel
  - focus history: câte intră în focus, câte dau OPEN_NOW
  - symbol rankings (profitability proxy)
  - user stats per ID (doar Elite, private)
  - admin dashboards (global)

Documente care îl guvernează:
- PERFORMANCE_ANALYTICS_SPEC.md
- TRADING_RESEARCH_SPEC.md (dacă îl folosim separat)
- SYSTEM_INVARIANTS.md
- GOVERNANCE_AND_CHANGE_CONTROL.md

---

### 2.7 fsm_runtime.py  (FSM IMPLEMENTATION)
Responsabil:
- Definește states: IDLE/WATCHLIST/LIVE_SENT/COOLDOWN
- Definește global modes: WIDE_SCAN / FOCUS
- Tranziții exacte + invariants enforcement
- Persistă focus_state.json (survive restart)

Documente care îl guvernează:
- FSM_SPEC.md
- SYSTEM_INVARIANTS.md
- TELEGRAM_UX.md (anti-spam dedup keys)

---

### 2.8 storage.py  (SAFE PERSISTENCE)
Responsabil:
- atomic read/write JSON
- locks (evităm corupție la restart)
- helpers: load/save for settings, focus_state, active_symbols, dist_state

Documente care îl guvernează:
- OBSERVABILITY_LOGGING_SPEC.md (consistency)
- SIGNAL_DISTRIBUTION_SPEC.md (persistence MUST)
- CHECKLIST.md (backup rules)

---

## 3) DOC → CODE MAPPING (CANONICAL)

### 3.1 ALGO_SPEC.md
Conține:
- definiția strategiei, gates, scoring, buffer/expiry logic

Implementare:
- strategy_v2.py (decide_v1 / decide_* canonical)
- config/algo_params.json (toți parametrii; fără hardcode)
- signal_engine.py doar „apelează” și respectă decizia

---

### 3.2 FSM_SPEC.md
Conține:
- states, transitions, invariants focus max 2, cooldown, no live in wide scan, dedup per candle

Implementare:
- fsm_runtime.py (apply_transition + enforce_invariants)
- focus_state.json (watchlist/pending_open/cooldown + timestamps)
- signal_engine.py (nu „inventează” stări, doar cere transition)

---

### 3.3 TELEGRAM_UX.md
Conține:
- structura mesajelor, topics, anti-spam, comenzi

Implementare:
- bot_service.py (commands + admin UX)
- distribution_router.py (publish to channels)
- observability_logger.py (admin proof logs)

---

### 3.4 RISK_MODEL.md
Conține:
- SR gate, spike filters, feasibility, cooldown philosophy

Implementare:
- strategy_v2.py (hard gates + reject reasons)
- fsm_runtime.py (cooldown enforcement)
- analytics_engine.py (risk escalation detection)

---

### 3.5 SIGNAL_DISTRIBUTION_SPEC.md
Conține:
- tier limits, silent mode, only OPEN_NOW counts, but silent blocks all stages, reset at 08:10 London, same SIGNAL_ID across stages

Implementare:
- distribution_router.py
- dist_state.json (persist)
- observability_logger.py (tier_publish_result events)

---

### 3.6 CHANNEL_CONFIG_SPEC.md
Conține:
- FREE/BASIC/PRO/ELITE channel IDs, limits, admin visibility, missing IDs => DISABLED tier

Implementare:
- config/channel_config.json OR env vars (dar persist recomandat)
- bot_service.py (admin view)
- distribution_router.py (mapping validation)
- observability_logger.py (critical event if missing)

---

### 3.7 OBSERVABILITY_LOGGING_SPEC.md
Conține:
- schema log events, dovadă pentru schimbări și pentru setări, audit trails

Implementare:
- observability_logger.py
- log directory: /opt/binarybot/observability/*.jsonl
- admin topic “proof logs”: confirmă schimbări buffer/symbols/tier state/reset

---

### 3.8 PERFORMANCE_ANALYTICS_SPEC.md
Conține:
- WR/expectancy/funnel/rejection rate/session breakdown/drift detection

Implementare:
- analytics_engine.py (agregări)
- observability logs (source of truth)
- bot_service.py (admin commands: /stats, /symbol_rank, /focus_history)

---

### 3.9 PARAMS_REFERENCE.md
Conține:
- contract complet pentru `config/algo_params.json` (chei, tipuri, default-uri)

Implementare:
- storage.py validator (schema check)
- strategy_v2.py (param lookup)
- signal_engine.py (nu hardcode thresholds)

---

### 3.10 GOVERNANCE_AND_CHANGE_CONTROL.md
Conține:
- cine poate schimba, ce se loghează, cum se face patch

Implementare:
- bot_service.py (admin-only actions)
- observability_logger.py (change events)
- CHECKLIST.md workflow enforcement

---

### 3.11 SYSTEM_INVARIANTS.md
Conține:
- reguli NON-NEGOTIABLE (max 2 focus, dedup, cooldown, silent tiers)

Implementare:
- fsm_runtime.py (assert invariants)
- distribution_router.py (assert invariants)
- signal_engine.py (guardrails)
- analytics_engine.py (alerts dacă invariants se rup)

---

### 3.12 FORMAL_SPEC.md
Conține:
- definire formală (inputs/outputs, state schemas, event schemas)

Implementare:
- shared schemas în cod (dataclasses / pydantic-style dacă alegem)
- unit tests (test_plan)

---

### 3.13 CHECKLIST.md
Conține:
- BEFORE/DURING/AFTER patch protocol

Implementare:
- Nu e “cod”, dar devine:
  - scripts/verify_json.sh
  - scripts/backup.sh
  - scripts/restart_service.sh
  - plus un “/health” admin command pentru status

---

### 3.14 CHANGELOG.md
Conține:
- fiecare schimbare mapată la versiune + motiv + impact

Implementare:
- update manual + referințe din observability logs (deploy marker event)

---

## 4) “14 MODULE INTERNE” (STANDARDIZARE)

Acestea sunt „piese” separate ca să nu se amestece logica.

1) Strategy Core (strategy_v2.py)
2) Params Loader/Validator (storage.py + PARAMS_REFERENCE)
3) Candle Source Adapter (twelvedata adapter)
4) Signal Decision Wrapper (normalize Decision -> SignalEvent)
5) FSM Runtime (fsm_runtime.py)
6) Wide Scan Scheduler (engine loop)
7) Focus Scheduler (engine loop)
8) Dedup Store (last_pre/confirm/open per symbol+candle)
9) Distribution Router (tiers)
10) Tier State Store (dist_state.json)
11) Telegram Publisher (sendMessage abstraction)
12) Observability Logger (JSONL + admin proofs)
13) Analytics Engine (aggregator + reports)
14) Admin UX Layer (bot_service.py: panel, docs viewer, outcomes UI)

---

## 5) ADMIN PANEL (UPDATED WITH YOUR RULES)

### 5.1 Core buttons
- Set Symbols
  - deschide lista completă (toggle active_symbols.json)
  - wide scan scanează TOT ce e selectat
- Buffer Mode
  - SMALL / MEDIUM / LARGE (settings.json)
  - trimite “proof message” în topicul special
- Status
  - arată: mode (WIDE/FOCUS), watchlist, cooldown symbols, counters tiers, reset time

### 5.2 Research / Analytics buttons (NU payout, ci “selection frequency proxy”)
- Focus History (pe săptămâni/luni)
  - câte simboluri au intrat în focus
  - câte au dat OPEN_NOW
  - conversion rate: PRE→OPEN_NOW
- Symbol Ranking
  - top symbols by OPEN_NOW count
  - rejection reasons breakdown
- Session Breakdown
  - ASIA/LONDON/NY performance

### 5.3 Outcome marking (Elite-only, varianta ta finală)
- Pentru fiecare OPEN_NOW în ELITE:
  - Win / Lose / Missed (poll-style buttons)
  - RULE: One outcome per user per SIGNAL_ID (LOCK: first write wins)
  - Buttons disappear after vote (edit message markup)
  - Vote window:
    - apare după expiry (ideal) sau imediat dar user-ul e instruit să voteze după închidere
    - expiră complet după max 15 minute de la OPEN_NOW (sau după expiry + 5 min)
  - Public per-signal stats:
    - %Win / %Lose / %Missed (visible în canal)
  - Private per-user stats:
    - fiecare user își vede doar statisticile lui (DM bot)

Admin-only:
- Admin vede global (toate voturile agregate)
- Membrii văd doar:
  - rezultatul lor (confirmare)
  - stats agregate per semnal (fără IDs)

---

## 6) “PROOF MESSAGES” (CERINȚA TA)

Orice schimbare de control (buffer / symbols / tier reset / tier silent) trebuie să producă:
- un mesaj în topicul special (admin logs / system proofs)
cu:
- timestamp
- cine a schimbat (admin user id)
- ce s-a schimbat (before/after)
- version (algo_version)

---

## 7) IMPLEMENTATION CHECKPOINTS (CE TREBUIE SĂ EXISTE ÎN COD)

Mandatory state files:
- settings.json
- active_symbols.json
- focus_state.json
- dist_state.json

Mandatory event logs:
- observability/*.jsonl

Mandatory dedup keys:
- symbol + candle_timestamp + stage (engine)
- tier + SIGNAL_ID + stage (distribution)

Mandatory reset:
- 08:10 Europe/London (DST safe)

---

End of ARCHITECTURE_CODE_MAPPING.md