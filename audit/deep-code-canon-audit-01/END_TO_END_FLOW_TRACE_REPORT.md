# END_TO_END_FLOW_TRACE_REPORT

## Flow 1 — Market data ingestion → normalization → feature/indicator preparation
- Entry: `runtime/engine_loop.py:start_engine()` → `core.signal_engine.run_once()`.
- Intended call chain: `signal_engine.run_once()` (`signal_engine.py:248-333`) → `runtime.market_client.get_candles()` (`market_client.py:45-70`) → `core.candle_adapter.normalize()/validate()` (`candle_adapter.py:35-134`) → `core.strategy_v2.decide()` (`strategy_v2.py:264-728`).
- Implemented stages: fetch M1/M5, normalize, validate, compute EMA/RSI/ATR/range/spike/time metrics.
- Missing/contradictory stages:
  - `core.signal_engine` fails to import because `core.storage.config_path` does not exist (`signal_engine.py:47,64-66`; import-check failure).
  - `market_client` does not validate API key presence before request (`market_client.py:5-18`).
- Persistence/state ops: none in this segment.
- External side effects: TwelveData API requests.
- Observability: decision event would be logged later; no explicit market-ingestion event.
- Failure behavior: engine loop catches and logs error, then sleeps (`engine_loop.py:17-31`).
- Security/risk controls: none at ingress beyond timeout.
- Final status: **FAILED AT IMPORT / CONTRADICTORY**.

## Flow 2 — Strategy evaluation → candidate generation → gating → scoring
- Entry: `signal_engine.run_once()` per symbol.
- Call chain: `strategy_v2.decide()`.
- Implemented stages:
  - Activity gate (`strategy_v2.py:361-390`)
  - Trend classification (`392-426`)
  - Buffer/SR gate (`432-448`)
  - Spike gate (`452-469`)
  - Feasibility/time gate (`475-497`)
  - Scoring and threshold stage selection (`500-728`)
- Contradictory stages:
  - Strategy reads `strategy_v2`, `score_thresholds`, `buffer_multipliers`, `expiry_limits_minutes`; runtime config provides `thresholds`, `buffer.modes`, `expiry` (`strategy_v2.py:303-343` vs `config/algo_params.json:4-38`).
  - Thresholds in config are therefore not authoritative for strategy execution.
- Observability: decision event payload emitted in `signal_engine.py:308-328`.
- Risk controls: SR/spike/feasibility gates implemented; cooldown/max concurrent exposure not integrated.
- Final status: **PARTIAL/CONTRADICTORY**.

## Flow 3 — Support/resistance corridor evaluation
- Entry: inside `strategy_v2.decide()`.
- Call chain: `_swing_points_from_m5()` → `_nearest_support_resistance()` → `_available_space()` (`strategy_v2.py:141-195,443-448`).
- Implemented: simple swing-derived support/resistance and available-space comparison.
- Missing: no first-class corridor object, no richer corridor semantics from spec, no persistence of structural explanation beyond debug blob.
- Observability: SR gate stored in `gates.sr_gate` and decision debug.
- Final status: **PARTIAL**.

## Flow 4 — Signal decision → signal creation → persistence
- Entry: `signal_engine.run_once()` after decision.
- Call chain: `_make_signal_event()` (`signal_engine.py:105-120`) → `distribution_router.route()`.
- Implemented: PRE/CONFIRM/OPEN_NOW events created; decision and transition events logged.
- Persistence: FSM state saved (`signal_engine.py:332-333`); no durable signal store separate from logs.
- Contradictions:
  - No canonical signal object persistence layer.
  - OPEN_NOW registration attempts missing telemetry module (`signal_engine.py:359-372`).
- Final status: **PARTIAL/CONTRADICTORY**.

## Flow 5 — Open-now trade registration → temporal telemetry → outcome tracking
- Entry: OPEN_NOW branch in `signal_engine.run_once()`.
- Intended chain: `trade_temporal_telemetry.register_open_now_trade()` → `distribution_router.route()` → `outcome_service.register_open_now()`.
- Actual chain: import of `trade_temporal_telemetry` missing; router separately calls `outcome_service.register_open_now()` on successful ELITE/admin publish (`distribution_router.py:595-603`).
- Missing stages:
  - Entire canonical temporal telemetry module absent.
  - No canonical temporal metrics store.
- Contradictory stages:
  - Outcome registration exists without canonical telemetry layer.
- Final status: **MISSING / CRITICAL**.

## Flow 6 — Signal distribution → entitlement/tier/channel routing → Telegram publishing
- Entry: `distribution_router.route()`.
- Call chain: load config/state → reset check → dedup/limit logic → `telegram_publisher.send_message()`.
- Implemented: tier loop, silent mode, OPEN_NOW counters, admin mirror, feedback markup.
- Contradictory stages:
  - `load_config()` ignores file admin IDs and limits (`distribution_router.py:91-145`).
  - `_log_tier_publish()` calls `observability_logger.build_event()` with invalid kwargs (`264-302` vs logger signature `150-164`).
  - Dedup key string format undocumented (`209-220`).
