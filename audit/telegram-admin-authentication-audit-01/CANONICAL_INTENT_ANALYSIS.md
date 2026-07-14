# CANONICAL_INTENT_ANALYSIS

## Canonical docs vs implementation

## Canonical docs (active)
- `TELEGRAM_UX_v2.0.0.md` states admin UX is private, role-scoped, and may use inline keyboards (`:416`, `:437`).
- Canonical admin entry command remains `/admin` (`:451-457`).
- Docs do not define a Telegram password-login/session command flow.

## Current implementation
- `/admin` exists.
- Role/permission model exists.
- Admin command execution is restricted by admin chat-id context before permission checks.
- Current `/admin` response is plain text list (no inline admin menu rendering in active path).

## Best evidence-supported intended model
Option **E**:
- Role/permission-based control plane is canonical.
- Context-gating is part of current control-plane hardening.
- Private role-scoped UX is canonically desired, but current runtime implementation is narrower (chat-id restricted).
- Password-session layer is not evidenced in repository code history.
