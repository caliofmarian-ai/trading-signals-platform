# DECISION_AUDIT_SPEC.md

## 1. PURPOSE

This document defines the canonical **Decision Audit Layer** for BinaryBot / DROPi Signals.

The purpose of this layer is to record, explain, aggregate, and later analyze **why a signal was promoted, rejected, delayed, killed, or never reached the final `OPEN_NOW` stage**.

This is not a cosmetic analytics feature.

This is a core architectural layer used for:

- strategy learning
- rejection analysis
- parameter tuning
- focus/watchlist optimization
- signal lifecycle observability
- post-mortem analysis of dead signals
- safe iteration of scoring and gates
- evidence-based improvement of the strategy

Without this layer, the system can only answer:

- “a PRE appeared”
- “an OPEN_NOW did not appear”

With this layer, the system must be able to answer:

- why PRE appeared
- why PRE did not become CONFIRM
- why CONFIRM did not become OPEN_NOW
- which gate killed the signal
- whether the signal was rejected due to score, spike, SR, feasibility, focus pressure, cooldown, dedup, or channel distribution limits
- whether the same symbol repeatedly dies for the same reason
- whether a parameter change improved or degraded the conversion pipeline

This specification upgrades the project from a simple signal emission engine to an **observable, learnable strategy system**.

---

## 2. SCOPE

This specification applies to the full signal decision pipeline, including:

- wide scan
- focus/watchlist selection
- PRE stage
- CONFIRM stage
- OPEN_NOW stage
- distribution routing
- channel-level acceptance/rejection
- signal death after partial promotion
- post-decision analytics and aggregation

This document does **not** replace:

- `EVENT_SCHEMA_SPEC.md`
- `ALGO_SPEC.md`
- `FSM_SPEC.md`
- `TELEGRAM_UX.md`
- `OBSERVABILITY_LOGGING_SPEC.md`
- `RESEARCH_AND_LEARNING_FRAMEWORK_SPEC.md`

Instead, it extends them by defining the **decision audit contract** that links all of them into a learning loop.

---

## 3. DESIGN PRINCIPLES

### 3.1 Strategy quality is single and universal

The system must not define different signal quality standards for FREE, BASIC, PRO, or ELITE.

Signal quality is determined only by:

- market data
- strategy logic
- scoring
- gates
- focus policy
- execution timing

Channel routing is an operational layer, not a quality layer.

### 3.2 Rejections must be explicit, not inferred

If a signal dies, the system must log the reason directly.

The system must never require operators to infer cause by reading raw code, comparing logs manually, or guessing from absence of output.

### 3.3 Every major decision point must be observable

The strategy must log all meaningful transitions and all meaningful rejections.

This includes both positive and negative outcomes.

### 3.4 Learning must be based on data, not impressions

Any future parameter change should be justified by aggregated decision audit evidence, not by isolated anecdotes.

### 3.5 The audit layer must be production-safe

The audit system must not:

- block engine progress
- crash the engine when logging fails
- silently corrupt logs
- generate unbounded noisy spam without structure

---

## 4. HIGH-LEVEL OBJECTIVE

The Decision Audit Layer must answer the following classes of questions:

### 4.1 Detection questions

- Which symbols produce the most PRE candidates?
- Which symbols rarely even reach PRE?
- At what times do viable candidates appear?

### 4.2 Rejection questions

- Do most signals die because of score?
- Do most signals die because of SR gate?
- Do most signals die because of spike filter?
- Do most signals die because of feasibility?
- Do most signals die because focus/watchlist is full?
- Do most signals die because another symbol already occupies focus?

### 4.3 Promotion questions

- What percentage of PRE becomes CONFIRM?
- What percentage of CONFIRM becomes OPEN_NOW?
- Which symbols convert best?
- Which symbols stall at PRE but never confirm?

### 4.4 Operational questions

- Which channels are hitting `OPEN_NOW` limits?
- Are dedup rules suppressing too aggressively?
- Are distribution limits preventing visibility of otherwise valid signals?

### 4.5 Research questions

- If threshold `open` is reduced from 80 to 75, how many additional OPEN_NOW events appear?
- If `sr_gate` is softened, what is the projected increase in candidate flow?
- If spike rejection is relaxed, does winrate degrade or improve?

---

## 5. DECISION LIFECYCLE MODEL

The canonical signal lifecycle is:

```text
WIDE_SCAN
  ↓
CANDIDATE_DETECTED
  ↓
SCORE_COMPUTED
  ↓
GATE_EVALUATION
  ↓
FOCUS_DECISION
  ↓
PRE
  ↓
CONFIRM
  ↓
OPEN_NOW
  ↓
DISTRIBUTION
  ↓
OUTCOME / FEEDBACK / EXPIRY```

