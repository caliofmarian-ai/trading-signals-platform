# R-016 — Role / Permission Fail-Closed Reconciliation

Status: IMPLEMENTED — FINAL VALIDATION PENDING
Issue: #128
Parent: #97
PR: #129
Base main commit: `401ff45399cddeb45b613b0a6bbb23d1e740a356`

## Defect

The live permission loader treated missing, empty, malformed, and non-object permission state as an empty file matrix, while authorization always unioned that result with the hardcoded role matrix. This silently restored baseline non-Owner privileges when critical operator permission authority was unsafe. Valid file entries could also extend the hardcoded matrix with permissions not present in the governed role ceiling.

A second defect allowed `affiliate.view` to be granted literally in `admin_permissions.json`. Generic permission membership was checked before the scoped affiliate authorization branch, so a direct grant could bypass `target_affiliate_code` isolation.

## R-016 authority decision

- `PERMISSION_MATRIX` is the governed maximum permission ceiling for each role.
- `admin_permissions.json` is the explicit effective grant authority for non-Owner roles.
- Configuration may restrict grants but may never widen the governed ceiling.
- Missing, empty, malformed, non-object, unknown-role, unknown-permission, duplicate-role, or ceiling-violating permission state is unsafe.
- Unsafe permission state fails closed for non-Owner authorization.
- Owner recovery remains an explicit Owner bypass and is not implemented as permissive config fallback.
- `affiliate.view` is synthetic and cannot be granted directly; it is resolved only through `affiliate.view.any` or `affiliate.view.own` plus affiliate target scope.
- Startup preflight calls the same strict permission loader, so deployment validation and runtime authorization share the same permission-state semantics.

## Regression proof

R-016 adds and updates regression coverage proving:

- malformed permission JSON is explicit and non-Owner access is denied;
- Owner recovery remains available while diagnostics report blocked permission state;
- operator config cannot grant `roles.write` to Primary Admin or invent a custom permission outside the ceiling;
- omission from valid effective config restricts a baseline permission rather than falling back to it;
- direct synthetic `affiliate.view` grants are rejected;
- Affiliate Admin may view own affiliate code/referral scope but not another affiliate;
- Primary Admin `affiliate.view.any` remains bounded by the governed ceiling;
- Analyst/User mutation and unauthorized paths remain denied;
- startup preflight rejects the same ceiling violation before workers start;
- legacy tests that asserted permissive GAP-012 fallback are migrated to the fail-closed contract.

## Safety boundary

R-016 does not change strategy mathematics, score thresholds, SR/Corridor, Trade Physics, Time Model, market provider behavior, signal distribution semantics, market data, broker execution, or canonical document activation status.

## Validation history

Initial PR validation run `33670036317` proved provider selector **5 passed** and Telegram admin regression **72 passed**, then intentionally exposed five legacy tests that still required the superseded permissive fallback/extension behavior. The implementation was not relaxed. Those legacy expectations were migrated to the R-016 fail-closed contract.

The final exact-head GitHub Actions run, merge candidate, and full-suite count are recorded in PR #129 after successful validation.
