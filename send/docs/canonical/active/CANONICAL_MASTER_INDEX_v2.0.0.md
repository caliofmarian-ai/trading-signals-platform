# CANONICAL_MASTER_INDEX_v2.0.0

Canonical Name: CANONICAL_MASTER_INDEX  
Version: 2.0.0  
Status: ACTIVE CANONICAL AUTHORITATIVE MASTER INDEX  
Owner: BinaryBot / DROPi Signals  
Date: 2026-09-01  
Supersedes: `CANONICAL_MASTER_INDEX_v1.0.0.md`

---

## 0. Active authority declaration

This document is the sole authoritative Master Index for the canonical documentation graph after the staged-execution + current-scope Trade Physics promotion executed on 2026-09-01.

`CANONICAL_MASTER_INDEX_v1.0.0.md` is superseded and historical only.

Canonical functional inventory: **43 unique active functional specifications**.

The Master Index itself and supporting governance records are not counted in the 43 functional specifications.

---

## 1. Purpose

This index defines:
- the complete active functional inventory;
- cluster hierarchy and authority relationships;
- exact active versions;
- treatment of active, proposed, supporting, superseded, deprecated and intake material;
- current-scope Trade Physics ownership;
- staged-execution ownership and publication boundaries;
- truth-domain separation;
- implementation/audit entry points.

Where a lower-level document contains stale pre-promotion wording, the executed `CANONICAL_ACTIVATION_RECORD_20260901.md`, this Master Index, and canonical path classification determine current status.

---

## 2. Inventory reconciliation

The prior active baseline contained 41 unique functional domains. The Trade Physics program adds two new functional authorities:
- `TRADE_PHYSICS_MODEL_SPEC_v1.0.0.md`;
- `TRADE_PHYSICS_INTELLIGENCE_SPEC_v1.0.0.md`.

All other promoted files replace existing domains.

Post-promotion total: **43 unique functional canonical specifications**.

`CANON_BATCH_EVALUATION` is a governance/evaluation record and is not a functional canonical specification.

---

## 3. Canonical authority hierarchy

### 3.1 Root manifests

| Root manifest | Cluster |
|---|---|
| `CANONICAL_STRATEGY_STACK_v2.0.0.md` | Strategy/runtime strategy cluster |
| `ADMIN_SURFACE_AND_CONTROL_PLANE_CANON_v2.0.1.md` | Admin/control-plane cluster |

### 3.2 Layered policy/mechanics authority

| Policy / Architecture Authority | Mechanics / Bounded Implementation Authority |
|---|---|
| `SYSTEM_ARCHITECTURE_MAP_v3.0.0.md` | `SYSTEM_INVARIANTS_v3.0.0.md`, `MODULE_INTERFACE_SPEC_v3.0.0.md`, `TEST_PLAN_v3.0.0.md` |
| `OBSERVABILITY_SPEC_v3.0.0.md` | `OBSERVABILITY_LOGGING_SPEC_v3.0.0.md`, `EVENT_SCHEMA_SPEC_v3.0.0.md` |
| `SIGNAL_DISTRIBUTION_ARCHITECTURE_v2.0.1.md` | `SIGNAL_DISTRIBUTION_SPEC_v2.0.1.md` |
| `TRADE_PHYSICS_MODEL_SPEC_v1.0.0.md` | ALGO / DecisionObject / Telemetry consumers; Signal Engine is downstream only |
| `TRADE_PHYSICS_INTELLIGENCE_SPEC_v1.0.0.md` | Research / Analytics / Strategy Intelligence / Autonomous Evolution consumers |

### 3.3 Document classes

| Class | Current treatment |
|---|---|
| Active Canonical | Binding authority for its domain. |
| Proposed | Not authoritative. |
| Supporting / Governance Record | Evidence, governance or migration material; cannot override active canon. |
| Superseded | Replaced canonical version; historical only. |
| Deprecated | Historical dead-end; non-authoritative. |
| Intake | Source/provenance material; non-authoritative after absorption. |

---

## 4. Complete active functional inventory

### 4.1 Root manifests

| # | Canonical filename | Version | Status | Domain | Authority role |
|---:|---|---:|---|---|---|
| 1 | `CANONICAL_STRATEGY_STACK_v2.0.0.md` | 2.0.0 | Active Canonical | Strategy architecture | Root manifest for strategy/runtime strategy cluster |
| 2 | `ADMIN_SURFACE_AND_CONTROL_PLANE_CANON_v2.0.1.md` | 2.0.1 | Active Canonical | Admin/control-plane architecture | Root manifest for admin/control plane |

