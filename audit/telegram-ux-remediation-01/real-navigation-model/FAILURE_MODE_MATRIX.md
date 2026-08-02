# Failure Mode Matrix

| Failure mode | Mitigation |
|---|---|
| APP history empty on Back | Safe fallback to Home |
| Unsupported APP history entry | Safe fallback to Home |
| APP history loop attempt | Same-page parent is rejected; fallback to Home |
| Stale APP callback generation | Safe fallback to current Home generation |
| Restart/state loss before Back | Safe fallback to Home |
| Unauthorized admin callback context | Existing wrong-chat denial remains |
| Roles reload in owner DM | Denied |
| Roles reload without permission | Denied |
| Runtime audit export failure | Returns to the correct diagnostic/health/security parent instead of unconditional admin root |
