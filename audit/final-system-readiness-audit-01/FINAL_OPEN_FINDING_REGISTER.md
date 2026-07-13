# FINAL_OPEN_FINDING_REGISTER.md

**Audit ID:** final-system-readiness-audit-01  
**Date:** 2026-07-13  
**Branch:** copilot/conduct-final-system-readiness-audit  
**HEAD Commit:** 5aa40f0

---

## PURPOSE

This register collects ALL open findings from canonical audit through BATCH-09, plus any newly discovered findings from this final audit. For each finding, the current status is independently determined.

---

## FINDING STATUS KEY
- **RESOLVED** — Finding addressed; implementation verified in current code.
- **PARTIALLY RESOLVED** — Partially addressed; residual exists.
- **STILL OPEN** — Not addressed; still present.
- **SUPERSEDED** — Replaced by a later finding or design change.
- **INVALIDATED** — Determined not to be a real issue.
- **REQUIRES OWNER DECISION** — Technical fix is blocked pending owner direction.
- **DEFERRED** — Acknowledged; planned for future batch; non-blocking.

---

## SECTION 1 — CANONICAL AUDIT (canonical-audit-01)

| Finding ID | Description | Original Severity | Current Status | Evidence |
|---|---|---|---|---|
| GAP-001 | Legacy index superseded by canonical master index | MEDIUM | RESOLVED | CANONICAL_MASTER_INDEX_v1.0.0.md is authoritative; legacy indexes retained as superseded |
| GAP-002 | Missing canonical authority hierarchy | HIGH | RESOLVED | Master index sections 2.1–2.5 define full authority hierarchy |
| GAP-003 | Missing `storage.config_path()` helper | HIGH | RESOLVED (BATCH-01) | `storage.config_path()` implemented; 7 tests pass |
| GAP-004–GAP-012 | Various canonical conflicts resolved | MEDIUM–HIGH | RESOLVED | Per canonical-reconciliation-01 and subsequent batches |
| GAP-013 | Fail-open bug in `in_admin_context()` | CRITICAL | RESOLVED (BATCH-05) | `in_admin_context()` fails-closed; 3 security tests pass |
| GAP-016 | Legacy `send/legacy/bot_control.py` orphan | MEDIUM | RESOLVED (BATCH-09) | File deleted; non-importability test passes |
| GAP-020 | Inert health/metrics modules | LOW | RESOLVED (BATCH-09) | Files deleted; non-importability tests pass |
| CON-001 | Module-boundary import blocked | HIGH | RESOLVED (BATCH-01) | Import chain verified; 7 tests pass |

---

## SECTION 2 — CANONICAL RECONCILIATION (canonical-reconciliation-01)

| Finding ID | Description | Current Status | Evidence |
|---|---|---|---|
| OWNER-001 through OWNER-004 | Owner decisions on document classification | RESOLVED | Master index documents classification decisions; active/superseded set confirmed |
| OWNER-005 | Master index authority | RESOLVED | CANONICAL_MASTER_INDEX_v1.0.0.md is single authoritative index |

---

## SECTION 3 — DEEP CODE-TO-CANON AUDIT (deep-code-canon-audit-01)

| Finding ID | Description | Current Status | Evidence |
|---|---|---|---|
| Dead module findings | Various modules classified as dead/orphan | RESOLVED (BATCH-09) | Dead modules deleted; active replacements confirmed |
| admin_permissions.json DEAD classification | File classified as dead | PARTIALLY — Reclassified | File is TEST_ONLY fixture (OF-09-004); classification error in audit not fixed in code (non-issue) |
| Path authority findings | /opt/binarybot hardcoded paths | PARTIALLY RESOLVED | Live writes converged (BATCH-09); env-var defaults remain (OF-09-002) |

---

## SECTION 4 — BATCH-SPECIFIC OPEN FINDINGS (from batch reports)

### BATCH-01 Open Findings
All resolved. No items carried forward.

### BATCH-02 Open Findings
All resolved. No items carried forward.

### BATCH-03 Open Findings
All resolved. No items carried forward.

### BATCH-04 Open Findings
All resolved. No items carried forward.

