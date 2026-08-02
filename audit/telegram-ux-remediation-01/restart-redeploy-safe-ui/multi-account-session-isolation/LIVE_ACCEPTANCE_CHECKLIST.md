# Live Acceptance Checklist — Two-Account Isolation Test

**Status:** Pending live validation (cannot be automated — requires two Telegram accounts)

## USER Account Test

1. [ ] Delete USER conversation history
2. [ ] Send `/start`
3. [ ] Confirm exactly one USER message U1 appears
4. [ ] Send `/status`
5. [ ] Confirm U1 is edited (no new message sent)

## ADMIN Account Test

6. [ ] Switch to ADMIN account in same Telegram application
7. [ ] Delete ADMIN conversation history
8. [ ] Send `/start`
9. [ ] Confirm exactly one ADMIN message A1 appears
10. [ ] Send `/admin`
11. [ ] Confirm A1 is edited (no new message)
12. [ ] Press Engine button
13. [ ] Confirm A1 is edited

## Isolation Test

14. [ ] Switch to USER
15. [ ] Send `/status`
16. [ ] Confirm U1 still works (not disturbed by ADMIN operations)
17. [ ] Switch to ADMIN
18. [ ] Press Home button
19. [ ] Confirm A1 still works
20. [ ] Delete ADMIN message A1 only
21. [ ] Send ADMIN `/start`
22. [ ] Confirm exactly one replacement ADMIN message A2
23. [ ] Confirm USER U1 remains unaffected
24. [ ] Switch between accounts at least 3 times
25. [ ] Both accounts remain responsive throughout

## Success Criteria

- No silent commands for either account
- Edit never creates a new message unless previous is stale/deleted
- ADMIN stale recovery does not affect USER session
- Replacement A2 works as new active message for all ADMIN commands
