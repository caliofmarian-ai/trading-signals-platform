# BATCH_07_FLOW_BEFORE

## Before-State End-to-End Flow Map

### Canonical Pipeline (pre-BATCH-07)

```
canonical runtime records
    │
    ├─ outcomes.jsonl          (outcome_service, BATCH-04)
    ├─ engine_events.jsonl     (observability_logger, BATCH-03)
    ├─ distribution_events.jsonl (observability_logger, BATCH-03)
    ├─ fsm_events.jsonl        (observability_logger, BATCH-06)
    └─ error_events.jsonl      (observability_logger, BATCH-03)
         │
         ▼
    loading/parsing
    ┌──────────────────────────────────────────────────────────────┐
    │ analytics_engine._safe_json_loads()   → silently returns {}  │
    │   on any malformed JSON (silent data loss — PROHIBITED)       │
    │                                                              │
    │ research_engine._safe_json_loads()    → same silent failure  │
    │                                                              │
    │ strategy_auditor_lib._read_jsonl()    → silently skips bad   │
    │   lines with bare except: continue                           │
    └──────────────────────────────────────────────────────────────┘
         │
         ▼
    normalization (BROKEN)
    ┌──────────────────────────────────────────────────────────────┐
    │ research_engine reads rec.get("data", {}).get("stage")       │
    │   → always None because stage is a top-level correlation     │
    │   field in canonical events, not inside data{}               │
    │   → signal funnel always shows PRE=0, CONFIRM=0, OPEN_NOW=0  │
    │   even with valid input                                       │
    └──────────────────────────────────────────────────────────────┘
         │
         ▼
    aggregation
    ┌──────────────────────────────────────────────────────────────┐
    │ analytics_engine: no deduplication by (signal_id, user_id)   │
    │   → duplicate outcome votes inflate WIN/LOSE/MISSED counts   │
    │                                                              │
    │ analytics_engine: None key created in signals{} when         │
    │   signal_id is missing from a record                         │
    │                                                              │
    │ No distribution metrics (PUBLISHED/FAILED/SKIPPED/etc.)      │
    └──────────────────────────────────────────────────────────────┘
         │
         ▼
    metric computation
    ┌──────────────────────────────────────────────────────────────┐
    │ win_rate=0 when no data (should be explicit no_data flag)     │
    │ No insufficient-sample reporting                             │
    │ No invalid_records count exposed                             │
    └──────────────────────────────────────────────────────────────┘
         │
         ▼
    research interpretation (BROKEN)
    ┌──────────────────────────────────────────────────────────────┐
    │ research_engine returns flat dict with no advisory structure  │
    │ No observations / hypotheses / recommendations separation     │
    │ No advisory_only / auto_apply flags                          │
    └──────────────────────────────────────────────────────────────┘
         │
         ▼
    report generation
    ┌──────────────────────────────────────────────────────────────┐
    │ strategy_auditor_daily: from strategy_auditor_lib import …   │
    │   → ModuleNotFoundError (GAP-015 — tool entirely unusable)   │
    │                                                              │
    │ strategy_auditor_lib: SETTINGS_PATH="/opt/binarybot/…"       │
    │   → hard-requires /opt/binarybot/ on every host              │
    │                                                              │
    │ strategy_auditor_lib.write_reports: non-atomic file writes   │
    │   → partial overwrite possible on crash                      │
    └──────────────────────────────────────────────────────────────┘
         │
         ▼
    persistence
    ┌──────────────────────────────────────────────────────────────┐
    │ analytics_engine: storage.save_json_atomic OK                │
    │ research_engine: no persistence at all                       │
    │ strategy_auditor_lib: direct open()+write (non-atomic)       │
    └──────────────────────────────────────────────────────────────┘
         │
         ▼
    downstream consumer
        analytics reports, research reports, daily audit outputs
```

### Path Hard-Coding Problems

All analytics/research/audit modules used hard-coded `/opt/binarybot/` prefixes:

| Module                  | Hard-coded path                                      |
|-------------------------|------------------------------------------------------|
| analytics_engine.py     | `/opt/binarybot/observability`, `/opt/binarybot/outcomes`, `/opt/binarybot/analytics` |
| research_engine.py      | `/opt/binarybot/observability`, `/opt/binarybot/outcomes` |
| strategy_auditor_lib.py | `/opt/binarybot/config/intelligence_settings.json`   |
| report_loader.py        | `/opt/binarybot/analytics/reports`                   |

These differ from `observability_logger.py` which already used env-var overrides (`OBS_DIR`, `ENGINE_EVENTS_LOG`, etc.) established by BATCH-03/04.
