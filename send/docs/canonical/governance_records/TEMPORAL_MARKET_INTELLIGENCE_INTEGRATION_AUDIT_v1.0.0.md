# TEMPORAL_MARKET_INTELLIGENCE_INTEGRATION_AUDIT_v1.0.0

Version: 1.0.0  
Status: GOVERNANCE / INTEGRATION AUDIT — SUPPORTING RECORD — NON-AUTHORITATIVE BY ITSELF  
Owner: BinaryBot / DROPi Signals  
Date: 2026-09-05  
Governance issue: `#137`  
Draft PR: `#138`  
Branch: `canon/temporal-market-behavior-intelligence-v1`  
Base main audited: `9427fad7633b279b30ab97a49656f87e8b637e59`

---

## 0. Purpose

This audit determines whether the four Owner-directed temporal-market candidates represent genuine missing canonical domains, whether they conflict with current active authorities, and what exact integration work is required before activation.

Candidate documents:

1. `MARKET_BEHAVIOR_OBSERVATION_SPEC_v1.0.0.md`
2. `TEMPORAL_MARKET_BEHAVIOR_ANALYTICS_SPEC_v1.0.0.md`
3. `STRATEGY_TRADING_WINDOW_INTELLIGENCE_SPEC_v1.0.0.md`
4. `TEMPORAL_PATTERN_VALIDATION_SPEC_v1.0.0.md`

This record does not activate them.

---

## 1. Owner requirement being preserved

The system must not learn only from signal outcomes.

It must preserve and analyze how governed market price behaves continuously across time so that the project can later determine:

- whether price behavior differs by hour, weekday, month, quarter and regime;
- whether continuation, reversal, impulse, pullback, compression, expansion, breakout and structural-reaction behavior show repeatable temporal structure;
- whether those structures are stable or accidental;
- whether a specific strategy performs better or worse than the relevant market baseline under those conditions;
- when a strategy appears favorable, neutral or unfavorable to trade;
- whether any such finding survives chronological/out-of-sample validation before it may influence production.

The Owner explicitly requires preservation of the information first so valuable evidence is not lost while later analytics and strategy calibration are still being built.

---

## 2. Active canonical graph audited

The following active authorities were reviewed as integration owners or conflict surfaces:

- `CANONICAL_MASTER_INDEX_v2.0.0.md`
- `CANONICAL_STRATEGY_STACK_v2.0.0.md`
- `SYSTEM_ARCHITECTURE_MAP_v3.0.0.md`
- `MODULE_INTERFACE_SPEC_v3.0.0.md`
- `SYSTEM_INVARIANTS_v3.0.0.md`
- `OBSERVABILITY_SPEC_v3.0.0.md`
- `OBSERVABILITY_LOGGING_SPEC_v3.0.0.md`
- `EVENT_SCHEMA_SPEC_v3.0.0.md`
- `TRADE_TEMPORAL_TELEMETRY_SPEC_v3.0.0.md`
- `PERFORMANCE_ANALYTICS_SPEC_v3.0.0.md`
- `RESEARCH_AND_LEARNING_FRAMEWORK_SPEC_v3.0.0.md`
- `STRATEGY_INTELLIGENCE_SYSTEM_v3.0.0.md`
- `AUTONOMOUS_STRATEGY_EVOLUTION_SYSTEM_v3.0.0.md`
- `STRATEGY_PARAMETER_CONTROL_SPEC_v3.0.0.md`
- `TEST_PLAN_v3.0.0.md`
- `GOVERNANCE_AND_CHANGE_CONTROL_v2.0.1.md`

The Master Index is the status authority even where promoted active files retain stale pre-promotion header wording.

---

## 3. Existing authority: Market Model

`MODULE_INTERFACE_SPEC_v3.0.0` assigns Market Model ownership over runtime market context including:

- raw-to-derived market context;
- EMA/RSI/ATR/activity/noise evidence;
- buffer-distance derivation under strategy contract;
- gross/non-directional movement context;
- direction-aware movement evidence required upstream by Time/Trade Physics where assigned there.

It also defines a `MarketModelResult` consumed by the strategy pipeline.

### Integration decision

`MARKET_BEHAVIOR_OBSERVATION_SPEC` must **not** become a competing Market Model.

The boundaries are:

### Market Model

Owns decision-time runtime interpretation needed by the live strategy.

