# SIGNAL_STRATEGY_AND_RISK_READINESS_REPORT.md

**Audit ID:** final-system-readiness-audit-01  
**Date:** 2026-07-13  
**Branch:** copilot/conduct-final-system-readiness-audit  
**HEAD Commit:** 5aa40f0

---

## 1. SIGNAL LIFECYCLE TRACE

The complete supported signal lifecycle from market input to analytics:

```
market/input data (TwelveData API via runtime.market_client.fetch_klines)
  → core.candle_adapter (normalization, epoch-seconds ts)
  → core.strategy_v2.decide() (deterministic, stateless, pure function)
      - EMA 50/200 trend detection
      - RSI 14-period overbought/oversold
      - ATR-based buffer sizing (SMALL/MEDIUM/LARGE)
      - S/R corridor validation (sr_required_multiplier)
      - Spike filter (wick_body_ratio, range_z, jump_vs_atr)
      - Score accumulation (0–100 scale)
      - Threshold hierarchy: PRE(70) → CONFIRM(75) → OPEN(80)
      → returns Decision(stage, direction, score, expiry, buffer, ...)
  → core.signal_engine.run_once() (per-tick orchestrator)
      - loads active symbols
      - loads algo params
      - calls strategy for each symbol
      - emits signal_event to observability
      - calls core.fsm_runtime.evaluate(decision)
  → core.fsm_runtime.evaluate()
      - FSM state per symbol: IDLE → WATCH → OPEN → CLOSED
      - Applies signal to state machine
      - OPEN_NOW decision for qualifying signals
      - emits FSM events to observability
  → signal_id assignment (hash-based identity in signal_engine)
  → OPEN_NOW decision → core.distribution_router.route_signal()
  → core.distribution_router
      - loads channel_config
      - checks tier limits (FREE/BASIC/PRO/ELITE)
      - checks daily reset
      - duplicate suppression
      - calls core.telegram_publisher.send_message() per tier
      - produces publish_result per tier (PUBLISHED/FAILED/SKIPPED_SILENT/SKIPPED_LIMIT/SKIPPED_DISABLED/DUPLICATE_SUPPRESSED)
      - emits distribution_events to observability
      - calls outcome_service.register_signal_open()
  → core.outcome_service.register_signal_open()
      - registers signal in open_now_registry
      - single mutation authority for open signal lifecycle
  → core.trade_temporal_telemetry (registration on OPEN_NOW)
      - registers trade in open_trades_registry
      - captures entry price, entry ts, expiry ts
  → core.observability_logger
      - routes events to JSONL sinks (engine, FSM, distribution, admin_proofs, error)
      - validates against event_schema.json
  → outcome (async — user votes via Telegram callback)
      → outcome_service.record_vote()
          - validates callback context (member check via Telegram API)
          - pseudonymizes user ID (SHA-256 + COMMUNITY_FEEDBACK_SALT)
          - atomic write to outcomes.jsonl and outcomes_index.json
  → core.analytics_engine (batch — run by strategy_auditor_daily)
      - consumes engine_events.jsonl, distribution_events.jsonl, outcomes.jsonl
      - deduplication by (signal_id, user_id)
      - computes win_rate, distribution metrics
      - writes aggregates.json atomically
  → intelligence.research_engine (batch)
      - signal funnel analysis (signal_event → decision → distribution → outcome)
      - advisory only — no auto-apply
      - writes research_report.json atomically
```

---

## 2. CANONICAL PARAMETER CONTRACT

- **Schema:** `send/schema/params_schema.json`
- **Live config:** `send/config/algo_params.json`
- **Loader:** `core.params_loader`
- **Consumer:** `core.strategy_v2` via `signal_engine`

**Verification:** `tests/batch_02/test_canonical_parameter_contract.py::test_live_algo_params_validates_against_canonical_contract` — PASS.

**Current algo_params.json values:**
- PRE threshold: 70 | CONFIRM threshold: 75 | OPEN threshold: 80 (correct hierarchy: PRE < CONFIRM < OPEN)
- expiry_limits_minutes: min=2, max=15
- buffer_multipliers: SMALL=0.3, MEDIUM=0.55, LARGE=1.0
- EMA fast/slow: 50/200
- RSI period: 14 | rsi_call: 58.0 | rsi_put: 42.0

