# R-020 — Decision Audit Identity Authority and Implementation Report

Status: IMPLEMENTATION IN PROGRESS
Issue: #146
Branch: `remediation/audit-2026-09-01-r020-decision-audit-identity`
Base main: `4bfb770ee8a380ce49d03fd46e9617c515227128`

## Purpose

R-020 materializes a stable, auditable identity chain across the existing decision lifecycle without recomputing strategy truth downstream.

This change does **not** change strategy thresholds, scoring, Market Model, SR/Structure, Model Time, Execution Time, FSM policy, distribution entitlements, provider selection, two-second evaluation semantics, Telegram authorization, or broker-execution governance.

## Canonical authority reviewed

The implementation was checked against the active authority selected by `CANONICAL_MASTER_INDEX_v2.0.0`, including:

- `DECISION_AUDIT_SPEC_v3.0.0.md`
- `DECISION_OBJECT_CANONICAL_SPEC_v2.0.0.md`
- active Event Schema v3 correlation fields
- existing SignalEvent / FSM / Trade Temporal Telemetry contracts

The active Decision Audit authority places decision truth before FSM. FSM, distribution, telemetry and outcome layers may correlate to that truth but must not overwrite or recompute it.

## Identity meanings

### `setup_correlation_id`

Authority/source: `DecisionObject.setup.cycle_id`.

Meaning: the shared setup/evaluation-cycle correlation boundary. It may intentionally be shared by multiple evaluations in the same setup/candle context.

It is **not** the unique identity of one exact DecisionObject truth snapshot.

### `decision_id`

Authority/source: materialized exactly once by `DecisionObject` before FSM.

Meaning: deterministic fingerprint of one exact pre-FSM DecisionObject semantic truth snapshot.

The fingerprint includes the decision kind, signal identity when assigned, setup, Market Model context, Structure context, Model Time context, Score/Trade Physics context, strategic flags, reject semantics, FSM inputs, explanations, schema version, producer and compatibility mode.

Consequences:

- exact retry/replay of the same semantic DecisionObject produces the same `decision_id`;
- two evaluations on the same candle/setup produce different `decision_id` values when their pre-FSM truth differs;
- downstream modules never generate a replacement `decision_id`.

Current format: `dec-v1-<24 hex chars>`.

The format/version is an implementation identity contract, not a trading threshold or market inference.

### `decision_audit_id`

Authority/source: derived once from the materialized `decision_id` by DecisionObject.

Meaning: stable audit-facing reference for that exact decision evaluation.

Current format: `da-v1-<24 hex chars>`.

Downstream code propagates this value verbatim.

### `fsm_transition_id`

Authority/source: Persistent FSM boundary.

Meaning: deterministic identity of the FSM interpretation/result for one already-materialized decision. It is based on the upstream decision identity plus requested/accepted stage, prior/resulting state and actual FSM reason.

It does not recalculate strategy truth.

Current format: `fsm-v1-<24 hex chars>`.

### `execution_attempt_id`

Authority/source: existing Signal Execution Gate authority.

Meaning: identity of the pre-distribution execution-gate attempt. R-020 preserves the existing authority and propagates that already-created value into SignalEvent instead of rebuilding it there.

### `signal_id`

Authority/source: existing opportunity/signal identity mechanism.

Meaning: opportunity continuity across actionable lifecycle stages where assigned. It is not substituted for `decision_id` because multiple strategy evaluations may exist for the same opportunity.

### Event IDs and publication evidence IDs

Event IDs remain identities of individual observability records. Distribution publication evidence (`route_result_event_id`, visibility event identity, destination/message evidence) remains Distribution-owned evidence.

R-020 does not collapse these IDs into the decision identity. Objective Trade Temporal Telemetry retains both decision lineage and publication evidence, which creates an auditable join without allowing Distribution to rewrite the DecisionObject.

## Materialized runtime chain

The intended chain is:

`setup_correlation_id`
→ exact pre-FSM `decision_id` / `decision_audit_id`
→ FSM `fsm_transition_id`
→ Signal Execution Gate `execution_attempt_id`
→ SignalEvent carrying all upstream identities
→ Distribution consuming the same SignalEvent and producing publication evidence
→ objective Trade Temporal Telemetry preserving decision/FSM/execution identity plus publication evidence
→ objective expiry/post-expiry outcome updates on the same persisted telemetry record.

No downstream layer hashes the DecisionObject again.

## Distribution linkage boundary

Distribution already owns route-attempt/result/visibility event identities and dedup evidence. R-020 does not replace those authorities.

Exact decision lineage reaches Distribution in the SignalEvent consumed by the router. On successful OPEN_NOW publication, the same SignalEvent is supplied to objective Trade Temporal Telemetry together with Distribution publication evidence. The telemetry record therefore contains:

- setup correlation;
- decision identity;
- decision audit identity;
- FSM transition identity;
- execution-attempt identity;
- signal identity;
- route-result / visibility publication evidence.

This is a direct evidence chain; no strategy truth is recomputed from route output.

## Outcome boundary

Objective MARKET_TRUTH outcome evolution occurs on the Trade Temporal Telemetry record and preserves its lineage fields.

COMMUNITY_TRUTH remains a separate source. R-020 does not fabricate decision lineage onto community feedback records that do not possess authoritative linkage.

## Fail-closed behavior

Signal Execution Gate now refuses to use an FSM result whose `decision_id` or `decision_audit_id` does not match the DecisionObject presented to the gate.

This prevents a changed DecisionObject from reusing a prior FSM acceptance merely because symbol/signal/stage identifiers still appear compatible.

Missing or mismatched lineage does not authorize publication or broker execution.

## Restart and retry semantics

The pre-FSM decision fingerprint contains semantic truth, not wall-clock generation time or random UUID state. Exact semantic replay therefore preserves identity.

A changed 2-second evaluation on the same candle receives a different decision identity when its pre-FSM evidence changes.

FSM transition identity similarly uses semantic FSM result fields rather than the runtime call timestamp.

Execution attempts remain independently identifiable through the existing execution-attempt authority.

## Security and safety

The materialized identifiers contain hashes only; they do not expose secrets, provider keys, Telegram tokens or account credentials.

Broker execution remains disabled. Shadow mode and existing distribution governance are unchanged.

## Validation targets

R-020 is not complete until all of the following are evidenced on the exact final PR head:

- deterministic exact-replay decision identity;
- distinct decision identity when pre-FSM truth changes within the same setup/candle;
- DecisionObject serialization contains the materialized IDs;
- FSM propagates the exact upstream decision IDs and materializes its own bounded transition ID;
- Signal Execution Gate detects mismatched DecisionObject/FSM identity fail-closed;
- SignalEvent preserves setup/decision/audit/FSM/execution identity without recomputation;
- objective OPEN_NOW telemetry reports `linkage_state=COMPLETE` for a production-built candidate;
- legacy/hand-built records with genuinely absent linkage remain explicit rather than fabricated;
- provider selector regression passes;
- Telegram Admin regression passes;
- full repository regression suite passes.
