# R-018 Baseline

- Repository: `caliofmarian-ai/trading-signals-platform`
- Existing PR: `#136`
- Actual implementation branch: `copilot/r-018-strategy-auditor-v3`
- PR head at hardening start: `3223c1f6aada530550f9b710da43984fed4be591`
- Base main at PR creation: `9427fad7633b279b30ab97a49656f87e8b637e59`
- Governing remediation plan file: `audit/repository-wide-audit-2026-09-01/REMEDIATION_MASTER_PLAN.md`

## Governance state at hardening start

- R-017 remains `IN PROGRESS` because live Railway/Telegram acceptance is still outstanding.
- R-018 remains open repository work on PR `#136`; it is not closed.
- Issue `#97` remains open and still shows the older global execution pointer text.
- The prior R-018 implementation was directionally correct but required hardening for canonical non-decision classification, reject-distribution backward compatibility, real branch metadata, and issue/governance truthfulness.

## Verified defects on PR #136 head `3223c1f6aada530550f9b710da43984fed4be591`

1. schema-recognized non-decision events could still be counted as `unsupported_event_types` because the supporting-event allowlist was incomplete;
2. reject distribution and symbol-health semantics counted all reject blockers instead of preserving one primary reason per rejected decision for backward-compatible analytics;
3. R-018 artifacts and remediation metadata claimed a suggested branch name instead of the actual Copilot branch;
4. no dedicated R-018 issue existed, and issue creation is not available through the tools/auth present in this environment.
