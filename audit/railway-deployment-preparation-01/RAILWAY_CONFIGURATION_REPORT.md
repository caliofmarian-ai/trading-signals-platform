# RAILWAY_CONFIGURATION_REPORT.md

## Files added
- `railway.json`
- `runtime.txt`
- `requirements.txt`

## Build command
`python -m pip install --upgrade pip && python -m pip install --no-cache-dir -r requirements.txt`

## Start command
`PYTHONPATH=send python -m scripts.railway_start`

## Restart policy
- `ON_FAILURE`
- max retries: `10`
- replicas: `1`

## Runtime
- Python `3.12.3`

## Notes
- No deployment was performed.
- No Railway project/account data is hardcoded.
- No HTTP health path is configured because the service is worker-style; health is exposed as a bounded command instead.
