# TSP-BILL-07 — Support Cases + Manual Payment Proof Evidence

Issue: #164
PR: #181
Baseline: `main = ea955a508298fc013ecefd7c6246f532e26464e8`

## Scope

This lane implements the audited fallback path used when automated payment detection/reconciliation cannot prove a client's payment or when billing assistance is required.

Implemented authority:

- append-only support-case lifecycle: `OPEN`, `WAITING_FOR_CLIENT`, `UNDER_REVIEW`, `HOLD_ESCALATION`, `VERIFIED`, `REJECTED`, `RESOLVED`;
- immutable `case_id` timeline with contiguous global and per-case sequencing;
- client and admin messages correlated to `case_id`;
- restricted Telegram payment-proof metadata with SHA-256 evidence and duplicate suppression;
- proof download bounded to the Telegram Bot API `getFile` 20 MB boundary;
- proof bytes are hashed in memory and are not persisted by the support runtime adapter;
- explicit private Telegram subscriber binding; `subscriber_ref` is never inferred from a Telegram ID;
- exactly one active support context is required before private messages or proof attachments are consumed;
- OWNER / PRIMARY_ADMIN review gate using the existing fail-closed RBAC authority;
- `REQUEST_MORE_INFO`, `VERIFY`, `REJECT`, `ESCALATE`, `RESOLVE` transitions;
- provider/payment contradictions force `HOLD_ESCALATION`;
- manual verification evidence is written into the existing #159 Payment Ledger and never directly mutates subscription, entitlement, Telegram membership, signal distribution or broker execution;
- already-settled payments receive manual-review audit evidence without a duplicate settlement;
- reopen creates a new case while preserving the prior case history;
- client-safe views redact restricted Telegram file identifiers and reviewer-only evidence;
- Telegram runtime routing for support text and `document` / `photo` payment proof attachments;
- proof-shaped ingestion failures are contained and return a safe client message instead of falling through into unrelated bot navigation.

## Concurrency / crash safety

`VERIFY` uses a stable payment-ledger -> support-case lock order, revalidates the case and proof inside the critical section and uses idempotent payment evidence. If payment evidence was appended but the support review was interrupted before its case event, replay recovers the case review without producing a second matched settlement.

Unlinked proof can be recorded first and later associated with a payment intent through an audited correlation event. This supports the `PAYMENT_NOT_DETECTED` path without fabricating provider truth.

## Invariants

- `PAYMENT PROOF SUBMITTED != PAYMENT VERIFIED`
- `ADMIN VERIFY != DIRECT ENTITLEMENT / CHANNEL MUTATION`
- `CONTRADICTORY PROVIDER EVIDENCE => HOLD_ESCALATION`
- `FILE RECEIVED != SAFE PUBLIC DISCLOSURE`
- support-case state is not payment truth;
- payment truth is not entitlement truth;
- entitlement truth is not Telegram membership truth.

## CI evidence

An intermediate exact-head run on `94ec3bd5dc2aba8a4f413a66d06541eb3e1f495a` correctly failed only because one test still expected the previous reason-code string. Result: `1426 passed, 1 failed`. The runtime behavior remained fail-closed.

The test was aligned to the consolidated fail-closed reason `NO_UNIQUE_SUPPORT_CONTEXT`, and Telegram proof routing regressions were added.

Exact-head pre-evidence verification on `5d6e5736a1bcb7f1912c0e884a1d0881d32f352f`:

- `Required Repository CI`: `SUCCESS`
- workflow run: `35144785916`
- repository governance: PASS
- provider selector regression: PASS
- Telegram Admin regression: PASS (`72 passed`)
- critical canonical contracts: PASS (`31 passed`)
- full repository regression suite: **1430 passed**

A fresh exact-head run is required after this evidence commit before merge. The earlier green run is not transferred to the new head.

## Explicit non-scope

This lane does not implement or enable:

- Revolut or KuCoin credentials/provider calls;
- pricing policy;
- subscription activation directly from support state;
- direct entitlement mutation;
- Telegram paid-channel membership reconciliation;
- strategy/FSM mathematics;
- market-provider policy changes;
- broker execution.
