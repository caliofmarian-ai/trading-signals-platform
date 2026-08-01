# Live Acceptance Checklist

> **Status update (corrective cycle 2)**: PR #29 was merged and automated tests passed
> (114 Telegram-focused, 499 total).  Railway deployment succeeded.  However, live
> Telegram acceptance still failed — see ROOT_CAUSE_ANALYSIS in the
> `telegram-transport-and-recovery-hardening` subdirectory for the independently
> verified root causes (parse_mode inconsistency, silent failure, token leakage,
> unanswered callbacks).  A corrective branch and new PR have been raised.  The items
> below remain open until live acceptance passes after that corrective fix is deployed.

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
