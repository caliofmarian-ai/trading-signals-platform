# TSP-BILL-08 — Telegram Membership Reconciliation Evidence

Issue: #165
PR: #182
Baseline: `main = 4a214e43f545283e87a430162883b6dbb56b8920`

## Scope

This lane implements entitlement-driven Telegram membership reconciliation for the EXCLUSIVE BINARY_TRADING tier topology while preserving separation between entitlement truth and Telegram membership truth.

Implemented behavior:

- append-only reconciliation evidence under `BINARYBOT_BASE_DIR/billing/membership_reconciliation_events.jsonl`;
- states `IN_SYNC`, `INVITE_REQUIRED`, `REMOVE_REQUIRED`, `ACCESS_LEAK_RISK`, `ACTION_FAILED`, `UNKNOWN`;
- target tier is derived only from `subscription_registry.resolve_entitlement()`;
- Telegram channel IDs are consumed from the existing distribution configuration; no tier/channel IDs are hardcoded in runtime code;
- explicit private subscriber -> Telegram identity binding is consumed from notification delivery authority; ambiguous reverse identity fails closed;
- all EXCLUSIVE tier channels are observed with `getChatMember` before mutation;
- Telegram channel/supergroup IDs correctly accept signed non-zero IDs, including canonical `-100...` identifiers, while Telegram user/private-chat identities remain strictly positive;
- stale memberships are removed before a new target invite is created;
- removal is verified with `getChatMember`; paid-channel removal failure/unverifiable state becomes `ACCESS_LEAK_RISK` and emits CRITICAL observability evidence;
- failure to remove only a stale FREE-channel membership is `ACTION_FAILED`, not a paid access-leak incident;
- a previously kicked user is unbanned only when that channel is the current entitlement target;
- invite links are bounded (`member_limit=1`, default 15-minute lifetime, hard maximum one hour);
- raw invite links are never persisted in reconciliation evidence; only SHA-256 evidence is stored;
- invite delivery failure becomes `ACTION_FAILED` and never `IN_SYNC`;
- existing active invite evidence suppresses duplicate invites until expiry; expired evidence permits rotation;
- invite delivery is never treated as membership proof; a later `getChatMember` observation is required for `IN_SYNC`;
- `restricted` Telegram members are treated as members only when `is_member=true`;
- `SUSPENDED` / `HOLD` entitlements have no target channel; stale access is removed and no new invite is generated;
- `ChatMemberUpdated` evidence can be persisted idempotently but does not replace entitlement truth;
- global dry-run reconciliation can enumerate known subscribers with `apply_actions=false`;
- `BILLING_MEMBERSHIP_RECONCILER_ENABLED` is disabled by default. This PR does not wire an automatic production mutation cycle.

## Security / fail-closed findings

### Negative Telegram channel IDs

The first CI run on `fd5e7498e290ca3706cebe2327020d478ea28728` failed exactly because the initial validator incorrectly required Telegram channel IDs to be positive. Real channels/supergroups commonly use signed IDs such as `-100...`.

Result: **1434 passed / 9 failed**. All nine failures had the same root cause. The tests were not weakened.

The implementation was corrected to use distinct identifier contracts:

- Telegram user/private chat IDs: positive integer;
- Telegram channel/supergroup IDs: non-zero signed integer.

### Additional hardening

After the negative-ID fix passed, additional regressions were added for:

- duplicate EXCLUSIVE channel mappings -> `UNKNOWN` before API mutation;
- `restricted + is_member=true` normalization;
- FREE-channel removal failure -> `ACTION_FAILED`, not `ACCESS_LEAK_RISK`;
- invite delivery failure -> `ACTION_FAILED` with no raw invite capability persisted;
- Telegram transport exceptions redact bot tokens;
- global dry-run does not enable mutations.

## CI evidence

Exact-head run on `9ee576e169a3fb7f455a8b0f5944fcd0efd3910a` after correcting Telegram identifier semantics:

- `Required Repository CI`: SUCCESS — run `35146253272`;
- full repository regression suite: **1443 passed**.

Exact-head pre-evidence run on `35c296630489a2f1f32f1baadb0609e9a90fb203` after hardening regressions:

- `Required Repository CI`: SUCCESS — run `35146518003`;
- repository governance: PASS;
- provider selector regression: PASS;
- Telegram Admin regression: PASS (`72 passed`);
- critical canonical contracts: PASS (`31 passed`);
- full repository regression suite: **1449 passed**.

A fresh exact-head CI run is required after this evidence commit before merge. Earlier green runs are not transferred to the new head.

## Explicit non-scope / production safety

This lane does not:

- enable an automatic membership mutation scheduler;
- claim live membership verification without production Bot API evidence;
- alter pricing/payment/subscription truth;
- alter Telegram RBAC semantics;
- change strategy/FSM/market-data provider policy;
- enable broker execution.

Production membership actions remain opt-in and must not be activated merely by merging this source implementation.
