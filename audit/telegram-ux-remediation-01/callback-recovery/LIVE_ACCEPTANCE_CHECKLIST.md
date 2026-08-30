# Live Railway and Telegram Acceptance Checklist

Issue: #42

Use the existing Railway service and the existing Telegram bot. The Owner tests
with the normal administrator account; no second bot is required.

- [ ] Railway deployment completes successfully.
- [ ] Normal Admin Home and Owner Knowledge pages still render correctly.
- [ ] Pressing a button from an older `/start` generation returns Home and shows
      a short `Button expired` notification.
- [ ] The current active Telegram panel remains the single tracked panel after
      stale recovery.
- [ ] A retired button, if one is available in an older message, returns Admin
      Home with working buttons and a short retirement notification.
- [ ] An unauthorized admin callback displays only an access-denied notification
      and does not replace the visible panel.
- [ ] Back, Home, Refresh, and `What is this?` continue to work.
- [ ] Opening recovery routes does not change strategy parameters, symbols,
      permissions, distribution, FSM state, or broker execution state.
- [ ] Restart/redeploy leaves `/start` and normal navigation operational.

Final acceptance must be recorded only after the Owner confirms the live result.
