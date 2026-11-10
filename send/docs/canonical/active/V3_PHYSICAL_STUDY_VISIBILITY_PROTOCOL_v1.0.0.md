# V3_PHYSICAL_STUDY_VISIBILITY_PROTOCOL_v1.0.0

Status: ACTIVE OWNER RESEARCH WORKFLOW — 2026-11-06

The Owner requests visible OPEN_NOW stages so the complete strategy can be
studied, measured and improved. This supporting protocol belongs to the existing
research/observability domains; the functional inventory remains 43. It does
not replace the scoreless V3 strategy or approve execution expiry.

## Research visibility

An internally accepted physical OPEN_NOW with a complete PRE/CONFIRM chain may
admit one prospective experiment. When governed Execution Time is unavailable,
the new experiment may emit **OPEN_NOW · STUDIU V3** to the already opted-in
private Owner destination, only in Shadow Mode with broker execution disabled.
The publisher rechecks genuine PRE and CONFIRM API receipts and the existing
minimum 30-second PRE lead at the experiment's creation time. Every ordinary
physical and identity/history-policy gate still applies upstream.

The message explicitly identifies a simulation, the actual observed entry quote
and its timestamp, the frozen buffer, and the uncalibrated Model Time horizon.
Model Time is declared before entry; the published baseline is always the
predeclared bias-zero horizon, never whichever paired horizon later wins.

This is a research notification, not a canonical `SignalEvent`, approved expiry,
trade-execution handoff or canonical performance record. The ordinary OPEN_NOW
execution gate remains unchanged. No tier, group, affiliate or broker receives a
new publication through this path. If governed execution timing is available,
the normal OPEN is not duplicated by a study-entry notification.

## Observations and diagnosis

Genuine source ticks are retained in a bounded observation buffer. A delayed
research worker selects the earliest retained genuine quote inside each already
declared entry/expiry window. Existing source-second timestamp semantics and
10-second entry/2-second expiry limits remain unchanged. No candle close is
substituted for a missing tick, and a newer out-of-window price cannot recover
an observation. Future provider ticks are not exposed before their source time.
An absent observation remains UNKNOWN after its declared arrival allowance.

The original V3 expiry-research release read existing V2 records without rewriting
their outcomes and wrote version V3, preserving an exact hashed V2 backup before
the first upgraded write. Retained-quote observations expose
their distinct provenance. Old market features are never backfilled. New entries
freeze the originating physical DecisionObject measurements and their digest.
Research reports source coverage, sampling sources, operational handoff reasons
and descriptive outcomes by observed trend. Small samples are not efficacy proof.

Direction WIN/LOSS/DRAW and **buffer met at expiry** remain distinct labels.
Missing quotes remain UNKNOWN, not LOSS. Extra observations at Model Time plus
1, 3 and 5 minutes are declared before entry and are diagnostic only; they do not
change the original result, fit an approved expiry or authorize execution beyond
the governed horizon. Paired prospective training and untouched holdout rules
remain unchanged; no scoring, threshold relaxation or automatic activation is added.

## Directional result and collected evidence — Owner clarification, 2026-11-10

The Owner explicitly defines settlement by the actual entry and expiry prices:

| Direction | Expiry above entry | Expiry below entry | Equal prices |
|---|---|---|---|
| BUY | WIN | LOSS | DRAW |
| SELL | LOSS | WIN | DRAW |

This is the existing directional classifier. When both declared observations
are valid and available, a missing or unmet buffer does not turn the result into
UNKNOWN. A favorable expiry inside the buffer is WIN, with the buffer position
and incomplete full margin reported separately. At or beyond the favorable edge
it is WIN with the full margin met. The main result remains WIN; any fragility
description belongs to the separate buffer evidence, not a replacement verdict.

Each result presentation makes the collected entry and expiry observations
explicit, including their prices, source timestamps and available provenance.
A known result shows the numeric price comparison. Missing expiry evidence shows
UNKNOWN / incomplete data, which observation is missing, the original eligible
source-time window, and the recorded reason. A generic missing-observation reason
does not establish a specific provider failure, transport failure or rejection.
Receipt timing is not manufactured when the persisted sample does not contain it.

The chart distinguishes entry/threshold reference lines, the expiry-time line,
completed M1 candles and an actual expiry-price marker. A favorable earlier candle
or an earlier buffer-edge contact does not establish the price at the later
expiry. If the expiry observation is absent, its price field explicitly says
LIPSĂ; the available candle context cannot supply a closing-price verdict.

