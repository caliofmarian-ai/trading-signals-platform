# TSP-BILL-06 — Notification Scheduler + Client Intent Lifecycle Evidence

Issue: #163  
Parent epic: #157  
Branch: `billing/tsp-bill-06-notification-intents`  
Baseline: `main = 4b4de72504554b39b09a30d9dd4aea5726af4dcb`

## Scope

This lane implements restart-safe subscription notification scheduling, delivery evidence, client-intent capture and the governed evidence handoff required by #162 before the no-response +72h FREE downgrade.

It does not create payment truth, directly activate entitlement, mutate Telegram channel membership or change strategy/FSM/provider-market-data behavior.

## Truth boundaries

The implementation preserves:

- `NOTIFICATION SENT != PAYMENT`
- `NOTIFICATION SENT != ENTITLEMENT`
- `FAILED BOT DELIVERY != CLIENT SILENCE`
- `CLIENT INTENT != PAYMENT VERIFIED`
- `CLIENT INTENT != ENTITLEMENT MUTATION`
- `SUBSCRIBER IDENTITY != TELEGRAM DELIVERY ADDRESS`

Billing notification/client-intent evidence is append-only under:

`BINARYBOT_BASE_DIR/billing/notification_events.jsonl`

On governed Railway production, `BINARYBOT_BASE_DIR=/data`, so the effective path is `/data/billing/notification_events.jsonl`.

## Notification schedule

The scheduler owns these lifecycle points:

- `T_MINUS_3D`
- `T_MINUS_1D`
- `T0`
- `PLUS_24H`
- `PLUS_48H`

A point that predates the actual paid period start is excluded from required evidence because there was no valid scheduling opportunity for it.

Each notification has a deterministic `notification_key` tied to subscription identity, period expiry and lifecycle point. A successful delivery is never sent again for the same key.

## Delivery evidence and retries

Delivery results are persisted as:

- `SENT`
- `FAILED`
- `FAILED_TERMINAL`

Failures use bounded persisted retry/backoff. A failed or terminally failed Telegram delivery is not interpreted as user silence and therefore cannot support an automatic FREE downgrade.

The runtime scheduler is called only after a successful Telegram `getUpdates` response and is throttled to at most one scan per minute per process. Scheduler errors are caught and logged so they do not terminate the Telegram poller.

## Subscriber identity and Telegram address

The commercial identity is `subscriber_ref`.

Telegram delivery uses an explicit private-DM binding containing:

- `telegram_user_id`
- `telegram_chat_id`

The implementation does not infer either Telegram identifier from `subscriber_ref`. Current billing notifications require an explicitly bound private chat where `telegram_chat_id == telegram_user_id`.

Callbacks verify both the delivery event identity and the latest delivery binding. A callback from the wrong Telegram identity or an old binding fails closed.

## Client actions

Telegram billing notifications expose governed intent actions:

- `KEEP_CURRENT_PLAN`
- `UPGRADE`
- `DOWNGRADE`
- `CANCEL`
- `PAYMENT_NOT_DETECTED`
- `SUPPORT`

Callbacks use bounded `BILL:I:` payloads that remain under Telegram's callback-data size limit.

Client intent is deterministic per subscription period. Replaying the same choice is idempotent. A later different choice for the same subscription period becomes the latest intent state rather than creating an unrelated competing intent identity.

Plan-changing callbacks resolve target plan IDs from the shared #158 billing catalog; they do not hardcode commercial plan IDs into presentation transport logic.

## Subscription transition boundary

`CANCEL` delegates to #162 `cancel_at_period_end()`.

A governed paid `DOWNGRADE` delegates to #162 `request_downgrade()`.

`KEEP_CURRENT_PLAN` and `UPGRADE` record intent only; payment remains required before subscription/entitlement can change.

`PAYMENT_NOT_DETECTED` and `SUPPORT` become `SUPPORT_REQUIRED` evidence for the later support-case lane.

## Payment-intent handoff

The payment handoff validates that the payment-intent creation record matches the recorded client intent on all of:

- `subscriber_ref`
- `strategy_product_id`
- requested `plan_id`

Only after that validation does it delegate to #162 `record_payment_intent_pending()`.

This keeps payment truth in #159 and subscription pending state in #162.

## +72h automatic FREE downgrade evidence

#162 deliberately refuses to grant automatic FREE at +72h based on time alone.

This lane may create a `downgrade_evidence_id` only when all applicable prerequisites are proven:

1. +72h has been reached;
2. every required lifecycle notification has a persisted `SENT` delivery event;
3. no active client intent exists for the subscription period;
4. no `SETTLED + MATCHED` payment remains unconsumed by subscription history.

The proof references the concrete delivery event IDs and is deterministic/idempotent.

If any delivery is missing/failed, a client intent exists, or an unconsumed verified payment exists, the proof is not created and the paid entitlement remains suspended under #162 rather than being silently downgraded.

## Multi-subscriber safety

The notification event stream uses one repository-wide contiguous sequence under the canonical storage lock. Tests include multiple subscribers in the same scheduler cycle to ensure per-subscriber work cannot reuse or duplicate event sequence values.

## Telegram runtime integration

`send/runtime/telegram_updates.py` integrates billing in two bounded places:

- after a successful poll heartbeat, invoke the throttled billing scheduler through an exception-isolating wrapper;
- intercept `BILL:I:` callback payloads before the existing VOTE / APP / ADMIN callback dispatch.

Existing voting, Admin UI, strategy, distribution and provider-market-data paths are otherwise unchanged.

## Regression coverage

Dedicated tests cover:

- explicit/private Telegram delivery binding and replay;
- each lifecycle notification delivered once;
- retry/backoff and no false silence;
- all required deliveries -> +72h proof -> governed FREE transition;
- missing/failed delivery blocks downgrade;
- callback identity and stale-context checks;
- replay-safe client intent;
- upgrade/downgrade target-plan binding;
- cancellation-at-period-end without immediate access loss;
- payment-intent handoff into #162 pending state;
- unconsumed SETTLED payment blocks downgrade;
- two-subscriber contiguous event sequencing;
- runtime callback interception;
- callback failure isolation;
- scheduler failure isolation from poller liveness.

## CI evidence before final evidence-only commit

Head `855c2c12f510bfee5c5f6d4cee5382247d550471` passed `Required Repository CI` run `35112680153` with:

- repository governance checks: PASS;
- provider selector regression: PASS;
- Telegram Admin regression: PASS;
- critical canonical contract regressions: PASS;
- full repository suite: **1404 passed**.

This evidence file itself moves the branch head. Merge acceptance therefore still requires a fresh exact-head `Required Repository CI` result after this commit.

## Explicit non-ownership

This lane does not implement:

- Revolut Merchant provider integration (#160);
- KuCoin provider integration (#161);
- support-case/manual-proof processing (#164);
- Telegram membership reconciliation (#165);
- billing Admin surfaces (#166);
- tax/legal/commercial go-live approval (#168);
- end-to-end paid acceptance (#169).

No broker execution is enabled.