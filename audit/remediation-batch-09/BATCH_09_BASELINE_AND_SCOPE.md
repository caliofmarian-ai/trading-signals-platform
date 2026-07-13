# BATCH_09_BASELINE_AND_SCOPE

## Owner Approval
Owner explicitly approved BATCH-09. Authorization covers:
- Controlled cleanup, deletion, archival, or reclassification of legacy/orphan/dead files proven safe by repository evidence.
- Correction of residual hardcoded `/opt/binarybot/...` runtime paths in `core/outcome_service.py` and `core/admin_commands.py`.
- Behavior-preserving fix of the `datetime.utcnow()` deprecation warning.

Authorization does NOT cover: product-feature expansion, new trading strategies, broker/Pocket Option/Railway integration, paper/live trading, broad canonical redesign, or deletion based only on filename/directory/age/suspicion.

## Prior Batches Confirmed Present
- BATCH-01: `audit/remediation-batch-01/` ✓
- BATCH-02: `audit/remediation-batch-02/` ✓
- BATCH-03: `audit/remediation-batch-03/` ✓
- BATCH-04: `audit/remediation-batch-04/` ✓
- BATCH-05: `audit/remediation-batch-05/` ✓
- BATCH-06: `audit/remediation-batch-06/` ✓
- BATCH-07: `audit/remediation-batch-07/` ✓
- BATCH-08: `audit/remediation-batch-08/` ✓

## Baseline Test Result (Pre-Cleanup)
- Suite: complete offline suite (`tests/`)
- Command: `PYTHONPATH=send python3 -m pytest tests/ -q`
- Total: **230 passed, 0 skipped, 0 xfailed, 6 warnings**
- Warnings: all are `DeprecationWarning: datetime.datetime.utcnow()` from `send/tools/strategy_auditor_lib.py:387`
- Result: matches BATCH-08 expected baseline exactly

## Open Findings from BATCH-08 Addressed in BATCH-09
| Finding | Source | Action |
|---------|--------|--------|
| OF-08-001 | TEST_PLAN truncation | Re-inspected; documented in BATCH_09_TEST_PLAN_TRUNCATION_ANALYSIS.md |
| OF-08-002 | Hardcoded outcomes paths in outcome_service.py | Converged via storage.root_path() |
| OF-08-003 | Hardcoded config/obs constants in admin_commands.py | Converged via _storage.root_path() |
| OF-08-004 | datetime.utcnow() deprecation in strategy_auditor_lib.py | Fixed with datetime.now(datetime.UTC) |

## GAP Closures
- **GAP-016**: Legacy bot cleanup — `send/legacy/bot_control.py` deleted (no callers, missing dotenv dep, divergent control surface)
- **GAP-020**: Health/metrics path inert — `send/monitoring/health_check.py`, `send/metrics/metrics_collector.py`, `send/metrics/aggregates_writer.py` deleted (no active runtime callers)

## Scope of BATCH-09
Primary domains inspected:
- `legacy/` — single orphan file: `bot_control.py`
- `metrics/` — fully orphaned: `metrics_collector.py`, `aggregates_writer.py`, `__init__.py`
- `journal/` — fully orphaned: `trade_journal.py`, `__init__.py`, committed log `boot.log`
- `state_store/` — `event_store.py` orphaned; `state_store.py` ACTIVE (preserved)
- `snapshots/` — `snapshot_manager.py` ACTIVE (imported by system_boot + tests)
- Config files — `admin_permissions.json` dead
- State artifacts — `state/event_store.json`, `state/state_store.json` dead
- Runtime artifacts — `engine.log`, `tmp_decision_*`, `send(2).zip`
- Duplicate code — `core/strategy_v2 - Copy.py` byte-for-byte duplicate
- Dead placeholder — `validation/statistical_proof.py` (0 bytes)
- Hardcoded paths — `outcome_service.py`, `admin_commands.py`
- Datetime warning — `tools/strategy_auditor_lib.py`
