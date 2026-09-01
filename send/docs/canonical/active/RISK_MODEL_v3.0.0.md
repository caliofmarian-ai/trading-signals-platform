# RISK_MODEL_v3.0.0

Canonical Name: RISK_MODEL  
Version: 3.0.0  
Status: PROPOSED COMPLETE SUCCESSOR — NOT ACTIVE CANONICAL  
Owner: BinaryBot / DROPi Signals  
Supersession Intent: `RISK_MODEL_v2.0.0.md`  
Scope: strategy risk filtering, physical-feasibility protection, instability defense, lifecycle risk constraints and capital-protection discipline

Linked proposed/current authorities:
- `CANONICAL_STRATEGY_STACK_v2.0.0.md`
- `ALGO_SPEC_v3.0.0.md`
- `SR_CORRIDOR_ENGINE_SPEC_v3.0.0.md`
- `TIME_MODEL_UNIFIED_CANON_v3.0.0.md`
- `TRADE_PHYSICS_MODEL_SPEC_v1.0.0.md`
- `DECISION_OBJECT_CANONICAL_SPEC_v2.0.0.md`
- `FSM_DECISION_ENGINE_SPEC_v2.0.0.md`
- `SIGNAL_ENGINE_EXECUTION_SPEC_v3.0.0.md`
- `SYSTEM_INVARIANTS_v3.0.0.md`
- `OBSERVABILITY_SPEC_v3.0.0.md`
- `FAILURE_RECOVERY_SPEC_v2.0.0.md`
- `SECURITY_MODEL_v2.0.0.md`
- `TELEGRAM_UX_v2.0.0.md`

---

## 0. Authority and promotion status

Until explicit atomic canonical promotion, `RISK_MODEL_v2.0.0.md` remains active.

This v3 successor exists because the active v2 document contains legacy parallel strategy mathematics (`buffer_price` and its own `t_needed` formula) that would conflict with the approved Time Model and Trade Physics successor graph.

Risk v3 therefore consumes strategy truth from its canonical owners rather than redefining it.

No runtime code change is authorized by this proposal alone.

---

## 1. Purpose

The Risk Model is the defensive strategy boundary of BinaryBot / DROPi Signals.

Its objectives are:
- capital-protection discipline;
- rejection of physically or structurally unsafe opportunities;
- volatility/instability defense;
- prevention of stale or impossible timing assumptions;
- prevention of lifecycle and duplicate exposure errors;
- explicit treatment of missing or contradictory strategy evidence;
- preservation of deterministic, auditable risk decisions.

The objective is not signal frequency.

**Rejection is protection.**

---

## 2. Core risk philosophy

The system follows:

1. Capital > Frequency
2. Quality > Quantity
3. Structure > Momentum
4. Physical Feasibility > Indicator Appearance
5. Stability > Aggression
6. Determinism > Emotion
7. Canonical Evidence > Runtime Convenience

A high indicator score or high TPS must never override a hard structural, temporal, instability, lifecycle or integrity blocker.

---

## 3. Ownership boundary

Risk consumes governed evidence; it does not become a parallel strategy engine.

Primary owners:
- ALGO: strategic orchestration and lifecycle decision policy;
- SR/Corridor: structural barriers and `available_space`;
- Time Model: `directional_effective_speed`, `t_needed`, `t_needed_adjusted`, `model_expiry`, time ratios/states;
- Trade Physics Model: deterministic physical-feasibility metrics and TPS;
- DecisionObject: complete pre-FSM strategy truth;
- FSM: operational lifecycle/focus/cooldown truth;
- Signal Engine: post-FSM candidate/execution truth.

Risk MUST NOT redefine these formulas independently.

---

## 4. Defensive layer hierarchy

An opportunity must survive all applicable defensive layers:

1. market evidence integrity;
2. structural/corridor validity;
3. directional structural space;
4. temporal feasibility;
5. instability/spike/noise policy;
6. deterministic Trade Physics readiness and physical-feasibility evidence;
7. classical strategy score/gates;
8. lifecycle/focus/cooldown/dedup protection;
9. downstream execution/distribution constraints where applicable.

Failure at a hard layer prevents trusted actionable progression.

---

## 5. Structural risk control

SR/Corridor is the authority for structural truth.

For Trade Physics v1:

`required_space = buffer_distance`

and:

`space_to_buffer_ratio = available_space / required_space`

Hard rule:

If `available_space < required_space`, the required move does not fit before the directional structural barrier.

That setup is structurally constrained and cannot become eligible merely because momentum, classical score or arithmetic TPS is high.

`buffer_price` is legacy compatibility vocabulary and MUST NOT be the primary risk term.

---

## 6. Trade-space normalization

Risk may consume the canonical normalized structural metric:

`trade_space_margin_atr = (available_space - required_space) / atr_m5`

Interpretation:
- negative -> insufficient structural room;
- near zero -> marginal/tight structural room;
- positive -> positive volatility-normalized structural room.

Risk does not independently reselect barriers or recompute corridor truth.

---

