# CANONICAL_CODE_ALIGNMENT_MATRIX_v1.0.0

Status: Satellite / Non-Canonical Reference
Canonical Position: Supporting document only; does not define active canonical truth.
Primary Active Canon: Refer to active canonical documents under /opt/binarybot/docs/canonical/active/

---

# CANONICAL CODE ALIGNMENT MATRIX

Version: 1.0.0  
Status: Canonical Alignment Audit  
Scope: Canonical Documentation vs Real Codebase Mapping  
Authoritative Source: /opt/binarybot code audit (STEP 106.1)

---

## 1. PURPOSE OF THIS DOCUMENT

Acest document definește **alinierea reală între documentele canonice ale arhitecturii BinaryBot și implementarea actuală din cod**.

Scopul documentului este:

- să identifice ce componente canonice există în cod
- să identifice ce componente lipsesc
- să identifice unde logica este amestecată
- să definească direcția corectă de refactorizare

Acest document NU modifică codul.

Acest document este **instrumentul de control al refactorizării arhitecturale**.

---

## 2. INPUT SOURCES

Acest document este construit pe baza:

CANONICAL DOCUMENTS

- canonical/active/ALGO_SPEC_v2.0.0.md
- canonical/active/SR_CORRIDOR_ENGINE_SPEC_v2.0.0.md
- canonical/active/SIGNAL_ENGINE_EXECUTION_SPEC_v2.0.0.md
- SIGNAL_TIME_MODEL_SPEC_v2.0.0.md
- canonical/active/FSM_DECISION_ENGINE_SPEC_v1.0.0.md
- canonical/active/DECISION_OBJECT_CANONICAL_SPEC_v1.0.0.md
- canonical/active/OBSERVABILITY_SPEC_v2.0.0.md
- STRATEGY_ENGINE_ARCHITECTURE_MAP_v1.0.0.md

și

REAL CODEBASE AUDIT

- STEP 106.1 — CODE_PHYSICAL_AUDIT

---

## 3. HIGH LEVEL ARCHITECTURE (CANONICAL)

Arhitectura canonică a motorului strategic este:

MARKET DATA ↓ MARKET MODEL ↓ SR CORRIDOR ENGINE ↓ TIME MODEL ↓ SCORING MODEL ↓ DECISION OBJECT ↓ DECISION FSM ↓ EXECUTION MODEL ↓ SIGNAL ENGINE ↓ TELEGRAM / DISTRIBUTION

---

## 4. REAL CODE STRUCTURE

Auditul codului arată următoarele module principale:

CORE ENGINE

core/strategy_v2.py core/signal_engine.py core/fsm_runtime.py core/buffer_selector.py core/symbol_selector.py

EXECUTION + RUNTIME

runtime/engine_loop.py runtime/system_boot.py runtime/market_client.py runtime/distribution_scheduler.py

OBSERVABILITY

core/observability_logger.py core/trade_temporal_telemetry.py metrics/metrics_collector.py journal/trade_journal.py

INTELLIGENCE

intelligence/research_engine.py intelligence/strategy_optimizer.py intelligence/signal_diagnostics.py intelligence/symbol_health.py

STATE STORAGE

state_store/state_store.py state_store/event_store.py snapshots/snapshot_manager.py

ADMIN CONTROL

core/admin_commands.py core/admin_router.py core/admin_ui.py

---

## 5. CANONICAL → CODE ALIGNMENT MATRIX

### 5.1 MARKET MODEL

Canonical responsibility:

- price speed estimation
- buffer distance
- volatility context
- structural context

Expected outputs:

price_speed buffer_distance trend_context volatility_state structure_context

REAL IMPLEMENTATION

core/strategy_v2.py core/candle_adapter.py core/buffer_selector.py

STATUS

PARTIAL

Problem:

Market model logic este amestecată direct în strategia principală.

---

### 5.2 SR CORRIDOR ENGINE

Canonical responsibility:

- support/resistance corridor detection
- corridor width
- corridor geometry
- breakout feasibility

Expected outputs:

corridor_width corridor_direction corridor_structure

REAL IMPLEMENTATION