### 4.2 Strategy pipeline cluster

| # | Canonical filename | Version | Status | Domain | Authority role |
|---:|---|---:|---|---|---|
| 3 | `ALGO_SPEC_v3.0.0.md` | 3.0.0 | Active Canonical | Trading algorithm / strategic orchestration | Strategy evaluation/scoring/gating authority |
| 4 | `SR_CORRIDOR_ENGINE_SPEC_v3.0.0.md` | 3.0.0 | Active Canonical | Structural/SR/corridor truth | Directional structural-space authority |
| 5 | `TIME_MODEL_UNIFIED_CANON_v3.0.0.md` | 3.0.0 | Active Canonical | Unified directional time model | Time/speed/expiry semantics authority |
| 6 | `TRADE_PHYSICS_MODEL_SPEC_v1.0.0.md` | 1.0.0 | Active Canonical | Deterministic Trade Physics | S/T/P/V and TPS authority |
| 7 | `DECISION_OBJECT_CANONICAL_SPEC_v2.0.0.md` | 2.0.0 | Active Canonical | Strategy-to-FSM contract | Complete pre-FSM strategic truth contract |
| 8 | `FSM_DECISION_ENGINE_SPEC_v2.0.0.md` | 2.0.0 | Active Canonical | Operational lifecycle FSM | Exact-stage acceptance/handoff authority |
| 9 | `SIGNAL_ENGINE_EXECUTION_SPEC_v3.0.0.md` | 3.0.0 | Active Canonical | Signal execution | SignalEvent candidate/execution-outcome authority |
| 10 | `RISK_MODEL_v3.0.0.md` | 3.0.0 | Active Canonical | Risk/capital protection | Risk filtering/protection authority aligned to canonical structure/time/Trade Physics truth |

### 4.3 Observability / decision evidence

| # | Canonical filename | Version | Status | Domain | Authority role |
|---:|---|---:|---|---|---|
| 11 | `OBSERVABILITY_SPEC_v3.0.0.md` | 3.0.0 | Active Canonical | Observability policy | End-to-end evidence/truth-separation authority |
| 12 | `OBSERVABILITY_LOGGING_SPEC_v3.0.0.md` | 3.0.0 | Active Canonical | Structured logging | Logging mechanics authority |
| 13 | `EVENT_SCHEMA_SPEC_v3.0.0.md` | 3.0.0 | Active Canonical | Event schema | Event families/envelope/correlation authority |
| 14 | `DECISION_AUDIT_SPEC_v3.0.0.md` | 3.0.0 | Active Canonical | Decision audit | Pre-FSM decision/rejection audit authority |
| 15 | `TRADE_TEMPORAL_TELEMETRY_SPEC_v3.0.0.md` | 3.0.0 | Active Canonical | Objective market telemetry | Market truth / Trade Physics feature-label lineage authority |

### 4.4 Signal distribution

| # | Canonical filename | Version | Status | Domain | Authority role |
|---:|---|---:|---|---|---|
| 16 | `SIGNAL_DISTRIBUTION_ARCHITECTURE_v2.0.1.md` | 2.0.1 | Active Canonical | Routing topology | Distribution architecture authority |
| 17 | `SIGNAL_DISTRIBUTION_SPEC_v2.0.1.md` | 2.0.1 | Active Canonical | Entitlement/delivery policy | Route/delivery policy authority |
| 18 | `CHANNEL_CONFIG_SPEC_v2.0.1.md` | 2.0.1 | Active Canonical | Channel configuration | Channel/topic mapping authority |
| 19 | `TELEGRAM_UX_v2.0.1.md` | 2.0.1 | Active Canonical | Telegram UX | User-facing Telegram presentation authority |
| 20 | `AFFILIATE_SIGNAL_DISTRIBUTION_MODEL_v2.0.1.md` | 2.0.1 | Active Canonical | Affiliate distribution | Affiliate distribution/commercial-participation authority |
| 21 | `SIGNAL_ECONOMICS_AND_MONETIZATION_MODEL_v2.0.1.md` | 2.0.1 | Active Canonical | Signal economics | Monetization/economics authority |

### 4.5 Admin / control plane

