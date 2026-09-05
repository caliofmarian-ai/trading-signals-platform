# R-019 open findings

## Operational acceptance retained for the Owner

- No unresolved implementation-review findings or CodeQL alerts remain in the validated change (1189 local/agent full-suite passes; CodeQL 0 alerts).
- The daily UTC clock is intentionally not supplied by this remediation. The Owner must choose the clock and explicitly enable the auditor. Until then, no scheduled report is promised.
- A persistent Railway volume with usable read/write permissions and POSIX locking is required for cross-redeploy idempotency. Local temporary-volume/restart/process tests cannot prove the deployed volume configuration.
- After merge, verify runtime auditor readiness, an eligible report, JSON/Markdown consumption, success state retained across redeploy, and sanitized failure evidence. Issue #140 remains open until that evidence is reconciled.
- GitHub Actions must run on the exact final PR head. Approval-required or absent workflow jobs are not a successful CI result.

## Deliberately outside R-019

- The auditor currently reads all available source history. Its date identifies a generation/report period, not a filtered single-day analytical window. No historical backfill, collector, temporal pattern detection or trading-window score/gate is added.
- Source reading is not a transactionally frozen snapshot across all five live append-only files. No new interpretation of incomplete live evidence or source rotation is introduced.
- The general-purpose storage lock's age/deployment reclamation policy is unchanged. The auditor uses its own non-stealable kernel lock because changing every existing lock consumer would broaden this remediation.
- Cache is currently unused by auditor computation. R-019 provides its persistent directory contract, not invented cached metrics or disposable completion truth.
- R-017 live Telegram/Railway acceptance (#131/#23), temporal canon (#137), and R-020 through R-026 remain separate. No issue is automatically closed and no PR is merged by this task.
