# Strategy efficacy and missing-expiry estimates — 10 November 2026

## Verified starting point

Read-only production audit at **11:28 UTC / Dublin**, deployed commit
`8696425dae369624330c5ba73ef4a9914d818d9d`, Railway deployment
`5cc81f5f-2aff-4605-ae4d-3164fe8790e3`, project
`54752c90-3929-4854-9b50-049b5c63ab98`, service
`c2c41294-4eca-4092-8cdf-94ba57511c6e`.

| Published population | WIN | LOSS | DRAW | UNKNOWN | Total |
|---|---:|---:|---:|---:|---:|
| Legacy quote policy | 124 | 100 | 6 | 123 | 353 |
| Recovery policy introduced by #270 | 4 | 3 | 0 | 2 | 9 |
| All published studies | 128 | 103 | 6 | 125 | 362 |

All 125 published UNKNOWNs have recorded reason
`EXPIRY_OBSERVATION_MISSING`. The nine recovery-cohort results were independently
recounted from 18 delivery events (one entry and one result each), bounded
09:09:20–11:28:02: #266 WIN, #267 LOSS, #310 LOSS, #317 WIN, #328 LOSS,
#329 UNKNOWN, #337 UNKNOWN, #339 WIN, #338 WIN. All had API acceptance; no
duplicate result inflation was found.

The 231 decisive published outcomes have 128/231 = **55.41% observed WIN**.
There are also 125/362 = **34.53% UNKNOWN** and six draws. These studies span
historical duration policies and can overlap; this is not a validated estimate
of future strategy profitability. The current seconds-duration grouping is
34 = 13 WIN + 7 LOSS + 14 UNKNOWN, with 65% WIN among only 20 decisive results.
It is another grouping of the same published records, not an extra population.

## Reconstructed post-repair UNKNOWNs

| Study | Entry | Declared expiry | Missing eligible source window | Neighbor timestamps |
|---|---|---|---|---|
| #329 BUY | 1.122445 at 11:04:41 | 11:12:31; 470 seconds | 11:12:31–11:12:33 | 11:12:12 and 11:12:49; 37-second gap |
| #337 SELL | 1.12222 at 11:20:33 | 11:25:15; 282 seconds | 11:25:15–11:25:17 | 11:25:14 and 11:25:18; 4-second gap |

The exact #329 lookup at 11:12:34 had last retained timestamp 11:12:12;
later adjacent-window diagnostics show the next timestamp 11:12:49. They are
not asserted to be #329's terminal diagnostic. The #337 exact-window diagnostic
is `BRACKETED_WITHOUT_ELIGIBLE_TICK`. Both show zero eviction, zero future ticks
and zero in-window out-of-order ticks. These data establish missing eligible
received observations, not what the vendor emitted upstream.

The 11:26:12 collection snapshot (logged 11:26:20.972975) had 6,496 restored
ticks, 377 new received and 377 persisted generations, zero pending generations,
zero archive/request/start failures and one connection with zero transport
failures. In its bounded last-128 source-interval sample, 52 intervals exceeded
two seconds. Waiting for arrivals cannot create a source-time observation in
an empty expiry window. Issue #269 therefore remains open.

## Strategy findings

V3 is deterministic and scoreless: EMA/RSI supply direction/context and physical
activity, noise, structural room and time-feasibility rules gate admission.
This verifies implemented logic, not predictive efficacy. The current evidence
does not establish the Owner's minimum 70% WIN objective or complete outcomes.

The separate internal population is 427 = 142 WIN + 117 LOSS + 6 DRAW + 162
UNKNOWN. Its missing reasons are 23 entry and 139 expiry observations. It must
not be added to the published population. Its model-labeled `WITH_TREND` group
has 109 WIN / 65 LOSS; `COUNTER_TREND` has 33 WIN / 50 LOSS (62.64% and 39.76%
among decisive outcomes). This is an exploratory weakness, not causal proof or
a tested rule to remove future countertrend entries. The context label does
not always mean the final direction opposes the EMA orientation.

The duration estimator uses recency-weighted favorable movement without
subtracting adverse movement. A synthetic alternating 21-close sequence
100,101,100,...,100 has zero net change but produces BUY speed 0.476190/min
and SELL speed 0.523810/min. This demonstrates that the measure is not net
directional drift; it does not prove that this formula caused every live LOSS.

Full buffer margin at expiry is met in 45/237 observed published outcomes
(18.99%); 83 of the 128 WINs are favorable without the full margin. Thus buffer
size is not evidence of a guaranteed WIN, and an incomplete margin must not
erase a real directional WIN.

Calibration is `TRAINING_DATA_QUALITY_FAILED`, with no selected bias, no ready
policy and no evaluated selected holdout (`untouched_holdout=null`). The fixed
first 60 nonoverlapping training entries remain the same when later records
arrive. New quote-recovery policy is not a new training scope. Consequently
additional collection alone cannot repair the already failed first training
sample. A prospectively declared evaluation cohort, preserving the old one,
is required for a meaningful future recalibration. The current store is also
bounded at 512 experiments; no strategy or calibration change is made here.

## Owner-requested implementation

The Owner requested approximate closing-price information between the nearest
known observations and explicitly authorized implementation followed by
production verification. The supporting visibility protocol now defines
`ADJACENT_SOURCE_QUOTES_ESTIMATE_V1` as separate approximation evidence:

- nearest genuine same-source quote on each side, at most 60 seconds per side;
- visible endpoint prices, timestamps, source and gap;
- WIN estimated / LOSS estimated / inconclusive / unavailable;
- endpoint range explicitly not a bound on the unobserved path;
- original UNKNOWN, observed quote absence, duration, buffer and calibration
  evidence preserved;
- estimates separately counted within published UNKNOWN, never as verified wins;
- no new connection, paid access, invented ticks or broker action.

Implementation tests and actual deployment evidence belong to the associated
pull request. This audit does not claim a production release before one is
verified, a zero-UNKNOWN feed, or improved strategy performance.
