# SECURITY_RISK_ASSESSMENT

## If password-login is restored, key risks

1. **Plaintext password exposure in Telegram chat history** (high).
2. **Secret storage risk**: env/plaintext vs hash/derivation strategy.
3. **Brute-force risk** without rate limit/lockout/backoff.
4. **Session hijack/reuse risk** without TTL + binding controls.
5. **Scope bleed risk** if session not bound to user and context.
6. **Audit insufficiency risk** if login attempts/success/failures not logged safely.
7. **Rotation risk** if password not versioned/rotatable.
8. **Recovery risk** if no revocation/logout-all mechanism.

## Minimum controls required if reintroduced
- One-way secret verification (no plaintext persistence).
- Attempt throttling + temporary lockout.
- Session TTL + explicit logout + emergency revocation.
- Bind session to Telegram user id (and optionally chat context).
- Structured audit events without leaking secret content.
- Secret rotation protocol.

## Current model risk profile
Current model avoids password-in-chat exposure, but currently blocks owner admin commands from private chat due strict chat context gate.
