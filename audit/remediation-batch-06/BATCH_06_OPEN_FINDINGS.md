# BATCH_06_OPEN_FINDINGS

## BATCH-06 residual risks

1. **Focused scan starvation remains architectural debt**
   - current runtime still scans watchlist-only while focus mode is active
   - this pre-existed BATCH-06 and was not expanded into a broader scheduler redesign
   - risk: wide-scan opportunity coverage may still be reduced while focus is active

2. **Snapshot restore is rollback-aware but not multi-file transactional across process crash boundaries**
   - restore now validates before writing and rolls back on in-process failure
   - a host crash between file replacements could still leave one restored file already updated

3. **Buffer-mode compatibility remains transitional**
   - `admin_settings.json` is now the canonical segmented settings target
   - legacy root `settings.json` may still be read for controlled migration if present
   - no new buffer-mode control surface was introduced

## Remaining repo findings outside BATCH-06 scope

- `GAP-010` — analytics/research readers call undefined helper (**HIGH**, BATCH-07/BATCH-08 path)
- `GAP-015` — `strategy_auditor_daily.py` package import broken (**MEDIUM**, BATCH-07/BATCH-08 path)
- `GAP-017` — full canonical test-plan implementation still incomplete (**HIGH**, later dedicated batch)
- `GAP-016` — legacy bot cleanup deferred (**MEDIUM**, cleanup batch)
- `GAP-020` — health/metrics path still inert (**LOW**, cleanup batch)

## Exact work remaining for BATCH-07

- restore analytics/research toolchain only
- do not revisit FSM/restart/path migration unless BATCH-07 uncovers a direct dependency

## Rollback instructions

1. Revert the BATCH-06 commits.
2. Remove `audit/remediation-batch-06/`.
3. Re-run `PYTHONPATH=send python -m pytest -q tests`.
4. If rollback is partial, ensure segmented canonical state files remain the sole live write targets before restarting runtime.