At any step, a signal may die.
Every death point must be auditable.

## 6. CORE CONCEPTS

### 6.1 Candidate

A candidate is a symbol-direction-timeframe combination under evaluation before or during signal progression.

Canonical candidate identity:

- `symbol`
- `direction`
- `timeframe`
- `candle_ts`
- optional `signal_id` if already assigned

### 6.2 Decision

A decision is the structured result returned by the strategy for a candidate at a given evaluation moment.

Decision kinds may include:

- `NO_SIGNAL`
- `PRE`
- `CONFIRM`
- `OPEN_NOW`
- `REJECT`

### 6.3 Rejection

A rejection is any event where a candidate fails to progress or is explicitly blocked.

A rejection is not limited to full candidate death. It also includes:

- failing to enter focus
- failing to upgrade from PRE to CONFIRM
- failing to upgrade from CONFIRM to OPEN_NOW
- failing distribution due to limits or dedup

### 6.4 Decision Audit Event

A Decision Audit Event is a structured observability event describing:

- what was evaluated
- what the strategy concluded
- why it concluded that
- what gate(s) passed or failed
- what happened next

## 7. AUDIT EVENT CLASSES

The system must support at least the following event classes.

### 7.1 candidate_detected

Emitted when a symbol becomes a meaningful evaluation candidate.

Purpose:
- mark symbol entry into serious evaluation
- support later conversion metrics

### 7.2 decision_evaluated

Emitted after scoring + gates are computed, even if final kind is `NO_SIGNAL`.

Purpose:
- preserve decision evidence
- expose score and gate statuses

### 7.3 decision_rejected

Emitted when the final evaluation blocks promotion or blocks a candidate entirely.

Purpose:
- explicit rejection taxonomy
- analytics by cause

### 7.4 focus_entered

Emitted when a symbol is added to watchlist/focus.

### 7.5 focus_rejected

Emitted when a symbol deserved escalation but could not enter focus.

Typical reasons:

- watchlist full
- lower priority than existing focus symbols
- cooldown conflict
- duplicate focus symbol
- stale candidate

### 7.6 stage_promoted

Emitted when a signal transitions:

- `NO_SIGNAL → PRE`
- `PRE → CONFIRM`
- `CONFIRM → OPEN_NOW`

### 7.7 stage_killed

Emitted when a signal that already had a stage loses viability.

Examples:

- PRE dies before CONFIRM
- CONFIRM dies before OPEN_NOW
- OPEN_NOW withheld due to operational constraints

### 7.8 distribution_decision

Emitted when router decides:

- published
- suppressed duplicate
- blocked by tier limit
- blocked by inactive channel state

### 7.9 outcome_linked

Emitted when later feedback or expiry result is attached to a prior signal.

## 8. CANONICAL REJECTION TAXONOMY

The following rejection reasons are canonical.

Implementations may extend them, but must not change existing meanings.

### 8.1 Score-based rejections

- `score_pre_fail`
- `score_confirm_fail`
- `score_open_fail`

Meaning:
score did not reach stage threshold.

### 8.2 Gate-based rejections

- `spike_reject`
- `sr_reject`
- `feasibility_reject`
- `trend_reject`
- `structure_reject`
- `buffer_reject`
- `expiry_reject`

### 8.3 Focus/watchlist rejections

- `focus_not_required_yet`
- `focus_full`
- `focus_priority_lost`
- `focus_duplicate`
- `focus_cooldown_active`
- `focus_state_missing`
- `focus_state_invalid`

### 8.4 Lifecycle drop reasons

- `pre_stalled`
- `confirm_stalled`
- `open_window_expired`
- `signal_invalidated_by_new_candle`
- `direction_flipped`
- `momentum_lost`
- `trend_changed`

### 8.5 Operational rejections

- `distribution_limit_reached`
- `distribution_channel_inactive`
- `distribution_duplicate`
- `distribution_error`
- `observability_log_failed`

### 8.6 Data / integrity rejections

- `missing_candles`
- `invalid_candle_shape`
- `market_api_error`
- `adapter_validation_failed`
- `state_corruption`
- `unknown_error`

## 9. REQUIRED AUDIT FIELDS

Every audit-capable decision event must include the following minimum fields unless explicitly not applicable.

### 9.1 Identity

- `event_id`
- `event_type`
- `schema_version`
- `ts_utc`
- `ts_epoch_ms`
- `run_id`
- `service`
- `env`
- `module`
- `function`

