# Prospective execution-expiry calibration V1

Owner task: 5 November 2026, calibrate first; broker integration is a later task.
This is a research protocol implementing observation, not a new active strategy
canon, production calibration approval or broker authorization.

## Paired prospective evidence

Existing severity 0..20 research FSMs supply complete PRE -> CONFIRM -> OPEN_NOW
chains retaining the same data/structure/time/Trade Physics gates and 30-second
PRE lead. Record the CONFIRM Model Time and OPEN Model Time at their actual
observations. A chain begun before this instrumentation is not backfilled.

Before obtaining any entry quote, declare pressure-bias candidates
`0, .05, .10, .15, .20, .25` and exact horizons `Model Time * (1 - bias)`.
These are experimental hypotheses, never default production values. Reject a
candidate horizon below `t_needed_adjusted`. Use the existing real Finnhub
sample validator, ten-second entry deadline and two-second post-expiry sample
tolerance. Never interpolate, backfill, round expiry or treat missing quotes as
losses. Quote gaps become UNKNOWN. Prices and identifiers stay in private state;
logs contain only scope, counters, timing quantiles and readiness summaries.

Identical direction/open timestamp/model/adjusted-time/source entries occurring
at multiple severity levels share one experiment and quote set. Level membership
is retained for analysis, but is not multiplied into independent sample size.
The ledger is atomic, locked, restart-safe, and bounded to 512 unique entries and
4 MiB. At capacity, new registrations are explicitly counted as rejected while
existing pending observations continue; no old evidence is overwritten. This
first fixed calibration cohort is not an unlimited archive.

## Predeclared analysis and review policy

Within each level, select entries chronologically without consulting outcomes.
Keep only nonoverlapping intervals, including the entire entry-delay allowance,
longest declared horizon and quote tolerance. The first 60 admitted intervals
are training; the next 60 are an untouched holdout. Never select expiry using
holdout performance or keep extending the holdout until it passes.

Require complete finalization, at least 30 decisive WIN/LOSS samples per split,
and at most 10% UNKNOWN among eligible observed/unknown results. Select the
candidate on training Wilson 95% lower bound, breaking ties toward less pressure.
Report READY_FOR_REVIEW only when the fixed holdout's Wilson lower bound reaches
the Owner's 80% target. DRAW, INFEASIBLE and missing data are separately counted.
This policy is declared for this experiment, not claimed to be a pre-existing
canonical sample-size rule. Wilson describes binomial sampling uncertainty;
regime dependence and Finnhub-versus-future-broker quote differences remain.

A proposal derives CONFIRM tolerance from the maximum observed training difference
between the CONFIRM forecast and the selected OPEN expiry, widened if necessary
to cover pressure over the governed model range. Every fixed holdout interval
must contain its selected OPEN expiry. Exact minimum/maximum horizons follow that range.
Proposals retain a source digest and source scope. They do not write
`execution_calibration.json`, mutate thresholds, publish signals or call a broker.
Source-scope drift cannot be mixed into the cohort. Deployment restarts do not
erase already collected evidence.

## Operation

The existing Owner private/shadow research opt-ins enable collection. No new
provider request, credential, Telegram route or app service is created.
`TSP_EXECUTION_EXPIRY_CALIBRATION` is a minute-level status marker, including
WAITING_FIRST_COMPLETE_CHAIN when no new complete chain has yet occurred.
The Owner private audit includes the complete sanitized analysis. Local command:

```
PYTHONPATH=send python -m scripts.analyze_execution_calibration PRIVATE_STATE.json
```

Synthetic test fixtures prove implementation behavior only; their READY status is
not production evidence. No efficacy or phone-receipt claim follows from a build.
