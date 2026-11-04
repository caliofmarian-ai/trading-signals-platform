# SHADOW_GATE_SWEEP_V1 — Owner-requested levels 0–20

Status: approved research implementation scope, not a new active strategy policy.
Owner: Marian Caliof. Request: 2026-11-04, test gates successively from 0 to 20
and study each before considering a later selection. Related: #208, #217.

## Meaning of the scale

This is one isolated experimental question: does an additional deterministic TPS
filter improve the unchanged strategy's accepted-OPEN cohort? Level `k` admits
an opportunity when its decision-time TPS is at least `5*k`, for k = 0…20.
Thus 0 adds no filter and 20 requires TPS=100. These are research cutoffs, not
probabilities, predicted returns, or new production PRE/CONFIRM/OPEN thresholds.
The hypothesis that higher selectivity helps may be rejected by the evidence.
Level 20 can have zero observations or worse results; it cannot promise a win.

Authority reviewed: active Master Index v2, ALGO v3 §§9–17/25–26, Parameter
Control v3 §§5/8/14/20, Research v3 §§5/7/9/13/15/17, Time v3 §§20–25 and Signal
Engine v3 §§2/6/19/27. No canonical mathematics, hard gate, FSM rule, parameter
file, provider, calibration, distribution entitlement, or broker setting changes.

## Cohort and prospective boundary

Only existing SHADOW_MODEL_TIME_RESEARCH_V1 records from exact FSM-accepted
OPEN_NOW may contribute. All original data/structure/time/physics requirements
remain prerequisites. REJECT, PRE, CONFIRM and unaccepted OPEN requests do not
become observations through this experiment. Raw quotes and identities stay in
the private source records; the new report contains aggregates only.

At first enabled worker observation, an atomic experiment state fixes its UTC
start, protocol and targets. Earlier records are excluded, including records
whose outcomes finish later. New source records retain the SHA-256 of the exact
validated strategy parameter bundle used by that evaluation, before observing
outcomes. The first eligible record fixes this experiment's parameter baseline.
Missing version provenance/TPS is counted as excluded, never imputed as zero.
A different parameter hash or Trade Physics formula/schema pauses progression.
Source corruption makes the report unavailable; it does not fabricate zero.

## Paired discovery and successive verification

All 21 cutoffs are described against the same prospective cohort, preserving
classical score and the original strategy as the control. This paired table
supports comparison without confusing a different market hour with a filter
effect. It is exploratory, not an automatic winner selection.

One verification level is active at a time, starting at 0. Later levels enroll
only opportunities registered after their activation. A level completes after
at least 100 decisive, conservatively nonoverlapping observations across at
least 3 distinct UTC registration dates, with no selected pending record and
UNKNOWN at most 5% of selected final records. These are frozen operational
collection targets, not proof of adequate statistical power or profitability.
Progress depends on evidence quantity/quality, never on an attractive win rate.
No observations means waiting; a high cutoff may never complete.

Nonoverlap thinning is outcome-blind: sort by registration time/record identity,
then reserve registration through registration + entry deadline + Model Time
horizon + expiry lateness. Retain the first opportunity and exclude overlapping
ones regardless of label, including UNKNOWN/pending. Discovery thinning occurs
before applying any cutoff, so every cutoff shares the same reference cohort.
Verification thinning occurs within its prespecified level/window. Nonoverlap
does not prove statistical independence. Completed windows and their aggregate
evidence digests are persisted; the next window starts after any remaining
observation envelope to avoid crossing the preceding window. Restart does not
reset a level, erase results, or retrospectively assign old opportunities to it.

## Reporting and eventual selection

Each cutoff reports WIN/LOSS/DRAW/UNKNOWN, decisive=WIN+LOSS, pending, observation
interval, missingness and hypothetical directional rate. DRAW/UNKNOWN stay out
of the decisive denominator. A nominal 95% Wilson interval is an IID reference
only: dependence, 21 comparisons and repeated monitoring prevent interpreting
it as a simultaneous or sequential coverage guarantee. No ranking is promoted
merely by its largest observed rate. References: NIST confidence intervals,
https://www.itl.nist.gov/div898/handbook/prc/section2/prc241.htm ; Bailey et al.,
The Probability of Backtest Overfitting,
https://www.davidhbailey.com/dhbpapers/backtest-prob.pdf .

Finishing all levels yields REVIEW_REQUIRED, never an automatically selected
production gate. A later candidate needs a frozen hypothesis and further
chronological holdout/replay, dependence/regime/multiple-comparison review,
evidence-backed expiry calibration, and actual permitted broker-demo evidence.
Actual payout, terminal entry/settlement quotes and UTC times are required for
broker economics. No payout, break-even rate, P&L or acceptable-efficiency
target is invented here. Finnhub EUR/USD is not Pocket Option EUR/USD OTC.

## Activation, isolation and rollback

Runs only with SHADOW_GATE_SWEEP_RESEARCH_ENABLED=true and the original shadow
collector enabled (Shadow Mode on; broker execution off). The new flag only
enables derived private research reporting and the successive research ledger.
It has no signal/gating/calibration setter, router, publisher or order access.
The worker uses the already ingested source, without additional provider calls.
Atomic bounded state/report files are separate from the source evidence and
shared runtime status. Failure is isolated and retried with sanitized warnings.
The observation timestamp is not a heartbeat. Disabling the flag stops updates;
existing immutable source observations and completed research stages remain.

Acceptance: offline mapping/boundary, outcome/denominator, prospective window,
outcome-blind overlap, sequential progression/restart, provenance drift,
corruption/storage/privacy and worker-isolation regressions; complete required
CI; deployed SHA; explicit live enabled/level/status marker. Software success
alone establishes neither strategy efficacy nor manual-signal delivery.
