# CANON_BATCH_EVALUATION_v3.0.0

Version: 3.0.0  
Status: PROPOSED COMPLETE SUCCESSOR — NOT ACTIVE CANONICAL  
Owner: BinaryBot / DROPi Signals  
Date: 2026-09-01  
Supersession Intent: `CANON_BATCH_EVALUATION_v2.0.0.md`

## 1. Purpose

This document records the updated canonical evaluation verdict for surfaced satellite/intake strategy and intelligence documents.

It replaces the prior evaluation only after explicit promotion.

The major version is required because Owner direction materially changes the classification and intended canonical destination of the complete Trade Physics family.

This evaluation is documentation-governance only. It does not itself patch runtime code or activate distribution/broker behavior.

## 2. Evaluation method

Each source document is evaluated against:

1. whether it defines distinct current system truth;
2. whether it overlaps an existing canonical owner;
3. whether its content belongs in current operational strategy, intelligence/research, or supporting material;
4. whether it should be promoted directly, absorbed into a versioned successor, retained as a satellite, or kept as hypothesis material;
5. whether Owner direction has changed the prior lifecycle classification.

## 3. Updated verdict table

| Source document | Updated verdict | Canonical destination / alignment | Rationale | Required next action |
|---|---|---|---|---|
| `AI_STRATEGY_AUDITOR_SPEC.md` | MERGE_INTO_ACTIVE | Research / Performance Analytics / Strategy Intelligence successors | Valuable reject analysis, bottleneck logic, starvation and recommendation material; no need for independent root authority. | Preserve bounded source content in versioned owner docs. |
| `AI_TRADING_INTELLIGENCE_ARCHITECTURE.md` | KEEP_OUTSIDE_ACTIVE | Strategy Intelligence alignment | Useful conceptual architecture but overlaps active intelligence ownership. | Keep as satellite/reference; absorb unique clarifications only. |
| `INTELLIGENCE_LAYER_ARCHITECTURE.md` | KEEP_OUTSIDE_ACTIVE | Strategy Intelligence / System Architecture alignment | Useful layer framing but overlapping authority. | Keep outside active; absorb unique architecture clarifications where needed. |
| `INTELLIGENCE_DATA_PIPELINE_DEFINITION.md` | MERGE_INTO_ACTIVE | Strategy Intelligence / Module Interface / Observability / Analytics | Valuable pipeline, snapshot and aggregation detail. | Merge into canonical owner docs. |
| `INTELLIGENCE_FILES_AND_MODULE_MAP.md` | MERGE_INTO_ACTIVE | Module Interface / Strategy Intelligence | Useful implementation mapping, not independent domain authority. | Absorb ownership/module map. |
| `COMMUNITY_FEEDBACK_AND_PRIVACY_SPEC.md` | PROMOTE_OR_MAJOR_MERGE | Outcome / Analytics / Telegram / Governance/Security cluster | Distinct privacy/community analytics concern. | Separate governed decision still required. |
| `ADAPTIVE_ACTIVITY_GATE_SPEC.md` | MERGE_INTO_ACTIVE | ALGO / Decision Audit / Temporal Telemetry | Strategy-rule refinement belongs in strategy truth. | Continue active alignment and evidence validation. |
| `AI_TRADE_PHYSICS_SPACE_MODEL_SPEC.md` | CURRENT_SCOPE — ABSORB COMPLETELY | `TRADE_PHYSICS_MODEL_SPEC_v1.0.0`, SR/Corridor, Time Model, ALGO, DecisionObject, Audit, Intelligence | Owner direction makes structural Trade Physics current-scope. The source must not remain merely satellite/reference. | Absorb every source section; normalize vocabulary and ownership; retain original as historical Intake source after promotion. |
| `TRADE_PHYSICS_SCORE_SPEC.md` | CURRENT_SCOPE — PROMOTE THROUGH CANONICAL SUCCESSOR | `TRADE_PHYSICS_MODEL_SPEC_v1.0.0` plus ALGO/DecisionObject/Audit integration | Defines the deterministic S/T/P/V physical-feasibility score already partially implemented in runtime but previously under-documented. | Establish one canonical deterministic TPS `[0,100]`; move mathematics into strategy/scoring ownership before DecisionObject. |
| `AI_TRADE_PHYSICS_INTELLIGENCE_SPEC.md` | CURRENT_SCOPE — PROMOTE THROUGH GOVERNED INTELLIGENCE SUCCESSOR | `TRADE_PHYSICS_INTELLIGENCE_SPEC_v1.0.0`, Strategy Intelligence, Research, Analytics, Autonomous Evolution | Owner direction removes the prior “future upgrade” classification. AI/calibration infrastructure must be integrated now, while learned outputs remain evidence/readiness gated. | Separate deterministic TPS from learned probability; implement data/model/readiness governance in canon before code. |

## 4. Grouped decision summary

### 4.1 Current-scope Trade Physics integration — changed from v2

The following Intake sources are now mandatory current-scope source material:

- `AI_TRADE_PHYSICS_SPACE_MODEL_SPEC.md`
- `TRADE_PHYSICS_SCORE_SPEC.md`
- `AI_TRADE_PHYSICS_INTELLIGENCE_SPEC.md`

