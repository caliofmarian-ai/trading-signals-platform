# DEAD_AND_UNREACHABLE_CODE_REGISTER

| Item | Type | Evidence | Confidence | Notes |
|---|---|---|---|---|
| `send/core/strategy_v2 - Copy.py` | Dead duplicate module | `cmp -s` returned identical; file count and direct compare confirm byte-for-byte duplicate of `strategy_v2.py` | High | Known item; no distinct callers |
| `send/core/bot_service.py` branch `from core import outcome_tracker` | Unreachable/broken branch | `bot_service.py:331-337`; no `core/outcome_tracker.py` exists | High | Only reachable for `VOTE_` format outside current `VOTE_|...` path |
| `send/legacy/bot_control.py` | Orphan legacy module | No callers found; separate Telegram stack; import-check fails on missing `dotenv` | High | Divergent state schema and Romanian UI text |
| `send/tools/strategy_auditor_daily.py` | Operational script with broken import | `strategy_auditor_daily.py:4-9`; import-check failed `No module named 'strategy_auditor_lib'` | High | Not runnable as package module |
| `send/config/admin_permissions.json` | Dead config artifact | No runtime readers; `admin_permissions.py` uses hardcoded matrix | High | Operator-editable but ineffective |
| `send/state/event_store.json` | Dead state artifact | File is `[]`; active event store writes JSONL elsewhere (`state_store/event_store.py:17-20`) | Medium | Confusing stale artifact |
| `send/state/state_store.json` | Dead config/state artifact | Holds channel/limits/admin schema, but active router reads `config/channel_config.json`/env instead | Medium | Overlapping truth source |
| `send/validation/statistical_proof.py` | Empty/placeholder module | Filesystem audit reported 0 lines/0 bytes | High | Canonical proof layer absent |
| `send/monitoring/health_check.py` | Practically unreachable utility | No callers found by repo search | Medium | Health file never written unless invoked manually |
| `send/metrics/aggregates_writer.py` | Orphan utility | No callers found by repo search | Medium | Writes metrics snapshots/history only if scheduled externally |
| `send/state_store/*` facade | Stale compatibility path | No active runtime callers found; schema/path drift from `core/*` modules | Medium | Should be consolidated or archived |
| `send/snapshots/snapshot_manager.py` | Orphan utility | No callers found | Medium | Useful operationally but currently unattached |
| `signal_engine.update_symbol_replacement_score()` | Broken runtime helper | `signal_engine.py:4-41` imports absent `core.scan_scheduler`; exceptions swallowed | High | Silent no-op path |