### Market Behavior Observation

Owns continuous, replayable preservation of governed market evidence and versioned behavior-feature materialization for research/analytics independent of whether a strategy signal exists.

Market Behavior Observation may reuse raw governed provider evidence and may derive research behavior features, but it cannot silently replace the Market Model fields consumed by live strategy.

If a future validated behavior feature is proposed as a live Market Model feature, that is a separate governed Market Model / strategy change.

**Conflict status: RESOLVABLE — explicit ownership boundary required at promotion.**

---

## 4. Existing authority: Trade Temporal Telemetry

`TRADE_TEMPORAL_TELEMETRY_SPEC_v3.0.0` is explicitly post-executable / signal-conditioned.

Its canonical registration boundary is an effective executable `OPEN_NOW` and its purpose is to preserve what the market objectively did after that executable intent.

It does not collect a continuous unconditional market-history research dataset.

### Integration decision

The two domains remain distinct:

`Market Behavior Observation`
= unconditional / continuous market evidence.

`Trade Temporal Telemetry`
= signal-conditioned post-executable objective market truth.

The same governed source prices may support both where provenance permits, but semantic records, eligibility and identities remain different.

Market Behavior Observation must not create phantom telemetry trades.

Trade Temporal Telemetry must not be broadened into a continuous market recorder merely to avoid creating the missing domain.

**Conflict status: NONE after explicit boundary. New domain is justified.**

---

## 5. Existing authority: Performance Analytics

`PERFORMANCE_ANALYTICS_SPEC_v3.0.0` owns strategy/system performance analytics and already requires segmentation by dimensions including:

- symbol;
- direction;
- timeframe;
- session;
- weekday;
- volatility regime;
- trend regime;
- corridor regime;
- score/TPS bands and related strategy evidence.

It is downstream of strategy, DecisionObject, FSM, execution, telemetry and outcomes.

### Integration decision

Performance Analytics remains the authority for:

**How did Strategy/System X perform?**

`TEMPORAL_MARKET_BEHAVIOR_ANALYTICS_SPEC` is the authority candidate for:

**How did the market itself behave under temporal/context conditions, independent of Strategy X?**

Strategy Trading Window Intelligence may compare both, but cannot merge their truth domains.

**Conflict status: NONE after scope separation. New unconditional analytics domain is justified.**

---

## 6. Existing authority: Research & Learning

`RESEARCH_AND_LEARNING_FRAMEWORK_SPEC_v3.0.0` already requires:

- evidence-led research;
- time-aware validation;
- chronological/out-of-sample approaches;
- leakage protection;
- hypothesis/version lineage;
- sample/confidence discipline;
- governed experiment lifecycle;
- no direct production mutation.

### Integration decision

`TEMPORAL_PATTERN_VALIDATION_SPEC` does not replace Research & Learning.

It specializes Research discipline for the unusually high data-snooping risk created by temporal pattern searches across:

- 24 hours;
- weekdays;
- months;
- directions;
- regimes;
- sequence classes;
- multiple horizons;
- strategy versions;
- score/TPS bands.

It owns temporal-pattern-specific requirements such as:

- candidate pattern identity/version;
- discovery versus proof separation;
- overlapping future-label protection;
- temporal search-space/multiple-testing disclosure;
- chronological replication/out-of-sample validation;
- stability/drift requirements before advisory promotion.

Research & Learning remains the broader scientific workflow authority.

**Conflict status: SUBORDINATE SPECIALIZATION — valid if linked explicitly.**

---

## 7. Existing authority: Strategy Intelligence

`STRATEGY_INTELLIGENCE_SYSTEM_v3.0.0` already owns diagnostic/recommendation intelligence and may analyze symbol/session/regime effects.

It is not a signal generator and cannot silently mutate production.

### Integration decision

`STRATEGY_TRADING_WINDOW_INTELLIGENCE_SPEC` is a bounded specialized subsystem under Strategy Intelligence.

It owns the specialized question:

**When is this exact strategy/version historically better or worse matched to this market/time context relative to an explicit market/strategy baseline?**

Its initial mode is `OBSERVE`.

Later `ADVISORY` requires validated evidence.

`GOVERNED_GATE` remains future-only and requires separate promotion/change approval.

No universal numeric 0–100 suitability formula is authorized in v1 because no evidence yet establishes valid weights.

