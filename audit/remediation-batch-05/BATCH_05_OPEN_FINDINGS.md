# BATCH_05_OPEN_FINDINGS

**Owner Decision Applied:** OWNER-002 = A
**Original Findings:** GAP-011, GAP-012, GAP-013
**Date:** 2026-07-13

---

## Resolved in BATCH-05

| Finding | Status | Resolution |
|---------|--------|------------|
| GAP-011: Admin mutation path bypasses atomic write/locks | ✅ RESOLVED | `storage.with_lock()` added to all 5 mutation helpers |
| GAP-012: Hardcoded permission matrix ignores admin_permissions.json | ✅ RESOLVED | `load_permissions_config()` added; `list_permissions_for_user()` merges both sources |
| GAP-013: bot_service uses separate RBAC/state path and fail-open chat guard | ✅ RESOLVED | Legacy Admin path retired; `in_admin_context()` fail-closed; VOTE forwarding preserved |

---

## Deferred to Later Batches

### BATCH-06 (Owner decision pending: GAP-018)

**GAP-018**: State/path abstractions conflict between active core and `state_store`.
- Multiple path definitions for the same conceptual files across modules
- `bot_service.py` path constants were part of this conflict (partially mitigated by removing the legacy bot_service paths)
- Full resolution requires consolidating path layer onto `storage.config_path()` / `storage.state_path()`
- Defer to BATCH-06 segmented-state migration

**GAP-014**: FSM lifecycle lacks release/cooldown path.
- `fsm_runtime.py` focus mode can persist indefinitely
- Defer to BATCH-06

### BATCH-08 (Tools)

**GAP-015**: `strategy_auditor_daily.py` package import is broken.
- Import-check fails for `strategy_auditor_lib`
- Not related to Admin control plane; defer to BATCH-08

### BATCH-09 or BATCH-10 (Cleanup)

**GAP-016**: Legacy `legacy/bot_control.py` remains with missing `dotenv` dependency.
- Not part of BATCH-05 Admin control plane scope
- Should be archived/removed in a cleanup batch

**GAP-020**: Daily metrics/health path is effectively inert.
- Not Admin control plane related; defer

---

## Remaining Risks

### Risk 1: `in_admin_context()` scope after BATCH-05

**Risk**: VOTE_ callbacks bypass `in_admin_context()` by design (they're public-facing). Any new callback type added to `bot_service.handle_callback()` in future must explicitly decide whether it needs admin context gating.

**Mitigation**: Clear code structure — VOTE forwarding is before the `in_admin_context()` gate; all new callbacks after the gate will be denied if ADMIN_CONTROL_CHAT_ID is not set.

**Deferred to**: Operational discipline / code review.

### Risk 2: `OUTCOME:` legacy callback format still accepted

**Risk**: The `OUTCOME:<outcome>:<signal_id>` callback format is still handled (now delegated to `outcome_service` instead of the retired `_record_outcome`). If `outcome_service.handle_vote_callback()` rejects the call due to missing membership config or unknown signal, the error is surfaced to the user but the callback is not logged as an unauthorized Admin attempt.

**Mitigation**: `outcome_service` already handles this path with its own rejection/logging logic. The legacy format is now simply a redundant code path through the same canonical service.

**Deferred to**: BATCH-09 cleanup (could remove the `OUTCOME:` handler when no callers remain).

### Risk 3: bot_service.OUTCOMES_PATH retained

**Risk**: `OUTCOMES_PATH` is still declared in `bot_service.py` for BATCH-04 test compatibility. This path (`/opt/binarybot/state/outcomes.json`) is now written by no code path after BATCH-04/BATCH-05. It may create operator confusion if they see it in the module.

**Mitigation**: Comment explicitly states it is retained for BATCH-04 compatibility and is not written. Can be removed in BATCH-09 after confirming all test fixtures have been updated.

**Deferred to**: BATCH-09 cleanup.

### Risk 4: Buffer mode control gap

**Risk**: The legacy buffer mode (`BUFFER_SMALL/MEDIUM/LARGE`) callbacks have been retired without a canonical replacement. If operators relied on Telegram keyboard button buffer control, they now have no path.

**Assessment**: The canonical v2 spec explicitly superseded buffer-setting concepts. No canonical replacement is defined. If buffer mode control is operationally needed, a future batch must define it in the canonical Admin spec and implement it through `admin_commands.py`.

**Deferred to**: Future canonical update if required.

### Risk 5: Permissions file mutual override (no conflict detection)

**Risk**: When `admin_permissions.json` defines the same permission as the hardcoded `PERMISSION_MATRIX` for the same role, both apply (union). There is no detection of conflicts or override — the union is always taken. If the file grants fewer permissions than the hardcoded matrix for some role, the hardcoded matrix still applies.

**Assessment**: This is the safe direction. The file can only ADD permissions, not remove them. This prevents accidental permission regression via a misconfigured file. If full file-based override is required, a future design change is needed.

**Deferred to**: Canonical specification decision if needed.

---

## Work Required for BATCH-06

From BATCH-06 scope:
- FSM lifecycle: release/cooldown path for focus mode
- Segmented mutable runtime state/config paths
- Migration shims for state path consolidation
- bot_service.OUTCOMES_PATH can be removed when BATCH-06 confirms no callers remain

---

## Rollback Instructions

To revert BATCH-05 changes:

```bash
# Revert all three modified source files to their BATCH-04 state
git revert <BATCH-05 commit hash>
```

Or manually revert specific files:
- `send/core/admin_commands.py`: Remove `with _storage.with_lock(...)` wrappers from 5 mutation helpers
- `send/core/admin_permissions.py`: Remove `PERMISSIONS_CONFIG_PATH`, `_ROLE_NAME_MAP`, `load_permissions_config`, `reload_permissions_config`; revert `list_permissions_for_user` to only use `PERMISSION_MATRIX`
- `send/core/bot_service.py`: Restore from BATCH-04 state (re-add all legacy Admin panel code)

Note: Rolling back BATCH-05 re-introduces the GAP-011, GAP-012, GAP-013 defects.
