# DECISION_AUDIT_SPEC_v2.0.0

Version: 2.0.0  
Status: Active Canonical  
Path: /opt/binarybot/docs/canonical/active/DECISION_AUDIT_SPEC_v2.0.0.md  

Linked Documents:
- /opt/binarybot/docs/canonical/active/DECISION_OBJECT_CANONICAL_SPEC_v1.0.0.md
- /opt/binarybot/docs/canonical/active/FSM_DECISION_ENGINE_SPEC_v1.0.0.md
- /opt/binarybot/docs/canonical/active/SR_CORRIDOR_ENGINE_SPEC_v2.0.0.md
- /opt/binarybot/docs/canonical/active/TIME_MODEL_UNIFIED_CANON_v2.0.0.md
- /opt/binarybot/docs/canonical/active/OBSERVABILITY_SPEC_v2.0.0.md
- /opt/binarybot/docs/canonical/active/OBSERVABILITY_LOGGING_SPEC_v2.0.0.md
- /opt/binarybot/docs/canonical/active/EVENT_SCHEMA_SPEC_v2.0.0.md
- /opt/binarybot/docs/canonical/active/FAILURE_RECOVERY_SPEC_v2.0.0.md
- /opt/binarybot/docs/canonical/active/OUTCOME_TRACKING_SPEC_v2.0.0.md
- /opt/binarybot/docs/canonical/active/PERFORMANCE_ANALYTICS_SPEC_v2.0.0.md


## 1. PURPOSE

This document defines the canonical **Decision Audit Layer** for BinaryBot / DROPi Signals.

The purpose of this layer is to record, explain, correlate, aggregate, and later analyze **why a candidate was promoted, rejected, delayed, stalled, killed, suppressed, or never reached the final `OPEN_NOW` stage**.

This is not a cosmetic analytics feature.

This is a core architectural layer used for:

- strategy learning
- rejection analysis
- parameter tuning
- focus/watchlist optimization
- signal lifecycle observability
- post-mortem analysis of dead candidates and dead signals
- safe iteration of scoring and gates
- evidence-based improvement of the strategy
- downstream telemetry correlation
- downstream reconciliation and analytics

Without this layer, the system can only answer:

- “a PRE appeared”
- “an OPEN_NOW did not appear”

With this layer, the system must be able to answer:

- why a candidate appeared
- why a PRE appeared
- why a PRE did not become CONFIRM
- why a CONFIRM did not become OPEN_NOW
- which gate killed the candidate or signal
- whether the candidate was rejected due to score, spike, SR, feasibility, focus pressure, cooldown, dedup, or routing constraints
- whether the same symbol repeatedly dies for the same reason
- whether a parameter change improved or degraded the conversion pipeline
- whether the system is suffering from strategic friction or only operational suppression

This specification upgrades the project from a simple signal emission engine to an **observable, learnable, and auditable strategy system**.

---

## 2. CANONICAL POSITION IN THE ARCHITECTURE

Decision Audit is a **root observability truth layer**.

It is not a downstream dashboard.
It is not a cosmetic admin report.
It is not a community feedback feature.
It is not an outcome-truth replacement layer.

It is the canonical upstream record of **what the strategy decided and why**.

### 2.1 Canonical upstream/downstream placement

Decision Audit sits:

- downstream of strategy evaluation
- downstream of `DecisionObject` production
- upstream of FSM lifecycle handling
- upstream of temporal telemetry correlation
- upstream of outcome reconciliation
- upstream of performance analytics
- upstream of research and learning
- upstream of strategy intelligence views
- upstream of autonomous evolution suggestions

### 2.2 Canonical architectural truths enforced by this document

This specification is written under the following canonical truths:

- `DecisionObject` is produced before FSM.
- `Corridor Engine` is before `Time Model` in the strategic pipeline.
- Strategy decision truth must remain separate from distribution truth.
- Strategy decision truth must remain separate from telemetry truth.
- Strategy decision truth must remain separate from manual/admin outcome reconciliation.
- Intelligence and AI layers are downstream analytical consumers, not runtime decision authorities.

