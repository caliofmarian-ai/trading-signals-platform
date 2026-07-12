# RUNTIME_EXECUTION_TIMELINE

Status: Satellite / Non-Canonical Reference
Canonical Position: Supporting document only; does not define active canonical truth.
Primary Active Canon: Refer to active canonical documents under /opt/binarybot/docs/canonical/active/

---

# RUNTIME_EXECUTION_TIMELINE.md
BinaryBot — Runtime Execution Timeline
Version: 1.0.0
Status: Canonical

Linked Docs:
- EVENT_SCHEMA_SPEC_v2.0.0.md
- ARCHITECTURE_CODE_MAPPING.md
- FSM_DECISION_ENGINE_SPEC_v1.0.0.md
- SIGNAL_DISTRIBUTION_SPEC_v2.0.0.md
- TELEGRAM_UX_v2.0.0.md
- PERFORMANCE_ANALYTICS_SPEC_v2.0.0.md

---

# 1. PURPOSE

Acest document descrie comportamentul exact al BinaryBot în runtime.

El explică:

- ordinea execuției engine-ului
- fluxul complet al semnalelor
- evenimentele generate în fiecare etapă
- interacțiunea dintre module
- modul în care sistemul poate fi analizat sau reprodus din loguri

Runtime-ul BinaryBot este:

event-driven  
loop-based  
state-aware  

și produce evenimente conforme cu:

EVENT_SCHEMA_SPEC_v2.0.0.md

---

# 2. ENGINE START SEQUENCE

Pornirea sistemului.

---

## Step 1 — Process Start

BinaryBot este lansat de regulă prin:

systemd  
docker container  
manual python process  

Procesul pornește:

python binarybot

Modulele inițializate:

- storage layer
- FSM runtime
- distribution router
- observability logger
- analytics hooks

---

## Step 2 — Persistent State Loading

BinaryBot încarcă toate stările persistente.

Files:

/opt/binarybot/settings.json  
/opt/binarybot/active_symbols.json  
/opt/binarybot/focus_state.json  
/opt/binarybot/dist_state.json  
/opt/binarybot/config/algo_params.json  
/opt/binarybot/config/channel_config.json  

Validare:

storage.py

Verificări:

- schema validă
- lipsă câmpuri
- corupție JSON
- consistență state

---

## Step 3 — Observability Event

Se emite primul eveniment.

event_type = engine_start

Acest eveniment conține:

engine_mode  
symbols_loaded  
buffer_mode  
reset_time_london  

Evenimentul este scris în:

/opt/binarybot/observability/engine_events.jsonl

---

## Step 4 — Engine Loop Start

Engine-ul pornește bucla principală.

Modul responsabil:

signal_engine.py

Interval tipic:

1 secundă

Pseudo-logic:

while engine_running:

    load active symbols
    determine engine mode
    fetch candles
    evaluate strategy
    process FSM
    emit signal events
    route distribution
    sleep(loop_interval)

---

# 3. SCHEDULER ARCHITECTURE

Engine-ul rulează cu două bucle logice active:

- WIDE_SCAN loop
- FOCUS_SCAN loop

Acestea nu se exclud reciproc.

Model canonic:

- WIDE_SCAN rămâne activ permanent
- FOCUS_SCAN rulează în paralel când există simboluri în watchlist
- FOCUS_SCAN este strat de prioritate, nu înlocuitor complet pentru WIDE_SCAN

Capacitate focus:

- maxim 2 simboluri simultan în focus/watchlist

Buget API / runtime:

- aproximativ 70% din atenție/resursă merge către focus
- aproximativ 30% rămâne rezervat pentru wide scan
- dacă sunt 2 simboluri în focus, bugetul focus se împarte între ele conform priorității

---

# 4. WIDE SCAN LOOP

Scop:

- scanarea tuturor simbolurilor active/selectate
- descoperirea candidaților PRE
- prevenirea starvation-ului simbolurilor non-focus
- menținerea acoperirii pieței

Simboluri sursă:

/opt/binarybot/active_symbols.json

Flux per simbol:

