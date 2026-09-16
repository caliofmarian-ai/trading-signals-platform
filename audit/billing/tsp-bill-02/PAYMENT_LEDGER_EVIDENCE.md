# TSP-BILL-02 — Payment Intent + append-only Payment Ledger / Audit core

Issue: #159  
Parent: #157  
Depends on: #158  
Branch: `billing/tsp-bill-02-payment-ledger`  
Baseline: `main = 49983d9f09d8424303f2f67622919d9ad7ac27f9`

## Purpose

Create the provider-neutral payment truth authority required before provider integrations or subscription/entitlement resolution.

This lane owns payment intent, provider-payment evidence, reconciliation and immutable payment history. It does not own subscription activation, entitlement resolution or Telegram membership.

## Persistence authority

The ledger path is derived through the canonical storage layer:

`BINARYBOT_BASE_DIR/billing/payment_ledger.jsonl`

In Railway production, the governed base directory is `/data`, so the effective path is:

`/data/billing/payment_ledger.jsonl`

Every mutation executes under `core.storage.with_lock("billing_payment_ledger")` and persists with `core.storage.append_jsonl()`. The existing storage layer provides cross-process exclusion, stale-lock recovery, append-only writes, flush and fsync durability.

The JSONL ledger is the payment-history source of truth. There is no mutable shadow index that can override it.

## Payment states

Provider-neutral states owned here:

- `CREATED`
- `PENDING`
- `SETTLED`
- `FAILED`
- `EXPIRED`
- `REFUNDED`
- `CHARGEBACK`
- `UNKNOWN`

`CREATED` belongs to locally created payment intents. Provider ingestion cannot submit `CREATED` as provider truth.

## Event families

- `PAYMENT_INTENT_CREATED`
- `PROVIDER_PAYMENT_EVENT`
- `PAYMENT_RECONCILIATION_EVIDENCE`
- `PAYMENT_REVERSAL_EVENT`

Every appended ledger record receives a unique `ledger_event_id` and contiguous positive `ledger_seq`.

## Payment intent contract

A payment intent binds:

- `payment_intent_id`
- `subscriber_ref`
- `strategy_product_id`
- `plan_id`
- `amount_minor`
- `currency`
- `payment_method`
- intended provider
- `idempotency_key`
- `audit_correlation_id`

Product/plan validity is resolved through the shared #158 billing contract. FREE is not a paid payment-intent target.

An identical payment-intent idempotency replay returns the existing record without append. Reuse of the same idempotency key for different intent evidence fails closed.

## Provider-event contract

Provider ingestion accepts normalized evidence only. It stores stable evidence references/hashes rather than provider secrets or raw secret-bearing payloads.

Required evidence includes:

- `payment_intent_id`
- provider identity
- normalized payment state
- raw provider state label
- amount and currency
- `raw_event_hash`
- caller `idempotency_key`
- at least one of `provider_event_id`, `provider_tx_ref`, `wallet_tx_id`
- received timestamp
- settled timestamp when applicable
- audit correlation

The intent is the only authority for subscriber/product/plan attribution. Provider input is not allowed to assert a different subscriber, product or plan.

## Exactly-once semantics

Exactly-once protection operates at multiple layers:

1. caller `idempotency_key`;
2. exact provider-evidence equivalence independent of caller idempotency;
3. strong provider event identity (`provider_event_id` / raw event hash) collision detection;
4. at most one `SETTLED + MATCHED` record per payment intent;
5. at most one matched compensating reversal per payment intent in the current provider-neutral contract.

A replay of the same provider event with a different caller idempotency key returns the already recorded provider event and does not append another payment event.

A second distinct settlement or reversal does not mutate prior truth. It becomes `PAYMENT_RECONCILIATION_EVIDENCE` with payment state `UNKNOWN` and `CONTRADICTORY` reconciliation status.

## Reconciliation behavior

`UNMATCHED` means the provider evidence cannot yet be attributed to a recorded payment intent.

`CONTRADICTORY` covers evidence such as:

- idempotency key reused for different provider evidence;
- provider event identity reused with different evidence;
- provider / amount / currency disagreement with the intent;
- second settlement attempt;
- non-reversal event after settlement;
- reversal before settlement;
- second distinct reversal.

Reconciliation entries use a deterministic fingerprint derived from stable evidence plus reason/result. Therefore replaying the same unmatched or contradictory evidence with a different caller idempotency key does not append duplicate reconciliation records.

Reconciliation evidence is not a settled payment and must be routed to later support/reconciliation workflows instead of creating entitlement.

## Reversal contract

`REFUNDED` and `CHARGEBACK` are compensating append-only events. A valid reversal:

- requires an existing unique matched settlement;
- appends a new `PAYMENT_REVERSAL_EVENT`;
- references the original settlement through `reversal_of_ledger_event_id`;
- never edits or deletes the settlement.

Multiple distinct reversals for one intent are fail-closed as contradictory under the current contract rather than guessed as partial/multiple refunds. A future partial-refund model would require an explicit governed extension.

## Downstream boundary

For #162 Subscription Registry + Entitlement Resolver, the only positive payment evidence exposed by this lane is a unique ledger record satisfying both:

- `payment_state == SETTLED`
- `reconciliation_result == MATCHED`

Even that record is payment truth only. It is not itself subscription-active truth or entitlement truth.

The following must never directly create entitlement:

- payment intent creation;
- `PENDING`;
- `UNMATCHED`;
- `CONTRADICTORY`;
- `UNKNOWN`;
- a manual payment proof merely being submitted;
- a provider event that has not been reconciled to an intent.

## Corruption handling

Ledger loading fails closed on:

- malformed JSON;
- non-object records;
- missing/duplicate `ledger_event_id`;
- invalid/duplicate sequence values;
- non-contiguous ledger sequence;
- more than one matched settlement or reversal where uniqueness is required.

The code does not silently truncate, repair or overwrite corrupt payment history.

## Test coverage

`tests/billing/test_payment_ledger.py` covers:

- payment-intent persistence and idempotency;
- rejection of FREE as a paid intent;
- conflicting intent idempotency reuse;
- PENDING -> SETTLED evidence;
- attribution from recorded intent;
- provider-event replay with a different idempotency key;
- provider event identity collision;
- second settlement contradiction;
- unmatched evidence and replay deduplication;
- provider/amount/currency mismatch;
- refund as immutable compensating append;
- chargeback replay deduplication;
- second reversal contradiction;
- reversal without settlement;
- missing provider reference rejection;
- raw-payload/secrets absence;
- malformed JSON and duplicate-sequence corruption.

## Explicit non-ownership

TSP-BILL-02 does not implement:

- Revolut Merchant API integration (#160);
- KuCoin watcher/reconciliation (#161);
- subscription lifecycle or entitlement resolution (#162);
- notifications/client intent timing (#163);
- manual proof/support cases (#164);
- Telegram membership mutation (#165);
- billing Admin UI (#166);
- commercial/legal/tax go-live (#168);
- paid end-to-end acceptance (#169).

No strategy mathematics, FSM semantics, market-data provider policy, EUR/USD scope, Telegram RBAC, signal distribution or broker execution is modified by this lane.