### 2.3 Core question answered by Decision Audit

Decision Audit answers:

**What did the strategy decide, at what stage, and for what reason?**

It does **not** answer by itself:

- what the market objectively did later
- what the operator manually reconciled later
- whether production strategy should automatically mutate

Those belong to downstream layers.

---

## 3. SCOPE

This specification applies to the full signal decision pipeline, including:

- wide scan
- candidate detection
- structural qualification
- corridor qualification
- time model qualification
- score computation
- gate evaluation
- focus/watchlist selection
- PRE stage
- CONFIRM stage
- OPEN_NOW stage
- distribution routing decisions linked to valid or blocked signals
- signal death after partial promotion
- post-decision observability linkage for downstream analytics

This document does **not** replace the active canonical documents governing strategy logic, time logic, execution logic, or observability storage.
Instead, it defines the **decision audit contract** that links strategy decisions into the larger learning loop.

This document is conceptually aligned with the active canonical architecture, especially:

- strategy stack and strategy execution canon
- time model canon
- corridor engine canon
- signal execution canon
- observability canon
- downstream telemetry, reconciliation, analytics, and research layers

---

## 4. DESIGN PRINCIPLES

### 4.1 Strategy quality is single and universal

The system must not define different signal quality standards for FREE, BASIC, PRO, or ELITE.

Signal quality is determined only by:

- market data
- strategy logic
- structure
- corridor qualification
- time qualification
- scoring
- gates
- focus policy
- execution timing

Channel routing is an operational layer, not a quality layer.

### 4.2 Rejections must be explicit, not inferred

If a candidate or signal dies, the system must log the reason directly.

The system must never require operators to infer cause by reading raw code, comparing logs manually, or guessing from absence of output.

### 4.3 Every major decision point must be observable

The strategy must log all meaningful transitions and all meaningful rejections.

This includes both positive and negative outcomes.

### 4.4 Learning must be based on data, not impressions

Any future parameter change should be justified by aggregated decision audit evidence, not by isolated anecdotes.

### 4.5 The audit layer must be production-safe

The audit system must not:

- block engine progress
- crash the engine when logging fails
- silently corrupt logs
- generate unbounded noisy spam without structure

### 4.6 Audit truth must not be overwritten by downstream interpretation

Later telemetry, operator input, or analytics interpretation must never overwrite what the strategy actually decided at decision time.

### 4.7 Audit events must be correlation-ready

Decision audit must be designed from the start to link safely with:

- temporal telemetry
- distribution events
- FSM events
- manual/admin reconciliation
- analytics summaries
- experiment reports

---

## 5. HIGH-LEVEL OBJECTIVE

The Decision Audit Layer must answer the following classes of questions.

### 5.1 Detection questions

- Which symbols produce the most meaningful candidates?
- Which symbols rarely reach structural or corridor qualification?
- At what times do viable candidates appear?

### 5.2 Rejection questions

- Do most candidates die because of score?
- Do most candidates die because of corridor structure or SR gate?
- Do most candidates die because of spike filter?
- Do most candidates die because of feasibility?
- Do most candidates die because focus/watchlist is full?
- Do most candidates die because another symbol already occupies focus?
- Do most candidates die before PRE, between PRE and CONFIRM, or between CONFIRM and OPEN_NOW?

### 5.3 Promotion questions

- What percentage of candidates become PRE?
- What percentage of PRE becomes CONFIRM?
- What percentage of CONFIRM becomes OPEN_NOW?
- Which symbols convert best?
- Which symbols stall at PRE but never confirm?

### 5.4 Operational questions

- Which valid signals are later suppressed at distribution level?
- Are dedup rules suppressing too aggressively?
- Are routing limits preventing visibility of otherwise valid signals?
- Are strategy-valid signals being blocked by operational constraints rather than strategic weakness?

