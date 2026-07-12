# FOCUS_LEARNING_SPEC — Focus History + Profitability Learning Layer
Version: 1.0.0  
Status: Canonical  
Scope: Observability + analytics for Focus selection & symbol profitability  
Linked Docs: ALGO_SPEC.md, FSM_SPEC.md, TELEGRAM_UX.md, OBSERVABILITY_LOGGING_SPEC.md, PERFORMANCE_ANALYTICS_SPEC.md

---

## 1. PURPOSE

This system is a **learning function** for both:
- the engine (future parameter tuning)
- the operator (decision support)

It must answer, with proof:
- Which symbols generate the most **OPEN_NOW**
- Which symbols waste time (PRE/CONFIRM but rarely OPEN_NOW)
- Which symbols are unstable (spike/gates/cooldowns frequent)
- Which buffer modes produce best conversion (PRE→OPEN_NOW)

This is not a daily log.  
This is a **long-term historical dataset** over weeks/months.

---

## 2. CORE CONCEPTS

### 2.1 “Success”
A setup is considered **successful for analytics** only if it produces:
- `OPEN_NOW` (sent)

Optional later extension:
- if you mark result WIN/LOSS manually → true profit analytics
But for now: success = OPEN_NOW.

### 2.2 Signal identity consistency
All stages share the same:
- `SIGNAL_ID`

Stages:
- PRE
- CONFIRM
- OPEN_NOW

---

## 3. DATA MODEL

### 3.1 Event stream (append-only)
We store **every lifecycle event** as a JSON line (JSONL).

File:
`/opt/binarybot/logs/focus_history.jsonl`

Rules:
- append-only
- never rewrite history
- survives restart
- never spam duplicates

### 3.2 Aggregates (computed, rewrite ok)
Daily + rolling stats computed from events.

Folder:
`/opt/binarybot/state/`

Files:
- `focus_stats_daily.json` (keyed by day)
- `focus_stats_rolling.json` (rolling windows: 7d / 30d / all-time)
- `focus_symbol_leaderboard.json`

---

## 4. EVENT TYPES (MANDATORY)

Events are emitted by the engine during runtime.

### 4.1 Focus lifecycle
- `FOCUS_ENTER`
- `FOCUS_EXIT`

### 4.2 Signal lifecycle
- `PRE_SENT`
- `CONFIRM_SENT`
- `OPEN_NOW_SENT`

### 4.3 Gate / rejection reasons (learning why we lose opportunities)
- `REJECT_SPIKE`
- `REJECT_SR_SPACE`
- `REJECT_FEASIBILITY`
- `REJECT_SCORE`
- `COOLDOWN_START`
- `COOLDOWN_END`

### 4.4 Admin actions (operator behavior matters)
- `ADMIN_SET_SYMBOLS`
- `ADMIN_SET_BUFFER_MODE`
- `ADMIN_RELEASE_FOCUS`
- `DAILY_RESET`

---

## 5. EVENT SCHEMA (JSONL)

Each line is a JSON object.

Required fields:

- `ts_utc` : ISO8601 UTC timestamp
- `event` : one of event types above
- `symbol` : e.g. "EUR/USD"
- `signal_id` : string or null (must exist for PRE/CONFIRM/OPEN_NOW)
- `buffer_mode` : SMALL/MEDIUM/LARGE
- `score` : numeric or null
- `expiry_sec` : int or null
- `buffer_value` : numeric or null (pips for forex / points for crypto)
- `buffer_extra` : e.g. percent for crypto, null otherwise
- `focus_slot` : 1 or 2 or null
- `session` : ASIA/LONDON/NY/LATE
- `reason` : short reason code (for reject/exit)
- `meta` : object (free fields, must be small)

Example:

{
  "ts_utc": "2026-03-04T08:14:22Z",
  "event": "OPEN_NOW_SENT",
  "symbol": "EUR/USD",
  "signal_id": "EURUSD_M1_20260304_004",
  "buffer_mode": "MEDIUM",
  "score": 86,
  "expiry_sec": 300,
  "buffer_value": 5.8,
  "buffer_extra": null,
  "focus_slot": 1,
  "session": "LONDON",
  "reason": null,
  "meta": {"algo_version":"1.0.0"}
}

---

## 6. INVARIANTS

1) No duplicates:
`event + symbol + signal_id + candle_key` must be unique.

2) If tier is silent (distribution layer):
- the learning layer still logs internal events
- but it must record `delivered=false` in meta if not published

3) If restart happens:
- event stream continues
- deduplication prevents replay spam

---

## 7. REQUIRED ANALYTICS OUTPUTS

### 7.1 Symbol profitability proxy (conversion)
We compute conversion metrics:

For each symbol:
- `PRE_count`
- `CONFIRM_count`
- `OPEN_count`
- `PRE_to_OPEN_rate = OPEN / PRE`
- `CONFIRM_to_OPEN_rate = OPEN / CONFIRM`
- `reject_rate` by reason
- `cooldown_rate`

### 7.2 Most profitable symbols
“Profitability” for now means:
- highest OPEN count
- highest PRE→OPEN conversion
- lowest reject/spike frequency

Leaderboards:
- Top 10 by OPEN volume
- Top 10 by conversion
- Worst 10 by wasted PRE (high PRE, low OPEN)

### 7.3 Buffer mode effectiveness
For each buffer mode:
- PRE count
- OPEN count
- Conversion
- Average expiry
- Reject reasons distribution

### 7.4 Session behavior
By session bucket:
- ASIA / LONDON / NY / LATE
Compute:
- OPEN frequency
- conversion
- avg expiry
- spikes

---

## 8. ADMIN UX (TELEGRAM CONTROL PANEL)

Admin button:
`📊 Focus Learning`

When opened:
1) Summary (today + 7d + 30d + all-time)
2) Top symbols (OPEN + conversion)
3) Worst symbols (wasted PRE)
4) Buffer mode stats
5) Session stats
6) Export options:
   - “Export last 7 days JSONL”
   - “Export all-time summary JSON”

All views include:
- current algo_version
- params_hash (optional)

---

## 9. EXPORT / ARCHIVE POLICY

Because history can grow:

- Keep JSONL as primary raw truth
- Rotate monthly:
  `/opt/binarybot/logs/archive/focus_history_YYYY_MM.jsonl`

Never delete archives automatically.

---

## 10. RESET POLICY

Daily reset is for tier counters only.  
Learning layer **does not reset**.

However it logs:
- `DAILY_RESET` event at `08:10 Europe/London`

---

## 11. IMPLEMENTATION NOTES (NON-NEGOTIABLE)

- Use JSONL for raw events (append-only)
- Aggregates are computed safely from raw stream
- Must never block trading loop (async write or buffered)
- If logging fails, engine continues (fail-open)
- Logging must not expose tokens or secrets

---

End of FOCUS_LEARNING_SPEC.md