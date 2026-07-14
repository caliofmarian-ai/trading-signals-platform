# RAILWAY_VOLUME_CHECKLIST.md

- [ ] Create one persistent Railway volume
- [ ] Mount it at `/data`
- [ ] Confirm `/data` is writable
- [ ] Confirm `/data/config` exists after first start
- [ ] Confirm `/data/state`, `/data/outcomes`, `/data/observability`, `/data/analytics`, `/data/snapshots` exist
- [ ] Keep the same volume across redeployments
- [ ] Export/backup the volume before destructive config resets