| # | Canonical filename | Version | Status | Domain | Authority role |
|---:|---|---:|---|---|---|
| 22 | `ADMIN_CONTROL_SPEC_v2.0.1.md` | 2.0.1 | Active Canonical | Admin control surface | Admin command/control authority |
| 23 | `ADMIN_OPERATIONS_SPEC_v2.0.1.md` | 2.0.1 | Active Canonical | Admin operations | Operational procedures authority |
| 24 | `ADMIN_TREE_MAP_v2.0.1.md` | 2.0.1 | Active Canonical | Admin structural map | Admin navigation/hierarchy authority |
| 25 | `CONTROL_PANEL_HIERARCHY_AND_INTELLIGENCE_SPEC_v2.0.1.md` | 2.0.1 | Active Canonical | Control panel/intelligence presentation | Control-panel hierarchy authority |
| 26 | `ROLE_AND_PERMISSION_MATRIX_SPEC_v2.0.1.md` | 2.0.1 | Active Canonical | Roles/permissions | Authorization authority |
| 27 | `STRATEGY_PARAMETER_CONTROL_SPEC_v3.0.0.md` | 3.0.0 | Active Canonical | Strategy/model parameter control | Governed tunable-parameter authority |

### 4.6 Analytics / Research / Intelligence

| # | Canonical filename | Version | Status | Domain | Authority role |
|---:|---|---:|---|---|---|
| 28 | `OUTCOME_TRACKING_SPEC_v3.0.0.md` | 3.0.0 | Active Canonical | Operational outcome reconciliation | Admin/operational outcome truth authority |
| 29 | `PERFORMANCE_ANALYTICS_SPEC_v3.0.0.md` | 3.0.0 | Active Canonical | Performance analytics | Truth-layer-separated analytics authority |
| 30 | `RESEARCH_AND_LEARNING_FRAMEWORK_SPEC_v3.0.0.md` | 3.0.0 | Active Canonical | Research/learning | Hypothesis/experiment/evidence governance authority |
| 31 | `TRADE_PHYSICS_INTELLIGENCE_SPEC_v1.0.0.md` | 1.0.0 | Active Canonical | Trade Physics ML/calibration | Dataset/model/calibration/readiness authority |
| 32 | `STRATEGY_INTELLIGENCE_SYSTEM_v3.0.0.md` | 3.0.0 | Active Canonical | Strategy intelligence | Diagnostic/recommendation intelligence authority |
| 33 | `AUTONOMOUS_STRATEGY_EVOLUTION_SYSTEM_v3.0.0.md` | 3.0.0 | Active Canonical | Controlled evolution | Governed experiment/evolution proposal authority |
| 34 | `COMMUNITY_FEEDBACK_AND_PRIVACY_SPEC_v3.0.0.md` | 3.0.0 | Active Canonical | Community feedback/privacy | Member self-report/privacy authority, separate from market/operational truth |

### 4.7 System architecture / infrastructure

| # | Canonical filename | Version | Status | Domain | Authority role |
|---:|---|---:|---|---|---|
| 35 | `SYSTEM_ARCHITECTURE_MAP_v3.0.0.md` | 3.0.0 | Active Canonical | System architecture | Overall architecture-map authority |
| 36 | `MODULE_INTERFACE_SPEC_v3.0.0.md` | 3.0.0 | Active Canonical | Module interfaces | Cross-module ownership/contracts authority |
| 37 | `SYSTEM_INVARIANTS_v3.0.0.md` | 3.0.0 | Active Canonical | System invariants | Non-negotiable Trade Physics/execution/system rules |
| 38 | `FAILURE_RECOVERY_SPEC_v2.0.1.md` | 2.0.1 | Active Canonical | Failure recovery | Failure/recovery authority |
| 39 | `DEPLOYMENT_PROTOCOL_v2.0.1.md` | 2.0.1 | Active Canonical | Deployment | Deployment/safety authority |

### 4.8 Security / governance / testing / human comprehension

| # | Canonical filename | Version | Status | Domain | Authority role |
|---:|---|---:|---|---|---|
| 40 | `SECURITY_MODEL_v2.0.1.md` | 2.0.1 | Active Canonical | Security | Security/threat authority; delegates RBAC/outcome timing to domain owners |
| 41 | `GOVERNANCE_AND_CHANGE_CONTROL_v2.0.1.md` | 2.0.1 | Active Canonical | Governance/change control | Approval/version/change authority |
| 42 | `TEST_PLAN_v3.0.0.md` | 3.0.0 | Active Canonical | Testing/validation | Validation authority for Trade Physics, exact-stage execution, observability and regression |
| 43 | `HUMAN_COMPREHENSION_AND_SELF_EXPLAINING_CONTROL_SURFACE_CANON_v1.0.1.md` | 1.0.1 | Active Canonical | Human comprehension / operational memory | Self-explaining control-surface and operational-memory authority |

