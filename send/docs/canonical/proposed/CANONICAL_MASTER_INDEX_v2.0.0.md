# CANONICAL_MASTER_INDEX_v2.0.0

Canonical Name: CANONICAL_MASTER_INDEX  
Version: 2.0.0  
Status: PROPOSED COMPLETE AUTHORITATIVE MASTER INDEX — NOT ACTIVE CANONICAL  
Owner: BinaryBot / DROPi Signals  
Date: 2026-09-01  
Supersession Intent: `CANONICAL_MASTER_INDEX_v1.0.0.md`

---

## 0. Promotion status

This document describes the intended authoritative inventory **after** the staged-execution + Trade Physics canonical promotion program completes.

Until promotion, `CANONICAL_MASTER_INDEX_v1.0.0.md` remains the authoritative master index.

This proposed index does not make any proposed document active merely by listing it.

---

## 1. Purpose

This index provides:
- a unique inventory of intended active canonical functional specifications;
- cluster hierarchy;
- authority relationships;
- promoted successor versions;
- treatment of proposed/transitional/supporting/superseded/deprecated/intake material;
- explicit inclusion of current-scope Trade Physics;
- exact final versions for all reference-repair successors.

The index must be promoted atomically with the final canonical successor set and reference repairs.

---

## 2. Inventory correction from v1

The prior v1 index declared 41 active canonical documents, but its presentation was inconsistent because:
- `RISK_MODEL_v2.0.0.md` was shown in two sections while counted once;
- `HUMAN_COMPREHENSION_AND_SELF_EXPLAINING_CONTROL_SURFACE_CANON_v1.0.0.md` was added later outside the numbered inventory.

The reconciled current baseline is **41 unique functional canonical specifications**.

The Trade Physics program introduces two new functional authorities:
- `TRADE_PHYSICS_MODEL_SPEC_v1.0.0.md`;
- `TRADE_PHYSICS_INTELLIGENCE_SPEC_v1.0.0.md`.

Risk v3, Community Feedback v3, and the 17 reference-repair successors replace existing domains and therefore do not increase the unique-domain count.

Therefore the intended post-promotion inventory is:

**43 unique functional canonical specifications.**

Master Index itself and supporting governance records are documented separately and are not counted as functional-domain specifications.

---

## 3. Canonical authority hierarchy

### 3.1 Root manifests

| Root manifest | Cluster |
|---|---|
| `CANONICAL_STRATEGY_STACK_v2.0.0.md` | Strategy/runtime strategy cluster |
| `ADMIN_SURFACE_AND_CONTROL_PLANE_CANON_v2.0.1.md` | Admin/control-plane cluster |

### 3.2 Layered policy/implementation authority

| Policy/Architecture Authority | Implementation/Mechanics Authority |
|---|---|
| `SYSTEM_ARCHITECTURE_MAP_v3.0.0.md` | `SYSTEM_INVARIANTS_v3.0.0.md`, `MODULE_INTERFACE_SPEC_v3.0.0.md`, `TEST_PLAN_v3.0.0.md` as bounded system-level contracts |
| `OBSERVABILITY_SPEC_v3.0.0.md` | `OBSERVABILITY_LOGGING_SPEC_v3.0.0.md`, `EVENT_SCHEMA_SPEC_v3.0.0.md` |
| `SIGNAL_DISTRIBUTION_ARCHITECTURE_v2.0.1.md` | `SIGNAL_DISTRIBUTION_SPEC_v2.0.1.md` |
| `TRADE_PHYSICS_MODEL_SPEC_v1.0.0.md` | ALGO/DecisionObject/Telemetry consumers; Signal Engine is downstream only |
| `TRADE_PHYSICS_INTELLIGENCE_SPEC_v1.0.0.md` | Research/Analytics/Strategy Intelligence/Autonomous Evolution consumers |

### 3.3 Document classes

