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

Accepted source ticks are retained in a bounded in-process buffer. A delayed
research worker selects the earliest retained genuine quote inside each already
declared entry/expiry window. Existing source-second timestamp semantics and
10-second entry/2-second expiry limits remain unchanged. No candle close is
substituted for a missing tick, and a newer out-of-window price cannot recover
an observation. Future provider ticks are not exposed before their source time.
An absent or evicted observation remains UNKNOWN.

The V3 expiry-research protocol reads existing V2 records without rewriting
their outcomes and writes version V3, preserving an exact hashed V2 backup before
the first upgraded write. New retained-quote observations expose
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
remain preserved across restart. The in-process quote buffer cannot reconstruct
ticks missed during an outage; those observations remain unavailable.
Study transport uses one separate sender so API latency does not block the
sampling worker. Reservations are persisted independently of quote measurement.

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
