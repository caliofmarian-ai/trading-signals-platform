# Live Acceptance Checklist

> Historical note: the PR #32 live run failed this checklist in production. Two bot application messages became visible in one private session and later commands appeared unresponsive. Issue #31 remains open.

- [ ] Deploy branch to Railway with persistent volume attached.
- [ ] Open `/start`, verify one interactive UI message is tracked.
- [ ] Restart service (no code change), trigger `/status`, confirm existing UI message is edited (no extra message).
- [ ] Redeploy service, trigger `APP:STATUS` and `APP:HOME`, confirm same-message reuse.
- [ ] Manually delete active UI message in Telegram, trigger `/status`, confirm one replacement message is sent and becomes active.
- [ ] Verify multiple sessions isolation:
  - [ ] same user different chats
  - [ ] same user same chat different topics
  - [ ] different users
- [ ] Verify non-owner role cannot access owner-only surfaces after restart/redeploy.
- [ ] Verify callback acknowledgement still dismisses spinner.
- [ ] Verify no persisted file contains message text or user message body.
- [ ] Verify logs contain no bot token leakage.