### BATCH-05 Open Findings
All resolved. No items carried forward.

### BATCH-06 Open Findings
All resolved. No items carried forward.

### BATCH-07 Open Findings
All resolved. No items carried forward.

### BATCH-08 Open Findings
| Finding ID | Description | Current Status | Notes |
|---|---|---|---|
| OF-08-001 | TEST_PLAN_v2.0.0.md truncation | STILL OPEN → OF-09-001 | Carried to BATCH-09; owner decision required |
| OF-08-002 | Hardcoded outcomes paths in outcome_service.py | RESOLVED (BATCH-09) | Converged to `storage.root_path()` |
| OF-08-003 | Hardcoded config/obs constants in admin_commands.py | RESOLVED (BATCH-09) | Converged to `_storage.root_path()` |
| OF-08-004 | `datetime.utcnow()` deprecation | RESOLVED (BATCH-09) | Replaced with `datetime.now(timezone.utc)` |

### BATCH-09 Open Findings
| Finding ID | Description | Severity | Current Status | Notes |
|---|---|---|---|---|
| OF-09-001 | TEST_PLAN_v2.0.0.md truncation at section 17 | MEDIUM | STILL OPEN | OWNER-DECISION-BATCH09-001; owner must supply section 17+ text |
| OF-09-002 | Residual /opt/binarybot env-var defaults in multiple modules | LOW | STILL OPEN (DEFERRED) | All env-var overridable; not a deployment blocker if env vars set correctly |
| OF-09-003 | 5 .bak files committed to send/core/ | LOW | STILL OPEN (DEFERRED) | `send/core/signal_engine.py.bak_{3 files}`, `send/core/strategy_v2.py.bak_{2 files}`; no runtime impact |
| OF-09-004 | admin_permissions.json DEAD classification in deep audit | INFO | INVALIDATED | File is a TEST_ONLY fixture; correct classification; deep audit classification error is non-actionable |

---

## SECTION 5 — NEWLY DISCOVERED FINDINGS (This Final Audit)

| Finding ID | Description | Severity | Status | Notes |
|---|---|---|---|---|
| FA-001 | `outcome_service._check_membership()` uses `requests.get()` without explicit timeout | LOW | DEFERRED | Network hang risk in production; recommend adding `timeout=10` in future quality pass |
| FA-002 | `telegram_publisher.send_message()` uses HTTP without explicit timeout | LOW | DEFERRED | Same concern as FA-001 |
| FA-003 | channel_config.json committed with real production Telegram channel IDs | LOW | DEFERRED | Not credentials; operator decision whether to gitignore or treat as configuration-in-repo |
| FA-004 | No HTTP health endpoint exists | LOW | DEFERRED | No liveness check available for Railway monitoring; recommend future health check writer |
| FA-005 | `*.bak*` not in `.gitignore` | LOW | DEFERRED | Causes .bak files to be tracked; add to .gitignore in future cleanup |
| FA-006 | `strategy_auditor_daily.py` has no external scheduler configured | INFO | DEFERRED | Scheduling is a deployment planning concern, not a code defect |
| FA-007 | No production `requirements.txt` (runtime-only) | LOW | DEFERRED | `requirements-test.txt` exists; a minimal production `requirements.txt` should be created during deployment preparation |

---

## SECTION 6 — SUMMARY

| Severity | Resolved | Deferred/Open | REQUIRES OWNER |
|---|---|---|---|
| CRITICAL | 1 (GAP-013) | 0 | 0 |
| HIGH | 4 (GAP-003, CON-001, GAP-002, GAP-013) | 0 | 0 |
| MEDIUM | All batch findings | OF-09-001 | 1 (OWNER-DECISION-BATCH09-001) |
| LOW | All batch findings | OF-09-002, OF-09-003, FA-001 through FA-005 | 0 |
| INFO | — | OF-09-004, FA-006, FA-007 | 0 |

**CRITICAL/HIGH unresolved:** 0  
**MEDIUM unresolved:** 1 (TEST_PLAN truncation — owner decision required)  
**LOW unresolved:** 7 (all deferred — no deployment blockers)  
**INFO:** 3 (informational)
