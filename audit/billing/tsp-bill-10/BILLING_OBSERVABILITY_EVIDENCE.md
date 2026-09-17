# TSP-BILL-10 — Billing observability, reconciliation evidence and incident escalation

Issue: #167  
Parent: #157  
Baseline: `4b3eeeb913db9c545ad5da482dee13935dc70b81`

## Authority boundary

`send/billing/billing_observability.py` is a `READ_ONLY_DERIVED` projection over existing billing truth logs.

It does **not** create or mutate:

- Payment Ledger truth;
- subscription truth;
- entitlement truth;
- Telegram membership truth;
- provider payment truth;
- strategy/FSM/broker execution truth.

Its only optional write is a bounded, rebuildable observability snapshot ring under `observability/billing_observability_snapshots.json`. Source JSONL truth logs are never rotated, truncated, or rewritten by this module.

## Source surfaces

The projection consumes validated public readers from:

- `send/billing/payment_ledger.py`;
- `send/billing/subscription_registry.py`;
- `send/billing/notification_scheduler.py`;
- `send/billing/support_cases.py`;
- `send/billing/membership_reconciler.py`;
- `send/billing/revolut_merchant.py`;
- `send/billing/kucoin_watcher.py`.

Source-state semantics are explicit:

- missing source file -> `UNKNOWN`, `event_count = null`;
- existing validated empty source -> `PASS`, `event_count = 0`;
- unreadable/corrupt/contract-invalid source -> `FAIL`, `event_count = null`.

This prevents missing evidence from becoming a synthetic zero.

## Correlation

The normalized timeline exposes only allow-listed fields and correlates across the governed identifiers:

- `payment_intent_id`;
- `case_id`;
- `subscriber_ref`;
- `subscription_id`;
- `entitlement_id`;
- `reconciliation_id`;
- `audit_correlation_id`.

`reconstruct_transition(...)` performs a transitive closure across these identifiers. It reports persisted evidence only; it does not infer missing transitions.

## Secret and sensitive-payload boundary

Normalized observability events do not copy arbitrary source payloads. Free-form support messages, Telegram tokens/IDs, provider secrets, raw payment-proof contents, raw provider hashes, addresses/memos, and arbitrary error/detail fields are excluded from the normalized timeline by allow-list.

Provider credentials remain environment-only in their owning adapters and are not required for the projection.

## Provider health

Provider health is derived only from persisted adapter evidence:

- Revolut: provider-unavailable vs successfully bound/recovered/reconciled/recurring provider operations;
- KuCoin: provider-unavailable vs observed WebSocket deposit awareness or REST deposit reconciliation.

No provider call is executed by observability itself.

No provider evidence -> health `UNKNOWN` rather than `HEALTHY`.

Repeated consecutive provider-unavailable evidence produces a separate `REPEATED_PROVIDER_FAILURE` critical incident once the configured threshold is reached.

## Backlog and incident separation

The snapshot keeps distinct counters for:

- pending/unknown payment intents;
- unmatched payment evidence;
- contradictory payment evidence;
- KuCoin manual review;
- Revolut unmatched webhook evidence;
- open support cases;
- failed notification deliveries;
- subscription hold states;
- membership not in sync;
- `ACCESS_LEAK_RISK`.

Critical incidents are emitted separately for:

- `CONTRADICTORY_PROVIDER_EVIDENCE`;
- `ACCESS_LEAK_RISK`;
- `REPEATED_PROVIDER_FAILURE`.

Provider outage, reconciliation backlog and access leakage are therefore not collapsed into one status.

## Duplicate visibility

For each validated source, the projection reports:

- number of persisted events carrying an `idempotency_key`;
- number of duplicate persisted idempotency keys;
- per-source and overall integrity status.

If any source is unavailable, the aggregate duplicate assessment remains `UNKNOWN` unless an actual persisted duplicate already proves `FAIL`.

This does not invent suppressed attempts that were deliberately not persisted by the owning truth layer.

## Bounded retention / rotation

Derived observability snapshots use the canonical atomic JSON writer and a bounded ring:

- default maximum: `200` snapshots;
- configurable via `BILLING_OBSERVABILITY_MAX_SNAPSHOTS`;
- oldest derived snapshots are dropped when the ring is full;
- `dropped_snapshot_count` is retained;
- truth-source JSONL files are not modified.

Repeated-provider-failure threshold is configurable through `BILLING_OBSERVABILITY_PROVIDER_FAILURE_THRESHOLD` and defaults to `3` consecutive persisted provider-unavailable observations.

## Operator-readable proof

`render_operator_summary(...)` produces a compact proof summary containing:

- per-source `PASS` / `FAIL` / `UNKNOWN` and measured event count;
- provider health;
- backlog counters with `UNKNOWN` retained explicitly;
- observed critical-incident count plus incident assessment status.

An observed count of `0` is not represented as proof of no incident when required source evidence is missing.

## Verification status

Before exact-head repository CI:

- `SOURCE VERIFIED = PASS` for repository authority boundaries and existing billing source contracts.
- `CI VERIFIED = PENDING`.
- `DEPLOYED = PENDING`.
- `PROVIDER VERIFIED = NOT APPLICABLE` — this lane makes no provider calls.
- `BILLING VERIFIED = PENDING` until deterministic tests and repository CI pass.
- `MEMBERSHIP VERIFIED = NOT APPLICABLE` to mutation; membership evidence is read-only input.
- `END-TO-END ACCEPTED = NOT APPLICABLE`; final independent acceptance remains #169.

No paid product becomes `SELLABLE` from this lane. #168 and #169 remain separate gates.
