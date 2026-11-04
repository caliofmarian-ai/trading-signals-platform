# Owner-requested successive gate research

CHANGE_ID: 20261104-SHADOW-GATE-SWEEP-01  
TYPE: MINOR, isolated observational research and aggregate reporting  
OWNER / REQUESTED_BY: Marian Caliof, direct request 2026-11-04  
APPROVAL_STATUS: implementation/activation of research requested by Owner;
production gate adoption and efficacy remain unapproved/unproven  
PROTOCOL: `SHADOW_GATE_SWEEP_V1`, defined before implementation in PROTOCOL.md

## Rationale and intended behavior

The Owner requested levels 0–20, successive observation, and later retention of
an effective level. The existing prospective accepted-OPEN collector provides
an isolated source for testing an additional TPS selectivity hypothesis. The
level is a research label: `minimum TPS = 5*level`. The proposed assumption that
20 guarantees maximum efficiency is explicitly rejected as unestablished.

The paired table retains all cutoffs on the same cohort; an independent
successive ledger starts at 0 and advances on frozen collection/quality targets.
No level is supplied to production strategy/FSM. Completion requests review;
there is no automatic selection or production promotion.

## Authority and exact targets

Active Master Index v2; ALGO v3; Time v3; Signal Engine v3; Parameter Control v3;
Research v3; Governance/Deployment v2.0.1. Active specs remain unchanged because
their strategy, execution and authority contracts remain unchanged. This is the
research-only future-policy-threshold experiment allowed by Research §15.

Code: new `send/intelligence/shadow_gate_sweep_research.py`; existing source
collector gains version/validated-parameter hash provenance and a locked,
bounded read API. Signal Engine supplies the hash of the parameters it actually
used. Telemetry worker runs/retries the independent study and prints a compact
aggregate marker. Runtime status overlays a bounded validated cache.

Research targets: 100 nonoverlapping decisive observations, at least 3 UTC
registration dates, no selected pending, UNKNOWN at most 5% of selected finals.
These control collection/progression, not production thresholds or significance.

## Risk, scope and isolation

Potential risks: incorrect denominators/cutoff boundaries, outcome-based sample
selection, comparing market regimes as if randomized, resetting stages after
restart, mixing parameter/model versions, stale cached status, or source/storage
failure. Regressions cover these cases. Full report is bounded at 128 KiB; the
deploy marker contains compact aggregates instead of raw source records.

Only research files under `analytics/shadow_gate_sweep_research/` are updated.
Existing source records receive provenance only at creation; old records,
market telemetry and completed outcomes are not rewritten. No additional quote
request, learned-model authority, order, signal publication, broker/provider,
route, production parameter or license/role change is included.

## Backup, deployment, rollback and monitoring

Before snapshot/backup: immutable commit
`d4f2326419a00cc04f6a1e0e4e783f8e8fc34e7d`, tree
`1f74187205a626b899523bc9f5fc45bcf90f71c8`; touched pre-existing files are
recoverable via `git show <commit>:<path>`. Existing runtime config/state is not
migrated. New flag absent at pre-scan. Previous successful Railway deployment
`dcad420c-a20f-4706-b531-262ad367cd88` remains the code rollback reference.

Deployment: required CI must pass for the PR's actual head; set only
`SHADOW_GATE_SWEEP_RESEARCH_ENABLED=true` with deployment skipped, then merge the
reviewed code for the normal main deploy. This avoids an extra restart solely
to set a passive research flag. Confirm live settled deployment SHA separately
from queued/building versions, replica health, explicit new enabled/level marker,
original research and calibration markers, and bounded error/startup evidence.

Rollback: set this single research flag false; preserve research/source files.
If code health is affected, revert the bounded PR through normal verified CI
and main deployment, or use the recorded prior deployment under the existing
operational rollback procedure. Do not reset data, remove source evidence, or
change strategy parameters to make the study appear successful.

Monitoring: initial restart acceptance plus the existing hourly read-only
strategy monitoring. Continued collection can legitimately stay at level 0.
Failure triggers: repeated research storage/schema warnings, baseline drift,
missing live activation evidence, crashes, source corruption or unexpected
production-gate/publication change. Efficacy acceptance is a separate future
decision requiring chronological validation and actual permitted broker demo.

Evidence bundle: `output_docs/gate-sweep-research-20261104/STEP_REPORT.md`, this
protocol/proposal, the PR diff and the PR's post-deploy proof section. Private
runtime quotes, account identifiers and raw audits must not be committed.