## 7. Temporal feasibility control

Risk v3 does not define a parallel `t_needed` equation.

The Time Model owns:
- `directional_effective_speed`;
- `t_needed`;
- `t_needed_adjusted`;
- `model_expiry`;
- `model_time_reach_ratio`;
- `time_to_buffer_ratio` mapping;
- `corridor_time_pressure`;
- `time_state`.

Canonical orientation:

`model_time_reach_ratio = t_needed_adjusted / model_expiry`

and, when synchronized/positive:

`time_to_buffer_ratio = model_expiry / t_needed_adjusted = 1 / model_time_reach_ratio`

If Time Model declares the setup infeasible, Risk cannot override it.

---

## 8. Directional speed risk

Gross absolute movement is not sufficient evidence of usable movement in the trade direction.

Risk consumes the canonical direction-aware speed evidence produced under Time/Trade Physics contracts, including:
- `directional_effective_speed`;
- `weighted_gross_speed` where applicable;
- `flow_efficiency`;
- `directional_speed_ratio`.

A market may be active while directional efficiency is poor.

Risk must preserve that distinction.

---

## 9. Volatility and movement stress

Trade Physics defines:

`movement_stress = required_space / atr_m5`

and:

`V = 1 / (1 + movement_stress)`

Risk consumes these values as physical-feasibility evidence.

It MUST NOT double-count an equivalent legacy energy ratio under a different name as if it were independent evidence.

---

## 10. Instability / spike defense

The existing defensive principle remains:

Severe abnormal or unstable market evidence may block/degrade actionability according to active strategy policy.

Relevant evidence may include governed spike/noise families such as:
- extreme range behavior;
- abnormal wick/body structure;
- abnormal ATR acceleration;
- discontinuous jumps;
- market-model instability state.

Trade Physics does not bypass instability defense.

If synchronized market evidence is declared `UNSTABLE`, a normal READY TPS must not be presented as if noise were absent.

---

## 11. Deterministic TPS risk role

TPS is a deterministic `[0,100]` physical-feasibility companion score.

Canonical formula ownership belongs to `TRADE_PHYSICS_MODEL_SPEC_v1.0.0.md`.

Risk rules:
- TPS does not replace `score_total`;
- TPS is not an empirical probability;
- TPS interpretation bands are not automatic PRE/CONFIRM/OPEN_NOW thresholds;
- no undocumented TPS lifecycle gate may be introduced;
- a high TPS never overrides a hard structural/time/instability/integrity blocker;
- classical score and TPS disagreement must remain visible.

Any future TPS-specific lifecycle threshold is a governed strategy change requiring ALGO/parameter/replay evidence.

---

## 12. Trade Physics readiness risk

A trusted numeric TPS requires complete synchronized evidence.

Recognized readiness families include:
- READY;
- unavailable due to structure;
- unavailable due to time;
- unavailable due to ATR/volatility evidence;
- unavailable due to speed evidence;
- blocked by unstable market;
- invalid evidence.

When Trade Physics readiness is not READY:
- TPS MUST NOT be fabricated;
- DecisionObject must expose the reason;
- the strategy must not pretend full physical feasibility was evaluated;
- exact reject/degrade semantics remain governed by ALGO/DecisionObject policy.

After Trade Physics implementation is active, incomplete mandatory Trade Physics evidence is a strategic gating condition, not a reason to silently fall back to the legacy risk formula.

---

## 13. Learned probability risk boundary

`trade_success_probability` is separate from TPS.

Risk MUST NOT consume a fabricated or unvalidated learned probability as production authority.

A learned probability may influence production behavior only when:
- a model exists;
- model/version/calibration provenance is present;
- readiness authorizes the intended usage;
- governance explicitly authorizes that decision role.

No such authority is implied merely because Trade Physics Intelligence is current-scope.

---

## 14. Classical score risk filtering

Classical score remains a separate strategy-quality truth governed by ALGO.

Risk consumes the stage thresholds and score semantics active in ALGO/parameter governance.

Risk v3 does not independently redefine score allocations or silently merge score with TPS.

Threshold hierarchy remains:

`PRE <= CONFIRM <= OPEN_NOW`

Exact values come from governed strategy/parameter truth.

---

## 15. Cooldown protection

Cooldown remains an absolute lifecycle protection where active canon requires it.

During active cooldown:
- no PRE;
- no CONFIRM;
- no OPEN_NOW.

Cooldown must survive restart and remain observable.

Risk does not bypass FSM/persistence ownership for cooldown state.

---

## 16. Focus / watchlist exposure control

The active hard limit remains maximum two focus/watchlist symbols unless future canon changes it.

Purpose:
- bound simultaneous opportunity exposure;
- prevent signal clustering;
- preserve deterministic focus governance;
- prevent lifecycle overload.

Risk consumes the canonical FSM/focus state and must not create a shadow focus model.

---

## 17. Deduplication protection

Stable opportunity/signal identity and dedup are mandatory.

