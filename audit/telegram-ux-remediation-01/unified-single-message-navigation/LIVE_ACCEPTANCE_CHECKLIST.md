# Live Acceptance Checklist

- [ ] `/start`, `/help`, `/status` remain single-message interactive pages
- [ ] `/admin`, `/strategy`, `/thresholds`, `/sr`, `/spike`, `/symbols`, `/engine`, `/debug`, `/report`, `/roles`, `/affiliate` converge to single-message navigation
- [ ] APP callbacks never create additional interactive pages
- [ ] ADMIN_NAV callbacks never create additional interactive pages
- [ ] Home/Back/Refresh always edit the active interactive message
- [ ] Unauthorized/rate-limited/unknown interactive responses do not accumulate panels
- [ ] Stale/deleted active message produces one tracked replacement only
- [ ] File/document delivery remains separate and does not replace active UI state
- [ ] Signal/outcome/publication and operational alert flows remain unaffected
- [ ] Issue #27 remains OPEN until live acceptance fully passes
