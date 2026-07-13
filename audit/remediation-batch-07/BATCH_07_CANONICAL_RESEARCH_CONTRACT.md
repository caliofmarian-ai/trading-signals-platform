# BATCH_07_CANONICAL_RESEARCH_CONTRACT

## Research Engine — Canonical Contract

### Module: `send/intelligence/research_engine.py`

### Path Resolution

Same env-var pattern as analytics_engine:

| Variable             | Default                                         |
|----------------------|-------------------------------------------------|
| `OBS_DIR`            | `/opt/binarybot/observability`                  |
| `ENGINE_EVENTS_LOG`  | `$OBS_DIR/engine_events.jsonl`                  |
| `DIST_EVENTS_LOG`    | `$OBS_DIR/distribution_events.jsonl`            |
| `OUTCOMES_LOG`       | `/opt/binarybot/outcomes/outcomes.jsonl`        |
| `ANALYTICS_DIR`      | `/opt/binarybot/analytics`                      |

### Signal Funnel (compute_signal_funnel)

- Reads `engine_events.jsonl`; filters for `event_type == "signal_event"`
- **`stage` is read from the top-level correlation field** (`rec.get("stage")`), NOT `rec.get("data", {}).get("stage")`
  - This is the canonical location after `observability_logger._normalize_event()` processing
- Counts: `PRE`, `CONFIRM`, `OPEN_NOW`
- Unknown stage values → classified in `unsupported_stages` dict (never silently coerced)
- Missing stage → excluded, `invalid_count++`
- Dedup by `event_id` where present

### Outcome Stats (compute_outcome_stats)

- Same dedup and validity rules as analytics_engine
- `no_data=True` when no valid records exist
- `win_rate=None` when `no_data=True`

### Distribution Summary (compute_distribution_summary)

- Counts all `tier_publish` events by `data.publish_result`
- Unknown results → `invalid_count++`

### Research Report Output Contract (build_research_report)

```json
{
  "signal_funnel": { ... },
  "outcomes": { ... },
  "distribution": { ... },
  "research": {
    "observations": ["..."],
    "hypotheses": ["..."],
    "recommendations": ["[ADVISORY] ..."],
    "limitations": ["..."],
    "validation_status": "UNVALIDATED",
    "confidence": "LOW | MEDIUM",
    "advisory_only": true,
    "auto_apply": false
  }
}
```

### Advisory Rules

1. `advisory_only` is always `true`.
2. `auto_apply` is always `false`.
3. All recommendations are prefixed `[ADVISORY]` and require operator review.
4. Research output does not change live parameters, promote strategies, or modify deployment state.
5. `insufficient_sample` data produces explicit `limitations` entries, not fabricated findings.
6. `validation_status` starts as `"UNVALIDATED"` until a human validates the findings.

### Persistence (persist_research_report)

- Optional: call `persist_research_report(report)` to write atomically via `storage.save_json_atomic()`
- `build_research_report()` alone does not write any files
- Failed write preserves the last valid `research_report.json`

### Invariants

1. `stage` is always read from the top-level of the canonical event record.
2. Malformed lines are excluded and counted.
3. Duplicate event_ids in engine log are deduplicated.
4. Duplicate (signal_id, user_id) in outcomes are deduplicated.
5. Repeated calls on identical input are deterministic.
6. No live-service calls, no parameter mutations.
