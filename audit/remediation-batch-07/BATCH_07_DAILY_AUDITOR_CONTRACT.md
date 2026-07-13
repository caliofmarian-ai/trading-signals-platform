# BATCH_07_DAILY_AUDITOR_CONTRACT

## Daily Strategy Auditor — Canonical Contract

### Modules

- `send/tools/__init__.py` (new — makes `tools` a proper Python package)
- `send/tools/strategy_auditor_lib.py`
- `send/tools/strategy_auditor_daily.py`

### Path Resolution (GAP-015 fix)

**Before BATCH-07**: `strategy_auditor_daily.py` imported `from strategy_auditor_lib import ...` which failed with `ModuleNotFoundError: No module named 'strategy_auditor_lib'` when the module was loaded as `tools.strategy_auditor_daily`.

**After BATCH-07**: Import changed to `from tools.strategy_auditor_lib import ...`. A `tools/__init__.py` was created to register the package.

### Settings Path Resolution

**Before**: `SETTINGS_PATH = "/opt/binarybot/config/intelligence_settings.json"` — hard-coded, fails on any non-production host.

**After**: Resolved by priority:
1. Explicit `path` argument to `load_settings(path=...)`
2. `STRATEGY_AUDITOR_SETTINGS` environment variable
3. Project-relative default: `<package_root>/config/intelligence_settings.json`

### Input Event Loading

`load_all_events(settings)` returns:
```python
{
    "engine": [valid_records],
    "fsm": [valid_records],
    "distribution": [valid_records],
    "errors": [valid_records],
    "outcomes": [valid_records],
    "invalid_counts": {
        "engine": <int>,
        "fsm": <int>,
        "distribution": <int>,
        "errors": <int>,
        "outcomes": <int>,
    }
}
```

Invalid JSON lines are counted and reported; they are not silently dropped.

### Report Output Contract

`build_report(events, settings)` produces:
```json
{
  "date": "YYYY-MM-DD",
  "input_sources": {
    "engine_events": {"valid": <int>, "invalid": <int>},
    "fsm_events": {"valid": <int>, "invalid": <int>},
    "distribution_events": {"valid": <int>, "invalid": <int>},
    "error_events": {"valid": <int>, "invalid": <int>},
    "outcomes": {"valid": <int>, "invalid": <int>}
  },
  "decisions": <int>,
  "pre": <int>,
  "confirm": <int>,
  "open_now": <int>,
  "rejects": <int>,
  "avg_score": <float | null>,
  "min_score": <float | null>,
  "max_score": <float | null>,
  "top_reject_reasons": { ... },
  "symbol_activity": { ... },
  "heatmap": { ... },
  "bottleneck": { ... },
  "symbol_health": { ... },
  "limitations": ["..."]
}
```

### Report Persistence

`write_reports(report, settings)` writes atomically:
- JSON: tmpfile + os.fsync + os.replace → no partial overwrite possible
- Markdown: same atomic pattern
- Failed write preserves last valid report on disk

### Invariants

1. Auditor imports without `ModuleNotFoundError` (GAP-015 resolved).
2. No `/opt/binarybot/` path is hard-required; any path can be configured.
3. Missing settings file raises `RuntimeError` with a clear message.
4. Source JSONL files are read-only; auditor does not write to them.
5. Invalid JSONL lines are counted, not silently skipped.
6. Auditor does not mutate live strategy parameters, config, or runtime state.
7. Report identifies: input sources, period analyzed, valid/invalid record counts, findings, limitations.
