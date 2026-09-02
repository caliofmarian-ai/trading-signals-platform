# R-017 — Telegram Multi-Role Final Acceptance

Status: IN PROGRESS — AUTOMATED ACCEPTANCE PENDING
Issue: #131
Parent Telegram remediation: #23
Parent repository-wide remediation: #97
Base main commit: `92f272cb3ce2450c2e0e93abc92d0e26c4e348f9`

## Audit result

The existing Telegram application already has substantial automated and live evidence:

- `/start` produces a navigable application page for every canonical role;
- active UI sessions are scoped by chat, user, and thread and persist through the governed state layer;
- Home, Back, Refresh, status/help navigation, stale callback recovery, duplicate taps, and role reload behavior have automated coverage;
- Owner/Admin production acceptance is recorded in Issue #23;
- callback recovery for stale, unknown, retired, and unauthorized actions is already delivered by Issue #42 / PR #43;
- R-016 now provides strict, fail-closed role/permission authority.

The remaining repository gap is a complete non-Owner journey matrix through the real Telegram authorization path. Existing tests cover individual pieces, but do not prove the full interaction of Admin-topic context, strict permissions, panel visibility, forged callback rejection, and affiliate scope for every non-Owner role.

## R-017 automated acceptance matrix

The R-017 focused suite covers:

- PRIMARY_ADMIN;
- STRATEGY_ADMIN;
- RESEARCH_ADMIN;
- ANALYST;
- MODERATOR;
- AFFILIATE_ADMIN;
- USER.

It proves:

- non-Owner private-DM Admin access remains denied;
- configured Admin-topic context is necessary but is not sufficient by itself — role permission is still required;
- wrong Admin thread fails closed;
- each non-Owner admin role receives exactly its governed canonical panel set;
- Primary Admin can inspect roles but cannot use Owner-only role mutation;
- Strategy Admin keeps governed strategy mutation authority without unrelated domains;
- Research Admin and Analyst remain read-oriented;
- Moderator remains limited to support/channel/system-health authority;
- Affiliate Admin is restricted to own affiliate/referral scope and cannot gain global affiliate authority;
- USER remains public-only even if a message originates inside the Admin topic;
- private forged Admin callbacks are denied;
- authorized Admin-topic callbacks work only for role-allowed panels;
- forged callbacks to unauthorized panels must fail closed.

If the focused suite exposes a direct-callback authorization bypass, R-017 will repair that runtime defect rather than weakening the acceptance test.

## Live acceptance gate

Automated evidence does not replace live Telegram/Railway proof. R-017 cannot be marked CLOSED until the final multi-role acceptance evidence is recorded. A role that is not configured on a real test account must not be recorded as PASS.

The live checklist will verify, for each actually configured test role:

1. `/start` role-scoped entry;
2. private-DM Admin denial for non-Owner roles;
3. Admin-topic entry where authorized;
4. visible panel set;
5. one allowed action;
6. one denied action outside role scope;
7. Back/Home/Refresh continuity;
8. affiliate own-vs-other scope where an Affiliate Admin test identity exists;
9. no broker execution activation and no strategy/provider mutation outside the explicitly tested control.

## Safety boundary

R-017 does not change trading mathematics, score thresholds, SR/Corridor, Trade Physics, Time Model, market-data provider selection, event truth, signal distribution semantics, subscription entitlements, or broker execution. Any runtime change is limited to Telegram authorization if the acceptance suite proves a real fail-open path.
