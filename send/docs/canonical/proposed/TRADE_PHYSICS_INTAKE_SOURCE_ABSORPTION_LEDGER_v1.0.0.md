# TRADE_PHYSICS_INTAKE_SOURCE_ABSORPTION_LEDGER_v1.0.0

Version: 1.0.0  
Status: PROPOSED SUPPORTING CANONICAL GOVERNANCE RECORD — NOT ACTIVE CANONICAL  
Owner: BinaryBot / DROPi Signals  
Date: 2026-09-01

## 1. Purpose

This ledger proves that the complete Trade Physics family currently stored under `send/docs/intake/` has been reviewed section-by-section and assigned a canonical destination.

Source corpus:

1. `send/docs/intake/AI_TRADE_PHYSICS_SPACE_MODEL_SPEC.md`
2. `send/docs/intake/TRADE_PHYSICS_SCORE_SPEC.md`
3. `send/docs/intake/AI_TRADE_PHYSICS_INTELLIGENCE_SPEC.md`

Owner direction is that Trade Physics is current-scope and must be integrated now, not retained as a future upgrade.

This ledger does not activate any runtime behavior. It records source coverage and reconciliation only.

## 2. Verdict vocabulary

- `ABSORBED` — source truth is carried into a proposed canonical successor.
- `ABSORBED_WITH_VOCABULARY_RECONCILIATION` — concept retained, legacy names replaced by active canonical vocabulary.
- `ABSORBED_WITH_AUTHORITY_RECONCILIATION` — concept retained but moved to the canonical owner layer.
- `RECONCILED_CONFLICT` — conflicting source definitions resolved explicitly.
- `CURRENT_SCOPE_GOVERNED_READINESS` — capability is current-scope, but live effect requires evidence/readiness rather than fabricated output.
- `RETAINED_AS_RESEARCH_HYPOTHESIS` — useful hypothesis retained for measurement, not promoted as proven truth.
- `NOT_ADOPTED_AS_RUNTIME_RULE` — source text preserved historically but not accepted as a current deterministic runtime rule.

## 3. Space Model source coverage

Source: `AI_TRADE_PHYSICS_SPACE_MODEL_SPEC.md`

| Source section | Verdict | Canonical destination / resolution |
|---|---|---|
| 1. Purpose | ABSORBED | `TRADE_PHYSICS_MODEL_SPEC_v1.0.0`; structural-space feasibility is current strategy truth. |
| 2. Conceptual Foundation | ABSORBED | Trade Physics physical-feasibility premise retained, but probability claims are treated as hypotheses until outcome evidence validates them. |
| 3. Core Variables | ABSORBED_WITH_VOCABULARY_RECONCILIATION | `available_space`, `required_space`, `atr_m5` retained; `buffer_price` becomes canonical `buffer_distance`; ownership moves upstream from signal engine into Market/SR/Time/Scoring contracts. |
| 4. Space to Buffer Ratio | ABSORBED | `space_to_buffer_ratio = available_space / required_space`. |
| 5. Normalized Trade Space Margin | ABSORBED | `trade_space_margin_atr = (available_space - required_space) / atr_m5`. |
| 6. Relation to Buffer Model | ABSORBED_WITH_VOCABULARY_RECONCILIATION | `required_space = buffer_distance`; actual multiplier values remain governed parameters, not frozen merely because Intake gives examples. |
| 7. Relation to Structure / SR Gate | ABSORBED_WITH_AUTHORITY_RECONCILIATION | Directional nearest barrier becomes SR/Corridor ownership; BUY uses nearest relevant resistance, SELL nearest relevant support. `SR_SPACE_INSUFFICIENT` may be represented by canonical structural blocker taxonomy. |
| 8. Relation to Feasibility | ABSORBED_WITH_VOCABULARY_RECONCILIATION | `speed_price_per_min`, `t_needed_adj_min`, `expiry_minutes` mapped to canonical directional speed / `t_needed_adjusted` / `model_expiry` semantics. |
| 9. Role in AI Strategy Analysis | CURRENT_SCOPE_GOVERNED_READINESS | Features become mandatory dataset candidates now; predictive importance is not asserted until validated. |
| 10. AI Dataset Features | ABSORBED_WITH_VOCABULARY_RECONCILIATION | Dataset contract moved to `TRADE_PHYSICS_INTELLIGENCE_SPEC_v1.0.0`; legacy names normalized. |
| 11. Expected Predictive Importance | RETAINED_AS_RESEARCH_HYPOTHESIS | Ranking order is a hypothesis to test, not a canonical fact. |
| 12. Role in Strategy Optimization | CURRENT_SCOPE_GOVERNED_READINESS | Optimization/recommendation is active infrastructure scope, but mutation remains governed. |
| 13. Future Extensions | RETAINED_AS_RESEARCH_HYPOTHESIS | SQI, structural density, dynamic buffer adjustment are not silently activated; they enter research/hypothesis registry. |
| 14. Summary | ABSORBED | Core structural-space role retained. |

