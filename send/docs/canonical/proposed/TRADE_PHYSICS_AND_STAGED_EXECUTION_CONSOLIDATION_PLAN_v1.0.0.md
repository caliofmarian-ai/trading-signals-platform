# TRADE_PHYSICS_AND_STAGED_EXECUTION_CONSOLIDATION_PLAN_v1.0.0

Version: 1.0.0  
Status: PROPOSED SUPPORTING GOVERNANCE RECORD — NOT ACTIVE CANONICAL  
Owner: BinaryBot / DROPi Signals  
Date: 2026-09-01

## 1. Purpose

Two Owner-approved structural documentation programs now intersect:

1. staged signal execution / post-FSM observability remediation;
2. current-scope Trade Physics integration.

They overlap in:
- Event Schema;
- Observability Policy;
- Observability Logging;
- Module Interface;
- Signal Engine Execution;
- Root Strategy Stack;
- Master Index;
- reference-only dependency repairs.

This plan prevents parallel proposed documents with the same semantic ownership from becoming competing future authorities.

## 2. Hard rule

There must be only one next promoted successor per canonical ownership domain.

No promotion may leave:
- two different `EVENT_SCHEMA v3` truths;
- two different Observability v3 truths;
- two different Module Interface v3 truths;
- one Signal Engine contract that permits strategic TPS recomputation and another that forbids it;
- a Root Stack that includes staged execution but omits Trade Physics;
- a Root Stack that includes Trade Physics but omits staged execution.

## 3. Consolidation strategy

The earlier staged-execution complete successors remain source material for the combined successor set.

Trade Physics adds the following requirements on top of that source material:

### Event Schema
- deterministic `TPS` is strategy/DecisionObject evidence;
- Trade Physics component fields and feature schema/version must be representable in decision evidence;
- `trade_success_probability` is distinct from TPS and requires model/version/readiness metadata when present;
- telemetry/outcome events must preserve feature/label lineage;
- no generic `TPS` field may ambiguously represent learned probability.

### Observability Policy
- strategy -> Trade Physics -> DecisionObject truth must be reconstructible;
- absence of Trade Physics evidence where required is observable degradation;
- learned probability availability/readiness must be explicit;
- post-FSM execution truth remains separate from strategy truth.

### Observability Logging
- logging must capture deterministic Trade Physics snapshot/version at decision time;
- model prediction/version/readiness must be logged only when a real validated model exists;
- telemetry labels and operational outcomes remain different truth domains.

### Module Interface
- Market/SR/Time/Scoring own upstream Trade Physics inputs/calculation;
- DecisionObject carries Trade Physics truth;
- Signal Engine consumes but does not recompute TPS;
- Telemetry/Analytics/Intelligence consume versioned snapshots and labels.

### Signal Engine Execution
- signal engine must not own or recompute TPS/Trade Physics mathematics;
- it may carry the pre-FSM snapshot/reference downstream;
- staged execution event semantics remain as already proposed.

## 4. Versioning approach

Because the staged-execution successor material already uses major versions such as Event/Observability/Module v3, the consolidated Trade Physics additions should not create a second incompatible file with the same version identity.

The combined package will use the next version identity where necessary, or replace the not-yet-promoted proposal before promotion, provided exactly one final candidate exists per domain.

Version choice must be documented in the final promotion matrix.

## 5. Promotion gate

Promotion is blocked until the combined candidate set satisfies all of:

1. staged-execution truth preserved;
2. Trade Physics truth preserved;
3. no duplicate ownership;
4. no same-version divergent documents;
5. all active references mapped to final successor names;
6. Root Stack and Master Index point only to the final candidate set;
7. source absorption ledger passes;
8. no runtime code change is included.

## 6. Code gate

After combined canonical promotion:

- PR #73/runtime staged-execution code must be re-audited;
- current undocumented TPS code must be re-audited;
- scoring/time/market/corridor/DecisionObject code must be compared to promoted Trade Physics formulas;
- Signal Engine TPS recomputation must be removed or converted to downstream snapshot consumption as required by canon;
- only then may implementation proceed.

## 7. Final principle

The project will not solve one canonical drift by introducing another.

Staged execution and Trade Physics are separate conceptual changes, but their shared contracts must be consolidated into a single future canonical graph before runtime remediation.
