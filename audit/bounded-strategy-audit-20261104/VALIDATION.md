# Validation — bounded live strategy evidence

## Reproduced failure

The new private-audit integration regression first failed against main 5a5d2d4: `handle_audit_runtime` invoked the full-history `_iter_jsonl` reader before slicing to 50 records. After the correction it returns the final 50 decision rows and an earlier sparse execution event with its original identity, without invoking that iterator.

## Local validation

- Full repository suite: **1,903 passed in 54.69s** (31 additional cases over the 1,872-test baseline).
- Focused initial run: 137 passed; the final full run also includes the subsequent transient-status-write retry case.
- `git diff --check`: clean.
- Bounded JSONL evidence: 16 MiB maximum per source, 5,000 engine records maximum, last 50 exported rows per family. A sparse 32 MiB source is tested with a measured 128 KiB read budget; no unbounded read is permitted. Exact event identity/schema and observed interval are preserved. Missing/empty/corrupt/oversized/rotated/truncated/append-during-read sources are distinguished; an incomplete record cannot become a false empty report.
- Permission checks precede source access. Sparse execution events have their own explicit bounded-window metadata; no complete-history absence is claimed.
- A derived, price/identity-free research summary is persisted independently, limited to 8 KiB, validated for exact truth labels, counts and decisive denominator. UNKNOWN and DRAW remain outside WIN+LOSS. An unrelated shared status replacement does not erase this observation. Observation time is explicitly not a heartbeat; current activation is reported separately. Transient persistence failure is retried without inventing or duplicating outcomes.
- Strategy mathematics, decision thresholds, calibration values, Finnhub distribution block and broker controls are unchanged.

## Production evidence before this patch

Private audit generated 2026-11-04T09:16:30Z, SHA-256 `46db90f105bee5bc94ea9da379f1303070a6a18f21d5057052a5e14b7357e593`. Its runtime snapshot reports 3,484 real Finnhub ticks, 500 M1/M5 bars and 1,069 evaluations; last 50 decision rows at 09:14:19.699Z–09:16:11.435Z are REJECT (activity 49, structure/time 34 each, unstable noise 7). Its error tail includes a post-#220 PRE distribution block at 08:52:03.658Z and no post-#220 signal-engine error. This proves a real PRE reached Distribution, not live OPEN_NOW or delivery. The artifact is private and is not committed.

CI, deployed SHA, terminal Railway status and actual post-deploy Telegram audit must be verified separately and recorded in the PR. No calibration approval, strategy efficacy, Pocket Option result or permitted signal delivery follows from these software tests.
