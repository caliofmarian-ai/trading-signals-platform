# RUNTIME_PATH_COMPARISON.md
# Issue #31 — Runtime Path Comparison

## base_dir() Resolution

```python
def base_dir() -> str:
    raw = os.getenv("BINARYBOT_BASE_DIR", "").strip()
    if raw:
        # Validates: exists, absolute, is directory
        return str(Path(raw).expanduser())
    return str(_PACKAGE_BASE_DIR)  # = send/  directory inside container
```

## Lock File Path

`state_path(".locks")` = `os.path.join(base_dir(), "state", ".locks")`

If `BINARYBOT_BASE_DIR` is NOT set (Railway default with no volume):
- Lock files are at `<container_image>/send/state/.locks/`
- These are **ephemeral** — exist in the container's writable layer
- Cleared on Redeploy (new container), survive on Restart (same container)

If `BINARYBOT_BASE_DIR` IS set (Railway volume mount):
- Lock files are at `<volume_mount>/state/.locks/`
- These are **persistent** — survive both Restart and Redeploy
- Post-fix: deployment ID check in `_lock_is_stale()` handles this case correctly

## Diagnostics Emitted at Startup

`telegram_app_nav.initialize_active_ui_state()` logs:
```json
{
  "code": "TELEGRAM_UI_STATE_INITIALIZED",
  "pid": <pid>,
  "deployment_id": "<railway_deployment_id>",
  "context": {
    "status": "ok|skipped|deferred",
    "path": "<resolved_state_path>",
    "session_count": <n>
  }
}
```

`telegram_updates.py` logs on startup:
```json
{
  "event": "poller_started",
  "component": "telegram_poller",
  "pid": <pid>,
  "deployment_identifier": "<deployment_id>",
  "state_path": "<resolved_state_path>"
}
```
