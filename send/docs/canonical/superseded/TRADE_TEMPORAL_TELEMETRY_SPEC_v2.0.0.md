# TRADE_TEMPORAL_TELEMETRY_SPEC_v2.0.0

Version: 2.0.0  
Path: /opt/binarybot/docs/canonical/active/TRADE_TEMPORAL_TELEMETRY_SPEC_v2.0.0.md  

Linked Documents:
- /opt/binarybot/docs/canonical/active/CANONICAL_STRATEGY_STACK_v1.0.0.md
- /opt/binarybot/docs/canonical/active/TIME_MODEL_UNIFIED_CANON_v2.0.0.md
- /opt/binarybot/docs/canonical/active/OUTCOME_TRACKING_SPEC_v2.0.0.md
- /opt/binarybot/docs/canonical/active/PERFORMANCE_ANALYTICS_SPEC_v2.0.0.md
- /opt/binarybot/docs/canonical/active/DECISION_AUDIT_SPEC_v2.0.0.md
- /opt/binarybot/docs/canonical/active/OBSERVABILITY_SPEC_v2.0.0.md


Status: Active Canonical  
Path target: `/opt/binarybot/docs/canonical/active/TRADE_TEMPORAL_TELEMETRY_SPEC_v2.0.0.md`  
Supersedes: `/opt/binarybot/docs/TRADE_TEMPORAL_TELEMETRY_SPEC.md`  
Related canonical documents:
- `/opt/binarybot/docs/canonical/active/CANONICAL_STRATEGY_STACK_v1.0.0.md`
- `/opt/binarybot/docs/canonical/active/ALGO_SPEC_v2.0.0.md`
- `/opt/binarybot/docs/canonical/active/TIME_MODEL_UNIFIED_CANON_v2.0.0.md`
- `/opt/binarybot/docs/canonical/active/SR_CORRIDOR_ENGINE_SPEC_v2.0.0.md`
- `/opt/binarybot/docs/canonical/active/DECISION_OBJECT_CANONICAL_SPEC_v1.0.0.md`
- `/opt/binarybot/docs/canonical/active/FSM_DECISION_ENGINE_SPEC_v1.0.0.md`
- `/opt/binarybot/docs/canonical/active/SIGNAL_ENGINE_EXECUTION_SPEC_v2.0.0.md`
- `/opt/binarybot/docs/canonical/active/OBSERVABILITY_SPEC_v2.0.0.md`
- `/opt/binarybot/docs/canonical/active/DECISION_AUDIT_SPEC_v2.0.0.md`

---

## 1. PURPOSE

The purpose of the Trade Temporal Telemetry layer is to record the post-decision market truth lifecycle for every strategy-approved trade candidate that reaches executable state.

This document upgrades the older telemetry concept into a canonical v2.0.0 form aligned with the current architecture truths already fixed in the project:

1. `DecisionObject` is produced before FSM.
2. `Corridor Engine` is upstream of the `Time Model`.
3. Telemetry must explain not only final expiry result, but also temporal structure, execution timing quality, recovery behavior, and feedback value for optimization.

The telemetry layer exists to answer questions such as:

- Did the trade fail because the directional thesis was wrong?
- Did the trade fail because expiry was too short?
- Did the trade initially move correctly and only later reverse?
- Did the structure stay valid but timing degrade?
- Which checkpoint patterns correlate with later win or loss?
- Which combinations of score, TPS, corridor quality, and time model state produce stable outcomes?

This telemetry layer is objective market-truth instrumentation. It is not a Telegram sentiment system and it does not depend on user-reported manual execution.

---

## 2. ARCHITECTURAL POSITION

Trade Temporal Telemetry sits downstream of the strategy decision pipeline.

High-level flow:

`Market Data -> Corridor Engine -> Time Model -> DecisionObject -> FSM -> OPEN_NOW candidate -> trade registration -> temporal checkpoints -> expiry evaluation -> post-expiry evaluation -> outcome storage -> analytics`

Important implications:

- Telemetry begins only after a candidate reaches executable trade state.
- Telemetry must preserve linkage to pre-trade strategy context.
- Telemetry is not allowed to rewrite pre-trade truth; it only measures what happened after the executable event.
- Telemetry records must remain joinable with `DecisionObject`, FSM outcome, observability logs, and decision audit records.

