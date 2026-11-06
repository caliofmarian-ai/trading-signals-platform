# Atomic quote observation and coverage timing V1

6 November 2026. The public Finnhub sample reader previously copied M1 candles,
then read health separately. A real tick could arrive between these reads,
pairing an earlier close with the newer tick's timestamp. A controlled replay
reproduced exactly that mismatch. No production mismatch is asserted from this
replay, and it does not explain every historical missing-expiry observation.

The Finnhub API now reads the current M1 close and its real observation timestamp
under the same reentrant ingestion lock. The existing history, continuity,
freshness and symbol checks still run. The source remains
LIVE_STREAM_CURRENT_M1_CLOSE and the original whole-second timestamp convention
is retained. Restored candles alone cannot yield a live sample. No new provider
request, interpolation, historical quote reconstruction or extra tick journal is
introduced. The other provider's API is outside this scoped Finnhub repair.

Malformed nonfinite/boolean prices, timestamps and volumes, negative volumes,
and timestamps outside the positive safe-integer domain are discarded before
they can advance live state or poison the candle history. Valid stream ticks
retain their existing candle and persistence behavior.

Price-free stream evidence now exposes the last 128 positive provider timestamp
steps and accepted-tick receive ages as sample/min/p50/p95/max plus a count of intervals
over two seconds. Receive age uses the provider's millisecond timestamp; it is
signed so future timestamps remain visible as such. This diagnostic does not
change the existing timestamp convention or freshness gate. Windows reset with
the process; they are not whole-cohort coverage estimates.

TSP_TELEMETRY_LOOP_TIMING reports last-128 monotonic loop intervals and work
durations once per minute, separately from configured sleep. It records intervals
over two seconds, without changing sleep, labels, sampling deadlines or strategy
gates. Diagnostic failure cannot interrupt the sampling worker. Loop intervals
alone cannot prove that an eligible quote existed during a missed window;
provider spacing and receive delay are separate evidence.

The 39 historical and subsequent buffer observations remain intact. No old label
or quote is repaired from today's state. Buffer snapshots, exact expiry windows,
missing-data rules, calibration scope, train/holdout and activation boundaries
are unchanged. Installation correctness and diagnostic coverage are not efficacy.