**Conflict status: SUBORDINATE SPECIALIZATION — valid if authority mode remains explicit.**

---

## 8. Existing authority: Autonomous Strategy Evolution

`AUTONOMOUS_STRATEGY_EVOLUTION_SYSTEM_v3.0.0` permits autonomous analysis/proposal workflows but forbids silent production mutation.

It requires readiness, evidence, experiment design, approval and rollback before material rollout.

### Integration decision

Validated temporal findings may eventually become Evolution inputs, but:

- a discovered time pattern is not a production proposal by itself;
- an advisory favorable/unfavorable window is not a live gate;
- a live temporal filter requires an explicit governed experiment/change;
- Owner approval and rollback remain mandatory.

**Conflict status: NONE. Existing evolution boundary reinforces new candidates.**

---

## 9. Existing authority: Event Schema and Observability

Current Event Schema v3 focuses on material system/lifecycle events such as:

- engine lifecycle;
- decision events;
- FSM transitions;
- signal execution;
- distribution/publication;
- telemetry/outcomes;
- admin/governance;
- warnings/errors.

Observability requires reconstructable market evidence for material strategy flows, but its canonical chain is setup/signal lifecycle oriented.

### Critical integration decision: raw market evidence is not the same thing as the general event stream

Continuous price observation may be high-volume.

The project must not require every tick or every retained candle to be copied into `engine_events.jsonl` merely so it can be called observable.

Canonical separation at promotion should be:

### High-volume market evidence store

Owns raw/replayable provider-derived observations and candle history used by Market Behavior Observation.

### Material observability/event stream

Owns material lifecycle/state/evidence events about the observation subsystem, for example where later specified:

- collector start/stop/degraded state;
- provider provenance change;
- market-data gap/integrity incident;
- storage/replay failure;
- dataset materialization completion/failure;
- pattern validation/advisory state transitions where governed.

Exact event names must be added only through Event Schema governance.

No new event name becomes canonical merely because this audit gives examples.

**Conflict status: REQUIRES PROMOTION-TIME INTERFACE UPDATE, not per-price event duplication.**

---

## 10. Existing authority: System Invariants

Current invariants already provide strong supporting rules including:

- documentation supremacy;
- no undocumented material change;
- determinism/version discipline;
- no fabricated learned probability;
- no future-label leakage into pre-trade features;
- no silent governed mutation;
- observability/evidence requirements.

### New invariant families required at activation

A promoted successor should add explicit non-negotiable rules for temporal market evidence:

1. **Continuous Evidence Independence** — market-behavior research data must not be limited only to strategy-selected moments.
2. **Raw Market Truth Preservation** — derived analytics cannot overwrite provider-derived raw evidence.
3. **No Fabricated Continuity** — missing observations/gaps cannot be silently interpolated as observed market truth.
4. **UTC Temporal Authority** — raw temporal grouping is reconstructable from UTC; local/session views are derived and timezone-aware.
5. **Provider Provenance Integrity** — different provider streams cannot be silently merged as one canonical raw series.
6. **Temporal Pattern Is Not Strategy Authority** — discovered/advisory temporal effects cannot become live gates without separate governed promotion.
7. **Discovery/Validation Separation** — exploratory temporal pattern discovery cannot be presented as out-of-sample proof.

Exact invariant IDs must be assigned during successor drafting/promotion, not invented as active IDs by this supporting record.

**Conflict status: REQUIRES INVARIANT SUCCESSOR UPDATE BEFORE ACTIVE LIVE-INFLUENCE; data-collection activation may reference equivalent candidate rules only after formal promotion.**

---

## 11. Canonical inventory conclusion

Current Master Index declares 43 unique active functional specifications.

The audit finds that the four candidates represent four materially distinct functions rather than simple duplicate wording:

1. continuous market observation/evidence preservation;
2. unconditional temporal market-behavior analytics;
3. strategy-specific temporal suitability intelligence;
4. temporal-pattern validation/proof discipline.

### Recommended functional inventory after full activation

`43 -> 47`

This requires a new Master Index successor/version and cannot be achieved merely by moving files into `canonical/active`.

No candidate is active until that governance step is executed.

---

## 12. Required promotion impact matrix

### 12.1 Must change for activation

