# REPOSITORY_AND_CANONICAL_INTEGRITY_REPORT.md

**Audit ID:** final-system-readiness-audit-01  
**Date:** 2026-07-13  
**Branch:** copilot/conduct-final-system-readiness-audit  
**HEAD Commit:** 5aa40f0

---

## 1. REPOSITORY INTEGRITY

### 1.1 Git Status
- **Branch:** `copilot/conduct-final-system-readiness-audit`
- **HEAD:** `5aa40f0` — Merge pull request #13 from caliofmarian-ai/copilot/batch-09-controlled-legacy-cleanup
- **Working tree:** clean — no modified, staged, or untracked files.
- **BATCH-09 parent commit:** `63834b3` — BATCH-09: complete remediation — 272 tests pass, 0 warnings, GAP-016/020 closed
- **BATCH-08 merge commit:** `43b097d` — Merge pull request #12 from caliofmarian-ai/copilot/batch-08-full-canonical-test-suite

### 1.2 Committed Backup Files (Finding)
The following backup files are committed in the repository and should not be in version control:

| File | Classification |
|---|---|
| `send/core/signal_engine.py.bak_1772805524` | Development backup artifact — should be in .gitignore |
| `send/core/signal_engine.py.bak_envelope_fix` | Development backup artifact |
| `send/core/signal_engine.py.bak_fix` | Development backup artifact |
| `send/core/strategy_v2.py.bak_1772804197` | Development backup artifact |
| `send/core/strategy_v2.py.bak_decision_audit` | Development backup artifact |

**Severity:** LOW — no runtime impact; these files are not imported; they create repository hygiene noise.  
**Classification per OF-09-003 pattern:** Development artifacts in version control.  
**Action required:** Future cleanup batch should remove these and add `*.bak*` to `.gitignore`.

### 1.3 Channel Config — Live IDs in Repository
`send/config/channel_config.json` contains real Telegram channel IDs (negative integers for group/channel chats). These are committed to the repository. Bot token is NOT present in any committed file.

**Assessment:** Channel IDs are configuration values, not credentials. They do not grant API access without the bot token. However, they identify live production channels and should be noted for deployment planning. The operator should decide whether channel_config.json should be managed as a deployment secret or kept in repository.

### 1.4 `.gitignore` Coverage
- `*.log`, `*.jsonl`, `tmp/` are covered.
- `*.bak*` pattern is NOT in `.gitignore` — this is why backup files were committed.

### 1.5 Committed State Files
The following state files are committed in `send/state/` and `send/outcomes/`:
- `send/state/active_symbols.json` — active symbols config (appropriate: this is config, not transient state)
- `send/state/focus_state.json` — FSM state (development baseline)
- `send/state/dist_state.json` — distribution state (development baseline)
- `send/state/outcomes.json` — outcome index (development baseline)
- `send/state/restart_guard.json` — restart guard state (development baseline)
- `send/state/trade_journal.json` — trade journal (development baseline)
- `send/outcomes/open_now_registry.json` — open trades registry (development baseline)
- `send/outcomes/outcomes.jsonl` — outcome records (development baseline, should be empty or absent in production)

**Assessment:** These committed state files serve as test fixtures and development baselines. At deployment, `BINARYBOT_BASE_DIR` should point to a Railway persistent volume, so these files will not be used as production state.

---

## 2. CANONICAL INTEGRITY

### 2.1 Active Canonical Document Count
- **Master index declares:** 41 active canonical documents
- **Files on disk in `send/docs/canonical/active/`:** 42 (41 documents + 1 index file = CANONICAL_MASTER_INDEX_v1.0.0.md)
- **Reconciliation:** The master index lists itself as the index document and lists 41 domain documents. Every document on disk is either the index itself or appears in the index. No orphaned documents.

### 2.2 Active Canonical Documents — Full Inventory