core/strategy_v2.py core/buffer_selector.py

STATUS

PARTIAL

Problem:

Nu există un modul separat pentru corridor engine.

Logica este embedded în strategy_v2.

---

### 5.3 TIME MODEL

Canonical responsibility:

t_needed = D / V model_expiry model_time_reach_ratio corridor_time_pressure

REAL IMPLEMENTATION

core/strategy_v2.py core/trade_temporal_telemetry.py

STATUS

MIXED

Problem:

- expiry logic
- time feasibility
- signal timing

sunt amestecate.

---

### 5.4 SCORING MODEL

Canonical responsibility:

score_total score_components normalized_score

REAL IMPLEMENTATION

core/strategy_v2.py

STATUS

EMBEDDED

Problem:

Scoring model nu este modular.

---

### 5.5 DECISION OBJECT

Canonical responsibility:

Decizia matematică completă a strategiei.

Expected structure:

DecisionObject symbol direction price_speed buffer_distance model_expiry model_time_reach_ratio corridor_width score_total time_pressure

REAL IMPLEMENTATION

❌ NOT IMPLEMENTED

STATUS

MISSING

Acesta este cel mai mare gap între documente și cod.

---

### 5.6 DECISION FSM

Canonical responsibility:

Transformă decizia matematică în state de semnal.

States:

NO_SIGNAL REJECT PRE CONFIRM OPEN_NOW

REAL IMPLEMENTATION

core/fsm_runtime.py

STATUS

PARTIAL

Problem:

FSM primește date brute din strategie.

Nu primește DecisionObject.

---

### 5.7 EXECUTION MODEL

Canonical responsibility:

Calculul expiry final pentru:

CONFIRM OPEN_NOW

REAL IMPLEMENTATION

core/signal_engine.py

STATUS

PARTIAL

Problem:

Execution model este amestecat cu publishing.

---

### 5.8 SIGNAL ENGINE

Canonical responsibility:

- create signal
- publish signal
- route signal

REAL IMPLEMENTATION

core/signal_engine.py core/distribution_router.py core/telegram_publisher.py

STATUS

GOOD

Acest layer este relativ clar.

---

### 5.9 OBSERVABILITY

Canonical responsibility:

decision logs signal telemetry performance metrics strategy diagnostics

REAL IMPLEMENTATION

core/observability_logger.py metrics/metrics_collector.py journal/trade_journal.py core/trade_temporal_telemetry.py

STATUS

GOOD

Observability există și este destul de bine modularizat.

---

## 6. ARCHITECTURE MISALIGNMENTS

Principalele diferențe între canon și cod sunt:

1️⃣ DecisionObject nu există.

2️⃣ Strategy engine conține prea multă logică:

market model time model scoring model corridor logic

3️⃣ FSM nu operează pe obiect canonic.

4️⃣ Execution model este amestecat cu signal engine.

---

## 7. REQUIRED REFACTORING

Refactorizarea necesară este:

#### STEP 1

Introduce

DecisionObject

ca structură centrală.

---

#### STEP 2

Separă:

MarketModel TimeModel ScoringModel

din strategy_v2.

---

#### STEP 3

Strategy engine produce:

DecisionObject

nu semnal direct.

---

#### STEP 4

FSM operează pe:

DecisionObject

---

#### STEP 5

Execution model produce:

confirm_expiry open_now_expiry

---

#### STEP 6

Signal engine publică doar rezultatul.

---

## 8. FINAL CONCLUSION

Codul actual este:

FUNCTIONAL DAR ARCHITECTURAL MIXED

Documentația canonică definește o arhitectură mai clară.

Refactorizarea va introduce:

DecisionObject layer modular strategy engine clean FSM inputs separate execution model

Acest document este baza pentru:

CANONICAL_REFACTOR_PLAN_v1.0.0.md

care va defini pașii exacți de refactorizare.

---

END OF DOCUMENT

## Non-Canonical Usage Note

This document is retained as a supporting/satellite reference only. It must not be treated as active canonical truth. Where conflict exists, active canonical documents in /opt/binarybot/docs/canonical/active/ take precedence.
