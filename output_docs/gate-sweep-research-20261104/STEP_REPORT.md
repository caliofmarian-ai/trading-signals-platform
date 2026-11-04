# 20261104-SHADOW-GATE-SWEEP-01

Purpose: implement Owner-requested private gate levels 0–20 and successive
research verification without changing the active Binary Strategy V2 gates.

## Before scan and backup

- Clean starting worktree and GitHub main:
  `d4f2326419a00cc04f6a1e0e4e783f8e8fc34e7d`.
- Backup content tree: `1f74187205a626b899523bc9f5fc45bcf90f71c8`.
- Railway project `54752c90-3929-4854-9b50-049b5c63ab98`, production
  `c8e55f1a-7518-4e7b-ae38-bad46b0a4171`, service
  `c2c41294-4eca-4092-8cdf-94ba57511c6e`.
- Settled deployment `dcad420c-a20f-4706-b531-262ad367cd88`, SUCCESS at
  2026-11-04T09:30:43Z, online 1/1; no issues/failures/pending work at pre-scan.
- New research flag absent; no existing variable or runtime file is replaced.
- Unchanged baseline scoring module SHA-256:
  `8de600a2c27a79906e7c0d31e34c02ae58e9ec3215e31a9339099c2799871776`.

## Intended delta and checks

The PR diff is the precise file/content change record. New study protocol and
proposal are under `audit/gate-sweep-research-20261104/`. Source observations
retain parameter/version provenance at registration; no past observation is
backfilled. The new worker consumer writes its own atomic research ledger and
derived cache. The compact deploy marker is
`TSP_GATE_SWEEP_RESEARCH_EVIDENCE`, component `shadow_gate_sweep_research`.

Existing research outcomes, point-in-time features, canonical market truth,
execution calibration, provider selection, production thresholds, FSM acceptance
and distribution/broker guards must retain their previous behavior.

Offline validation includes cutoff boundaries, stricter filters with worse
results, UNKNOWN/DRAW separation, conservative overlap handling, prospective
windows, insufficient/low-quality evidence, parameter/formula drift, restart,
complete 21-level traversal ending in review, corrupt ledgers/cache privacy,
worker retry isolation, and a real canonical collector-to-report regression.
Test observations are synthetic offline fixtures and never live study results.

Local result: full repository suite **1,946 passed in 65.75s**; the unchanged
source collector and new experiment had 80 focused tests passing before the
final provenance/completion cases were included in the full run. There are 43
new experiment regressions relative to the 1,903-test pre-change baseline.
`git diff --check` passed. Required remote CI and live acceptance remain separate.

## Restart / after scan acceptance record

The linked PR's validation and post-deploy sections record the final local test
count, required CI run/job/head, merge SHA, actual settled Railway deployment,
replica health, timestamped activation/source/calibration markers and bounded
error check. That durable post-deploy proof must be populated before operational
acceptance is claimed. This pre-deployment document does not claim future results.

Rollback reference and triggers are in PROPOSAL.md. The source data and all
completed research stages are retained if the new flag is disabled. Neither a
green test suite nor an enabled/empty initial study proves efficacy, delivery,
broker compatibility, or profitability.