- `CANONICAL_MASTER_INDEX` successor — add four functional authorities and update inventory count/hierarchy.
- `SYSTEM_ARCHITECTURE_MAP` successor — add the unconditional market-evidence and temporal-intelligence chain.
- `MODULE_INTERFACE_SPEC` successor — define Market Model versus Market Behavior Observation ownership and new downstream interfaces.
- `SYSTEM_INVARIANTS` successor — add continuous-evidence, raw-truth, UTC/provenance, anti-selection-bias and no-auto-gate invariants.
- `TEST_PLAN` successor — add observation/data-integrity/temporal-validation/strategy-window contract tests.

### 12.2 Must be reviewed and likely amended

- `OBSERVABILITY_SPEC` — add observation-subsystem provenance/health/data-quality observability without requiring per-tick generic events.
- `OBSERVABILITY_LOGGING_SPEC` — define material observation lifecycle/error evidence.
- `EVENT_SCHEMA_SPEC` — add only material new event families/states that are actually needed; do not eventize every market price by default.
- `PERFORMANCE_ANALYTICS_SPEC` — explicitly consume temporal market baselines for strategy comparison while preserving strategy-performance ownership.
- `RESEARCH_AND_LEARNING_FRAMEWORK_SPEC` — link Temporal Pattern Validation as specialized temporal proof authority.
- `STRATEGY_INTELLIGENCE_SYSTEM` — register Strategy Trading Window Intelligence as a bounded specialized subsystem.
- `AUTONOMOUS_STRATEGY_EVOLUTION_SYSTEM` — permit validated temporal findings only as governed proposal inputs.
- `GOVERNANCE_AND_CHANGE_CONTROL` — ensure any future `GOVERNED_GATE` promotion is classified as a material strategy policy change.

### 12.3 Does not need semantic ownership transfer

- `TRADE_TEMPORAL_TELEMETRY_SPEC` — remains signal-conditioned objective market truth; add cross-reference only.
- `OUTCOME_TRACKING_SPEC` — remains operational/admin outcome authority.
- `ALGO_SPEC` — no temporal gate or strategy rule is being activated now.
- `SR_CORRIDOR_ENGINE_SPEC` — structural truth remains unchanged.
- `TIME_MODEL_UNIFIED_CANON` — signal-specific timing/expiry remains unchanged.
- `TRADE_PHYSICS_MODEL_SPEC` — deterministic TPS remains unchanged.
- `STRATEGY_PARAMETER_CONTROL_SPEC` — no new temporal parameter is declared tunable by these v1 candidates.

---

## 13. Implementation priority after activation

Because the Owner's primary concern is loss of valuable evidence, the implementation order should prioritize **capture before sophisticated interpretation**.

### Phase T0 — Preservation foundation

Implement the smallest safe continuous market-evidence layer that preserves:

- provider provenance;
- symbol/timeframe/cadence identity;
- UTC timestamps;
- real observed price/candle values;
- gap/freshness/integrity state;
- durable storage/replayability;
- retention sufficient for future recomputation.

No strategy influence.

### Phase T1 — Deterministic behavior derivation

Add versioned derived features such as:

- displacement;
- ranges/volatility;
- directional persistence;
- reversal behavior;
- impulse/pullback;
- compression/expansion;
- structurally defined breakout/reaction evidence.

No predictive claim by existence.

### Phase T2 — Temporal analytics

Build UTC/hour/weekday/month/regime baselines and rolling windows.

### Phase T3 — Pattern validation

Materialize candidate identity, discovery/replication/out-of-sample state, stability and data-snooping controls.

### Phase T4 — Strategy window comparison

Compare exact strategy/version behavior against unconditional/matched market baselines.

Authority remains `OBSERVE`, later `ADVISORY` only after validation.

### Phase T5 — Future governed experiment

Only a separately approved future change may test a temporal gate in staged/shadow conditions.

Broker execution remains disabled unless governed separately.

---

## 14. Data retention principle

The project should preserve primary evidence at a resolution that supports future recomputation where provider capability, licensing, storage and operating cost permit.

A destructive policy that stores only today's chosen aggregates risks making tomorrow's research impossible.

However, this principle does not authorize unlimited uncontrolled storage.

Before runtime implementation, the implementation plan must define:

- source cadence actually available;
- expected daily storage volume;
- retention horizons;
- partitioning;
- compression;
- integrity checks;
- backup/recovery;
- provider licensing constraints;
- cost limits;
- what evidence is primary versus reproducibly derivable.