---

## 3. TELEMETRY SCOPE

The telemetry layer applies to every signal that reaches effective executable emission.

Canonical baseline event:

- `OPEN_NOW`

Optional future executable states may also be supported if formally introduced by canonical execution documents, but until then the required baseline is:

- only `OPEN_NOW` creates a trade temporal telemetry record

This preserves a clean invariant between executable strategy intent and temporal market evaluation.

---

## 4. CORE PRINCIPLE

Every `OPEN_NOW` event emitted by the canonical execution path is treated as a virtual executed trade for analytics purposes, regardless of whether a human subscriber actually placed the trade manually. fileciteturn24file0

This rule exists because the telemetry layer measures strategy truth, not user reaction latency, broker delay, or Telegram consumption behavior. fileciteturn24file0

Consequences:

- dataset consistency is preserved
- strategy evaluation remains independent from user behavior
- time-based analytics remain comparable across symbols and sessions
- AI and research layers receive deterministic records

---

## 5. OBJECTIVES

The telemetry layer must support all of the following:

- objective expiry result determination
- mid-trade temporal health measurement
- post-expiry recovery analysis
- expiry calibration research
- failure-cause classification support
- score-to-outcome correlation analysis
- symbol-specific temporal optimization
- joinability with research, observability, intelligence, and audit layers

The layer should be useful both for direct strategy maintenance and for future AI-assisted optimization systems.

---

## 6. REQUIRED LINKAGE TO OTHER CANONICAL OBJECTS

Each telemetry record must be joinable, directly or indirectly, with the following canonical entities:

### 6.1 Decision linkage
- `signal_id`
- `decision_id` if present
- `decision_object_version`
- `decision_timestamp`

### 6.2 Strategy context linkage
- symbol
- timeframe
- direction
- score_total
- TPS
- corridor context summary
- time model summary
- feasibility or execution eligibility summary

### 6.3 FSM linkage
- fsm path summary
- final pre-open state
- transition reason into executable state

### 6.4 Audit linkage
- decision audit classification id or equivalent trace key
- rejection-family compatibility fields when relevant
- observability trace or correlation id

The exact field names may evolve, but the joinability requirement is canonical and mandatory.

---

## 7. TRADE LIFECYCLE PHASES

Each telemetry-tracked trade passes through the following phases.

### 7.1 Phase 1 — Trade Registration

Triggered when strategy emits:

- `OPEN_NOW`

Recorded immediately:

- `signal_id`
- `symbol`
- `timeframe`
- `direction`
- `entry_price`
- `open_ts`
- `expiry_minutes`
- `expiry_ts`
- `TPS`
- `score_total`
- strategy metadata snapshot
- decision/fsm trace linkage identifiers

A registry of currently open telemetry-tracked trades may be maintained for checkpoint scheduling and completion handling.

Suggested operational path retained from the older document:

- `/opt/binarybot/observability/open_trades_registry.json`

If implementation evolves, path changes are allowed only if all related canonical documents are updated consistently.

### 7.2 Phase 2 — Mid-Trade Checkpoint Layer

The first required checkpoint is:

- `MID_EXPIRY`

Definition:

`mid_expiry_ts = open_ts + (expiry_minutes / 2)`

Recorded data:

- `mid_expiry_ts`
- `mid_expiry_price`
- `mid_delta_from_entry`
- `mid_direction_correct`

Purpose:

- detect early directional health
- detect bad entry timing
- separate immediately-bad trades from late reversals
- improve expiry calibration research

### 7.3 Phase 3 — Official Expiry Evaluation

This is the canonical official result checkpoint.

Recorded data:

- `expiry_ts`
- `expiry_price`
- `result_at_expiry`

Result rules:

For `BUY`:

- `expiry_price > entry_price` -> `WIN`
- `expiry_price < entry_price` -> `LOSS`
- `expiry_price = entry_price` -> `DRAW`

For `SELL`:

- `expiry_price < entry_price` -> `WIN`
- `expiry_price > entry_price` -> `LOSS`
- `expiry_price = entry_price` -> `DRAW`

