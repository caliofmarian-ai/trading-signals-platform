# Railway Persistence Analysis

## Runtime base dir contract
- Railway startup path (`scripts/railway_start.py`) resolves and enforces `BINARYBOT_BASE_DIR` on persistent volume.
- `scripts/railway_init.py` ensures runtime directories exist, including `state/`.

## Active UI persistence fit
- Active UI artifact uses existing runtime state directory and atomic persistence.
- No second persistence framework was introduced.
- On Railway restart/redeploy with persistent volume, active UI metadata survives and can be reused.

## Safety behavior
- If volume file is corrupt or schema is unsupported, runtime still starts and polling remains active.
- App falls back to replacement generation when persisted `message_id` is stale/deleted.
