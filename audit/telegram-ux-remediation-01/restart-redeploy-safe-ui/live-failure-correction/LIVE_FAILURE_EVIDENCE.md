# Live Failure Evidence

- Production acceptance after PR #32 merge/deploy failed during restart and redeploy testing.
- Authoritative evidence from the conversation screenshots showed two simultaneous bot application messages in one private `(chat_id, user_id, thread_id)` session.
- Observed sequence:
  1. `/start` created message A titled `⚙️ Admin Control Surface` with a Home button.
  2. `/admin` created a second message B containing the full Admin menu.
  3. Later `/admin`, `/start`, `/engine`, `/start` activity included silent or stuck behavior.
- This means Issue #31 acceptance still failed in production even though PR #32 test coverage passed.
- Issue #31 remains open.