### 9.2 Candidate identity

- `symbol`
- `direction`
- `timeframe`
- `candle_ts`
- `signal_id` (nullable before assignment)

### 9.3 Decision data

- `decision_kind`
- `score_total`
- `buffer_mode`
- `buffer_price`
- `expiry_minutes`

### 9.4 Gate data

- `spike_ok`
- `sr_ok`
- `feasibility_ok`
- `trend_ok`
- `structure_ok`

### 9.5 Focus / state data

- `mode`
- `watchlist_size`
- `watchlist_symbols`
- `focus_entered`
- `focus_reason`
- `cooldown_active`

### 9.6 Rejection data

- `rejected_reason`
- `rejection_stage`
- `rejection_details`

### 9.7 Distribution data

- `channel`
- `channel_limit`
- `tier_state`
- `publish_decision`
- `was_duplicate`

## 10. OPTIONAL HIGH-VALUE FIELDS

These fields are strongly recommended because they significantly improve future research value.

- `trend_class`
- `ema_fast`
- `ema_slow`
- `rsi_value`
- `atr_value`
- `required_sr_space`
- `available_sr_space`
- `spike_wick_body_ratio`
- `spike_range_z`
- `spike_jump_vs_atr`
- `feasibility_t_needed`
- `feasibility_t_adjusted`
- `focus_rank`
- `candidate_rank_among_symbols`
- `focus_competitors`
- `previous_state`
- `next_state`

## 11. STORAGE CONTRACT

### 11.1 Primary log file

A dedicated file must exist:

/opt/binarybot/observability/decision_audit.jsonl

This file is the canonical audit stream for strategy decisions.

### 11.2 Existing logs remain valid

Existing logs remain in place:

- /opt/binarybot/observability/engine_events.jsonl
- /opt/binarybot/observability/fsm_events.jsonl
- /opt/binarybot/observability/distribution_events.jsonl
- /opt/binarybot/observability/error_events.jsonl
- /opt/binarybot/observability/admin_proofs.jsonl

The new audit layer must complement them, not replace them.

### 11.3 Mirroring rule

High-value audit events may also be mirrored into existing logs if useful, but decision_audit.jsonl remains the canonical source for learning analytics.

### 11.4 Write safety

Audit writing must be:

- append-only
- line-delimited JSON
- robust to partial failure
- non-blocking to engine progression

## 12. EVENT EXAMPLES

### Example: candidate_detected

{
  "event_type": "candidate_detected",
  "ts_utc": "2026-03-06T11:02:14Z",
  "symbol": "EURUSD",
  "direction": "SELL",
  "timeframe": "M15",
  "candle_ts": 1772800000,
  "candidate_rank_among_symbols": 3,
  "focus_rank": null,
  "score_total": 38,
  "trend_ok": true,
  "spike_ok": true,
  "sr_ok": true,
  "feasibility_ok": true
}

### Example: decision_rejected

{
  "event_type": "decision_rejected",
  "ts_utc": "2026-03-06T11:02:17Z",
  "symbol": "EURUSD",
  "direction": "SELL",
  "timeframe": "M15",
  "decision_kind": "NO_SIGNAL",
  "score_total": 36,
  "rejected_reason": "score_pre_fail",
  "trend_ok": true,
  "spike_ok": true,
  "sr_ok": true,
  "feasibility_ok": true
}

### Example: focus_entered

{
  "event_type": "focus_entered",
  "symbol": "EURUSD",
  "direction": "SELL",
  "timeframe": "M15",
  "watchlist_size": 2,
  "watchlist_symbols": ["EURUSD","GBPUSD"]
}

### Example: stage_promoted

{
  "event_type": "stage_promoted",
  "symbol": "EURUSD",
  "direction": "SELL",
  "stage_from": "PRE",
  "stage_to": "CONFIRM",
  "score_total": 66
}

### Example: distribution_decision

{
  "event_type": "distribution_decision",
  "symbol": "EURUSD",
  "stage": "PRE",
  "channel": "FREE",
  "publish_decision": "PUBLISHED",
  "tier_state": "ACTIVE"
}

## 13. AGGREGATIONS REQUIRED

Analytics systems must compute the following aggregates.

### Rejection counts by reason

Example table:

| reason | count |
|------|------|
| score_pre_fail | 420 |
| spike_reject | 120 |
| sr_reject | 80 |
| feasibility_reject | 90 |

Purpose:
identify dominant rejection causes.

### Conversion funnel

Candidate → PRE → CONFIRM → OPEN_NOW

Example:

| stage | count |
|------|------|
| candidate | 10,000 |
| PRE | 1,200 |
| CONFIRM | 450 |
| OPEN_NOW | 220 |

This reveals where signals die.

### Symbol performance

| symbol | candidates | PRE | CONFIRM | OPEN |
|------|------|------|------|------|
| EURUSD | 1000 | 120 | 60 | 32 |
| BTCUSD | 900 | 200 | 100 | 45 |

### Timeframe performance

| timeframe | candidates | PRE | OPEN |
|------|------|------|------|
| M5 | 5000 | 400 | 120 |
| M15 | 3500 | 700 | 400 |

### Focus analytics

| metric | value |
|------|------|
| average_focus_size | 1.7 |
| focus_rejections | 340 |
| focus_duplicates | 120 |

Focus analytics reveals if the engine is starved by focus constraints.

## 14. STRATEGY LEARNING RULES

Decision audit logs must support controlled strategy improvement.

### Rule 1 — No tuning without data

Strategy parameters must not be changed based on intuition alone.

Changes must reference:

- rejection statistics
- conversion funnel
- symbol distribution

### Rule 2 — Gate analysis

Every gate must be evaluated by rejection frequency.

Example:

spike_reject rate = 17%

If rejection exceeds acceptable thresholds, spike detection may be too aggressive.

### Rule 3 — Score threshold tuning

If:

PRE conversion rate < expected baseline

then:

pre threshold may be too strict.

### Rule 4 — Symbol specialization

Some symbols behave differently.

Example:

BTCUSD may require different spike tolerance compared to EURUSD.

### Rule 5 — Timeframe specialization

Some timeframes generate more reliable signals.

Example:

M15 may outperform M5.

### Rule 6 — Focus optimization

If:

focus_rejected events are high

then watchlist capacity may need tuning.

### Rule 7 — Safe tuning workflow

1. collect 10k+ events
2. run analytics
3. propose parameter change
4. simulate
5. deploy cautiously


## 15. VERSIONING REQUIREMENTS

Every strategy decision must be traceable to the configuration that produced it.

Required version markers:

- algo_version
- config_version
- params_hash
- engine_build_id

Example:

{
  "algo_version": "1.0.0",
  "params_hash": "9f234aa",
  "engine_build_id": "2026.03.06"
}

This allows historical reconstruction of strategy behavior.


## 16. RELATION TO CHANNELS

Strategy decision and channel distribution must remain separate.

Pipeline:

Strategy decision
↓
Distribution router
↓
Channel publication

A signal may be suppressed even if valid.

Reasons:

- duplicate signal
- tier limit reached
- channel inactive
- operational suppression

Therefore:

strategy logs must not be overwritten by distribution results.


## 17. MINIMUM ACCEPTANCE CRITERIA

The Decision Audit Layer is considered implemented when:

1. strategy decisions are logged
2. rejection reasons are logged
3. focus events are logged
4. stage promotions are logged
5. distribution decisions are logged
6. analytics aggregates can be computed

Additionally:

logs must not slow the engine.

All logging must be non-blocking.


## 18. INITIAL IMPLEMENTATION PLAN

Phase 1 — documentation

create specification document.

Phase 2 — event instrumentation

add audit events to:

- signal_engine
- focus manager
- distribution router

Phase 3 — storage

create:

/opt/binarybot/observability/decision_audit.jsonl

Phase 4 — analytics tools

create scripts to compute:

- rejection statistics
- conversion funnel
- symbol performance

Phase 5 — dashboard

optional future step:

visual analytics dashboard.

## 19. RECOMMENDED FILES TO CREATE LATER

/opt/binarybot/analytics/rejection_stats.py

/opt/binarybot/analytics/conversion_funnel.py

/opt/binarybot/analytics/symbol_performance.py

/opt/binarybot/analytics/timeframe_performance.py

/opt/binarybot/analytics/focus_analysis.py

These scripts process decision_audit logs and generate reports.


## 20. RELATION TO FUTURE PROJECT EVOLUTION

Decision audit transforms strategy development.

Without audit:

strategy evolves by guesswork.

With audit:

strategy evolves using empirical evidence.

This system allows:

- rejection pattern discovery
- strategy specialization
- parameter optimization
- research-grade signal analysis


## 21. FINAL CANONICAL STATEMENT

BinaryBot / DROPi Signals must not only emit signals.

It must also explain, record, and analyze why signals:

- appeared
- advanced
- stalled
- died
- were rejected
- were suppressed

The Decision Audit Layer enables evidence-based strategy evolution.

Without it, strategy improvement is subjective.

With it, strategy improvement becomes measurable and scientific.