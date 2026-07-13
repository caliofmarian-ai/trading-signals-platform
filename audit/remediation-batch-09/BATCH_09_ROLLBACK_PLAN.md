# BATCH_09_ROLLBACK_PLAN

## Overview
BATCH-09 changes are all committed in a single logical group on the current branch. Rollback can be performed at any granularity using git.

## Pre-BATCH-09 Commit Reference
The commit immediately before BATCH-09 implementation can be identified by:
```bash
git log --oneline | grep -B1 "BATCH-09" | tail -1
# Or find the commit with message: "BATCH-08: ..."
```

## Full Rollback (Revert Everything)
```bash
# Find the last pre-BATCH-09 commit hash
ROLLBACK_SHA=$(git log --oneline | grep -A1 "BATCH-09" | tail -1 | awk '{print $1}')

# Hard reset to pre-BATCH-09 state
git reset --hard $ROLLBACK_SHA
```

## Selective Rollback by Group

### Restore deleted files
```bash
# Restore a specific deleted file from git history
git checkout HEAD~N -- send/legacy/bot_control.py  # where N = commits ago
```

### Revert code modifications
```bash
# Revert strategy_auditor_lib.py datetime fix
git checkout HEAD~N -- send/tools/strategy_auditor_lib.py

# Revert outcome_service.py path convergence
git checkout HEAD~N -- send/core/outcome_service.py

# Revert admin_commands.py path convergence
git checkout HEAD~N -- send/core/admin_commands.py
```

## Rollback Verification
After any rollback:
```bash
PYTHONPATH=send python3 -m pytest tests/ -q
# Expected: 230 passed (without BATCH-09 tests: 230; with: varies)
```

## Risk Assessment
- **Path convergence rollback**: Low risk. Test monkeypatching is unaffected. The only behavior change is the default path for new deployments without BINARYBOT_BASE_DIR.
- **Datetime fix rollback**: Low risk. Only affects deprecation warning suppression.
- **Deleted file rollback**: Any deleted file can be restored individually from git history. No data was lost; files were version-controlled.
- **Gitignore rollback**: Removing .gitignore has no runtime impact.

## No Data Was Destroyed
All deleted files were version-controlled and remain in git history. The `send/_archive/` directory was not touched. All canonical documents were preserved.

## Specific Reclassification Note
`send/config/admin_permissions.json` was initially deleted then immediately restored when tests revealed it as a test fixture dependency. The file is preserved in the final BATCH-09 state and no further rollback is needed for it.
