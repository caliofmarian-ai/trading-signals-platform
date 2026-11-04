# SHADOW_GATE_TIMEBOX_V1 — Owner's same-day, two-hour test

CHANGE_ID: 20261104-GATE-TIMEBOX-01
Owner: Marian Caliof; direct request 2026-11-04: test today, at most two hours,
and explain every missing observation rather than conceal an UNKNOWN label.

The initial 2026-11-04T14:06:26Z--16:06:26Z attempt missed activation because
publication was rejected; it has no prospective two-hour test results. The
prepared implementation is retained in local commit dc07d473f069512e39f0cd985bfa01edf055d8d9.
The Owner explicitly resumed work at 16:05, including the already authorized
implementation and Telegram diagnosis. This is a distinct attempt, not an
extension or backfill of the missed one.

The resumed request window starts 2026-11-04T16:05:00Z and ends at
2026-11-04T18:05:00Z. Setup and deployment consume this same budget; the actual
prospective observation start is the first enabled worker update. Deployment,
restart, lack of opportunities and missing data cannot extend the deadline.
If activation misses the deadline, the report says EXPIRED_BEFORE_ACTIVATION.
RUN_ID is 20261104T160500Z; its caches live in a separate subdirectory, preserving
any prior attempt's evidence. Both UTC times are also Europe/Dublin local time
on this date. No later restart or continuation may silently move this deadline.

## Authority and scope

Active Master Index v2, ALGO v3 sections 13–17/25–26, Time Model v3 sections
20–29, Signal Engine v3 sections 2/6/27–29 and Research v3 apply. This replaces
the V1 three-date/100-decisive progression for this requested preliminary test.
The old ledger and all source records are preserved. The new research flag
suppresses updates to the old progression; rollback resumes it without migration.
No strategy thresholds, formulas, FSM acceptance, calibration, distribution,
provider, broker, license or financial action is changed.

## Cohort, comparisons and time limit

Only validated SHADOW_MODEL_TIME_RESEARCH_V1 records from actual FSM-accepted
OPEN_NOW, registered after actual activation and before the fixed deadline, are
eligible. PRE, CONFIRM, REJECT and unaccepted OPEN requests stay diagnostics.
The first eligible record fixes parameter/model provenance. Drift pauses use
of further evidence and is explicit. Missing TPS/provenance is an exclusion.

All 21 TPS cutoffs (5*k, k=0..20) are compared on the same prospective window.
Paired all-record and common, outcome-blind nonoverlap metrics are separate.
Additionally the remaining observation time is split into 21 chronological
registration slots, one per research level. Elapsed slots count time coverage,
not validated/completed levels. An entry in an earlier slot can finish later
in the same two-hour window. Sequential comparisons are confounded by market
time and are exploratory. No high rate selects a production cutoff.

The final report includes only outcomes finalized by the deadline. Anything
still awaiting entry/expiry at the cutoff stays pending in that report; later
source observations cannot backfill it. A frozen final report survives restart.
The underlying collector may continue its separately authorized observation,
but that cannot change the two-hour test's final result.

## Transparent evidence quality

WIN/LOSS/DRAW/UNKNOWN are retained; decisive=WIN+LOSS and rate=100*WIN/decisive.
Draws, unknowns and pending never enter that denominator. Every unknown has an
allowlisted cause: missing entry quote, missing expiry quote, provider change
or a checkpoint missed on restart. Counts plus bounded timestamp-only gap
details are exposed; raw prices and account/signal identities remain private.
An unrecognized source reason is a data error, never a fabricated result.
Pending entry and pending expiry counts are explicit. Missing data prevents
evidence completeness; zero observations cannot be described as clean success.

Aggregate decision/FSM/blocker counts and the first/last evaluation timestamps
explain whether the strategy is actually evaluating or merely has cached status.
The worker also validates an already-ingested live sample and reports its age,
without requesting extra provider data. Repeated evaluations of one candle are
not independent opportunities. Summaries are refreshed at most once a minute
and at the deadline; these timestamps are not a feed heartbeat.

## Interpretation, validation and rollback

This is preliminary HYPOTHETICAL_RESEARCH with UNCALIBRATED_MODEL_TIME. Two
hours establish neither profit nor independent statistical power. Paired levels
overlap; opportunities can correlate; nominal Wilson intervals are IID reference
only and do not correct repeated monitoring or multiple comparisons. Finnhub
EUR/USD is not Pocket Option EUR/USD OTC. Broker quotes, actual UTC entry/expiry,
payout, permitted access, empirical execution calibration and delivery remain
separate requirements. No claim of certain wins or real-money readiness follows.

Tests cover fixed deadline, no extension/restart, late-finalization censoring,
empty cohorts, every gap cause, denominators, strict cutoffs, provenance drift,
private/malformed caches, source corruption and worker isolation. Run the full
repository suite and required CI; verify the actual deployed SHA and explicit
TSP_GATE_TIMEBOX_RESEARCH_EVIDENCE marker. Set only the new research enable flag
after tests and before the verified main deployment. Disable it for rollback;
preserve old/new research evidence. Baseline rollback commit: af41a2523e971d71b792298b3eb5cd47a0ce987e.