Retention is therefore governed by **maximum future research value under explicit operational constraints**, not by indiscriminate logging.

---

## 15. Time semantics conclusion

UTC is canonical raw time authority.

The system may derive:

- hour;
- weekday;
- day of month;
- ISO week;
- month;
- quarter;
- year;
- explicit market-session labels;
- `Europe/London` or other IANA timezone views.

Local/session views must preserve their derivation definition and timezone identity.

DST transitions must not cause two historically different UTC periods to be silently treated as the same raw timestamp.

---

## 16. Statistical / anti-overfitting conclusion

The Owner wants the system to identify rhythms, frequencies and patterns that may help estimate what could happen next.

That objective is admissible only through probabilistic, evidence-led research.

The audit therefore confirms these boundaries:

- descriptive recurrence is not predictive proof;
- a high percentage with small N is not strong evidence by itself;
- search-space size must be disclosed;
- discovery and final proof must be separated;
- chronological validation is mandatory;
- overlapping future horizons reduce effective independence;
- regime stability must be examined;
- strategy-version compatibility must be preserved;
- historical frequency is never certainty;
- a pattern may drift and lose advisory standing.

No fixed universal statistical threshold is invented in this canonicalization wave.

---

## 17. Immediate data-collection design requirement

Before implementation begins, a bounded implementation specification must answer:

1. Which provider-native evidence can current FINNHUB scope actually supply continuously?
2. Which resolution is genuinely observed versus derived?
3. Which M1/M5 data is already persisted and at what retention depth?
4. Which shorter-than-M1 observations are genuinely available under current provider/rate limits?
5. What stable observation/dedup identity will be used?
6. How will gaps/weekends/provider downtime be represented?
7. Where will durable market-observation data live under Railway `/data`?
8. How large is expected storage growth per day/month/year?
9. What rotation/compression can occur without destroying reproducibility?
10. How will raw observation data be joined to strategy `decision_evaluated`, telemetry and outcomes without rewriting any of them?

The implementation must inspect actual current provider/runtime contracts before answering these questions.

No capability may be assumed from the word "Finnhub" alone.

---

## 18. Activation recommendation

**CANONICAL GAP: CONFIRMED.**

**FOUR-DOMAIN MODEL: ACCEPTABLE.**

**CURRENT PR #138 STATUS SHOULD REMAIN DRAFT / TRANSITIONAL.**

Recommended next canonical step before activation:

1. review the four candidate documents against this audit;
2. add/repair explicit Market Model ownership linkage in the candidate set where needed;
3. draft promotion impact changes for the five mandatory owner documents in section 12.1;
4. perform a canon consistency review;
5. only then prepare a controlled activation PR / Master Index successor.

No runtime implementation should precede explicit activation of at least the data-collection authority and its required system/interface/invariant contracts.

---

## 19. Final authority map

```text
GOVERNED MARKET PROVIDER
        |
        +------------------------------+
        |                              |
        v                              v
MARKET MODEL                    MARKET BEHAVIOR OBSERVATION
(live strategy context)         (continuous replayable market evidence)
        |                              |
        v                              v
STRATEGY PIPELINE               TEMPORAL MARKET BEHAVIOR ANALYTICS
        |                              |
        v                              v
DECISION / FSM / SIGNAL         TEMPORAL PATTERN VALIDATION
        |                              |
        v                              |
TRADE TEMPORAL TELEMETRY               |
        |                              |
        v                              |
PERFORMANCE ANALYTICS -----------------+
        |                              |
        +--------------+---------------+
                       v
          STRATEGY TRADING WINDOW INTELLIGENCE
                       |
                       v
              RESEARCH / STRATEGY INTELLIGENCE
                       |
                       v
            GOVERNED RECOMMENDATION ONLY
                       |
                       v
          FUTURE SEPARATE OWNER-APPROVED EXPERIMENT
```

---

## 20. Final principle

The system must first preserve the market well enough to learn from it later.

It must then distinguish:

- what the market normally does;
- what the strategy selects;
- what happened after selected executable signals;
- whether a temporal effect is real and stable;
- whether that effect is actually useful for the exact strategy.

Only after those truths are separately measured and validated may temporal knowledge become a candidate for governed trading influence.
