# BATCH_07_IMPLEMENTATION_REPORT

## Findings Addressed

| Finding | Description | Status |
|---------|-------------|--------|
| GAP-010 | Analytics/research readers call undefined `safe_json_loads` | RESOLVED |
| GAP-015 | `strategy_auditor_daily.py` package import broken | RESOLVED |

## Root Causes Fixed

### GAP-010

1. **Silent data loss via `_safe_json_loads`**: Both `analytics_engine.py` and `research_engine.py` defined a local `_safe_json_loads()` that returned `{}` for any malformed JSON. This constitutes silent data loss (prohibited by canonical rules).

2. **Wrong field access for `stage`**: `research_engine.py` read `rec.get("data", {}).get("stage")` but `stage` is a top-level correlation field in canonical events (after `observability_logger._normalize_event()` wrapping). This caused the signal funnel to always report 0 for all stages.

3. **No deduplication**: `analytics_engine.py` allowed the same `(signal_id, user_id)` outcome to be counted multiple times, inflating metrics.

4. **No invalid record reporting**: Errors were silently absorbed with no count surfaced.

5. **No distribution metrics**: No parsing of `tier_publish` events.

6. **Hardcoded `/opt/binarybot/` paths**: All four modules used hardcoded paths not overridable by env vars, unlike `observability_logger.py` which already had env-var overrides.

7. **No no-data/insufficient-sample reporting**: When inputs were empty, `win_rate=0` was reported (fabricated) instead of `no_data=True`.

### GAP-015

1. **Broken import**: `strategy_auditor_daily.py` used `from strategy_auditor_lib import ...` which fails when loaded as `tools.strategy_auditor_daily` because `strategy_auditor_lib` is not a top-level module.

2. **No `tools/__init__.py`**: The `tools/` directory was not a Python package.

## Implementation Changes

### Created: `send/core/jsonl_parser.py`

New canonical shared JSONL parsing helper:
- `ParseError` typed exception with `source_path`, `line_number`, `raw` fields
- `parse_json_line(line, *, source_path, line_number)` — raises ParseError for malformed input; never returns `{}`
- `iter_jsonl(path)` — yields `(record, None)` or `(None, ParseError)` per line; record-level isolation; raises `FileNotFoundError` for missing files

### Modified: `send/core/analytics_engine.py`

- Removed local `_safe_json_loads()` (silent failure helper)
- Replaced with `core.jsonl_parser.iter_jsonl()` for explicit error surfacing
- Replaced hardcoded `/opt/binarybot/` paths with env-var-based resolution (`OBS_DIR`, `OUTCOMES_LOG`, `DIST_EVENTS_LOG`, `ANALYTICS_DIR`)
- Added `_load_outcomes()`: deduplication by `(signal_id, user_id)`, invalid_count reporting, no_data detection, insufficient_sample flag
- Added `_load_distribution_metrics()`: parses `tier_publish` events, counts all 6 result types separately
- Updated `recompute()`: exposes distribution metrics, invalid_count, no_data flag; preserves atomic write via `storage.save_json_atomic()`
- Updated `get_user_stats()`: added dedup, invalid_count, no_data flag

### Modified: `send/intelligence/research_engine.py`

- Removed local `_safe_json_loads()` (silent failure helper)
- Replaced with `core.jsonl_parser.iter_jsonl()`
- Replaced hardcoded paths with env-var-based resolution
- **Fixed critical bug**: `stage` now read from `rec.get("stage")` (top-level), NOT `rec.get("data", {}).get("stage")`
- Added `_classify_stage()`: explicitly classifies unknown stage values
- Added dedup by `event_id` in signal funnel
- Added dedup by `(signal_id, user_id)` in outcome stats
- Added `compute_distribution_summary()`: new function for distribution metrics
- Restructured `build_research_report()`: now produces advisory-structured output with `observations`, `hypotheses`, `recommendations`, `limitations`, `advisory_only=True`, `auto_apply=False`
- Added `persist_research_report()`: atomic persistence via `storage.save_json_atomic()`

### Created: `send/tools/__init__.py`

Empty file registering `tools/` as a Python package (required for GAP-015).

### Modified: `send/tools/strategy_auditor_daily.py`

- Changed `from strategy_auditor_lib import ...` → `from tools.strategy_auditor_lib import ...`

### Modified: `send/tools/strategy_auditor_lib.py`

- Replaced `SETTINGS_PATH = "/opt/binarybot/..."` with env-var-based resolution (`STRATEGY_AUDITOR_SETTINGS`)
- `load_settings()` now accepts optional `path` argument; raises `RuntimeError` with clear path message on missing file
- `_read_jsonl()` now returns `(records, invalid_count)` tuple — invalid lines counted, not silently dropped
- `load_all_events()` returns `invalid_counts` dict alongside event collections
- `build_report()` includes `input_sources` with valid/invalid counts per source; adds `limitations` field
- `write_reports()` now writes atomically (tmpfile + os.fsync + os.replace); no partial overwrite possible
- Added type annotations

### Modified: `send/intelligence/report_loader.py`

- Replaced `REPORTS_DIR = "/opt/binarybot/analytics/reports"` with env-var-based resolution via `ANALYTICS_DIR`

## Tests Created

File: `tests/batch_07/test_analytics_research_toolchain.py`

52 tests covering:
- Module imports (4 tests)
- Parsing and input normalization (15 tests)
- Analytics metrics (11 tests)
- Research engine (8 tests)
- Daily auditor (8 tests)
- GAP-010/GAP-015 specific regression (3 tests)
- Stage field correctness (2 tests)
- Path override (1 test)

## Commands Executed

```bash
# Verify all imports
PYTHONPATH=send python -c "
import core.jsonl_parser; import core.analytics_engine
import intelligence.research_engine; import tools.strategy_auditor_lib
import tools.strategy_auditor_daily; import intelligence.report_loader
print('All imports OK')
"

# BATCH-07 tests
PYTHONPATH=send python -m pytest tests/batch_07/ -v

# Full regression
PYTHONPATH=send python -m pytest tests/ -q
```

## Test Results

| Suite | Tests | Passed | Failed |
|-------|-------|--------|--------|
| BATCH-07 | 52 | 52 | 0 |
| Full (all batches) | 205 | 205 | 0 |

## Preserved Contracts

- BATCH-02: parameter contract (params_loader) — unchanged
- BATCH-03: event/distribution schema and logging (observability_logger, distribution_router) — unchanged
- BATCH-04: telemetry/outcome authority (outcome_service, trade_temporal_telemetry) — unchanged
- BATCH-05: Admin/control-plane (admin_commands, admin_permissions) — unchanged
- BATCH-06: segmented-state, FSM, restart recovery (fsm_runtime, state_store, snapshot_manager) — unchanged