| Class | Treatment |
|---|---|
| Active Canonical | Binding authority for its domain. |
| Proposed | Under review; not authoritative until promoted. |
| Transitional | Historical migration/progression record; not binding. |
| Supporting | Reference/governance material; cannot override active canon. |
| Superseded | Replaced canonical version; historical only. |
| Deprecated | Dead-end historical material; non-authoritative. |
| Intake | Source material awaiting/under canonical absorption; non-authoritative after absorption. |

---

## 4. Intended authoritative functional inventory

### 4.1 Root manifests

| # | Canonical filename | Version | Intended status | Domain | Authority role |
|---:|---|---:|---|---|---|
| 1 | `CANONICAL_STRATEGY_STACK_v2.0.0.md` | 2.0.0 | Active Canonical | Strategy architecture | Root manifest for strategy/runtime strategy cluster |
| 2 | `ADMIN_SURFACE_AND_CONTROL_PLANE_CANON_v2.0.1.md` | 2.0.1 | Active Canonical | Admin/control-plane architecture | Root manifest for admin/control plane |

### 4.2 Strategy pipeline cluster

Governed by `CANONICAL_STRATEGY_STACK_v2.0.0.md`.

| # | Canonical filename | Version | Intended status | Domain | Authority role |
|---:|---|---:|---|---|---|
| 3 | `ALGO_SPEC_v3.0.0.md` | 3.0.0 | Active Canonical | Trading algorithm / strategic orchestration | Strategy evaluation/scoring/gating authority |
| 4 | `SR_CORRIDOR_ENGINE_SPEC_v3.0.0.md` | 3.0.0 | Active Canonical | Structural/SR/corridor truth | Directional structural-space authority |
| 5 | `TIME_MODEL_UNIFIED_CANON_v3.0.0.md` | 3.0.0 | Active Canonical | Unified directional time model | Time/speed/expiry semantics authority |
| 6 | `TRADE_PHYSICS_MODEL_SPEC_v1.0.0.md` | 1.0.0 | Active Canonical | Deterministic Trade Physics | S/T/P/V and TPS authority |
| 7 | `DECISION_OBJECT_CANONICAL_SPEC_v2.0.0.md` | 2.0.0 | Active Canonical | Strategy-to-FSM contract | Complete pre-FSM strategic truth contract |
| 8 | `FSM_DECISION_ENGINE_SPEC_v2.0.0.md` | 2.0.0 | Active Canonical | Operational lifecycle FSM | Exact-stage acceptance/handoff authority |
| 9 | `SIGNAL_ENGINE_EXECUTION_SPEC_v3.0.0.md` | 3.0.0 | Active Canonical | Signal execution | SignalEvent candidate/execution outcome authority |
| 10 | `RISK_MODEL_v3.0.0.md` | 3.0.0 | Active Canonical | Risk/capital protection | Risk filtering/protection authority aligned to canonical structure/time/Trade Physics truth |

### 4.3 Observability / decision evidence cluster

Layered authority: Observability Policy -> Logging/Event Schema mechanics.

| # | Canonical filename | Version | Intended status | Domain | Authority role |
|---:|---|---:|---|---|---|
| 11 | `OBSERVABILITY_SPEC_v3.0.0.md` | 3.0.0 | Active Canonical | Observability policy | End-to-end evidence/truth-separation authority |
| 12 | `OBSERVABILITY_LOGGING_SPEC_v3.0.0.md` | 3.0.0 | Active Canonical | Structured logging | Logging mechanics authority |
| 13 | `EVENT_SCHEMA_SPEC_v3.0.0.md` | 3.0.0 | Active Canonical | Event schema | Event families/envelope/correlation authority |
| 14 | `DECISION_AUDIT_SPEC_v3.0.0.md` | 3.0.0 | Active Canonical | Decision audit | Pre-FSM decision/rejection audit authority |
| 15 | `TRADE_TEMPORAL_TELEMETRY_SPEC_v3.0.0.md` | 3.0.0 | Active Canonical | Objective market telemetry | Post-executable market truth/Trade Physics label lineage authority |

