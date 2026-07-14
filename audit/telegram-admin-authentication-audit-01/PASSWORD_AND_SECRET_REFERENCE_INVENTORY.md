# PASSWORD_AND_SECRET_REFERENCE_INVENTORY

## Requested markers inventory

| Marker | Found? | Location(s) | Classification |
|---|---|---|---|
| `ADMIN_PASSWORD` | Not found | N/A | No repository evidence |
| `ADMIN_SECRET` | Not found | N/A | No repository evidence |
| `BOT_PASSWORD` | Not found | N/A | No repository evidence |
| `CONTROL_PASSWORD` | Not found | N/A | No repository evidence |
| admin passcode/PIN/login secret | Not found | N/A | No repository evidence |
| generic `password` in auth flow | Not found in admin runtime flow | N/A | No admin-password flow evidence |

## Related security text that can be misread
- `send/docs/canonical/active/SECURITY_MODEL_v2.0.0.md:365` says "Password login disabled" in server-hardening section (`SSH` context), not Telegram admin-password flow config.

## Actual secret/env usage around Telegram admin
- `TELEGRAM_BOT_TOKEN` (bot API token) used by publisher/update poller.
- `OWNER_TELEGRAM_ID`, `ADMIN_CONTROL_CHAT_ID`, `ADMIN_CONTROL_THREAD_ID` are identity/context selectors, not passwords.

## Historical password recoverability assessment
- Historical admin password value: **not found**.
- Recoverable from repo: **no**.
- Rotation required for that unknown historical value: if owner reused old secret externally, rotation is prudent operationally; repository itself does not disclose one.