1. încărcare date candle
2. apel strategy_v2
3. calcul scor / gates / buffer / expiry
4. rezultat posibil:
   - NO_SIGNAL
   - REJECT
   - PRE candidate

Dacă apare PRE:

- FSM poate face tranziția:
  IDLE → WATCHLIST
- simbolul poate primi prioritate de focus
- WIDE_SCAN nu se oprește global

Observație:

WIDE_SCAN nu produce direct OPEN_NOW pentru simboluri aflate în afara contextului valid de focus/watchlist.

---

# 5. FOCUS SCAN LOOP

FOCUS_SCAN devine activ când watchlist-ul nu este gol.

Scop:

- monitorizare live mai intensă
- validare pentru CONFIRM
- decizie finală pentru OPEN_NOW
- rafinare a timing-ului real de intrare

Sursă simboluri:

/opt/binarybot/focus_state.json

Reguli:

- doar simbolurile aflate în WATCHLIST / focus context sunt urmărite aici
- maxim 2 simboluri în același timp
- acest loop primește majoritatea resursei runtime/API

Flux focus:

1. recalculează scorul în condiții live
2. verifică persistența setup-ului
3. verifică buffer reachability
4. verifică expiry feasibility
5. decide:
   - rămâne în watchlist
   - emite CONFIRM
   - emite OPEN_NOW
   - iese din focus

Regulă critică:

OPEN_NOW este permis doar pentru simboluri aflate în context valid de focus/watchlist.

---

# 6. FOCUS ROTATION / RELEASE

Focus nu este blocaj permanent.

Un simbol iese din focus dacă:

- scorul scade sub PRE
- setup-ul se invalidează
- fereastra de validitate expiră
- OPEN_NOW lifecycle se finalizează
- cooldown impune eliberarea slotului
- un candidat mai puternic îl înlocuiește conform politicii canonice

Consecință:

- slotul focus eliberat devine disponibil pentru alt candidat
- rotația între simboluri este permisă
- WIDE_SCAN continuă să descopere noi oportunități în paralel

Focus replacement:

- dacă watchlist-ul este plin
- și apare un candidat superior
- sistemul poate face focus_replace
- fără a depăși limita de 2 simboluri

---

# 7. SIGNAL PROGRESSION UNDER CONCURRENT SCHEDULER

Model canonic:

WIDE_SCAN
→ detectează PRE candidate
→ FSM: IDLE → WATCHLIST
→ simbolul intră în focus context
→ FOCUS_SCAN monitorizează live
→ CONFIRM
→ OPEN_NOW
→ LIVE_SENT / COOLDOWN
→ focus slot released

Clarificare:

- PRE este descoperit în wide coverage
- CONFIRM și OPEN_NOW apar în focus context
- wide coverage continuă și în timpul focus monitoring

---

# 8. OPEN_NOW SIGNAL

Dacă strategia produce:

OPEN_NOW

condițiile:

want_open_now = true  
score ≥ threshold  
dedup = ok  

---

## FSM Transition

WATCHLIST → LIVE_SENT

Persistat în:

focus_state.json

---

## Signal Event

Se emite:

signal_event

stage = OPEN_NOW

Payload:

symbol  
direction  
buffer  
expiry  
confidence  
signal_id  

---

# 9. DISTRIBUTION ROUTER

Modul:

distribution_router.py

Primește:

SignalEvent

---

## Router Process

Router verifică:

tier state  
tier limits  
silent mode  
tier dedup  

Stare persistată:

/opt/binarybot/dist_state.json

---

## Tiers

FREE  
BASIC  
PRO  
ELITE  

---

## Publish Event

Se generează:

tier_publish

Log:

/opt/binarybot/observability/distribution_events.jsonl

---

# 10. TELEGRAM MESSAGE SEND

Modul:

telegram_publisher

Telegram API:

sendMessage  
editMessage  

Dacă succes:

message_id este salvat.

Dacă eșec:

error event.

---

# 11. ELITE OUTCOME SYSTEM

Activ doar pentru:

ELITE channel.

După OPEN_NOW.

Outcome service creează:

vote buttons.

Opțiuni:

WIN  
LOSE  
MISSED  

---

## Vote Window

Vote start:

trade_expiry

Vote end:

expiry + 5 minutes

Exemplu:

OPEN_NOW = 10:00  
expiry = 5m  

vote_start = 10:05  
vote_end = 10:10  

---

## Outcome Storage

File:

/opt/binarybot/outcomes/outcomes.jsonl

Eveniment:

user_outcome

---

# 12. COOLDOWN PHASE

După OPEN_NOW:

FSM transition:

LIVE_SENT → COOLDOWN

Previne:

semnale repetate pe același simbol.

Exemplu:

cooldown = 3 candles

Stare salvată în:

focus_state.json

---

# 13. DAILY TIER RESET

Ora reset:

08:10 Europe/London

Eveniment:

tier_reset

Router resetează:

FREE counter  
BASIC counter  
PRO counter  

ELITE rămâne nelimitat.

---

# 14. ANALYTICS PIPELINE

Analytics engine citește:

/opt/binarybot/observability/*.jsonl  
/opt/binarybot/outcomes/outcomes.jsonl  

Calculează:

win rate  
expectancy  
conversion funnel  
symbol ranking  
focus efficiency  

Output:

/opt/binarybot/analytics/aggregates.json

---

# 15. ADMIN INTERACTION

Admin panel:

bot_service.py

Acțiuni:

set buffer  
set symbols  
view stats  
view logs  

Orice schimbare produce:

admin_change

Log:

/opt/binarybot/observability/admin_proofs.jsonl

---

# 16. FULL SIGNAL LIFECYCLE

Exemplu complet:

engine_start  
decision(PRE)  
signal_event(PRE)  
fsm_transition(IDLE→WATCHLIST)

decision(CONFIRM)  
signal_event(CONFIRM)

decision(OPEN_NOW)  
fsm_transition(WATCHLIST→LIVE_SENT)  
signal_event(OPEN_NOW)

tier_publish(FREE)  
tier_publish(PRO)  
tier_publish(ELITE)

user_outcome(WIN)

fsm_transition(LIVE_SENT→COOLDOWN)

---

# 17. SYSTEM GUARANTEES

BinaryBot garantează:

- fără duplicate signals
- maxim 2 focus symbols
- respectarea limitelor tier
- lifecycle consistent
- logs append-only
- restart-safe persistence
- audit complet al deciziilor

---

End of RUNTIME_EXECUTION_TIMELINE.md


# Focus Lease and Decision Freeze Runtime Rules

## Focus Lease Runtime Rule

Runtime must treat focus residency as leased, not permanent.

Every focus symbol must be checked continuously for:

- active universe membership
- lease age
- lifecycle validity
- replacement pressure

If any required condition fails, the symbol must exit focus immediately.

## Runtime Active-Universe Eviction Rule

If a symbol disappears from active_symbols, runtime must evict it from watchlist/focus before allocating further focus resources to it.

No removed symbol may continue consuming focus budget.

## Runtime Lease Expiry Rule

If focus TTL expires:

- symbol exits focus
- focus_expire_reason is recorded
- watchlist is compacted
- freed capacity becomes available for other candidates

## Runtime Decision Freeze Rule

Runtime must not perform redundant full decision recomputation for the same opportunity every scheduler tick.

Instead runtime must distinguish:

- observation tick
- materially changed reevaluation tick

## Freeze Identity

The canonical operational identity of an opportunity must be formed from stable decision fields such as:

- symbol
- candle_ts
- direction
- stage / context

## Freeze Release Conditions

Freeze may be broken only by material change such as:

- new candle
- direction flip
- major score delta
- focus context change
- expiry feasibility shift
- canonical stage progression

## Runtime Goal

These two controls exist to achieve:

- stable focus rotation
- reduced redundant recomputation
- lower API waste
- clearer telemetry
- stronger PRE → CONFIRM → OPEN discipline

## Non-Canonical Usage Note

This document is retained as a supporting/satellite reference only. It must not be treated as active canonical truth. Where conflict exists, active canonical documents in /opt/binarybot/docs/canonical/active/ take precedence.