### 4.4 Signal distribution cluster

| # | Canonical filename | Version | Intended status | Domain | Authority role |
|---:|---|---:|---|---|---|
| 16 | `SIGNAL_DISTRIBUTION_ARCHITECTURE_v2.0.1.md` | 2.0.1 | Active Canonical | Routing topology | Distribution architecture authority |
| 17 | `SIGNAL_DISTRIBUTION_SPEC_v2.0.1.md` | 2.0.1 | Active Canonical | Entitlement/delivery policy | Route/delivery policy authority |
| 18 | `CHANNEL_CONFIG_SPEC_v2.0.1.md` | 2.0.1 | Active Canonical | Channel configuration | Channel/topic mapping authority |
| 19 | `TELEGRAM_UX_v2.0.1.md` | 2.0.1 | Active Canonical | Telegram UX | User-facing Telegram presentation authority |
| 20 | `AFFILIATE_SIGNAL_DISTRIBUTION_MODEL_v2.0.1.md` | 2.0.1 | Active Canonical | Affiliate distribution | Affiliate signal-distribution/commercial-participation authority |
| 21 | `SIGNAL_ECONOMICS_AND_MONETIZATION_MODEL_v2.0.1.md` | 2.0.1 | Active Canonical | Signal economics | Monetization/economics authority |

### 4.5 Admin / control-plane cluster

Governed by `ADMIN_SURFACE_AND_CONTROL_PLANE_CANON_v2.0.1.md`.

| # | Canonical filename | Version | Intended status | Domain | Authority role |
|---:|---|---:|---|---|---|
| 22 | `ADMIN_CONTROL_SPEC_v2.0.1.md` | 2.0.1 | Active Canonical | Admin control surface | Admin command/control authority |
| 23 | `ADMIN_OPERATIONS_SPEC_v2.0.1.md` | 2.0.1 | Active Canonical | Admin operations | Operational procedures authority |
| 24 | `ADMIN_TREE_MAP_v2.0.1.md` | 2.0.1 | Active Canonical | Admin structural map | Admin navigation/hierarchy authority |
| 25 | `CONTROL_PANEL_HIERARCHY_AND_INTELLIGENCE_SPEC_v2.0.1.md` | 2.0.1 | Active Canonical | Control panel/intelligence presentation | Control-panel hierarchy authority |
| 26 | `ROLE_AND_PERMISSION_MATRIX_SPEC_v2.0.1.md` | 2.0.1 | Active Canonical | Roles/permissions | Authorization authority |
| 27 | `STRATEGY_PARAMETER_CONTROL_SPEC_v3.0.0.md` | 3.0.0 | Active Canonical | Strategy/model parameter control | Governed tunable-parameter authority |

### 4.6 Analytics / Research / Intelligence cluster

| # | Canonical filename | Version | Intended status | Domain | Authority role |
|---:|---|---:|---|---|---|
| 28 | `OUTCOME_TRACKING_SPEC_v3.0.0.md` | 3.0.0 | Active Canonical | Operational outcome reconciliation | Admin/operational outcome truth authority |
| 29 | `PERFORMANCE_ANALYTICS_SPEC_v3.0.0.md` | 3.0.0 | Active Canonical | Performance analytics | Truth-layer-separated analytics authority |
| 30 | `RESEARCH_AND_LEARNING_FRAMEWORK_SPEC_v3.0.0.md` | 3.0.0 | Active Canonical | Research/learning | Hypothesis/experiment/evidence governance authority |
| 31 | `TRADE_PHYSICS_INTELLIGENCE_SPEC_v1.0.0.md` | 1.0.0 | Active Canonical | Trade Physics ML/calibration | Dataset/model/calibration/readiness authority |
| 32 | `STRATEGY_INTELLIGENCE_SYSTEM_v3.0.0.md` | 3.0.0 | Active Canonical | Strategy intelligence | Diagnostic/recommendation intelligence authority |
| 33 | `AUTONOMOUS_STRATEGY_EVOLUTION_SYSTEM_v3.0.0.md` | 3.0.0 | Active Canonical | Controlled evolution | Governed evolution/experiment/rollout proposal authority |
| 34 | `COMMUNITY_FEEDBACK_AND_PRIVACY_SPEC_v3.0.0.md` | 3.0.0 | Active Canonical | Community feedback/privacy | Self-reported member-experience and privacy authority; distinct from market/operational outcome truth |

