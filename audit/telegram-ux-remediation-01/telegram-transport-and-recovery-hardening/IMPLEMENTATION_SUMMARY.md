# IMPLEMENTATION SUMMARY

## Branch

`copilot/correction-telegram-ux-remediation`

## Problem

PR #29 merged and all automated tests passed (114 Telegram-focused, 499 total) and
Railway deployed successfully.  However, live Telegram acceptance still failed:

- Navigation commands and buttons sent new messages instead of editing the existing one.
- After the user deleted all messages and restarted, the bot stopped responding.

## Root causes found (4)

1. **parse_mode inconsistency** — `edit_message()` set `parse_mode="HTML"` while
   `send_message()` used no parse_mode.  Admin panel text (from `render_admin_home`) includes
   `<value>`, `<dir>`, `<filename>` from the command registry.  These caused Telegram 400
   parse-entities errors on every admin panel edit.  The error was classified "unexpected",
   active state was not cleared, and `send_message` was called as fallback — sending a new
   message and violating the single-message contract.

2. **Silent send_message failure** — `_send_interactive_page` swallowed `send_message`
   exceptions with `except Exception: pass`.  When both edit and send failed, nothing was
   logged and no active message was tracked, making the bot appear unresponsive.

3. **Bot token in JSONL logs** — `requests` exceptions embed the full API URL (including
   the token) in `str(e)`.  The poller logged `str(e)` directly without sanitization.

4. **Unanswered callback queries** — APP: and ADMIN_NAV: callbacks were never acknowledged
   with `answerCallbackQuery`, leaving a 10-second Telegram loading spinner and an "error
   occurred" indication even when the edit succeeded.

## Fixes applied

1. Removed `payload["parse_mode"] = "HTML"` from `edit_message()`.  Both transport
   functions now use no parse_mode — consistent, plain-text rendering, no parse errors.
2. Replaced `except Exception: pass` with `observability_logger.log_error(...)`.
3. Added `_sanitize()` to `telegram_publisher`; applied to all error strings before logging.
4. Added `_ack_callback()` to `telegram_updates`; called for all non-VOTE_ callbacks.

## Tests

18 new tests in `tests/telegram_transport/test_telegram_transport_and_recovery.py`.
Full suite: 517 passed (499 baseline + 18 new).  No regressions.

## Security

- Token never appears in JSONL logs or exception strings (test 15, test 14).
- Raw API error responses replaced with safe summaries.
- Secret scan: clean.
- CodeQL: run (see CodeQL result in PR).

## Status

Automated tests pass.  Live Telegram acceptance is still required after merge.
Issue #27 remains open until live acceptance passes.
