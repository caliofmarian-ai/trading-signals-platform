# TSP-BILL-05 — Subscription Registry + Entitlement Resolver

Issue: #162  
Parent: #157  
Depends on merged #158 and #159  
Branch: `billing/tsp-bill-05-subscription-entitlement`  
Baseline: `main = ad30115c94fa581ed859539792ab2d80f92669ac`

## Authority owned by this lane

TSP-BILL-05 owns the persisted subscription lifecycle and the single authoritative entitlement resolution consumed by later Telegram-membership/distribution integration.

Payment truth remains owned by #159. A subscription transition may consume a unique `SETTLED + MATCHED` payment-ledger record, but payment truth is not itself subscription or entitlement truth.

The event-sourced subscription registry is persisted at:

`BINARYBOT_BASE_DIR/billing/subscription_events.jsonl`

In governed Railway production that resolves below `/data/billing/`.

Every subscription event carries a globally contiguous `subscription_seq`, a unique `subscription_event_id`, a per-subscription monotonic `entitlement_version`, and a `previous_subscription_event_id` chain. Corrupt JSON, duplicate IDs/sequences, broken version chains, invalid plan/tier relationships, or multiple subscription identities for one subscriber/product fail closed.

## Subscription states

Current lifecycle states:

- `ACTIVE`
- `PAYMENT_DUE`
- `PAYMENT_FAILED`
- `EXPIRED`
- `GRACE_HOLD`
- `INTENT_PAYMENT_PENDING`
- `CANCELED_AT_PERIOD_END`
- `CHARGEBACK_OPEN`
- `REFUND_HOLD`

The resolver exposes a separate access state:

- `ACTIVE`
- `SUSPENDED`
- `HOLD`
- `FREE_FALLBACK`

This separation prevents a subscription label from being treated as direct Telegram membership authority.

## Expiry / grace / intent policy

For paid plans:

1. paid entitlement is active until `expires_at_epoch`;
2. at expiry, paid access becomes `SUSPENDED` even if deadline reconciliation has not yet run;
3. persisted lifecycle enters `GRACE_HOLD` for 48 hours;
4. after +48h without a verified payment, lifecycle becomes `PAYMENT_DUE`;
5. a recorded paid-plan payment intent can create `INTENT_PAYMENT_PENDING` for at most 24 hours;
6. when that 24h window expires, the lifecycle returns to the state implied by the underlying expiry policy;
7. a FREE subscriber with an unverified paid intent remains FREE and returns to FREE/ACTIVE when the intent window expires.

An explicit cancellation or scheduled downgrade to FREE is user-directed policy and can become effective at period end without the no-response notification gate.

## Critical #162 / #163 boundary — +72h automatic FREE downgrade

Issue #162 provides the +72h timing boundary, but Issue #163 requires mandatory notification/delivery evidence before a no-payment/no-intent subscriber is automatically downgraded to FREE.

Therefore this implementation deliberately does **not** infer client silence from time alone.

`evaluate_deadlines(..., downgrade_evidence_id=None)` behaves fail-closed:

- once +72h is reached, state remains `PAYMENT_DUE` / `PAYMENT_FAILED`;
- paid access remains `SUSPENDED`;
- resolver reason becomes `AUTO_DOWNGRADE_BLOCKED_PENDING_NOTIFICATION_EVIDENCE`;
- no FREE downgrade event is written.

Only a non-empty `downgrade_evidence_id` supplied by the future #163 notification-policy authority permits the final persisted transition to `EXPIRED`, after which entitlement resolves to FREE fallback. The evidence identifier is stored as `last_downgrade_evidence_id` on the transition.

This prevents `FAILED BOT DELIVERY` from being silently converted into `CLIENT SILENCE` before #163 exists.

## Activation and renewal

A paid activation requires:

- exactly one recorded payment-intent creation;
- exactly one `SETTLED + MATCHED` payment record from #159;
- matching subscriber/product/plan attribution;
- a non-overlapping governed paid period.

Replaying the same settlement cannot increment `entitlement_version` again.

Same-tier renewal starts at or after the prior paid period boundary. A lower paid tier cannot become effective mid-period. After the prior period has expired, a verified lower-tier payment may activate without requiring a stale pre-expiry downgrade schedule because the expiry/non-payment policy boundary already applies.

## Upgrade / downgrade

Mid-period paid upgrade is allowed only after verified payment and deterministic pro-rata validation.

Proration uses:

- full-period source and target price evidence;
- actual remaining seconds in the current period;
- integer minor units;
- `ROUND_HALF_UP`;
- exact equality between computed `net_due_minor` and the settled payment amount;
- currency equality.

Because #158 currently has paid prices `NOT_CONFIGURED`, the source/target full-period amounts are explicit evidence supplied to the upgrade transition. If catalog pricing becomes configured later, the resolver additionally requires that evidence to match catalog pricing.

Paid downgrade before expiry is schedule-only and becomes effective next billing period after the required verified payment. Explicit downgrade to FREE can become effective at period end without a new paid settlement.

## Cancellation / reversal

Cancellation baseline is `CANCELED_AT_PERIOD_END`: paid access remains active until period end, then resolves to FREE.

A matched current-period `REFUNDED` or `CHARGEBACK` payment reversal is consumed from #159 as a separate persisted subscription transition:

- refund -> `REFUND_HOLD`;
- chargeback -> `CHARGEBACK_OPEN`;
- entitlement access -> `HOLD`.

A reversal of an older payment cannot place a newer subscription period on hold.

## Entitlement authority

`resolve_entitlement()` is the sole authoritative read surface introduced by this lane. It returns:

- `entitlement_id` and monotonic `entitlement_version`;
- subscriber/product/subscription identity;
- subscription state;
- resolved plan/tier;
- access state;
- source subscription event;
- expiry/grace/auto-downgrade boundaries;
- pending/scheduled plan information;
- last downgrade-policy evidence where applicable;
- an explicit reason.

No-subscription fallback is deterministic FREE version `0` and does not require a database write.

The resolver is time-aware: a stale runtime scheduler cannot leave expired paid access marked ACTIVE.

## Downstream ownership boundaries

This lane does not:

- call Revolut or KuCoin (#160/#161);
- send billing notifications or decide whether mandatory notifications were successfully delivered (#163);
- own manual payment proof/support cases (#164);
- mutate Telegram membership (#165);
- own billing Admin UI (#166);
- create commercial/legal/tax readiness (#168);
- constitute paid end-to-end acceptance (#169).

Telegram membership must consume entitlement truth later; it must not infer access directly from payment records or subscription fields.

## Regression evidence

The dedicated lifecycle suite covers:

- deterministic FREE fallback/bootstrap;
- activation only from unique settled/matched payment;
- replay-safe entitlement versioning;
- fail-safe paid suspension at expiry;
- GRACE_HOLD and PAYMENT_DUE catch-up;
- +72h notification-evidence gate;
- paid intent crossing +72h for no more than 24 hours;
- FREE pending-intent expiry;
- cancellation at period end, including pending intent crossing expiry;
- scheduled paid downgrade;
- post-expiry lower-tier activation;
- invalid/non-owned plan rejection;
- mid-period downgrade rejection;
- deterministic proration upgrade and amount mismatch rejection;
- non-overlapping renewal;
- refund/chargeback HOLD;
- stale-payment reversal rejection;
- payment-failed access behavior;
- registry corruption fail-closed behavior.

Exact-head CI must be re-run after this evidence commit before merge.

## Safety

No strategy mathematics, FSM semantics, market-data provider policy, EUR/USD scope, Telegram RBAC, signal-distribution behavior or broker execution is changed by TSP-BILL-05.