### 4.7 System architecture / infrastructure

| # | Canonical filename | Version | Intended status | Domain | Authority role |
|---:|---|---:|---|---|---|
| 35 | `SYSTEM_ARCHITECTURE_MAP_v3.0.0.md` | 3.0.0 | Active Canonical | System architecture | Overall architecture-map authority aligned with Trade Physics and staged execution |
| 36 | `MODULE_INTERFACE_SPEC_v3.0.0.md` | 3.0.0 | Active Canonical | Module interfaces | Cross-module ownership/contracts authority |
| 37 | `SYSTEM_INVARIANTS_v3.0.0.md` | 3.0.0 | Active Canonical | System invariants | Non-negotiable Trade Physics/execution/system rules |
| 38 | `FAILURE_RECOVERY_SPEC_v2.0.1.md` | 2.0.1 | Active Canonical | Failure recovery | Failure/recovery authority |
| 39 | `DEPLOYMENT_PROTOCOL_v2.0.1.md` | 2.0.1 | Active Canonical | Deployment | Deployment/safety authority |

### 4.8 Security / governance / testing / human comprehension

| # | Canonical filename | Version | Intended status | Domain | Authority role |
|---:|---|---:|---|---|---|
| 40 | `SECURITY_MODEL_v2.0.1.md` | 2.0.1 | Active Canonical | Security | Security/threat authority; delegates RBAC/outcome timing to domain owners |
| 41 | `GOVERNANCE_AND_CHANGE_CONTROL_v2.0.1.md` | 2.0.1 | Active Canonical | Governance/change control | Approval/version/change authority |
| 42 | `TEST_PLAN_v3.0.0.md` | 3.0.0 | Active Canonical | Testing/validation | Validation authority for Trade Physics, exact-stage execution, observability and regression |
| 43 | `HUMAN_COMPREHENSION_AND_SELF_EXPLAINING_CONTROL_SURFACE_CANON_v1.0.1.md` | 1.0.1 | Active Canonical | Human comprehension / operational memory | Mandatory self-explaining control-surface and operational-memory authority |

---

## 5. Supporting governance records

The following may reside in/near canonical folders but are supporting governance records rather than functional-domain authorities and are not counted in the 43:

- `CANON_BATCH_EVALUATION_v3.0.0.md` — updated intake classification record;
- `TRADE_PHYSICS_INTAKE_SOURCE_ABSORPTION_LEDGER_v1.0.0.md` — source coverage proof;
- `TRADE_PHYSICS_AND_STAGED_EXECUTION_CONSOLIDATION_PLAN_v1.0.0.md` — cross-program consolidation proof;
- `CANONICAL_REFERENCE_REPAIR_FINAL_SET_20260901.md` — final 17-document PATCH assignment;
- canonical promotion/reference-impact matrices;
- audit and conflict-resolution records.

---

## 6. Trade Physics canonical position

Trade Physics is no longer future-state.

### Deterministic runtime authority
`TRADE_PHYSICS_MODEL_SPEC_v1.0.0.md`

Owns:
- structural/time/speed/volatility physical-feasibility metrics;
- S/T/P/V;
- deterministic TPS `[0,100]`.

### Learned intelligence authority
`TRADE_PHYSICS_INTELLIGENCE_SPEC_v1.0.0.md`

Owns:
- dataset/materialization;
- training/evaluation/calibration;
- model registry;
- `trade_success_probability` `[0,1]`;
- readiness/drift/recommendation governance.

