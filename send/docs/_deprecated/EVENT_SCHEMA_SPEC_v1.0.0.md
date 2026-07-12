# EVENT_SCHEMA_SPEC.md
BinaryBot — Event Schema Specification
Version: 1.0.0
Status: Canonical

Linked Docs:
- OBSERVABILITY_LOGGING_SPEC.md
- PERFORMANCE_ANALYTICS_SPEC.md
- SIGNAL_DISTRIBUTION_SPEC.md
- CHANNEL_CONFIG_SPEC.md
- TELEGRAM_UX.md
- FSM_SPEC.md
- ARCHITECTURE_CODE_MAPPING.md
- GOVERNANCE_AND_CHANGE_CONTROL.md
- SYSTEM_INVARIANTS.md
- FORMAL_SPEC.md

---

## 0) PURPOSE

Acest document definește **schema canonică** pentru toate evenimentele pe care BinaryBot le scrie în logurile JSONL și le folosește pentru:
- debugging rapid
- analytics corecte
- audit complet (proof logs)
- reproducerea bugurilor
- reconstrucția funnel-ului PRE→CONFIRM→OPEN_NOW
- corelarea: engine ⇄ FSM ⇄ distribution ⇄ outcome ⇄ admin changes

Regulă:
- **Orice log JSONL trebuie să respecte aceste câmpuri.**
- Evenimentele sunt **append-only**.
- Orice schimbare de schemă = bump de versiune + CHANGELOG entry.

---

## 1) EVENT ENVELOPE (COMMON FIELDS)

Toate evenimentele au acest „envelope” comun.

### 1.1 Required fields (all events)
- `event_id` (string)  
  - unique global id (ex: UUID4)
- `event_type` (string enum)
  - one of:
    - `engine_start`
    - `engine_stop`
    - `signal_event`
    - `decision`
    - `fsm_transition`
    - `tier_publish`
    - `tier_reset`
    - `admin_change`
    - `user_outcome`
    - `error`
- `schema_version` (string)
  - example: `"1.0.0"`
- `ts_utc` (string, ISO 8601, UTC, Z)
  - example: `"2026-03-04T08:12:34.123Z"`
- `ts_epoch_ms` (integer)
  - milliseconds epoch
- `ts_local` (string, ISO 8601 with tz offset)
  - local operator time (optional but recommended)
- `service` (string)
  - `"binarybot"`
- `env` (string)
  - `"prod"` | `"staging"` | `"dev"`
- `run_id` (string)
  - identifies current runtime session (new on each process start)
- `host` (object)
  - `hostname` (string)
  - `pid` (int)
  - `version` (string) bot/app version
  - `git_sha` (string, optional)
- `source` (object)
  - `module` (string) ex: `"signal_engine"`
  - `function` (string) ex: `"engine_loop"`
  - `line` (int, optional)

### 1.2 Optional correlation fields (common)
- `trace_id` (string, optional)
  - correlates multiple events in same logical flow
- `symbol` (string, optional)
  - ex: `"EURUSD"`
- `timeframe` (string, optional)
  - ex: `"M15"`
- `candle_ts` (string, optional ISO8601 Z)
  - timestamp of candle used for decision
- `signal_id` (string, optional)
  - stable id across PRE/CONFIRM/OPEN_NOW (same trade idea)
- `tier` (string, optional)
  - `FREE|BASIC|PRO|ELITE`
- `user_id` (int/string, optional)
  - Telegram user id (only for user_outcome/admin_change)
- `chat_id` (int/string, optional)
  - Telegram chat/channel id (publish target)
- `message_id` (int, optional)
  - Telegram message_id for sent/edited messages

### 1.3 MUST NOT
- No secrets (tokens, API keys).
- No raw personal data beyond Telegram numeric IDs where necessary.

---

## 2) CANONICAL ENUMS

### 2.1 Engine mode
- `engine_mode`: `WIDE_SCAN` | `FOCUS_MODE`

### 2.2 Signal stage
- `stage`: `PRE` | `CONFIRM` | `OPEN_NOW`

