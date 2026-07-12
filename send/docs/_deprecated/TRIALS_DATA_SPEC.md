# TRIALS_DATA_SPEC — Trial Capture (Manual Result via Telegram Command)
Version: 1.0.0
Status: Canonical
Linked: STATISTICAL_PROOF_LAYER.md, TELEGRAM_UX.md, OBSERVABILITY_LOGGING_SPEC.md, PERFORMANCE_ANALYTICS_SPEC.md

---

## 0. PURPOSE
Definește standardul unic prin care capturăm rezultatele (WIN/LOSS) pentru fiecare OPEN_NOW executat manual.

Fără acest standard:
- nu există statistici valide
- nu există dovadă de edge
- nu există audit / regresie / drift detection

---

## 1. DEFINITIONS
### 1.1 Trial
Un **trial** = un OPEN_NOW transmis de engine + confirmat ulterior ca WIN/LOSS de admin/user prin comandă Telegram.

### 1.2 Trial ID (canonical)
Fiecare trial are un ID determinist, construit din:
- `algo_version`
- `params_hash`
- `symbol`
- `open_candle_ts_utc` (timestamp-ul lumânării pe care s-a emis OPEN_NOW)
- `expiry_seconds`
- `side`

**trial_id format**
`{algo_version}|{params_hash8}|{symbol}|{open_ts}|{expiry_s}|{side}`

Exemplu:
`1.0.0|a1b2c3d4|EUR/USD|2026-03-03T12:34:00Z|180|BUY`

---

## 2. STORAGE (single source of truth)
### 2.1 Append-only log
Path:
`/opt/binarybot/data/trials.jsonl`

Regulă:
- fiecare linie = 1 JSON obiect
- append-only (nu rescriem trecutul)
- orice corecție se face printr-un event nou (REVISE)

### 2.2 Current index (fast lookup)
Path:
`/opt/binarybot/data/trials_index.json`

Conține map:
- trial_id -> pointer (line number / last status)
- last_open_now_per_symbol
- pending_trials list

### 2.3 Pending trial cache
Path:
`/opt/binarybot/data/pending_trials.json`

Conține doar ultimele OPEN_NOW care așteaptă rezultat.

Trebuie să supraviețuiască restart.

---

## 3. TRIAL RECORD — SCHEMA (JSON)
### 3.1 Required fields (must exist)
{
  "event_type": "OPEN_NOW" | "RESULT" | "REVISE" | "VOID",
  "trial_id": "string",

  "symbol": "EUR/USD",
  "side": "BUY" | "SELL",

  "open_ts_utc": "ISO8601Z",
  "expiry_seconds": 180,

  "confidence": 0-100,
  "buffer_mode": "SMALL" | "MEDIUM" | "LARGE",

  "algo_version": "1.0.0",
  "params_hash": "fullhashstring",

  "source": "engine" | "telegram_admin",
  "created_ts_utc": "ISO8601Z"
}

### 3.2 Optional fields (recommended)
{
  "buffer_pips": 3.4,
  "buffer_points": 12.5,
  "buffer_percent": 0.18,

  "target_min": 1.08342,

  "sr_ok": true,
  "spike_ok": true,
  "feasibility_ok": true,

  "nearest_support": 1.08210,
  "nearest_resistance": 1.08590,

  "session": "ASIA" | "LONDON" | "NY" | "LATE",

  "reason_codes": ["SR_OK", "NO_SPIKE", "FEAS_OK"],

  "engine_open_msg_id": "telegram message id (if available)",
  "result": "WIN" | "LOSS",
  "result_ts_utc": "ISO8601Z",
  "result_actor": "username_or_id",
  "result_note": "free text"
}

---

## 4. TELEGRAM COMMANDS (canonical UX)
### 4.1 /result (primary)
**Command**
`/result SYMBOL WIN`
`/result SYMBOL LOSS`

Rules:
- SYMBOL must match the most recent pending OPEN_NOW for that SYMBOL.
- If no pending trial exists for that symbol -> reply with error + show last 3 pending.
- If multiple pending exist (rare) -> require explicit trial_id.

Responses (admin topic):
- ✅ RESULT saved
- shows: trial_id, symbol, side, expiry, confidence, buffer_mode, result

Also optional echo (signals topic, if enabled):
- “RESULT logged: EUR/USD WIN (trial_id short)”

### 4.2 /result_id (explicit)
**Command**
`/result_id TRIAL_ID WIN`
`/result_id TRIAL_ID LOSS`

Use when:
- there are multiple pending for same symbol
- symbol renamed / mismatch

### 4.3 /pending (list)
**Command**
`/pending`

Response:
- list last max 10 pending trials with:
  - symbol, side, expiry, confidence, buffer_mode, open_ts
  - short trial_id (first 8 chars of hash section)
  - hint: `/result SYMBOL WIN`

### 4.4 /void (invalidate)
**Command**
`/void SYMBOL`
or
`/void_id TRIAL_ID`

Use when:
- user did not execute trade
- broker glitch
- missed entry

Effect:
- writes event_type=VOID
- removes from pending

### 4.5 /revise (change result)
**Command**
`/revise SYMBOL WIN|LOSS`
or
`/revise_id TRIAL_ID WIN|LOSS`

Rule:
- never edits old line
- appends REVISE event referencing same trial_id
- latest event wins

---

## 5. DEDUP & SAFETY RULES
1) A trial enters pending list ONLY after OPEN_NOW is sent.
2) A trial can have only one FINAL status at any time:
   - WIN / LOSS / VOID
   Latest event timestamp wins.
3) If engine restarts:
   - pending_trials.json + trials_index.json must reload
   - no duplicate OPEN_NOW may create duplicate trial_id for same candle
4) If /result is called twice:
   - second call becomes REVISE (explicitly logged as correction)

---

## 6. VALIDATION RULES
On /result:
- reject invalid SYMBOL format
- reject invalid outcome
- reject if trial not found
- reject if trial already VOID and no /revise used

On write:
- JSON must be valid
- created_ts_utc must be set
- actor must be captured

---

## 7. REQUIRED LOGGING (to OBSERVABILITY)
Every command must emit a structured log:
- action=trial_result_set
- trial_id
- symbol
- actor
- outcome
- pending_count_before/after
- success=true/false
- error_reason if failed

---

End of TRIALS_DATA_SPEC.md