### 7.4 Phase 4 — Post-Expiry Recovery Checkpoints

Required canonical checkpoints:

- `expiry_plus_1m`
- `expiry_plus_3m`
- `expiry_plus_5m`

Recorded data:

- `post_1m_price`
- `post_3m_price`
- `post_5m_price`

Derived fields:

- `would_win_at_plus_1m`
- `would_win_at_plus_3m`
- `would_win_at_plus_5m`
- `post_expiry_recovery`

Purpose:

- detect expiry too short situations
- distinguish structural failure from temporal mismatch
- measure continuation and delayed confirmation patterns

---

## 8. CANONICAL OUTCOME EVALUATION RULES

### 8.1 Official result authority

The official trade result for baseline strategy statistics is `result_at_expiry`.

### 8.2 Recovery-aware interpretation

Post-expiry checkpoints do not rewrite the official result. They add explanatory context.

Example:

- official result = `LOSS`
- `would_win_at_plus_3m = true`

Interpretation:

- official result remains `LOSS`
- explanatory label may include `EXPIRY_TOO_SHORT` or equivalent classification

### 8.3 Draw preservation

`DRAW` is a distinct market outcome and must not be silently collapsed into `LOSS` or `WIN` in raw telemetry storage.

Derived research views may later merge classes for analytics, but raw telemetry must preserve the original state.

---

## 9. TRADE TEMPORAL DATA MODEL

Each finalized trade should be written in append-only form to a durable analytics-friendly store.

Canonical baseline storage path retained from the old spec:

- `/opt/binarybot/observability/trade_outcomes.jsonl` fileciteturn24file0

Recommended format:

- JSONL

Reason:

- append-only behavior
- efficient analytics ingestion
- compatibility with Python pipelines and later aggregation jobs fileciteturn24file0

### 9.1 Example canonical record

```json
{
  "signal_id": "EURUSD_M5_1773112320_BUY",
  "decision_id": "dec_1773112320_eurusd_buy",
  "symbol": "EUR/USD",
  "timeframe": "M5",
  "direction": "BUY",

  "entry_price": 1.08450,
  "open_ts": 1773112320,

  "expiry_minutes": 5,
  "expiry_ts": 1773112620,

  "mid_expiry_ts": 1773112470,
  "mid_expiry_price": 1.08461,
  "mid_direction_correct": true,

  "expiry_price": 1.08443,
  "result_at_expiry": "LOSS",

  "post_1m_price": 1.08472,
  "post_3m_price": 1.08491,
  "post_5m_price": 1.08502,

  "would_win_at_plus_1m": true,
  "would_win_at_plus_3m": true,
  "would_win_at_plus_5m": true,
  "post_expiry_recovery": true,

  "TPS": 41.8,
  "score_total": 47.3,

  "corridor_state": "VALID",
  "time_model_state": "ALIGNED",
  "fsm_terminal_pre_open_state": "OPEN_NOW_READY",
  "telemetry_version": "2.0.0"
}
```

---

## 10. REQUIRED FIELD GROUPS

A canonical implementation must persist the following minimum field groups.

### 10.1 Identity fields
- `signal_id`
- symbol
- timeframe
- direction

### 10.2 Timing fields
- `open_ts`
- `expiry_minutes`
- `expiry_ts`
- `mid_expiry_ts`

### 10.3 Price fields
- `entry_price`
- `mid_expiry_price`
- `expiry_price`
- `post_1m_price`
- `post_3m_price`
- `post_5m_price`

### 10.4 Outcome fields
- `result_at_expiry`
- `would_win_at_plus_1m`
- `would_win_at_plus_3m`
- `would_win_at_plus_5m`
- `post_expiry_recovery`

### 10.5 Strategy context fields
- `TPS`
- `score_total`
- corridor summary
- time model summary
- execution/fsm linkage summary

### 10.6 Versioning fields
- telemetry spec version
- decision object version if available
- source engine version if available

---

## 11. DERIVED TEMPORAL METRICS

The raw telemetry dataset must support the derivation of advanced temporal metrics.

### 11.1 Early Direction Accuracy

Measures whether the trade moved correctly from entry to mid-expiry.