### 5.5 Research questions

- If threshold `open` is reduced from 80 to 75, how many additional OPEN_NOW events appear?
- If `sr_gate` is softened, what is the projected increase in candidate flow?
- If spike rejection is relaxed, does winrate degrade or improve?
- Are focus constraints creating false negatives?
- Are corridor or time-model gates too restrictive for specific symbols or sessions?

---

## 6. DECISION LIFECYCLE MODEL

The canonical decision lifecycle is:

```text
WIDE_SCAN
  ↓
CANDIDATE_DETECTED
  ↓
STRUCTURE / CONTEXT QUALIFICATION
  ↓
CORRIDOR QUALIFICATION
  ↓
TIME MODEL QUALIFICATION
  ↓
DECISION_OBJECT_PRODUCED
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
DISTRIBUTION_DECISION
  ↓
DOWNSTREAM TELEMETRY / RECONCILIATION / ANALYTICS
```

At any step, a candidate or promoted signal may die.
Every death point must be auditable.

### 6.1 Canonical rule about FSM

Decision Audit begins **before FSM**.

FSM handles downstream state lifecycle progression after the strategy has already produced a decision object and corresponding decision truth.

Therefore:

- Decision Audit is not a subset of FSM
- FSM is not the authority for initial strategy reasoning
- both may be correlated, but they must remain conceptually distinct

---

## 7. CORE CONCEPTS

### 7.1 Candidate

A candidate is a symbol-direction-timeframe-candle evaluation unit under consideration before or during signal progression.

Canonical candidate identity includes:

- `symbol`
- `direction`
- `timeframe`
- `candle_ts`
- `candidate_id`
- optional `signal_id` if already assigned

### 7.2 DecisionObject

A `DecisionObject` is the structured strategy output produced before FSM.
It represents the strategy’s current evaluated conclusion for a candidate at a given evaluation moment.

Decision Audit must be able to capture the resulting truth emitted by this object.

### 7.3 Decision

A decision is the structured result returned by the strategy for a candidate at a given evaluation moment.

Decision kinds may include:

- `NO_SIGNAL`
- `PRE`
- `CONFIRM`
- `OPEN_NOW`
- `REJECT`

### 7.4 Rejection

A rejection is any event where a candidate fails to progress or is explicitly blocked.

A rejection is not limited to full candidate death. It also includes:

- failing structural qualification
- failing corridor qualification
- failing time qualification
- failing to enter focus
- failing to upgrade from PRE to CONFIRM
- failing to upgrade from CONFIRM to OPEN_NOW
- failing publication due to operational limits or dedup

### 7.5 Decision Audit Event

A Decision Audit Event is a structured observability event describing:

- what was evaluated
- what the strategy concluded
- why it concluded that
- what gate(s) passed or failed
- what stage the candidate was in
- what happened next
- how this event can be linked downstream

### 7.6 Correlation identity

Decision Audit must support stable correlation across layers.

Recommended canonical linkage identifiers:

- `candidate_id`
- `decision_audit_id`
- `correlation_id`
- `signal_id` when assigned
- `run_id`

---

## 8. AUDIT EVENT CLASSES

The system must support at least the following event classes.

### 8.1 `candidate_detected`

Emitted when a symbol becomes a meaningful evaluation candidate.

Purpose:

- mark symbol entry into serious evaluation
- support later conversion metrics
- support upstream funnel metrics

### 8.2 `decision_evaluated`

Emitted after structure, corridor, time, scoring, and gates are computed, even if final kind is `NO_SIGNAL`.

Purpose:

- preserve decision evidence
- expose score and gate statuses
- preserve pre-FSM strategic truth

### 8.3 `decision_rejected`

Emitted when the final evaluation blocks promotion or blocks a candidate entirely.

Purpose:

- explicit rejection taxonomy
- analytics by cause
- root-cause learning

### 8.4 `focus_entered`

Emitted when a symbol is added to watchlist/focus.

### 8.5 `focus_rejected`

Emitted when a symbol deserved escalation but could not enter focus.

Typical reasons:

- watchlist full
- lower priority than existing focus symbols
- cooldown conflict
- duplicate focus symbol
- stale candidate

### 8.6 `stage_promoted`

Emitted when a signal transitions:

- `NO_SIGNAL -> PRE`
- `PRE -> CONFIRM`
- `CONFIRM -> OPEN_NOW`

### 8.7 `stage_killed`

Emitted when a signal that already had a stage loses viability.

Examples:

- PRE dies before CONFIRM
- CONFIRM dies before OPEN_NOW
- OPEN_NOW withheld due to operational constraints

### 8.8 `distribution_decision`

Emitted when the router decides:

- published
- suppressed duplicate
- blocked by tier or route limit
- blocked by inactive channel state
- blocked by operational policy

### 8.9 `outcome_linked`

Emitted when later telemetry or reconciliation records are linked to a prior signal or candidate.

Canonical rule:
this event links downstream truth but does not overwrite original decision truth.

---

## 9. CANONICAL REJECTION TAXONOMY

The following rejection reasons are canonical baseline reasons.

Implementations may extend them, but must not change existing meanings without taxonomy version update.

### 9.1 Taxonomy governance fields

Every rejection-capable event should support:

- `rejection_family`
- `rejected_reason`
- `rejection_taxonomy_version`

### 9.2 Score-based rejections

- `score_pre_fail`
- `score_confirm_fail`
- `score_open_fail`

Meaning:
score did not reach stage threshold.

### 9.3 Structural / gate-based rejections

- `spike_reject`
- `sr_reject`
- `feasibility_reject`
- `trend_reject`
- `structure_reject`
- `buffer_reject`
- `expiry_reject`
- `corridor_reject`
- `time_model_reject`

### 9.4 Focus/watchlist rejections

- `focus_not_required_yet`
- `focus_full`
- `focus_priority_lost`
- `focus_duplicate`
- `focus_cooldown_active`
- `focus_state_missing`
- `focus_state_invalid`

### 9.5 Lifecycle drop reasons

- `pre_stalled`
- `confirm_stalled`
- `open_window_expired`
- `signal_invalidated_by_new_candle`
- `direction_flipped`
- `momentum_lost`
- `trend_changed`

### 9.6 Operational block reasons

These are not strategic invalidation reasons.
They are operational suppression reasons and must be kept analytically distinguishable.

- `distribution_limit_reached`
- `distribution_channel_inactive`
- `distribution_duplicate`
- `distribution_policy_block`
- `distribution_error`

### 9.7 Data / integrity reasons

- `missing_candles`
- `invalid_candle_shape`
- `market_api_error`
- `adapter_validation_failed`
- `state_corruption`
- `unknown_error`

### 9.8 Observability / audit infrastructure reasons

These reasons describe observability failure, not strategic failure.

- `observability_log_failed`
- `audit_schema_invalid`
- `audit_write_degraded`

---

## 10. REQUIRED AUDIT FIELDS

Every audit-capable decision event must include the following minimum fields unless explicitly not applicable.

## 10.1 Identity

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

## 10.2 Correlation identity

- `candidate_id`
- `decision_audit_id`
- `correlation_id`
- `signal_id` (nullable before assignment)

## 10.3 Candidate identity

- `symbol`
- `direction`
- `timeframe`
- `candle_ts`

## 10.4 Decision data

- `decision_kind`
- `decision_origin_stage`
- `score_total`
- `buffer_mode`
- `buffer_price`
- `expiry_minutes`

## 10.5 Structural / gate data

- `corridor_ok`
- `time_model_ok`
- `spike_ok`
- `sr_ok`
- `feasibility_ok`
- `trend_ok`
- `structure_ok`