- Persistence: `dist_state.json` via `save_state()`.
- External side effects: Telegram `sendMessage`.
- Final status: **CONTRADICTORY / HIGH-CRITICAL**.

## Flow 7 — Outcome recording → performance analytics → research/learning feedback
- Entry: Telegram callback vote.
- Actual chain:
  - `runtime.telegram_updates.process_update()` calls `outcome_service.handle_vote_callback()` for any `VOTE_...` (`telegram_updates.py:86-99`).
  - Then same update is forwarded to `bot_service.process_update()` (`telegram_updates.py:101`), whose callback handler also records `VOTE_|...` to separate `state/outcomes.json` store (`bot_service.py:283-337`).
- Implemented: membership/window/locking in `outcome_service` plus offline aggregates/reporting.
- Contradictory stages:
  - Double handling, divergent stores, different security semantics.
  - `analytics_engine.py` and `research_engine.py` call undefined `storage.safe_json_loads`.
- Final status: **CONTRADICTORY / CRITICAL**.

## Flow 8 — Strategy intelligence → parameter recommendations → parameter governance/control
- Entry: offline/intelligence modules (`adaptive_params`, `strategy_optimizer`).
- Call chain: `strategy_optimizer.optimize_strategy()` → `adaptive_params.adjust_parameters()` → `params_loader.load_algo_params()`.
- Implemented: heuristic threshold adjustments returned in-memory.
- Missing: no approval gate, no proof logging, no controlled writeback, no promotion lifecycle.
- Contradictory: optimizer emits disallowed event type `strategy_optimizer`.
- Final status: **PARTIAL**.

## Flow 9 — Autonomous strategy evolution → batch evaluation → promotion/rejection lifecycle
- Entry: `experiments/parameter_search.py`, `experiments/experiment_runner.py`, `model_registry/registry.py`.
- Implemented: parameter grid generation, skeleton experiment logging, atomic registry utility.
- Missing: simulation, comparative evaluation, promotion/rejection, safety gates, branch isolation, approval workflow.
- Final status: **MOSTLY MISSING**.

## Flow 10 — Admin/control-plane command → authorization → validation → mutation → audit record
- Entry: `bot_service.process_update()` slash commands → `admin_commands.handle_admin_command()`.
- Call chain: parse command → `admin_permissions.require_permission()` → direct JSON mutate/write → `_audit()` append JSONL.
- Implemented: command families for thresholds, SR, spike, symbols, reports, roles.
- Contradictions:
  - Writes bypass `core.storage` atomic/lock layer (`admin_commands.py:53-56,97-99,123-139`).
  - Validation is hardcoded and not sourced from `admin_settings.json` or `params_loader`.
  - Separate `bot_service` control plane still active.
- Security: role checks exist, but callback path has fail-open chat check in `bot_service.py:79-82`.
- Final status: **CONTRADICTORY / HIGH**.

## Flow 11 — Startup → configuration loading → schema validation → dependency initialization → runtime health
- Entry: `runtime/system_boot.py:start_system()`.
- Implemented: `.env` load before imports, restart guard, three daemon threads.
- Missing/contradictory:
  - No schema validation at boot.
  - Boot fails because `signal_engine` import fails (`config_path` missing).
  - Telegram publisher import fails without token at import time, coupling boot to env completeness.
- Final status: **FAILED / CRITICAL**.

## Flow 12 — Failure path → exception handling → observability/logging → alerting → recovery behavior
- Implemented:
  - Per-loop exception capture in engine/scheduler/Telegram poller.
  - `observability_logger.log_error()` fallback path.
  - Restart guard and snapshot utilities.
- Contradictions:
  - Several modules emit disallowed event types, so observability degrades silently.
  - No actual alert dispatch pipeline beyond file logging.
  - Snapshot restore is non-atomic.
- Final status: **PARTIAL/CONTRADICTORY**.

## Flow 13 — Security-sensitive path → authorization/secret handling/input validation/state mutation
- Entry: admin commands and outcome votes.
- Implemented: RBAC in `admin_permissions.py`; elite membership check in `outcome_service.py`.
- Contradictions:
  - `bot_service` callback path duplicates outcome mutation without membership/window guard.
  - `bot_service.in_admin_context()` is fail-open if `ADMIN_CONTROL_CHAT_ID` unset.
  - Secrets handled via env vars, but no boot-time validation/audit of required secrets.
- Final status: **CONTRADICTORY / CRITICAL**.

## Flow 14 — Risk-control path → risk policy evaluation → blocking/allowing action → auditability
- Implemented: SR gate, spike filter, feasibility gate inside strategy core.
- Missing/contradictory:
  - No enforced max concurrent exposure or cooldown policy in active runtime path.
  - `risk_monitor.evaluate_risk()` is not wired into engine and uses invalid logger call on low win rate.
- Final status: **PARTIAL/CONTRADICTORY**.
