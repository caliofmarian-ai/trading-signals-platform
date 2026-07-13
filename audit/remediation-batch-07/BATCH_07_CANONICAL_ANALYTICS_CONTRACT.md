# BATCH_07_CANONICAL_ANALYTICS_CONTRACT

## Analytics Engine — Canonical Contract

### Module: `send/core/analytics_engine.py`

### Path Resolution

All paths are resolved from environment variables (following the pattern in `observability_logger.py`). No `/opt/binarybot/` prefix is hard-required.

| Variable             | Default                                         | Description                  |
|----------------------|-------------------------------------------------|------------------------------|
| `OBS_DIR`            | `/opt/binarybot/observability`                  | Observability log directory  |
| `OUTCOMES_LOG`       | `/opt/binarybot/outcomes/outcomes.jsonl`        | Outcome records              |
| `DIST_EVENTS_LOG`    | `$OBS_DIR/distribution_events.jsonl`            | Distribution events          |
| `ANALYTICS_DIR`      | `/opt/binarybot/analytics`                      | Analytics output directory   |

### Input Population

- **Outcome records**: all records in `outcomes.jsonl` with valid `signal_id` and `outcome in {WIN, LOSE, MISSED}`.
- **Exclusions**: records missing `signal_id`, records with unknown outcome values, malformed JSON lines.
- **Deduplication**: one record per `(signal_id, user_id)` pair; subsequent duplicates are skipped.

### Metric Definitions

#### Outcome Counts (wins / loses / missed)

- **Input population**: deduplicated valid outcome records
- **Denominator**: count of deduplicated valid records per outcome type
- **Missing outcomes**: no fabrication; counted as part of `total` only if outcome is valid
- **Duplicates**: excluded via `(signal_id, user_id)` dedup key
- **Partial/failed distribution**: not factored into outcome counts (separate distribution metrics)
- **Invalid records**: excluded; reported in `invalid_count`

#### win_rate

- **Input population**: deduplicated valid outcome records
- **Denominator**: `total = wins + loses + missed`
- **Insufficient sample**: if `total < _MIN_SAMPLE_FOR_RATE (5)`, `win_rate=None`, `insufficient_sample=True`
- **Empty data**: `win_rate=None`, `no_data=True`

#### signals_tracked

- **Input population**: all valid outcome records with known signal_id and valid outcome
- **Count**: distinct signal_ids

#### Distribution Metrics (from distribution_events.jsonl)

Counted separately per `data.publish_result` enum value:
- `PUBLISHED`
- `FAILED`
- `SKIPPED_SILENT`
- `SKIPPED_LIMIT`
- `SKIPPED_DISABLED`
- `DUPLICATE_SUPPRESSED`

### Output Contract (aggregates.json)

```json
{
  "updated_ts": <int epoch seconds>,
  "no_data": <bool>,
  "wins": <int>,
  "loses": <int>,
  "missed": <int>,
  "total_votes": <int>,
  "win_rate": <float | null>,
  "insufficient_sample": <bool>,
  "signals_tracked": <int>,
  "invalid_outcome_records": <int>,
  "distribution": {
    "no_data": <bool>,
    "PUBLISHED": <int>,
    "FAILED": <int>,
    "SKIPPED_SILENT": <int>,
    "SKIPPED_LIMIT": <int>,
    "SKIPPED_DISABLED": <int>,
    "DUPLICATE_SUPPRESSED": <int>,
    "total_distribution_events": <int>,
    "invalid_count": <int>
  }
}
```

### Persistence

- Written via `storage.save_json_atomic()` (tmpfile + fsync + os.replace)
- Failed write preserves the last valid `aggregates.json`
- Analytics does not mutate live trading state, strategy parameters, or config

### Invariants

1. Malformed JSON is never silently converted to `{}` or counted as a valid record.
2. One malformed line does not invalidate the entire file; each line is isolated.
3. Duplicate `(signal_id, user_id)` pairs cannot inflate metrics.
4. Empty input yields `no_data=True`, zero counts, `win_rate=None`.
5. Repeated calls on the same input produce identical output (excluding `updated_ts`).
6. No network calls, live services, or parameter mutations occur during analysis.