## 10.6 Focus / state data

- `mode`
- `watchlist_size`
- `watchlist_symbols`
- `focus_entered`
- `focus_reason`
- `cooldown_active`

## 10.7 Rejection data

- `rejection_family`
- `rejected_reason`
- `rejection_stage`
- `rejection_taxonomy_version`
- `rejection_details`

## 10.8 Distribution data

- `channel`
- `channel_limit`
- `tier_state`
- `publish_decision`
- `was_duplicate`

## 10.9 Version traceability

- `algo_version`
- `config_version`
- `params_hash`
- `engine_build_id`

---

## 11. OPTIONAL HIGH-VALUE FIELDS

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
- `corridor_id`
- `time_window_class`
- `regime_hint`
- `decision_notes`

---

## 12. STORAGE CONTRACT

### 12.1 Primary log file

A dedicated file must exist:

`/opt/binarybot/observability/decision_audit.jsonl`

This file is the canonical audit stream for strategy decision truth.

### 12.2 Existing logs remain valid

Existing logs remain in place as complementary observability streams.

Examples may include:

- engine events
- FSM events
- distribution events
- error events
- admin proof events

The new audit layer must complement them, not replace them.

### 12.3 Mirroring rule

High-value audit events may also be mirrored into other observability streams if useful, but `decision_audit.jsonl` remains the canonical source for decision-learning analytics.

### 12.4 Write safety

Audit writing must be:

- append-only
- line-delimited JSON
- robust to partial failure
- non-blocking to engine progression

### 12.5 Canonical non-overwrite rule

No downstream consumer may retroactively rewrite original decision audit truth.
Downstream layers may only attach linked records.

---

## 13. EVENT EXAMPLES

### Example: `candidate_detected`

```json
{
  "event_type": "candidate_detected",
  "ts_utc": "2026-03-06T11:02:14Z",
  "candidate_id": "EURUSD_SELL_M15_1772800000",
  "correlation_id": "corr_9f2d11",
  "symbol": "EURUSD",
  "direction": "SELL",
  "timeframe": "M15",
  "candle_ts": 1772800000,
  "candidate_rank_among_symbols": 3,
  "focus_rank": null,
  "score_total": 38,
  "corridor_ok": true,
  "time_model_ok": true,
  "trend_ok": true,
  "spike_ok": true,
  "sr_ok": true,
  "feasibility_ok": true
}
```

### Example: `decision_rejected`

```json
{
  "event_type": "decision_rejected",
  "ts_utc": "2026-03-06T11:02:17Z",
  "candidate_id": "EURUSD_SELL_M15_1772800000",
  "decision_audit_id": "da_001992",
  "correlation_id": "corr_9f2d11",
  "symbol": "EURUSD",
  "direction": "SELL",
  "timeframe": "M15",
  "decision_kind": "NO_SIGNAL",
  "decision_origin_stage": "PRE_GATE",
  "score_total": 36,
  "rejection_family": "score",
  "rejected_reason": "score_pre_fail",
  "rejection_taxonomy_version": "1.0.0",
  "corridor_ok": true,
  "time_model_ok": true,
  "trend_ok": true,
  "spike_ok": true,
  "sr_ok": true,
  "feasibility_ok": true
}
```

### Example: `focus_entered`

```json
{
  "event_type": "focus_entered",
  "candidate_id": "EURUSD_SELL_M15_1772800000",
  "correlation_id": "corr_9f2d11",
  "symbol": "EURUSD",
  "direction": "SELL",
  "timeframe": "M15",
  "watchlist_size": 2,
  "watchlist_symbols": ["EURUSD", "GBPUSD"]
}
```

### Example: `stage_promoted`

