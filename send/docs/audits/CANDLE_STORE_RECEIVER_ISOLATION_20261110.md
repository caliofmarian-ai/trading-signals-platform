# Candle-store receiver isolation — 2026-11-10

Status: SUPPORTING IMPLEMENTATION / REGRESSION RECORD
Baseline: `f031f28dd014a912858229973b76bfd998e03ad8` (PR #266)
Verified baseline feed blob: `8da8757dc615950778409bc7a77fa98170c0829d`

## Source defect and bounded claim

The live receive loop calls `ingest_message`, which synchronously serializes and
replaces the complete M1/M5 candle file after each accepted trade frame. A slow
write therefore prevents the same thread from reading its next WebSocket frame.
An OSError escapes ingestion into the transport retry handler, unnecessarily
closing the socket even though a real tick has been accepted in memory.
The old persistence payload also holds references to mutable candle dictionaries
after releasing the quote lock, rather than freezing a snapshot.

A deterministic offline blocked-write reproducer compared the exact baseline
module with this patch. While disk remained blocked, baseline accepted one tick
and did not read the second frame; patched receiver accepted both ticks and
made the second quote queryable before the writer was released. This proves a
local blocking defect and its removal, NOT that all historic missing expiries
were caused by disk latency.

## Change

- One coalescing writer per live feed. Requests contain only monotonically
  increasing generations; no unbounded queue of candle copies or tick payloads.
- The latest snapshot is copied under the feed lock; serialization, file I/O and
  replacement run outside it, serialized by a separate store I/O lock.
- A request arriving during a write causes a follow-up write. A failed attempt
  remains pending and retries after one second, including when no new tick arrives.
  Frequent ticks cannot defeat the failure backoff.
- Disk errors remain explicit (`store_write_state: ERROR` and writer failure
  evidence) but are no longer misclassified as socket failures. A subsequent
  successful snapshot clears current error state without erasing failure counts.
- Stream termination drains requests after the last accepted frame, with a
  bounded two-second join. Failure/timeouts are NOT claimed as durable saves.
  A blocking OS write cannot be forcibly cancelled; the existing single daemon
  may finish later. Sudden process death may still lose unsaved candles and the
  already nonpersistent tick buffer; this change does not claim restart recovery.
- Explicit direct/offline ingestion retains synchronous persistence.
- The existing stream/health evidence includes a price-free bounded writer
  summary: pending/completed generations, successes/failures and last-128 write
  durations. Error messages/paths are not retained. No extra market requests.

## Invariants unchanged

Only genuinely accepted provider ticks populate the observation buffer. No new
sampling window, carry-forward price, interpolation, out-of-order acceptance,
future-tick admission, duration, calibration artifact, signal routing, score,
broker action or historical outcome rewrite. Stored OHLC candles are not turned
into raw tick observations. Original atomic replacement and private permissions
are retained; a failed replacement leaves the previous saved file intact.

## Local verification

29 focused tests passed. Coverage includes bounded burst coalescing (10,001
requests, two writes), receiving the next frame during a blocked disk write,
immutable snapshots during serialization, disk failure/recovery without socket
reconnect, retry without new ticks, backoff, invalid deadlines, bounded shutdown,
thread-start failure, no second writer, failed replacement, restart semantics,
unchanged quote-window selection and 128-sample timing retention.

Baseline feed plus the three real imported dependency modules were reconstructed
and matched against exact Git blob SHAs before editing. The full repository
suite was not available locally; Required Repository CI on the exact PR head
and merge must pass before claiming release. Production acceptance requires the
matching deployed commit and natural stream evidence with the writer running.

## Missing-quote investigation remains open

New diagnostics after #266 still show source windows bracketed by available
quotes with no qualifying tick, and a distinct late-but-valid in-window recovery.
For example, 06:25:12–06:25:14 was bracketed by06:25:11 and06:25:17; no retention
eviction, future exclusion or rejected tick in that window was recorded.
This patch cannot manufacture that missing source observation or demonstrate
upstream provider fault. Residual UNKNOWN and strategy efficacy must be evaluated
separately after deployment; a passing concurrency regression is not calibration.
