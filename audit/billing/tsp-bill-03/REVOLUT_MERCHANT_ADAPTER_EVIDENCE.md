# TSP-BILL-03 — Revolut Merchant adapter evidence

Issue: #160
PR: #183
Baseline main: `af26daa56943042b5c1c93993a5018b51e13d808`

## Scope

This evidence covers the repository implementation of the Revolut Merchant FIAT adapter. It does not claim production readiness, provider-account eligibility, live money movement, or webhook reachability.

## Official provider contract checked

The implementation was checked against Revolut Developer documentation for Merchant API versioning/authentication, Sandbox vs Production endpoints, saved payment methods / merchant-initiated payments, and webhook signature verification.

Relevant provider contracts used by this implementation:

- Sandbox Merchant base URL: `https://sandbox-merchant.revolut.com`.
- Production Merchant base URL: `https://merchant.revolut.com`.
- Server requests use `Authorization: Bearer <secret>` and an explicit `Revolut-Api-Version` header.
- Version `2026-04-20` is a documented supported Merchant API version.
- Saved payment methods may be charged through the Pay for an order `/payments` flow; merchant-initiated use requires the payment method to have been saved for merchant use/consent.
- Merchant webhooks use `Revolut-Request-Timestamp` and `Revolut-Signature`, with HMAC-SHA256 over `v1.<timestamp>.<raw-body>` and a five-minute timestamp tolerance.
- A webhook notification is treated only as a trigger. The adapter retrieves provider order state before writing provider evidence into the governed Payment Ledger.

## Repository implementation

`send/billing/revolut_merchant.py` implements:

- fail-closed Sandbox default and explicit production opt-in;
- provider order creation bound to an existing governed `payment_intent_id`;
- crash recovery by merchant reference before creating another provider order;
- append-only adapter evidence under `BINARYBOT_BASE_DIR/billing/revolut_merchant_events.jsonl`;
- bounded retry/backoff for retryable provider/transport failures;
- webhook HMAC verification, multiple signatures, timestamp tolerance and raw-body hashing;
- provider order reconciliation into `send/billing/payment_ledger.py` rather than direct subscription/entitlement mutation;
- exact provider order/payment references and canonical provider-response hash preservation;
- saved-payment-method recurring initiation with customer/method/consent identifiers hashed in adapter evidence;
- polling recovery for bound non-final orders;
- an explicit truthful runtime boundary: signature verifier and handler are implemented, but inbound HTTP webhook transport is `NOT_CONFIGURED` in the current worker-only Railway deployment.

`.env.example` documents variable names only. No real Revolut credential or webhook secret is committed.

## Safety invariants verified by tests

- production calls require explicit opt-in;
- transport errors redact configured secrets;
- invalid/stale webhook signatures fail closed;
- duplicate webhooks cannot create duplicate settlement;
- webhook `ORDER_COMPLETED` does not settle a payment when retrieved provider order is still pending;
- provider outage adds no fabricated payment truth;
- amount/currency contradiction does not create a matched settlement;
- failed/cancelled orders are not settled;
- recurring initiation requires explicit consent evidence and does not persist raw customer/method/consent identifiers;
- crash recovery reuses exactly one provider order and fails closed if multiple orders exist for one reference;
- final payment intents are skipped by recovery polling.

## Verification status

- SOURCE VERIFIED: PASS
- OFFICIAL PROVIDER CONTRACT REVIEW: PASS
- CI VERIFIED on implementation head `20048708f7738a5acf473cd79fd166652aa70c18`: PASS
- `Required Repository CI` run `35147721721`: SUCCESS
- full repository suite on that head: `1466 passed`
- PROVIDER SANDBOX VERIFIED: UNKNOWN / NOT EXECUTED — no authenticated Revolut Sandbox credentials were supplied to this session
- WEBHOOK INGRESS VERIFIED: NOT_CONFIGURED — current Railway service is intentionally a worker-style process without governed public HTTP ingress
- PRODUCTION VERIFIED: NOT APPLICABLE / NOT ENABLED

## Merge boundary

Merging this adapter is safe without provider credentials because it does not wire automatic charges or expose a webhook listener. Provider/Sandbox acceptance and production go-live remain separate evidence gates. No pricing, subscription policy, entitlement, Telegram membership, strategy/FSM, market-provider policy, or broker execution authority is changed by this lane.