Periodic summaries show the current recovery-policy cohort separately from the
legacy cohort. Recovery-policy and duration-policy views partition the same
published records in different ways and must never be added together. Each view
reconciles WIN + LOSS + DRAW + UNKNOWN to its published source total. Unavailable
statistics are not converted to zeros or replaced by internal calibration rows.

This clarification improves presentation and auditability. It changes no
classification formula, quote window, confirmed duration, persisted outcome,
calibration authority or delivery destination. Historical results remain bound
to their original declared evidence and policy.

## Delivery evidence

Only entries admitted with the new publication intent may notify. Existing old
experiments cannot generate retrospective OPEN_NOW messages. Entry delivery must
start inside the original entry window. A reservation is saved before transport;
ambiguous acceptance is retained as UNKNOWN and not automatically retried.
Only an actual successful API response with a message ID counts as API acceptance.
It does not prove phone display. Results are sent only after an accepted study
entry and measured/unknown baseline expiry; future checkpoints cannot rewrite it.

Separate study-entry/result counters preserve the distinction from canonical
OPEN_NOW publication and broker execution. Pending experiments and real receipts
remain preserved across restart. The genuine quote archive can recover ticks
persisted before a restart, but cannot reconstruct ticks missed during an outage;
those observations remain unavailable.
Study transport uses one separate sender so API latency does not block the
sampling worker. Reservations are persisted independently of quote measurement.

## Prospective quote recovery — Owner correction, 2026-11-10

The Owner requests investigation and repair of UNKNOWN outcomes. Production
evidence after receiver/disk isolation includes genuine tick receive delays of
7.366 seconds; the previous four-second arrival grace can close an otherwise
recoverable observation prematurely. New experiments therefore freeze
`RETAINED_SOURCE_QUOTE_RECOVERY_V1` at capture: 15 seconds of arrival grace,
10 seconds of source-time entry eligibility, and 2 seconds of source-time expiry
eligibility. The final missing-data deadline for a new expiry observation is
expiry + 2 + 15 seconds. Observed results are available as soon as the eligible
tick is found. The extra arrival allowance never extends a trade, moves its
expiry, or admits a later source price. Existing experiments without this policy
retain their four-second allowance. Published final outcomes are immutable.

The bounded durable archive stores only genuine FINNHUB/OANDA:EUR_USD stream
observations, with the original provider millisecond timestamp, price and
receipt timestamp. Restart recovery exposes actual archived ticks with distinct
`DURABLE_STREAM_PROVIDER_TICK_BUFFER_V1` provenance. It never turns a persisted
candle into a tick, supplies live readiness, or substitutes startup time for
source/receipt time. Archive failure cannot block live quote receipt; durability
and archive failures are reported separately. The archive does not contain ticks
that were never received or restore observations from before its introduction.

Genuine out-of-order ticks remain available to the research observation selector,
which chooses the earliest eligible source tick deterministically. They cannot
rewind the current price, candles or readiness. Future-stamped observations are
quarantined from live chronology and cannot be selected before their source time.
No extra provider connection, alternate venue, historical candle fallback or
subscription change is introduced.

Storage protocol V5 preserves exact hashed pre-upgrade bytes before its first
write, reads V2/V3/V4 records without relabelling outcomes, and distinguishes
published results by frozen quote-recovery policy. The 15-second bound addresses
measured arrival latency; it is not a completeness guarantee. Source-event gaps
wider than the unchanged expiry window can still produce UNKNOWN. Issue #269
remains open until natural post-release evidence demonstrates acceptable source
coverage. Calibration and broker-execution authorities are unchanged.

## Prospective lifecycle diagnosis

`PHYSICAL_V3_OPPORTUNITY_TRACE_V1` observes the first internally accepted PRE,
CONFIRM and OPEN, and an observed FSM rejection that releases a traced opportunity
to cooldown. It records the exact rejection/noise/structure reasons, Model Time,
room-to-buffer ratio, candle phase, genuine PRE API receipt age at evaluation,
and declared cooldown. It cannot publish, alter gates, score, or release a trade.
First PRE must be observed prospectively; prior chains receive no manufactured
history. A first PRE observed after a failed publication is internal acceptance,
not proof of delivery. API receipt availability at evaluation is explicit.
Trace storage is separate and parameter-scoped, bounded to 32 episodes/256 KiB;
cumulative observed-event counts and retained episodes remain distinct. An
unobserved ending stays incomplete, never a fabricated rejection or market loss.
Trace timestamps preserve evaluation time separately from collector time. Logs
contain derived measurements and hashed opportunities, without quotes or private
destination IDs. This diagnostic does not change expiry-study observations or
establish strategy efficacy.
