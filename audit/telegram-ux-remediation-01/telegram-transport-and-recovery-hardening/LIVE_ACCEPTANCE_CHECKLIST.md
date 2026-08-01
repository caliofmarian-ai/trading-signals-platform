# LIVE ACCEPTANCE CHECKLIST

To be completed manually after the PR is merged and deployed to Railway.

**Issue #27 must remain open until ALL items below pass in live production.**

---

## Prerequisites

- [ ] PR merged to main
- [ ] Railway deployment complete and running (check Railway dashboard)
- [ ] `TELEGRAM_BOT_TOKEN` configured in Railway environment
- [ ] `ENABLE_TELEGRAM=1` set in Railway environment
- [ ] Bot is polling (visible in Railway logs: no repeated 400/401 errors)

---

## Acceptance steps

### 1. Fresh start (delete conversation first)

- [ ] In Telegram, delete the entire private conversation with the bot
- [ ] Press the native **Start** button (or send `/start`)
- [ ] Bot produces **one** message — a welcome page with inline buttons

### 2. Single-message navigation — Engine

- [ ] Send `/engine` command
- [ ] The **existing welcome message is edited** in place (no new message appears)
- [ ] Engine Status panel is visible in the same message

### 3. Single-message navigation — Admin via callback

- [ ] Press **Admin Control Surface** button (from welcome page) or navigate back to welcome via Home button
- [ ] The **existing message is edited** in place (no new message)
- [ ] Admin-related page is visible

### 4. Single-message contract — multi-step

- [ ] Navigate: Start → Status (button) → Help (button) → Home (button)
- [ ] Only **one** message exists in the conversation throughout
- [ ] Each button press edits that message (no new messages accumulate)

### 5. Deleted active message recovery

- [ ] While the bot is running, delete the active bot message from Telegram
- [ ] Send `/start`
- [ ] Bot sends **exactly one** new message
- [ ] Subsequent navigation edits that new message

### 6. Deleted conversation recovery

- [ ] Delete the entire conversation again
- [ ] Press Start (or send `/start`)
- [ ] Bot responds with **one** welcome message
- [ ] Navigation continues to edit that message (repeat steps 2–4)

### 7. Button spinner dismissal

- [ ] Press any inline button (Status, Help, Home)
- [ ] The Telegram loading spinner **disappears immediately** after the edit completes
- [ ] No "An error occurred" notification appears from Telegram

### 8. Railway log inspection

- [ ] Check Railway logs for the session above
- [ ] No bot token visible in any log line (search for `:AA` which is the start of token suffix)
- [ ] No unhandled exception stack traces visible
- [ ] `telegram_app_nav_send_failure` events present only if a send genuinely failed
- [ ] No `telegram_app_nav_edit_failure` events with category "unexpected" for normal navigation

---

## Pass criterion

All 8 sections above pass without manual intervention.

Issue #27 may be closed only after this checklist is fully signed off in production.
