# BATCH_09_CLEANUP_MANIFEST

## Pre-Cleanup Rollback Commit
The repository state before BATCH-09 changes is preserved in git history. Rollback instructions are in `BATCH_09_ROLLBACK_PLAN.md`.

---

## Group 1: GAP-016 — Legacy Orphan Deletion

### Files Deleted
| File | Reason |
|------|--------|
| `send/legacy/bot_control.py` | ORPHAN; no callers; missing deps; divergent control surface |

### Evidence
- No `import legacy` or `from legacy` found in any active Python file
- `dotenv` and `python-telegram-bot` not installed as project deps
- GAP-016 specified for BATCH-09 cleanup

---

## Group 2: GAP-020 — Metrics/Health Orphan Deletion

### Files Deleted
| File | Reason |
|------|--------|
| `send/monitoring/health_check.py` | ORPHAN; no callers; reads from orphan metrics_collector |
| `send/metrics/metrics_collector.py` | ORPHAN; only health_check.py called it |
| `send/metrics/aggregates_writer.py` | ORPHAN; no callers |
| `send/metrics/__init__.py` | DEAD; empty package init for deleted modules |

### Evidence
- GAP-020: "Either wire metrics into runtime or demote/remove feature" — BATCH-09 authorization covers removal
- `grep -rn "metrics_collector|from metrics|import metrics"` → only health_check.py (itself orphan)
- `grep -rn "health_check|from monitoring"` → only `monitoring/restart_guard` in system_boot (restart_guard, NOT health_check)

---

## Group 3: Dead Duplicate Deletion

### Files Deleted
| File | Reason |
|------|--------|
| `send/core/strategy_v2 - Copy.py` | DUPLICATE; byte-for-byte identical to strategy_v2.py |

### Evidence
- `diff` exit code 0 (files identical)
- No callers reference the copy filename

---

## Group 4: Dead State Artifacts

### Files Deleted
| File | Reason |
|------|--------|
| `send/state/event_store.json` | DEAD; content `[]`; active logging uses JSONL via observability_logger |
| `send/state/state_store.json` | DEAD; old channel/limits schema; active router reads channel_config.json |

### Evidence
- `send/state/event_store.json` content: `[]` (empty array)
- `send/state/state_store.json` content: schema_version 1.0.0 channel+limits config not read by any active module
- `grep -rn "event_store.json|state_store.json"` in runtime code → zero results

---

## Group 5: Dead Config Artifact — PRESERVED (Reclassified)

| File | Classification | Action |
|------|---------------|--------|
| `send/config/admin_permissions.json` | TEST_ONLY | PRESERVED |

**Reclassification note**: The deep audit classified this as DEAD (no runtime reader). Re-inspection during BATCH-09 found it is required by:
- `tests/canonical/conftest.py:50` — `canonical_runtime_root` fixture copies it
- `tests/batch_01/test_boot_and_import_stabilization.py` — asserts its existence as a supported config file

It is not read by live runtime code (`admin_permissions.py` uses a hardcoded matrix). Reclassified as TEST_ONLY; preserved in place.

---

## Group 6: Dead Code Placeholders

### Files Deleted
| File | Reason |
|------|--------|
| `send/validation/statistical_proof.py` | DEAD; 0-byte empty placeholder; no callers |
| `send/validation/__init__.py` | DEAD; 0-byte empty package init |

---

## Group 7: Journal Orphan Deletion

### Files Deleted
| File | Reason |
|------|--------|
| `send/journal/trade_journal.py` | ORPHAN; no callers; hardcoded /opt paths |
| `send/journal/__init__.py` | DEAD; empty package init for orphan |

---

## Group 8: State Store Orphan

### Files Deleted
| File | Reason |
|------|--------|
| `send/state_store/event_store.py` | ORPHAN; no callers; parallel observability facade superseded by core/observability_logger.py |

---

## Group 9: Committed Runtime Artifacts

### Files Deleted
| File | Type |
|------|------|
| `send/engine.log` | Generated runtime log |
| `send/journal/boot.log` | Generated runtime log |
| `send/tmp_decision_audit_patch_input.txt` | Remediation working file |
| `send/tmp_decision_chunk_00` | Remediation working file |
| `send/tmp_decision_chunk_01` | Remediation working file |
| `send/tmp_decision_chunk_02` | Remediation working file |
| `send/tmp_decision_chunk_03` | Remediation working file |
| `send/tmp_decision_chunk_04` | Remediation working file |
| `send/tmp_decision_chunk_05` | Remediation working file |
| `send(2).zip` | 25 MB development archive |

---

## Group 10: Path Convergence

### Files Modified
| File | Change |
|------|--------|
| `send/core/outcome_service.py` | Replace 3 hardcoded `/opt/binarybot/outcomes/` constants with `storage.root_path()` |
| `send/core/admin_commands.py` | Replace `CONFIG_DIR`, `OBS_DIR`, `REPORTS_DIR` and 6 derived constants with `_storage.root_path()` |

---

## Group 11: Datetime Warning Fix

### Files Modified
| File | Change |
|------|--------|
| `send/tools/strategy_auditor_lib.py` | `datetime.datetime.utcnow()` → `datetime.datetime.now(datetime.UTC)` |

---

## Group 12: Artifact Prevention

### Files Created
| File | Purpose |
|------|---------|
| `.gitignore` | Prevents recurrence of log files, tmp_decision_*, zip archives, pycache |

---

## Group 13: Test Coverage

### Files Created
| File | Tests |
|------|-------|
| `tests/batch_09/test_batch09_cleanup.py` | 42 targeted BATCH-09 tests |

---

## Total Summary
| Action | Count |
|--------|-------|
| Files deleted (orphan/dead/duplicate/artifact) | 23 |
| Files preserved (reclassified TEST_ONLY) | 1 |
| Files modified (path convergence + datetime fix) | 3 |
| Files created (tests + gitignore + audit docs) | 14+ |
