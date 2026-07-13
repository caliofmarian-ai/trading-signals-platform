# BATCH_09_CANDIDATE_INVENTORY

## 1. legacy/ Directory
| File | Size | Import check | Notes |
|------|------|-------------|-------|
| `send/legacy/bot_control.py` | 8.3 KB | FAIL — missing `python-telegram-bot`, `dotenv` | Separate Telegram stack; Romanian UI text; divergent path schema |

## 2. metrics/ Directory
| File | Size | Callers | Notes |
|------|------|---------|-------|
| `send/metrics/metrics_collector.py` | ~1 KB | `monitoring/health_check.py` only (itself orphan) | In-memory counter; not wired to runtime |
| `send/metrics/aggregates_writer.py` | ~1 KB | None | Writes metrics snapshots; never scheduled |
| `send/metrics/__init__.py` | 0 bytes | — | Empty package init |

## 3. journal/ Directory
| File | Size | Callers | Notes |
|------|------|---------|-------|
| `send/journal/trade_journal.py` | ~2 KB | None | Hardcoded `/opt/binarybot/journal/`; no active callers |
| `send/journal/__init__.py` | 0 bytes | — | Empty package init |
| `send/journal/boot.log` | varies | — | Generated log artifact committed to repo |

## 4. state_store/ Directory
| File | Status | Callers | Notes |
|------|--------|---------|-------|
| `send/state_store/state_store.py` | ACTIVE | `core/fsm_runtime.py`, `core/distribution_router.py`, `core/signal_engine.py`, `snapshots/snapshot_manager.py`, `monitoring/restart_guard.py` | Canonical state store — DO NOT DELETE |
| `send/state_store/__init__.py` | ACTIVE | (package) | — |
| `send/state_store/event_store.py` | ORPHAN | None found | Parallel observability facade; superseded by `core/observability_logger.py` |

## 5. snapshots/ Directory
| File | Status | Callers | Notes |
|------|--------|---------|-------|
| `send/snapshots/snapshot_manager.py` | ACTIVE | `runtime/system_boot.py`, `tests/batch_06/`, `tests/canonical/persistence/` | PRESERVE |
| `send/snapshots/__init__.py` | ACTIVE | (package) | PRESERVE |

## 6. monitoring/ Directory
| File | Status | Callers | Notes |
|------|--------|---------|-------|
| `send/monitoring/restart_guard.py` | ACTIVE | `runtime/system_boot.py`, tests | PRESERVE |
| `send/monitoring/health_check.py` | ORPHAN | None | No runtime/test callers; reads from orphan metrics_collector |

## 7. Configuration Files
| File | Status | Runtime reader | Notes |
|------|--------|---------------|-------|
| `send/config/admin_permissions.json` | DEAD | None | `admin_permissions.py` uses hardcoded matrix; file never loaded |
| `send/config/algo_params.json` | ACTIVE | `params_loader.py`, `admin_commands.py` | PRESERVE |
| `send/config/channel_config.json` | ACTIVE | `distribution_router.py` | PRESERVE |
| `send/config/admin_roles.json` | ACTIVE | `admin_permissions.py` | PRESERVE |
| `send/config/admin_settings.json` | ACTIVE | `admin_commands.py` (engine_tick_interval) | PRESERVE |
| `send/config/active_symbols.json` | ACTIVE | `signal_engine.py`, `admin_commands.py` | PRESERVE |

## 8. State Artifacts
| File | Status | Notes |
|------|--------|-------|
| `send/state/event_store.json` | DEAD | Content: `[]` — empty array; active event store writes JSONL via observability_logger |
| `send/state/state_store.json` | DEAD | Old channel/limits schema; active router reads `config/channel_config.json`/env |
| `send/state/focus_state.json` | ACTIVE | Read/written by `state_store/state_store.py` | PRESERVE |
| `send/state/dist_state.json` | ACTIVE | Read/written by `state_store/state_store.py` | PRESERVE |
| `send/state/restart_guard.json` | ACTIVE | Read/written via `monitoring/restart_guard.py` | PRESERVE |

## 9. Duplicate Implementations
| File | Authoritative replacement | Evidence |
|------|--------------------------|----------|
| `send/core/strategy_v2 - Copy.py` | `send/core/strategy_v2.py` | `diff` returned identical; byte-for-byte copy; no callers |

## 10. Dead Placeholders
| File | Size | Notes |
|------|------|-------|
| `send/validation/statistical_proof.py` | 0 bytes | Never implemented; no callers |
| `send/validation/__init__.py` | 0 bytes | Empty package init for dead module |

## 11. Committed Runtime Artifacts
| File | Type | Notes |
|------|------|-------|
| `send/engine.log` | Runtime log | Generated; should not be version-controlled |
| `send/journal/boot.log` | Runtime log | Generated; should not be version-controlled |
| `send/tmp_decision_audit_patch_input.txt` | Temp working file | Remediation working artifact |
| `send/tmp_decision_chunk_00..05` | Temp working files | Remediation working artifacts (6 files) |
| `send(2).zip` | Development archive | 25 MB zip of send/ directory; not needed |

## 12. Hardcoded Path Targets
| File | Constants | Action |
|------|-----------|--------|
| `send/core/outcome_service.py` | `OUTCOMES_JSONL`, `OPEN_REGISTRY_JSON`, `OUTCOMES_INDEX_JSON` | Replace with `storage.root_path()` |
| `send/core/admin_commands.py` | `CONFIG_DIR`, `OBS_DIR`, `REPORTS_DIR` and derived constants | Replace with `_storage.root_path()` |

## 13. Datetime Warning Target
| File | Location | Fix |
|------|----------|-----|
| `send/tools/strategy_auditor_lib.py` | Line 387 | Replace `datetime.datetime.utcnow()` with `datetime.datetime.now(datetime.UTC)` |

## 14. Preserved (ACTIVE / GOVERNANCE / HISTORICAL)
- All `audit/` documents
- `send/_archive/` (governance backups)
- `send/core/storage.py`, `send/core/observability_logger.py`, all active core modules
- `send/state_store/state_store.py`, `send/snapshots/snapshot_manager.py`
- `send/monitoring/restart_guard.py`
- All canonical documents in `send/docs/canonical/`