The two authorities must never use the same `TPS` identity for different values.

---

## 7. Staged-execution canonical position

The promoted set must preserve:
- explicit FSM requested/accepted stage;
- `stage_handoff_ready` separate from `trade_execution_ready`;
- PRE/CONFIRM/OPEN_NOW candidate eligibility only after exact FSM acceptance;
- SignalEvent candidate != delivery;
- dedicated `signal_execution_result`;
- EMITTED only with downstream successful publication evidence.

---

## 8. Truth-domain separation

The promoted graph must preserve separate owners for:

- strategy/pre-FSM truth → ALGO / DecisionObject / Decision Audit;
- deterministic Trade Physics truth → Trade Physics Model;
- FSM lifecycle truth → FSM;
- signal-execution truth → Signal Engine;
- route/publication truth → Distribution / Publisher observability;
- objective market truth → Trade Temporal Telemetry;
- operational/admin outcome truth → Outcome Tracking;
- community/member self-report truth → Community Feedback;
- analytics/research/model interpretations → their respective downstream authorities.

No downstream truth may silently overwrite another truth class.

---

## 9. Reference migration rule

Before this Master Index can be promoted:
- every intended active successor must reference final successor filenames or explicitly historical/compatibility predecessors only;
- no intended active successor may point to an obsolete root/version as current authority;
- distribution wording must distinguish SignalEvent candidate handoff from `EMITTED` successful-publication truth;
- all 17 reference-only successors in `CANONICAL_REFERENCE_REPAIR_FINAL_SET_20260901.md` must be complete/self-contained;
- all reference-only changes must receive correct version treatment under Governance SemVer rules.

---

## 10. Supersession targets

Upon successful atomic promotion, the following current active versions are intended to become superseded.

### Structural/root successors
- `CANONICAL_STRATEGY_STACK_v1.0.0.md`
- `CANONICAL_MASTER_INDEX_v1.0.0.md`
- `ALGO_SPEC_v2.0.0.md`
- `SR_CORRIDOR_ENGINE_SPEC_v2.0.0.md`
- `TIME_MODEL_UNIFIED_CANON_v2.0.0.md`
- `DECISION_OBJECT_CANONICAL_SPEC_v1.0.0.md`
- `FSM_DECISION_ENGINE_SPEC_v1.0.0.md`
- `SIGNAL_ENGINE_EXECUTION_SPEC_v2.0.0.md`
- `RISK_MODEL_v2.0.0.md`
- `OBSERVABILITY_SPEC_v2.0.0.md`
- `OBSERVABILITY_LOGGING_SPEC_v2.0.0.md`
- `EVENT_SCHEMA_SPEC_v2.0.0.md`
- `DECISION_AUDIT_SPEC_v2.0.0.md`
- `TRADE_TEMPORAL_TELEMETRY_SPEC_v2.0.0.md`
- `OUTCOME_TRACKING_SPEC_v2.0.0.md`
- `PERFORMANCE_ANALYTICS_SPEC_v2.0.0.md`
- `RESEARCH_AND_LEARNING_FRAMEWORK_SPEC_v2.0.0.md`
- `STRATEGY_INTELLIGENCE_SYSTEM_v2.0.0.md`
- `AUTONOMOUS_STRATEGY_EVOLUTION_SYSTEM_v2.0.0.md`
- `STRATEGY_PARAMETER_CONTROL_SPEC_v2.0.0.md`
- `MODULE_INTERFACE_SPEC_v2.0.0.md`
- `SYSTEM_ARCHITECTURE_MAP_v2.0.0.md`
- `SYSTEM_INVARIANTS_v2.0.0.md`
- `TEST_PLAN_v2.0.0.md`
- `COMMUNITY_FEEDBACK_AND_PRIVACY_SPEC_v2.0.0.md`
- `CANON_BATCH_EVALUATION_v2.0.0.md` as supporting record where promoted replacement is used.