### 2.3 Decision kind
- `decision_kind`: `PRE` | `CONFIRM` | `OPEN_NOW` | `REJECT` | `NO_SIGNAL`

### 2.4 Tier state
- `tier_state`: `ACTIVE` | `SILENT` | `DISABLED`

### 2.5 Publish decision
- `publish_decision`: `PUBLISHED` | `SKIPPED_SILENT` | `SKIPPED_LIMIT` | `SKIPPED_DISABLED` | `FAILED` | `DUPLICATE_SUPPRESSED`

### 2.6 Outcome
- `outcome`: `WIN` | `LOSE` | `MISSED`

### 2.7 Session labels
- `session`: `ASIA` | `LONDON` | `NY` | `UNKNOWN`

---

## 3) EVENT TYPES (SCHEMAS)

### 3.1 engine_start
Emis o singură dată la pornirea procesului.

Required fields:
- common envelope
- `event_type`: `"engine_start"`
- `data`:
  - `engine_mode` (enum)
  - `loop_interval_ms` (int)
  - `symbols_selected_count` (int)
  - `symbols_selected` (array[string], optional)
  - `buffer_mode` (enum: SMALL|MEDIUM|LARGE)
  - `params_version` (string, optional)
  - `channel_config_loaded` (bool)
  - `reset_time_london` (string, ex `"08:10 Europe/London"`)

---

### 3.2 engine_stop
Emis la oprire normală / shutdown.

Required:
- `event_type`: `"engine_stop"`
- `data`:
  - `reason` (string) ex: `"manual_stop"|"crash"|"deploy"`
  - `uptime_sec` (number)
  - `last_engine_mode` (enum)

---

### 3.3 decision
Log intern pentru fiecare evaluare de simbol/candle (și când e REJECT/NO_SIGNAL).

Required:
- `event_type`: `"decision"`
- correlation:
  - `symbol`, `timeframe`, `candle_ts`
- `data`:
  - `decision_kind` (enum)
  - `stage` (enum or null)
    - stage is meaningful when decision_kind is PRE/CONFIRM/OPEN_NOW
  - `signal_id` (string or null)
    - MUST exist when decision_kind ∈ {PRE,CONFIRM,OPEN_NOW}
  - `score_total` (number, 0-100)
  - `buffer_mode` (SMALL|MEDIUM|LARGE)
  - `buffer_value` (number, optional)
  - `expiry_min` (number, optional)
  - `want_open_now` (bool)
  - `trend_class` (WITH_TREND|FLAT|COUNTER_TREND, optional)
  - `session` (enum)
  - `gates` (object)
    - `sr_gate`:
      - `passed` (bool)
      - `available_space` (number, optional)
      - `required_space` (number, optional)
      - `reason` (string, optional)
    - `spike_filter`:
      - `passed` (bool)
      - `range_z` (number, optional)
      - `wick_body_ratio` (number, optional)
      - `atr_accel` (number, optional)
      - `jump_vs_atr` (number, optional)
      - `reason` (string, optional)
    - `feasibility`:
      - `passed` (bool)
      - `t_needed` (number, optional)
      - `expiry_min` (number, optional)
      - `reason` (string, optional)
  - `dedup` (object)
    - `key` (string)  // symbol+candle_ts+stage
    - `was_duplicate` (bool)
    - `action` (string) // "emit"|"suppress"

Notes:
- Dacă `decision_kind` este `REJECT` sau `NO_SIGNAL`, `signal_id` poate fi null.
- Dacă `decision_kind` este PRE/CONFIRM/OPEN_NOW, `signal_id` este obligatoriu.

---

### 3.4 signal_event
Evenimentul „public” emis de engine către distribution layer (după decizie + FSM ok).

Required:
- `event_type`: `"signal_event"`
- correlation:
  - `signal_id` (required)
  - `symbol` (required)
  - `timeframe` (required)
  - `candle_ts` (required)