Typical interpretation use:

- late entry detection
- early thesis validation
- bad timing diagnosis

### 11.2 Expiry Miss Distance

Measures how close the trade was to winning at official expiry.

Example basis:

- signed directional delta between `expiry_price` and `entry_price`

Use cases:

- expiry calibration
- minimum movement threshold tuning
- near-miss analysis

### 11.3 Post-Expiry Recovery

Detects whether a trade that officially lost later moved into a winning state at post-expiry checkpoints. This recovery logic is a key ingredient for identifying expiry mismatch rather than thesis failure. fileciteturn24file0

### 11.4 Temporal Continuation Strength

Can measure how strongly price continued in the predicted direction after expiry.

Potential use cases:

- identify under-extended expiry defaults
- detect high-conviction slow-burn patterns
- cluster symbols by continuation behavior

### 11.5 Temporal Stability Profile

Can summarize whether a trade was:

- immediately correct and stable
- late but eventually correct
- correct early then reversed
- wrong throughout
- noisy and unstable

This metric is useful for research and AI pattern extraction.

---

## 12. FAILURE CLASSIFICATION SUPPORT MODEL

If a trade results in `LOSS`, the telemetry layer should support explanatory classification rather than storing only raw failure.

The older document proposed categories such as: `INSUFFICIENT_SPACE`, `TIME_EXPIRED`, `SLOW_MARKET`, `REVERSAL_AFTER_ENTRY`, `SPIKE_NOISE`, `WRONG_DIRECTIONAL_BIAS`, `LATE_ENTRY_STRUCTURE`, and `EXPIRY_TOO_SHORT`. fileciteturn24file0

In v2.0.0, these remain valid directional examples, but classification must be tied to canonical evidence inputs, including:

- space metrics
- corridor quality
- time model timing state
- mid-expiry behavior
- post-expiry recovery checkpoints
- volatility and spike context
- direction correctness at multiple phases

Important rule:

Telemetry classification is explanatory and analytic. It must not falsify the official expiry result.

---

## 13. DATA USAGE DOMAINS

Telemetry output is intended for the following domains.

### 13.1 Strategy calibration
- TPS threshold tuning
- expiry optimization
- entry timing refinement
- buffer or feasibility threshold refinement

### 13.2 Symbol performance analytics
Examples:
- best expiry family by symbol
- recovery-prone symbols
- symbols with frequent early reversal patterns

### 13.3 Score bucket analysis
Examples:
- winrate by `score_total` band
- delayed recovery rate by score band
- corridor-quality versus outcome stability

### 13.4 Time-model research
Examples:
- which time states produce clean early confirmation
- which states produce delayed success
- where expiry mismatch is structurally concentrated

### 13.5 AI and intelligence systems
Telemetry is a foundational truth source for:

- research loops
- intelligence layers
- autonomous adaptation proposals
- statistically justified policy upgrades

---

## 14. DATA INTEGRITY RULES

The telemetry layer must follow strict rules.

### Rule 1 — One executable event, one telemetry outcome chain

Every canonical `OPEN_NOW` must produce exactly one final telemetry outcome record, even if intermediate checkpoint writes are retried. fileciteturn24file0

### Rule 2 — Independence from Telegram feedback

Telemetry truth must remain independent from Telegram user reactions, votes, screenshots, or manual reports. fileciteturn24file0

### Rule 3 — Market feed authority

Prices used for evaluation must come from the strategy market data authority, not from user broker screenshots or external anecdotal sources. fileciteturn24file0

### Rule 4 — Raw truth preservation

Raw timestamps, raw prices, and raw official result fields must remain preserved even when derived labels are added later.

### Rule 5 — Joinability preservation

A telemetry record that cannot be linked back to its strategy context is incomplete and should be marked degraded or invalid for advanced analytics.

---

## 15. PERFORMANCE AND STORAGE CONSIDERATIONS

The system must support high-volume longitudinal datasets.

The previous document estimated a scale of roughly `10,000 - 100,000 trades`; this remains a reasonable baseline planning range for append-only telemetry storage. fileciteturn24file0

Recommended baseline design:

