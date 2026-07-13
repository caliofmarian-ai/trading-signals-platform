# BATCH_09_CALLER_REFERENCE_ANALYSIS

## Methodology
For each deletion candidate, a repository-wide search was performed across:
- Python import statements (`import X`, `from X import`)
- Module attribute access (string grep for module name)
- String path references (file path strings)
- Test references
- Documentation references
- Dynamic imports, subprocess calls, plugin loading

Search tool: `grep -rn` across `send/` and `tests/` (excluding `_archive/` and `__pycache__/`)

---

## send/legacy/bot_control.py
- **Import search**: `grep -rn "bot_control|from legacy|import legacy"` → zero results outside file itself
- **String path search**: `grep -rn "bot_control"` → zero results in tests or send/
- **Runtime entry point**: No setup.py/pyproject.toml entry point
- **Test references**: None
- **Dynamic import**: None
- **Verdict**: ORPHAN — no callers of any type

## send/core/strategy_v2 - Copy.py
- **Import search**: `grep -rn "strategy_v2.*Copy|Copy.*strategy"` → zero results
- **`diff` check**: `diff "strategy_v2 - Copy.py" strategy_v2.py` → identical (exit 0)
- **Callers of strategy_v2**: `send/core/signal_engine.py` (imports `strategy_v2`)
- **Verdict**: DUPLICATE — byte-for-byte copy; all callers use `strategy_v2.py`

## send/state/event_store.json
- **Content**: `[]` — empty JSON array
- **Readers**: `grep -rn "event_store.json"` → zero results in runtime code
- **Active event store**: `core/observability_logger.py` writes JSONL to `observability/engine_events.jsonl`
- **Verdict**: DEAD — empty artifact, no runtime reader

## send/state/state_store.json
- **Content**: old channel/limits/admin schema (schema_version 1.0.0)
- **Readers**: `grep -rn "state_store.json"` → zero results in runtime code
- **Active config**: `distribution_router.py` reads `config/channel_config.json` + env vars
- **Verdict**: DEAD — superseded by channel_config.json; no reader

## send/config/admin_permissions.json
- **Runtime readers**: `admin_permissions.py` uses a hardcoded permission matrix; never reads this file
- **grep**: `grep -rn "admin_permissions.json"` in runtime code → only `PERMISSIONS_CONFIG` env var reference in `admin_permissions.py` but that var is not used to load the file at runtime
- **TEST dependency**: `tests/canonical/conftest.py:50` — fixture copies the file to test runtime root; `tests/batch_01/test_boot_and_import_stabilization.py` verifies it exists as a supported config file
- **RECLASSIFICATION**: TEST_ONLY — required by test fixture and batch_01 test; not by live runtime
- **Action**: PRESERVED (reclassified to TEST_ONLY; NOT deleted)

## send/validation/statistical_proof.py
- **Content**: 0 bytes — empty file
- **Import search**: `grep -rn "statistical_proof|from validation|import validation"` → single comment in `alerts/alert_engine.py:1` (a file-header comment referencing the old path, not an import)
- **Test references**: None
- **Verdict**: DEAD — empty placeholder; no callers

## send/validation/__init__.py
- **Content**: 0 bytes
- **Import search**: no callers to `validation` package
- **Verdict**: DEAD — empty package init for dead module

## send/monitoring/health_check.py
- **Import search**: `grep -rn "health_check|from monitoring"` → zero results outside `runtime/system_boot.py:66` which imports from `monitoring.restart_guard` (NOT health_check)
- **Test references**: None
- **Verdict**: ORPHAN (GAP-020) — no active callers; reads from orphan metrics_collector

## send/metrics/metrics_collector.py
- **Import search**: `grep -rn "metrics_collector|from metrics|import metrics"` → only `monitoring/health_check.py` (itself orphan)
- **Test references**: None
- **Verdict**: ORPHAN (GAP-020) — only caller is health_check.py which is also orphan

## send/metrics/aggregates_writer.py
- **Import search**: `grep -rn "aggregates_writer|from metrics"` → zero results
- **Test references**: None
- **Verdict**: ORPHAN — no callers of any type

## send/metrics/__init__.py
- **Content**: empty (package init only for deleted modules)
- **Verdict**: DEAD — no package members remaining

## send/journal/trade_journal.py
- **Import search**: `grep -rn "trade_journal|from journal|import journal"` → zero results in send/ or tests/
- **Test references**: None
- **Verdict**: ORPHAN — no callers; hardcoded `/opt/binarybot/journal/` paths

## send/journal/__init__.py
- **Content**: 0 bytes
- **Verdict**: DEAD — package init for orphan module only

## send/journal/boot.log
- **Type**: Generated log file
- **Verdict**: COMMITTED ARTIFACT — should not be version-controlled

## send/engine.log
- **Type**: Generated runtime log file
- **Verdict**: COMMITTED ARTIFACT — should not be version-controlled

## send/tmp_decision_audit_patch_input.txt + send/tmp_decision_chunk_00..05
- **Type**: Temporary working files from remediation decision audit
- **Verdict**: COMMITTED ARTIFACT — should not be version-controlled

## send(2).zip
- **Type**: 25 MB zip archive of send/ directory
- **Verdict**: COMMITTED ARTIFACT — development artifact; should not be version-controlled

## send/state_store/event_store.py
- **Import search**: `grep -rn "event_store" --include="*.py"` → zero results outside the file itself
- **Package import**: `send/state_store/__init__.py` is empty; does not re-export event_store
- **Functional overlap**: `core/observability_logger.py` provides canonical observability writes (events, errors, warnings, proofs)
- **Test references**: None
- **Verdict**: ORPHAN — parallel observability facade; superseded by core/observability_logger.py; no callers

## send/core/outcome_service.py (path convergence — NOT deleted)
- **OUTCOMES_JSONL**: referenced by outcome_service internally; patched in 6 test files via `monkeypatch.setattr(outcome_service, "OUTCOMES_JSONL", ...)`
- **OPEN_REGISTRY_JSON**: same pattern
- **OUTCOMES_INDEX_JSON**: same pattern
- **Action**: Replace hardcoded strings with `storage.root_path("outcomes", name)` — tests continue to monkeypatch after import

## send/core/admin_commands.py (path convergence — NOT deleted)
- **CONFIG_DIR**: derived constants ACTIVE_SYMBOLS_PATH, ADMIN_SETTINGS_PATH, ALGO_PARAMS_PATH
- **OBS_DIR**: derived constants ADMIN_EVENTS_PATH, ADMIN_PROOFS_PATH, ENGINE_EVENTS_PATH
- **REPORTS_DIR**: used by _find_latest_report_json()
- **Test monkeypatching**: `ADMIN_EVENTS_PATH` and `ADMIN_PROOFS_PATH` patched in batch_05 tests via `monkeypatch.setattr(ac, "...", str(path))`
- **Action**: Replace with `_storage.root_path()` — tests continue to monkeypatch specific constants after import

## send/tools/strategy_auditor_lib.py (datetime fix — NOT deleted)
- **datetime.utcnow()**: Line 387; 6 DeprecationWarnings per suite run
- **Replacement**: `datetime.datetime.now(datetime.UTC)` — semantically identical; returns UTC datetime
- **Serialization**: `.strftime("%Y-%m-%d")` — identical output format, no serialization change