- `data`:
  - `stage` (required enum)
  - `direction` (BUY|SELL)
  - `buffer_mode` (SMALL|MEDIUM|LARGE)
  - `buffer_value` (number)
  - `expiry_min` (number)
  - `score_total` (number)
  - `engine_mode` (WIDE_SCAN|FOCUS_MODE)
  - `message_template` (string, optional) // PRE/CONFIRM/OPEN
  - `payload_hash` (string, optional) // integrity
  - `dedup`:
    - `key` (string) // symbol+candle_ts+stage
    - `was_duplicate` (bool)
    - `action` (emit|suppress)

Guarantee:
- PRE/CONFIRM/OPEN_NOW pentru aceeași idee → același `signal_id`.

---

### 3.5 fsm_transition
Orice tranzitie a FSM-ului (inclusiv no-op dacă vrei să loghezi).

Required:
- `event_type`: `"fsm_transition"`
- correlation:
  - `symbol` (required)
  - `signal_id` (optional but recommended when triggered by stage)
- `data`:
  - `from_state` (IDLE|WATCHLIST|LIVE_SENT|COOLDOWN)
  - `to_state` (IDLE|WATCHLIST|LIVE_SENT|COOLDOWN)
  - `reason` (string) // ex: "pre_emitted"|"confirm_emitted"|"open_sent"|"cooldown_expired"|"symbol_deselected"
  - `watchlist_size` (int)
  - `focus_symbols` (array[string])
  - `cooldown_until_utc` (string, optional)
  - `invariants` (object)
    - `max_focus_ok` (bool)
    - `dedup_ok` (bool)
    - `cooldown_ok` (bool)
  - `persisted` (bool)

---

### 3.6 tier_publish
Rezultatul publicării către fiecare tier/channel.

Required:
- `event_type`: `"tier_publish"`
- correlation:
  - `tier` (required)
  - `signal_id` (required)
  - `stage` (required)
  - `chat_id` (required)
- `data`:
  - `publish_decision` (required enum)
  - `tier_state_before` (ACTIVE|SILENT|DISABLED)
  - `tier_state_after` (ACTIVE|SILENT|DISABLED)
  - `limit` (int or null) // null for unlimited
  - `counter_before` (int)
  - `counter_after` (int)
  - `counted` (bool) // true only if OPEN_NOW published successfully and tier != ELITE
  - `telegram` (object)
    - `ok` (bool)
    - `message_id` (int, optional)
    - `error` (string, optional)
    - `retryable` (bool, optional)
  - `dedup` (object)
    - `key` (string) // tier+signal_id+stage
    - `was_duplicate` (bool)
    - `action` (string) // publish|suppress

Rules:
- counter increases ONLY if:
  - stage == OPEN_NOW
  - publish_decision == PUBLISHED
  - tier != ELITE
- if counter reaches limit → tier_state_after becomes SILENT and future stages blocked.

---

### 3.7 tier_reset
Reset zilnic pentru counters + tier states.

Required:
- `event_type`: `"tier_reset"`
- `data`:
  - `reset_time_london` (string) // "08:10 Europe/London"
  - `effective_date_london` (string, YYYY-MM-DD)
  - `tiers` (object)
    - `FREE`:
      - `counter_before` (int)
      - `counter_after` (int)
      - `state_before` (ACTIVE|SILENT|DISABLED)
      - `state_after` (ACTIVE|SILENT|DISABLED)
    - similarly BASIC/PRO/ELITE
  - `idempotent` (bool) // true if called twice same day results same
  - `persisted` (bool)

---

### 3.8 user_outcome
Feedback de la membri (ELITE) pe OPEN_NOW.

Required:
- `event_type`: `"user_outcome"`
- correlation:
  - `signal_id` (required)
  - `tier` (required, must be ELITE)
  - `user_id` (required)
