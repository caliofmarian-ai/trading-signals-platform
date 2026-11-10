# Directional results and collected-price evidence — 10 November 2026

## Owner instruction and baseline

The Owner clarifies that BUY is WIN when the expiry price is above entry and
LOSS when below; SELL reverses that comparison. A favorable close inside the
buffer still wins. When data are unavailable, reporting must say what was
collected and what is missing instead of presenting an unexplained UNKNOWN.

Fresh repository and production baseline: `51d1a67b2c58f79512a56812ec3e21d75648beb2`
(#270), Railway deployment `f1f9a64a-65f5-40f2-a690-7e2acdda68ae`, SUCCESS since
09:09:21 UTC. This correction builds on the already-deployed durable quote
archive and prospective 15-second arrival allowance; it does not claim those
changes again or alter their source-time windows.

## Verified findings

1. The actual directional classifier already implements the Owner's rule.
   Equal entry/expiry prices are DRAW. The buffer measurement is independent.
   The persisted-state validator rejects UNKNOWN observations with a non-null
   expiry quote; two valid stored prices cannot silently become UNKNOWN.
2. The chart uses complete M1 candles wholly inside the study interval. A last
   candle can finish before the actual expiry. For example, a study expiring at
   10:46:20 can have its last full plotted M1 candle end at 10:46:00. That earlier
   close does not establish the price twenty seconds later. Horizontal entry
   and buffer reference lines are also not an observed market-price path.
3. The original result caption says `cotație lipsă`, but does not expose the
   recorded UNKNOWN reason, eligible window or quote provenance. The chart's
   absent-price dash is poorly rendered by its portable font. Its visible
   earlier candles and buffer contacts can therefore be misread as final-price
   evidence. A separate `WIN fragil` heading also obscures the primary WIN label.
   Fixed seven-place chart formatting can make distinct close prices look equal;
   quote displays must preserve their distinction. Computed buffer boundaries
   that require display rounding must explicitly identify that approximation.
4. Periodic owner messages show duration cohorts, while #270's separate quote
   recovery cohorts exist only in the underlying analysis. The current duration
   cohort still includes historical UNKNOWNs from older collection behavior.
5. Finalized outcomes are immutable. This presentation change does not silently
   rerun historical settlement against later available observations, substitute
   a last-before quote or candle close, or reconstruct never-received data.

## Production observations before this presentation correction

At the bounded 10:48 UTC inspection, the new recovery-policy published cohort
had **3 completed results = 1 WIN + 2 LOSS + 0 DRAW + 0 UNKNOWN**. All three had
a genuine quote at their exact recorded expiry second:

| Signal | Observed entry time | Confirmed duration | Expiry / expiry quote time | Outcome |
|---|---|---:|---|---|
| #266 | 09:11:35 | 120 seconds | 09:13:35 | WIN |
| #267 | 09:13:33 | 120 seconds | 09:15:33 | LOSS |
| #310 | 10:41:35 | 285 seconds | 10:46:20 | LOSS |

#266 was SELL and its favorable movement was inside the buffer (coverage
0.250866). It was already counted as WIN despite incomplete full margin. The
three-result new cohort had 0 full margins met and 3 not met. Exact entry prices
and frozen buffer boundaries are not inferred from these aggregate ratios.

Historical published results remained 353 = 124 WIN + 100 LOSS + 6 DRAW +
123 UNKNOWN. All published results totalled 356 = 125 WIN + 102 LOSS + 6 DRAW +
123 UNKNOWN. These are different populations from the broader internal
calibration baseline: 419 = 139 WIN + 116 LOSS + 6 DRAW + 158 UNKNOWN, with
22 missing entries and 136 missing expiry observations.

The internal baseline added one missing-expiry UNKNOWN between the 10:42 and
10:43 reports while the published result count stayed unchanged. During that
interval, a diagnostic window 10:42:43–10:42:45 was bracketed by retained ticks
10:42:40 and 10:42:48, with zero eviction or in-window chronological rejection.
The diagnostic has no study ID, so timing alone is not definitive row-level
correlation. It is evidence that missing source-window coverage still exists,
not a published new-policy UNKNOWN.

## Correction and acceptance

- Result captions explicitly name the primary WIN/LOSS/DRAW result, show the
  actual numeric comparison and collected entry/expiry evidence, and keep buffer
  position/full-margin evidence separate. Quote precision remains visible;
  rounded long buffer boundaries carry an explicit approximation marker.
- Missing observations are explained using stored reasons and original eligible
  windows. No unrecorded receipt time or provider root cause is invented.
- Charts make absent expiry prices explicit and distinguish earlier candle or
  buffer context from an actual expiry observation.
- Periodic messages separate recovery cohorts from their historical predecessors
  and label duration groupings as an alternate view of the same records.
- Regression coverage must retain BUY/SELL, equality, inside/edge/beyond-buffer,
  missing-expiry-with-favorable-context and inconsistent-cohort behavior. Caption
  and message lengths must fit Telegram limits; representative charts require
  visual inspection.

Exact test, commit and production verification evidence belongs in the pull
request. Source coverage remains open in #269. This change proves neither a
winning strategy nor a guaranteed zero-UNKNOWN feed.
