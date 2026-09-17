# TSP-BILL-04 — KuCoin account watcher and crypto deposit reconciliation evidence

Issue: #161  
Parent: #157  
Baseline: `fa2c3365d329075ed8185a8ffeb8155cd0e6d357`

## Scope

`send/billing/kucoin_watcher.py` implements a read-only KuCoin payment observer/reconciler that consumes the existing append-only Payment Ledger from #159. It does not mutate subscription, entitlement, Telegram membership, strategy, FSM, or broker-execution truth.

## Provider contract reviewed

The implementation was checked against current official KuCoin documentation on 2026-09-17:

- private REST authentication: `https://www.kucoin.com/docs-new/authentication`;
- Classic Spot/Margin private WebSocket token: `POST /api/v1/bullet-private`;
- Classic private balance topic: `/account/balance`, where `main.deposit` is a deposit-awareness event;
- Classic Deposit History: `GET /api/v1/deposits`;
- KuCoin EU uses `https://api.kucoin.eu`, while global Classic uses `https://api.kucoin.com`.

The adapter supports explicit `global` / `eu` site selection and fails closed for UTA. It does not infer account jurisdiction or account type from deployment location.

## Truth boundary

`KUCOIN WEBSOCKET DEPOSIT EVENT != SETTLED PAYMENT`

A WebSocket `main.deposit` event is only a trigger. Payment evidence is produced only after REST Deposit History returns provider data and deterministic attribution to one existing governed `payment_intent_id` succeeds. The adapter never creates an alternative payment ledger.

## Deterministic attribution

A REST deposit may match an open KuCoin `CRYPTO` payment intent only when:

1. the asset is compatible with the existing Payment Ledger currency contract;
2. a governed minor-unit scale is supplied by the caller;
3. amount conversion is exact at that scale; and
4. exactly one open intent has the same currency and exact `amount_minor`.

Non-provable outcomes are recorded as `MANUAL_REVIEW_REQUIRED` and do not create `SETTLED` truth:

- `UNMATCHED`;
- `AMBIGUOUS`;
- `UNDERPAID`;
- `OVERPAID`;
- `NORMALIZATION_REVIEW_REQUIRED`;
- `LEDGER_CURRENCY_CONTRACT_UNSUPPORTED`.

## Existing #159 currency boundary

`send/billing/payment_ledger.py` currently requires `currency` to be exactly three alphabetic characters. A four-character asset such as `USDT` therefore cannot currently be written as matched provider evidence without changing #159.

TSP-BILL-04 does not bypass or silently widen that contract. Such deposits fail closed into `MANUAL_REVIEW_REQUIRED`. Accepted crypto assets/networks and any future contract widening remain governed decisions for #168 or a separately approved Payment Ledger change.

## Preserved provider evidence

When available from KuCoin Deposit History, the adapter preserves:

- deposit `id` as `provider_tx_ref`;
- `walletTxId` as `wallet_tx_id`;
- currency and exact normalized amount;
- provider status;
- address and memo;
- `chain` / `chainId` network identifier;
- `createdAt` and `updatedAt`;
- `preConfirms`, `confirms`, and `currentConfirms`;
- canonical hash of the provider deposit payload.

State-versioned `provider_event_id` values allow a deposit to evolve from `PENDING` to `SETTLED` without treating a legitimate provider state transition as a duplicate identity collision.

## Idempotency and failure handling

- duplicate WebSocket awareness events are suppressed by `relationEventId` when present;
- duplicate REST observations are suppressed by provider event identity/hash;
- replay cannot create a second matched settlement through this adapter;
- bounded REST retry/backoff re-signs every retry with a fresh timestamp;
- provider transport failure records `PROVIDER_UNAVAILABLE` and never fabricates `SETTLED`;
- WebSocket reconnect is bounded and retries transport-style failures only;
- parsing/configuration/contract errors fail closed rather than being hidden by reconnect loops.

## Secret boundary

The following values are environment-only and must never be committed or emitted into Telegram/admin evidence:

- `KUCOIN_API_KEY`;
- `KUCOIN_API_SECRET`;
- `KUCOIN_API_PASSPHRASE`.

Fixtures use visibly fake values. Runtime error redaction removes credential values. Live provider reads are disabled unless `KUCOIN_ALLOW_LIVE_READS=true` is explicitly configured.

## Verification status

At implementation time:

- `SOURCE VERIFIED`: `PASS` against the official provider contract listed above.
- `CI VERIFIED`: `PENDING` until exact-head repository CI completes.
- `DEPLOYED`: `PENDING` until merge and Railway automatic deployment are verified.
- `PROVIDER VERIFIED`: `UNKNOWN` — no authenticated KuCoin provider credentials/evidence were provisioned for this lane.
- `BILLING VERIFIED`: limited to deterministic mocked/no-network tests until exact-head CI.
- `MEMBERSHIP VERIFIED`: `NOT APPLICABLE` to this lane.
- `END-TO-END ACCEPTED`: `NOT APPLICABLE`; owned independently by #169.

No paid product is `SELLABLE` from this implementation alone. #168 and #169 remain separate gates.
