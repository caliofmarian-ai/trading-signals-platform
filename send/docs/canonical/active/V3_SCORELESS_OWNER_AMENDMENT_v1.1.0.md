# V3_SCORELESS_OWNER_AMENDMENT_v1.1.0

Status: ACTIVE OWNER AMENDMENT — 2026-11-06

This version retains the complete scoreless rules of
[v1.0.0](V3_SCORELESS_OWNER_AMENDMENT_v1.0.0.md) and amends market-history readiness
under the Owner's instruction to reduce the dependence on uninterrupted history.
It remains an amendment of the same 43 functional domains.

## Saved context and present measurements

History is evidence for quantities measured in the present. A single current
price cannot establish speed, volatility or confirmed support/resistance.
The feed must distinguish the existing mathematical dependencies:

| Purpose | Existing evidence | Continuity |
| --- | --- | --- |
| Directional speed | 21 closed M1 candles, 20 intervals; normally 22 including forming | Recent exact M1 cadence |
| ATR14 and buffer | 15 M5 candles, including the preceding close | Recent exact M5 cadence |
| EMA50/EMA200 context | At least 201 genuine saved M5 observations | Earlier gaps disclosed, no fabricated prices |
| Structural levels | Existing 80-observation M5 lookback, two neighbors per side | Each confirming five-bar pivot window must be complete and consecutive |

The provider must not impose 201 consecutive M5 bars when the market model
requires only 15 recent consecutive bars for ATR. Older genuine context survives
restarts and may retain disclosed gaps. EMA remains an observed-bar context
indicator; it is not represented as an uninterrupted elapsed-time measurement.
No gap is compressed into the speed or ATR calculation. Recent missing bars,
invalid OHLC, stale quotes and insufficient genuine context still block decisions.

Operational policy: `RECENT_PHYSICS_WITH_SAVED_CONTEXT_V1`. It is explicitly bound
in the validated parameter bundle and its hash. Existing V3 bundles migrate once
with a byte-identical backup; physical parameter values are preserved. Unknown
history policies and scoring controls remain invalid. Rollback restores the saved
pre-migration bundle together with the preceding code.

## Opposing recent movement at CONFIRM and OPEN_NOW

Owner correction, 2026-11-11. Evaluate net movement using the same 20 completed
M1 close-to-close intervals and the existing recency weights 1–20. Favorable
movement is `directional_effective_speed`. Opposing movement is
`weighted_gross_speed - directional_effective_speed`. For BUY, price declines
are opposing movement. For SELL, price increases are opposing movement.

At CONFIRM and OPEN_NOW, reject through the existing physical eligibility path
with `MARKET_DIRECTIONAL_FLOW_OPPOSED` when weighted opposing movement strictly
exceeds weighted favorable movement. Equal movement is neutral. Existing
evidence gates govern missing data and PRE eligibility. Rejection preserves the
original signal direction. Buffer distance and duration are calculated under
their existing contracts. The decision remains scoreless.

Prospective validation of the new rule uses `V3_DIRECTIONAL_FLOW_GATE_V1`.
Earlier observations retain their original cohort and can settle there.

## Real market time to the price buffer

Owner correction, 2026-11-11. The safety buffer is a price distance, not a
manually added time reserve. For each new private OPEN study, freeze the buffer
and confirmed study horizon already declared before entry, then measure the
earliest genuine Finnhub EUR/USD tick after the observed entry that reaches the
favorable buffer edge. Persist the elapsed seconds and its fraction of the
confirmed horizon under `BUFFER_FIRST_OBSERVED_HIT_TIME_V1`.

This is a prospective diagnostic only. It does not change PRE, CONFIRM,
OPEN_NOW, Model Time, the confirmed duration, the true expiry, publication or
execution. It must use retained provider ticks with original millisecond source
and receipt times; it may not interpolate, substitute OHLC, infer a crossing
inside a source gap or backfill earlier studies. `OBSERVED_HIT` means only that
an eligible tick was observed at or beyond the frozen edge. A path without such
a tick is reported separately from a missing path. The expiry result and
buffer-at-expiry result remain separate, because an earlier hit can reverse
before expiry. No observation may auto-select or activate a new duration.
Bounded aggregate evidence is emitted as `TSP_PHYSICAL_BUFFER_FIRST_HIT_TIME`;
it contains counts and timing distributions, never prices or private identities.

## Continuity of operation and research

The cloud feed collects independently of the Android phone's connection. Phone
offline time does not clear the server history. A provider/server outage cannot
be recovered by inventing missing candles; only the affected recent measurement
window must rebuild once sufficient genuine saved context exists.

PRE/CONFIRM continuity is bound to the declared history policy. An opportunity
started under a preceding data policy cannot inherit a new-policy confirmation.
Execution expiry remains separately governed. Changing the parameter hash
invalidates an old-scope calibration; no artifact is manufactured by migration.

Prospective expiry research uses protocol `PROSPECTIVE_PHYSICAL_V3_EXPIRY_V2`,
with the history policy in its scope and separate `recent_history_state.json`.
Prior scored and prior scoreless cohorts remain preserved. Owner timing uses
a separate history-policy ledger. Status reports saved context and recent
contiguous windows separately. This change does not claim calibrated efficacy.