```json
{
  "event_type": "stage_promoted",
  "candidate_id": "EURUSD_SELL_M15_1772800000",
  "signal_id": "sig_20260306_110217_EURUSD_SELL",
  "correlation_id": "corr_9f2d11",
  "symbol": "EURUSD",
  "direction": "SELL",
  "stage_from": "PRE",
  "stage_to": "CONFIRM",
  "score_total": 66
}
```

### Example: `distribution_decision`

```json
{
  "event_type": "distribution_decision",
  "candidate_id": "EURUSD_SELL_M15_1772800000",
  "signal_id": "sig_20260306_110217_EURUSD_SELL",
  "correlation_id": "corr_9f2d11",
  "symbol": "EURUSD",
  "stage": "OPEN_NOW",
  "channel": "FREE",
  "publish_decision": "SUPPRESSED",
  "rejection_family": "operational",
  "rejected_reason": "distribution_limit_reached",
  "tier_state": "ACTIVE"
}
```

---

## 14. AGGREGATIONS REQUIRED

Analytics systems must compute the following aggregates.

### 14.1 Rejection counts by reason

Example table:

| reason | count |
|------|------|
| score_pre_fail | 420 |
| spike_reject | 120 |
| sr_reject | 80 |
| feasibility_reject | 90 |

Purpose:
identify dominant rejection causes.

### 14.2 Conversion funnel

Candidate -> PRE -> CONFIRM -> OPEN_NOW

Example:

| stage | count |
|------|------|
| candidate | 10,000 |
| PRE | 1,200 |
| CONFIRM | 450 |
| OPEN_NOW | 220 |

This reveals where candidates die.

### 14.3 Symbol performance

| symbol | candidates | PRE | CONFIRM | OPEN |
|------|------|------|------|------|
| EURUSD | 1000 | 120 | 60 | 32 |
| BTCUSD | 900 | 200 | 100 | 45 |

### 14.4 Timeframe performance

| timeframe | candidates | PRE | OPEN |
|------|------|------|------|
| M5 | 5000 | 400 | 120 |
| M15 | 3500 | 700 | 400 |

### 14.5 Focus analytics

| metric | value |
|------|------|
| average_focus_size | 1.7 |
| focus_rejections | 340 |
| focus_duplicates | 120 |

Focus analytics reveals if the engine is starved by focus constraints.

### 14.6 Strategic vs operational suppression split

Analytics must distinguish between:

- strategically rejected candidates
- strategically valid but operationally suppressed signals
- observability-degraded records

This distinction is mandatory for correct tuning.

---

## 15. STRATEGY LEARNING RULES

Decision audit logs must support controlled strategy improvement.

### Rule 1 — No tuning without data

Strategy parameters must not be changed based on intuition alone.

Changes must reference:

- rejection statistics
- conversion funnel
- symbol distribution
- stage-specific bottlenecks

### Rule 2 — Gate analysis

Every gate must be evaluated by rejection frequency.

Example:

`spike_reject rate = 17%`

If rejection exceeds acceptable thresholds, spike detection may be too aggressive.

### Rule 3 — Score threshold tuning

If:

`PRE conversion rate < expected baseline`

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

`focus_rejected` events are high

then watchlist capacity may need tuning.

### Rule 7 — Safe tuning workflow

1. collect sufficiently large event volume
2. run analytics
3. propose parameter change
4. simulate or branch-test
5. deploy cautiously with audit continuity

---

## 16. RELATION TO DOWNSTREAM LAYERS

### 16.1 Relation to temporal telemetry

Decision Audit records what the strategy decided and why.

Temporal Telemetry records what the market objectively did later.

Telemetry must not overwrite decision truth.

### 16.2 Relation to outcome reconciliation

Outcome reconciliation records operational/manual/broker-side reality and discrepancy handling.

Outcome reconciliation must not overwrite decision truth.

### 16.3 Relation to performance analytics

Performance analytics aggregates decision truth, telemetry truth, and reconciled operational truth into metrics and diagnostics.

### 16.4 Relation to research and learning