| # | Filename | Present on Disk |
|---|---|---|
| 1 | CANONICAL_STRATEGY_STACK_v1.0.0.md | YES |
| 2 | ADMIN_SURFACE_AND_CONTROL_PLANE_CANON_v2.0.0.md | YES |
| 3 | OBSERVABILITY_SPEC_v2.0.0.md | YES |
| 4 | SIGNAL_DISTRIBUTION_ARCHITECTURE_v2.0.0.md | YES |
| 5 | CANON_BATCH_EVALUATION_v2.0.0.md | YES |
| 6 | ALGO_SPEC_v2.0.0.md | YES |
| 7 | AUTONOMOUS_STRATEGY_EVOLUTION_SYSTEM_v2.0.0.md | YES |
| 8 | CANONICAL_MASTER_INDEX_v1.0.0.md | YES (index itself) |
| 9 | CHANNEL_CONFIG_SPEC_v2.0.0.md | YES |
| 10 | COMMUNITY_FEEDBACK_AND_PRIVACY_SPEC_v2.0.0.md | YES |
| 11 | CONTROL_PANEL_HIERARCHY_AND_INTELLIGENCE_SPEC_v2.0.0.md | YES |
| 12 | DECISION_AUDIT_SPEC_v2.0.0.md | YES |
| 13 | DECISION_OBJECT_CANONICAL_SPEC_v1.0.0.md | YES |
| 14 | DEPLOYMENT_PROTOCOL_v2.0.0.md | YES |
| 15 | EVENT_SCHEMA_SPEC_v2.0.0.md | YES |
| 16 | FAILURE_RECOVERY_SPEC_v2.0.0.md | YES |
| 17 | FSM_DECISION_ENGINE_SPEC_v1.0.0.md | YES |
| 18 | GOVERNANCE_AND_CHANGE_CONTROL_v2.0.0.md | YES |
| 19 | MODULE_INTERFACE_SPEC_v2.0.0.md | YES |
| 20 | OBSERVABILITY_LOGGING_SPEC_v2.0.0.md | YES |
| 21 | OUTCOME_TRACKING_SPEC_v2.0.0.md | YES |
| 22 | PERFORMANCE_ANALYTICS_SPEC_v2.0.0.md | YES |
| 23 | RESEARCH_AND_LEARNING_FRAMEWORK_SPEC_v2.0.0.md | YES |
| 24 | RISK_MODEL_v2.0.0.md | YES |
| 25 | ROLE_AND_PERMISSION_MATRIX_SPEC_v2.0.0.md | YES |
| 26 | SECURITY_MODEL_v2.0.0.md | YES |
| 27 | SIGNAL_DISTRIBUTION_SPEC_v2.0.0.md | YES |
| 28 | SIGNAL_ECONOMICS_AND_MONETIZATION_MODEL_v2.0.0.md | YES |
| 29 | SIGNAL_ENGINE_EXECUTION_SPEC_v2.0.0.md | YES |
| 30 | SR_CORRIDOR_ENGINE_SPEC_v2.0.0.md | YES |
| 31 | STRATEGY_INTELLIGENCE_SYSTEM_v2.0.0.md | YES |
| 32 | STRATEGY_PARAMETER_CONTROL_SPEC_v2.0.0.md | YES |
| 33 | SYSTEM_ARCHITECTURE_MAP_v2.0.0.md | YES |
| 34 | SYSTEM_INVARIANTS_v2.0.0.md | YES |
| 35 | TELEGRAM_UX_v2.0.0.md | YES |
| 36 | TEST_PLAN_v2.0.0.md | YES (truncated — OF-09-001) |
| 37 | TIME_MODEL_UNIFIED_CANON_v2.0.0.md | YES |
| 38 | TRADE_TEMPORAL_TELEMETRY_SPEC_v2.0.0.md | YES |
| 39 | ADMIN_CONTROL_SPEC_v2.0.0.md | YES |
| 40 | ADMIN_OPERATIONS_SPEC_v2.0.0.md | YES |
| 41 | ADMIN_TREE_MAP_v2.0.0.md | YES |
| 42 | AFFILIATE_SIGNAL_DISTRIBUTION_MODEL_v2.0.0.md | YES |

**Result:** All 41 domain canonical documents present. No document missing. No orphan.

### 2.3 Contradictory Status Declarations
No contradictory version or status declarations detected across active canonical documents. All active documents declare v2.0.0 (domain) or v1.0.0 (index and root manifests), consistent with the master index.

### 2.4 TEST_PLAN Truncation (OPEN — OWNER ACTION)
- **File:** `send/docs/canonical/active/TEST_PLAN_v2.0.0.md`
- **Status:** Truncated — 594 lines, ends at `## 17. Analytics and Research Va`
- **Missing:** Section 17 body content, sections 18+
- **Owner decision:** OWNER-DECISION-BATCH09-001 (open)
- **Impact on canonical integrity:** ONE of 41 active canonical documents is incomplete. This is a defect in the canonical document set.

### 2.5 Canonical Directory Structure
- `send/docs/canonical/active/` — 42 files (index + 41 documents): CORRECT
- `send/docs/canonical/deprecated/` — present (historical)
- `send/docs/canonical/proposed/` — present
- `send/docs/canonical/superseded/` — present
- `send/docs/canonical/transitional/` — present

### 2.6 Superseded Documents
- `send/docs/MASTER_DOCUMENT_INDEX.md` — superseded, retained for history: PRESENT
- `send/docs/BINARYBOT_MASTER_INDEX.md` — superseded, retained for history: PRESENT

---

## 3. VERDICTS

| Dimension | Verdict | Notes |
|---|---|---|
| Repository integrity | CONDITIONALLY READY | 5 committed .bak files; state files committed (non-blocking for deployment with BINARYBOT_BASE_DIR override); channel IDs in repo config |
| Canonical integrity | CONDITIONALLY READY | 40/41 documents complete; TEST_PLAN truncated (OWNER-DECISION-BATCH09-001 open) |
