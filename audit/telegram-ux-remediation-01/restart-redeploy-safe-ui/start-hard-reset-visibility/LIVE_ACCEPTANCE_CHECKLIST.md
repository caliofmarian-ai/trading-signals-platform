# LIVE_ACCEPTANCE_CHECKLIST.md

## Live Acceptance Checklist — Issue #31 Deleted-Conversation Visibility

This checklist must be completed manually against the live Railway deployment
before Issue #31 is considered resolved.

---

## USER Account Test

- [ ] 1. Send `/start` to the bot.
- [ ] 2. Confirm exactly one USER message U1 is visible.
- [ ] 3. Delete the complete USER conversation from the Telegram client.
- [ ] 4. Open the bot and press Start (or send `/start`).
- [ ] 5. Confirm exactly one visible USER message U2 appears.
- [ ] 6. Send `/status`.
- [ ] 7. Confirm U2 is edited in-place (no new message sent).

## ADMIN/OWNER Account Test

- [ ] 8. Send `/start` to the bot from the ADMIN account.
- [ ] 9. Confirm exactly one ADMIN message A1 is visible.
- [ ] 10. Delete the complete ADMIN conversation from the Telegram client.
- [ ] 11. Open the bot and press Start (or send `/start`).
- [ ] 12. Confirm exactly one visible ADMIN message A2 appears.
- [ ] 13. Press the Admin button (open Admin panel).
- [ ] 14. Press the Engine button (open Engine status).
- [ ] 15. Press the Home button.
- [ ] 16. Confirm A2 is continuously edited in-place throughout steps 13–15.

## Railway Restart Test

- [ ] 17. Perform a Railway Restart.
- [ ] 18. Wait for the poller heartbeat to appear in logs.
- [ ] 19. Delete the USER conversation and press Start.
- [ ] 20. Confirm exactly one visible USER replacement message appears.
- [ ] 21. Delete the ADMIN conversation and press Start.
- [ ] 22. Confirm exactly one visible ADMIN replacement message appears.

## Railway Redeploy Test

- [ ] 23. Perform a Railway Redeploy.
- [ ] 24. Delete the USER conversation and press Start.
- [ ] 25. Confirm exactly one visible USER replacement message appears.
- [ ] 26. Delete the ADMIN conversation and press Start.
- [ ] 27. Confirm exactly one visible ADMIN replacement message appears.

---

## Pass Criteria

All 27 items above must be checked before Issue #31 is considered resolved.

Issue #31 **must not** be closed until this checklist is fully completed and
the live sequence passes without any invisible-response or duplicate-anchor
incidents.

---

## Failure Response

If any item fails:
- Note the exact step and exact observed behavior.
- Check Railway logs for the structured `start_hard_reset` diagnostic entry.
- Verify that `edit_path_bypassed: true` appears in the log for the failing `/start`.
- Verify that `send_result: ok` or `send_result: failed` appears.
- Open a new corrective work item referencing Issue #31.