**Threshold ordering:** PRE(70) < CONFIRM(75) < OPEN(80) — CORRECT. Canonical requirement satisfied.

---

## 3. STRATEGY INTEGRITY

- `strategy_v2.decide()` is a pure function: no file I/O, no network calls, no Telegram calls, deterministic for identical inputs.
- Confirmed by `tests/canonical/unit/test_strategy_and_corridor.py::test_strategy_is_deterministic_and_preserves_inputs` — PASS.
- Threshold hierarchy controls stage selection: confirmed by `tests/canonical/unit/test_strategy_and_corridor.py::test_threshold_hierarchy_controls_stage_selection` — PASS.
- Strategy behavior: UNCHANGED through all 9 remediation batches.

---

## 4. SIGNAL IDENTITY AND DEDUPLICATION

- Signal identity: hash-based (derived from symbol, direction, stage, score, timestamp) — stable for identical inputs.
- Duplicate suppression in distribution_router: checks `seen_signals` set; emits `DUPLICATE_SUPPRESSED` if seen.
- Duplicate suppression in outcome_service: deduplication key `(signal_id, user_id)` in outcomes.jsonl.
- Confirmed by `tests/canonical/end_to_end/test_offline_end_to_end_flows.py::test_restart_lifecycle_preserves_dedup_and_no_duplicate_irreversible_action` — PASS.

---

## 5. EXPIRY SEMANTICS

- `expiry_limits_minutes`: min=2, max=15. Strategy computes expiry based on ATR and trend; clamped to [min, max].
- Trade temporal telemetry: records `entry_ts`, `expiry_ts` (entry_ts + expiry_minutes * 60).
- Vote window: `VOTE_WINDOW_GRACE_SECONDS = 5 * 60` (5 minutes past expiry).

---

## 6. BUFFER SEMANTICS

- ATR-based buffer (SMALL/MEDIUM/LARGE multiplied against ATR) applied to S/R corridor entry threshold.
- `sr_required_multiplier = 1.5` — price must be at least 1.5x ATR buffer away from nearest S/R level.

---

## 7. SPIKE FILTERS

- `wick_body_ratio_max = 6.0` — rejects candles with excessive wick-to-body ratio.
- `range_z_max = 3.0` — rejects abnormal range candles (z-score).
- `jump_vs_atr_max = 2.5` — rejects large gap jumps relative to ATR.

---

## 8. RISK GATES

- `send/intelligence/risk_monitor.py` — implements risk monitoring (imported by analytics/research flows).
- Threshold limits in `admin_settings.json`: min_threshold=50, max_threshold=95.
- Admin parameter changes validated against these limits in `admin_commands.py`.
- Risk control: threshold hierarchy enforced; spike filters active; buffer minimum enforced.
- `tests/batch_05/` includes admin mutation prevention tests — all PASS.

---

## 9. FAILURE BEHAVIOR

- Engine loop catches all exceptions per tick; logs error event; continues.
- Telegram publisher catches failures; emits `FAILED` publish_result; no silent failure.
- Confirmed: `tests/canonical/end_to_end/test_offline_end_to_end_flows.py::test_failure_lifecycle_publisher_exception_has_no_false_success` — PASS.
- `tests/canonical/failure_recovery/test_failure_injection_behaviors.py::test_distribution_publisher_failure_has_no_false_success` — PASS.

---

## 10. PERSISTENCE AND RESTART BEHAVIOR FOR SIGNALS

- FSM state persisted after each state change.
- Distribution state (tier counts, last_reset_date) persisted after each signal routing.
- Open trades registry persisted on each OPEN_NOW.
- On restart: FSM state and distribution state reloaded in `start_system()`. Any open trades in registry remain registered. Vote window continues from persisted state.

---

## 11. VERDICT

| Dimension | Verdict | Notes |
|---|---|---|
| Signal engine readiness | READY | Complete signal lifecycle implemented, tested, deterministic |
| Strategy parameter readiness | READY | Canonical parameter contract validated; schema present; live config passes validation |
| Risk-control readiness | READY | Threshold hierarchy, spike filters, buffer gates, admin limits all active and tested |