## 4. Trade Physics Score source coverage

Source: `TRADE_PHYSICS_SCORE_SPEC.md`

| Source section | Verdict | Canonical destination / resolution |
|---|---|---|
| 1. Purpose | ABSORBED | Deterministic physical-feasibility score is current strategy scope. |
| 2. Conceptual Foundation | ABSORBED | Space/time/speed/volatility constraints retained. |
| 3. Core Dimensions | ABSORBED | Canonical deterministic components remain `S`, `T`, `P`, `V`. |
| 4. Space Component | ABSORBED | `S = min(space_to_buffer_ratio, 3.0) / 3.0`. |
| 5. Time Feasibility Component | ABSORBED_WITH_VOCABULARY_RECONCILIATION | `time_to_buffer_ratio = model_expiry / t_needed_adjusted`; this is reciprocal orientation to active `model_time_reach_ratio` when synchronized. `T = min(time_to_buffer_ratio, 2.0) / 2.0`. |
| 6. Price Speed Component | ABSORBED_WITH_AUTHORITY_RECONCILIATION | Intake ATR reference is authoritative proposed Trade Physics formula: `atr_speed_reference = atr_m5 / 5`, `directional_speed_ratio = directional_effective_speed / atr_speed_reference`, `P = min(ratio,2.0)/2.0`. Existing signal-engine `buffer/expiry` reference is treated as drift, not canonized. |
| 7. Volatility Efficiency | ABSORBED | `movement_stress = required_space / atr_m5`; `V = 1/(1+movement_stress)`. |
| 8. TPS Formula | ABSORBED | `TPS = 100 * (0.35*S + 0.25*T + 0.20*P + 0.20*V)`, bounded to `[0,100]`. |
| 9. Interpretation of TPS | ABSORBED_AS_EXPLANATION_BANDS | Bands remain explanatory baseline, not automatic PRE/CONFIRM/OPEN_NOW gates unless separately authorized. |
| 10. Relation to Existing Strategy Score | ABSORBED | Classical score and TPS remain distinct first-class strategic metrics; no undocumented combined score. |
| 11. Example | ABSORBED_AS_VALIDATION_VECTOR | Numerical example becomes a canonical test vector after vocabulary normalization. |
| 12. Role in AI Dataset | ABSORBED | Mandatory Trade Physics feature lineage enters intelligence/data contract. |
| 13. Role in Decision Audit | ABSORBED | TPS and components become pre-FSM decision truth and audit material. |

## 5. Trade Physics Intelligence source coverage

Source: `AI_TRADE_PHYSICS_INTELLIGENCE_SPEC.md`