### Reference-repair PATCH successors
- `ADMIN_SURFACE_AND_CONTROL_PLANE_CANON_v2.0.0.md`
- `ADMIN_CONTROL_SPEC_v2.0.0.md`
- `ADMIN_OPERATIONS_SPEC_v2.0.0.md`
- `ADMIN_TREE_MAP_v2.0.0.md`
- `CONTROL_PANEL_HIERARCHY_AND_INTELLIGENCE_SPEC_v2.0.0.md`
- `ROLE_AND_PERMISSION_MATRIX_SPEC_v2.0.0.md`
- `SIGNAL_DISTRIBUTION_ARCHITECTURE_v2.0.0.md`
- `SIGNAL_DISTRIBUTION_SPEC_v2.0.0.md`
- `CHANNEL_CONFIG_SPEC_v2.0.0.md`
- `TELEGRAM_UX_v2.0.0.md`
- `AFFILIATE_SIGNAL_DISTRIBUTION_MODEL_v2.0.0.md`
- `SIGNAL_ECONOMICS_AND_MONETIZATION_MODEL_v2.0.0.md`
- `FAILURE_RECOVERY_SPEC_v2.0.0.md`
- `DEPLOYMENT_PROTOCOL_v2.0.0.md`
- `SECURITY_MODEL_v2.0.0.md`
- `GOVERNANCE_AND_CHANGE_CONTROL_v2.0.0.md`
- `HUMAN_COMPREHENSION_AND_SELF_EXPLAINING_CONTROL_SURFACE_CANON_v1.0.0.md`

Superseded files remain historically preserved; they do not remain competing active truth.

---

## 11. Intake treatment after promotion

The original Trade Physics Intake files remain preserved for provenance but are explicitly non-authoritative after their content is absorbed:
- `AI_TRADE_PHYSICS_SPACE_MODEL_SPEC.md`
- `TRADE_PHYSICS_SCORE_SPEC.md`
- `AI_TRADE_PHYSICS_INTELLIGENCE_SPEC.md`

Implementation must cite promoted canonical successors, never these Intake files directly.

---

## 12. Promotion gates

This index is not promotion-ready until all pass:

- [ ] 43 intended functional specifications are present/verified;
- [ ] every changed structural specification is complete/self-contained;
- [ ] Risk v3 and Community Feedback v3 pass cross-document audit;
- [ ] all 17 reference-repair successors are complete/self-contained;
- [ ] `SYSTEM_ARCHITECTURE_MAP_v3.0.0.md`, `SYSTEM_INVARIANTS_v3.0.0.md`, and `TEST_PLAN_v3.0.0.md` pass cross-document audit;
- [ ] no duplicate same-domain active authority will remain after promotion;
- [ ] exact stale-reference scan passes for the intended successor graph;
- [ ] supersession/move plan is explicit;
- [ ] Trade Physics source absorption ledger passes;
- [ ] staged-execution consolidation passes;
- [ ] Event/Observability/Module/Signal Engine/FSM contracts agree;
- [ ] runtime code is unchanged in the documentation promotion PR;
- [ ] post-promotion code re-audit plan is prepared.

---

## 13. Version history

| Version | Date | Description |
|---|---|---|
| 1.0.0 | 2026-07-12 | Initial authoritative reconciled index. |
| 2.0.0 | 2026-09-01 | Proposed structural inventory update for staged execution + current-scope Trade Physics; 43 unique functional domains, Risk/Community structural successors, final 17 reference-repair versions, and complete system architecture/invariants/testing alignment. |

---

## 14. Final principle

The Master Index is a map of authority, not a mechanism for creating authority by itself.

After promotion, the active canonical graph must contain exactly one current authority per domain, 43 unique functional specifications, explicit Trade Physics ownership, explicit execution/publication boundaries, separated truth domains, system-level architecture/invariant/test coverage, and no active normative references that require engineers to guess which superseded version governs implementation.