---

## 5. Supporting governance records

Supporting/non-functional records include:
- `canonical/governance_records/CANON_BATCH_EVALUATION_v3.0.0.md`;
- `TRADE_PHYSICS_INTAKE_SOURCE_ABSORPTION_LEDGER_v1.0.0.md`;
- `TRADE_PHYSICS_AND_STAGED_EXECUTION_CONSOLIDATION_PLAN_v1.0.0.md`;
- `CANONICAL_REFERENCE_REPAIR_FINAL_SET_20260901.md`;
- promotion/reference-impact matrices;
- audit, activation and conflict-resolution records.

They cannot override this Master Index or the active functional authorities.

---

## 6. Trade Physics canonical position

Trade Physics is active current-scope canon.

`TRADE_PHYSICS_MODEL_SPEC_v1.0.0.md` owns deterministic physical-feasibility mathematics, S/T/P/V and deterministic TPS `[0,100]`.

`TRADE_PHYSICS_INTELLIGENCE_SPEC_v1.0.0.md` owns dataset/model/calibration/readiness governance and `trade_success_probability` `[0,1]`.

TPS and learned probability are distinct values and must not share identity.

---

## 7. Staged-execution canonical position

The active graph requires:
- explicit FSM requested/accepted stage;
- `stage_handoff_ready` separate from `trade_execution_ready`;
- PRE/CONFIRM/OPEN_NOW candidate eligibility only after exact FSM acceptance;
- SignalEvent candidate != delivery;
- dedicated `signal_execution_result`;
- `EMITTED` only with downstream successful-publication evidence.

---

## 8. Truth-domain separation

Current owners remain separate:
- strategy/pre-FSM truth → ALGO / DecisionObject / Decision Audit;
- deterministic Trade Physics truth → Trade Physics Model;
- FSM lifecycle truth → FSM;
- signal-execution truth → Signal Engine;
- route/publication truth → Distribution / publisher observability;
- objective market truth → Trade Temporal Telemetry;
- operational/admin outcome truth → Outcome Tracking;
- community/member self-report truth → Community Feedback;
- analytics/research/model interpretations → their bounded authorities.

No downstream truth may silently overwrite another truth class.

---

## 9. Superseded baseline

The former active baseline replaced by this promotion is historical only. It includes the prior Root Stack, Master Index, strategy/time/SR/DecisionObject/FSM/Signal Engine/Risk/Observability/Event/Audit/Telemetry/Outcome/Analytics/Research/Intelligence/System/Admin/Distribution/Security/Governance/Test/Human-Comprehension versions listed in the promotion execution manifest.

Those predecessor files are preserved under `canonical/superseded/` and are not implementation authority.

---

## 10. Intake treatment

The source files:
- `AI_TRADE_PHYSICS_SPACE_MODEL_SPEC.md`;
- `TRADE_PHYSICS_SCORE_SPEC.md`;
- `AI_TRADE_PHYSICS_INTELLIGENCE_SPEC.md`
remain provenance only after absorption.

Implementation must cite active canonical successors, not Intake.

---

## 11. Runtime gate after documentation promotion

This documentation promotion does not itself authorize runtime changes.

A fresh canon-to-code audit is mandatory before runtime patching. Known areas for that audit include TPS ownership/formula drift, directional speed, Event Schema runtime drift, PRE/CONFIRM handoff, execution observability and PR #73.

PR #73 remains DO NOT MERGE until that audit decides whether it is corrected, superseded or replaced.

---

## 12. Version history

| Version | Date | Description |
|---|---|---|
| 1.0.0 | 2026-07-12 | Initial authoritative reconciled index. |
| 2.0.0 | 2026-09-01 | Activated structural inventory for staged execution + current-scope Trade Physics; 43 unique functional domains, consolidated truth boundaries, Risk/Community structural successors and final reference-repair versions. |

---

## 13. Final principle

There is exactly one active authority per canonical domain. The current graph contains 43 functional specifications, explicit Trade Physics ownership, explicit execution/publication boundaries, separated truth domains, complete system architecture/invariant/test coverage and no permission to use superseded or Intake material as primary implementation authority.