Their prior classifications as satellite/future-state are superseded by Owner direction once this successor is promoted.

They are not copied blindly into active canon. Their content is reconciled into a governed canonical graph with single ownership per topic.

### 4.2 Merge into active, do not create unnecessary duplicate roots

- `AI_STRATEGY_AUDITOR_SPEC.md`
- `INTELLIGENCE_DATA_PIPELINE_DEFINITION.md`
- `INTELLIGENCE_FILES_AND_MODULE_MAP.md`
- `ADAPTIVE_ACTIVITY_GATE_SPEC.md`

### 4.3 Keep outside active as satellite/reference

- `AI_TRADING_INTELLIGENCE_ARCHITECTURE.md`
- `INTELLIGENCE_LAYER_ARCHITECTURE.md`

### 4.4 Separate unresolved promote/major-merge candidate

- `COMMUNITY_FEEDBACK_AND_PRIVACY_SPEC.md`

This document does not resolve that independent governance decision.

## 5. Trade Physics governance interpretation

### 5.1 Current-scope does not mean code-first

The Owner decision changes scope/timing, not governance discipline.

Therefore:

`Owner current-scope direction -> canonical conflict reconciliation -> complete versioned successors -> promotion -> code audit/remediation -> tests -> staged/runtime validation`

Code must not outrun the promoted documentation.

### 5.2 Intake source files do not become active merely because their headers say “Canonical”

The Intake files remain source material.

Their authority is realized only through versioned canonical successors under `canonical/active` after promotion.

### 5.3 Deterministic TPS identity

There must be exactly one deterministic metric called `TPS`:

`TPS in [0,100]`

with the governed S/T/P/V formula from the score source, after canonical vocabulary reconciliation.

### 5.4 Learned probability identity

The sigmoid / ML probability concept from `AI_TRADE_PHYSICS_INTELLIGENCE_SPEC.md` must not remain another `TPS`.

Its canonical identity is:

`trade_success_probability in [0,1]`

and it may be produced only by a validated model under explicit readiness/evidence rules.

### 5.5 Structural space is operational strategy truth

Trade Physics structural space is not merely an AI feature.

The following are current strategic evidence:

- directional `available_space`
- `required_space`
- `space_to_buffer_ratio`
- `trade_space_margin_atr`

SR/Corridor owns structural derivation; Trade Physics consumes it.

### 5.6 Directional time/speed integration

The current-scope integration includes the Intake requirement for direction-aware effective speed.

The proposed Time Model must distinguish:

- gross/non-directional price activity;
- `directional_effective_speed` for movement feasibility;
- `flow_efficiency` as directional movement cleanliness.

### 5.7 AI infrastructure is current-scope while model authority remains readiness-gated

Current-scope work includes:

- feature capture
- lineage
- labels
- dataset building
- leakage protection
- training/evaluation pipeline
- calibration
- model registry/versioning
- drift monitoring
- recommendation outputs
- approval/readiness state

Current-scope does not authorize fabricated model predictions or silent self-mutation.

## 6. Required canonical successor set

At minimum, Trade Physics integration affects:

- `TRADE_PHYSICS_MODEL_SPEC_v1.0.0`
- `TRADE_PHYSICS_INTELLIGENCE_SPEC_v1.0.0`
- ALGO successor
- SR/Corridor successor
- Time Model successor
- DecisionObject successor
- Decision Audit successor
- Performance Analytics successor
- Research & Learning successor
- Strategy Intelligence successor
- Autonomous Strategy Evolution successor
- Strategy Parameter Control successor
- Temporal Telemetry successor
- Outcome Tracking successor
- Module Interface successor
- Event Schema successor
- Observability Policy/Logging successors
- Root Strategy Stack successor
- Master Index successor

Additional reference-only patches may be required after full dependency scan.

## 7. Source absorption proof

The companion supporting record:

`TRADE_PHYSICS_INTAKE_SOURCE_ABSORPTION_LEDGER_v1.0.0.md`

must show every source section as:

- absorbed;
- reconciled;
- retained as hypothesis;
- or explicitly not adopted as a runtime rule.

No Trade Physics source section may disappear silently.

## 8. Runtime drift note

Repository runtime already contains partial Trade Physics implementation, including TPS metrics in/around signal execution telemetry.

This fact is evidence of implementation drift, not authority to bypass the canonical process.

The target architecture moves Trade Physics mathematics into strategy/scoring before DecisionObject and leaves Signal Engine as downstream consumer/execution layer.

## 9. Promotion rule

Promotion must be atomic enough that active canon does not temporarily contain contradictory statements such as:

- Trade Physics is future-state in one active document;
- Trade Physics is current strategy truth in another;
- two distinct values are both called TPS;
- active Time Model uses opposite ratio meaning without explicit mapping;
- Signal Engine owns strategic math while ALGO says scoring is strategy-owned.

If such contradictions would remain after the proposed patch set, promotion must stop.

## 10. Final decision statement

The v2 evaluation is no longer sufficient for Trade Physics classification.

The updated proposed truth is:

**Trade Physics is current-scope and must be integrated completely into the Binary Strategy V2 canonical system now.**

The original Intake documents remain historical/source evidence after absorption; they do not remain parallel active authorities.