- `data`:
  - `outcome` (WIN|LOSE|MISSED)
  - `policy` (string) // "LOCK_FIRST_WRITE_WINS"
  - `accepted` (bool)
  - `rejected_reason` (string, optional) // "already_voted"|"vote_window_closed"|"too_early"
  - `vote_window` (object)
    - `trade_open_utc` (string)
    - `expiry_min` (number)
    - `vote_start_utc` (string)
    - `vote_end_utc` (string)
    - `ts_clicked_utc` (string)
  - `telegram` (object, optional)
    - `callback_query_id` (string, optional)
    - `message_id` (int, optional)
  - `aggregates_after` (object, optional)
    - `win_count` (int)
    - `lose_count` (int)
    - `missed_count` (int)
    - `total` (int)

Privacy:
- nu logăm username/phone/name.

---

### 3.9 admin_change
Orice schimbare de setare făcută de admin (buffer mode, symbols, tier config updates, etc.)
Trebuie să producă și „proof message”.

Required:
- `event_type`: `"admin_change"`
- correlation:
  - `user_id` (required)
- `data`:
  - `action` (string)
    - ex: "set_buffer"|"set_symbols"|"reload_channel_config"|"manual_reset"|"set_limits"
  - `before` (object)
  - `after` (object)
  - `scope` (string)
    - "settings.json"|"active_symbols.json"|"channel_config.json"|"dist_state.json"
  - `proof` (object)
    - `posted_to_admin_topic` (bool)
    - `proof_message_id` (int, optional)
  - `persisted` (bool)

---

### 3.10 error
Eveniment standard pentru excepții / runtime failures.

Required:
- `event_type`: `"error"`
- `data`:
  - `severity` (INFO|WARN|ERROR|CRITICAL)
  - `error_type` (string)
  - `message` (string)
  - `stack` (string, optional)
  - `context` (object, optional)

---

## 4) LOG FILES (RECOMMENDED SPLIT)

Recomandat (nu obligatoriu):
- `/opt/binarybot/observability/engine_events.jsonl`
  - engine_start/stop, decision, signal_event
- `/opt/binarybot/observability/fsm_events.jsonl`
  - fsm_transition
- `/opt/binarybot/observability/distribution_events.jsonl`
  - tier_publish, tier_reset
- `/opt/binarybot/observability/admin_proofs.jsonl`
  - admin_change + critical alerts
- `/opt/binarybot/outcomes/outcomes.jsonl`
  - user_outcome (sau tot în observability)

Regulă:
- Toate sunt JSONL append-only.
- Rotation: by size/day (definit în OBSERVABILITY_LOGGING_SPEC.md).

---

## 5) INTEGRITY RULES (MUST)

1) `signal_id` stabil:
- aceeași idee de trade → același signal_id pentru PRE/CONFIRM/OPEN_NOW.

2) Dedup keys:
- engine: `symbol + candle_ts + stage`
- distribution: `tier + signal_id + stage`

3) Counter correctness:
- numai OPEN_NOW publicat cu succes crește counter (non-ELITE).

4) Restart safety:
- logurile nu se rescriu, doar append.
- state files persist: settings/active_symbols/focus_state/dist_state.

---

## 6) EXAMPLES (MINI)

### 6.1 Example: tier_publish OPEN_NOW counted
{
  "event_id":"6f3c...uuid",
  "event_type":"tier_publish",
  "schema_version":"1.0.0",
  "ts_utc":"2026-03-04T08:20:00.100Z",
  "ts_epoch_ms":1772612400100,
  "service":"binarybot",
  "env":"prod",
  "run_id":"run_20260304_001",
  "host":{"hostname":"srv1","pid":1234,"version":"1.1.0"},
  "source":{"module":"distribution_router","function":"publish_stage"},
  "tier":"FREE",
  "signal_id":"EURUSD_M15_20260304_001",
  "data":{
    "publish_decision":"PUBLISHED",
    "tier_state_before":"ACTIVE",
    "tier_state_after":"ACTIVE",
    "limit":6,
    "counter_before":2,
    "counter_after":3,
    "counted":true,
    "telegram":{"ok":true,"message_id":555},
    "dedup":{"key":"FREE|EURUSD_M15_20260304_001|OPEN_NOW","was_duplicate":false,"action":"publish"}
  }
}

---

End of EVENT_SCHEMA_SPEC.md