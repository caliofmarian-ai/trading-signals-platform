# Quote-window investigation and second-duration acceptance — 2026-11-10

Status: SUPPORTING DIAGNOSTIC RECORD, NOT CALIBRATION OR STRATEGY AUTHORITY
Baseline: `2309bf3477ee457458fc8ec306af7c074f9ce774` (PR #265)
Railway deployment: `5e86e0d6-360f-42d6-9911-221a0562877a`

## New duration lifecycle now has natural production evidence

Signal `10.11.2026 · 00:39:16 · nr. 42`, SELL:

- PRE and CONFIRM: PHOTO with Owner API acceptance, log ingestion at
  00:39:26.661/662 UTC. CONFIRM duration is **223 seconds (3 min 43 s)**,
  confirmation timestamp `1794271158`, policy
  `ADJUSTED_MOVEMENT_SECOND_CEILING_V1`.
- OPEN study: PHOTO/API_ACCEPTED, logged 00:39:52.632 UTC; observed entry
  `1794271188` (00:39:48), planned expiry `1794271411` (00:43:31).
- Result: PHOTO/API_ACCEPTED, logged 00:43:39.536 UTC; same duration, expiry,
  confirmation timestamp and plan ID; recorded result WIN, expiry price
  `1.121635`, quote source timestamp exactly `1794271411`.
- Plan ID: `d65dd6758acc67b4a8bf19b7339ab0ec528d08b4c3fabc2f17ae2dafc191e148`.

This proves the natural API-delivered duration lifecycle and the recorded paired
observation. It does NOT prove broker settlement, phone display, buffer clearance
for that particular signal or future strategy efficacy. The entry/expiry clock
is not the log ingestion timestamp. No synthetic production signal was sent.

## Remaining missing-quote problem

At 05:45 UTC, policy-separated published results for the second-duration policy
were **19 = 6 WIN + 2 LOSS + 11 UNKNOWN**; five of the eight observed outcomes
met the full buffer margin. The apparent 75% directional rate uses only eight
observed decisive outcomes, not all 19 and not independent validated trials.
Every UNKNOWN in this cohort was `EXPIRY_OBSERVATION_MISSING`.

The aggregate historical results (347 delivered results) and independent
OPEN-model calibration grid (396 finalized experiments) are different cohorts.
The latter still reported `TRAINING_DATA_QUALITY_FAILED`, no selected bias and
no ready policy. Do not mix these populations or promote calibration.

Example of feed evidence near missing result #135: the 04:17:48 log reported one
connection, no transport failures, and 128 positive provider steps with p95
10.63 seconds, max 32.584 seconds; 51 steps exceeded two seconds. Receive-age
maximum was 15.288 seconds. This is evidence of irregular available timestamps
and occasional delivery/processing lag, NOT proof of the precise cause of each
missing expiry and NOT proof of a provider outage. Heartbeats are not prices.

## Source audit and bounded diagnostic change

The accepted-tick buffer and query were verified at blob
`f2adfa82a14b3fb85e9b2c69996c3f2a2a8e0914`. Existing tests intentionally reject
out-of-order ticks and exclude raw future ticks. This patch does NOT reinterpret
those rejections as usable prices. It records rejected source timestamps only,
in a bounded deque, and reports diagnostic evidence for requested missing windows.

`TSP_QUOTE_WINDOW_EVIDENCE` reports the original target/window, lookup time,
nearest accepted source timestamps before/after, retained range, eviction count,
future ticks and recent out-of-order rejections in that window. It distinguishes
an empty restarted buffer, a target outside the retained range, a stream not yet
reaching the window, a bracketed missing interval and actual policy rejection.
A later genuine successful lookup after a prior miss gets a distinct diagnostic.
That observation may occur during the existing grace; it never reopens a result.

The records are snapshots AT LOOKUP, never terminal UNKNOWN classifications or
an automatic diagnosis of upstream fault. Only timestamps and counts are logged;
no prices, credentials, destination IDs or raw provider frames are included.

Bounds: 512 tracked windows, 512 recent rejected timestamps, at most 32 diagnostic
events per minute per process. Repeated same-reason lookups are suppressed;
changed reason/recovery may emit again. Suppression is explicit. Diagnostic
exceptions cannot erase a selected quote or manufacture one; printing happens
outside the ingestion lock. Saved candles cannot restore raw tick evidence.

No duration, strategy gate, source-second convention, quote-window width, arrival
grace, provider, publication route, historical observation or outcome changes.
The active research protocol's 10-second entry/2-second expiry windows remain
unchanged. Missing values remain UNKNOWN. Broker execution stays disabled.

## Acceptance

Tests must verify both diagnostics and unchanged selection (future ticks,
out-of-order rejection, inclusive boundaries, retention, restart, failures,
copy isolation, rate/memory bounds). Exact-head Repository CI and matching
Railway deployment must be checked before claiming rollout. Natural window
records are needed before attributing future misses to a specific mechanism.
