# BATCH_09_CLASSIFICATION_REGISTER

| Candidate | Classification | Rationale | Action |
|-----------|---------------|-----------|--------|
| `send/legacy/bot_control.py` | ORPHAN | No import or runtime callers; missing dotenv/telegram deps; divergent control surface | DELETED |
| `send/core/strategy_v2 - Copy.py` | DUPLICATE | Byte-for-byte identical to `strategy_v2.py`; no callers; authoritative replacement exists | DELETED |
| `send/state/event_store.json` | DEAD | Empty `[]` array; no runtime reader; observability writes go elsewhere | DELETED |
| `send/state/state_store.json` | DEAD | Old channel/limits schema; active router reads channel_config.json; no reader | DELETED |
| `send/config/admin_permissions.json` | TEST_ONLY | Runtime code never reads it; test conftest fixture copies it; batch_01 asserts its presence | PRESERVED |
| `send/validation/statistical_proof.py` | DEAD | 0-byte empty placeholder; no callers | DELETED |
| `send/validation/__init__.py` | DEAD | Empty package init for dead module | DELETED |
| `send/monitoring/health_check.py` | ORPHAN | No runtime or test callers; reads from orphan metrics_collector (GAP-020) | DELETED |
| `send/metrics/metrics_collector.py` | ORPHAN | Only caller is health_check.py (itself orphan); not wired to runtime (GAP-020) | DELETED |
| `send/metrics/aggregates_writer.py` | ORPHAN | No callers; imports metrics_collector | DELETED |
| `send/metrics/__init__.py` | DEAD | Empty package init; all package members deleted | DELETED |
| `send/journal/trade_journal.py` | ORPHAN | No callers; hardcoded /opt/binarybot/journal/ paths; not referenced by runtime | DELETED |
| `send/journal/__init__.py` | DEAD | Empty package init for orphan module | DELETED |
| `send/journal/boot.log` | DEAD (artifact) | Generated runtime log; should not be version-controlled | DELETED |
| `send/engine.log` | DEAD (artifact) | Generated runtime log; should not be version-controlled | DELETED |
| `send/tmp_decision_audit_patch_input.txt` | DEAD (artifact) | Temporary remediation working file | DELETED |
| `send/tmp_decision_chunk_00..05` (6 files) | DEAD (artifact) | Temporary remediation working files | DELETED |
| `send(2).zip` | DEAD (artifact) | Development archive; 25 MB; should not be version-controlled | DELETED |
| `send/state_store/event_store.py` | ORPHAN | No callers; parallel observability facade superseded by core/observability_logger.py | DELETED |
| `send/state_store/state_store.py` | ACTIVE | Imported by fsm_runtime, distribution_router, signal_engine, snapshot_manager, restart_guard | PRESERVED |
| `send/state_store/__init__.py` | ACTIVE | Package init for active state_store module | PRESERVED |
| `send/snapshots/snapshot_manager.py` | ACTIVE | Imported by system_boot; tested in batch_06 and canonical/persistence | PRESERVED |
| `send/snapshots/__init__.py` | ACTIVE | Package init | PRESERVED |
| `send/monitoring/restart_guard.py` | ACTIVE | Imported by system_boot; tested in batch_06 | PRESERVED |
| `send/core/outcome_service.py` | ACTIVE (path-converge) | Hardcoded /opt/binarybot/outcomes/ paths replaced with storage.root_path() | MODIFIED |
| `send/core/admin_commands.py` | ACTIVE (path-converge) | Hardcoded CONFIG_DIR, OBS_DIR, REPORTS_DIR replaced with _storage.root_path() | MODIFIED |
| `send/tools/strategy_auditor_lib.py` | ACTIVE (datetime-fix) | datetime.utcnow() → datetime.now(datetime.UTC) | MODIFIED |
| `send/config/algo_params.json` | ACTIVE | Runtime params; loaded by params_loader, admin_commands | PRESERVED |
| `send/config/channel_config.json` | ACTIVE | Distribution config; loaded by distribution_router | PRESERVED |
| `send/config/admin_roles.json` | ACTIVE | Role config; loaded by admin_permissions | PRESERVED |
| `send/config/admin_settings.json` | ACTIVE | Admin settings; read by admin_commands | PRESERVED |
| `send/config/active_symbols.json` | ACTIVE | Symbol list; read by signal_engine, admin_commands | PRESERVED |
| `send/state/focus_state.json` | ACTIVE | FSM state; read/written by state_store/state_store.py | PRESERVED |
| `send/state/dist_state.json` | ACTIVE | Distribution state; read/written by state_store/state_store.py | PRESERVED |
| `send/state/restart_guard.json` | ACTIVE | Restart guard state; read/written via restart_guard.py | PRESERVED |
| `send/_archive/` | GOVERNANCE/HISTORICAL | Remediation backups and housekeeping reports | PRESERVED |
| All `audit/` documents | GOVERNANCE/HISTORICAL | Audit and remediation records | PRESERVED |
| All `send/docs/canonical/` | GOVERNANCE/HISTORICAL | Canonical specifications | PRESERVED |

## UNKNOWN Candidates
None — all candidates were classified from repository evidence.

## Summary Counts
| Classification | Count |
|---------------|-------|
| DELETED (ORPHAN) | 8 files |
| DELETED (DEAD) | 6 files |
| DELETED (DUPLICATE) | 1 file |
| DELETED (DEAD artifact) | 9 items |
| TEST_ONLY (preserved) | 1 file |
| ACTIVE (preserved) | many |
| ACTIVE (modified) | 3 files |