- JSONL append-only storage for raw trade outcomes
- optional registry for open trades
- optional downstream aggregation jobs for batch analytics
- optional compression/rotation policy when scale grows

The raw telemetry layer should remain simple, durable, and analytics-friendly.

---

## 16. OBSERVABILITY AND AUDIT INTEGRATION

Trade Temporal Telemetry must integrate with:

- observability logs
- decision audit
- performance analytics
- outcome tracking
- research framework
- intelligence systems

This means telemetry should expose enough stable identifiers so that analysts can reconstruct:

- what the engine believed before entry
- why the engine allowed the trade
- what the market did during the trade
- whether expiry timing was appropriate
- whether future policy changes are justified

---

## 17. FUTURE EXTENSIONS

The older document listed future extensions such as:

- Maximum Favorable Excursion (MFE)
- Maximum Adverse Excursion (MAE)
- Full Trade Price Path fileciteturn24file0

These remain desirable and are now formally grouped as optional upgrade tracks.

### 17.1 MFE
Best price reached during trade window.

### 17.2 MAE
Worst adverse move during trade window.

### 17.3 Full Price Path Capture
Optional higher-resolution path telemetry for research-heavy modes.

### 17.4 Multi-checkpoint adaptive telemetry
Future versions may add additional checkpoints based on expiry length or symbol behavior.

### 17.5 AI-ready feature extraction
Future versions may automatically derive feature vectors for intelligence and optimization layers.

---

## 18. UPGRADE PROPOSALS INTRODUCED IN V2.0.0

To align this spec with the broader upgraded architecture, the following additions are now recommended.

### 18.1 DecisionObject snapshot linkage
Persist a compact snapshot of the pre-FSM decision context so temporal analytics can directly relate outcome to upstream reasoning quality.

### 18.2 Corridor-to-time attribution fields
Store enough context to determine whether losses cluster more strongly around corridor weakness or around time-state degradation.

### 18.3 Execution latency quality field
Even for virtual trades, the engine may later record internal emission-to-registration latency for system health diagnostics.

### 18.4 Recovery pattern taxonomy
Introduce normalized labels such as:
- `NO_RECOVERY`
- `RECOVERED_AT_1M`
- `RECOVERED_AT_3M`
- `RECOVERED_AT_5M`
- `EARLY_CORRECT_THEN_REVERSED`

### 18.5 Temporal quality score
A derived composite score can later summarize temporal behavior quality independent of official expiry result.

---

## 19. IMPLEMENTATION GUIDANCE

Implementation should proceed conservatively.

Recommended order:

1. guarantee one-record-per-OPEN_NOW invariant
2. persist baseline registration and expiry fields
3. add `MID_EXPIRY`
4. add post-expiry checkpoints
5. add derived recovery fields
6. add classification support fields
7. add research/AI enrichment fields only after raw truth is stable

This avoids mixing raw collection problems with advanced interpretation layers.

---

## 20. NON-GOALS

This document does not define:

- Telegram user feedback schemas
- broker execution reconciliation
- paid-member subjective signal reviews
- manual trade journaling UX
- front-end dashboard design details

Those may consume telemetry outputs, but they are not part of the telemetry truth layer itself.

---

## 21. SUMMARY

The Trade Temporal Telemetry layer upgrades trade evaluation from simple expiry win/loss accounting into a full temporal market-truth system.

Instead of learning only from final result, the strategy can learn from:

- entry timing
- mid-trade health
- expiry accuracy
- post-expiry continuation
- recovery behavior
- failure mode evidence
- score and structure correlation

This creates the canonical data foundation for:

- better expiry calibration
- stronger observability
- deeper research
- AI-assisted optimization
- long-term statistical robustness

In canonical v2.0.0, telemetry is no longer just a results log. It is a strategic truth instrument for understanding how and why executable decisions behave over time.

## 18. Adaptive Activity Telemetry

This section absorbs bounded content from ADAPTIVE_ACTIVITY_GATE_SPEC.md.

### 18.1 Telemetry scope
Telemetry may include normalized activity ratio, volatility reference scale, gate outcome, and any downstream effect on actionability.

### 18.2 Observability purpose
These fields support research, diagnostics, and future refinement without creating a parallel strategy truth source.