Research consumes audit evidence to generate hypotheses, experiments, and improvement proposals.

### 16.5 Relation to intelligence and AI

Intelligence and AI are downstream consumers.
They may interpret and propose, but they may not retroactively alter original audit truth.

---

## 17. RELATION TO CHANNELS AND DISTRIBUTION

Strategy decision and channel distribution must remain separate.

Pipeline:

```text
Strategy decision truth
  ↓
Distribution router
  ↓
Channel publication / suppression
```

A signal may be suppressed even if strategically valid.

Reasons may include:

- duplicate signal
- tier limit reached
- channel inactive
- operational suppression

Therefore:

- strategy truth must not be overwritten by distribution results
- operational suppression must remain visible for analytics
- routing constraints must not be misread as strategy weakness

---

## 18. MINIMUM ACCEPTANCE CRITERIA

The Decision Audit Layer is considered implemented when:

1. candidate and strategy decisions are logged
2. rejection reasons are logged
3. focus events are logged
4. stage promotions are logged
5. distribution decisions are logged
6. analytics aggregates can be computed
7. correlation IDs exist for downstream linkage
8. strategic vs operational vs observability failure classes are distinguishable

Additionally:

- logs must not slow the engine
- all logging must be non-blocking
- original decision truth must remain append-only and non-overwritten

---

## 19. INITIAL IMPLEMENTATION PLAN

### Phase 1 — documentation

Finalize this specification.

### Phase 2 — event instrumentation

Add audit events to the strategy decision path, focus manager, and distribution router.

### Phase 3 — storage

Create:

`/opt/binarybot/observability/decision_audit.jsonl`

### Phase 4 — analytics tools

Create scripts to compute:

- rejection statistics
- conversion funnel
- symbol performance
- timeframe performance
- focus analysis
- strategic vs operational suppression split

### Phase 5 — dashboard

Optional future step:

visual analytics dashboard and admin diagnostic views.

---

## 20. RECOMMENDED FILES TO CREATE LATER

- `/opt/binarybot/analytics/rejection_stats.py`
- `/opt/binarybot/analytics/conversion_funnel.py`
- `/opt/binarybot/analytics/symbol_performance.py`
- `/opt/binarybot/analytics/timeframe_performance.py`
- `/opt/binarybot/analytics/focus_analysis.py`
- `/opt/binarybot/analytics/suppression_split_analysis.py`

These scripts process decision audit logs and generate reports.

---

## 21. RELATION TO FUTURE PROJECT EVOLUTION

Decision Audit transforms strategy development.

Without audit:

strategy evolves by guesswork.

With audit:

strategy evolves using empirical evidence.

This system allows:

- rejection pattern discovery
- strategy specialization
- parameter optimization
- focus-capacity optimization
- corridor and time-model diagnostics
- research-grade signal analysis
- safer, evidence-backed experimentation

---

## 22. FINAL CANONICAL STATEMENT

BinaryBot / DROPi Signals must not only emit signals.

It must also explain, record, and analyze why candidates and signals:

- appeared
- advanced
- stalled
- died
- were rejected
- were operationally suppressed
- were later correlated downstream

The Decision Audit Layer is the canonical upstream truth for strategy reasoning.

Without it, strategy improvement is subjective.

With it, strategy improvement becomes measurable, reconstructible, and scientific.

## 23. Adaptive Activity Gate Audit Fields

This section absorbs bounded content from ADAPTIVE_ACTIVITY_GATE_SPEC.md.

### 23.1 Audit requirement
Decision audit records should capture whether adaptive activity gating contributed to pass/fail eligibility.

### 23.2 Recommended fields
Recommended fields include normalized activity ratio, reference volatility context, gate decision, and rejection reason where applicable.

### 23.3 Rejection clarity
If a setup is rejected due to insufficient normalized activity, the rejection must be distinguishable from corridor failure, timing failure, score insufficiency, or operator veto.