Risk depends on canonical identity and lifecycle contracts to prevent:
- duplicate PRE;
- duplicate CONFIRM;
- duplicate OPEN_NOW;
- restart replay spam;
- repeated exposure to the same governed opportunity.

Deduplication must remain observable.

---

## 18. Buffer risk semantics

`buffer_distance` is the primary strategy distance term.

Larger buffer distance generally implies:
- larger required movement;
- potentially stronger noise tolerance;
- increased time/space demand.

Smaller buffer distance generally implies:
- faster required movement completion;
- potentially greater noise sensitivity.

Risk does not hardcode buffer selection outside governed parameter/ALGO ownership.

---

## 19. Expiry risk semantics

Risk consumes model/execution time from Time Model and downstream contracts.

General risk truths remain:
- too-short execution time may convert a valid thesis into an avoidable loss;
- overly long time may increase reversal exposure;
- model time and trader-facing execution time are distinct;
- expiry must not be selected by a parallel formula inside Risk.

Telemetry provides evidence for later expiry calibration; it does not rewrite the original result.

---

## 20. Failure scenarios protected against

Risk v3 explicitly protects against:
- trading into insufficient directional structural space;
- temporal infeasibility;
- high gross activity with poor directional efficiency;
- abnormal/unstable market conditions;
- incomplete mandatory Trade Physics evidence masquerading as READY;
- fabricated learned probability;
- high score or high TPS overriding hard blockers;
- duplicate/replay signal storms;
- cooldown bypass;
- focus/watchlist over-capacity;
- undocumented parallel strategy mathematics.

---

## 21. What this model does not control

This document does not define:
- broker position sizing;
- account leverage;
- broker-specific payout/slippage;
- external broker execution;
- Telegram presentation;
- distribution entitlement;
- learned model training algorithm;
- independent strategy formulas owned by ALGO/SR/Time/Trade Physics.

---

## 22. Risk escalation events

Material risk degradation must be observable.

Review/freeze triggers may include:
- repeated instability/spike rejection;
- repeated structural-space failure;
- repeated time-feasibility failure;
- Trade Physics readiness missingness spike;
- unexplained TPS distribution drift;
- sudden win-rate or signal-frequency change;
- score/TPS disagreement pattern shift;
- invariant breach;
- data/model provenance failure.

The governed response may include:
1. restrict/freeze unsafe forward behavior;
2. preserve evidence;
3. audit parameters and recent versions;
4. compare behavior against active ALGO/Trade Physics/Time/Risk canon;
5. rollback where required.

---

## 23. Observability requirement

For any material risk gate or block, evidence must identify enough context to reconstruct:
- setup/signal identity;
- risk family;
- blocker/reason;
- structural/time/Trade Physics readiness relevant to the decision;
- classical score/TPS where valid;
- lifecycle/focus/cooldown context where relevant;
- algorithm/parameter/spec version provenance.

Risk truth must not exist only as an opaque debug string.

---

## 24. Determinism requirement

Given materially identical:
- market inputs;
- canonical algorithm/model versions;
- governed parameters;
- synchronized Trade Physics evidence;
- state/lifecycle context;

the risk decision must be materially identical.

No random production risk decision is allowed.

---

## 25. Code alignment rule

Post-promotion implementation must answer:
- where structural risk consumes `available_space` and `required_space`;
- where time risk consumes canonical Time Model output instead of rederiving `t_needed`;
- where Trade Physics readiness/TPS enter pre-DecisionObject risk evaluation;
- how high TPS is prevented from bypassing hard blockers;
- how score and TPS remain separate;
- how learned probability is blocked when not authorized/ready;
- how cooldown/focus/dedup risk remains downstream-owned and auditable.

Any parallel legacy formula inside Risk/Signal Engine that contradicts promoted canon is implementation drift to remediate after canonical promotion.

---

## 26. Migration from v2

When this successor is promoted:
- `RISK_MODEL_v2.0.0.md` becomes Superseded;
- `buffer_price` risk wording is replaced by `buffer_distance` primary vocabulary;
- the local legacy `t_needed = buffer / (ATR * momentum_factor) * trend_time_adjust` formula is retired as Risk authority;
- Time Model becomes the only time-mathematics authority;
- Trade Physics physical-feasibility evidence becomes current mandatory strategy evidence;
- Risk remains defensive and does not become a second scoring engine.

Runtime changes remain a separate post-promotion implementation program.

---

## 27. Version history

| Version | Date | Description |
|---|---|---|
| 3.0.0 | 2026-09-01 | Proposed structural successor aligned with current-scope Trade Physics, directional Time Model and staged execution. Removes parallel legacy time formula and legacy primary buffer vocabulary. |
| 2.0.0 | 2026-07-12 | Active canonical version produced through canonical reconciliation. |

---

## 28. Final principle

Risk is the defensive consumer of canonical strategy truth, not an alternative source of strategy mathematics.

The system protects capital by requiring coherent structural space, time feasibility, physical feasibility, stability, score quality, lifecycle integrity and complete evidence — while refusing to let any single attractive number override a hard blocker.