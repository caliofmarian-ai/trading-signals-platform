# UNKNOWN outcome investigation and quote recovery — 10 November 2026

## Verified baseline

Repository: `caliofmarian-ai/trading-signals-platform`, main
`a39eadc948f12f40768aeb30a45741c831d7b70a` (#268).
Railway production deployment `917b373c-bdaf-4033-9d64-144b946fcaba` became
successful at 08:30:04 UTC / Europe/Dublin. Earlier corrections #257, #258,
#266 and #267 were already present; this investigation does not claim them as
new work. Remaining coverage issue: #269, parent #217.

At 08:43 the current seconds-duration published cohort contained 25 results:
9 WIN, 4 LOSS, 0 DRAW, 12 UNKNOWN. Every UNKNOWN in that cohort had reason
`EXPIRY_OBSERVATION_MISSING`. This cumulative cohort spans collector releases;
it is not a measurement of #267 or this correction. All published duration
policies totalled 353 = 124 WIN + 100 LOSS + 6 DRAW + 123 UNKNOWN.

## Two different failure mechanisms

1. **Source-window coverage.** The research protocol requires an actual provider
   tick at or after the frozen expiry, within two source seconds. At 08:42:07
   the requested 08:42:02–08:42:04 window was bracketed by retained ticks at
   08:42:01 and 08:42:06. There was no eligible tick, eviction, future tick or
   in-window chronological rejection. This diagnostic window is not asserted
   to be a published study outcome without a matching study identity.

   Published study #218 had entry 06:53:57, duration 246 seconds and expiry
   06:58:03. The lookup at 06:58:06.020702 had 269 retained quotes and latest
   source tick 06:57:58. Its published result was UNKNOWN at 06:58:11. This
   proves missing evidence at lookup, not that the vendor never emitted or
   subsequently delivered a tick.

2. **Arrival latency.** After the receiver was isolated from candle disk writes
   at 06:49:28, sampled accepted-tick receive-age maxima still included 4.352,
   6.485, 5.439, 4.757, 4.126, 4.106 and 7.366 seconds. The existing four-second
   grace can therefore finalize before a valid source-window tick arrives.
   Aggregate latency metrics do not identify which past UNKNOWNs are recoverable.

Across 45 instrumented diagnostic events / 25 unique windows from 06:07:59 to
08:42:07 there were 25 `NO_TICK_REACHED_WINDOW`, 12
`BRACKETED_WITHOUT_ELIGIBLE_TICK` and 8 `OBSERVATION_FOUND_AFTER_MISS` events.
No instrumented missing window showed eviction or an in-window chronological
rejection. These are event counts, not 45 independent trades.

The 08:40 feed snapshot had one connection, zero transport failures, 605
accepted ticks, matched requested/persisted candle generations and no writer
failure. Receive-age p95 was 0.320 seconds, while provider interval p95 was
4.609 seconds and the maximum was 10.903 seconds. Thirty of the last 128
positive source intervals exceeded two seconds. Faster polling cannot create
an event absent from the received stream.

## Implemented correction and limits

- New experiments freeze `RETAINED_SOURCE_QUOTE_RECOVERY_V1` with 15 seconds of
  arrival grace. The source windows remain ten seconds for entry and two for
  expiry. This is a bounded response to measured latency, not a guarantee that
  every late tick arrives within fifteen seconds.
- Existing rows retain their four-second allowance. Version V5 stores the new
  per-row policy and backs up exact old V2/V3/V4 file bytes before migration.
- A separate bounded durable archive retains actual FINNHUB/OANDA:EUR_USD ticks
  with provider and original receipt timestamps. Restored observations have
  distinct provenance and do not establish live market readiness.
- A valid out-of-order tick may provide research evidence without rewinding
  current market state. Future timestamps cannot poison the live chronological
  high-water mark. Selection remains deterministic and restricted to the
  declared source window.
- Missing raw ticks are not manufactured from candle closes, previous prices,
  another provider, or later favorable prices. Published historical results
  remain unchanged. A restored archive does not reconstruct a feed outage.
- Published outcome accounting includes a separate quote-recovery-policy
  partition. Aggregate calibration analysis is not independent acceptance of
  the new policy, and no execution calibration is automatically activated.

Durable retention and chronological isolation fix reproducible local loss
conditions. Neither was proved to cause the recent instrumented UNKNOWNs.
The remaining sparse-source limitation stays open in #269.

## Same-source recovery research

Primary source checked on 10 November 2026:
<https://finnhub.io/static/swagger.json>.

The official schema documents Forex exchange, symbol, candle and rates
endpoints. Forex candle resolutions begin at one minute. `/stock/tick` is
described as Global Stocks Tick Data and lists stock venues; no exact historical
OANDA Forex tick recovery endpoint was established. The WebSocket supplies
actual millisecond source timestamps but documents no replay command. Thus no
REST fallback, account upgrade or competing stream is activated by this change.
This is absence of a documented suitable capability, not a claim about every
private enterprise offering.

## Acceptance evidence

The pre-change #268 release-only baseline from 08:30:04 to the last queried
08:45:28 evidence had two published completed studies (#250, 160 seconds;
#252, 198 seconds), both with actual expiry ticks and WIN outcomes. This tiny
sample does not establish reliable coverage.

Required checks for this change: late genuine quote regression; unchanged
source-window and historical-result tests; exact-byte migration; actual-tick
restart recovery; live readiness isolation; deterministic late/future ordering;
blocked/failing disk isolation; full repository CI; matching production commit;
and natural release-specific outcome observation. Record exact test/deployment
results in the pull request. Keep #269 open until the data coverage requirement
is met by real evidence.