| Source section | Verdict | Canonical destination / resolution |
|---|---|---|
| 1. Purpose | CURRENT_SCOPE_GOVERNED_READINESS | Self-calibrating intelligence infrastructure is current-scope now. The old timing sentence “after stabilization / STEP 100” is superseded by Owner direction. |
| 2. Fundamental Trade Physics Model | ABSORBED_WITH_AUTHORITY_RECONCILIATION | Energy/space/time/flow conceptual framing is retained; deterministic runtime TPS remains governed by `TRADE_PHYSICS_MODEL_SPEC`. |
| 3. Fundamental Variables | RECONCILED_CONFLICT | E/S/T/F are useful conceptual/feature variables but do not create a second deterministic TPS formula. `S` and temporal concepts map to canonical structural/time metrics; energy and flow remain explicit features. |
| 4. Trade Probability Score (TPS sigmoid) | RECONCILED_CONFLICT | It is forbidden to coexist under the same `TPS` identity. Deterministic TPS remains `[0,100]`; learned/calibrated model output is renamed `trade_success_probability` `[0,1]`. Source thresholds are not activated without validation. |
| 5. Directional Effective Speed | ABSORBED | Critical improvement promoted into proposed Market/Time/Trade Physics contracts. Exact deterministic algorithm is defined in proposed canon; no longer left conceptual. |
| 6. Flow Efficiency | ABSORBED | `flow_efficiency = directional_effective_speed / gross_speed` with governed zero/invalid handling. |
| 7. Dataset for AI | ABSORBED_WITH_VOCABULARY_RECONCILIATION | Dataset fields retained and expanded with provenance, feature version, signal/candidate lineage, truth-layer labels and anti-leakage controls. |
| 8. Recommended AI Model | CURRENT_SCOPE_GOVERNED_READINESS | Gradient-boosted trees remain an allowed candidate family, not a hard-coded mandatory provider/library. Model selection requires evidence. |
| 9. Self-Learning Architecture | ABSORBED | Decision evidence -> Outcome/Telemetry -> lineage -> calibration -> recommendations -> approval. Truth-layer separation is added. |
| 10. Safety Governance | ABSORBED | `recommend-only`, `admin-approve`, bounded modes retained; silent production mutation forbidden. |
| 11. Implementation Timing | RECONCILED_CONFLICT | “implement later” is superseded by Owner current-scope decision. However model deployment still requires real dataset/validation readiness. |
| 12. Final Objective | ABSORBED | Move from indicator-only evaluation toward quantitative, evidence-calibrated physical feasibility and probability modeling. |

## 6. Cross-source conflicts and their canonical resolutions

### 6.1 Two different TPS definitions

Resolution:
- deterministic `TPS`: `[0,100]`, weighted S/T/P/V formula from `TRADE_PHYSICS_SCORE_SPEC`;
- learned probability: `trade_success_probability` `[0,1]`;
- no second sigmoid value may be called TPS.

### 6.2 Time-ratio orientation

Active Time Model truth:

`model_time_reach_ratio = t_needed_adjusted / model_expiry`

Trade Physics convenience ratio:

`time_to_buffer_ratio = model_expiry / t_needed_adjusted`

When evidence is synchronized and denominator is valid:

`time_to_buffer_ratio = 1 / model_time_reach_ratio`

Neither ratio may silently substitute for the other without naming its orientation.

### 6.3 Legacy buffer terminology

`buffer_price` is compatibility-only. Canonical strategy term is `buffer_distance`.

### 6.4 Speed model

Old runtime `price_speed` is gross/absolute movement speed. Trade Physics requires direction-aware speed.

Proposed separation:
- `gross_price_speed` / existing context speed: non-directional activity magnitude;
- `directional_effective_speed`: direction-specific, recency-weighted movement used by Trade Physics and proposed Time Model v3;
- `flow_efficiency = directional_effective_speed / gross_price_speed` where denominator is valid.

### 6.5 Existing undocumented TPS runtime

Current `signal_engine.py` contains an undocumented TPS computation. It is evidence of partial prior implementation, not normative authority.

Canonical target ownership is Scoring/Strategy before `DecisionObject`. Signal Engine must not remain owner of Trade Physics mathematics after remediation.

## 7. Completeness rule

Trade Physics integration is not complete until:

1. every source section above has a canonical destination;
2. all affected active contracts have versioned successors;
3. Root Strategy Stack and Master Index identify Trade Physics correctly;
4. Event/Observability/Module contracts carry required Trade Physics truth without creating parallel ownership;
5. telemetry/outcome/analytics/research lineage preserves Trade Physics features and feature versions;
6. the three Intake source files are explicitly reclassified as historical intake/source material after promotion;
7. runtime code is re-audited only after the new canonical set becomes active.

## 8. Final statement

The Intake Trade Physics corpus is not being discarded, selectively cherry-picked, or postponed.

It is being fully absorbed under the current canonical ownership model, with conflicts resolved explicitly and unproven predictive claims retained as testable hypotheses rather than mislabeled production facts.
