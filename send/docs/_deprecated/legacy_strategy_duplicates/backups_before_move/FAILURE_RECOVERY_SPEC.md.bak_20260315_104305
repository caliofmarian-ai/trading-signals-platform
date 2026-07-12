# FAILURE_RECOVERY_SPEC.md
BinaryBot — Failure Recovery Specification
Version: 1.0.0
Status: Canonical

Linked Docs:
- ARCHITECTURE_CODE_MAPPING.md
- EVENT_SCHEMA_SPEC.md
- RUNTIME_EXECUTION_TIMELINE.md
- OBSERVABILITY_LOGGING_SPEC.md
- SIGNAL_DISTRIBUTION_SPEC.md
- FSM_SPEC.md
- TELEGRAM_UX.md
- SYSTEM_INVARIANTS.md

---

# 1. PURPOSE

Acest document definește comportamentul BinaryBot în situații de eroare sau întrerupere a serviciului.

Scopul este să garanteze:

- **fără semnale duplicate**
- **fără pierderea stării FSM**
- **fără resetarea accidentală a limitelor de tier**
- **fără pierderea datelor pentru analytics**
- **restart sigur al motorului**

BinaryBot trebuie să poată:

- opri
- reporni
- recupera starea

fără a compromite integritatea sistemului.

---

# 2. FAILURE TYPES

BinaryBot tratează următoarele categorii de eșec.

1. Engine crash
2. Server restart
3. Telegram API failure
4. Market Data API failure
5. File corruption
6. Network interruption
7. Partial message publish
8. Admin configuration errors

Fiecare caz are un mecanism clar de recuperare.

---

# 3. ENGINE CRASH

## Scenario

Procesul Python se oprește brusc.

Exemple:

- Out of memory
- Unhandled exception
- Kill signal
- Container restart

---

## Recovery Method

La repornire, BinaryBot trebuie să încarce starea completă din fișiere persistente.

Fișiere critice:

/opt/binarybot/settings.json  
/opt/binarybot/active_symbols.json  
/opt/binarybot/focus_state.json  
/opt/binarybot/dist_state.json  

Aceste fișiere trebuie să fie:

atomic write  
JSON valid  

---

## Restart Behavior

La restart:

1. engine_start event
2. focus_state.json este reîncărcat
3. dist_state.json este reîncărcat
4. counters NU se resetează
5. cooldown state rămâne activ

---

# 4. DUPLICATE SIGNAL PREVENTION

Pentru a preveni duplicate signals după restart.

BinaryBot utilizează două nivele de deduplicare.

---

## Engine Dedup

Cheie:

symbol + candle_timestamp + stage

Aceasta previne:

PRE duplicate  
CONFIRM duplicate  
OPEN_NOW duplicate

---

## Distribution Dedup

Cheie:

tier + signal_id + stage

Aceasta previne:

mesaje duplicate către același canal.

---

# 5. TELEGRAM API FAILURE

## Scenario

Telegram API nu răspunde.

Exemple:

timeout  
rate limit  
network error  

---

## Recovery Strategy

La publish:

1. Router încearcă transmiterea
2. Dacă eșuează:

publish_decision = FAILED

Se scrie eveniment:

tier_publish

---

## Retry Policy

Retries limitate:

max 3 încercări

Delay:

1 sec  
3 sec  
5 sec  

Dacă toate eșuează:

evenimentul rămâne FAILED.

Nu se încearcă infinit.

---

# 6. PARTIAL DISTRIBUTION FAILURE

## Scenario

Mesaj trimis la unele tiers dar nu la toate.

Exemplu:

FREE succes  
PRO eșec  

---

## Recovery

Router tratează fiecare tier independent.

FREE publish nu influențează PRO.

Counters cresc doar dacă:

stage = OPEN_NOW  
publish_decision = PUBLISHED

---

# 7. MARKET DATA FAILURE

## Scenario

API market data indisponibil.

Exemplu:

TwelveData outage.

---

## Recovery Behavior

Engine intră în:

SAFE MODE

Acțiuni:

- nu generează semnale noi
- continuă loop
- încearcă reconectare

Observability event:

error

severity = WARN

---

# 8. NETWORK INTERRUPTION

## Scenario

Server pierde conexiunea internet.

---

## Behavior

Engine continuă loop dar:

- nu poate primi candles
- nu poate publica Telegram

Evenimentele sunt logate:

error

După reconectare:

engine reia funcționarea normală.

---

# 9. FILE CORRUPTION

## Scenario

Un fișier JSON este corupt.

Exemplu:

focus_state.json invalid.

---

## Recovery

Storage layer încearcă:

1. reload
2. fallback backup

Backup recomandat:

focus_state.json.bak

Dacă recovery eșuează:

engine refuză start.

Se emite:

CRITICAL error event.

---

# 10. DAILY RESET SAFETY

Tier reset rule:

08:10 Europe/London

Pentru a evita reseturi multiple:

Router verifică:

last_reset_date

Stocat în:

dist_state.json

Reset este:

idempotent.

---

# 11. OBSERVABILITY GUARANTEE

Toate evenimentele sunt:

append-only

Fișiere:

/opt/binarybot/observability/engine_events.jsonl  
/opt/binarybot/observability/distribution_events.jsonl  
/opt/binarybot/observability/admin_proofs.jsonl  

Nu se șterg.

Doar rotație periodică.

---

# 12. SAFE RESTART PROCEDURE

Restart corect:

1. stop engine
2. persist state
3. restart service
4. reload configs
5. emit engine_start

Engine nu trebuie să trimită semnale vechi.

---

# 13. INVARIANTS AFTER RECOVERY

După restart trebuie să rămână adevărat:

- max 2 focus symbols
- cooldown symbols active
- tier counters corecte
- dedup keys respectate
- signal lifecycle intact

---

# 14. FAILURE EVENT LOGGING

Pentru fiecare incident se loghează:

event_type = error

Câmpuri:

severity  
error_type  
message  
context  

Severity levels:

INFO  
WARN  
ERROR  
CRITICAL

---

# 15. SYSTEM GUARANTEE

Dacă acest document este respectat:

BinaryBot poate:

- supraviețui crash-urilor
- preveni duplicate signals
- menține integritatea FSM
- păstra counters corecți
- continua analytics fără pierderi

Sistemul devine **restart-safe și production-ready**.

---

End of FAILURE_RECOVERY_SPEC.md