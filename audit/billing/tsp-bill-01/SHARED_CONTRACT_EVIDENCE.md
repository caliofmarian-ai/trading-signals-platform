# TSP-BILL-01 — Shared billing contracts and Binary plan catalog

Issue: #158  
Parent epic: #157  
Branch: `billing/tsp-bill-01-shared-contracts`  
Baseline: `main = 3e23984e2548f1049eb531cf5605d8231f856a47`

## Purpose

Establish one machine-readable billing-domain contract that every downstream billing lane consumes instead of independently redefining identifiers, enums, product IDs, plan IDs, or catalog mappings.

## Existing authority preserved

The active canonical commercial model already defines the commercial tiers:

- `FREE`
- `BASIC`
- `PRO`
- `ELITE`

Signal-distribution configuration already owns live Telegram destination IDs and signal limits. TSP-BILL-01 therefore references configuration keys such as `BASIC_CHANNEL_ID` and `BASIC_LIMIT`; it does not copy the numeric destination or limit values into the billing catalog.

The existing strategy catalog exposes `binary_canonical` / `BINARY_OPTIONS` as AVAILABLE and `forex_future` as UNAVAILABLE. Current billing scope therefore admits only `BINARY_TRADING`, mapped to `binary_canonical`.

## Machine-readable authority

`send/config/billing_contract.json` is the shared machine-readable authority introduced by this lane.

It defines:

- the current billing strategy-product scope;
- the four distinct truth layers: PAYMENT, SUBSCRIPTION, ENTITLEMENT and TELEGRAM_MEMBERSHIP;
- required cross-lane identifier names;
- shared enum values needed by downstream lanes;
- the BINARY_TRADING plan IDs;
- plan-tier mapping;
- monthly paid-plan cadence;
- exclusive channel-membership model;
- references to existing Telegram destination and signal-limit config keys;
- Owner-approved named policy states and separation invariants.

`send/billing/contracts.py` is a fail-closed consumer/validator of that JSON. It is not a second business authority.

## Plan IDs

Current Binary plan IDs are:

- `BINARY_TRADING_FREE`
- `BINARY_TRADING_BASIC`
- `BINARY_TRADING_PRO`
- `BINARY_TRADING_ELITE`

The plan IDs deliberately include the strategy-product identity so future product families cannot collide with Binary plan identifiers.

## Pricing boundary

No paid price has been approved in #157/#158.

Accordingly:

- FREE uses `pricing.status = NOT_APPLICABLE`;
- BASIC / PRO / ELITE use `pricing.status = NOT_CONFIGURED`;
- no amount or currency is present for an unconfigured price;
- the validator rejects an amount/currency inserted while status remains NOT_CONFIGURED.

This is intentional. A later governed commercial decision may configure pricing without changing strategy mathematics or signal-quality truth.

## Provider boundary

The shared contract distinguishes payment-method classes `FIAT` and `CRYPTO` but contains no provider credential, account, API key, wallet address or other secret material.

Provider-specific integration remains owned by later lanes:

- #160 — Revolut Merchant adapter/reconciliation;
- #161 — KuCoin watcher/reconciliation.

Manual payment proof/support remains a separate fallback workflow owned by #164; it is not misclassified as a payment method.

## Shared identifier contract

The contract defines the cross-lane names required by the epic:

- `subscriber_ref`
- `strategy_product_id`
- `plan_id`
- `subscription_id`
- `payment_intent_id`
- `provider_event_id`
- `provider_tx_ref`
- `wallet_tx_id` where applicable
- `case_id`
- `entitlement_id`
- `entitlement_version`
- `reconciliation_id`
- `audit_correlation_id`

Opaque identifiers do not encode Telegram IDs, e-mail addresses, plan state or provider secrets by contract. `entitlement_version` is a positive monotonic integer rather than an opaque identifier.

## Truth separation

The shared contract preserves the epic invariants that:

- PAYMENT != SUBSCRIPTION;
- SUBSCRIPTION != ENTITLEMENT;
- ENTITLEMENT != TELEGRAM MEMBERSHIP;
- PAYMENT PROOF SUBMITTED != PAYMENT VERIFIED;
- ADMIN VERIFY != DIRECT CHANNEL UPGRADE;
- INVITE SENT != MEMBER JOINED;
- REMOVAL REQUESTED != ACCESS REVOKED;
- an unmatched provider deposit must not create entitlement.

No downstream lane may collapse these domains into a single generic paid/member flag.

## Figma audit

The Figma file referenced by epic #157 was inspected read-only during this lane. The currently accessible document contains only the cover/authority page and does not expose the claimed v3.1–v3.10 billing frames as implementation-readable nodes. No pricing, provider, entitlement or checkout behavior was therefore inferred from missing Figma content.

GitHub issue policy + active canon + current repository configuration remain the basis for this contract. Figma can bind presentation later when concrete billing nodes are available.

## Regression coverage

`tests/billing/test_shared_billing_contracts.py` verifies:

- one current BINARY_TRADING product only;
- future unavailable strategy products are not admitted;
- exactly one FREE/BASIC/PRO/ELITE plan each;
- unique plan IDs;
- destination/limit fields reference existing config keys rather than copying values;
- paid-plan prices remain explicitly unconfigured;
- required shared identifiers remain present;
- truth layers and named policy states remain distinct;
- future strategy activation, invented pricing, copied channel IDs, secret-bearing fields and missing required IDs fail closed.

## Downstream consumption rule

Billing lanes #159–#169 must load/consume this shared contract and may extend their own domain records, but they must not create incompatible replacements for these shared IDs/enums/catalog identities.

This lane does not implement payment verification, ledger semantics, subscriptions, entitlement resolution, notifications, support cases, Telegram membership mutation, provider APIs, billing UI, invoicing/tax go-live, or end-to-end commercial acceptance.

## Safety

No strategy mathematics, FSM semantics, market-data provider policy, EUR/USD scope, Telegram RBAC, signal-distribution behavior or broker execution is changed by TSP-BILL-01.
